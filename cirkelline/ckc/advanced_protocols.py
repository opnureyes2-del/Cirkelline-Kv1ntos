"""
CKC Avancerede Operative Protokoller
=====================================

Implementerer TILFØJELSE TIL DEN ULTIMATIVE DEFINITIVE MANDAT:

5.1 - Dynamisk Sikkerhedsjustering i Læringsrum
5.2 - ILCP: Inter-Læringsrum Kommunikationsprotokoller
5.3 - CKC Super-Admin Terminal & External Implementation Access Protocol (EIAP)

Kerneprincipper:
- Kompromisløs komplethed og fejlfri præcision
- Dynamisk, selvoptimerende læringsrums-økosystem
- Central styring med strenge sikkerhedsprotokoller
- HITL-godkendelse for alle kritiske handlinger
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Tuple, Union
from enum import Enum
import asyncio
import uuid
import hashlib
import secrets
import json
from collections import defaultdict

from cirkelline.config import logger


# Forward reference for TaskContext (imported lazily to avoid circular imports)
TaskContext = None

def _get_task_context():
    """Lazy import of TaskContext to avoid circular imports."""
    global TaskContext
    if TaskContext is None:
        from .context import TaskContext as TC
        TaskContext = TC
    return TaskContext


# ═══════════════════════════════════════════════════════════════
# 5.1 DYNAMISK SIKKERHEDSJUSTERING
# ═══════════════════════════════════════════════════════════════

class SecurityLevel(Enum):
    """Sikkerhedsniveauer for læringsrum."""
    HIGH = "high"           # Fuld sikkerhed, alle checks
    MODERATE = "moderate"   # Reducerede checks, monitorering aktiv
    LIGHT = "light"         # Minimal sikkerhed, kontinuerlig overvågning
    LOCKDOWN = "lockdown"   # Nødsituation, alle operationer standses


@dataclass
class SecurityProfile:
    """En sikkerhedsprofil der definerer sikkerhedsindstillinger."""
    level: SecurityLevel
    validation_frequency: int  # Sekunder mellem valideringer
    require_double_check: bool
    allow_auto_approve: bool
    max_operations_per_minute: int
    sandbox_required: bool
    audit_level: str  # minimal, standard, full
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "validation_frequency": self.validation_frequency,
            "require_double_check": self.require_double_check,
            "allow_auto_approve": self.allow_auto_approve,
            "max_operations_per_minute": self.max_operations_per_minute,
            "sandbox_required": self.sandbox_required,
            "audit_level": self.audit_level,
            "description": self.description
        }


# Predefinerede sikkerhedsprofiler
SECURITY_PROFILES = {
    SecurityLevel.HIGH: SecurityProfile(
        level=SecurityLevel.HIGH,
        validation_frequency=10,
        require_double_check=True,
        allow_auto_approve=False,
        max_operations_per_minute=10,
        sandbox_required=True,
        audit_level="full",
        description="Fuld sikkerhed - alle operationer valideres og logges"
    ),
    SecurityLevel.MODERATE: SecurityProfile(
        level=SecurityLevel.MODERATE,
        validation_frequency=30,
        require_double_check=False,
        allow_auto_approve=True,  # For low-risk operations
        max_operations_per_minute=30,
        sandbox_required=False,
        audit_level="standard",
        description="Moderat sikkerhed - rutineoperationer auto-godkendes"
    ),
    SecurityLevel.LIGHT: SecurityProfile(
        level=SecurityLevel.LIGHT,
        validation_frequency=60,
        require_double_check=False,
        allow_auto_approve=True,
        max_operations_per_minute=100,
        sandbox_required=False,
        audit_level="minimal",
        description="Let sikkerhed - højt tillidsoptimeret drift"
    ),
    SecurityLevel.LOCKDOWN: SecurityProfile(
        level=SecurityLevel.LOCKDOWN,
        validation_frequency=1,
        require_double_check=True,
        allow_auto_approve=False,
        max_operations_per_minute=0,
        sandbox_required=True,
        audit_level="full",
        description="Nødstop - alle operationer blokeret"
    )
}


@dataclass
class RoomSecurityState:
    """Sikkerhedstilstand for et læringsrum."""
    room_id: int
    current_level: SecurityLevel
    error_free_since: datetime
    total_error_free_hours: float
    last_error: Optional[datetime]
    error_count_last_24h: int
    operations_count: int
    last_security_check: datetime
    eligible_for_reduction: bool = False
    reduction_blocked_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "current_level": self.current_level.value,
            "error_free_since": self.error_free_since.isoformat(),
            "total_error_free_hours": self.total_error_free_hours,
            "last_error": self.last_error.isoformat() if self.last_error else None,
            "error_count_last_24h": self.error_count_last_24h,
            "operations_count": self.operations_count,
            "eligible_for_reduction": self.eligible_for_reduction,
            "reduction_blocked_reason": self.reduction_blocked_reason
        }


class DynamicSecurityManager:
    """
    Manager for dynamisk sikkerhedsjustering.

    Protokol: 72 timers fejlfri drift -> gradvis sikkerhedsreduktion
    Fail-safe: Ved mindste fejl -> øjeblikkelig tilbagerulning
    """

    # Konstanter
    ERROR_FREE_HOURS_FOR_REDUCTION = 72  # 72 timer fejlfri drift kræves
    SECURITY_CHECK_INTERVAL = 300  # 5 minutter mellem checks

    def __init__(self):
        self._room_states: Dict[int, RoomSecurityState] = {}
        self._error_log: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self._reduction_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

        logger.info("DynamicSecurityManager initialized")

    async def register_room(
        self,
        room_id: int,
        initial_level: SecurityLevel = SecurityLevel.HIGH
    ) -> RoomSecurityState:
        """Registrer et læringsrum for sikkerhedsovervågning."""
        now = datetime.utcnow()

        state = RoomSecurityState(
            room_id=room_id,
            current_level=initial_level,
            error_free_since=now,
            total_error_free_hours=0.0,
            last_error=None,
            error_count_last_24h=0,
            operations_count=0,
            last_security_check=now
        )

        self._room_states[room_id] = state
        logger.info(f"Room {room_id} registered with security level: {initial_level.value}")
        return state

    async def record_operation(
        self,
        room_id: int,
        success: bool,
        operation_type: str = "standard"
    ) -> None:
        """Registrer en operation og opdater sikkerhedstilstand."""
        async with self._lock:
            state = self._room_states.get(room_id)
            if not state:
                return

            state.operations_count += 1
            now = datetime.utcnow()

            if success:
                # Update error-free time
                hours_since_start = (now - state.error_free_since).total_seconds() / 3600
                state.total_error_free_hours = hours_since_start
            else:
                # FEJL DETEKTERET - FAIL-SAFE AKTIVERES
                await self._handle_error(state, operation_type)

    async def _handle_error(
        self,
        state: RoomSecurityState,
        operation_type: str
    ) -> None:
        """Håndter fejl - fail-safe tilbagerulning."""
        now = datetime.utcnow()

        # Log fejlen
        error_entry = {
            "timestamp": now.isoformat(),
            "operation_type": operation_type,
            "security_level_at_error": state.current_level.value
        }
        self._error_log[state.room_id].append(error_entry)

        # Opdater state
        state.last_error = now
        state.error_count_last_24h += 1
        state.error_free_since = now
        state.total_error_free_hours = 0.0
        state.eligible_for_reduction = False

        # FAIL-SAFE: Øjeblikkelig tilbagerulning til HIGH sikkerhed
        if state.current_level != SecurityLevel.HIGH:
            old_level = state.current_level
            state.current_level = SecurityLevel.HIGH

            self._reduction_history.append({
                "room_id": state.room_id,
                "action": "rollback",
                "from_level": old_level.value,
                "to_level": SecurityLevel.HIGH.value,
                "reason": "Error detected - fail-safe activated",
                "timestamp": now.isoformat()
            })

            logger.warning(
                f"FAIL-SAFE: Room {state.room_id} security rolled back from "
                f"{old_level.value} to HIGH due to error"
            )

    async def check_reduction_eligibility(
        self,
        room_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Check om et rum er berettiget til sikkerhedsreduktion."""
        state = self._room_states.get(room_id)
        if not state:
            return False, "Room not registered"

        now = datetime.utcnow()

        # Check fejlfri tid
        if state.total_error_free_hours < self.ERROR_FREE_HOURS_FOR_REDUCTION:
            remaining = self.ERROR_FREE_HOURS_FOR_REDUCTION - state.total_error_free_hours
            return False, f"Need {remaining:.1f} more error-free hours"

        # Check om allerede på laveste niveau
        if state.current_level == SecurityLevel.LIGHT:
            return False, "Already at minimum security level"

        # Check fejl i seneste 24 timer
        cutoff = now - timedelta(hours=24)
        recent_errors = [
            e for e in self._error_log.get(room_id, [])
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]
        if recent_errors:
            return False, f"{len(recent_errors)} errors in last 24 hours"

        state.eligible_for_reduction = True
        state.reduction_blocked_reason = None
        return True, None

    async def reduce_security(
        self,
        room_id: int,
        approved_by: str
    ) -> bool:
        """Reducer sikkerhedsniveau trinvist."""
        async with self._lock:
            eligible, reason = await self.check_reduction_eligibility(room_id)
            if not eligible:
                logger.warning(f"Security reduction blocked for room {room_id}: {reason}")
                return False

            state = self._room_states[room_id]
            now = datetime.utcnow()

            # Trinvis reduktion
            level_order = [SecurityLevel.HIGH, SecurityLevel.MODERATE, SecurityLevel.LIGHT]
            current_idx = level_order.index(state.current_level)

            if current_idx >= len(level_order) - 1:
                return False

            new_level = level_order[current_idx + 1]
            old_level = state.current_level
            state.current_level = new_level

            # Reset error-free counter for næste niveau
            state.error_free_since = now
            state.total_error_free_hours = 0.0
            state.eligible_for_reduction = False

            self._reduction_history.append({
                "room_id": room_id,
                "action": "reduce",
                "from_level": old_level.value,
                "to_level": new_level.value,
                "approved_by": approved_by,
                "timestamp": now.isoformat()
            })

            logger.info(
                f"Security reduced for room {room_id}: "
                f"{old_level.value} -> {new_level.value} (approved by {approved_by})"
            )
            return True

    async def get_room_security(self, room_id: int) -> Optional[Dict[str, Any]]:
        """Hent sikkerhedstilstand for et rum."""
        state = self._room_states.get(room_id)
        if not state:
            return None

        profile = SECURITY_PROFILES.get(state.current_level)

        return {
            "state": state.to_dict(),
            "profile": profile.to_dict() if profile else None,
            "error_log_count": len(self._error_log.get(room_id, []))
        }

    async def get_all_room_security(self) -> List[Dict[str, Any]]:
        """Hent sikkerhedstilstand for alle rum."""
        results = []
        for room_id in self._room_states:
            security = await self.get_room_security(room_id)
            if security:
                results.append(security)
        return results


# ═══════════════════════════════════════════════════════════════
# 5.2 ILCP - INTER-LÆRINGSRUM KOMMUNIKATION
# ═══════════════════════════════════════════════════════════════

# JSON Schemas for ILCP Message Validation
ILCP_MESSAGE_SCHEMA = {
    "type": "object",
    "required": ["type"],
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "data_request", "data_response", "assistance_request",
                "assistance_offer", "status_update", "knowledge_share",
                "resource_request", "error_notification"
            ]
        },
        "payload": {"type": "object"},
        "task_context": {"type": ["object", "null"]},
        "validation_level": {
            "type": "string",
            "enum": ["strict", "normal", "lenient"],
            "default": "normal"
        }
    }
}

ILCP_DATA_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["request_type", "data_keys"],
    "properties": {
        "request_type": {"type": "string"},
        "data_keys": {"type": "array", "items": {"type": "string"}},
        "filters": {"type": "object"},
        "urgency": {"type": "string", "enum": ["emergency", "high", "normal", "low"]}
    }
}

ILCP_DATA_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["request_id", "success"],
    "properties": {
        "request_id": {"type": "string"},
        "success": {"type": "boolean"},
        "data": {"type": "object"},
        "error": {"type": ["string", "null"]}
    }
}

ILCP_KNOWLEDGE_SHARE_SCHEMA = {
    "type": "object",
    "required": ["knowledge_type", "content"],
    "properties": {
        "knowledge_type": {
            "type": "string",
            "enum": ["finding", "insight", "correction", "update", "warning"]
        },
        "content": {"type": "object"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "source_agent": {"type": "string"}
    }
}


class ValidationMode(Enum):
    """Validation mode for ILCP messages."""
    STRICT = "strict"       # All fields must validate
    NORMAL = "normal"       # Standard validation
    LENIENT = "lenient"     # Minimal validation, only required fields
    DISABLED = "disabled"   # No validation (for backwards compatibility)


class MessagePriority(Enum):
    """Prioritet for ILCP beskeder."""
    EMERGENCY = 1   # Akut - afbryder alt
    HIGH = 2        # Høj prioritet
    NORMAL = 3      # Standard
    LOW = 4         # Lav - kan vente


class MessageType(Enum):
    """Typer af ILCP beskeder."""
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    ASSISTANCE_REQUEST = "assistance_request"
    ASSISTANCE_OFFER = "assistance_offer"
    STATUS_UPDATE = "status_update"
    KNOWLEDGE_SHARE = "knowledge_share"
    RESOURCE_REQUEST = "resource_request"
    ERROR_NOTIFICATION = "error_notification"


@dataclass
class ILCPMessage:
    """
    En ILCP besked mellem læringsrum.

    Understøtter nu:
    - JSON-schema validering af content
    - TaskContext integration for work-loop tracking
    - Validation mode for fleksibel validering
    """
    id: str
    message_type: MessageType
    priority: MessagePriority
    sender_room_id: int
    recipient_room_id: int
    content: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    encrypted: bool = True
    requires_ack: bool = True
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # New: TaskContext support (v1.1.0)
    task_context_data: Optional[Dict[str, Any]] = None
    validation_mode: ValidationMode = ValidationMode.NORMAL
    validation_errors: List[str] = field(default_factory=list)
    is_validated: bool = False

    def attach_context(self, context: Any) -> None:
        """
        Attach a TaskContext to this message.

        Args:
            context: TaskContext instance or dict
        """
        if hasattr(context, 'to_dict'):
            self.task_context_data = context.to_dict()
        elif isinstance(context, dict):
            self.task_context_data = context
        else:
            raise ValueError("Context must be TaskContext instance or dict")

        self.metadata["has_context"] = True
        self.metadata["context_id"] = self.task_context_data.get("context_id")

    def get_context(self) -> Optional[Any]:
        """
        Get attached TaskContext.

        Returns:
            TaskContext instance if attached, None otherwise
        """
        if not self.task_context_data:
            return None

        TC = _get_task_context()
        return TC.from_dict(self.task_context_data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_type": self.message_type.value,
            "priority": self.priority.name,
            "sender_room_id": self.sender_room_id,
            "recipient_room_id": self.recipient_room_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "encrypted": self.encrypted,
            "requires_ack": self.requires_ack,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "metadata": self.metadata,
            "task_context": self.task_context_data,
            "validation_mode": self.validation_mode.value,
            "is_validated": self.is_validated,
            "validation_errors": self.validation_errors
        }


@dataclass
class AssistanceRequest:
    """En anmodning om assistance fra et andet læringsrum."""
    id: str
    requester_room_id: int
    task_description: str
    required_capabilities: Set[str]
    urgency: MessagePriority
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_room_id: Optional[int] = None
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    result: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "requester_room_id": self.requester_room_id,
            "task_description": self.task_description,
            "required_capabilities": list(self.required_capabilities),
            "urgency": self.urgency.name,
            "created_at": self.created_at.isoformat(),
            "assigned_room_id": self.assigned_room_id,
            "status": self.status
        }


class ILCPManager:
    """
    Inter-Læringsrum Kommunikationsprotokol Manager.

    Håndterer:
    - Peer-to-peer kommunikation mellem læringsrum
    - Assistance requests og routing
    - Videnudveksling
    - Kommandant-orkestrering af alle beskeder

    Nye features (v1.1.0):
    - JSON-schema validering af message content
    - TaskContext integration for work-loop tracking
    - Configurable validation modes
    """

    # Schema mapping for message types
    MESSAGE_SCHEMAS: Dict[MessageType, Dict[str, Any]] = {
        MessageType.DATA_REQUEST: ILCP_DATA_REQUEST_SCHEMA,
        MessageType.DATA_RESPONSE: ILCP_DATA_RESPONSE_SCHEMA,
        MessageType.KNOWLEDGE_SHARE: ILCP_KNOWLEDGE_SHARE_SCHEMA,
    }

    def __init__(self, default_validation_mode: ValidationMode = ValidationMode.NORMAL):
        self._messages: Dict[str, ILCPMessage] = {}
        self._message_queue: Dict[int, List[str]] = defaultdict(list)  # room_id -> message_ids
        self._assistance_requests: Dict[str, AssistanceRequest] = {}
        self._room_capabilities: Dict[int, Set[str]] = {}
        self._message_log: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

        # Validation settings (v1.1.0)
        self._default_validation_mode = default_validation_mode
        self._validation_stats = {
            "total_validated": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }

        logger.info(f"ILCPManager initialized with validation mode: {default_validation_mode.value}")

    async def register_room_capabilities(
        self,
        room_id: int,
        capabilities: Set[str]
    ) -> None:
        """Registrer et læringsrums kapabiliteter."""
        self._room_capabilities[room_id] = capabilities
        logger.debug(f"Room {room_id} capabilities registered: {capabilities}")

    # ═══════════════════════════════════════════════════════════
    # VALIDATION METHODS (v1.1.0)
    # ═══════════════════════════════════════════════════════════

    def _validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        mode: ValidationMode
    ) -> Tuple[bool, List[str]]:
        """
        Validate data against a JSON schema.

        Simple implementation without external dependency.

        Args:
            data: The data to validate
            schema: The JSON schema
            mode: Validation mode (strict, normal, lenient)

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        if mode == ValidationMode.DISABLED:
            return True, []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if mode == ValidationMode.LENIENT:
            # Only check required fields
            return len(errors) == 0, errors

        # Type checking for properties
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field not in data:
                continue

            value = data[field]
            expected_type = field_schema.get("type")

            if expected_type:
                if not self._check_type(value, expected_type):
                    errors.append(f"Field '{field}' has wrong type: expected {expected_type}")

            # Enum validation
            if "enum" in field_schema:
                if value not in field_schema["enum"]:
                    errors.append(f"Field '{field}' value '{value}' not in allowed values")

            # Range validation for numbers
            if expected_type == "number" and isinstance(value, (int, float)):
                if "minimum" in field_schema and value < field_schema["minimum"]:
                    errors.append(f"Field '{field}' value {value} below minimum {field_schema['minimum']}")
                if "maximum" in field_schema and value > field_schema["maximum"]:
                    errors.append(f"Field '{field}' value {value} above maximum {field_schema['maximum']}")

        if mode == ValidationMode.STRICT:
            # Check for unknown fields
            allowed_fields = set(properties.keys())
            for field in data.keys():
                if field not in allowed_fields and allowed_fields:
                    errors.append(f"Unknown field: {field}")

        return len(errors) == 0, errors

    def _check_type(self, value: Any, expected_type: Union[str, List[str]]) -> bool:
        """Check if value matches expected type(s)."""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }

        if isinstance(expected_type, list):
            # Multiple allowed types
            return any(self._check_type(value, t) for t in expected_type)

        if expected_type not in type_mapping:
            return True  # Unknown type, accept

        return isinstance(value, type_mapping[expected_type])

    async def validate_message_content(
        self,
        message_type: MessageType,
        content: Any,
        mode: Optional[ValidationMode] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate message content against schema for its type.

        Args:
            message_type: Type of ILCP message
            content: Content to validate
            mode: Validation mode (uses default if not specified)

        Returns:
            Tuple of (is_valid, list of errors)
        """
        validation_mode = mode or self._default_validation_mode

        if validation_mode == ValidationMode.DISABLED:
            self._validation_stats["skipped"] += 1
            return True, []

        self._validation_stats["total_validated"] += 1

        # Get schema for message type
        schema = self.MESSAGE_SCHEMAS.get(message_type)
        if not schema:
            # No schema defined, accept any content
            self._validation_stats["passed"] += 1
            return True, []

        # Convert content to dict if possible
        if isinstance(content, dict):
            data = content
        elif hasattr(content, 'to_dict'):
            data = content.to_dict()
        else:
            self._validation_stats["failed"] += 1
            return False, ["Content must be dict or have to_dict() method"]

        is_valid, errors = self._validate_against_schema(data, schema, validation_mode)

        if is_valid:
            self._validation_stats["passed"] += 1
        else:
            self._validation_stats["failed"] += 1
            logger.warning(f"ILCP validation failed for {message_type.value}: {errors}")

        return is_valid, errors

    def set_validation_mode(self, mode: ValidationMode) -> None:
        """Set the default validation mode."""
        self._default_validation_mode = mode
        logger.info(f"ILCP validation mode set to: {mode.value}")

    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            **self._validation_stats,
            "default_mode": self._default_validation_mode.value
        }

    # ═══════════════════════════════════════════════════════════
    # MESSAGE OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def send_message(
        self,
        sender_room_id: int,
        recipient_room_id: int,
        message_type: MessageType,
        content: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        task_context: Optional[Any] = None,
        validation_mode: Optional[ValidationMode] = None,
        validate: bool = True
    ) -> ILCPMessage:
        """
        Send en ILCP besked med valgfri validering og TaskContext.

        Args:
            sender_room_id: ID på afsender-læringsrum
            recipient_room_id: ID på modtager-læringsrum
            message_type: Type af besked
            content: Beskedens indhold
            priority: Prioritet (default: NORMAL)
            metadata: Ekstra metadata
            task_context: Optional TaskContext at vedhæfte
            validation_mode: Valideringsmode (bruger default hvis ikke angivet)
            validate: Om content skal valideres (default: True)

        Returns:
            ILCPMessage objektet

        Raises:
            ValueError: Hvis validering fejler i STRICT mode
        """
        async with self._lock:
            message_id = f"ilcp_{uuid.uuid4().hex[:12]}"
            effective_mode = validation_mode or self._default_validation_mode
            validation_errors = []

            # Validate content if enabled
            if validate and effective_mode != ValidationMode.DISABLED:
                is_valid, validation_errors = await self.validate_message_content(
                    message_type, content, effective_mode
                )

                if not is_valid and effective_mode == ValidationMode.STRICT:
                    raise ValueError(f"ILCP validation failed: {validation_errors}")

            message = ILCPMessage(
                id=message_id,
                message_type=message_type,
                priority=priority,
                sender_room_id=sender_room_id,
                recipient_room_id=recipient_room_id,
                content=content,
                metadata=metadata or {},
                validation_mode=effective_mode,
                validation_errors=validation_errors,
                is_validated=validate
            )

            # Attach TaskContext if provided
            if task_context is not None:
                message.attach_context(task_context)

            self._messages[message_id] = message
            self._message_queue[recipient_room_id].append(message_id)

            # Log for audit
            self._message_log.append({
                "message_id": message_id,
                "type": message_type.value,
                "sender": sender_room_id,
                "recipient": recipient_room_id,
                "priority": priority.name,
                "timestamp": message.timestamp.isoformat(),
                "validated": validate,
                "validation_passed": len(validation_errors) == 0,
                "has_context": task_context is not None
            })

            logger.debug(
                f"ILCP message sent: {message_type.value} from room {sender_room_id} "
                f"to room {recipient_room_id} (validated={validate}, context={task_context is not None})"
            )
            return message

    async def send_message_with_context(
        self,
        sender_room_id: int,
        recipient_room_id: int,
        message_type: MessageType,
        content: Any,
        task_context: Any,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> ILCPMessage:
        """
        Convenience method til at sende besked med TaskContext.

        Wrapper omkring send_message der sikrer TaskContext er vedhæftet.
        """
        return await self.send_message(
            sender_room_id=sender_room_id,
            recipient_room_id=recipient_room_id,
            message_type=message_type,
            content=content,
            priority=priority,
            task_context=task_context,
            validate=True
        )

    async def get_messages_for_room(
        self,
        room_id: int,
        unacknowledged_only: bool = True
    ) -> List[ILCPMessage]:
        """Hent beskeder til et læringsrum."""
        message_ids = self._message_queue.get(room_id, [])
        messages = [self._messages[mid] for mid in message_ids if mid in self._messages]

        if unacknowledged_only:
            messages = [m for m in messages if not m.acknowledged]

        # Sort by priority and timestamp
        messages.sort(key=lambda m: (m.priority.value, m.timestamp))
        return messages

    async def acknowledge_message(
        self,
        message_id: str,
        room_id: int
    ) -> bool:
        """Kvitter for en besked."""
        message = self._messages.get(message_id)
        if not message or message.recipient_room_id != room_id:
            return False

        message.acknowledged = True
        message.acknowledged_at = datetime.utcnow()
        return True

    async def request_assistance(
        self,
        requester_room_id: int,
        task_description: str,
        required_capabilities: Set[str],
        urgency: MessagePriority = MessagePriority.NORMAL
    ) -> AssistanceRequest:
        """Anmod om assistance fra et andet læringsrum."""
        request_id = f"assist_{uuid.uuid4().hex[:8]}"

        request = AssistanceRequest(
            id=request_id,
            requester_room_id=requester_room_id,
            task_description=task_description,
            required_capabilities=required_capabilities,
            urgency=urgency
        )

        self._assistance_requests[request_id] = request

        # Find passende rum
        best_room = await self._find_capable_room(required_capabilities, requester_room_id)

        if best_room:
            request.assigned_room_id = best_room
            request.status = "assigned"

            # Send besked til det assignede rum
            await self.send_message(
                sender_room_id=requester_room_id,
                recipient_room_id=best_room,
                message_type=MessageType.ASSISTANCE_REQUEST,
                content={
                    "request_id": request_id,
                    "task": task_description,
                    "capabilities_needed": list(required_capabilities)
                },
                priority=urgency
            )

        logger.info(
            f"Assistance request {request_id} from room {requester_room_id}: "
            f"{'assigned to room ' + str(best_room) if best_room else 'no capable room found'}"
        )
        return request

    async def _find_capable_room(
        self,
        required_capabilities: Set[str],
        exclude_room: int
    ) -> Optional[int]:
        """Find et læringsrum med de nødvendige kapabiliteter."""
        for room_id, capabilities in self._room_capabilities.items():
            if room_id == exclude_room:
                continue
            if required_capabilities.issubset(capabilities):
                return room_id
        return None

    async def complete_assistance(
        self,
        request_id: str,
        result: Any,
        success: bool = True
    ) -> bool:
        """Fuldfør en assistance request."""
        request = self._assistance_requests.get(request_id)
        if not request:
            return False

        request.status = "completed" if success else "failed"
        request.result = result

        # Send resultat tilbage til requester
        if request.assigned_room_id:
            await self.send_message(
                sender_room_id=request.assigned_room_id,
                recipient_room_id=request.requester_room_id,
                message_type=MessageType.DATA_RESPONSE,
                content={
                    "request_id": request_id,
                    "success": success,
                    "result": result
                },
                priority=request.urgency
            )

        return True

    async def get_communication_stats(self) -> Dict[str, Any]:
        """Hent kommunikationsstatistik."""
        return {
            "total_messages": len(self._messages),
            "pending_messages": sum(
                1 for m in self._messages.values()
                if not m.acknowledged
            ),
            "active_assistance_requests": sum(
                1 for r in self._assistance_requests.values()
                if r.status in ["pending", "assigned", "in_progress"]
            ),
            "registered_rooms": len(self._room_capabilities),
            "message_log_size": len(self._message_log)
        }


# ═══════════════════════════════════════════════════════════════
# 5.3 CKC SUPER-ADMIN TERMINAL & EIAP
# ═══════════════════════════════════════════════════════════════

class AuthorizationLevel(Enum):
    """Autorisationsniveauer for ekstern adgang."""
    NONE = 0        # Ingen adgang
    READ_ONLY = 1   # Kun læseadgang
    LIMITED = 2     # Begrænset skrive
    STANDARD = 3    # Standard adgang
    ELEVATED = 4    # Udvidet adgang
    ADMIN = 5       # Fuld admin


@dataclass
class ExternalEntity:
    """En ekstern enhed der kan få adgang til CKC."""
    entity_id: str
    name: str
    entity_type: str  # ai_model, developer_tool, api_client
    authorization_level: AuthorizationLevel
    allowed_rooms: Set[int]  # Hvilke læringsrum enheden kan tilgå
    allowed_actions: Set[str]  # Tilladte handlinger
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_access: Optional[datetime] = None
    access_count: int = 0
    api_key_hash: Optional[str] = None
    is_active: bool = True
    sandbox_only: bool = True  # Default: kun sandbox adgang

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type,
            "authorization_level": self.authorization_level.name,
            "allowed_rooms": list(self.allowed_rooms),
            "allowed_actions": list(self.allowed_actions),
            "created_at": self.created_at.isoformat(),
            "last_access": self.last_access.isoformat() if self.last_access else None,
            "access_count": self.access_count,
            "is_active": self.is_active,
            "sandbox_only": self.sandbox_only
        }


@dataclass
class HITLApprovalRequest:
    """En anmodning om Human-in-the-Loop godkendelse."""
    id: str
    action_type: str
    description: str
    requested_by: str  # entity_id
    target_resource: str
    risk_level: str  # low, medium, high, critical
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
    status: str = "pending"  # pending, approved, rejected, expired
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    execution_log: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type,
            "description": self.description,
            "requested_by": self.requested_by,
            "target_resource": self.target_resource,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None
        }


@dataclass
class AuditLogEntry:
    """En entry i audit loggen."""
    id: str
    timestamp: datetime
    entity_id: str
    action: str
    target: str
    result: str  # success, failure, blocked
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "entity_id": self.entity_id,
            "action": self.action,
            "target": self.target,
            "result": self.result,
            "details": self.details,
            "ip_address": self.ip_address,
            "session_id": self.session_id
        }


class CKCSuperAdminTerminal:
    """
    CKC Super-Admin Terminal

    Central hub for:
    - Systemkonfiguration
    - Agentledelse
    - Ressourceallokering
    - Sikkerhedsprotokoller
    - Udvikling og implementering
    - External Implementation Access Protocol (EIAP)

    Alle kritiske handlinger kræver HITL-godkendelse.
    """

    # Kritiske handlinger der ALTID kræver HITL
    CRITICAL_ACTIONS = {
        "create_agent",
        "delete_agent",
        "modify_security",
        "production_deploy",
        "database_modify",
        "system_config_change",
        "grant_admin_access",
        "execute_code"
    }

    def __init__(self):
        self._external_entities: Dict[str, ExternalEntity] = {}
        self._hitl_requests: Dict[str, HITLApprovalRequest] = {}
        self._audit_log: List[AuditLogEntry] = []
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._sandbox_environments: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

        # Statistik
        self._stats = {
            "total_operations": 0,
            "hitl_approvals": 0,
            "hitl_rejections": 0,
            "blocked_attempts": 0
        }

        logger.info("CKC Super-Admin Terminal initialized")

    # ═══════════════════════════════════════════════════════════
    # EXTERNAL ENTITY MANAGEMENT (EIAP)
    # ═══════════════════════════════════════════════════════════

    async def register_external_entity(
        self,
        name: str,
        entity_type: str,
        authorization_level: AuthorizationLevel,
        allowed_rooms: Set[int],
        allowed_actions: Set[str],
        sandbox_only: bool = True
    ) -> Tuple[ExternalEntity, str]:
        """
        Registrer en ekstern enhed med EIAP.

        Returns:
            Tuple af (entity, api_key)
        """
        entity_id = f"ext_{uuid.uuid4().hex[:12]}"
        api_key = secrets.token_urlsafe(32)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        entity = ExternalEntity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            authorization_level=authorization_level,
            allowed_rooms=allowed_rooms,
            allowed_actions=allowed_actions,
            api_key_hash=api_key_hash,
            sandbox_only=sandbox_only
        )

        self._external_entities[entity_id] = entity

        await self._log_audit(
            entity_id="system",
            action="register_external_entity",
            target=entity_id,
            result="success",
            details={"name": name, "type": entity_type, "level": authorization_level.name}
        )

        logger.info(f"External entity registered: {name} ({entity_id})")
        return entity, api_key

    async def verify_entity(
        self,
        entity_id: str,
        api_key: str
    ) -> Optional[ExternalEntity]:
        """Verificer en ekstern enheds identitet."""
        entity = self._external_entities.get(entity_id)
        if not entity or not entity.is_active:
            return None

        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if entity.api_key_hash != api_key_hash:
            await self._log_audit(
                entity_id=entity_id,
                action="verify_identity",
                target="self",
                result="failure",
                details={"reason": "Invalid API key"}
            )
            return None

        entity.last_access = datetime.utcnow()
        entity.access_count += 1
        return entity

    async def check_authorization(
        self,
        entity_id: str,
        action: str,
        target_room: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """Check om en enhed er autoriseret til en handling."""
        entity = self._external_entities.get(entity_id)
        if not entity or not entity.is_active:
            return False, "Entity not found or inactive"

        # Check action er tilladt
        if action not in entity.allowed_actions:
            return False, f"Action '{action}' not permitted"

        # Check room adgang hvis relevant
        if target_room is not None and target_room not in entity.allowed_rooms:
            return False, f"Access to room {target_room} not permitted"

        return True, None

    # ═══════════════════════════════════════════════════════════
    # HITL - HUMAN IN THE LOOP
    # ═══════════════════════════════════════════════════════════

    async def request_hitl_approval(
        self,
        action_type: str,
        description: str,
        requested_by: str,
        target_resource: str,
        risk_level: str = "medium"
    ) -> HITLApprovalRequest:
        """Anmod om Human-in-the-Loop godkendelse."""
        request_id = f"hitl_{uuid.uuid4().hex[:8]}"

        request = HITLApprovalRequest(
            id=request_id,
            action_type=action_type,
            description=description,
            requested_by=requested_by,
            target_resource=target_resource,
            risk_level=risk_level
        )

        self._hitl_requests[request_id] = request

        await self._log_audit(
            entity_id=requested_by,
            action="request_hitl_approval",
            target=target_resource,
            result="pending",
            details={"action_type": action_type, "risk_level": risk_level}
        )

        logger.info(f"HITL approval requested: {action_type} by {requested_by}")
        return request

    async def approve_hitl_request(
        self,
        request_id: str,
        approved_by: str
    ) -> bool:
        """Godkend en HITL anmodning."""
        request = self._hitl_requests.get(request_id)
        if not request or request.status != "pending":
            return False

        if datetime.utcnow() > request.expires_at:
            request.status = "expired"
            return False

        request.status = "approved"
        request.approved_by = approved_by
        request.approved_at = datetime.utcnow()
        self._stats["hitl_approvals"] += 1

        await self._log_audit(
            entity_id=approved_by,
            action="approve_hitl",
            target=request_id,
            result="success"
        )

        logger.info(f"HITL request {request_id} approved by {approved_by}")
        return True

    async def reject_hitl_request(
        self,
        request_id: str,
        rejected_by: str,
        reason: str
    ) -> bool:
        """Afvis en HITL anmodning."""
        request = self._hitl_requests.get(request_id)
        if not request or request.status != "pending":
            return False

        request.status = "rejected"
        request.approved_by = rejected_by
        request.approved_at = datetime.utcnow()
        request.rejection_reason = reason
        self._stats["hitl_rejections"] += 1

        await self._log_audit(
            entity_id=rejected_by,
            action="reject_hitl",
            target=request_id,
            result="rejected",
            details={"reason": reason}
        )

        logger.info(f"HITL request {request_id} rejected by {rejected_by}: {reason}")
        return True

    async def get_pending_hitl_requests(self) -> List[HITLApprovalRequest]:
        """Hent alle ventende HITL anmodninger."""
        now = datetime.utcnow()
        pending = []

        for request in self._hitl_requests.values():
            if request.status == "pending":
                if now > request.expires_at:
                    request.status = "expired"
                else:
                    pending.append(request)

        return sorted(pending, key=lambda r: r.created_at)

    # ═══════════════════════════════════════════════════════════
    # SANDBOX MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    async def create_sandbox(
        self,
        entity_id: str,
        environment_type: str = "standard"
    ) -> Dict[str, Any]:
        """Opret et sandbox miljø for en ekstern enhed."""
        sandbox_id = f"sandbox_{uuid.uuid4().hex[:8]}"

        sandbox = {
            "id": sandbox_id,
            "entity_id": entity_id,
            "environment_type": environment_type,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "resources": {},
            "execution_log": []
        }

        self._sandbox_environments[sandbox_id] = sandbox

        await self._log_audit(
            entity_id=entity_id,
            action="create_sandbox",
            target=sandbox_id,
            result="success"
        )

        logger.info(f"Sandbox {sandbox_id} created for entity {entity_id}")
        return sandbox

    async def execute_in_sandbox(
        self,
        sandbox_id: str,
        code: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """Eksekver kode i sandbox (simuleret)."""
        sandbox = self._sandbox_environments.get(sandbox_id)
        if not sandbox or sandbox["status"] != "active":
            return {"success": False, "error": "Sandbox not found or inactive"}

        if sandbox["entity_id"] != entity_id:
            return {"success": False, "error": "Entity not authorized for this sandbox"}

        # Simuleret eksekvering
        result = {
            "success": True,
            "sandbox_id": sandbox_id,
            "execution_time": 0.0,
            "output": "[Sandbox execution simulated]",
            "timestamp": datetime.utcnow().isoformat()
        }

        sandbox["execution_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "code_hash": hashlib.sha256(code.encode()).hexdigest()[:16],
            "result": "success"
        })

        return result

    # ═══════════════════════════════════════════════════════════
    # TERMINAL OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def execute_command(
        self,
        entity_id: str,
        command: str,
        params: Dict[str, Any],
        require_hitl: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Eksekver en terminal kommando."""
        async with self._lock:
            self._stats["total_operations"] += 1

            # Check autorisation
            authorized, reason = await self.check_authorization(entity_id, command)
            if not authorized:
                self._stats["blocked_attempts"] += 1
                await self._log_audit(
                    entity_id=entity_id,
                    action=command,
                    target=str(params),
                    result="blocked",
                    details={"reason": reason}
                )
                return {"success": False, "error": reason}

            # Check om HITL er påkrævet
            needs_hitl = require_hitl if require_hitl is not None else command in self.CRITICAL_ACTIONS

            if needs_hitl:
                # Opret HITL request
                hitl_request = await self.request_hitl_approval(
                    action_type=command,
                    description=f"Execute {command} with params: {params}",
                    requested_by=entity_id,
                    target_resource=str(params.get("target", "system")),
                    risk_level="high" if command in self.CRITICAL_ACTIONS else "medium"
                )

                return {
                    "success": False,
                    "pending_hitl": True,
                    "hitl_request_id": hitl_request.id,
                    "message": "Action requires Human-in-the-Loop approval"
                }

            # Eksekver kommando
            result = await self._execute_command_internal(command, params)

            await self._log_audit(
                entity_id=entity_id,
                action=command,
                target=str(params),
                result="success" if result.get("success") else "failure",
                details=result
            )

            return result

    async def _execute_command_internal(
        self,
        command: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Intern kommandoeksekvering."""
        # Simuleret kommandoeksekvering
        return {
            "success": True,
            "command": command,
            "params": params,
            "result": f"[{command}] executed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    # ═══════════════════════════════════════════════════════════
    # AUDIT & LOGGING
    # ═══════════════════════════════════════════════════════════

    async def _log_audit(
        self,
        entity_id: str,
        action: str,
        target: str,
        result: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log til audit."""
        entry = AuditLogEntry(
            id=f"audit_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            entity_id=entity_id,
            action=action,
            target=target,
            result=result,
            details=details or {}
        )
        self._audit_log.append(entry)

    async def get_audit_log(
        self,
        entity_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Hent audit log med filtrering."""
        entries = self._audit_log

        if entity_id:
            entries = [e for e in entries if e.entity_id == entity_id]
        if action:
            entries = [e for e in entries if e.action == action]

        return sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def get_terminal_status(self) -> Dict[str, Any]:
        """Hent terminal status."""
        pending_hitl = await self.get_pending_hitl_requests()

        return {
            "status": "operational",
            "registered_entities": len(self._external_entities),
            "active_sandboxes": len([s for s in self._sandbox_environments.values() if s["status"] == "active"]),
            "pending_hitl_requests": len(pending_hitl),
            "statistics": self._stats,
            "audit_log_size": len(self._audit_log),
            "timestamp": datetime.utcnow().isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# SINGLETON & CONVENIENCE
# ═══════════════════════════════════════════════════════════════

_security_manager: Optional[DynamicSecurityManager] = None
_ilcp_manager: Optional[ILCPManager] = None
_terminal: Optional[CKCSuperAdminTerminal] = None


def get_security_manager() -> DynamicSecurityManager:
    """Hent singleton DynamicSecurityManager."""
    global _security_manager
    if _security_manager is None:
        _security_manager = DynamicSecurityManager()
    return _security_manager


def get_ilcp_manager() -> ILCPManager:
    """Hent singleton ILCPManager."""
    global _ilcp_manager
    if _ilcp_manager is None:
        _ilcp_manager = ILCPManager()
    return _ilcp_manager


def get_terminal() -> CKCSuperAdminTerminal:
    """Hent singleton CKCSuperAdminTerminal."""
    global _terminal
    if _terminal is None:
        _terminal = CKCSuperAdminTerminal()
    return _terminal


logger.info("CKC Advanced Protocols module loaded - Security, ILCP, and Super-Admin Terminal ready")
