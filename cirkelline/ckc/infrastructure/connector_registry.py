"""
CKC Connector Registry
======================

Central registry for managing all CKC connectors.
Provides dynamic loading, health monitoring, and event routing.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type

from ..connectors.base import (
    CKCConnector,
    ConnectorConfig,
    ConnectorStatus,
    ConnectorCapability,
    ConnectorEvent,
    ConnectorHealthStatus,
)

logger = logging.getLogger(__name__)


class RegistryEvent(Enum):
    """Events emitted by the registry."""
    CONNECTOR_REGISTERED = "connector_registered"
    CONNECTOR_UNREGISTERED = "connector_unregistered"
    CONNECTOR_STARTED = "connector_started"
    CONNECTOR_STOPPED = "connector_stopped"
    CONNECTOR_ERROR = "connector_error"
    CONNECTOR_RECONNECTED = "connector_reconnected"
    HEALTH_CHECK_COMPLETE = "health_check_complete"


@dataclass
class ConnectorInfo:
    """Information about a registered connector."""
    connector: CKCConnector
    registered_at: datetime
    auto_start: bool = True
    priority: int = 0  # Higher = more important
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.connector.name,
            "platform_id": self.connector.platform_id,
            "status": self.connector.status.value,
            "capabilities": [c.value for c in self.connector.capabilities],
            "registered_at": self.registered_at.isoformat(),
            "auto_start": self.auto_start,
            "priority": self.priority,
            "tags": list(self.tags),
            "statistics": self.connector.get_statistics()
        }


class ConnectorRegistry:
    """
    Central registry for all CKC connectors.

    Features:
    - Dynamic connector registration/unregistration
    - Automatic health monitoring
    - Event routing across connectors
    - Graceful shutdown with proper ordering

    Usage:
        registry = ConnectorRegistry()
        registry.register(CosmicLibraryConnector())
        await registry.start_all()

        # Route events
        await registry.broadcast_event(event)

        # Shutdown
        await registry.stop_all()
    """

    def __init__(self, health_check_interval: int = 30):
        self._connectors: Dict[str, ConnectorInfo] = {}
        self._health_check_interval = health_check_interval
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._event_handlers: Dict[RegistryEvent, List[Callable]] = {}
        self._global_event_handlers: List[Callable] = []
        self._initialized = False

        logger.info("Connector Registry created")

    @property
    def connectors(self) -> Dict[str, CKCConnector]:
        """Get all registered connectors."""
        return {k: v.connector for k, v in self._connectors.items()}

    @property
    def active_connectors(self) -> List[CKCConnector]:
        """Get all active (connected) connectors."""
        return [
            info.connector
            for info in self._connectors.values()
            if info.connector.status == ConnectorStatus.CONNECTED
        ]

    def register(
        self,
        connector: CKCConnector,
        auto_start: bool = True,
        priority: int = 0,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register a connector with the registry.

        Args:
            connector: The connector to register
            auto_start: Whether to auto-start when start_all() is called
            priority: Start/stop priority (higher = start first, stop last)
            tags: Tags for categorization
            metadata: Additional metadata

        Returns:
            True if registered successfully
        """
        platform_id = connector.platform_id

        if platform_id in self._connectors:
            logger.warning(f"Connector already registered: {platform_id}")
            return False

        info = ConnectorInfo(
            connector=connector,
            registered_at=datetime.utcnow(),
            auto_start=auto_start,
            priority=priority,
            tags=tags or set(),
            metadata=metadata or {}
        )

        self._connectors[platform_id] = info

        logger.info(f"Registered connector: {connector.name} ({platform_id})")
        self._emit_event(RegistryEvent.CONNECTOR_REGISTERED, connector)

        return True

    def unregister(self, platform_id: str) -> bool:
        """
        Unregister a connector.

        Args:
            platform_id: The platform ID of the connector

        Returns:
            True if unregistered successfully
        """
        if platform_id not in self._connectors:
            logger.warning(f"Connector not found: {platform_id}")
            return False

        info = self._connectors.pop(platform_id)

        logger.info(f"Unregistered connector: {info.connector.name}")
        self._emit_event(RegistryEvent.CONNECTOR_UNREGISTERED, info.connector)

        return True

    def get(self, platform_id: str) -> Optional[CKCConnector]:
        """Get a connector by platform ID."""
        info = self._connectors.get(platform_id)
        return info.connector if info else None

    def get_by_capability(
        self,
        capability: ConnectorCapability
    ) -> List[CKCConnector]:
        """Get all connectors with a specific capability."""
        return [
            info.connector
            for info in self._connectors.values()
            if info.connector.has_capability(capability)
        ]

    def get_by_tag(self, tag: str) -> List[CKCConnector]:
        """Get all connectors with a specific tag."""
        return [
            info.connector
            for info in self._connectors.values()
            if tag in info.tags
        ]

    async def start_all(self) -> Dict[str, bool]:
        """
        Start all auto-start connectors.

        Returns:
            Dict mapping platform_id to success status
        """
        results = {}

        # Sort by priority (highest first)
        sorted_connectors = sorted(
            self._connectors.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )

        for platform_id, info in sorted_connectors:
            if not info.auto_start:
                logger.info(f"Skipping {info.connector.name} (auto_start=False)")
                continue

            try:
                success = await info.connector.start()
                results[platform_id] = success

                if success:
                    self._emit_event(RegistryEvent.CONNECTOR_STARTED, info.connector)
                else:
                    self._emit_event(RegistryEvent.CONNECTOR_ERROR, info.connector)

            except Exception as e:
                logger.error(f"Failed to start {info.connector.name}: {e}")
                results[platform_id] = False
                self._emit_event(RegistryEvent.CONNECTOR_ERROR, info.connector)

        # Start health check loop
        if self._health_check_interval > 0:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        self._initialized = True
        logger.info(f"Started {sum(results.values())}/{len(results)} connectors")

        return results

    async def stop_all(self) -> Dict[str, bool]:
        """
        Stop all connectors.

        Returns:
            Dict mapping platform_id to success status
        """
        self._shutdown_event.set()
        results = {}

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Sort by priority (lowest first - stop less important first)
        sorted_connectors = sorted(
            self._connectors.items(),
            key=lambda x: x[1].priority
        )

        for platform_id, info in sorted_connectors:
            try:
                success = await info.connector.stop()
                results[platform_id] = success

                if success:
                    self._emit_event(RegistryEvent.CONNECTOR_STOPPED, info.connector)

            except Exception as e:
                logger.error(f"Failed to stop {info.connector.name}: {e}")
                results[platform_id] = False

        self._initialized = False
        logger.info(f"Stopped {sum(results.values())}/{len(results)} connectors")

        return results

    async def restart(self, platform_id: str) -> bool:
        """Restart a specific connector."""
        info = self._connectors.get(platform_id)
        if not info:
            return False

        await info.connector.stop()
        return await info.connector.start()

    async def health_check_all(self) -> Dict[str, ConnectorHealthStatus]:
        """
        Perform health check on all connectors.

        Returns:
            Dict mapping platform_id to health status
        """
        results = {}

        for platform_id, info in self._connectors.items():
            try:
                health = await info.connector.health_check()
                results[platform_id] = health
            except Exception as e:
                results[platform_id] = ConnectorHealthStatus(
                    status=ConnectorStatus.ERROR,
                    last_check=datetime.utcnow(),
                    error_message=str(e)
                )

        self._emit_event(RegistryEvent.HEALTH_CHECK_COMPLETE, results)
        return results

    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self._health_check_interval)

                if self._shutdown_event.is_set():
                    break

                await self.health_check_all()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    async def broadcast_event(
        self,
        event: ConnectorEvent,
        exclude: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Broadcast an event to all connectors.

        Args:
            event: Event to broadcast
            exclude: List of platform_ids to exclude

        Returns:
            Dict mapping platform_id to success status
        """
        results = {}
        exclude = exclude or []

        for platform_id, info in self._connectors.items():
            if platform_id in exclude:
                continue

            if not info.connector.has_capability(ConnectorCapability.WRITE_EVENTS):
                continue

            if info.connector.status != ConnectorStatus.CONNECTED:
                continue

            try:
                success = await info.connector.publish_event(event)
                results[platform_id] = success
            except Exception as e:
                logger.error(f"Failed to publish to {info.connector.name}: {e}")
                results[platform_id] = False

        return results

    async def route_event(
        self,
        event: ConnectorEvent,
        target_platform_id: str
    ) -> bool:
        """
        Route an event to a specific connector.

        Args:
            event: Event to route
            target_platform_id: Target platform ID

        Returns:
            True if routed successfully
        """
        info = self._connectors.get(target_platform_id)
        if not info:
            logger.warning(f"Target platform not found: {target_platform_id}")
            return False

        if not info.connector.has_capability(ConnectorCapability.WRITE_EVENTS):
            logger.warning(f"Target platform cannot receive events: {target_platform_id}")
            return False

        try:
            return await info.connector.publish_event(event)
        except Exception as e:
            logger.error(f"Failed to route event to {target_platform_id}: {e}")
            return False

    def on_global_event(self, handler: Callable[[ConnectorEvent], None]) -> None:
        """Register a handler for all events from all connectors."""
        self._global_event_handlers.append(handler)

    async def subscribe_all_events(
        self,
        callback: Callable[[ConnectorEvent], None]
    ) -> None:
        """Subscribe to events from all connectors."""
        for info in self._connectors.values():
            if info.connector.has_capability(ConnectorCapability.READ_EVENTS):
                await info.connector.subscribe_events(["*"], callback)

    def on(
        self,
        event: RegistryEvent,
        handler: Callable[[Any], None]
    ) -> None:
        """Register a handler for registry events."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def _emit_event(self, event: RegistryEvent, data: Any) -> None:
        """Emit a registry event."""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Error in registry event handler: {e}")

    def get_overview(self) -> Dict[str, Any]:
        """Get registry overview."""
        return {
            "total_connectors": len(self._connectors),
            "active_connectors": len(self.active_connectors),
            "initialized": self._initialized,
            "connectors": {
                platform_id: info.to_dict()
                for platform_id, info in self._connectors.items()
            }
        }

    def list_connectors(self) -> List[Dict[str, Any]]:
        """List all connectors with their info."""
        return [info.to_dict() for info in self._connectors.values()]


# Singleton instance
_registry: Optional[ConnectorRegistry] = None


async def get_connector_registry() -> ConnectorRegistry:
    """Get or create the singleton connector registry."""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry


async def close_connector_registry() -> None:
    """Close the singleton connector registry."""
    global _registry
    if _registry is not None:
        await _registry.stop_all()
        _registry = None


async def initialize_default_connectors() -> ConnectorRegistry:
    """
    Initialize registry with default connectors.

    This sets up connectors for:
    - Internal CKC message bus
    - Cosmic Library
    - lib-admin
    - CLA
    - Webhooks
    """
    from ..connectors.internal_connector import InternalConnector
    from ..connectors.http_connector import (
        CosmicLibraryConnector,
        LibAdminConnector,
        CLAConnector
    )
    from ..connectors.webhook_connector import WebhookConnector

    registry = await get_connector_registry()

    # Internal connector (highest priority)
    registry.register(
        InternalConnector(),
        priority=100,
        tags={"internal", "message_bus"}
    )

    # Platform connectors
    registry.register(
        CosmicLibraryConnector(),
        priority=50,
        tags={"platform", "cosmic_library"}
    )

    registry.register(
        LibAdminConnector(),
        priority=50,
        tags={"platform", "lib_admin"}
    )

    registry.register(
        CLAConnector(),
        priority=40,
        tags={"platform", "cla", "local"}
    )

    # Webhook connector
    registry.register(
        WebhookConnector(),
        priority=30,
        tags={"webhooks", "inbound"}
    )

    logger.info(f"Initialized {len(registry.connectors)} default connectors")

    return registry
