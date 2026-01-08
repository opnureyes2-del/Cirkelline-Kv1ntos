"""
CKC Repository Layer
====================

Repository pattern implementation for CKC database tables.
Provides type-safe CRUD operations med automatic serialization.

Usage:
    from cirkelline.ckc.infrastructure import get_database, TaskContextRepository

    db = await get_database()
    repo = TaskContextRepository(db)

    # Create
    context = await repo.create(task_id="task_123", prompt="Hello world")

    # Read
    context = await repo.get_by_context_id("ctx_abc123")

    # Update
    await repo.update(context_id="ctx_abc123", status="completed")

    # Delete
    await repo.delete("ctx_abc123")
"""

import json
import hashlib
import logging
from typing import Optional, Dict, Any, List, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

from .database import CKCDatabase

logger = logging.getLogger(__name__)

# Type variable for generic repository
T = TypeVar('T')


# ==========================================================
# Data Classes for Database Entities
# ==========================================================

@dataclass
class TaskContextEntity:
    """Task context database entity."""
    context_id: str
    task_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    original_prompt: Optional[str] = None
    current_agent: Optional[str] = None
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)
    flags: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_record(cls, record) -> "TaskContextEntity":
        """Create entity from database record."""
        return cls(
            context_id=record["context_id"],
            task_id=record["task_id"],
            user_id=record.get("user_id"),
            session_id=record.get("session_id"),
            original_prompt=record.get("original_prompt"),
            current_agent=record.get("current_agent"),
            status=record.get("status", "active"),
            metadata=json.loads(record.get("metadata", "{}")) if isinstance(record.get("metadata"), str) else record.get("metadata", {}),
            flags=json.loads(record.get("flags", "{}")) if isinstance(record.get("flags"), str) else record.get("flags", {}),
            created_at=record.get("created_at"),
            updated_at=record.get("updated_at"),
        )


@dataclass
class WorkflowStepEntity:
    """Workflow step database entity."""
    step_id: str
    context_id: str
    agent_id: str
    action: Optional[str] = None
    status: str = "pending"
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    created_at: Optional[datetime] = None

    @classmethod
    def from_record(cls, record) -> "WorkflowStepEntity":
        """Create entity from database record."""
        return cls(
            step_id=record["step_id"],
            context_id=record["context_id"],
            agent_id=record["agent_id"],
            action=record.get("action"),
            status=record.get("status", "pending"),
            input_data=record.get("input_data", {}),
            output_data=record.get("output_data"),
            started_at=record.get("started_at"),
            completed_at=record.get("completed_at"),
            error=record.get("error"),
            retry_count=record.get("retry_count", 0),
            created_at=record.get("created_at"),
        )


class MemoryType(str, Enum):
    """Agent memory types."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class AgentMemoryEntity:
    """Agent memory database entity."""
    agent_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    id: Optional[str] = None
    importance: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_deleted: bool = False

    @classmethod
    def from_record(cls, record) -> "AgentMemoryEntity":
        """Create entity from database record."""
        return cls(
            id=str(record["id"]),
            agent_id=record["agent_id"],
            memory_type=MemoryType(record["memory_type"]),
            content=record.get("content", {}),
            importance=record.get("importance", 0.5),
            access_count=record.get("access_count", 0),
            last_accessed=record.get("last_accessed"),
            tags=record.get("tags", []),
            created_at=record.get("created_at"),
            expires_at=record.get("expires_at"),
            is_deleted=record.get("is_deleted", False),
        )


@dataclass
class LearningEventEntity:
    """Learning event database entity."""
    room_id: int
    event_type: str
    content: Dict[str, Any]
    id: Optional[str] = None
    room_name: Optional[str] = None
    source: Optional[str] = None
    integrity_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    @classmethod
    def from_record(cls, record) -> "LearningEventEntity":
        """Create entity from database record."""
        return cls(
            id=str(record["id"]),
            room_id=record["room_id"],
            room_name=record.get("room_name"),
            event_type=record["event_type"],
            source=record.get("source"),
            content=record.get("content", {}),
            integrity_hash=record.get("integrity_hash"),
            metadata=record.get("metadata", {}),
            created_at=record.get("created_at"),
        )


@dataclass
class ILCPMessageEntity:
    """ILCP message database entity."""
    message_id: str
    sender_room_id: int
    recipient_room_id: int
    message_type: str
    content: Dict[str, Any]
    id: Optional[str] = None
    priority: str = "normal"
    task_context_id: Optional[str] = None
    task_context_data: Optional[Dict[str, Any]] = None
    validation_mode: str = "normal"
    is_validated: bool = False
    validation_errors: Optional[List[str]] = None
    status: str = "pending"
    created_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    @classmethod
    def from_record(cls, record) -> "ILCPMessageEntity":
        """Create entity from database record."""
        return cls(
            id=str(record["id"]),
            message_id=record["message_id"],
            sender_room_id=record["sender_room_id"],
            recipient_room_id=record["recipient_room_id"],
            message_type=record["message_type"],
            priority=record.get("priority", "normal"),
            content=record.get("content", {}),
            task_context_id=record.get("task_context_id"),
            task_context_data=record.get("task_context_data"),
            validation_mode=record.get("validation_mode", "normal"),
            is_validated=record.get("is_validated", False),
            validation_errors=record.get("validation_errors"),
            status=record.get("status", "pending"),
            created_at=record.get("created_at"),
            delivered_at=record.get("delivered_at"),
            acknowledged_at=record.get("acknowledged_at"),
            expires_at=record.get("expires_at"),
        )


@dataclass
class KnowledgeEntryEntity:
    """Knowledge entry database entity."""
    entry_id: str
    title: str
    content: str
    category: str
    id: Optional[str] = None
    summary: Optional[str] = None
    subcategory: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)
    related_entries: List[str] = field(default_factory=list)
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = False

    @classmethod
    def from_record(cls, record) -> "KnowledgeEntryEntity":
        """Create entity from database record."""
        return cls(
            id=str(record["id"]),
            entry_id=record["entry_id"],
            title=record["title"],
            content=record["content"],
            category=record["category"],
            summary=record.get("summary"),
            subcategory=record.get("subcategory"),
            tags=record.get("tags", []),
            source_refs=record.get("source_refs", []),
            related_entries=record.get("related_entries", []),
            source_type=record.get("source_type"),
            source_id=record.get("source_id"),
            metadata=record.get("metadata", {}),
            version=record.get("version", 1),
            access_count=record.get("access_count", 0),
            last_accessed=record.get("last_accessed"),
            created_by=record.get("created_by"),
            updated_by=record.get("updated_by"),
            created_at=record.get("created_at"),
            updated_at=record.get("updated_at"),
            is_deleted=record.get("is_deleted", False),
        )


@dataclass
class AuditTrailEntity:
    """Audit trail database entity."""
    entity_type: str
    entity_id: str
    action: str
    id: Optional[str] = None
    actor: Optional[str] = None
    actor_type: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_record(cls, record) -> "AuditTrailEntity":
        """Create entity from database record."""
        return cls(
            id=str(record["id"]),
            entity_type=record["entity_type"],
            entity_id=record["entity_id"],
            action=record["action"],
            actor=record.get("actor"),
            actor_type=record.get("actor_type"),
            old_value=record.get("old_value"),
            new_value=record.get("new_value"),
            changed_fields=record.get("changed_fields"),
            metadata=record.get("metadata", {}),
            ip_address=str(record.get("ip_address")) if record.get("ip_address") else None,
            user_agent=record.get("user_agent"),
            created_at=record.get("created_at"),
        )


@dataclass
class WorkLoopSequenceEntity:
    """Work loop sequence database entity."""
    sequence_id: str
    id: Optional[str] = None
    context_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: str = "pending"
    current_step: int = 0
    total_steps: int = 0
    execution_mode: str = "sequential"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_record(cls, record) -> "WorkLoopSequenceEntity":
        """Create entity from database record."""
        return cls(
            id=str(record["id"]),
            sequence_id=record["sequence_id"],
            context_id=record.get("context_id"),
            name=record.get("name"),
            description=record.get("description"),
            status=record.get("status", "pending"),
            current_step=record.get("current_step", 0),
            total_steps=record.get("total_steps", 0),
            execution_mode=record.get("execution_mode", "sequential"),
            result=record.get("result"),
            error=record.get("error"),
            created_at=record.get("created_at"),
            started_at=record.get("started_at"),
            completed_at=record.get("completed_at"),
            updated_at=record.get("updated_at"),
        )


# ==========================================================
# Base Repository
# ==========================================================

class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with common operations."""

    def __init__(self, db: CKCDatabase):
        self.db = db

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the table name."""
        pass

    @property
    @abstractmethod
    def id_column(self) -> str:
        """Return the primary ID column name."""
        pass

    @abstractmethod
    def _entity_from_record(self, record) -> T:
        """Convert database record to entity."""
        pass

    def _serialize_json(self, value: Any) -> str:
        """Serialize value to JSON string."""
        if isinstance(value, dict) or isinstance(value, list):
            return json.dumps(value)
        return value


# ==========================================================
# Repository Implementations
# ==========================================================

class TaskContextRepository(BaseRepository[TaskContextEntity]):
    """Repository for task contexts."""

    @property
    def table_name(self) -> str:
        return "ckc.task_contexts"

    @property
    def id_column(self) -> str:
        return "context_id"

    def _entity_from_record(self, record) -> TaskContextEntity:
        return TaskContextEntity.from_record(record)

    async def create(
        self,
        task_id: str,
        prompt: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskContextEntity:
        """Create a new task context."""
        import uuid
        context_id = f"ctx_{uuid.uuid4().hex[:16]}"

        record = await self.db.fetchrow(
            f"""
            INSERT INTO {self.table_name}
            (context_id, task_id, user_id, session_id, original_prompt, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            context_id, task_id, user_id, session_id, prompt,
            json.dumps(metadata or {})
        )
        return self._entity_from_record(record)

    async def get_by_context_id(self, context_id: str) -> Optional[TaskContextEntity]:
        """Get task context by context_id."""
        record = await self.db.fetchrow(
            f"SELECT * FROM {self.table_name} WHERE context_id = $1",
            context_id
        )
        return self._entity_from_record(record) if record else None

    async def get_by_task_id(self, task_id: str) -> Optional[TaskContextEntity]:
        """Get active task context by task_id."""
        record = await self.db.fetchrow(
            f"SELECT * FROM {self.table_name} WHERE task_id = $1 AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            task_id
        )
        return self._entity_from_record(record) if record else None

    async def update(self, context_id: str, **kwargs) -> Optional[TaskContextEntity]:
        """Update task context fields."""
        if not kwargs:
            return await self.get_by_context_id(context_id)

        # Build update query dynamically
        set_clauses = []
        values = []
        for i, (key, value) in enumerate(kwargs.items(), 1):
            if key in ("metadata", "flags"):
                value = json.dumps(value)
            set_clauses.append(f"{key} = ${i}")
            values.append(value)

        values.append(context_id)
        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE context_id = ${len(values)}
            RETURNING *
        """

        record = await self.db.fetchrow(query, *values)
        return self._entity_from_record(record) if record else None

    async def list_active(self, limit: int = 100) -> List[TaskContextEntity]:
        """List active task contexts."""
        records = await self.db.fetch(
            f"SELECT * FROM {self.table_name} WHERE status = 'active' ORDER BY created_at DESC LIMIT $1",
            limit
        )
        return [self._entity_from_record(r) for r in records]

    async def delete(self, context_id: str) -> bool:
        """Delete task context (and cascade to related data)."""
        result = await self.db.execute(
            f"DELETE FROM {self.table_name} WHERE context_id = $1",
            context_id
        )
        return "DELETE 1" in result


class WorkflowStepRepository(BaseRepository[WorkflowStepEntity]):
    """Repository for workflow steps."""

    @property
    def table_name(self) -> str:
        return "ckc.workflow_steps"

    @property
    def id_column(self) -> str:
        return "step_id"

    def _entity_from_record(self, record) -> WorkflowStepEntity:
        return WorkflowStepEntity.from_record(record)

    async def create(
        self,
        context_id: str,
        step_id: str,
        agent_id: str,
        action: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> WorkflowStepEntity:
        """Create a new workflow step."""
        record = await self.db.fetchrow(
            f"""
            INSERT INTO {self.table_name}
            (context_id, step_id, agent_id, action, input_data)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            context_id, step_id, agent_id, action,
            json.dumps(input_data or {})
        )
        return self._entity_from_record(record)

    async def get_by_context(self, context_id: str) -> List[WorkflowStepEntity]:
        """Get all steps for a context."""
        records = await self.db.fetch(
            f"SELECT * FROM {self.table_name} WHERE context_id = $1 ORDER BY created_at",
            context_id
        )
        return [self._entity_from_record(r) for r in records]

    async def update_status(
        self,
        context_id: str,
        step_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[WorkflowStepEntity]:
        """Update step status and timestamps."""
        now = datetime.now()

        if status == "running":
            record = await self.db.fetchrow(
                f"""
                UPDATE {self.table_name}
                SET status = $1, started_at = $2
                WHERE context_id = $3 AND step_id = $4
                RETURNING *
                """,
                status, now, context_id, step_id
            )
        elif status in ("completed", "failed"):
            record = await self.db.fetchrow(
                f"""
                UPDATE {self.table_name}
                SET status = $1, completed_at = $2, output_data = $3, error = $4
                WHERE context_id = $5 AND step_id = $6
                RETURNING *
                """,
                status, now, json.dumps(output_data) if output_data else None,
                error, context_id, step_id
            )
        else:
            record = await self.db.fetchrow(
                f"""
                UPDATE {self.table_name}
                SET status = $1
                WHERE context_id = $2 AND step_id = $3
                RETURNING *
                """,
                status, context_id, step_id
            )

        return self._entity_from_record(record) if record else None


class AgentMemoryRepository(BaseRepository[AgentMemoryEntity]):
    """Repository for agent memory."""

    @property
    def table_name(self) -> str:
        return "ckc.agent_memory"

    @property
    def id_column(self) -> str:
        return "id"

    def _entity_from_record(self, record) -> AgentMemoryEntity:
        return AgentMemoryEntity.from_record(record)

    async def create(
        self,
        agent_id: str,
        memory_type: MemoryType,
        content: Dict[str, Any],
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> AgentMemoryEntity:
        """Create a new memory."""
        record = await self.db.fetchrow(
            f"""
            INSERT INTO {self.table_name}
            (agent_id, memory_type, content, importance, tags, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            agent_id, memory_type.value, json.dumps(content),
            importance, tags or [], expires_at
        )
        return self._entity_from_record(record)

    async def get_by_agent(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100,
    ) -> List[AgentMemoryEntity]:
        """Get memories for an agent."""
        if memory_type:
            records = await self.db.fetch(
                f"""
                SELECT * FROM {self.table_name}
                WHERE agent_id = $1 AND memory_type = $2 AND is_deleted = FALSE
                ORDER BY importance DESC, created_at DESC
                LIMIT $3
                """,
                agent_id, memory_type.value, limit
            )
        else:
            records = await self.db.fetch(
                f"""
                SELECT * FROM {self.table_name}
                WHERE agent_id = $1 AND is_deleted = FALSE
                ORDER BY importance DESC, created_at DESC
                LIMIT $2
                """,
                agent_id, limit
            )
        return [self._entity_from_record(r) for r in records]

    async def search_by_tags(
        self,
        agent_id: str,
        tags: List[str],
        limit: int = 50,
    ) -> List[AgentMemoryEntity]:
        """Search memories by tags."""
        records = await self.db.fetch(
            f"""
            SELECT * FROM {self.table_name}
            WHERE agent_id = $1 AND tags && $2 AND is_deleted = FALSE
            ORDER BY importance DESC
            LIMIT $3
            """,
            agent_id, tags, limit
        )
        return [self._entity_from_record(r) for r in records]

    async def touch(self, memory_id: str) -> None:
        """Update access count and last_accessed."""
        await self.db.execute(
            f"""
            UPDATE {self.table_name}
            SET access_count = access_count + 1, last_accessed = NOW()
            WHERE id = $1
            """,
            memory_id
        )

    async def soft_delete(self, memory_id: str) -> bool:
        """Soft delete a memory."""
        result = await self.db.execute(
            f"""
            UPDATE {self.table_name}
            SET is_deleted = TRUE, deleted_at = NOW()
            WHERE id = $1
            """,
            memory_id
        )
        return "UPDATE 1" in result


class LearningEventRepository(BaseRepository[LearningEventEntity]):
    """Repository for learning events."""

    @property
    def table_name(self) -> str:
        return "ckc.learning_events"

    @property
    def id_column(self) -> str:
        return "id"

    def _entity_from_record(self, record) -> LearningEventEntity:
        return LearningEventEntity.from_record(record)

    async def create(
        self,
        room_id: int,
        event_type: str,
        content: Dict[str, Any],
        room_name: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LearningEventEntity:
        """Create a new learning event."""
        # Generate integrity hash
        content_str = json.dumps(content, sort_keys=True)
        integrity_hash = hashlib.sha256(content_str.encode()).hexdigest()

        record = await self.db.fetchrow(
            f"""
            INSERT INTO {self.table_name}
            (room_id, room_name, event_type, source, content, integrity_hash, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            room_id, room_name, event_type, source,
            json.dumps(content), integrity_hash,
            json.dumps(metadata or {})
        )
        return self._entity_from_record(record)

    async def get_by_room(
        self,
        room_id: int,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[LearningEventEntity]:
        """Get events for a room."""
        if event_type:
            records = await self.db.fetch(
                f"""
                SELECT * FROM {self.table_name}
                WHERE room_id = $1 AND event_type = $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                room_id, event_type, limit
            )
        else:
            records = await self.db.fetch(
                f"""
                SELECT * FROM {self.table_name}
                WHERE room_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                room_id, limit
            )
        return [self._entity_from_record(r) for r in records]


class ILCPMessageRepository(BaseRepository[ILCPMessageEntity]):
    """Repository for ILCP messages."""

    @property
    def table_name(self) -> str:
        return "ckc.ilcp_messages"

    @property
    def id_column(self) -> str:
        return "message_id"

    def _entity_from_record(self, record) -> ILCPMessageEntity:
        return ILCPMessageEntity.from_record(record)

    async def create(
        self,
        message_id: str,
        sender_room_id: int,
        recipient_room_id: int,
        message_type: str,
        content: Dict[str, Any],
        priority: str = "normal",
        task_context_id: Optional[str] = None,
        task_context_data: Optional[Dict[str, Any]] = None,
        validation_mode: str = "normal",
    ) -> ILCPMessageEntity:
        """Create a new ILCP message."""
        record = await self.db.fetchrow(
            f"""
            INSERT INTO {self.table_name}
            (message_id, sender_room_id, recipient_room_id, message_type, content,
             priority, task_context_id, task_context_data, validation_mode)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            message_id, sender_room_id, recipient_room_id, message_type,
            json.dumps(content), priority, task_context_id,
            json.dumps(task_context_data) if task_context_data else None,
            validation_mode
        )
        return self._entity_from_record(record)

    async def get_pending_for_room(self, room_id: int, limit: int = 50) -> List[ILCPMessageEntity]:
        """Get pending messages for a room."""
        records = await self.db.fetch(
            f"""
            SELECT * FROM {self.table_name}
            WHERE recipient_room_id = $1 AND status = 'pending'
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                END,
                created_at
            LIMIT $2
            """,
            room_id, limit
        )
        return [self._entity_from_record(r) for r in records]

    async def mark_delivered(self, message_id: str) -> Optional[ILCPMessageEntity]:
        """Mark message as delivered."""
        record = await self.db.fetchrow(
            f"""
            UPDATE {self.table_name}
            SET status = 'delivered', delivered_at = NOW()
            WHERE message_id = $1
            RETURNING *
            """,
            message_id
        )
        return self._entity_from_record(record) if record else None

    async def mark_acknowledged(self, message_id: str) -> Optional[ILCPMessageEntity]:
        """Mark message as acknowledged."""
        record = await self.db.fetchrow(
            f"""
            UPDATE {self.table_name}
            SET status = 'acknowledged', acknowledged_at = NOW()
            WHERE message_id = $1
            RETURNING *
            """,
            message_id
        )
        return self._entity_from_record(record) if record else None

    async def update_validation(
        self,
        message_id: str,
        is_validated: bool,
        validation_errors: Optional[List[str]] = None,
    ) -> Optional[ILCPMessageEntity]:
        """Update validation status."""
        record = await self.db.fetchrow(
            f"""
            UPDATE {self.table_name}
            SET is_validated = $1, validation_errors = $2
            WHERE message_id = $3
            RETURNING *
            """,
            is_validated, validation_errors, message_id
        )
        return self._entity_from_record(record) if record else None


class KnowledgeEntryRepository(BaseRepository[KnowledgeEntryEntity]):
    """Repository for knowledge entries."""

    @property
    def table_name(self) -> str:
        return "ckc.knowledge_entries"

    @property
    def id_column(self) -> str:
        return "entry_id"

    def _entity_from_record(self, record) -> KnowledgeEntryEntity:
        return KnowledgeEntryEntity.from_record(record)

    async def create(
        self,
        entry_id: str,
        title: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeEntryEntity:
        """Create a new knowledge entry."""
        record = await self.db.fetchrow(
            f"""
            INSERT INTO {self.table_name}
            (entry_id, title, content, category, tags, source_type, source_id, created_by, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            entry_id, title, content, category, tags or [],
            source_type, source_id, created_by,
            json.dumps(metadata or {})
        )
        return self._entity_from_record(record)

    async def get_by_entry_id(self, entry_id: str) -> Optional[KnowledgeEntryEntity]:
        """Get entry by entry_id."""
        record = await self.db.fetchrow(
            f"SELECT * FROM {self.table_name} WHERE entry_id = $1 AND is_deleted = FALSE",
            entry_id
        )
        return self._entity_from_record(record) if record else None

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[KnowledgeEntryEntity]:
        """Search knowledge entries."""
        conditions = ["is_deleted = FALSE"]
        params = []
        param_idx = 1

        # Full-text search on title and content
        if query:
            conditions.append(f"(title ILIKE ${param_idx} OR content ILIKE ${param_idx})")
            params.append(f"%{query}%")
            param_idx += 1

        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category)
            param_idx += 1

        if tags:
            conditions.append(f"tags && ${param_idx}")
            params.append(tags)
            param_idx += 1

        params.append(limit)

        records = await self.db.fetch(
            f"""
            SELECT * FROM {self.table_name}
            WHERE {' AND '.join(conditions)}
            ORDER BY access_count DESC, updated_at DESC
            LIMIT ${param_idx}
            """,
            *params
        )
        return [self._entity_from_record(r) for r in records]

    async def update(
        self,
        entry_id: str,
        updated_by: Optional[str] = None,
        **kwargs
    ) -> Optional[KnowledgeEntryEntity]:
        """Update knowledge entry."""
        if not kwargs:
            return await self.get_by_entry_id(entry_id)

        kwargs["updated_by"] = updated_by

        set_clauses = []
        values = []
        for i, (key, value) in enumerate(kwargs.items(), 1):
            if key in ("metadata",):
                value = json.dumps(value)
            set_clauses.append(f"{key} = ${i}")
            values.append(value)

        # Increment version
        set_clauses.append(f"version = version + 1")

        values.append(entry_id)
        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE entry_id = ${len(values)} AND is_deleted = FALSE
            RETURNING *
        """

        record = await self.db.fetchrow(query, *values)
        return self._entity_from_record(record) if record else None

    async def touch(self, entry_id: str) -> None:
        """Update access count."""
        await self.db.execute(
            f"""
            UPDATE {self.table_name}
            SET access_count = access_count + 1, last_accessed = NOW()
            WHERE entry_id = $1
            """,
            entry_id
        )

    async def soft_delete(self, entry_id: str) -> bool:
        """Soft delete an entry."""
        result = await self.db.execute(
            f"""
            UPDATE {self.table_name}
            SET is_deleted = TRUE, deleted_at = NOW()
            WHERE entry_id = $1
            """,
            entry_id
        )
        return "UPDATE 1" in result


class AuditTrailRepository(BaseRepository[AuditTrailEntity]):
    """Repository for audit trail."""

    @property
    def table_name(self) -> str:
        return "ckc.audit_trail"

    @property
    def id_column(self) -> str:
        return "id"

    def _entity_from_record(self, record) -> AuditTrailEntity:
        return AuditTrailEntity.from_record(record)

    async def log(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: Optional[str] = None,
        actor_type: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditTrailEntity:
        """Create an audit log entry."""
        # Calculate changed fields
        changed_fields = None
        if old_value and new_value:
            changed_fields = [k for k in set(old_value.keys()) | set(new_value.keys())
                            if old_value.get(k) != new_value.get(k)]

        record = await self.db.fetchrow(
            f"""
            INSERT INTO {self.table_name}
            (entity_type, entity_id, action, actor, actor_type, old_value, new_value, changed_fields, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            entity_type, entity_id, action, actor, actor_type,
            json.dumps(old_value) if old_value else None,
            json.dumps(new_value) if new_value else None,
            changed_fields,
            json.dumps(metadata or {})
        )
        return self._entity_from_record(record)

    async def get_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
    ) -> List[AuditTrailEntity]:
        """Get audit history for an entity."""
        records = await self.db.fetch(
            f"""
            SELECT * FROM {self.table_name}
            WHERE entity_type = $1 AND entity_id = $2
            ORDER BY created_at DESC
            LIMIT $3
            """,
            entity_type, entity_id, limit
        )
        return [self._entity_from_record(r) for r in records]


class WorkLoopSequenceRepository(BaseRepository[WorkLoopSequenceEntity]):
    """Repository for work loop sequences."""

    @property
    def table_name(self) -> str:
        return "ckc.work_loop_sequences"

    @property
    def id_column(self) -> str:
        return "sequence_id"

    def _entity_from_record(self, record) -> WorkLoopSequenceEntity:
        return WorkLoopSequenceEntity.from_record(record)

    async def create(
        self,
        sequence_id: str,
        context_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        total_steps: int = 0,
        execution_mode: str = "sequential",
    ) -> WorkLoopSequenceEntity:
        """Create a new work loop sequence."""
        record = await self.db.fetchrow(
            f"""
            INSERT INTO {self.table_name}
            (sequence_id, context_id, name, description, total_steps, execution_mode)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            sequence_id, context_id, name, description, total_steps, execution_mode
        )
        return self._entity_from_record(record)

    async def get_by_sequence_id(self, sequence_id: str) -> Optional[WorkLoopSequenceEntity]:
        """Get sequence by sequence_id."""
        record = await self.db.fetchrow(
            f"SELECT * FROM {self.table_name} WHERE sequence_id = $1",
            sequence_id
        )
        return self._entity_from_record(record) if record else None

    async def update_progress(
        self,
        sequence_id: str,
        current_step: int,
        status: Optional[str] = None,
    ) -> Optional[WorkLoopSequenceEntity]:
        """Update sequence progress."""
        now = datetime.now()

        if status == "running":
            record = await self.db.fetchrow(
                f"""
                UPDATE {self.table_name}
                SET current_step = $1, status = $2, started_at = COALESCE(started_at, $3)
                WHERE sequence_id = $4
                RETURNING *
                """,
                current_step, status, now, sequence_id
            )
        elif status in ("completed", "failed"):
            record = await self.db.fetchrow(
                f"""
                UPDATE {self.table_name}
                SET current_step = $1, status = $2, completed_at = $3
                WHERE sequence_id = $4
                RETURNING *
                """,
                current_step, status, now, sequence_id
            )
        else:
            record = await self.db.fetchrow(
                f"""
                UPDATE {self.table_name}
                SET current_step = $1
                WHERE sequence_id = $2
                RETURNING *
                """,
                current_step, sequence_id
            )

        return self._entity_from_record(record) if record else None

    async def set_result(
        self,
        sequence_id: str,
        result: Dict[str, Any],
        error: Optional[str] = None,
    ) -> Optional[WorkLoopSequenceEntity]:
        """Set sequence result."""
        status = "failed" if error else "completed"

        record = await self.db.fetchrow(
            f"""
            UPDATE {self.table_name}
            SET result = $1, error = $2, status = $3, completed_at = NOW()
            WHERE sequence_id = $4
            RETURNING *
            """,
            json.dumps(result), error, status, sequence_id
        )
        return self._entity_from_record(record) if record else None
