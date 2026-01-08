"""
Event Bus (Redis Streams)
=========================
Async event-driven communication for Cirkelline agents.

Uses Redis Streams for:
- Pub/Sub messaging between agents
- Event persistence and replay
- Consumer groups for load balancing

Event Types:
- AGENT_* : Agent lifecycle events
- MISSION_* : Mission coordination events
- KNOWLEDGE_* : Knowledge graph updates
- SYSTEM_* : System health and alerts
"""

import json
import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class EventType(str, Enum):
    """Categories of events in the system."""

    # Agent Lifecycle
    AGENT_REGISTERED = "agent.registered"
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_ERROR = "agent.error"

    # Mission Coordination
    MISSION_CREATED = "mission.created"
    MISSION_ASSIGNED = "mission.assigned"
    MISSION_PROGRESS = "mission.progress"
    MISSION_COMPLETED = "mission.completed"
    MISSION_FAILED = "mission.failed"

    # Knowledge Graph
    KNOWLEDGE_ADDED = "knowledge.added"
    KNOWLEDGE_UPDATED = "knowledge.updated"
    KNOWLEDGE_LINKED = "knowledge.linked"
    KNOWLEDGE_QUERY = "knowledge.query"

    # System Events
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ALERT = "system.alert"
    SYSTEM_METRIC = "system.metric"

    # Terminal Events
    TERMINAL_CONNECTED = "terminal.connected"
    TERMINAL_DISCONNECTED = "terminal.disconnected"
    TERMINAL_REQUEST = "terminal.request"
    TERMINAL_RESPONSE = "terminal.response"


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT DATA CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Event:
    """
    Immutable event structure for the event bus.

    Attributes:
        event_type: Category of event
        source: Agent/service that emitted the event
        payload: Event-specific data
        event_id: Unique identifier
        timestamp: ISO format creation time
        correlation_id: For tracking related events
        priority: 0=low, 1=normal, 2=high, 3=critical
    """
    event_type: EventType
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: Optional[str] = None
    priority: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "source": self.source,
            "payload": json.dumps(self.payload),
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id or "",
            "priority": str(self.priority),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Reconstruct from Redis data."""
        return cls(
            event_type=EventType(data["event_type"]) if data["event_type"] in [e.value for e in EventType] else data["event_type"],
            source=data["source"],
            payload=json.loads(data["payload"]) if isinstance(data["payload"], str) else data["payload"],
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            correlation_id=data["correlation_id"] if data.get("correlation_id") else None,
            priority=int(data.get("priority", 1)),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT HANDLER TYPE
# ═══════════════════════════════════════════════════════════════════════════════

EventHandler = Callable[[Event], Awaitable[None]]


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT BUS
# ═══════════════════════════════════════════════════════════════════════════════

class EventBus:
    """
    Redis Streams-based event bus for agent communication.

    Features:
    - Async pub/sub with persistence
    - Consumer groups for scaling
    - Event filtering by type
    - Dead letter queue for failed events
    """

    STREAM_NAME = "cirkelline:events"
    CONSUMER_GROUP = "cirkelline:agents"
    DLQ_STREAM = "cirkelline:events:dlq"

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_stream_length: int = 10000,
    ):
        self.redis_url = redis_url
        self.max_stream_length = max_stream_length
        self._redis: Optional[aioredis.Redis] = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None
        self._consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"

    async def connect(self) -> bool:
        """Connect to Redis and initialize streams."""
        if aioredis is None:
            logger.warning("redis.asyncio not available - using in-memory fallback")
            return False

        try:
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

            # Test connection
            await self._redis.ping()

            # Create consumer group if not exists
            try:
                await self._redis.xgroup_create(
                    self.STREAM_NAME,
                    self.CONSUMER_GROUP,
                    id="0",
                    mkstream=True,
                )
            except aioredis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            logger.info(f"EventBus connected to Redis: {self.redis_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self._running = False

        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass

        if self._redis:
            await self._redis.close()
            self._redis = None

        logger.info("EventBus disconnected")

    async def publish(self, event: Event) -> Optional[str]:
        """
        Publish an event to the stream.

        Args:
            event: Event to publish

        Returns:
            Stream entry ID if successful, None otherwise
        """
        if not self._redis:
            logger.warning("EventBus not connected - event dropped")
            # Fallback: dispatch to local handlers
            await self._dispatch_local(event)
            return None

        try:
            entry_id = await self._redis.xadd(
                self.STREAM_NAME,
                event.to_dict(),
                maxlen=self.max_stream_length,
            )

            logger.debug(f"Published event {event.event_id}: {event.event_type}")
            return entry_id

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return None

    async def broadcast(self, events: List[Event]) -> int:
        """Publish multiple events. Returns count of successful publishes."""
        success_count = 0
        for event in events:
            if await self.publish(event):
                success_count += 1
        return success_count

    def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of events to receive
            handler: Async callback function
        """
        key = event_type.value if isinstance(event_type, EventType) else event_type

        if key not in self._handlers:
            self._handlers[key] = []

        self._handlers[key].append(handler)
        logger.debug(f"Subscribed handler to {key}")

    def subscribe_pattern(
        self,
        pattern: str,
        handler: EventHandler,
    ) -> None:
        """
        Subscribe to events matching a pattern.

        Args:
            pattern: Pattern like "agent.*" or "mission.*"
            handler: Async callback function
        """
        self._handlers[f"pattern:{pattern}"] = self._handlers.get(f"pattern:{pattern}", [])
        self._handlers[f"pattern:{pattern}"].append(handler)

    def unsubscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> bool:
        """Remove a handler subscription."""
        key = event_type.value if isinstance(event_type, EventType) else event_type

        if key in self._handlers and handler in self._handlers[key]:
            self._handlers[key].remove(handler)
            return True
        return False

    async def start_consuming(self) -> None:
        """Start the consumer loop in background."""
        if self._running:
            return

        self._running = True
        self._consumer_task = asyncio.create_task(self._consume_loop())
        logger.info("EventBus consumer started")

    async def stop_consuming(self) -> None:
        """Stop the consumer loop."""
        self._running = False
        if self._consumer_task:
            self._consumer_task.cancel()

    async def _consume_loop(self) -> None:
        """Main consumer loop - reads events from stream."""
        while self._running:
            try:
                if not self._redis:
                    await asyncio.sleep(1)
                    continue

                # Read from consumer group
                entries = await self._redis.xreadgroup(
                    self.CONSUMER_GROUP,
                    self._consumer_name,
                    {self.STREAM_NAME: ">"},
                    count=10,
                    block=1000,
                )

                if not entries:
                    continue

                for stream_name, messages in entries:
                    for msg_id, data in messages:
                        try:
                            event = Event.from_dict(data)
                            await self._dispatch(event)

                            # Acknowledge processed message
                            await self._redis.xack(
                                self.STREAM_NAME,
                                self.CONSUMER_GROUP,
                                msg_id,
                            )

                        except Exception as e:
                            logger.error(f"Failed to process event {msg_id}: {e}")
                            # Move to DLQ
                            await self._move_to_dlq(msg_id, data, str(e))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer loop error: {e}")
                await asyncio.sleep(1)

    async def _dispatch(self, event: Event) -> None:
        """Dispatch event to matching handlers."""
        event_key = event.event_type.value if isinstance(event.event_type, EventType) else event.event_type

        # Direct type match
        handlers = self._handlers.get(event_key, [])

        # Pattern matches
        for key, pattern_handlers in self._handlers.items():
            if key.startswith("pattern:"):
                pattern = key[8:]  # Remove "pattern:" prefix
                if self._match_pattern(pattern, event_key):
                    handlers.extend(pattern_handlers)

        # Execute handlers
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event_key}: {e}")

    async def _dispatch_local(self, event: Event) -> None:
        """Dispatch to local handlers when Redis unavailable."""
        await self._dispatch(event)

    def _match_pattern(self, pattern: str, event_type: str) -> bool:
        """Check if event type matches pattern (supports * wildcard)."""
        if "*" not in pattern:
            return pattern == event_type

        # Simple wildcard matching
        parts = pattern.split("*")
        if len(parts) == 2:
            prefix, suffix = parts
            return event_type.startswith(prefix) and event_type.endswith(suffix)

        return False

    async def _move_to_dlq(
        self,
        msg_id: str,
        data: Dict[str, Any],
        error: str,
    ) -> None:
        """Move failed message to dead letter queue."""
        if not self._redis:
            return

        try:
            dlq_data = {
                **data,
                "original_id": msg_id,
                "error": error,
                "dlq_timestamp": datetime.utcnow().isoformat(),
            }

            await self._redis.xadd(
                self.DLQ_STREAM,
                dlq_data,
                maxlen=1000,
            )

            # Acknowledge original to remove from pending
            await self._redis.xack(
                self.STREAM_NAME,
                self.CONSUMER_GROUP,
                msg_id,
            )

        except Exception as e:
            logger.error(f"Failed to move to DLQ: {e}")

    async def get_pending_count(self) -> int:
        """Get count of pending (unprocessed) events."""
        if not self._redis:
            return 0

        try:
            info = await self._redis.xpending(
                self.STREAM_NAME,
                self.CONSUMER_GROUP,
            )
            return info.get("pending", 0) if info else 0
        except Exception:
            return 0

    async def get_stream_length(self) -> int:
        """Get current stream length."""
        if not self._redis:
            return 0

        try:
            return await self._redis.xlen(self.STREAM_NAME)
        except Exception:
            return 0


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_event_bus_instance: Optional[EventBus] = None


def get_event_bus(redis_url: Optional[str] = None) -> EventBus:
    """
    Get the singleton EventBus instance.

    Args:
        redis_url: Optional Redis URL (only used on first call)

    Returns:
        EventBus singleton instance
    """
    global _event_bus_instance

    if _event_bus_instance is None:
        url = redis_url or "redis://localhost:6379/0"
        _event_bus_instance = EventBus(redis_url=url)

    return _event_bus_instance


async def init_event_bus(redis_url: str = "redis://localhost:6379/0") -> EventBus:
    """Initialize and connect the event bus."""
    bus = get_event_bus(redis_url)
    await bus.connect()
    return bus
