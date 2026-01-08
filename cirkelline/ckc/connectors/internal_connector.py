"""
CKC Internal Connector
======================

Connector for internal CKC-to-CKC communication via the Message Bus.
Used for agent-to-agent, room-to-room, and ILCP communication.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import json

from .base import (
    CKCConnector,
    ConnectorConfig,
    ConnectorCapability,
    ConnectorEvent,
    ConnectorHealthStatus,
    ConnectorStatus,
    ActionResult,
)

logger = logging.getLogger(__name__)


class InternalConnector(CKCConnector):
    """
    Internal connector for CKC Message Bus communication.

    This connector integrates with RabbitMQ/Redis message bus to:
    - Route messages between agents
    - Handle ILCP room-to-room communication
    - Manage task distribution and feedback
    """

    def __init__(
        self,
        config: Optional[ConnectorConfig] = None,
        event_bus: Optional[Any] = None  # CKCEventBus from message_bus
    ):
        config = config or ConnectorConfig(
            name="CKC Internal",
            platform_id="ckc_internal",
            enabled=True,
            auto_reconnect=True,
            health_check_interval=15,
        )
        super().__init__(config)

        # Add capabilities
        self.add_capability(ConnectorCapability.READ_EVENTS)
        self.add_capability(ConnectorCapability.WRITE_EVENTS)
        self.add_capability(ConnectorCapability.EXECUTE_ACTIONS)
        self.add_capability(ConnectorCapability.BIDIRECTIONAL)
        self.add_capability(ConnectorCapability.STREAM_DATA)

        # Event bus reference
        self._event_bus = event_bus
        self._subscriptions: Dict[str, asyncio.Task] = {}
        self._local_queue: asyncio.Queue = asyncio.Queue()

    async def connect(self) -> bool:
        """Connect to the internal message bus."""
        try:
            # If no event bus provided, try to get singleton
            if self._event_bus is None:
                from ..infrastructure.message_bus import get_event_bus
                self._event_bus = await get_event_bus()

            # Initialize the event bus if needed
            if not self._event_bus._initialized:
                await self._event_bus.initialize()

            logger.info(f"Internal connector connected to message bus")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to message bus: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from the message bus."""
        try:
            # Cancel all subscriptions
            for task in self._subscriptions.values():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            self._subscriptions.clear()

            logger.info("Internal connector disconnected")
            return True

        except Exception as e:
            logger.error(f"Error disconnecting from message bus: {e}")
            return False

    async def health_check(self) -> ConnectorHealthStatus:
        """Check message bus health."""
        start_time = datetime.utcnow()

        try:
            if self._event_bus is None:
                return ConnectorHealthStatus(
                    status=ConnectorStatus.ERROR,
                    last_check=start_time,
                    error_message="Event bus not initialized"
                )

            # Get event bus health
            bus_health = await self._event_bus.health_check()

            latency = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Determine status based on bus health
            if bus_health.get("status") == "healthy":
                status = ConnectorStatus.CONNECTED
            elif bus_health.get("status") == "degraded":
                status = ConnectorStatus.CONNECTED  # Still usable via Redis
            else:
                status = ConnectorStatus.ERROR

            return ConnectorHealthStatus(
                status=status,
                last_check=datetime.utcnow(),
                latency_ms=latency,
                events_processed=self._events_processed,
                events_failed=self._events_failed,
                uptime_seconds=self.get_uptime_seconds(),
                details=bus_health
            )

        except Exception as e:
            return ConnectorHealthStatus(
                status=ConnectorStatus.ERROR,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )

    async def subscribe_events(
        self,
        event_types: List[str],
        callback: Callable[[ConnectorEvent], None]
    ) -> bool:
        """
        Subscribe to internal events.

        Event types:
        - task.*: Task events (task.created, task.completed, task.failed)
        - agent.*: Agent events (agent.started, agent.completed)
        - ilcp.*: ILCP messages (ilcp.room.{id})
        - feedback.*: Feedback events
        """
        try:
            for event_type in event_types:
                # Register handler
                self.on_event(event_type, callback)

                # Set up message bus subscription based on type
                if event_type.startswith("task."):
                    # Subscribe to task queue
                    async def task_handler(msg):
                        event = ConnectorEvent(
                            event_id=msg.get("message_id", f"evt_{id(msg)}"),
                            event_type=f"task.{msg.get('type', 'unknown')}",
                            source="ckc_internal",
                            timestamp=datetime.utcnow(),
                            payload=msg.get("data", {}),
                            metadata=msg.get("metadata", {})
                        )
                        await self._dispatch_event(event)

                    task = asyncio.create_task(
                        self._event_bus.subscribe_tasks("internal_connector", task_handler)
                    )
                    self._subscriptions[f"task_{event_type}"] = task

                elif event_type.startswith("ilcp."):
                    # Subscribe to ILCP messages
                    room_pattern = event_type.replace("ilcp.", "")

                    async def ilcp_handler(msg):
                        event = ConnectorEvent(
                            event_id=msg.get("message_id", f"evt_{id(msg)}"),
                            event_type=f"ilcp.{msg.get('message_type', 'message')}",
                            source=f"room_{msg.get('sender_room_id', 'unknown')}",
                            timestamp=datetime.utcnow(),
                            payload=msg.get("content", {}),
                            metadata={
                                "sender_room_id": msg.get("sender_room_id"),
                                "recipient_room_id": msg.get("recipient_room_id"),
                                "priority": msg.get("priority")
                            }
                        )
                        await self._dispatch_event(event)

                    # For now use a single room pattern - could be expanded
                    task = asyncio.create_task(
                        self._event_bus.subscribe_ilcp(1, ilcp_handler)  # Room 1 as default
                    )
                    self._subscriptions[f"ilcp_{event_type}"] = task

                elif event_type.startswith("event."):
                    # Subscribe to general events
                    async def event_handler(msg):
                        event = ConnectorEvent(
                            event_id=msg.get("message_id", f"evt_{id(msg)}"),
                            event_type=msg.get("event_type", "unknown"),
                            source=msg.get("source", "ckc_internal"),
                            timestamp=datetime.utcnow(),
                            payload=msg.get("data", {}),
                            metadata=msg.get("metadata", {})
                        )
                        await self._dispatch_event(event)

                    task = asyncio.create_task(
                        self._event_bus.subscribe_events(event_handler)
                    )
                    self._subscriptions[f"event_{event_type}"] = task

            logger.info(f"Subscribed to events: {event_types}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            return False

    async def publish_event(self, event: ConnectorEvent) -> bool:
        """Publish an event to the message bus."""
        try:
            if self._event_bus is None:
                logger.warning("Event bus not initialized, cannot publish")
                return False

            # Route based on event type
            if event.event_type.startswith("task."):
                # Publish as task
                await self._event_bus.publish_task(
                    agent_id=event.metadata.get("agent_id", "unknown"),
                    task_type=event.event_type.replace("task.", ""),
                    data=event.payload,
                    priority=event.metadata.get("priority", "normal")
                )

            elif event.event_type.startswith("ilcp."):
                # Publish as ILCP message
                await self._event_bus.publish_ilcp(
                    sender_room_id=event.metadata.get("sender_room_id", 0),
                    recipient_room_id=event.metadata.get("recipient_room_id", 0),
                    message_type=event.event_type.replace("ilcp.", ""),
                    content=event.payload,
                    priority=event.metadata.get("priority", "normal")
                )

            elif event.event_type.startswith("feedback."):
                # Publish as feedback
                await self._event_bus.publish_feedback(
                    agent_id=event.metadata.get("agent_id", "unknown"),
                    feedback_type=event.event_type.replace("feedback.", ""),
                    content=event.payload
                )

            else:
                # Publish as general event
                await self._event_bus.publish_event(
                    event_type=event.event_type,
                    source=event.source,
                    data=event.payload,
                    metadata=event.metadata
                )

            self._events_processed += 1
            return True

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            self._events_failed += 1
            return False

    async def execute_action(
        self,
        action_type: str,
        action_data: Dict[str, Any]
    ) -> ActionResult:
        """
        Execute an internal action.

        Actions:
        - send_task: Send task to specific agent
        - broadcast_event: Broadcast to all subscribers
        - route_ilcp: Route ILCP message
        - get_bus_status: Get message bus status
        """
        import uuid
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        start_time = datetime.utcnow()

        try:
            result_data = None

            if action_type == "send_task":
                # Send task to agent
                await self._event_bus.publish_task(
                    agent_id=action_data.get("agent_id"),
                    task_type=action_data.get("task_type"),
                    data=action_data.get("data", {}),
                    priority=action_data.get("priority", "normal")
                )
                result_data = {"status": "sent"}

            elif action_type == "broadcast_event":
                # Broadcast event
                await self._event_bus.publish_event(
                    event_type=action_data.get("event_type"),
                    source=action_data.get("source", "internal_connector"),
                    data=action_data.get("data", {}),
                    metadata=action_data.get("metadata", {})
                )
                result_data = {"status": "broadcast"}

            elif action_type == "route_ilcp":
                # Route ILCP message
                await self._event_bus.publish_ilcp(
                    sender_room_id=action_data.get("sender_room_id"),
                    recipient_room_id=action_data.get("recipient_room_id"),
                    message_type=action_data.get("message_type"),
                    content=action_data.get("content", {}),
                    priority=action_data.get("priority", "normal")
                )
                result_data = {"status": "routed"}

            elif action_type == "get_bus_status":
                # Get bus status
                health = await self._event_bus.health_check()
                result_data = health

            else:
                return ActionResult(
                    success=False,
                    action_id=action_id,
                    error=f"Unknown action type: {action_type}",
                    duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ActionResult(
                success=True,
                action_id=action_id,
                result_data=result_data,
                duration_ms=duration
            )

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ActionResult(
                success=False,
                action_id=action_id,
                error=str(e),
                duration_ms=duration
            )

    async def send_to_agent(
        self,
        agent_id: str,
        task_type: str,
        data: Dict[str, Any],
        priority: str = "normal"
    ) -> bool:
        """Convenience method to send task to specific agent."""
        event = ConnectorEvent.create(
            event_type=f"task.{task_type}",
            source="internal_connector",
            payload=data,
            metadata={"agent_id": agent_id, "priority": priority}
        )
        return await self.publish_event(event)

    async def send_ilcp_message(
        self,
        sender_room_id: int,
        recipient_room_id: int,
        message_type: str,
        content: Dict[str, Any],
        priority: str = "normal"
    ) -> bool:
        """Convenience method to send ILCP message."""
        event = ConnectorEvent.create(
            event_type=f"ilcp.{message_type}",
            source=f"room_{sender_room_id}",
            payload=content,
            metadata={
                "sender_room_id": sender_room_id,
                "recipient_room_id": recipient_room_id,
                "priority": priority
            }
        )
        return await self.publish_event(event)


# Singleton instance
_internal_connector: Optional[InternalConnector] = None


async def get_internal_connector() -> InternalConnector:
    """Get or create the singleton internal connector."""
    global _internal_connector
    if _internal_connector is None:
        _internal_connector = InternalConnector()
        await _internal_connector.start()
    return _internal_connector


async def close_internal_connector() -> None:
    """Close the singleton internal connector."""
    global _internal_connector
    if _internal_connector is not None:
        await _internal_connector.stop()
        _internal_connector = None
