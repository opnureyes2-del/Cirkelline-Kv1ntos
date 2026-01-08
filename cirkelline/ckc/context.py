"""
CKC Context Module - Standardiseret Kontekstobjekt-Struktur
===========================================================

Implementerer TaskContext som det centrale kontekstobjekt der følger
opgaver gennem hele work-loopen.

Features:
    - TaskContext: Rigt kontekstobjekt med metadata
    - WorkflowStep: Sporing af trin i work-loop
    - JSON-Schema validering
    - Kontekst-bevarelse og -overførsel
    - Audit trail for alle ændringer

Version: 1.0.0
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import uuid
import json
import copy

from cirkelline.config import logger


# ==============================================================================
# ENUMS
# ==============================================================================

class ContextValidationLevel(Enum):
    """Validerings niveau for kontekst."""
    STRICT = "strict"       # Alle felter skal være korrekte
    NORMAL = "normal"       # Standard validering
    LENIENT = "lenient"     # Minimal validering


class WorkflowStepStatus(Enum):
    """Status for et workflow-trin."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ContextSource(Enum):
    """Kilde til kontekst-ændring."""
    USER = "user"
    ORCHESTRATOR = "orchestrator"
    AGENT = "agent"
    SYSTEM = "system"
    HITL = "hitl"


# ==============================================================================
# JSON SCHEMAS
# ==============================================================================

TASK_CONTEXT_SCHEMA = {
    "type": "object",
    "required": ["context_id", "task_id", "created_at"],
    "properties": {
        "context_id": {"type": "string", "pattern": "^ctx_[a-f0-9]{12}$"},
        "task_id": {"type": "string"},
        "user_id": {"type": ["string", "null"]},
        "session_id": {"type": ["string", "null"]},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
        "source_platform": {"type": "string"},
        "original_prompt": {"type": "string"},
        "current_agent": {"type": ["string", "null"]},
        "workflow_steps": {"type": "array"},
        "accumulated_results": {"type": "object"},
        "metadata": {"type": "object"},
        "flags": {"type": "object"},
        "audit_trail": {"type": "array"}
    }
}

WORKFLOW_STEP_SCHEMA = {
    "type": "object",
    "required": ["step_id", "agent_id", "action", "status"],
    "properties": {
        "step_id": {"type": "string"},
        "agent_id": {"type": "string"},
        "action": {"type": "string"},
        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "failed", "skipped"]},
        "input_data": {"type": "object"},
        "output_data": {"type": ["object", "null"]},
        "started_at": {"type": ["string", "null"]},
        "completed_at": {"type": ["string", "null"]},
        "error": {"type": ["string", "null"]}
    }
}


# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class WorkflowStep:
    """
    Et enkelt trin i et workflow.

    Repræsenterer en agents handling på en opgave.
    """
    step_id: str
    agent_id: str
    action: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING

    # Data
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error handling
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, agent_id: str, action: str, input_data: Dict[str, Any] = None) -> 'WorkflowStep':
        """Factory metode til at oprette et nyt step."""
        return cls(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            agent_id=agent_id,
            action=action,
            input_data=input_data or {}
        )

    def start(self) -> None:
        """Marker step som startet."""
        self.status = WorkflowStepStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

    def complete(self, output_data: Dict[str, Any]) -> None:
        """Marker step som fuldført."""
        self.status = WorkflowStepStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.output_data = output_data

    def fail(self, error: str) -> None:
        """Marker step som fejlet."""
        self.status = WorkflowStepStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error

    def can_retry(self) -> bool:
        """Tjek om step kan prøves igen."""
        return self.retry_count < self.max_retries

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "status": self.status.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "retry_count": self.retry_count
        }


@dataclass
class AuditEntry:
    """En entry i audit trail."""
    timestamp: datetime
    source: ContextSource
    action: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "source": self.source.value,
            "action": action,
            "details": self.details
        }


@dataclass
class TaskContext:
    """
    Det centrale kontekstobjekt der følger opgaver gennem hele work-loopen.

    Dette objekt indeholder alle relevante metadata:
    - Opgave-ID og bruger-ID
    - Oprindelig prompt
    - Hidtidige resultater fra agenter
    - Agent-historik (hvilke agenter har behandlet)
    - Tidspunkter
    - Flag for menneskelig intervention (HITL)

    Kontekstobjektet følger opgaven fra start til slut.
    """

    # Identifikation
    context_id: str
    task_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Tidsstempling
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Kilde
    source_platform: str = "ckc"
    original_prompt: str = ""

    # Workflow state
    current_agent: Optional[str] = None
    workflow_steps: List[WorkflowStep] = field(default_factory=list)

    # Akkumulerede resultater fra agenter
    accumulated_results: Dict[str, Any] = field(default_factory=dict)

    # Metadata og flags
    metadata: Dict[str, Any] = field(default_factory=dict)
    flags: Dict[str, bool] = field(default_factory=lambda: {
        "requires_hitl": False,
        "is_urgent": False,
        "has_errors": False,
        "is_complete": False,
        "validation_required": True
    })

    # Audit trail
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    # Validation
    validation_level: ContextValidationLevel = ContextValidationLevel.NORMAL

    @classmethod
    def create(
        cls,
        task_id: str,
        user_id: Optional[str] = None,
        prompt: str = "",
        source_platform: str = "ckc"
    ) -> 'TaskContext':
        """Factory metode til at oprette en ny TaskContext."""
        context = cls(
            context_id=f"ctx_{uuid.uuid4().hex[:12]}",
            task_id=task_id,
            user_id=user_id,
            original_prompt=prompt,
            source_platform=source_platform
        )
        context._add_audit("context_created", ContextSource.SYSTEM, {
            "task_id": task_id,
            "user_id": user_id
        })
        return context

    def _add_audit(self, action: str, source: ContextSource, details: Dict[str, Any]) -> None:
        """Tilføj entry til audit trail."""
        self.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "source": source.value,
            "action": action,
            "details": details
        })
        self.updated_at = datetime.utcnow()

    def set_current_agent(self, agent_id: str) -> None:
        """Sæt den aktuelle agent."""
        previous = self.current_agent
        self.current_agent = agent_id
        self._add_audit("agent_changed", ContextSource.ORCHESTRATOR, {
            "from": previous,
            "to": agent_id
        })

    def add_workflow_step(self, step: WorkflowStep) -> None:
        """Tilføj et workflow step."""
        self.workflow_steps.append(step)
        self._add_audit("step_added", ContextSource.ORCHESTRATOR, {
            "step_id": step.step_id,
            "agent_id": step.agent_id,
            "action": step.action
        })

    def add_result(self, agent_id: str, result: Any) -> None:
        """Tilføj et resultat fra en agent."""
        self.accumulated_results[agent_id] = {
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._add_audit("result_added", ContextSource.AGENT, {
            "agent_id": agent_id,
            "result_type": type(result).__name__
        })

    def get_result(self, agent_id: str) -> Optional[Any]:
        """Hent resultat fra en specifik agent."""
        entry = self.accumulated_results.get(agent_id)
        return entry.get("result") if entry else None

    def set_flag(self, flag: str, value: bool, source: ContextSource = ContextSource.SYSTEM) -> None:
        """Sæt et flag."""
        self.flags[flag] = value
        self._add_audit("flag_set", source, {"flag": flag, "value": value})

    def require_hitl(self, reason: str) -> None:
        """Marker at HITL er påkrævet."""
        self.set_flag("requires_hitl", True, ContextSource.SYSTEM)
        self.metadata["hitl_reason"] = reason

    def mark_complete(self) -> None:
        """Marker kontekst som fuldført."""
        self.set_flag("is_complete", True, ContextSource.SYSTEM)

    def mark_error(self, error: str) -> None:
        """Marker at der er sket en fejl."""
        self.set_flag("has_errors", True, ContextSource.SYSTEM)
        if "errors" not in self.metadata:
            self.metadata["errors"] = []
        self.metadata["errors"].append({
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_completed_steps(self) -> List[WorkflowStep]:
        """Hent alle fuldførte steps."""
        return [s for s in self.workflow_steps if s.status == WorkflowStepStatus.COMPLETED]

    def get_pending_steps(self) -> List[WorkflowStep]:
        """Hent alle ventende steps."""
        return [s for s in self.workflow_steps if s.status == WorkflowStepStatus.PENDING]

    def clone_for_agent(self, agent_id: str) -> 'TaskContext':
        """
        Lav en klon af kontekst til en specifik agent.

        Klonen har samme data men kan modificeres uden at påvirke originalen.
        """
        clone = copy.deepcopy(self)
        clone.set_current_agent(agent_id)
        return clone

    def merge_from(self, other: 'TaskContext') -> None:
        """
        Merge resultater fra en anden kontekst.

        Bruges når en agent returnerer sin modificerede kontekst.
        """
        # Merge results
        for agent_id, result in other.accumulated_results.items():
            if agent_id not in self.accumulated_results:
                self.accumulated_results[agent_id] = result

        # Merge workflow steps
        existing_ids = {s.step_id for s in self.workflow_steps}
        for step in other.workflow_steps:
            if step.step_id not in existing_ids:
                self.workflow_steps.append(step)
            else:
                # Update existing step
                for i, s in enumerate(self.workflow_steps):
                    if s.step_id == step.step_id:
                        self.workflow_steps[i] = step
                        break

        # Merge flags (other's True flags take precedence)
        for flag, value in other.flags.items():
            if value:
                self.flags[flag] = True

        self._add_audit("context_merged", ContextSource.SYSTEM, {
            "from_context": other.context_id
        })

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validér konteksten mod JSON-schema.

        Returns:
            Tuple af (is_valid, list of errors)
        """
        errors = []

        # Required fields
        if not self.context_id:
            errors.append("context_id is required")
        if not self.task_id:
            errors.append("task_id is required")

        # Format validation
        if not self.context_id.startswith("ctx_"):
            errors.append("context_id must start with 'ctx_'")

        # Workflow steps validation
        for step in self.workflow_steps:
            if not step.step_id or not step.agent_id:
                errors.append(f"Invalid workflow step: {step.step_id}")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary (JSON-serialiserbar)."""
        return {
            "context_id": self.context_id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source_platform": self.source_platform,
            "original_prompt": self.original_prompt,
            "current_agent": self.current_agent,
            "workflow_steps": [s.to_dict() for s in self.workflow_steps],
            "accumulated_results": self.accumulated_results,
            "metadata": self.metadata,
            "flags": self.flags,
            "audit_trail": self.audit_trail
        }

    def to_json(self) -> str:
        """Konverter til JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskContext':
        """Opret TaskContext fra dictionary."""
        context = cls(
            context_id=data["context_id"],
            task_id=data["task_id"],
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            source_platform=data.get("source_platform", "ckc"),
            original_prompt=data.get("original_prompt", "")
        )

        # Parse datetimes
        if "created_at" in data:
            context.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            context.updated_at = datetime.fromisoformat(data["updated_at"])

        # Parse workflow steps
        for step_data in data.get("workflow_steps", []):
            step = WorkflowStep(
                step_id=step_data["step_id"],
                agent_id=step_data["agent_id"],
                action=step_data["action"],
                status=WorkflowStepStatus(step_data["status"]),
                input_data=step_data.get("input_data", {}),
                output_data=step_data.get("output_data")
            )
            if step_data.get("started_at"):
                step.started_at = datetime.fromisoformat(step_data["started_at"])
            if step_data.get("completed_at"):
                step.completed_at = datetime.fromisoformat(step_data["completed_at"])
            step.error = step_data.get("error")
            context.workflow_steps.append(step)

        context.accumulated_results = data.get("accumulated_results", {})
        context.metadata = data.get("metadata", {})
        context.flags = data.get("flags", context.flags)
        context.audit_trail = data.get("audit_trail", [])
        context.current_agent = data.get("current_agent")

        return context

    @classmethod
    def from_json(cls, json_str: str) -> 'TaskContext':
        """Opret TaskContext fra JSON string."""
        return cls.from_dict(json.loads(json_str))


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def validate_context_schema(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validér data mod TaskContext JSON-schema.

    Simpel implementation uden ekstern dependency.
    """
    errors = []

    # Check required fields
    for field in TASK_CONTEXT_SCHEMA["required"]:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Type checking for key fields
    if "context_id" in data and not isinstance(data["context_id"], str):
        errors.append("context_id must be a string")

    if "task_id" in data and not isinstance(data["task_id"], str):
        errors.append("task_id must be a string")

    if "workflow_steps" in data and not isinstance(data["workflow_steps"], list):
        errors.append("workflow_steps must be an array")

    if "accumulated_results" in data and not isinstance(data["accumulated_results"], dict):
        errors.append("accumulated_results must be an object")

    return len(errors) == 0, errors


def create_context_for_task(
    task_id: str,
    prompt: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    source_platform: str = "ckc"
) -> TaskContext:
    """
    Convenience function til at oprette en ny TaskContext.
    """
    context = TaskContext.create(
        task_id=task_id,
        user_id=user_id,
        prompt=prompt,
        source_platform=source_platform
    )
    context.session_id = session_id
    return context


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Enums
    "ContextValidationLevel",
    "WorkflowStepStatus",
    "ContextSource",
    # Data classes
    "WorkflowStep",
    "TaskContext",
    "AuditEntry",
    # Schemas
    "TASK_CONTEXT_SCHEMA",
    "WORKFLOW_STEP_SCHEMA",
    # Functions
    "validate_context_schema",
    "create_context_for_task",
]
