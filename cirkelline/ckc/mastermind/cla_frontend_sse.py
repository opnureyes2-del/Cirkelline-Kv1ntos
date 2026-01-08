"""
CKC MASTERMIND CLA Frontend SSE (DEL AC)
========================================

Frontend real-time events til Cirkelline Admin (CLA).

Formål:
    - Server-Sent Events (SSE) til frontend
    - Real-time dashboard opdateringer
    - Agent status streaming
    - Notifikations push
    - System metrics streaming

Komponenter:
    1. FrontendEventType - Event typer til frontend
    2. SubscriptionTopic - Abonnerings emner
    3. ClientPriority - Klient prioritet
    4. ConnectionState - Forbindelses tilstand
    5. SSEConfig - SSE konfiguration
    6. FrontendEvent - Frontend event
    7. ClientSubscription - Klient abonnement
    8. StreamMetrics - Stream metrics
    9. SSEClient - SSE klient wrapper
    10. FrontendEventBus - Event bus til frontend
    11. CLAFrontendSSE - Hovedklasse

Forfatter: CKC MASTERMIND Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, AsyncIterator, Callable, Coroutine, Dict, List, Optional, Set
import asyncio
import hashlib
import json
import logging
import uuid
import time

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class FrontendEventType(Enum):
    """Event typer til frontend."""
    # System events
    SYSTEM_STATUS = "system_status"
    SYSTEM_HEALTH = "system_health"
    SYSTEM_METRICS = "system_metrics"
    SYSTEM_ALERT = "system_alert"

    # Agent events
    AGENT_STATUS_CHANGED = "agent_status_changed"
    AGENT_TASK_STARTED = "agent_task_started"
    AGENT_TASK_COMPLETED = "agent_task_completed"
    AGENT_TASK_FAILED = "agent_task_failed"
    AGENT_THOUGHT = "agent_thought"

    # Team events
    TEAM_ACTIVATED = "team_activated"
    TEAM_DEACTIVATED = "team_deactivated"
    TEAM_MEMBER_JOINED = "team_member_joined"
    TEAM_MEMBER_LEFT = "team_member_left"

    # Session events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_MESSAGE = "session_message"
    SESSION_TYPING = "session_typing"

    # Dashboard events
    DASHBOARD_UPDATE = "dashboard_update"
    WIDGET_REFRESH = "widget_refresh"
    CHART_DATA = "chart_data"
    TABLE_UPDATE = "table_update"

    # Notification events
    NOTIFICATION_NEW = "notification_new"
    NOTIFICATION_DISMISS = "notification_dismiss"
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_RESOLVED = "alert_resolved"

    # User events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_ACTIVITY = "user_activity"

    # Control events
    HEARTBEAT = "heartbeat"
    RECONNECT = "reconnect"
    ERROR = "error"


class SubscriptionTopic(Enum):
    """Abonnerings emner."""
    ALL = "all"
    SYSTEM = "system"
    AGENTS = "agents"
    TEAMS = "teams"
    SESSIONS = "sessions"
    DASHBOARD = "dashboard"
    NOTIFICATIONS = "notifications"
    USERS = "users"
    METRICS = "metrics"
    ALERTS = "alerts"


class ClientPriority(Enum):
    """Klient prioritet for resource allokering."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    ADMIN = "admin"
    SYSTEM = "system"


class ConnectionState(Enum):
    """Forbindelses tilstand."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class StreamFormat(Enum):
    """Output format for SSE stream."""
    JSON = "json"
    TEXT = "text"
    COMPACT = "compact"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SSEConfig:
    """Konfiguration for SSE server."""
    heartbeat_interval: int = 15  # seconds
    reconnect_timeout: int = 30  # seconds
    max_clients: int = 1000
    max_events_per_second: int = 100
    buffer_size: int = 1000
    default_priority: ClientPriority = ClientPriority.NORMAL
    enable_compression: bool = True
    enable_heartbeat: bool = True
    event_ttl: int = 300  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FrontendEvent:
    """Event til frontend."""
    event_id: str
    event_type: FrontendEventType
    timestamp: datetime
    topic: SubscriptionTopic
    data: Dict[str, Any]
    target_clients: Optional[List[str]] = None  # None = broadcast
    priority: ClientPriority = ClientPriority.NORMAL
    ttl: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: FrontendEventType,
        data: Dict[str, Any],
        topic: SubscriptionTopic = SubscriptionTopic.ALL,
        priority: ClientPriority = ClientPriority.NORMAL,
        target_clients: Optional[List[str]] = None
    ) -> "FrontendEvent":
        """Opret ny frontend event."""
        return cls(
            event_id=f"fe_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            timestamp=datetime.utcnow(),
            topic=topic,
            data=data,
            target_clients=target_clients,
            priority=priority
        )

    def to_sse(self, format: StreamFormat = StreamFormat.JSON) -> str:
        """Konverter til SSE format."""
        if format == StreamFormat.JSON:
            payload = json.dumps({
                "id": self.event_id,
                "type": self.event_type.value,
                "timestamp": self.timestamp.isoformat(),
                "topic": self.topic.value,
                "data": self.data,
                "metadata": self.metadata
            })
        elif format == StreamFormat.COMPACT:
            payload = json.dumps({
                "t": self.event_type.value,
                "d": self.data
            })
        else:
            payload = str(self.data)

        return f"event: {self.event_type.value}\ndata: {payload}\nid: {self.event_id}\n\n"

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "topic": self.topic.value,
            "data": self.data,
            "target_clients": self.target_clients,
            "priority": self.priority.value,
            "ttl": self.ttl,
            "metadata": self.metadata
        }


@dataclass
class ClientSubscription:
    """Klient abonnement."""
    client_id: str
    subscribed_topics: Set[SubscriptionTopic]
    created_at: datetime
    last_event_id: Optional[str] = None
    priority: ClientPriority = ClientPriority.NORMAL
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_subscribed_to(self, topic: SubscriptionTopic) -> bool:
        """Tjek om klient abonnerer på topic."""
        return (
            SubscriptionTopic.ALL in self.subscribed_topics or
            topic in self.subscribed_topics
        )


@dataclass
class StreamMetrics:
    """Metrics for SSE stream."""
    total_events_sent: int = 0
    total_bytes_sent: int = 0
    active_clients: int = 0
    events_per_second: float = 0.0
    avg_latency_ms: float = 0.0
    dropped_events: int = 0
    reconnections: int = 0
    errors: int = 0
    last_event_time: Optional[datetime] = None
    uptime_seconds: int = 0


@dataclass
class SSEClient:
    """SSE klient wrapper."""
    client_id: str
    state: ConnectionState
    connected_at: datetime
    subscription: ClientSubscription
    queue: asyncio.Queue
    last_heartbeat: datetime
    events_received: int = 0
    bytes_sent: int = 0
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        """Er klient forbundet."""
        return self.state == ConnectionState.CONNECTED


# =============================================================================
# EVENT BUS
# =============================================================================

class FrontendEventBus:
    """Event bus til frontend events."""

    def __init__(self, buffer_size: int = 1000):
        """Initialisér event bus."""
        self._buffer: List[FrontendEvent] = []
        self._buffer_size = buffer_size
        self._handlers: Dict[
            FrontendEventType,
            List[Callable[[FrontendEvent], Coroutine[Any, Any, None]]]
        ] = {}
        self._topic_handlers: Dict[
            SubscriptionTopic,
            List[Callable[[FrontendEvent], Coroutine[Any, Any, None]]]
        ] = {}
        self._lock = asyncio.Lock()

    async def publish(self, event: FrontendEvent) -> None:
        """Publicér event."""
        async with self._lock:
            # Buffer event
            self._buffer.append(event)
            if len(self._buffer) > self._buffer_size:
                self._buffer.pop(0)

        # Call type handlers
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

        # Call topic handlers
        topic_handlers = self._topic_handlers.get(event.topic, [])
        for handler in topic_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Topic handler error: {e}")

    def subscribe_type(
        self,
        event_type: FrontendEventType,
        handler: Callable[[FrontendEvent], Coroutine[Any, Any, None]]
    ) -> None:
        """Abonnér på event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_topic(
        self,
        topic: SubscriptionTopic,
        handler: Callable[[FrontendEvent], Coroutine[Any, Any, None]]
    ) -> None:
        """Abonnér på topic."""
        if topic not in self._topic_handlers:
            self._topic_handlers[topic] = []
        self._topic_handlers[topic].append(handler)

    async def get_recent_events(
        self,
        count: int = 50,
        topic: Optional[SubscriptionTopic] = None,
        event_type: Optional[FrontendEventType] = None
    ) -> List[FrontendEvent]:
        """Hent seneste events."""
        async with self._lock:
            events = list(self._buffer)

        if topic:
            events = [e for e in events if e.topic == topic]
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events[-count:]


# =============================================================================
# MAIN SSE CLASS
# =============================================================================

class CLAFrontendSSE:
    """
    CLA Frontend SSE Server.

    Håndterer Server-Sent Events til frontend klienter.

    Funktioner:
        - Client management
        - Event broadcasting
        - Topic-based subscriptions
        - Heartbeat monitoring
        - Metrics collection

    Eksempel:
        sse = await create_cla_frontend_sse()

        # Broadcast event
        await sse.broadcast(
            FrontendEventType.SYSTEM_STATUS,
            {"status": "healthy"}
        )

        # Stream events til klient
        async for event in sse.subscribe("client_123"):
            yield event.to_sse()
    """

    def __init__(self, config: Optional[SSEConfig] = None):
        """Initialisér SSE server."""
        self.config = config or SSEConfig()

        # Client management
        self._clients: Dict[str, SSEClient] = {}
        self._client_lock = asyncio.Lock()

        # Event bus
        self._event_bus = FrontendEventBus(self.config.buffer_size)

        # State
        self._running = False
        self._start_time: Optional[datetime] = None

        # Metrics
        self._metrics = StreamMetrics()

        # Background tasks
        self._tasks: List[asyncio.Task] = []

        logger.info("CLAFrontendSSE initialized")

    @property
    def is_running(self) -> bool:
        """Er SSE server kørende."""
        return self._running

    @property
    def client_count(self) -> int:
        """Antal tilsluttede klienter."""
        return len(self._clients)

    @property
    def metrics(self) -> StreamMetrics:
        """Hent stream metrics."""
        if self._start_time:
            self._metrics.uptime_seconds = int(
                (datetime.utcnow() - self._start_time).total_seconds()
            )
        self._metrics.active_clients = self.client_count
        return self._metrics

    async def start(self) -> None:
        """Start SSE server."""
        if self._running:
            return

        logger.info("Starting CLA Frontend SSE server...")
        self._running = True
        self._start_time = datetime.utcnow()

        # Start background tasks
        if self.config.enable_heartbeat:
            self._tasks.append(
                asyncio.create_task(self._heartbeat_task())
            )
        self._tasks.append(
            asyncio.create_task(self._cleanup_task())
        )

        logger.info("CLA Frontend SSE server started")

    async def stop(self) -> None:
        """Stop SSE server."""
        if not self._running:
            return

        logger.info("Stopping CLA Frontend SSE server...")
        self._running = False

        # Cancel tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._tasks.clear()

        # Disconnect all clients
        async with self._client_lock:
            for client in list(self._clients.values()):
                await self._disconnect_client(client.client_id)

        logger.info("CLA Frontend SSE server stopped")

    async def connect_client(
        self,
        client_id: Optional[str] = None,
        topics: Optional[Set[SubscriptionTopic]] = None,
        priority: ClientPriority = ClientPriority.NORMAL,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SSEClient:
        """Forbind ny klient."""
        if not self._running:
            raise RuntimeError("SSE server not running")

        if len(self._clients) >= self.config.max_clients:
            raise RuntimeError("Maximum clients reached")

        client_id = client_id or f"client_{uuid.uuid4().hex[:12]}"
        topics = topics or {SubscriptionTopic.ALL}

        subscription = ClientSubscription(
            client_id=client_id,
            subscribed_topics=topics,
            created_at=datetime.utcnow(),
            priority=priority,
            user_id=user_id
        )

        client = SSEClient(
            client_id=client_id,
            state=ConnectionState.CONNECTED,
            connected_at=datetime.utcnow(),
            subscription=subscription,
            queue=asyncio.Queue(maxsize=self.config.buffer_size),
            last_heartbeat=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        async with self._client_lock:
            self._clients[client_id] = client

        logger.info(f"Client {client_id} connected (topics: {len(topics)})")

        # Send connect event
        await self._send_to_client(
            client,
            FrontendEvent.create(
                FrontendEventType.HEARTBEAT,
                {"connected": True, "client_id": client_id},
                SubscriptionTopic.SYSTEM
            )
        )

        return client

    async def disconnect_client(self, client_id: str) -> None:
        """Afbryd klient forbindelse."""
        await self._disconnect_client(client_id)

    async def _disconnect_client(self, client_id: str) -> None:
        """Intern: Afbryd klient."""
        async with self._client_lock:
            if client_id not in self._clients:
                return

            client = self._clients[client_id]
            client.state = ConnectionState.DISCONNECTED

            # Clear queue
            while not client.queue.empty():
                try:
                    client.queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            del self._clients[client_id]

        logger.info(f"Client {client_id} disconnected")

    async def subscribe(
        self,
        client_id: str,
        last_event_id: Optional[str] = None
    ) -> AsyncIterator[FrontendEvent]:
        """
        Abonnér på events for klient.

        Yields events som de modtages.
        """
        async with self._client_lock:
            client = self._clients.get(client_id)

        if not client:
            raise ValueError(f"Client {client_id} not found")

        # Send missed events if resuming
        if last_event_id:
            missed = await self._get_missed_events(
                client_id, last_event_id
            )
            for event in missed:
                yield event

        # Stream new events
        try:
            while self._running and client.is_connected:
                try:
                    event = await asyncio.wait_for(
                        client.queue.get(),
                        timeout=self.config.heartbeat_interval
                    )
                    client.events_received += 1
                    yield event

                except asyncio.TimeoutError:
                    # Send heartbeat
                    if self.config.enable_heartbeat:
                        yield FrontendEvent.create(
                            FrontendEventType.HEARTBEAT,
                            {"timestamp": datetime.utcnow().isoformat()},
                            SubscriptionTopic.SYSTEM
                        )

        except asyncio.CancelledError:
            pass
        finally:
            await self._disconnect_client(client_id)

    async def broadcast(
        self,
        event_type: FrontendEventType,
        data: Dict[str, Any],
        topic: SubscriptionTopic = SubscriptionTopic.ALL,
        priority: ClientPriority = ClientPriority.NORMAL,
        exclude_clients: Optional[List[str]] = None
    ) -> int:
        """
        Broadcast event til alle relevante klienter.

        Returns antal klienter der modtog event.
        """
        event = FrontendEvent.create(
            event_type=event_type,
            data=data,
            topic=topic,
            priority=priority
        )

        return await self._broadcast_event(event, exclude_clients)

    async def send_to_client(
        self,
        client_id: str,
        event_type: FrontendEventType,
        data: Dict[str, Any],
        topic: SubscriptionTopic = SubscriptionTopic.ALL
    ) -> bool:
        """Send event til specifik klient."""
        async with self._client_lock:
            client = self._clients.get(client_id)

        if not client:
            return False

        event = FrontendEvent.create(
            event_type=event_type,
            data=data,
            topic=topic,
            target_clients=[client_id]
        )

        return await self._send_to_client(client, event)

    async def send_to_user(
        self,
        user_id: str,
        event_type: FrontendEventType,
        data: Dict[str, Any],
        topic: SubscriptionTopic = SubscriptionTopic.ALL
    ) -> int:
        """Send event til alle klienter for en bruger."""
        count = 0

        async with self._client_lock:
            clients = [
                c for c in self._clients.values()
                if c.subscription.user_id == user_id
            ]

        event = FrontendEvent.create(
            event_type=event_type,
            data=data,
            topic=topic
        )

        for client in clients:
            if await self._send_to_client(client, event):
                count += 1

        return count

    async def _broadcast_event(
        self,
        event: FrontendEvent,
        exclude_clients: Optional[List[str]] = None
    ) -> int:
        """Intern: Broadcast event til klienter."""
        exclude = set(exclude_clients or [])
        count = 0

        # Publish til event bus
        await self._event_bus.publish(event)

        async with self._client_lock:
            clients = list(self._clients.values())

        for client in clients:
            if client.client_id in exclude:
                continue

            if not client.subscription.is_subscribed_to(event.topic):
                continue

            if await self._send_to_client(client, event):
                count += 1

        self._metrics.total_events_sent += count
        self._metrics.last_event_time = datetime.utcnow()

        return count

    async def _send_to_client(
        self,
        client: SSEClient,
        event: FrontendEvent
    ) -> bool:
        """Intern: Send event til klient."""
        if not client.is_connected:
            return False

        try:
            # Non-blocking put
            client.queue.put_nowait(event)
            sse_data = event.to_sse()
            client.bytes_sent += len(sse_data.encode())
            return True

        except asyncio.QueueFull:
            self._metrics.dropped_events += 1
            logger.warning(f"Queue full for client {client.client_id}")
            return False

    async def _get_missed_events(
        self,
        client_id: str,
        last_event_id: str
    ) -> List[FrontendEvent]:
        """Hent events efter given event ID."""
        events = await self._event_bus.get_recent_events(count=100)

        found = False
        missed = []

        for event in events:
            if event.event_id == last_event_id:
                found = True
                continue
            if found:
                missed.append(event)

        return missed

    async def _heartbeat_task(self) -> None:
        """Baggrundsopgave: Send heartbeats."""
        logger.info("Heartbeat task started")

        while self._running:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)

                # Check for stale clients
                now = datetime.utcnow()
                timeout = timedelta(seconds=self.config.reconnect_timeout)

                async with self._client_lock:
                    stale = [
                        c for c in self._clients.values()
                        if (now - c.last_heartbeat) > timeout
                    ]

                for client in stale:
                    logger.warning(f"Client {client.client_id} timed out")
                    await self._disconnect_client(client.client_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat task error: {e}")
                self._metrics.errors += 1

        logger.info("Heartbeat task stopped")

    async def _cleanup_task(self) -> None:
        """Baggrundsopgave: Oprydning."""
        logger.info("Cleanup task started")

        while self._running:
            try:
                await asyncio.sleep(60)  # Hver minut

                # Update metrics
                async with self._client_lock:
                    total_events = sum(
                        c.events_received for c in self._clients.values()
                    )

                if self._metrics.uptime_seconds > 0:
                    self._metrics.events_per_second = (
                        total_events / self._metrics.uptime_seconds
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                self._metrics.errors += 1

        logger.info("Cleanup task stopped")

    def get_client(self, client_id: str) -> Optional[SSEClient]:
        """Hent klient info."""
        return self._clients.get(client_id)

    def get_clients_by_user(self, user_id: str) -> List[SSEClient]:
        """Hent alle klienter for en bruger."""
        return [
            c for c in self._clients.values()
            if c.subscription.user_id == user_id
        ]

    def get_clients_by_topic(
        self,
        topic: SubscriptionTopic
    ) -> List[SSEClient]:
        """Hent alle klienter der abonnerer på topic."""
        return [
            c for c in self._clients.values()
            if c.subscription.is_subscribed_to(topic)
        ]

    async def update_subscription(
        self,
        client_id: str,
        topics: Set[SubscriptionTopic]
    ) -> bool:
        """Opdater klient abonnement."""
        async with self._client_lock:
            client = self._clients.get(client_id)
            if not client:
                return False

            client.subscription.subscribed_topics = topics
            return True

    # Convenience methods for common events

    async def send_system_status(self, status: Dict[str, Any]) -> int:
        """Send system status update."""
        return await self.broadcast(
            FrontendEventType.SYSTEM_STATUS,
            status,
            SubscriptionTopic.SYSTEM
        )

    async def send_agent_status(
        self,
        agent_id: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """Send agent status ændring."""
        return await self.broadcast(
            FrontendEventType.AGENT_STATUS_CHANGED,
            {
                "agent_id": agent_id,
                "status": status,
                "details": details or {}
            },
            SubscriptionTopic.AGENTS
        )

    async def send_notification(
        self,
        title: str,
        message: str,
        level: str = "info",
        user_id: Optional[str] = None
    ) -> int:
        """Send notifikation."""
        data = {
            "title": title,
            "message": message,
            "level": level,
            "timestamp": datetime.utcnow().isoformat()
        }

        if user_id:
            return await self.send_to_user(
                user_id,
                FrontendEventType.NOTIFICATION_NEW,
                data,
                SubscriptionTopic.NOTIFICATIONS
            )
        else:
            return await self.broadcast(
                FrontendEventType.NOTIFICATION_NEW,
                data,
                SubscriptionTopic.NOTIFICATIONS
            )

    async def send_dashboard_update(
        self,
        widget_id: str,
        data: Dict[str, Any]
    ) -> int:
        """Send dashboard widget opdatering."""
        return await self.broadcast(
            FrontendEventType.WIDGET_REFRESH,
            {
                "widget_id": widget_id,
                "data": data
            },
            SubscriptionTopic.DASHBOARD
        )

    async def send_chart_data(
        self,
        chart_id: str,
        series: List[Dict[str, Any]]
    ) -> int:
        """Send chart data opdatering."""
        return await self.broadcast(
            FrontendEventType.CHART_DATA,
            {
                "chart_id": chart_id,
                "series": series
            },
            SubscriptionTopic.DASHBOARD
        )

    async def send_alert(
        self,
        alert_id: str,
        severity: str,
        message: str,
        source: str
    ) -> int:
        """Send system alert."""
        return await self.broadcast(
            FrontendEventType.ALERT_TRIGGERED,
            {
                "alert_id": alert_id,
                "severity": severity,
                "message": message,
                "source": source,
                "timestamp": datetime.utcnow().isoformat()
            },
            SubscriptionTopic.ALERTS,
            priority=ClientPriority.HIGH
        )

    async def resolve_alert(self, alert_id: str) -> int:
        """Løs/afslut alert."""
        return await self.broadcast(
            FrontendEventType.ALERT_RESOLVED,
            {
                "alert_id": alert_id,
                "resolved_at": datetime.utcnow().isoformat()
            },
            SubscriptionTopic.ALERTS
        )


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

_cla_frontend_sse: Optional[CLAFrontendSSE] = None


async def create_cla_frontend_sse(
    config: Optional[SSEConfig] = None
) -> CLAFrontendSSE:
    """Opret og start CLA Frontend SSE server."""
    sse = CLAFrontendSSE(config)
    await sse.start()
    return sse


def get_cla_frontend_sse() -> Optional[CLAFrontendSSE]:
    """Hent singleton SSE instans."""
    return _cla_frontend_sse


def set_cla_frontend_sse(sse: CLAFrontendSSE) -> None:
    """Sæt singleton SSE instans."""
    global _cla_frontend_sse
    _cla_frontend_sse = sse


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def broadcast_frontend_event(
    event_type: FrontendEventType,
    data: Dict[str, Any],
    topic: SubscriptionTopic = SubscriptionTopic.ALL
) -> int:
    """Broadcast event via global SSE server."""
    sse = get_cla_frontend_sse()
    if not sse:
        logger.warning("No CLA Frontend SSE server available")
        return 0

    return await sse.broadcast(event_type, data, topic)


async def notify_frontend_user(
    user_id: str,
    title: str,
    message: str,
    level: str = "info"
) -> int:
    """Send notifikation til frontend bruger."""
    sse = get_cla_frontend_sse()
    if not sse:
        return 0

    return await sse.send_notification(title, message, level, user_id)


async def update_frontend_dashboard(
    widget_id: str,
    data: Dict[str, Any]
) -> int:
    """Opdater dashboard widget."""
    sse = get_cla_frontend_sse()
    if not sse:
        return 0

    return await sse.send_dashboard_update(widget_id, data)


# =============================================================================
# MASTERMIND INTEGRATION
# =============================================================================

async def create_mastermind_frontend_sse() -> CLAFrontendSSE:
    """
    Opret CLA Frontend SSE konfigureret for MASTERMIND.

    Returns:
        Konfigureret CLAFrontendSSE

    Eksempel:
        sse = await create_mastermind_frontend_sse()
        await sse.send_agent_status("agent_1", "active")
    """
    config = SSEConfig(
        heartbeat_interval=15,
        max_clients=500,
        enable_compression=True,
        metadata={"source": "mastermind", "integration": "v1.0"}
    )

    sse = await create_cla_frontend_sse(config)
    set_cla_frontend_sse(sse)

    logger.info("MASTERMIND CLA Frontend SSE created and registered")
    return sse


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "FrontendEventType",
    "SubscriptionTopic",
    "ClientPriority",
    "ConnectionState",
    "StreamFormat",

    # Data classes
    "SSEConfig",
    "FrontendEvent",
    "ClientSubscription",
    "StreamMetrics",
    "SSEClient",

    # Classes
    "FrontendEventBus",
    "CLAFrontendSSE",

    # Factory functions
    "create_cla_frontend_sse",
    "get_cla_frontend_sse",
    "set_cla_frontend_sse",

    # Convenience functions
    "broadcast_frontend_event",
    "notify_frontend_user",
    "update_frontend_dashboard",

    # MASTERMIND integration
    "create_mastermind_frontend_sse",
]
