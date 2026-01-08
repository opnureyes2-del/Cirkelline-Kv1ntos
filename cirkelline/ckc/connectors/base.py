"""
CKC Base Connector
==================

Abstract base class for all platform connectors.
Connectors bridge CKC with external platforms (Cosmic Library, lib-admin, Notion, etc.)

Architecture:
    Platform --> Connector --> CKC Event Bus --> Agents
    Platform <-- Connector <-- CKC Event Bus <-- Agents
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import asyncio
import hashlib
import logging

logger = logging.getLogger(__name__)


class ConnectorStatus(Enum):
    """Connector lifecycle status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ConnectorCapability(Enum):
    """Capabilities a connector can provide."""
    READ_EVENTS = "read_events"           # Can receive events from platform
    WRITE_EVENTS = "write_events"         # Can send events to platform
    EXECUTE_ACTIONS = "execute_actions"   # Can execute actions on platform
    STREAM_DATA = "stream_data"           # Supports real-time streaming
    BATCH_OPERATIONS = "batch_operations" # Supports batch operations
    WEBHOOKS = "webhooks"                 # Can receive webhooks
    BIDIRECTIONAL = "bidirectional"       # Full two-way communication


@dataclass
class ConnectorConfig:
    """Configuration for a connector."""
    name: str
    platform_id: str
    enabled: bool = True
    auto_reconnect: bool = True
    reconnect_interval: int = 5  # seconds
    max_reconnect_attempts: int = 10
    health_check_interval: int = 30  # seconds
    timeout: int = 30  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorEvent:
    """Event received from or sent to a platform."""
    event_id: str
    event_type: str
    source: str
    timestamp: datetime
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: str,
        source: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ConnectorEvent":
        """Create a new event with auto-generated ID."""
        import uuid
        return cls(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            source=source,
            timestamp=datetime.utcnow(),
            payload=payload,
            metadata=metadata or {}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata
        }


@dataclass
class ActionResult:
    """Result of executing an action on a platform."""
    success: bool
    action_id: str
    result_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorHealthStatus:
    """Health status of a connector."""
    status: ConnectorStatus
    last_check: datetime
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    events_processed: int = 0
    events_failed: int = 0
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "uptime_seconds": self.uptime_seconds,
            "details": self.details
        }


class CKCConnector(ABC):
    """
    Abstract base class for all CKC platform connectors.

    A connector provides:
    1. Connection management to external platforms
    2. Event subscription and publishing
    3. Action execution on the platform
    4. Health monitoring

    Example:
        class NotionConnector(CKCConnector):
            async def connect(self) -> bool:
                # Connect to Notion API
                ...
    """

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._status = ConnectorStatus.DISCONNECTED
        self._capabilities: Set[ConnectorCapability] = set()
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._events_processed = 0
        self._events_failed = 0
        self._start_time: Optional[datetime] = None
        self._last_health_check: Optional[datetime] = None
        self._reconnect_attempts = 0
        self._shutdown_event = asyncio.Event()

        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        logger.info(f"Connector created: {self.config.name} ({self.config.platform_id})")

    @property
    def name(self) -> str:
        """Connector name."""
        return self.config.name

    @property
    def platform_id(self) -> str:
        """Platform identifier."""
        return self.config.platform_id

    @property
    def status(self) -> ConnectorStatus:
        """Current connector status."""
        return self._status

    @property
    def capabilities(self) -> Set[ConnectorCapability]:
        """Set of capabilities this connector provides."""
        return self._capabilities

    @property
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._status == ConnectorStatus.CONNECTED

    def add_capability(self, capability: ConnectorCapability) -> None:
        """Add a capability to this connector."""
        self._capabilities.add(capability)

    def has_capability(self, capability: ConnectorCapability) -> bool:
        """Check if connector has a specific capability."""
        return capability in self._capabilities

    # ========== Abstract Methods ==========

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the platform.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the platform.

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    async def health_check(self) -> ConnectorHealthStatus:
        """
        Perform health check on the connection.

        Returns:
            ConnectorHealthStatus with current health status
        """
        pass

    @abstractmethod
    async def subscribe_events(
        self,
        event_types: List[str],
        callback: Callable[[ConnectorEvent], None]
    ) -> bool:
        """
        Subscribe to events from the platform.

        Args:
            event_types: List of event types to subscribe to
            callback: Function to call when events are received

        Returns:
            True if subscription successful, False otherwise
        """
        pass

    @abstractmethod
    async def publish_event(self, event: ConnectorEvent) -> bool:
        """
        Publish an event to the platform.

        Args:
            event: Event to publish

        Returns:
            True if event published successfully, False otherwise
        """
        pass

    @abstractmethod
    async def execute_action(
        self,
        action_type: str,
        action_data: Dict[str, Any]
    ) -> ActionResult:
        """
        Execute an action on the platform.

        Args:
            action_type: Type of action to execute
            action_data: Data for the action

        Returns:
            ActionResult with the result of the action
        """
        pass

    # ========== Common Implementation ==========

    async def start(self) -> bool:
        """
        Start the connector (connect + start background tasks).

        Returns:
            True if started successfully, False otherwise
        """
        try:
            self._status = ConnectorStatus.CONNECTING
            self._start_time = datetime.utcnow()
            self._shutdown_event.clear()

            # Connect
            if await self.connect():
                self._status = ConnectorStatus.CONNECTED
                self._reconnect_attempts = 0

                # Start health check task
                if self.config.health_check_interval > 0:
                    self._health_check_task = asyncio.create_task(
                        self._health_check_loop()
                    )

                logger.info(f"Connector started: {self.name}")
                return True
            else:
                self._status = ConnectorStatus.ERROR
                return False

        except Exception as e:
            logger.error(f"Failed to start connector {self.name}: {e}")
            self._status = ConnectorStatus.ERROR
            return False

    async def stop(self) -> bool:
        """
        Stop the connector (disconnect + stop background tasks).

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            self._shutdown_event.set()

            # Cancel background tasks
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            if self._reconnect_task:
                self._reconnect_task.cancel()
                try:
                    await self._reconnect_task
                except asyncio.CancelledError:
                    pass

            # Disconnect
            await self.disconnect()
            self._status = ConnectorStatus.DISCONNECTED

            logger.info(f"Connector stopped: {self.name}")
            return True

        except Exception as e:
            logger.error(f"Error stopping connector {self.name}: {e}")
            return False

    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.health_check_interval)

                if self._shutdown_event.is_set():
                    break

                health = await self.health_check()
                self._last_health_check = health.last_check

                # Handle unhealthy status
                if health.status == ConnectorStatus.ERROR:
                    logger.warning(f"Health check failed for {self.name}: {health.error_message}")
                    if self.config.auto_reconnect:
                        await self._handle_reconnect()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {self.name}: {e}")

    async def _handle_reconnect(self) -> None:
        """Handle reconnection logic."""
        if self._reconnect_attempts >= self.config.max_reconnect_attempts:
            logger.error(
                f"Max reconnect attempts reached for {self.name}, giving up"
            )
            self._status = ConnectorStatus.ERROR
            return

        self._status = ConnectorStatus.RECONNECTING
        self._reconnect_attempts += 1

        logger.info(
            f"Attempting reconnect for {self.name} "
            f"(attempt {self._reconnect_attempts}/{self.config.max_reconnect_attempts})"
        )

        await asyncio.sleep(self.config.reconnect_interval)

        if await self.connect():
            self._status = ConnectorStatus.CONNECTED
            self._reconnect_attempts = 0
            logger.info(f"Reconnected successfully: {self.name}")
        else:
            logger.warning(f"Reconnect failed for {self.name}")

    def on_event(self, event_type: str, handler: Callable[[ConnectorEvent], None]) -> None:
        """
        Register an event handler.

        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def _dispatch_event(self, event: ConnectorEvent) -> None:
        """Dispatch event to registered handlers."""
        handlers = self._event_handlers.get(event.event_type, [])
        handlers.extend(self._event_handlers.get("*", []))  # Wildcard handlers

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                self._events_processed += 1
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type}: {e}")
                self._events_failed += 1

    def get_uptime_seconds(self) -> float:
        """Get connector uptime in seconds."""
        if self._start_time:
            return (datetime.utcnow() - self._start_time).total_seconds()
        return 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """Get connector statistics."""
        return {
            "name": self.name,
            "platform_id": self.platform_id,
            "status": self._status.value,
            "capabilities": [c.value for c in self._capabilities],
            "events_processed": self._events_processed,
            "events_failed": self._events_failed,
            "uptime_seconds": self.get_uptime_seconds(),
            "reconnect_attempts": self._reconnect_attempts,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, status={self._status.value})>"
