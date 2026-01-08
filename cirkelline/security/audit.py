"""
Audit Logger
============
Comprehensive audit trail for security and compliance.

Responsibilities:
- Log all security-relevant events
- Track user actions and system changes
- Support compliance requirements (GDPR, etc.)
- Provide tamper-evident logging
"""

import logging
import json
import hashlib
import time
import threading
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class AuditLevel(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(Enum):
    """Categories of audit events."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    SYSTEM = "system"
    AGENT = "agent"
    API = "api"
    USER_ACTION = "user_action"


@dataclass
class AuditEvent:
    """A single audit event."""
    event_id: str
    timestamp: str
    level: AuditLevel
    category: AuditCategory
    action: str
    actor_id: Optional[str] = None
    actor_type: str = "user"  # user, system, agent
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "level": self.level.value,
            "category": self.category.value,
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "success": self.success,
            "error_message": self.error_message,
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        return cls(
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            level=AuditLevel(data["level"]),
            category=AuditCategory(data["category"]),
            action=data["action"],
            actor_id=data.get("actor_id"),
            actor_type=data.get("actor_type", "user"),
            resource_type=data.get("resource_type"),
            resource_id=data.get("resource_id"),
            details=data.get("details", {}),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            session_id=data.get("session_id"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            previous_hash=data.get("previous_hash"),
            event_hash=data.get("event_hash"),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT STORAGE
# ═══════════════════════════════════════════════════════════════════════════════

class AuditStorage:
    """Base class for audit storage backends."""

    def store(self, event: AuditEvent) -> bool:
        """Store an audit event."""
        raise NotImplementedError

    def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """Query audit events."""
        raise NotImplementedError


class MemoryAuditStorage(AuditStorage):
    """In-memory audit storage (for development/testing)."""

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self._events: List[AuditEvent] = []
        self._lock = threading.Lock()

    def store(self, event: AuditEvent) -> bool:
        with self._lock:
            self._events.append(event)
            # Trim if over limit
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events:]
            return True

    def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        with self._lock:
            events = self._events.copy()

        # Apply filters
        if filters:
            if "level" in filters:
                level = AuditLevel(filters["level"]) if isinstance(filters["level"], str) else filters["level"]
                events = [e for e in events if e.level == level]

            if "category" in filters:
                category = AuditCategory(filters["category"]) if isinstance(filters["category"], str) else filters["category"]
                events = [e for e in events if e.category == category]

            if "actor_id" in filters:
                events = [e for e in events if e.actor_id == filters["actor_id"]]

            if "action" in filters:
                events = [e for e in events if e.action == filters["action"]]

            if "success" in filters:
                events = [e for e in events if e.success == filters["success"]]

            if "from_timestamp" in filters:
                events = [e for e in events if e.timestamp >= filters["from_timestamp"]]

            if "to_timestamp" in filters:
                events = [e for e in events if e.timestamp <= filters["to_timestamp"]]

        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return events[offset:offset + limit]

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count matching events."""
        return len(self.query(filters, limit=999999))

    def clear(self) -> None:
        """Clear all events."""
        with self._lock:
            self._events.clear()


class FileAuditStorage(AuditStorage):
    """File-based audit storage with append-only logs."""

    def __init__(self, log_dir: str, rotate_size_mb: int = 100):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.rotate_size_mb = rotate_size_mb
        self._current_file: Optional[Path] = None
        self._lock = threading.Lock()

    def _get_current_file(self) -> Path:
        """Get current log file, rotating if needed."""
        if self._current_file is None:
            self._current_file = self.log_dir / f"audit-{datetime.utcnow().strftime('%Y%m%d')}.jsonl"

        # Check for rotation
        if self._current_file.exists():
            size_mb = self._current_file.stat().st_size / (1024 * 1024)
            if size_mb >= self.rotate_size_mb:
                timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
                self._current_file = self.log_dir / f"audit-{timestamp}.jsonl"

        return self._current_file

    def store(self, event: AuditEvent) -> bool:
        with self._lock:
            try:
                log_file = self._get_current_file()
                with open(log_file, 'a') as f:
                    f.write(event.to_json() + '\n')
                return True
            except Exception as e:
                logger.error(f"Failed to store audit event: {e}")
                return False

    def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        events = []

        # Read all log files
        log_files = sorted(self.log_dir.glob("audit-*.jsonl"), reverse=True)

        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            event = AuditEvent.from_dict(data)
                            events.append(event)
            except Exception as e:
                logger.error(f"Error reading audit file {log_file}: {e}")

        # Apply filters (same as memory storage)
        if filters:
            if "level" in filters:
                level = AuditLevel(filters["level"]) if isinstance(filters["level"], str) else filters["level"]
                events = [e for e in events if e.level == level]

            if "category" in filters:
                category = AuditCategory(filters["category"]) if isinstance(filters["category"], str) else filters["category"]
                events = [e for e in events if e.category == category]

            if "actor_id" in filters:
                events = [e for e in events if e.actor_id == filters["actor_id"]]

            if "action" in filters:
                events = [e for e in events if e.action == filters["action"]]

            if "success" in filters:
                events = [e for e in events if e.success == filters["success"]]

        # Sort and paginate
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[offset:offset + limit]


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT LOGGER
# ═══════════════════════════════════════════════════════════════════════════════

class AuditLogger:
    """
    Comprehensive audit logging system.

    Provides tamper-evident logging with hash chains
    and multiple storage backends.
    """

    def __init__(
        self,
        storage: Optional[AuditStorage] = None,
        enable_hash_chain: bool = True,
    ):
        self._storage = storage or MemoryAuditStorage()
        self._enable_hash_chain = enable_hash_chain
        self._previous_hash: Optional[str] = None
        self._handlers: List[Callable[[AuditEvent], None]] = []
        self._lock = threading.Lock()

        # Statistics
        self._stats = {
            "total_events": 0,
            "events_by_level": {},
            "events_by_category": {},
            "failed_events": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # LOGGING
    # ═══════════════════════════════════════════════════════════════════════════

    def log(
        self,
        action: str,
        category: AuditCategory,
        level: AuditLevel = AuditLevel.INFO,
        actor_id: Optional[str] = None,
        actor_type: str = "user",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            action: Description of the action
            category: Event category
            level: Severity level
            actor_id: ID of the actor (user, agent, system)
            actor_type: Type of actor
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session identifier
            success: Whether the action succeeded
            error_message: Error message if failed

        Returns:
            The created AuditEvent
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            category=category,
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            success=success,
            error_message=error_message,
        )

        # Add hash chain
        if self._enable_hash_chain:
            with self._lock:
                event.previous_hash = self._previous_hash
                event.event_hash = self._compute_hash(event)
                self._previous_hash = event.event_hash

        # Store event
        stored = self._storage.store(event)

        # Update stats
        self._update_stats(event, stored)

        # Notify handlers
        for handler in self._handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Audit handler error: {e}")

        # Also log to standard logger
        log_method = getattr(logger, level.value, logger.info)
        log_method(f"AUDIT [{category.value}] {action}: {actor_id or 'system'}")

        return event

    def _compute_hash(self, event: AuditEvent) -> str:
        """Compute hash for event (for chain integrity)."""
        data = f"{event.event_id}:{event.timestamp}:{event.action}:{event.actor_id}:{event.previous_hash}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _update_stats(self, event: AuditEvent, stored: bool) -> None:
        """Update statistics."""
        with self._lock:
            self._stats["total_events"] += 1

            level_key = event.level.value
            self._stats["events_by_level"][level_key] = self._stats["events_by_level"].get(level_key, 0) + 1

            category_key = event.category.value
            self._stats["events_by_category"][category_key] = self._stats["events_by_category"].get(category_key, 0) + 1

            if not stored:
                self._stats["failed_events"] += 1

    # ═══════════════════════════════════════════════════════════════════════════
    # CONVENIENCE METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def log_auth(
        self,
        action: str,
        actor_id: str,
        success: bool = True,
        **kwargs,
    ) -> AuditEvent:
        """Log authentication event."""
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        return self.log(
            action=action,
            category=AuditCategory.AUTHENTICATION,
            level=level,
            actor_id=actor_id,
            success=success,
            **kwargs,
        )

    def log_access(
        self,
        action: str,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        **kwargs,
    ) -> AuditEvent:
        """Log data access event."""
        return self.log(
            action=action,
            category=AuditCategory.DATA_ACCESS,
            level=AuditLevel.INFO,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )

    def log_modification(
        self,
        action: str,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        **kwargs,
    ) -> AuditEvent:
        """Log data modification event."""
        return self.log(
            action=action,
            category=AuditCategory.DATA_MODIFICATION,
            level=AuditLevel.INFO,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )

    def log_security(
        self,
        action: str,
        level: AuditLevel = AuditLevel.WARNING,
        **kwargs,
    ) -> AuditEvent:
        """Log security event."""
        return self.log(
            action=action,
            category=AuditCategory.SECURITY,
            level=level,
            **kwargs,
        )

    def log_agent(
        self,
        action: str,
        agent_id: str,
        **kwargs,
    ) -> AuditEvent:
        """Log agent event."""
        return self.log(
            action=action,
            category=AuditCategory.AGENT,
            level=AuditLevel.INFO,
            actor_id=agent_id,
            actor_type="agent",
            **kwargs,
        )

    def log_api(
        self,
        action: str,
        endpoint: str,
        method: str,
        status_code: int,
        **kwargs,
    ) -> AuditEvent:
        """Log API event."""
        success = 200 <= status_code < 400
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        return self.log(
            action=action,
            category=AuditCategory.API,
            level=level,
            success=success,
            details={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                **kwargs.get("details", {}),
            },
            **{k: v for k, v in kwargs.items() if k != "details"},
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERYING
    # ═══════════════════════════════════════════════════════════════════════════

    def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """Query audit events."""
        return self._storage.query(filters, limit, offset)

    def get_user_events(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get events for a specific user."""
        return self.query({"actor_id": user_id}, limit)

    def get_security_events(
        self,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get security-related events."""
        return self.query({"category": AuditCategory.SECURITY}, limit)

    def get_failed_events(
        self,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get failed events."""
        return self.query({"success": False}, limit)

    # ═══════════════════════════════════════════════════════════════════════════
    # HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════

    def add_handler(self, handler: Callable[[AuditEvent], None]) -> None:
        """Add an event handler."""
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[AuditEvent], None]) -> None:
        """Remove an event handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)

    # ═══════════════════════════════════════════════════════════════════════════
    # INTEGRITY VERIFICATION
    # ═══════════════════════════════════════════════════════════════════════════

    def verify_chain_integrity(
        self,
        events: Optional[List[AuditEvent]] = None,
    ) -> Dict[str, Any]:
        """
        Verify the hash chain integrity.

        Returns verification result with any broken links.
        """
        if events is None:
            events = self.query(limit=10000)

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        broken_links = []
        previous_hash = None

        for event in events:
            if event.previous_hash != previous_hash:
                broken_links.append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp,
                    "expected_previous": previous_hash,
                    "actual_previous": event.previous_hash,
                })

            # Verify event hash
            computed_hash = self._compute_hash(event)
            if event.event_hash != computed_hash:
                broken_links.append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp,
                    "issue": "hash_mismatch",
                    "expected": computed_hash,
                    "actual": event.event_hash,
                })

            previous_hash = event.event_hash

        return {
            "valid": len(broken_links) == 0,
            "total_events": len(events),
            "broken_links": broken_links,
            "verified_at": datetime.utcnow().isoformat(),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get audit logger statistics."""
        with self._lock:
            return {
                **self._stats,
                "handlers_count": len(self._handlers),
                "hash_chain_enabled": self._enable_hash_chain,
            }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_audit_instance: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the singleton AuditLogger instance."""
    global _audit_instance

    if _audit_instance is None:
        _audit_instance = AuditLogger(
            storage=MemoryAuditStorage(max_events=10000),
            enable_hash_chain=True,
        )

    return _audit_instance


async def init_audit_logger(
    storage: Optional[AuditStorage] = None,
) -> AuditLogger:
    """Initialize and return the audit logger."""
    global _audit_instance

    if _audit_instance is None:
        _audit_instance = AuditLogger(
            storage=storage or MemoryAuditStorage(),
            enable_hash_chain=True,
        )

    return _audit_instance
