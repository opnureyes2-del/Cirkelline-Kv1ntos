"""
CKC MASTERMIND Coordinator
==========================

Central koordinator for MASTERMIND Tilstand - muliggør realtidssamarbejde
mellem alle CKC-agenter under direktion af Super Admin og Systems Dirigent.

Arkitektur:
- SessionManager: Håndterer MastermindSession lifecycle
- TaskOrchestrator: Koordinerer opgavefordeling
- ResourceAllocator: Dynamisk ressourceallokering
- FeedbackAggregator: Samler og syntetiserer feedback
- StateSynchronizer: Synkroniserer tilstand på tværs af agenter
- AuditLogger: Logger alle handlinger for audit
"""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class MastermindStatus(Enum):
    """Status for en MASTERMIND session."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class MastermindPriority(Enum):
    """Prioritetsniveau for MASTERMIND session."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class DirectiveType(Enum):
    """Type af direktiv fra Super Admin eller Dirigent."""
    OBJECTIVE = "objective"           # Nyt mål
    ADJUSTMENT = "adjustment"         # Justering af eksisterende
    PRIORITIZATION = "prioritization" # Ændring af prioritet
    PAUSE = "pause"                   # Pause session
    RESUME = "resume"                 # Genoptag session
    ABORT = "abort"                   # Afbryd session
    RESOURCE = "resource"             # Ressource ændring
    FEEDBACK = "feedback"             # Feedback til agent


class ParticipantRole(Enum):
    """Roller for deltagere i MASTERMIND session."""
    SUPER_ADMIN = "super_admin"
    SYSTEMS_DIRIGENT = "systems_dirigent"
    KOMMANDANT = "kommandant"
    SPECIALIST = "specialist"
    OBSERVER = "observer"


class TaskStatus(Enum):
    """Status for en opgave i MASTERMIND."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Directive:
    """Et direktiv fra Super Admin eller Systems Dirigent."""
    directive_id: str
    directive_type: DirectiveType
    source: str  # "super_admin" eller "systems_dirigent"
    target: str  # "all", agent_id, eller "session"
    content: Dict[str, Any]
    priority: MastermindPriority = MastermindPriority.NORMAL
    requires_acknowledgment: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    acknowledged_by: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "directive_id": self.directive_id,
            "directive_type": self.directive_type.value,
            "source": self.source,
            "target": self.target,
            "content": self.content,
            "priority": self.priority.value,
            "requires_acknowledgment": self.requires_acknowledgment,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "acknowledged_by": list(self.acknowledged_by)
        }


@dataclass
class AgentParticipation:
    """Information om en agents deltagelse i MASTERMIND."""
    agent_id: str
    agent_name: str
    role: ParticipantRole
    capabilities: List[str]
    joined_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    current_task: Optional[str] = None
    completed_tasks: int = 0
    status: str = "idle"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "joined_at": self.joined_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "current_task": self.current_task,
            "completed_tasks": self.completed_tasks,
            "status": self.status
        }


@dataclass
class MastermindTask:
    """En opgave i MASTERMIND session."""
    task_id: str
    title: str
    description: str
    assigned_to: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: MastermindPriority = MastermindPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    parent_task: Optional[str] = None
    sub_tasks: List[str] = field(default_factory=list)
    estimated_duration_seconds: int = 60
    actual_duration_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "parent_task": self.parent_task,
            "sub_tasks": self.sub_tasks,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "actual_duration_seconds": self.actual_duration_seconds
        }


@dataclass
class TaskResult:
    """Resultat fra en udført opgave."""
    task_id: str
    success: bool
    output: Any
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.now)
    agent_id: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "output": self.output,
            "metrics": self.metrics,
            "error": self.error,
            "completed_at": self.completed_at.isoformat(),
            "agent_id": self.agent_id,
            "confidence": self.confidence
        }


@dataclass
class ExecutionPlan:
    """Eksekveringsplan oprettet af Systems Dirigent."""
    plan_id: str
    objective: str
    phases: List[Dict[str, Any]] = field(default_factory=list)
    current_phase: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "objective": self.objective,
            "phases": self.phases,
            "current_phase": self.current_phase,
            "created_at": self.created_at.isoformat(),
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None
        }


@dataclass
class FeedbackReport:
    """Feedback rapport fra feedback aggregation."""
    report_id: str
    session_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    progress_percent: float = 0.0
    completed_tasks: int = 0
    pending_tasks: int = 0
    active_agents: int = 0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "progress_percent": self.progress_percent,
            "completed_tasks": self.completed_tasks,
            "pending_tasks": self.pending_tasks,
            "active_agents": self.active_agents,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "resource_usage": self.resource_usage
        }


# =============================================================================
# MASTERMIND SESSION (Central state container)
# =============================================================================

@dataclass
class MastermindSession:
    """
    Central state container for en MASTERMIND session.

    Indeholder al state for fælles opgave-kontekst, deltagere,
    direktiver og akkumulerede resultater.
    """
    session_id: str
    status: MastermindStatus = MastermindStatus.INITIALIZING

    # Fælles mål
    primary_objective: str = ""
    sub_objectives: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    # Deltagere
    active_agents: Dict[str, AgentParticipation] = field(default_factory=dict)
    active_kommandanter: Dict[str, AgentParticipation] = field(default_factory=dict)

    # Opgaver
    tasks: Dict[str, MastermindTask] = field(default_factory=dict)
    task_queue: List[str] = field(default_factory=list)

    # Kontekst
    shared_context: Dict[str, Any] = field(default_factory=dict)
    accumulated_results: List[TaskResult] = field(default_factory=list)

    # Direktion
    super_admin_directives: List[Directive] = field(default_factory=list)
    systems_dirigent_plan: Optional[ExecutionPlan] = None

    # Timeline
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.now)

    # Ressourcer
    budget_usd: float = 100.0
    consumed_usd: float = 0.0
    priority: MastermindPriority = MastermindPriority.NORMAL

    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Konverter session til dictionary."""
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "primary_objective": self.primary_objective,
            "sub_objectives": self.sub_objectives,
            "success_criteria": self.success_criteria,
            "active_agents": {k: v.to_dict() for k, v in self.active_agents.items()},
            "active_kommandanter": {k: v.to_dict() for k, v in self.active_kommandanter.items()},
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "task_queue": self.task_queue,
            "shared_context": self.shared_context,
            "accumulated_results": [r.to_dict() for r in self.accumulated_results],
            "super_admin_directives": [d.to_dict() for d in self.super_admin_directives],
            "systems_dirigent_plan": self.systems_dirigent_plan.to_dict() if self.systems_dirigent_plan else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_activity": self.last_activity.isoformat(),
            "budget_usd": self.budget_usd,
            "consumed_usd": self.consumed_usd,
            "priority": self.priority.value,
            "tags": self.tags,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MastermindSession":
        """Opret session fra dictionary."""
        session = cls(
            session_id=data["session_id"],
            status=MastermindStatus(data["status"]),
            primary_objective=data.get("primary_objective", ""),
            sub_objectives=data.get("sub_objectives", []),
            success_criteria=data.get("success_criteria", []),
            budget_usd=data.get("budget_usd", 100.0),
            consumed_usd=data.get("consumed_usd", 0.0),
            priority=MastermindPriority(data.get("priority", 2)),
            tags=data.get("tags", []),
            notes=data.get("notes", [])
        )
        return session


# =============================================================================
# MASTERMIND COORDINATOR
# =============================================================================

class MastermindCoordinator:
    """
    Central koordinator for MASTERMIND Tilstand.

    Håndterer:
    - Session lifecycle management
    - Opgave orchestration og delegation
    - Ressource allokering
    - Feedback aggregation
    - State synkronisering
    - Audit logging

    Eksempel:
        coordinator = MastermindCoordinator()
        session = await coordinator.create_session(
            objective="Generer komplet markedsføringsmateriale",
            budget_usd=50.0
        )
        await coordinator.start_session(session.session_id)
    """

    def __init__(
        self,
        max_concurrent_sessions: int = 5,
        max_agents_per_session: int = 20,
        default_timeout_seconds: int = 3600,
        enable_audit_logging: bool = True
    ):
        """
        Initialiser MastermindCoordinator.

        Args:
            max_concurrent_sessions: Max samtidige sessions
            max_agents_per_session: Max agenter per session
            default_timeout_seconds: Default timeout for sessions
            enable_audit_logging: Aktiver audit logging
        """
        self.max_concurrent_sessions = max_concurrent_sessions
        self.max_agents_per_session = max_agents_per_session
        self.default_timeout_seconds = default_timeout_seconds
        self.enable_audit_logging = enable_audit_logging

        # Session storage
        self._sessions: Dict[str, MastermindSession] = {}
        self._session_lock = asyncio.Lock()

        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {
            "session_created": [],
            "session_started": [],
            "session_completed": [],
            "session_failed": [],
            "task_assigned": [],
            "task_completed": [],
            "directive_issued": [],
            "feedback_received": [],
        }

        # Audit log
        self._audit_log: List[Dict[str, Any]] = []

        # Performance metrics
        self._metrics = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "failed_sessions": 0,
            "total_tasks": 0,
            "avg_session_duration": 0.0
        }

        logger.info("MastermindCoordinator initialiseret")

    # -------------------------------------------------------------------------
    # SESSION MANAGEMENT
    # -------------------------------------------------------------------------

    async def create_session(
        self,
        objective: str,
        sub_objectives: Optional[List[str]] = None,
        success_criteria: Optional[List[str]] = None,
        budget_usd: float = 100.0,
        priority: MastermindPriority = MastermindPriority.NORMAL,
        tags: Optional[List[str]] = None
    ) -> MastermindSession:
        """
        Opret en ny MASTERMIND session.

        Args:
            objective: Primært mål for sessionen
            sub_objectives: Delmål
            success_criteria: Succeskriterier
            budget_usd: Budget i USD
            priority: Prioritetsniveau
            tags: Tags for sessionen

        Returns:
            Den oprettede MastermindSession
        """
        async with self._session_lock:
            # Check limit
            active_count = sum(
                1 for s in self._sessions.values()
                if s.status in [MastermindStatus.ACTIVE, MastermindStatus.INITIALIZING]
            )
            if active_count >= self.max_concurrent_sessions:
                raise ValueError(f"Max antal samtidige sessions ({self.max_concurrent_sessions}) nået")

            # Create session
            session_id = f"mm_{secrets.token_hex(8)}"
            session = MastermindSession(
                session_id=session_id,
                primary_objective=objective,
                sub_objectives=sub_objectives or [],
                success_criteria=success_criteria or [],
                budget_usd=budget_usd,
                priority=priority,
                tags=tags or []
            )

            self._sessions[session_id] = session
            self._metrics["total_sessions"] += 1

            self._log_audit("session_created", {
                "session_id": session_id,
                "objective": objective,
                "budget_usd": budget_usd
            })

            await self._emit_event("session_created", session)

            logger.info(f"MASTERMIND session oprettet: {session_id}")
            return session

    async def start_session(self, session_id: str) -> bool:
        """
        Start en MASTERMIND session.

        Args:
            session_id: ID på sessionen

        Returns:
            True hvis startet succesfuldt
        """
        session = self._get_session(session_id)

        if session.status != MastermindStatus.INITIALIZING:
            raise ValueError(f"Session {session_id} kan ikke startes fra status {session.status.value}")

        session.status = MastermindStatus.ACTIVE
        session.started_at = datetime.now()
        session.last_activity = datetime.now()

        self._log_audit("session_started", {"session_id": session_id})
        await self._emit_event("session_started", session)

        logger.info(f"MASTERMIND session startet: {session_id}")
        return True

    async def pause_session(self, session_id: str) -> bool:
        """Pause en aktiv session."""
        session = self._get_session(session_id)

        if session.status != MastermindStatus.ACTIVE:
            raise ValueError(f"Kun aktive sessions kan pauses")

        session.status = MastermindStatus.PAUSED
        session.last_activity = datetime.now()

        self._log_audit("session_paused", {"session_id": session_id})
        logger.info(f"MASTERMIND session pauset: {session_id}")
        return True

    async def resume_session(self, session_id: str) -> bool:
        """Genoptag en pauset session."""
        session = self._get_session(session_id)

        if session.status != MastermindStatus.PAUSED:
            raise ValueError(f"Kun pausede sessions kan genoptages")

        session.status = MastermindStatus.ACTIVE
        session.last_activity = datetime.now()

        self._log_audit("session_resumed", {"session_id": session_id})
        logger.info(f"MASTERMIND session genoptaget: {session_id}")
        return True

    async def complete_session(
        self,
        session_id: str,
        final_result: Optional[Dict[str, Any]] = None
    ) -> MastermindSession:
        """
        Afslut en MASTERMIND session.

        Args:
            session_id: Session ID
            final_result: Endeligt resultat

        Returns:
            Den afsluttede session
        """
        session = self._get_session(session_id)

        session.status = MastermindStatus.COMPLETED
        session.completed_at = datetime.now()
        session.last_activity = datetime.now()

        if final_result:
            session.shared_context["final_result"] = final_result

        self._metrics["completed_sessions"] += 1

        # Calculate duration
        if session.started_at:
            duration = (session.completed_at - session.started_at).total_seconds()
            self._update_avg_duration(duration)

        self._log_audit("session_completed", {
            "session_id": session_id,
            "duration_seconds": duration if session.started_at else 0,
            "tasks_completed": len([t for t in session.tasks.values() if t.status == TaskStatus.COMPLETED])
        })

        await self._emit_event("session_completed", session)

        logger.info(f"MASTERMIND session afsluttet: {session_id}")
        return session

    async def abort_session(self, session_id: str, reason: str = "") -> bool:
        """Afbryd en session."""
        session = self._get_session(session_id)

        session.status = MastermindStatus.ABORTED
        session.completed_at = datetime.now()
        session.last_activity = datetime.now()
        session.notes.append(f"Aborted: {reason}")

        self._log_audit("session_aborted", {
            "session_id": session_id,
            "reason": reason
        })

        logger.warning(f"MASTERMIND session afbrudt: {session_id} - {reason}")
        return True

    def get_session(self, session_id: str) -> Optional[MastermindSession]:
        """Hent en session (offentlig)."""
        return self._sessions.get(session_id)

    def list_sessions(
        self,
        status: Optional[MastermindStatus] = None,
        limit: int = 50
    ) -> List[MastermindSession]:
        """List sessions med optional filter."""
        sessions = list(self._sessions.values())

        if status:
            sessions = [s for s in sessions if s.status == status]

        # Sort by created_at desc
        sessions.sort(key=lambda s: s.created_at, reverse=True)

        return sessions[:limit]

    # -------------------------------------------------------------------------
    # TASK MANAGEMENT
    # -------------------------------------------------------------------------

    async def create_task(
        self,
        session_id: str,
        title: str,
        description: str,
        priority: MastermindPriority = MastermindPriority.NORMAL,
        dependencies: Optional[List[str]] = None,
        parent_task: Optional[str] = None,
        estimated_duration_seconds: int = 60
    ) -> MastermindTask:
        """
        Opret en ny opgave i en session.

        Args:
            session_id: Session ID
            title: Opgavetitel
            description: Beskrivelse
            priority: Prioritet
            dependencies: Afhængigheder (task IDs)
            parent_task: Parent task ID
            estimated_duration_seconds: Estimeret varighed

        Returns:
            Den oprettede MastermindTask
        """
        session = self._get_session(session_id)

        task_id = f"task_{secrets.token_hex(6)}"
        task = MastermindTask(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies or [],
            parent_task=parent_task,
            estimated_duration_seconds=estimated_duration_seconds
        )

        session.tasks[task_id] = task
        session.task_queue.append(task_id)
        session.last_activity = datetime.now()

        # If parent task, add to parent's sub_tasks
        if parent_task and parent_task in session.tasks:
            session.tasks[parent_task].sub_tasks.append(task_id)

        self._metrics["total_tasks"] += 1

        self._log_audit("task_created", {
            "session_id": session_id,
            "task_id": task_id,
            "title": title
        })

        logger.info(f"Opgave oprettet: {task_id} i session {session_id}")
        return task

    async def assign_task(
        self,
        session_id: str,
        task_id: str,
        agent_id: str
    ) -> bool:
        """
        Tildel en opgave til en agent.

        Args:
            session_id: Session ID
            task_id: Task ID
            agent_id: Agent ID

        Returns:
            True hvis tildelt succesfuldt
        """
        session = self._get_session(session_id)

        if task_id not in session.tasks:
            raise ValueError(f"Opgave {task_id} findes ikke")

        task = session.tasks[task_id]

        # Check dependencies
        for dep_id in task.dependencies:
            dep_task = session.tasks.get(dep_id)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                raise ValueError(f"Afhængighed {dep_id} er ikke fuldført")

        task.assigned_to = agent_id
        task.status = TaskStatus.ASSIGNED
        session.last_activity = datetime.now()

        # Update agent participation
        if agent_id in session.active_agents:
            session.active_agents[agent_id].current_task = task_id
            session.active_agents[agent_id].status = "working"
            session.active_agents[agent_id].last_activity = datetime.now()

        self._log_audit("task_assigned", {
            "session_id": session_id,
            "task_id": task_id,
            "agent_id": agent_id
        })

        await self._emit_event("task_assigned", {"task": task, "agent_id": agent_id})

        logger.info(f"Opgave {task_id} tildelt til {agent_id}")
        return True

    async def start_task(self, session_id: str, task_id: str) -> bool:
        """Marker en opgave som startet."""
        session = self._get_session(session_id)

        if task_id not in session.tasks:
            raise ValueError(f"Opgave {task_id} findes ikke")

        task = session.tasks[task_id]
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        session.last_activity = datetime.now()

        # Remove from queue if present
        if task_id in session.task_queue:
            session.task_queue.remove(task_id)

        return True

    async def complete_task(
        self,
        session_id: str,
        task_id: str,
        result: TaskResult
    ) -> bool:
        """
        Marker en opgave som fuldført.

        Args:
            session_id: Session ID
            task_id: Task ID
            result: Opgaveresultat

        Returns:
            True hvis fuldført succesfuldt
        """
        session = self._get_session(session_id)

        if task_id not in session.tasks:
            raise ValueError(f"Opgave {task_id} findes ikke")

        task = session.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result = result.to_dict()

        if task.started_at:
            task.actual_duration_seconds = int(
                (task.completed_at - task.started_at).total_seconds()
            )

        # Update agent participation
        if task.assigned_to and task.assigned_to in session.active_agents:
            agent = session.active_agents[task.assigned_to]
            agent.current_task = None
            agent.status = "idle"
            agent.completed_tasks += 1
            agent.last_activity = datetime.now()

        # Add to accumulated results
        session.accumulated_results.append(result)
        session.last_activity = datetime.now()

        self._log_audit("task_completed", {
            "session_id": session_id,
            "task_id": task_id,
            "success": result.success,
            "duration_seconds": task.actual_duration_seconds
        })

        await self._emit_event("task_completed", {"task": task, "result": result})

        logger.info(f"Opgave {task_id} fuldført")
        return True

    async def fail_task(
        self,
        session_id: str,
        task_id: str,
        error: str
    ) -> bool:
        """Marker en opgave som fejlet."""
        session = self._get_session(session_id)

        if task_id not in session.tasks:
            raise ValueError(f"Opgave {task_id} findes ikke")

        task = session.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()
        task.result = {"error": error}

        session.last_activity = datetime.now()

        self._log_audit("task_failed", {
            "session_id": session_id,
            "task_id": task_id,
            "error": error
        })

        logger.error(f"Opgave {task_id} fejlede: {error}")
        return True

    def get_pending_tasks(self, session_id: str) -> List[MastermindTask]:
        """Hent ventende opgaver for en session."""
        session = self._get_session(session_id)
        return [
            session.tasks[tid]
            for tid in session.task_queue
            if tid in session.tasks and session.tasks[tid].status == TaskStatus.PENDING
        ]

    def get_next_task(self, session_id: str, agent_id: str) -> Optional[MastermindTask]:
        """
        Hent næste tilgængelige opgave for en agent.

        Tager højde for:
        - Prioritet
        - Afhængigheder
        - Agent capabilities
        """
        session = self._get_session(session_id)

        pending_tasks = self.get_pending_tasks(session_id)

        # Filter tasks with satisfied dependencies
        available_tasks = []
        for task in pending_tasks:
            deps_satisfied = all(
                session.tasks.get(dep_id, MastermindTask("", "", "")).status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            if deps_satisfied:
                available_tasks.append(task)

        if not available_tasks:
            return None

        # Sort by priority (highest first)
        available_tasks.sort(key=lambda t: t.priority.value, reverse=True)

        return available_tasks[0]

    # -------------------------------------------------------------------------
    # DIRECTIVE MANAGEMENT
    # -------------------------------------------------------------------------

    async def issue_directive(
        self,
        session_id: str,
        directive_type: DirectiveType,
        source: str,
        target: str,
        content: Dict[str, Any],
        priority: MastermindPriority = MastermindPriority.NORMAL,
        requires_acknowledgment: bool = True,
        expires_in_seconds: Optional[int] = None
    ) -> Directive:
        """
        Udsted et direktiv.

        Args:
            session_id: Session ID
            directive_type: Type af direktiv
            source: Kilde ("super_admin" eller "systems_dirigent")
            target: Mål ("all", agent_id, eller "session")
            content: Indhold af direktiv
            priority: Prioritet
            requires_acknowledgment: Kræver bekræftelse
            expires_in_seconds: Udløbstid i sekunder

        Returns:
            Det oprettede Directive
        """
        session = self._get_session(session_id)

        directive = Directive(
            directive_id=f"dir_{secrets.token_hex(6)}",
            directive_type=directive_type,
            source=source,
            target=target,
            content=content,
            priority=priority,
            requires_acknowledgment=requires_acknowledgment,
            expires_at=datetime.now() + timedelta(seconds=expires_in_seconds) if expires_in_seconds else None
        )

        session.super_admin_directives.append(directive)
        session.last_activity = datetime.now()

        self._log_audit("directive_issued", {
            "session_id": session_id,
            "directive_id": directive.directive_id,
            "type": directive_type.value,
            "source": source,
            "target": target
        })

        await self._emit_event("directive_issued", directive)

        logger.info(f"Direktiv udstedt: {directive.directive_id} ({directive_type.value})")
        return directive

    async def acknowledge_directive(
        self,
        session_id: str,
        directive_id: str,
        agent_id: str
    ) -> bool:
        """Bekræft modtagelse af direktiv."""
        session = self._get_session(session_id)

        for directive in session.super_admin_directives:
            if directive.directive_id == directive_id:
                directive.acknowledged_by.add(agent_id)
                return True

        return False

    def get_pending_directives(
        self,
        session_id: str,
        target: Optional[str] = None
    ) -> List[Directive]:
        """Hent ventende direktiver."""
        session = self._get_session(session_id)

        directives = []
        now = datetime.now()

        for d in session.super_admin_directives:
            # Skip expired
            if d.expires_at and d.expires_at < now:
                continue

            # Filter by target
            if target and d.target not in ["all", target]:
                continue

            directives.append(d)

        return directives

    # -------------------------------------------------------------------------
    # AGENT MANAGEMENT
    # -------------------------------------------------------------------------

    async def register_agent(
        self,
        session_id: str,
        agent_id: str,
        agent_name: str,
        role: ParticipantRole,
        capabilities: List[str]
    ) -> AgentParticipation:
        """
        Registrer en agent i en session.

        Args:
            session_id: Session ID
            agent_id: Agent ID
            agent_name: Agent navn
            role: Agent rolle
            capabilities: Agent kapabiliteter

        Returns:
            AgentParticipation objekt
        """
        session = self._get_session(session_id)

        if len(session.active_agents) >= self.max_agents_per_session:
            raise ValueError(f"Max antal agenter ({self.max_agents_per_session}) nået")

        participation = AgentParticipation(
            agent_id=agent_id,
            agent_name=agent_name,
            role=role,
            capabilities=capabilities
        )

        if role == ParticipantRole.KOMMANDANT:
            session.active_kommandanter[agent_id] = participation
        else:
            session.active_agents[agent_id] = participation

        session.last_activity = datetime.now()

        self._log_audit("agent_registered", {
            "session_id": session_id,
            "agent_id": agent_id,
            "role": role.value
        })

        logger.info(f"Agent registreret: {agent_id} ({role.value}) i session {session_id}")
        return participation

    async def unregister_agent(
        self,
        session_id: str,
        agent_id: str
    ) -> bool:
        """Afregistrer en agent fra en session."""
        session = self._get_session(session_id)

        if agent_id in session.active_agents:
            del session.active_agents[agent_id]
        elif agent_id in session.active_kommandanter:
            del session.active_kommandanter[agent_id]
        else:
            return False

        session.last_activity = datetime.now()

        self._log_audit("agent_unregistered", {
            "session_id": session_id,
            "agent_id": agent_id
        })

        return True

    def get_agent_status(
        self,
        session_id: str,
        agent_id: str
    ) -> Optional[AgentParticipation]:
        """Hent status for en agent."""
        session = self._get_session(session_id)
        return session.active_agents.get(agent_id) or session.active_kommandanter.get(agent_id)

    # -------------------------------------------------------------------------
    # FEEDBACK & REPORTING
    # -------------------------------------------------------------------------

    async def generate_feedback_report(
        self,
        session_id: str
    ) -> FeedbackReport:
        """
        Generer en feedback rapport for en session.

        Args:
            session_id: Session ID

        Returns:
            FeedbackReport med aktuel status
        """
        session = self._get_session(session_id)

        # Calculate progress
        total_tasks = len(session.tasks)
        completed_tasks = len([t for t in session.tasks.values() if t.status == TaskStatus.COMPLETED])
        pending_tasks = len([t for t in session.tasks.values() if t.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]])

        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Count active agents
        active_agents = len([
            a for a in session.active_agents.values()
            if a.status == "working"
        ])

        # Identify issues
        issues = []
        failed_tasks = [t for t in session.tasks.values() if t.status == TaskStatus.FAILED]
        if failed_tasks:
            issues.append(f"{len(failed_tasks)} opgave(r) fejlet")

        if session.consumed_usd > session.budget_usd * 0.9:
            issues.append("Budget næsten opbrugt")

        # Generate recommendations
        recommendations = []
        if pending_tasks > active_agents * 3:
            recommendations.append("Overvej at tilføje flere agenter")

        report = FeedbackReport(
            report_id=f"fb_{secrets.token_hex(6)}",
            session_id=session_id,
            progress_percent=round(progress, 2),
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            active_agents=active_agents,
            issues=issues,
            recommendations=recommendations,
            resource_usage={
                "budget_used_percent": round(session.consumed_usd / session.budget_usd * 100, 2) if session.budget_usd > 0 else 0,
                "consumed_usd": session.consumed_usd,
                "budget_usd": session.budget_usd
            }
        )

        await self._emit_event("feedback_received", report)

        return report

    # -------------------------------------------------------------------------
    # CONTEXT & STATE
    # -------------------------------------------------------------------------

    async def update_shared_context(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Opdater delt kontekst."""
        session = self._get_session(session_id)
        session.shared_context[key] = value
        session.last_activity = datetime.now()
        return True

    async def get_shared_context(
        self,
        session_id: str,
        key: Optional[str] = None
    ) -> Any:
        """Hent delt kontekst."""
        session = self._get_session(session_id)
        if key:
            return session.shared_context.get(key)
        return session.shared_context.copy()

    async def add_result(
        self,
        session_id: str,
        result: TaskResult
    ) -> bool:
        """Tilføj et resultat til sessionen."""
        session = self._get_session(session_id)
        session.accumulated_results.append(result)
        session.last_activity = datetime.now()
        return True

    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------

    def on(self, event: str, handler: Callable) -> None:
        """Registrer en event handler."""
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)

    def off(self, event: str, handler: Callable) -> None:
        """Afregistrer en event handler."""
        if event in self._event_handlers and handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)

    async def _emit_event(self, event: str, data: Any) -> None:
        """Emit et event til alle handlers."""
        if event not in self._event_handlers:
            return

        for handler in self._event_handlers[event]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Event handler fejl for {event}: {e}")

    # -------------------------------------------------------------------------
    # METRICS & AUDIT
    # -------------------------------------------------------------------------

    def get_metrics(self) -> Dict[str, Any]:
        """Hent performance metrics."""
        return {
            **self._metrics,
            "active_sessions": len([s for s in self._sessions.values() if s.status == MastermindStatus.ACTIVE])
        }

    def get_audit_log(
        self,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Hent audit log."""
        logs = self._audit_log

        if session_id:
            logs = [l for l in logs if l.get("session_id") == session_id]

        return logs[-limit:]

    def _log_audit(self, action: str, details: Dict[str, Any]) -> None:
        """Log en audit entry."""
        if not self.enable_audit_logging:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            **details
        }
        self._audit_log.append(entry)

        # Keep only last 10000 entries
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-10000:]

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _get_session(self, session_id: str) -> MastermindSession:
        """Hent session med validation."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} findes ikke")
        return session

    def _update_avg_duration(self, new_duration: float) -> None:
        """Opdater gennemsnitlig session varighed."""
        total = self._metrics["completed_sessions"]
        current_avg = self._metrics["avg_session_duration"]

        if total == 1:
            self._metrics["avg_session_duration"] = new_duration
        else:
            # Running average
            self._metrics["avg_session_duration"] = (
                (current_avg * (total - 1) + new_duration) / total
            )


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_coordinator_instance: Optional[MastermindCoordinator] = None


def create_mastermind_coordinator(
    max_concurrent_sessions: int = 5,
    max_agents_per_session: int = 20,
    default_timeout_seconds: int = 3600,
    enable_audit_logging: bool = True
) -> MastermindCoordinator:
    """Opret en ny MastermindCoordinator instance."""
    global _coordinator_instance
    _coordinator_instance = MastermindCoordinator(
        max_concurrent_sessions=max_concurrent_sessions,
        max_agents_per_session=max_agents_per_session,
        default_timeout_seconds=default_timeout_seconds,
        enable_audit_logging=enable_audit_logging
    )
    return _coordinator_instance


def get_mastermind_coordinator() -> Optional[MastermindCoordinator]:
    """Hent den aktuelle MastermindCoordinator instance."""
    return _coordinator_instance
