"""
CKC MASTERMIND Session Management
==================================

Udvidet session management med:
- Persistent storage (JSON/Database)
- Session recovery og resumption
- Checkpoint & rollback
- State snapshots
- Session cloning
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .coordinator import (
    MastermindSession,
    MastermindStatus,
    MastermindPriority,
    MastermindTask,
    TaskStatus,
    TaskResult,
    Directive,
    AgentParticipation,
    ExecutionPlan,
    FeedbackReport,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SESSION CHECKPOINT
# =============================================================================

@dataclass
class SessionCheckpoint:
    """Et checkpoint af en session's tilstand."""
    checkpoint_id: str
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    label: str = ""
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    tasks_snapshot: Dict[str, Any] = field(default_factory=dict)
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    is_auto: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "label": self.label,
            "state_snapshot": self.state_snapshot,
            "tasks_snapshot": self.tasks_snapshot,
            "context_snapshot": self.context_snapshot,
            "is_auto": self.is_auto
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionCheckpoint":
        return cls(
            checkpoint_id=data["checkpoint_id"],
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            label=data.get("label", ""),
            state_snapshot=data.get("state_snapshot", {}),
            tasks_snapshot=data.get("tasks_snapshot", {}),
            context_snapshot=data.get("context_snapshot", {}),
            is_auto=data.get("is_auto", False)
        )


# =============================================================================
# SESSION STORE (Abstract & Implementations)
# =============================================================================

class SessionStore:
    """Abstract base for session storage."""

    async def save(self, session: MastermindSession) -> bool:
        raise NotImplementedError

    async def load(self, session_id: str) -> Optional[MastermindSession]:
        raise NotImplementedError

    async def delete(self, session_id: str) -> bool:
        raise NotImplementedError

    async def list_sessions(
        self,
        status: Optional[MastermindStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def save_checkpoint(self, checkpoint: SessionCheckpoint) -> bool:
        raise NotImplementedError

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[SessionCheckpoint]:
        raise NotImplementedError

    async def list_checkpoints(self, session_id: str) -> List[SessionCheckpoint]:
        raise NotImplementedError


class FileSessionStore(SessionStore):
    """
    Fil-baseret session storage.

    Gemmer sessions som JSON filer i en specificeret mappe.
    """

    def __init__(self, base_path: str = "/tmp/mastermind_sessions"):
        self.base_path = Path(base_path)
        self.sessions_path = self.base_path / "sessions"
        self.checkpoints_path = self.base_path / "checkpoints"

        # Create directories
        self.sessions_path.mkdir(parents=True, exist_ok=True)
        self.checkpoints_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"FileSessionStore initialiseret: {self.base_path}")

    async def save(self, session: MastermindSession) -> bool:
        """Gem en session til fil."""
        try:
            filepath = self.sessions_path / f"{session.session_id}.json"
            data = session.to_dict()

            async with asyncio.Lock():
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Session gemt: {session.session_id}")
            return True

        except Exception as e:
            logger.error(f"Fejl ved gem af session {session.session_id}: {e}")
            return False

    async def load(self, session_id: str) -> Optional[MastermindSession]:
        """Indlæs en session fra fil."""
        try:
            filepath = self.sessions_path / f"{session_id}.json"

            if not filepath.exists():
                return None

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct session
            session = MastermindSession.from_dict(data)

            # Reconstruct nested objects
            session.tasks = {
                k: self._reconstruct_task(v)
                for k, v in data.get("tasks", {}).items()
            }

            session.active_agents = {
                k: self._reconstruct_participation(v)
                for k, v in data.get("active_agents", {}).items()
            }

            session.active_kommandanter = {
                k: self._reconstruct_participation(v)
                for k, v in data.get("active_kommandanter", {}).items()
            }

            session.accumulated_results = [
                self._reconstruct_result(r)
                for r in data.get("accumulated_results", [])
            ]

            session.super_admin_directives = [
                self._reconstruct_directive(d)
                for d in data.get("super_admin_directives", [])
            ]

            if data.get("systems_dirigent_plan"):
                session.systems_dirigent_plan = self._reconstruct_plan(
                    data["systems_dirigent_plan"]
                )

            logger.debug(f"Session indlæst: {session_id}")
            return session

        except Exception as e:
            logger.error(f"Fejl ved indlæsning af session {session_id}: {e}")
            return None

    async def delete(self, session_id: str) -> bool:
        """Slet en session."""
        try:
            filepath = self.sessions_path / f"{session_id}.json"

            if filepath.exists():
                filepath.unlink()
                logger.debug(f"Session slettet: {session_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Fejl ved sletning af session {session_id}: {e}")
            return False

    async def list_sessions(
        self,
        status: Optional[MastermindStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List alle sessions."""
        sessions = []

        for filepath in self.sessions_path.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if status and data.get("status") != status.value:
                    continue

                sessions.append({
                    "session_id": data.get("session_id"),
                    "status": data.get("status"),
                    "primary_objective": data.get("primary_objective"),
                    "created_at": data.get("created_at"),
                    "priority": data.get("priority")
                })

            except Exception as e:
                logger.warning(f"Kunne ikke læse {filepath}: {e}")

        # Sort by created_at desc
        sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)

        return sessions[:limit]

    async def save_checkpoint(self, checkpoint: SessionCheckpoint) -> bool:
        """Gem et checkpoint."""
        try:
            filepath = self.checkpoints_path / f"{checkpoint.checkpoint_id}.json"

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Fejl ved gem af checkpoint: {e}")
            return False

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[SessionCheckpoint]:
        """Indlæs et checkpoint."""
        try:
            filepath = self.checkpoints_path / f"{checkpoint_id}.json"

            if not filepath.exists():
                return None

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            return SessionCheckpoint.from_dict(data)

        except Exception as e:
            logger.error(f"Fejl ved indlæsning af checkpoint: {e}")
            return None

    async def list_checkpoints(self, session_id: str) -> List[SessionCheckpoint]:
        """List checkpoints for en session."""
        checkpoints = []

        for filepath in self.checkpoints_path.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if data.get("session_id") == session_id:
                    checkpoints.append(SessionCheckpoint.from_dict(data))

            except Exception as e:
                logger.warning(f"Kunne ikke læse {filepath}: {e}")

        # Sort by created_at desc
        checkpoints.sort(key=lambda c: c.created_at, reverse=True)

        return checkpoints

    # Reconstruction helpers
    def _reconstruct_task(self, data: Dict[str, Any]) -> MastermindTask:
        return MastermindTask(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            assigned_to=data.get("assigned_to"),
            status=TaskStatus(data.get("status", "pending")),
            priority=MastermindPriority(data.get("priority", 2)),
            dependencies=data.get("dependencies", []),
            parent_task=data.get("parent_task"),
            sub_tasks=data.get("sub_tasks", []),
            estimated_duration_seconds=data.get("estimated_duration_seconds", 60),
            actual_duration_seconds=data.get("actual_duration_seconds"),
            result=data.get("result")
        )

    def _reconstruct_participation(self, data: Dict[str, Any]) -> AgentParticipation:
        from .coordinator import ParticipantRole
        return AgentParticipation(
            agent_id=data["agent_id"],
            agent_name=data["agent_name"],
            role=ParticipantRole(data["role"]),
            capabilities=data.get("capabilities", []),
            current_task=data.get("current_task"),
            completed_tasks=data.get("completed_tasks", 0),
            status=data.get("status", "idle")
        )

    def _reconstruct_result(self, data: Dict[str, Any]) -> TaskResult:
        return TaskResult(
            task_id=data["task_id"],
            success=data["success"],
            output=data.get("output"),
            metrics=data.get("metrics", {}),
            error=data.get("error"),
            agent_id=data.get("agent_id", ""),
            confidence=data.get("confidence", 1.0)
        )

    def _reconstruct_directive(self, data: Dict[str, Any]) -> Directive:
        from .coordinator import DirectiveType
        return Directive(
            directive_id=data["directive_id"],
            directive_type=DirectiveType(data["directive_type"]),
            source=data["source"],
            target=data["target"],
            content=data.get("content", {}),
            priority=MastermindPriority(data.get("priority", 2)),
            requires_acknowledgment=data.get("requires_acknowledgment", True),
            acknowledged_by=set(data.get("acknowledged_by", []))
        )

    def _reconstruct_plan(self, data: Dict[str, Any]) -> ExecutionPlan:
        return ExecutionPlan(
            plan_id=data["plan_id"],
            objective=data["objective"],
            phases=data.get("phases", []),
            current_phase=data.get("current_phase", 0)
        )


class InMemorySessionStore(SessionStore):
    """In-memory session storage (til testing)."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    async def save(self, session: MastermindSession) -> bool:
        self._sessions[session.session_id] = session.to_dict()
        return True

    async def load(self, session_id: str) -> Optional[MastermindSession]:
        data = self._sessions.get(session_id)
        if not data:
            return None
        return MastermindSession.from_dict(data)

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def list_sessions(
        self,
        status: Optional[MastermindStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        sessions = list(self._sessions.values())
        if status:
            sessions = [s for s in sessions if s.get("status") == status.value]
        return sessions[:limit]

    async def save_checkpoint(self, checkpoint: SessionCheckpoint) -> bool:
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint.to_dict()
        return True

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[SessionCheckpoint]:
        data = self._checkpoints.get(checkpoint_id)
        if not data:
            return None
        return SessionCheckpoint.from_dict(data)

    async def list_checkpoints(self, session_id: str) -> List[SessionCheckpoint]:
        checkpoints = [
            SessionCheckpoint.from_dict(c)
            for c in self._checkpoints.values()
            if c.get("session_id") == session_id
        ]
        checkpoints.sort(key=lambda c: c.created_at, reverse=True)
        return checkpoints


# =============================================================================
# SESSION MANAGER
# =============================================================================

class SessionManager:
    """
    Håndterer session persistence, recovery og checkpoints.

    Features:
    - Automatisk persistence ved ændringer
    - Checkpoint & rollback
    - Session cloning
    - Recovery af afbrudte sessions
    """

    def __init__(
        self,
        store: Optional[SessionStore] = None,
        auto_save: bool = True,
        auto_checkpoint_interval_tasks: int = 5
    ):
        """
        Initialiser SessionManager.

        Args:
            store: Session store backend
            auto_save: Automatisk gem ved ændringer
            auto_checkpoint_interval_tasks: Auto-checkpoint efter X fuldførte opgaver
        """
        self.store = store or FileSessionStore()
        self.auto_save = auto_save
        self.auto_checkpoint_interval_tasks = auto_checkpoint_interval_tasks

        # Track task counts for auto-checkpoint
        self._task_counts: Dict[str, int] = {}

        logger.info("SessionManager initialiseret")

    async def save_session(self, session: MastermindSession) -> bool:
        """Gem en session."""
        return await self.store.save(session)

    async def load_session(self, session_id: str) -> Optional[MastermindSession]:
        """Indlæs en session."""
        return await self.store.load(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Slet en session."""
        return await self.store.delete(session_id)

    async def list_sessions(
        self,
        status: Optional[MastermindStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List sessions."""
        return await self.store.list_sessions(status, limit)

    # -------------------------------------------------------------------------
    # CHECKPOINT MANAGEMENT
    # -------------------------------------------------------------------------

    async def create_checkpoint(
        self,
        session: MastermindSession,
        label: str = "",
        is_auto: bool = False
    ) -> SessionCheckpoint:
        """
        Opret et checkpoint af session's nuværende tilstand.

        Args:
            session: Sessionen at checkpoint
            label: Label for checkpoint
            is_auto: Om det er auto-genereret

        Returns:
            SessionCheckpoint
        """
        checkpoint = SessionCheckpoint(
            checkpoint_id=f"cp_{secrets.token_hex(6)}",
            session_id=session.session_id,
            label=label or f"Checkpoint ved {session.status.value}",
            is_auto=is_auto,
            state_snapshot={
                "status": session.status.value,
                "priority": session.priority.value,
                "budget_usd": session.budget_usd,
                "consumed_usd": session.consumed_usd
            },
            tasks_snapshot={
                tid: task.to_dict()
                for tid, task in session.tasks.items()
            },
            context_snapshot=session.shared_context.copy()
        )

        await self.store.save_checkpoint(checkpoint)

        logger.info(f"Checkpoint oprettet: {checkpoint.checkpoint_id} for session {session.session_id}")
        return checkpoint

    async def rollback_to_checkpoint(
        self,
        session: MastermindSession,
        checkpoint_id: str
    ) -> bool:
        """
        Rul session tilbage til et checkpoint.

        Args:
            session: Sessionen at rulle tilbage
            checkpoint_id: Checkpoint ID

        Returns:
            True hvis succesfuldt
        """
        checkpoint = await self.store.load_checkpoint(checkpoint_id)

        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} findes ikke")

        if checkpoint.session_id != session.session_id:
            raise ValueError(f"Checkpoint tilhører ikke session {session.session_id}")

        # Restore state
        session.status = MastermindStatus(checkpoint.state_snapshot["status"])
        session.priority = MastermindPriority(checkpoint.state_snapshot["priority"])
        session.budget_usd = checkpoint.state_snapshot["budget_usd"]
        session.consumed_usd = checkpoint.state_snapshot["consumed_usd"]

        # Restore tasks (simplified - just status)
        for tid, task_data in checkpoint.tasks_snapshot.items():
            if tid in session.tasks:
                session.tasks[tid].status = TaskStatus(task_data["status"])

        # Restore context
        session.shared_context = checkpoint.context_snapshot.copy()
        session.last_activity = datetime.now()

        # Save the rolled-back session
        await self.store.save(session)

        logger.info(f"Session {session.session_id} rullet tilbage til checkpoint {checkpoint_id}")
        return True

    async def list_checkpoints(self, session_id: str) -> List[SessionCheckpoint]:
        """List checkpoints for en session."""
        return await self.store.list_checkpoints(session_id)

    async def maybe_auto_checkpoint(
        self,
        session: MastermindSession,
        completed_tasks: int
    ) -> Optional[SessionCheckpoint]:
        """
        Opret auto-checkpoint hvis tærskel er nået.

        Args:
            session: Sessionen
            completed_tasks: Antal fuldførte opgaver

        Returns:
            SessionCheckpoint hvis oprettet, ellers None
        """
        session_id = session.session_id
        prev_count = self._task_counts.get(session_id, 0)

        # Check if we crossed the threshold
        if completed_tasks >= prev_count + self.auto_checkpoint_interval_tasks:
            self._task_counts[session_id] = completed_tasks
            return await self.create_checkpoint(
                session,
                label=f"Auto-checkpoint ved {completed_tasks} opgaver",
                is_auto=True
            )

        return None

    # -------------------------------------------------------------------------
    # SESSION CLONING
    # -------------------------------------------------------------------------

    async def clone_session(
        self,
        session: MastermindSession,
        new_objective: Optional[str] = None,
        reset_tasks: bool = False
    ) -> MastermindSession:
        """
        Klon en session.

        Args:
            session: Sessionen at klone
            new_objective: Nyt mål (ellers behold eksisterende)
            reset_tasks: Nulstil opgaver

        Returns:
            Den klonede session
        """
        new_session_id = f"mm_{secrets.token_hex(8)}"

        cloned = MastermindSession(
            session_id=new_session_id,
            status=MastermindStatus.INITIALIZING,
            primary_objective=new_objective or session.primary_objective,
            sub_objectives=session.sub_objectives.copy(),
            success_criteria=session.success_criteria.copy(),
            budget_usd=session.budget_usd,
            consumed_usd=0.0,
            priority=session.priority,
            tags=session.tags.copy() + ["cloned"],
            shared_context=session.shared_context.copy()
        )

        if not reset_tasks:
            # Clone tasks but reset status
            for tid, task in session.tasks.items():
                new_task = MastermindTask(
                    task_id=f"task_{secrets.token_hex(6)}",
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    estimated_duration_seconds=task.estimated_duration_seconds
                )
                cloned.tasks[new_task.task_id] = new_task
                cloned.task_queue.append(new_task.task_id)

        cloned.notes.append(f"Klonet fra session {session.session_id}")

        await self.store.save(cloned)

        logger.info(f"Session klonet: {session.session_id} -> {new_session_id}")
        return cloned

    # -------------------------------------------------------------------------
    # RECOVERY
    # -------------------------------------------------------------------------

    async def find_recoverable_sessions(self) -> List[MastermindSession]:
        """
        Find sessions der kan genoptages efter et crash.

        Returns:
            Liste af recoverable sessions
        """
        session_list = await self.store.list_sessions()
        recoverable = []

        for session_info in session_list:
            status = session_info.get("status")

            if status in [
                MastermindStatus.ACTIVE.value,
                MastermindStatus.PAUSED.value,
                MastermindStatus.INITIALIZING.value
            ]:
                session = await self.store.load(session_info["session_id"])
                if session:
                    recoverable.append(session)

        return recoverable

    async def recover_session(
        self,
        session: MastermindSession,
        reset_in_progress_tasks: bool = True
    ) -> MastermindSession:
        """
        Genoptag en afbrudt session.

        Args:
            session: Sessionen at genoptage
            reset_in_progress_tasks: Nulstil in-progress opgaver

        Returns:
            Den genoptagne session
        """
        if reset_in_progress_tasks:
            for task in session.tasks.values():
                if task.status == TaskStatus.IN_PROGRESS:
                    task.status = TaskStatus.PENDING
                    task.assigned_to = None
                    task.started_at = None

                    # Add back to queue
                    if task.task_id not in session.task_queue:
                        session.task_queue.append(task.task_id)

        # Reset agent statuses
        for agent in session.active_agents.values():
            if agent.status == "working":
                agent.status = "idle"
                agent.current_task = None

        # Update session
        if session.status == MastermindStatus.ACTIVE:
            session.status = MastermindStatus.PAUSED  # Pause until explicitly resumed

        session.notes.append(f"Genoptaget efter afbrydelse: {datetime.now().isoformat()}")
        session.last_activity = datetime.now()

        await self.store.save(session)

        logger.info(f"Session genoptaget: {session.session_id}")
        return session

    # -------------------------------------------------------------------------
    # SESSION ANALYTICS
    # -------------------------------------------------------------------------

    async def get_session_statistics(
        self,
        session: MastermindSession
    ) -> Dict[str, Any]:
        """
        Beregn statistik for en session.

        Returns:
            Dictionary med statistik
        """
        tasks = session.tasks.values()
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED]

        # Calculate durations
        total_duration = 0
        if completed_tasks:
            total_duration = sum(
                t.actual_duration_seconds or t.estimated_duration_seconds
                for t in completed_tasks
            )

        # Success rate
        total_finished = len(completed_tasks) + len(failed_tasks)
        success_rate = (
            len(completed_tasks) / total_finished * 100
            if total_finished > 0
            else 0
        )

        # Budget utilization
        budget_util = (
            session.consumed_usd / session.budget_usd * 100
            if session.budget_usd > 0
            else 0
        )

        # Time statistics
        elapsed_time = None
        if session.started_at:
            end_time = session.completed_at or datetime.now()
            elapsed_time = (end_time - session.started_at).total_seconds()

        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "pending_tasks": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "success_rate_percent": round(success_rate, 2),
            "total_task_duration_seconds": total_duration,
            "elapsed_time_seconds": elapsed_time,
            "budget_usd": session.budget_usd,
            "consumed_usd": session.consumed_usd,
            "budget_utilization_percent": round(budget_util, 2),
            "active_agents": len(session.active_agents),
            "directives_issued": len(session.super_admin_directives),
            "checkpoints_available": len(await self.store.list_checkpoints(session.session_id))
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_session_manager_instance: Optional[SessionManager] = None


def create_session_manager(
    store: Optional[SessionStore] = None,
    auto_save: bool = True,
    auto_checkpoint_interval_tasks: int = 5
) -> SessionManager:
    """Opret en SessionManager instance."""
    global _session_manager_instance
    _session_manager_instance = SessionManager(
        store=store,
        auto_save=auto_save,
        auto_checkpoint_interval_tasks=auto_checkpoint_interval_tasks
    )
    return _session_manager_instance


def get_session_manager() -> Optional[SessionManager]:
    """Hent den aktuelle SessionManager instance."""
    return _session_manager_instance
