"""
CKC State Manager
=================

Persistent state management for Kommandant task execution.

Provides:
- Task state checkpointing
- Delegation progress tracking
- State recovery after restart
- Specialist performance metrics persistence

Usage:
    from cirkelline.ckc.infrastructure import get_state_manager

    state_mgr = await get_state_manager()
    await state_mgr.save_task_state(task_id, state)
    state = await state_mgr.get_task_state(task_id)
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from .database import CKCDatabase, get_database

logger = logging.getLogger(__name__)


# ========== Enums ==========

class TaskExecutionStatus(Enum):
    """Task execution status for persistence."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class CheckpointType(Enum):
    """Types of state checkpoints."""
    TASK_START = "task_start"
    TASK_PROGRESS = "task_progress"
    DELEGATION_START = "delegation_start"
    DELEGATION_COMPLETE = "delegation_complete"
    SPECIALIST_ASSIGNED = "specialist_assigned"
    SPECIALIST_RESULT = "specialist_result"
    TASK_COMPLETE = "task_complete"
    ERROR = "error"


# ========== Data Classes ==========

@dataclass
class TaskState:
    """Persistent task state."""
    task_id: str
    kommandant_id: str
    room_id: Optional[int]
    status: TaskExecutionStatus
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    delegations: List[Dict[str, Any]] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_checkpoint_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "kommandant_id": self.kommandant_id,
            "room_id": self.room_id,
            "status": self.status.value if isinstance(self.status, TaskExecutionStatus) else self.status,
            "prompt": self.prompt,
            "context": self.context,
            "delegations": self.delegations,
            "results": self.results,
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_checkpoint_at": self.last_checkpoint_at.isoformat() if self.last_checkpoint_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskState":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            kommandant_id=data["kommandant_id"],
            room_id=data.get("room_id"),
            status=TaskExecutionStatus(data["status"]) if isinstance(data["status"], str) else data["status"],
            prompt=data["prompt"],
            context=data.get("context", {}),
            delegations=data.get("delegations", []),
            results=data.get("results", []),
            errors=data.get("errors", []),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            last_checkpoint_at=datetime.fromisoformat(data["last_checkpoint_at"]) if data.get("last_checkpoint_at") else None,
            metadata=data.get("metadata", {}),
        )


@dataclass
class StateCheckpoint:
    """A checkpoint in task execution."""
    checkpoint_id: str
    task_id: str
    checkpoint_type: CheckpointType
    state_snapshot: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "task_id": self.task_id,
            "checkpoint_type": self.checkpoint_type.value,
            "state_snapshot": self.state_snapshot,
            "created_at": self.created_at.isoformat(),
            "message": self.message,
        }


@dataclass
class SpecialistMetrics:
    """Performance metrics for a specialist."""
    specialist_id: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_execution_time_ms: int = 0
    average_execution_time_ms: float = 0.0
    success_rate: float = 1.0
    last_task_at: Optional[datetime] = None
    capabilities: List[str] = field(default_factory=list)

    def update_with_result(self, success: bool, execution_time_ms: int) -> None:
        """Update metrics with a new task result."""
        self.total_tasks += 1
        self.total_execution_time_ms += execution_time_ms
        self.average_execution_time_ms = self.total_execution_time_ms / self.total_tasks
        self.last_task_at = datetime.now(timezone.utc)

        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1

        self.success_rate = self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specialist_id": self.specialist_id,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "total_execution_time_ms": self.total_execution_time_ms,
            "average_execution_time_ms": self.average_execution_time_ms,
            "success_rate": self.success_rate,
            "last_task_at": self.last_task_at.isoformat() if self.last_task_at else None,
            "capabilities": self.capabilities,
        }


# ========== State Manager ==========

class StateManager:
    """
    Manages persistent state for Kommandant task execution.

    Provides:
    - Task state CRUD operations
    - Checkpoint creation and retrieval
    - State recovery after restart
    - Specialist metrics tracking
    """

    # SQL for creating tables if they don't exist
    INIT_SQL = """
    -- Task executions table
    CREATE TABLE IF NOT EXISTS ckc.task_executions (
        task_id VARCHAR(64) PRIMARY KEY,
        kommandant_id VARCHAR(64) NOT NULL,
        room_id INTEGER,
        status VARCHAR(32) NOT NULL DEFAULT 'pending',
        prompt TEXT NOT NULL,
        context JSONB DEFAULT '{}',
        delegations JSONB DEFAULT '[]',
        results JSONB DEFAULT '[]',
        errors JSONB DEFAULT '[]',
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        last_checkpoint_at TIMESTAMP WITH TIME ZONE,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Checkpoints table
    CREATE TABLE IF NOT EXISTS ckc.state_checkpoints (
        checkpoint_id VARCHAR(64) PRIMARY KEY,
        task_id VARCHAR(64) NOT NULL REFERENCES ckc.task_executions(task_id) ON DELETE CASCADE,
        checkpoint_type VARCHAR(32) NOT NULL,
        state_snapshot JSONB NOT NULL,
        message TEXT DEFAULT '',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Specialist metrics table
    CREATE TABLE IF NOT EXISTS ckc.specialist_metrics (
        specialist_id VARCHAR(64) PRIMARY KEY,
        total_tasks INTEGER DEFAULT 0,
        successful_tasks INTEGER DEFAULT 0,
        failed_tasks INTEGER DEFAULT 0,
        total_execution_time_ms BIGINT DEFAULT 0,
        average_execution_time_ms FLOAT DEFAULT 0.0,
        success_rate FLOAT DEFAULT 1.0,
        last_task_at TIMESTAMP WITH TIME ZONE,
        capabilities JSONB DEFAULT '[]',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_task_executions_status ON ckc.task_executions(status);
    CREATE INDEX IF NOT EXISTS idx_task_executions_kommandant ON ckc.task_executions(kommandant_id);
    CREATE INDEX IF NOT EXISTS idx_state_checkpoints_task ON ckc.state_checkpoints(task_id);
    CREATE INDEX IF NOT EXISTS idx_specialist_metrics_success ON ckc.specialist_metrics(success_rate);
    """

    def __init__(self, database: CKCDatabase):
        self._db = database
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """Initialize state manager and create tables if needed."""
        async with self._lock:
            if self._initialized:
                return True

            try:
                # Check if ckc schema exists
                schema_exists = await self._db.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'ckc')"
                )

                if not schema_exists:
                    await self._db.execute("CREATE SCHEMA IF NOT EXISTS ckc")
                    logger.info("Created ckc schema")

                # Create tables
                await self._db.execute(self.INIT_SQL)
                logger.info("State manager tables initialized")

                self._initialized = True
                return True

            except Exception as e:
                logger.error(f"Failed to initialize state manager: {e}")
                return False

    # ========== Task State Operations ==========

    async def save_task_state(self, state: TaskState) -> bool:
        """Save or update task state."""
        try:
            await self._db.execute(
                """
                INSERT INTO ckc.task_executions (
                    task_id, kommandant_id, room_id, status, prompt,
                    context, delegations, results, errors,
                    started_at, completed_at, last_checkpoint_at, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (task_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    context = EXCLUDED.context,
                    delegations = EXCLUDED.delegations,
                    results = EXCLUDED.results,
                    errors = EXCLUDED.errors,
                    completed_at = EXCLUDED.completed_at,
                    last_checkpoint_at = EXCLUDED.last_checkpoint_at,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                """,
                state.task_id,
                state.kommandant_id,
                state.room_id,
                state.status.value if isinstance(state.status, TaskExecutionStatus) else state.status,
                state.prompt,
                json.dumps(state.context),
                json.dumps(state.delegations),
                json.dumps(state.results),
                json.dumps(state.errors),
                state.started_at,
                state.completed_at,
                state.last_checkpoint_at,
                json.dumps(state.metadata),
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save task state {state.task_id}: {e}")
            return False

    async def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """Get task state by ID."""
        try:
            row = await self._db.fetchrow(
                "SELECT * FROM ckc.task_executions WHERE task_id = $1",
                task_id
            )

            if not row:
                return None

            return TaskState(
                task_id=row["task_id"],
                kommandant_id=row["kommandant_id"],
                room_id=row["room_id"],
                status=TaskExecutionStatus(row["status"]),
                prompt=row["prompt"],
                context=json.loads(row["context"]) if row["context"] else {},
                delegations=json.loads(row["delegations"]) if row["delegations"] else [],
                results=json.loads(row["results"]) if row["results"] else [],
                errors=json.loads(row["errors"]) if row["errors"] else [],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                last_checkpoint_at=row["last_checkpoint_at"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )

        except Exception as e:
            logger.error(f"Failed to get task state {task_id}: {e}")
            return None

    async def update_task_status(
        self,
        task_id: str,
        status: TaskExecutionStatus,
        error: Optional[str] = None
    ) -> bool:
        """Update task status."""
        try:
            if status in (TaskExecutionStatus.COMPLETED, TaskExecutionStatus.FAILED,
                         TaskExecutionStatus.CANCELLED, TaskExecutionStatus.TIMEOUT):
                await self._db.execute(
                    """
                    UPDATE ckc.task_executions
                    SET status = $2, completed_at = NOW(), updated_at = NOW()
                    WHERE task_id = $1
                    """,
                    task_id, status.value
                )
            else:
                await self._db.execute(
                    """
                    UPDATE ckc.task_executions
                    SET status = $2, updated_at = NOW()
                    WHERE task_id = $1
                    """,
                    task_id, status.value
                )

            if error:
                await self._db.execute(
                    """
                    UPDATE ckc.task_executions
                    SET errors = errors || $2::jsonb
                    WHERE task_id = $1
                    """,
                    task_id, json.dumps([error])
                )

            return True

        except Exception as e:
            logger.error(f"Failed to update task status {task_id}: {e}")
            return False

    async def get_active_tasks(self, kommandant_id: Optional[str] = None) -> List[TaskState]:
        """Get all active (non-completed) tasks."""
        try:
            if kommandant_id:
                rows = await self._db.fetch(
                    """
                    SELECT * FROM ckc.task_executions
                    WHERE status IN ('pending', 'running', 'paused')
                    AND kommandant_id = $1
                    ORDER BY started_at DESC
                    """,
                    kommandant_id
                )
            else:
                rows = await self._db.fetch(
                    """
                    SELECT * FROM ckc.task_executions
                    WHERE status IN ('pending', 'running', 'paused')
                    ORDER BY started_at DESC
                    """
                )

            return [
                TaskState(
                    task_id=row["task_id"],
                    kommandant_id=row["kommandant_id"],
                    room_id=row["room_id"],
                    status=TaskExecutionStatus(row["status"]),
                    prompt=row["prompt"],
                    context=json.loads(row["context"]) if row["context"] else {},
                    delegations=json.loads(row["delegations"]) if row["delegations"] else [],
                    results=json.loads(row["results"]) if row["results"] else [],
                    errors=json.loads(row["errors"]) if row["errors"] else [],
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    last_checkpoint_at=row["last_checkpoint_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get active tasks: {e}")
            return []

    # ========== Checkpoint Operations ==========

    async def create_checkpoint(self, checkpoint: StateCheckpoint) -> bool:
        """Create a state checkpoint."""
        try:
            await self._db.execute(
                """
                INSERT INTO ckc.state_checkpoints (
                    checkpoint_id, task_id, checkpoint_type, state_snapshot, message
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                checkpoint.checkpoint_id,
                checkpoint.task_id,
                checkpoint.checkpoint_type.value,
                json.dumps(checkpoint.state_snapshot),
                checkpoint.message,
            )

            # Update last_checkpoint_at on task
            await self._db.execute(
                "UPDATE ckc.task_executions SET last_checkpoint_at = NOW() WHERE task_id = $1",
                checkpoint.task_id
            )

            return True

        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return False

    async def get_checkpoints(self, task_id: str, limit: int = 100) -> List[StateCheckpoint]:
        """Get checkpoints for a task."""
        try:
            rows = await self._db.fetch(
                """
                SELECT * FROM ckc.state_checkpoints
                WHERE task_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                task_id, limit
            )

            return [
                StateCheckpoint(
                    checkpoint_id=row["checkpoint_id"],
                    task_id=row["task_id"],
                    checkpoint_type=CheckpointType(row["checkpoint_type"]),
                    state_snapshot=json.loads(row["state_snapshot"]) if row["state_snapshot"] else {},
                    created_at=row["created_at"],
                    message=row["message"] or "",
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get checkpoints for {task_id}: {e}")
            return []

    async def get_latest_checkpoint(self, task_id: str) -> Optional[StateCheckpoint]:
        """Get the most recent checkpoint for a task."""
        checkpoints = await self.get_checkpoints(task_id, limit=1)
        return checkpoints[0] if checkpoints else None

    # ========== Specialist Metrics ==========

    async def save_specialist_metrics(self, metrics: SpecialistMetrics) -> bool:
        """Save or update specialist metrics."""
        try:
            await self._db.execute(
                """
                INSERT INTO ckc.specialist_metrics (
                    specialist_id, total_tasks, successful_tasks, failed_tasks,
                    total_execution_time_ms, average_execution_time_ms, success_rate,
                    last_task_at, capabilities
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (specialist_id) DO UPDATE SET
                    total_tasks = EXCLUDED.total_tasks,
                    successful_tasks = EXCLUDED.successful_tasks,
                    failed_tasks = EXCLUDED.failed_tasks,
                    total_execution_time_ms = EXCLUDED.total_execution_time_ms,
                    average_execution_time_ms = EXCLUDED.average_execution_time_ms,
                    success_rate = EXCLUDED.success_rate,
                    last_task_at = EXCLUDED.last_task_at,
                    capabilities = EXCLUDED.capabilities,
                    updated_at = NOW()
                """,
                metrics.specialist_id,
                metrics.total_tasks,
                metrics.successful_tasks,
                metrics.failed_tasks,
                metrics.total_execution_time_ms,
                metrics.average_execution_time_ms,
                metrics.success_rate,
                metrics.last_task_at,
                json.dumps(metrics.capabilities),
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save specialist metrics {metrics.specialist_id}: {e}")
            return False

    async def get_specialist_metrics(self, specialist_id: str) -> Optional[SpecialistMetrics]:
        """Get metrics for a specialist."""
        try:
            row = await self._db.fetchrow(
                "SELECT * FROM ckc.specialist_metrics WHERE specialist_id = $1",
                specialist_id
            )

            if not row:
                return None

            return SpecialistMetrics(
                specialist_id=row["specialist_id"],
                total_tasks=row["total_tasks"],
                successful_tasks=row["successful_tasks"],
                failed_tasks=row["failed_tasks"],
                total_execution_time_ms=row["total_execution_time_ms"],
                average_execution_time_ms=row["average_execution_time_ms"],
                success_rate=row["success_rate"],
                last_task_at=row["last_task_at"],
                capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
            )

        except Exception as e:
            logger.error(f"Failed to get specialist metrics {specialist_id}: {e}")
            return None

    async def get_top_specialists(self, limit: int = 10) -> List[SpecialistMetrics]:
        """Get top performing specialists by success rate."""
        try:
            rows = await self._db.fetch(
                """
                SELECT * FROM ckc.specialist_metrics
                WHERE total_tasks > 0
                ORDER BY success_rate DESC, total_tasks DESC
                LIMIT $1
                """,
                limit
            )

            return [
                SpecialistMetrics(
                    specialist_id=row["specialist_id"],
                    total_tasks=row["total_tasks"],
                    successful_tasks=row["successful_tasks"],
                    failed_tasks=row["failed_tasks"],
                    total_execution_time_ms=row["total_execution_time_ms"],
                    average_execution_time_ms=row["average_execution_time_ms"],
                    success_rate=row["success_rate"],
                    last_task_at=row["last_task_at"],
                    capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get top specialists: {e}")
            return []

    # ========== Recovery Operations ==========

    async def recover_interrupted_tasks(self, kommandant_id: str) -> List[TaskState]:
        """
        Recover tasks that were running when system stopped.

        Returns tasks that should be resumed.
        """
        try:
            # Find tasks that were running/pending
            rows = await self._db.fetch(
                """
                SELECT * FROM ckc.task_executions
                WHERE kommandant_id = $1
                AND status IN ('running', 'pending')
                ORDER BY started_at ASC
                """,
                kommandant_id
            )

            tasks = []
            for row in rows:
                task = TaskState(
                    task_id=row["task_id"],
                    kommandant_id=row["kommandant_id"],
                    room_id=row["room_id"],
                    status=TaskExecutionStatus(row["status"]),
                    prompt=row["prompt"],
                    context=json.loads(row["context"]) if row["context"] else {},
                    delegations=json.loads(row["delegations"]) if row["delegations"] else [],
                    results=json.loads(row["results"]) if row["results"] else [],
                    errors=json.loads(row["errors"]) if row["errors"] else [],
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    last_checkpoint_at=row["last_checkpoint_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                tasks.append(task)

            if tasks:
                logger.info(f"Recovered {len(tasks)} interrupted tasks for {kommandant_id}")

            return tasks

        except Exception as e:
            logger.error(f"Failed to recover tasks for {kommandant_id}: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get state manager statistics."""
        try:
            task_counts = await self._db.fetchrow(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'running') as running,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed
                FROM ckc.task_executions
                """
            )

            checkpoint_count = await self._db.fetchval(
                "SELECT COUNT(*) FROM ckc.state_checkpoints"
            )

            specialist_count = await self._db.fetchval(
                "SELECT COUNT(*) FROM ckc.specialist_metrics"
            )

            return {
                "tasks": {
                    "total": task_counts["total"] if task_counts else 0,
                    "pending": task_counts["pending"] if task_counts else 0,
                    "running": task_counts["running"] if task_counts else 0,
                    "completed": task_counts["completed"] if task_counts else 0,
                    "failed": task_counts["failed"] if task_counts else 0,
                },
                "checkpoints": checkpoint_count or 0,
                "specialists_tracked": specialist_count or 0,
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


# ========== Singleton ==========

_state_manager: Optional[StateManager] = None
_state_manager_lock = asyncio.Lock()


async def get_state_manager() -> StateManager:
    """Get the singleton state manager instance."""
    global _state_manager

    async with _state_manager_lock:
        if _state_manager is None:
            db = await get_database()
            _state_manager = StateManager(db)
            await _state_manager.initialize()

        return _state_manager


async def close_state_manager() -> None:
    """Close the state manager."""
    global _state_manager

    async with _state_manager_lock:
        _state_manager = None
