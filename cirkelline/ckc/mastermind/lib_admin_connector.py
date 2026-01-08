"""
CKC MASTERMIND Lib-Admin Connector (DEL AB)
===========================================

Admin platform forbindelse til MASTERMIND.

Formål:
    - Bridge til lib-admin admin platform
    - Bruger administration og SSO
    - Audit logging og compliance
    - Notifikations routing
    - Platform overvågning

Komponenter:
    1. AdminConnectionState - Forbindelses tilstande
    2. AdminEventType - Admin hændelsestyper
    3. AdminRole - Administratorroller
    4. AuditCategory - Audit log kategorier
    5. LibAdminConfig - Konfiguration
    6. AdminEvent - Admin hændelse
    7. AdminUser - Administrator bruger
    8. AuditLogEntry - Audit log entry
    9. AdminNotification - Admin notifikation
    10. PlatformStatus - Platform status
    11. LibAdminAPIClient - HTTP API klient
    12. LibAdminConnector - Hovedklasse

Forfatter: CKC MASTERMIND Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Union
import asyncio
import hashlib
import logging
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class AdminConnectionState(Enum):
    """Lib-Admin forbindelses tilstande."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AdminEventType(Enum):
    """Admin hændelsestyper fra lib-admin."""
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_LOCKED = "user_locked"
    USER_UNLOCKED = "user_unlocked"

    # Permission management
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"

    # System events
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    MAINTENANCE_STARTED = "maintenance_started"
    MAINTENANCE_ENDED = "maintenance_ended"
    BACKUP_COMPLETED = "backup_completed"
    SECURITY_ALERT = "security_alert"

    # Platform events
    PLATFORM_REGISTERED = "platform_registered"
    PLATFORM_STATUS_CHANGED = "platform_status_changed"
    SSO_TOKEN_ISSUED = "sso_token_issued"
    SSO_TOKEN_REVOKED = "sso_token_revoked"

    # Audit events
    AUDIT_LOG_EXPORTED = "audit_log_exported"
    COMPLIANCE_CHECK = "compliance_check"
    DATA_ACCESS = "data_access"

    # Notification events
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_READ = "notification_read"
    ALERT_TRIGGERED = "alert_triggered"


class AdminRole(Enum):
    """Administratorroller i lib-admin."""
    SUPER_ADMIN = "super_admin"
    PLATFORM_ADMIN = "platform_admin"
    USER_ADMIN = "user_admin"
    CONTENT_ADMIN = "content_admin"
    AUDIT_ADMIN = "audit_admin"
    SUPPORT_ADMIN = "support_admin"
    READ_ONLY = "read_only"
    SYSTEM = "system"


class AuditCategory(Enum):
    """Audit log kategorier."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    USER_MANAGEMENT = "user_management"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_CONFIGURATION = "system_configuration"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    API_ACCESS = "api_access"
    ERROR = "error"


class AuditSeverity(Enum):
    """Audit hændelses alvorlighed."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"


class NotificationPriority(Enum):
    """Notifikations prioritet."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class LibAdminConfig:
    """Konfiguration for lib-admin forbindelse."""
    api_url: str = "http://localhost:7779"
    api_key: str = ""
    admin_token: str = ""
    timeout: int = 30
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    enable_audit_sync: bool = True
    enable_user_sync: bool = True
    enable_notifications: bool = True
    health_check_interval: int = 30
    event_buffer_size: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdminEvent:
    """Admin hændelse fra lib-admin."""
    event_id: str
    event_type: AdminEventType
    timestamp: datetime
    actor_id: Optional[str]
    actor_role: Optional[AdminRole]
    target_id: Optional[str]
    target_type: Optional[str]
    payload: Dict[str, Any]
    source_platform: str
    processed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: AdminEventType,
        payload: Dict[str, Any],
        actor_id: Optional[str] = None,
        actor_role: Optional[AdminRole] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        source_platform: str = "ckc"
    ) -> "AdminEvent":
        """Opret ny admin event."""
        return cls(
            event_id=f"adm_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            timestamp=datetime.utcnow(),
            actor_id=actor_id,
            actor_role=actor_role,
            target_id=target_id,
            target_type=target_type,
            payload=payload,
            source_platform=source_platform
        )

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "actor_id": self.actor_id,
            "actor_role": self.actor_role.value if self.actor_role else None,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "payload": self.payload,
            "source_platform": self.source_platform,
            "processed": self.processed,
            "metadata": self.metadata
        }


@dataclass
class AdminUser:
    """Administrator bruger fra lib-admin."""
    user_id: str
    email: str
    display_name: str
    role: AdminRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    permissions: List[str]
    platforms: List[str]
    mfa_enabled: bool = False
    locked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: str) -> bool:
        """Tjek om bruger har specifik tilladelse."""
        if self.role == AdminRole.SUPER_ADMIN:
            return True
        return permission in self.permissions

    def has_platform_access(self, platform: str) -> bool:
        """Tjek om bruger har adgang til platform."""
        if self.role == AdminRole.SUPER_ADMIN:
            return True
        return platform in self.platforms


@dataclass
class AuditLogEntry:
    """Audit log entry."""
    entry_id: str
    timestamp: datetime
    category: AuditCategory
    severity: AuditSeverity
    action: str
    actor_id: Optional[str]
    actor_email: Optional[str]
    actor_role: Optional[str]
    target_type: Optional[str]
    target_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    session_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        category: AuditCategory,
        action: str,
        details: Dict[str, Any],
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True
    ) -> "AuditLogEntry":
        """Opret ny audit entry."""
        return cls(
            entry_id=f"aud_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            category=category,
            severity=severity,
            action=action,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=None,
            target_type=None,
            target_id=None,
            ip_address=None,
            user_agent=None,
            details=details,
            success=success
        )

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "severity": self.severity.value,
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_email": self.actor_email,
            "actor_role": self.actor_role,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details,
            "success": self.success,
            "error_message": self.error_message,
            "session_id": self.session_id
        }


@dataclass
class AdminNotification:
    """Admin notifikation."""
    notification_id: str
    timestamp: datetime
    priority: NotificationPriority
    title: str
    message: str
    category: str
    recipients: List[str]
    sender_id: Optional[str]
    action_url: Optional[str]
    expires_at: Optional[datetime]
    read_by: List[str] = field(default_factory=list)
    dismissed_by: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        title: str,
        message: str,
        recipients: List[str],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        category: str = "system",
        sender_id: Optional[str] = None,
        action_url: Optional[str] = None,
        ttl_hours: int = 72
    ) -> "AdminNotification":
        """Opret ny notifikation."""
        return cls(
            notification_id=f"not_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            priority=priority,
            title=title,
            message=message,
            category=category,
            recipients=recipients,
            sender_id=sender_id,
            action_url=action_url,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
        )

    def mark_read(self, user_id: str) -> None:
        """Markér som læst."""
        if user_id not in self.read_by:
            self.read_by.append(user_id)

    def dismiss(self, user_id: str) -> None:
        """Afvis notifikation."""
        if user_id not in self.dismissed_by:
            self.dismissed_by.append(user_id)


@dataclass
class PlatformStatus:
    """Platform status fra lib-admin."""
    platform_id: str
    platform_name: str
    status: str  # "healthy", "degraded", "down", "maintenance"
    last_heartbeat: datetime
    version: str
    uptime_seconds: int
    active_users: int
    error_count: int
    warning_count: int
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorStats:
    """Statistik for lib-admin connector."""
    events_received: int = 0
    events_sent: int = 0
    audit_entries_synced: int = 0
    users_synced: int = 0
    notifications_sent: int = 0
    errors: int = 0
    last_sync: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    uptime_seconds: int = 0
    connection_attempts: int = 0


# =============================================================================
# API CLIENT
# =============================================================================

class LibAdminAPIClient:
    """HTTP API klient til lib-admin."""

    def __init__(self, config: LibAdminConfig):
        """Initialisér API klient."""
        self.config = config
        self._session_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    async def authenticate(self) -> bool:
        """Autentificér med lib-admin."""
        try:
            # Simuleret autentificering
            logger.info(f"Authenticating with lib-admin at {self.config.api_url}")
            await asyncio.sleep(0.1)  # Simulér netværkskald

            self._session_token = f"sess_{uuid.uuid4().hex}"
            self._token_expiry = datetime.utcnow() + timedelta(hours=24)

            logger.info("Successfully authenticated with lib-admin")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    async def get_users(
        self,
        role: Optional[AdminRole] = None,
        active_only: bool = True
    ) -> List[AdminUser]:
        """Hent admin brugere."""
        try:
            await asyncio.sleep(0.05)  # Simulér netværkskald

            # Simuleret brugerdata
            users = [
                AdminUser(
                    user_id=f"user_{uuid.uuid4().hex[:8]}",
                    email="admin@cirkelline.com",
                    display_name="System Administrator",
                    role=AdminRole.SUPER_ADMIN,
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=365),
                    last_login=datetime.utcnow() - timedelta(hours=2),
                    permissions=["*"],
                    platforms=["ckc", "cosmic_library", "consulting"],
                    mfa_enabled=True
                ),
                AdminUser(
                    user_id=f"user_{uuid.uuid4().hex[:8]}",
                    email="support@cirkelline.com",
                    display_name="Support Admin",
                    role=AdminRole.SUPPORT_ADMIN,
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=180),
                    last_login=datetime.utcnow() - timedelta(hours=5),
                    permissions=["view_users", "manage_tickets"],
                    platforms=["ckc", "cosmic_library"]
                )
            ]

            if role:
                users = [u for u in users if u.role == role]
            if active_only:
                users = [u for u in users if u.is_active]

            return users

        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return []

    async def get_user(self, user_id: str) -> Optional[AdminUser]:
        """Hent specifik bruger."""
        users = await self.get_users()
        return next((u for u in users if u.user_id == user_id), None)

    async def create_audit_entry(self, entry: AuditLogEntry) -> bool:
        """Opret audit log entry."""
        try:
            await asyncio.sleep(0.02)  # Simulér netværkskald

            logger.debug(
                f"Audit entry created: {entry.category.value} - {entry.action}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create audit entry: {e}")
            return False

    async def get_audit_log(
        self,
        category: Optional[AuditCategory] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Hent audit log entries."""
        try:
            await asyncio.sleep(0.05)  # Simulér netværkskald

            # Simuleret audit data
            entries = [
                AuditLogEntry.create(
                    category=AuditCategory.AUTHENTICATION,
                    action="user_login",
                    details={"method": "password", "ip": "127.0.0.1"},
                    actor_email="admin@cirkelline.com"
                ),
                AuditLogEntry.create(
                    category=AuditCategory.DATA_ACCESS,
                    action="view_report",
                    details={"report_id": "rep_123", "report_type": "users"},
                    actor_email="admin@cirkelline.com"
                )
            ]

            if category:
                entries = [e for e in entries if e.category == category]

            return entries[:limit]

        except Exception as e:
            logger.error(f"Failed to get audit log: {e}")
            return []

    async def send_notification(self, notification: AdminNotification) -> bool:
        """Send admin notifikation."""
        try:
            await asyncio.sleep(0.03)  # Simulér netværkskald

            logger.info(
                f"Notification sent to {len(notification.recipients)} recipients: "
                f"{notification.title}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def get_platform_status(self, platform_id: str) -> Optional[PlatformStatus]:
        """Hent platform status."""
        try:
            await asyncio.sleep(0.02)  # Simulér netværkskald

            return PlatformStatus(
                platform_id=platform_id,
                platform_name=platform_id.upper(),
                status="healthy",
                last_heartbeat=datetime.utcnow(),
                version="1.0.0",
                uptime_seconds=86400 * 7,
                active_users=42,
                error_count=0,
                warning_count=2,
                metrics={"requests_per_minute": 150, "avg_response_ms": 45}
            )

        except Exception as e:
            logger.error(f"Failed to get platform status: {e}")
            return None

    async def validate_sso_token(
        self,
        token: str,
        target_platform: str
    ) -> Optional[Dict[str, Any]]:
        """Validér SSO token."""
        try:
            await asyncio.sleep(0.03)  # Simulér netværkskald

            # Simuleret token validering
            return {
                "valid": True,
                "user_id": f"user_{uuid.uuid4().hex[:8]}",
                "email": "user@cirkelline.com",
                "roles": ["user"],
                "platforms": [target_platform],
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to validate SSO token: {e}")
            return None

    async def issue_sso_token(
        self,
        user_id: str,
        target_platform: str
    ) -> Optional[str]:
        """Udsted SSO token."""
        try:
            await asyncio.sleep(0.02)  # Simulér netværkskald

            token = f"sso_{uuid.uuid4().hex}"
            logger.info(f"SSO token issued for user {user_id} to {target_platform}")
            return token

        except Exception as e:
            logger.error(f"Failed to issue SSO token: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Udfør health check."""
        try:
            await asyncio.sleep(0.01)  # Simulér netværkskald

            return {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "database": "healthy",
                    "cache": "healthy",
                    "queue": "healthy"
                }
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# =============================================================================
# MAIN CONNECTOR CLASS
# =============================================================================

class LibAdminConnector:
    """
    Hovedklasse for lib-admin forbindelse.

    Funktioner:
        - Bruger synchronisering
        - Audit log integration
        - Notifikations routing
        - SSO koordination
        - Platform overvågning

    Eksempel:
        connector = await create_lib_admin_connector()
        await connector.start()

        # Synkronisér brugere
        users = await connector.sync_users()

        # Log audit entry
        await connector.log_audit(
            AuditCategory.DATA_ACCESS,
            "view_report",
            {"report_id": "123"}
        )

        # Send notifikation
        await connector.send_admin_notification(
            title="System Update",
            message="Maintenance scheduled",
            recipients=["admin@cirkelline.com"]
        )

        await connector.stop()
    """

    def __init__(self, config: Optional[LibAdminConfig] = None):
        """Initialisér connector."""
        self.config = config or LibAdminConfig()
        self._client = LibAdminAPIClient(self.config)

        # State
        self._state = AdminConnectionState.DISCONNECTED
        self._running = False
        self._start_time: Optional[datetime] = None

        # Event handling
        self._event_queue: asyncio.Queue[AdminEvent] = asyncio.Queue(
            maxsize=self.config.event_buffer_size
        )
        self._event_handlers: Dict[
            AdminEventType,
            List[Callable[[AdminEvent], Coroutine[Any, Any, None]]]
        ] = {}

        # User cache
        self._user_cache: Dict[str, AdminUser] = {}
        self._user_cache_ttl: int = 300  # 5 minutes

        # Statistics
        self._stats = ConnectorStats()

        # Background tasks
        self._tasks: List[asyncio.Task] = []

        logger.info("LibAdminConnector initialized")

    @property
    def state(self) -> AdminConnectionState:
        """Hent nuværende tilstand."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Er forbundet til lib-admin."""
        return self._state == AdminConnectionState.CONNECTED

    @property
    def stats(self) -> ConnectorStats:
        """Hent statistik."""
        if self._start_time:
            self._stats.uptime_seconds = int(
                (datetime.utcnow() - self._start_time).total_seconds()
            )
        return self._stats

    async def start(self) -> bool:
        """Start connector."""
        if self._running:
            logger.warning("Connector already running")
            return True

        logger.info("Starting LibAdminConnector...")
        self._state = AdminConnectionState.CONNECTING

        try:
            # Autentificér
            self._state = AdminConnectionState.AUTHENTICATING
            if not await self._client.authenticate():
                self._state = AdminConnectionState.ERROR
                return False

            self._state = AdminConnectionState.CONNECTED
            self._running = True
            self._start_time = datetime.utcnow()

            # Start background tasks
            self._tasks.append(
                asyncio.create_task(self._event_processor())
            )
            self._tasks.append(
                asyncio.create_task(self._health_monitor())
            )

            if self.config.enable_user_sync:
                self._tasks.append(
                    asyncio.create_task(self._user_sync_task())
                )

            logger.info("LibAdminConnector started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start connector: {e}")
            self._state = AdminConnectionState.ERROR
            return False

    async def stop(self) -> None:
        """Stop connector."""
        if not self._running:
            return

        logger.info("Stopping LibAdminConnector...")
        self._running = False

        # Cancel tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._tasks.clear()
        self._state = AdminConnectionState.DISCONNECTED

        logger.info("LibAdminConnector stopped")

    def register_event_handler(
        self,
        event_type: AdminEventType,
        handler: Callable[[AdminEvent], Coroutine[Any, Any, None]]
    ) -> None:
        """Registrér event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type.value}")

    async def emit_event(self, event: AdminEvent) -> None:
        """Emit admin event."""
        try:
            await self._event_queue.put(event)
            self._stats.events_sent += 1
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping event")

    async def sync_users(
        self,
        role: Optional[AdminRole] = None
    ) -> List[AdminUser]:
        """Synkronisér brugere fra lib-admin."""
        if not self.is_connected:
            logger.warning("Cannot sync users: not connected")
            return []

        users = await self._client.get_users(role=role)

        # Opdater cache
        for user in users:
            self._user_cache[user.user_id] = user

        self._stats.users_synced = len(users)
        self._stats.last_sync = datetime.utcnow()

        logger.info(f"Synced {len(users)} users from lib-admin")
        return users

    async def get_user(self, user_id: str) -> Optional[AdminUser]:
        """Hent bruger (med cache)."""
        # Check cache first
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        # Fetch from API
        user = await self._client.get_user(user_id)
        if user:
            self._user_cache[user_id] = user

        return user

    async def log_audit(
        self,
        category: AuditCategory,
        action: str,
        details: Dict[str, Any],
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True
    ) -> bool:
        """Log audit entry til lib-admin."""
        if not self.is_connected:
            logger.warning("Cannot log audit: not connected")
            return False

        entry = AuditLogEntry.create(
            category=category,
            action=action,
            details=details,
            actor_id=actor_id,
            actor_email=actor_email,
            severity=severity,
            success=success
        )

        result = await self._client.create_audit_entry(entry)
        if result:
            self._stats.audit_entries_synced += 1

        return result

    async def get_audit_log(
        self,
        category: Optional[AuditCategory] = None,
        days: int = 7,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Hent audit log."""
        if not self.is_connected:
            return []

        start_date = datetime.utcnow() - timedelta(days=days)
        return await self._client.get_audit_log(
            category=category,
            start_date=start_date,
            limit=limit
        )

    async def send_admin_notification(
        self,
        title: str,
        message: str,
        recipients: List[str],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        category: str = "system"
    ) -> bool:
        """Send admin notifikation."""
        if not self.is_connected:
            logger.warning("Cannot send notification: not connected")
            return False

        notification = AdminNotification.create(
            title=title,
            message=message,
            recipients=recipients,
            priority=priority,
            category=category
        )

        result = await self._client.send_notification(notification)
        if result:
            self._stats.notifications_sent += 1

            # Emit event
            await self.emit_event(AdminEvent.create(
                event_type=AdminEventType.NOTIFICATION_SENT,
                payload={
                    "notification_id": notification.notification_id,
                    "title": title,
                    "recipients_count": len(recipients)
                }
            ))

        return result

    async def validate_sso_token(
        self,
        token: str,
        target_platform: str
    ) -> Optional[Dict[str, Any]]:
        """Validér SSO token."""
        if not self.is_connected:
            return None

        return await self._client.validate_sso_token(token, target_platform)

    async def issue_sso_token(
        self,
        user_id: str,
        target_platform: str
    ) -> Optional[str]:
        """Udsted SSO token."""
        if not self.is_connected:
            return None

        token = await self._client.issue_sso_token(user_id, target_platform)

        if token:
            await self.emit_event(AdminEvent.create(
                event_type=AdminEventType.SSO_TOKEN_ISSUED,
                payload={
                    "target_platform": target_platform
                },
                actor_id=user_id
            ))

        return token

    async def get_platform_status(self, platform_id: str) -> Optional[PlatformStatus]:
        """Hent platform status."""
        if not self.is_connected:
            return None

        return await self._client.get_platform_status(platform_id)

    async def health_check(self) -> Dict[str, Any]:
        """Udfør health check."""
        if not self.is_connected:
            return {
                "status": "disconnected",
                "connector_state": self._state.value
            }

        api_health = await self._client.health_check()

        return {
            "status": "healthy" if api_health.get("status") == "healthy" else "degraded",
            "connector_state": self._state.value,
            "stats": {
                "events_received": self._stats.events_received,
                "events_sent": self._stats.events_sent,
                "audit_entries_synced": self._stats.audit_entries_synced,
                "users_synced": self._stats.users_synced,
                "uptime_seconds": self.stats.uptime_seconds
            },
            "api_health": api_health
        }

    async def _event_processor(self) -> None:
        """Baggrundsopgave: Processér events."""
        logger.info("Event processor started")

        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )

                self._stats.events_received += 1

                # Call handlers
                handlers = self._event_handlers.get(event.event_type, [])
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Event handler error: {e}")
                        self._stats.errors += 1

                event.processed = True

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event processor error: {e}")
                self._stats.errors += 1

        logger.info("Event processor stopped")

    async def _health_monitor(self) -> None:
        """Baggrundsopgave: Overvåg forbindelse."""
        logger.info("Health monitor started")

        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                health = await self._client.health_check()
                self._stats.last_heartbeat = datetime.utcnow()

                if health.get("status") != "healthy":
                    logger.warning(f"Lib-admin health degraded: {health}")
                    self._state = AdminConnectionState.RECONNECTING
                else:
                    self._state = AdminConnectionState.CONNECTED

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                self._stats.errors += 1

        logger.info("Health monitor stopped")

    async def _user_sync_task(self) -> None:
        """Baggrundsopgave: Synkronisér brugere periodisk."""
        logger.info("User sync task started")

        while self._running:
            try:
                await asyncio.sleep(300)  # Hver 5 minutter
                await self.sync_users()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"User sync error: {e}")
                self._stats.errors += 1

        logger.info("User sync task stopped")


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

_lib_admin_connector: Optional[LibAdminConnector] = None


async def create_lib_admin_connector(
    config: Optional[LibAdminConfig] = None
) -> LibAdminConnector:
    """Opret og start lib-admin connector."""
    connector = LibAdminConnector(config)
    await connector.start()
    return connector


def get_lib_admin_connector() -> Optional[LibAdminConnector]:
    """Hent singleton connector instans."""
    return _lib_admin_connector


def set_lib_admin_connector(connector: LibAdminConnector) -> None:
    """Sæt singleton connector instans."""
    global _lib_admin_connector
    _lib_admin_connector = connector


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def log_admin_audit(
    category: AuditCategory,
    action: str,
    details: Dict[str, Any],
    actor_id: Optional[str] = None
) -> bool:
    """Log audit entry via global connector."""
    connector = get_lib_admin_connector()
    if not connector:
        logger.warning("No lib-admin connector available")
        return False

    return await connector.log_audit(
        category=category,
        action=action,
        details=details,
        actor_id=actor_id
    )


async def notify_admins(
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> bool:
    """Send notifikation til alle admins."""
    connector = get_lib_admin_connector()
    if not connector:
        return False

    users = await connector.sync_users(role=AdminRole.SUPER_ADMIN)
    recipients = [u.email for u in users if u.is_active]

    if not recipients:
        logger.warning("No active super admins to notify")
        return False

    return await connector.send_admin_notification(
        title=title,
        message=message,
        recipients=recipients,
        priority=priority
    )


async def validate_admin_access(
    user_id: str,
    required_permission: str
) -> bool:
    """Validér admin adgang."""
    connector = get_lib_admin_connector()
    if not connector:
        return False

    user = await connector.get_user(user_id)
    if not user:
        return False

    return user.has_permission(required_permission) and user.is_active


# =============================================================================
# MASTERMIND INTEGRATION
# =============================================================================

async def create_mastermind_lib_admin_connector(
    api_url: str = "http://localhost:7779"
) -> LibAdminConnector:
    """
    Opret lib-admin connector konfigureret for MASTERMIND.

    Args:
        api_url: Lib-admin API URL

    Returns:
        Konfigureret LibAdminConnector

    Eksempel:
        connector = await create_mastermind_lib_admin_connector()
        await connector.log_audit(
            AuditCategory.DATA_ACCESS,
            "mastermind_query",
            {"query": "user_report"}
        )
    """
    config = LibAdminConfig(
        api_url=api_url,
        enable_audit_sync=True,
        enable_user_sync=True,
        enable_notifications=True,
        metadata={"source": "mastermind", "integration": "v1.0"}
    )

    connector = await create_lib_admin_connector(config)
    set_lib_admin_connector(connector)

    logger.info("MASTERMIND lib-admin connector created and registered")
    return connector


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AdminConnectionState",
    "AdminEventType",
    "AdminRole",
    "AuditCategory",
    "AuditSeverity",
    "NotificationPriority",

    # Data classes
    "LibAdminConfig",
    "AdminEvent",
    "AdminUser",
    "AuditLogEntry",
    "AdminNotification",
    "PlatformStatus",
    "ConnectorStats",

    # Classes
    "LibAdminAPIClient",
    "LibAdminConnector",

    # Factory functions
    "create_lib_admin_connector",
    "get_lib_admin_connector",
    "set_lib_admin_connector",

    # Convenience functions
    "log_admin_audit",
    "notify_admins",
    "validate_admin_access",

    # MASTERMIND integration
    "create_mastermind_lib_admin_connector",
]
