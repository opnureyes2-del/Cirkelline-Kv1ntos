"""
CKC Message Bus Layer
=====================

Hybrid message bus implementation med:
- RabbitMQ for robust, guaranteed message delivery
- Redis Pub/Sub for volatile, real-time communication

Usage:
    from cirkelline.ckc.infrastructure import get_event_bus

    bus = await get_event_bus()

    # Publish task to agent
    await bus.publish_task("tool_explorer", {
        "action": "analyze",
        "target": "code.py"
    })

    # Subscribe to events
    async def handler(message):
        print(f"Got: {message}")

    await bus.subscribe_events("dashboard", handler)
"""

import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Optional imports for RabbitMQ and Redis
try:
    import aio_pika
    from aio_pika import Message, DeliveryMode, ExchangeType
    from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractExchange, AbstractQueue
    HAS_RABBITMQ = True
except ImportError:
    HAS_RABBITMQ = False
    aio_pika = None

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    try:
        import aioredis
        HAS_REDIS = True
    except ImportError:
        HAS_REDIS = False
        aioredis = None


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ExchangeNames(str, Enum):
    """CKC RabbitMQ exchange names."""
    TASKS = "ckc.tasks"
    EVENTS = "ckc.events"
    ILCP = "ckc.ilcp"
    FEEDBACK = "ckc.feedback"
    DLX = "ckc.dlx"


@dataclass
class MessageBusConfig:
    """Message bus configuration."""
    # RabbitMQ settings
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"  # Use guest for default RabbitMQ
    rabbitmq_password: str = field(default_factory=lambda: os.getenv("CKC_MQ_PASSWORD", "guest"))
    rabbitmq_vhost: str = "/"  # Use default vhost
    rabbitmq_prefetch_count: int = 10

    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = field(default_factory=lambda: os.getenv("CKC_REDIS_PASSWORD"))
    redis_db: int = 0

    # General settings
    use_rabbitmq: bool = True
    use_redis: bool = True
    default_message_ttl: int = 3600  # 1 hour

    @property
    def rabbitmq_url(self) -> str:
        """Get RabbitMQ connection URL."""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"

    @classmethod
    def from_env(cls) -> "MessageBusConfig":
        """Create config from environment variables."""
        return cls(
            rabbitmq_host=os.getenv("CKC_MQ_HOST", "localhost"),
            rabbitmq_port=int(os.getenv("CKC_MQ_PORT", "5672")),
            rabbitmq_user=os.getenv("CKC_MQ_USER", "guest"),
            rabbitmq_password=os.getenv("CKC_MQ_PASSWORD", "guest"),
            rabbitmq_vhost=os.getenv("CKC_MQ_VHOST", "/"),
            redis_host=os.getenv("CKC_REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("CKC_REDIS_PORT", "6379")),
            redis_password=os.getenv("CKC_REDIS_PASSWORD"),
        )


@dataclass
class CKCMessage:
    """Standard CKC message format."""
    message_id: str
    message_type: str
    sender: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    context_id: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "sender": self.sender,
            "payload": self.payload,
            "priority": self.priority.value,
            "context_id": self.context_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CKCMessage":
        """Create from dictionary."""
        return cls(
            message_id=data["message_id"],
            message_type=data["message_type"],
            sender=data["sender"],
            payload=data["payload"],
            priority=MessagePriority(data.get("priority", "normal")),
            context_id=data.get("context_id"),
            correlation_id=data.get("correlation_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else data.get("timestamp", datetime.now()),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "CKCMessage":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


class BaseMessageHandler(ABC):
    """Base class for message handlers."""

    @abstractmethod
    async def handle(self, message: CKCMessage) -> None:
        """Handle a message."""
        pass


class CKCEventBus:
    """
    CKC Event Bus - Hybrid RabbitMQ + Redis implementation.

    Uses RabbitMQ for:
    - Task assignments to agents (guaranteed delivery)
    - ILCP messages between rooms
    - Feedback to Kommandant

    Uses Redis for:
    - Real-time event broadcasting
    - Dashboard updates
    - Volatile status updates
    """

    def __init__(self, config: Optional[MessageBusConfig] = None):
        self.config = config or MessageBusConfig.from_env()
        self._rabbitmq_connection: Optional[AbstractConnection] = None
        self._rabbitmq_channel: Optional[AbstractChannel] = None
        self._exchanges: Dict[str, AbstractExchange] = {}
        self._queues: Dict[str, AbstractQueue] = {}
        self._redis: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._initialized = False
        self._lock = asyncio.Lock()
        self._consumers: Dict[str, asyncio.Task] = {}

    async def initialize(self) -> bool:
        """Initialize the event bus connections."""
        async with self._lock:
            if self._initialized:
                return True

            success = True

            # Initialize RabbitMQ
            if self.config.use_rabbitmq and HAS_RABBITMQ:
                try:
                    self._rabbitmq_connection = await aio_pika.connect_robust(
                        self.config.rabbitmq_url,
                        timeout=10.0
                    )
                    self._rabbitmq_channel = await self._rabbitmq_connection.channel()
                    await self._rabbitmq_channel.set_qos(prefetch_count=self.config.rabbitmq_prefetch_count)

                    # Declare exchanges
                    await self._setup_exchanges()

                    logger.info("CKC Event Bus: RabbitMQ connected")
                except Exception as e:
                    logger.warning(f"CKC Event Bus: RabbitMQ not available: {e}")
                    success = False

            # Initialize Redis
            if self.config.use_redis and HAS_REDIS:
                try:
                    self._redis = await aioredis.from_url(
                        f"redis://{self.config.redis_host}:{self.config.redis_port}/{self.config.redis_db}",
                        password=self.config.redis_password,
                        decode_responses=True,
                    )
                    await self._redis.ping()
                    logger.info("CKC Event Bus: Redis connected")
                except Exception as e:
                    logger.warning(f"CKC Event Bus: Redis not available: {e}")
                    # Redis is optional, don't fail

            self._initialized = True
            return success

    async def _setup_exchanges(self) -> None:
        """Set up RabbitMQ exchanges."""
        if not self._rabbitmq_channel:
            return

        # Direct exchange for task routing
        self._exchanges["tasks"] = await self._rabbitmq_channel.declare_exchange(
            ExchangeNames.TASKS.value,
            ExchangeType.DIRECT,
            durable=True,
        )

        # Fanout exchange for events
        self._exchanges["events"] = await self._rabbitmq_channel.declare_exchange(
            ExchangeNames.EVENTS.value,
            ExchangeType.FANOUT,
            durable=True,
        )

        # Topic exchange for ILCP
        self._exchanges["ilcp"] = await self._rabbitmq_channel.declare_exchange(
            ExchangeNames.ILCP.value,
            ExchangeType.TOPIC,
            durable=True,
        )

        # Direct exchange for feedback
        self._exchanges["feedback"] = await self._rabbitmq_channel.declare_exchange(
            ExchangeNames.FEEDBACK.value,
            ExchangeType.DIRECT,
            durable=True,
        )

        # DLX for failed messages
        self._exchanges["dlx"] = await self._rabbitmq_channel.declare_exchange(
            ExchangeNames.DLX.value,
            ExchangeType.FANOUT,
            durable=True,
        )

    async def close(self) -> None:
        """Close all connections."""
        # Cancel all consumers
        for task in self._consumers.values():
            task.cancel()
        self._consumers.clear()

        # Close RabbitMQ
        if self._rabbitmq_connection:
            await self._rabbitmq_connection.close()
            self._rabbitmq_connection = None
            self._rabbitmq_channel = None

        # Close Redis
        if self._redis:
            await self._redis.close()
            self._redis = None

        self._initialized = False
        logger.info("CKC Event Bus: Connections closed")

    async def ensure_connected(self) -> None:
        """Ensure event bus is connected."""
        if not self._initialized:
            await self.initialize()

    # =====================================================
    # Task Publishing (RabbitMQ)
    # =====================================================

    async def publish_task(
        self,
        agent_id: str,
        payload: Dict[str, Any],
        context_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> str:
        """
        Publish a task to a specific agent.

        Args:
            agent_id: Target agent ID (e.g., "tool_explorer")
            payload: Task payload
            context_id: Optional task context ID
            priority: Message priority

        Returns:
            Message ID
        """
        await self.ensure_connected()

        import uuid
        message_id = f"task_{uuid.uuid4().hex[:16]}"

        message = CKCMessage(
            message_id=message_id,
            message_type="task_assignment",
            sender="kommandant",
            payload=payload,
            priority=priority,
            context_id=context_id,
        )

        if self._rabbitmq_channel and "tasks" in self._exchanges:
            amqp_message = Message(
                body=message.to_json().encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                message_id=message_id,
                priority=self._get_amqp_priority(priority),
            )

            await self._exchanges["tasks"].publish(
                amqp_message,
                routing_key=agent_id,
            )
            logger.debug(f"Published task {message_id} to {agent_id}")
        else:
            # Fallback to Redis
            if self._redis:
                await self._redis.lpush(f"tasks:{agent_id}", message.to_json())
                logger.debug(f"Published task {message_id} to Redis queue tasks:{agent_id}")

        return message_id

    async def subscribe_tasks(
        self,
        agent_id: str,
        handler: Callable[[CKCMessage], Awaitable[None]],
    ) -> None:
        """
        Subscribe to tasks for an agent.

        Args:
            agent_id: Agent ID to subscribe for
            handler: Async callback for handling messages
        """
        await self.ensure_connected()

        queue_name = f"tasks.{agent_id}"

        if self._rabbitmq_channel and "tasks" in self._exchanges:
            # Declare queue
            queue = await self._rabbitmq_channel.declare_queue(
                queue_name,
                durable=True,
                arguments={"x-dead-letter-exchange": ExchangeNames.DLX.value},
            )

            # Bind to exchange
            await queue.bind(self._exchanges["tasks"], routing_key=agent_id)

            # Start consuming
            async def consumer(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        ckc_message = CKCMessage.from_json(message.body.decode())
                        await handler(ckc_message)
                    except Exception as e:
                        logger.error(f"Error processing task: {e}")
                        raise

            task = asyncio.create_task(self._consume_queue(queue, consumer))
            self._consumers[f"tasks:{agent_id}"] = task
            logger.info(f"Subscribed to tasks for {agent_id}")

    async def _consume_queue(self, queue, handler) -> None:
        """Consume messages from a queue."""
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await handler(message)

    # =====================================================
    # Event Broadcasting (Redis Pub/Sub)
    # =====================================================

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        context_id: Optional[str] = None,
    ) -> str:
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event
            payload: Event payload
            context_id: Optional context ID

        Returns:
            Message ID
        """
        await self.ensure_connected()

        import uuid
        message_id = f"evt_{uuid.uuid4().hex[:16]}"

        message = CKCMessage(
            message_id=message_id,
            message_type=event_type,
            sender="system",
            payload=payload,
            context_id=context_id,
        )

        if self._redis:
            # Publish to Redis channel
            await self._redis.publish(f"ckc:events:{event_type}", message.to_json())
            logger.debug(f"Published event {event_type}: {message_id}")
        elif self._rabbitmq_channel and "events" in self._exchanges:
            # Fallback to RabbitMQ fanout
            amqp_message = Message(
                body=message.to_json().encode(),
                message_id=message_id,
            )
            await self._exchanges["events"].publish(amqp_message, routing_key="")

        return message_id

    async def subscribe_events(
        self,
        subscriber_id: str,
        handler: Callable[[CKCMessage], Awaitable[None]],
        event_types: Optional[List[str]] = None,
    ) -> None:
        """
        Subscribe to events.

        Args:
            subscriber_id: Unique subscriber ID
            handler: Async callback for handling events
            event_types: Optional list of event types to subscribe to (None = all)
        """
        await self.ensure_connected()

        if self._redis:
            pubsub = self._redis.pubsub()

            if event_types:
                channels = [f"ckc:events:{et}" for et in event_types]
            else:
                channels = ["ckc:events:*"]

            await pubsub.psubscribe(*channels)

            async def listener():
                try:
                    async for message in pubsub.listen():
                        if message["type"] in ("message", "pmessage"):
                            try:
                                ckc_message = CKCMessage.from_json(message["data"])
                                await handler(ckc_message)
                            except Exception as e:
                                logger.error(f"Error handling event: {e}")
                except asyncio.CancelledError:
                    await pubsub.unsubscribe()
                    raise

            task = asyncio.create_task(listener())
            self._consumers[f"events:{subscriber_id}"] = task
            logger.info(f"Subscribed {subscriber_id} to events: {event_types or 'all'}")

    # =====================================================
    # ILCP Messaging (RabbitMQ Topic Exchange)
    # =====================================================

    async def publish_ilcp(
        self,
        sender_room_id: int,
        recipient_room_id: int,
        message_type: str,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        context_id: Optional[str] = None,
    ) -> str:
        """
        Publish an ILCP message between learning rooms.

        Args:
            sender_room_id: Sender room ID
            recipient_room_id: Recipient room ID
            message_type: Type of ILCP message
            content: Message content
            priority: Message priority
            context_id: Optional context ID

        Returns:
            Message ID
        """
        await self.ensure_connected()

        import uuid
        message_id = f"ilcp_{uuid.uuid4().hex[:16]}"

        message = CKCMessage(
            message_id=message_id,
            message_type=message_type,
            sender=f"room_{sender_room_id}",
            payload={
                "sender_room_id": sender_room_id,
                "recipient_room_id": recipient_room_id,
                "content": content,
            },
            priority=priority,
            context_id=context_id,
        )

        routing_key = f"room.{recipient_room_id}.{message_type}"

        if self._rabbitmq_channel and "ilcp" in self._exchanges:
            amqp_message = Message(
                body=message.to_json().encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                message_id=message_id,
                priority=self._get_amqp_priority(priority),
            )
            await self._exchanges["ilcp"].publish(amqp_message, routing_key=routing_key)
            logger.debug(f"Published ILCP {message_id} to room {recipient_room_id}")
        else:
            # Fallback to Redis
            if self._redis:
                await self._redis.lpush(f"ilcp:room:{recipient_room_id}", message.to_json())

        return message_id

    async def subscribe_ilcp(
        self,
        room_id: int,
        handler: Callable[[CKCMessage], Awaitable[None]],
        message_types: Optional[List[str]] = None,
    ) -> None:
        """
        Subscribe to ILCP messages for a room.

        Args:
            room_id: Room ID to subscribe for
            handler: Async callback for handling messages
            message_types: Optional list of message types to subscribe to
        """
        await self.ensure_connected()

        queue_name = f"ilcp.room.{room_id}"

        if self._rabbitmq_channel and "ilcp" in self._exchanges:
            queue = await self._rabbitmq_channel.declare_queue(
                queue_name,
                durable=True,
            )

            # Bind to patterns
            if message_types:
                for mt in message_types:
                    await queue.bind(self._exchanges["ilcp"], routing_key=f"room.{room_id}.{mt}")
            else:
                await queue.bind(self._exchanges["ilcp"], routing_key=f"room.{room_id}.*")

            async def consumer(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        ckc_message = CKCMessage.from_json(message.body.decode())
                        await handler(ckc_message)
                    except Exception as e:
                        logger.error(f"Error processing ILCP message: {e}")
                        raise

            task = asyncio.create_task(self._consume_queue(queue, consumer))
            self._consumers[f"ilcp:room:{room_id}"] = task
            logger.info(f"Subscribed to ILCP for room {room_id}")

    # =====================================================
    # Feedback Messages (RabbitMQ Direct)
    # =====================================================

    async def publish_feedback(
        self,
        sender_agent: str,
        feedback_type: str,
        payload: Dict[str, Any],
        context_id: Optional[str] = None,
    ) -> str:
        """
        Publish feedback from an agent to Kommandant.

        Args:
            sender_agent: Agent sending feedback
            feedback_type: Type of feedback
            payload: Feedback payload
            context_id: Optional context ID

        Returns:
            Message ID
        """
        await self.ensure_connected()

        import uuid
        message_id = f"fb_{uuid.uuid4().hex[:16]}"

        message = CKCMessage(
            message_id=message_id,
            message_type=feedback_type,
            sender=sender_agent,
            payload=payload,
            context_id=context_id,
        )

        if self._rabbitmq_channel and "feedback" in self._exchanges:
            amqp_message = Message(
                body=message.to_json().encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                message_id=message_id,
            )
            await self._exchanges["feedback"].publish(amqp_message, routing_key="kommandant")
            logger.debug(f"Published feedback {message_id} from {sender_agent}")

        return message_id

    # =====================================================
    # Utility Methods
    # =====================================================

    def _get_amqp_priority(self, priority: MessagePriority) -> int:
        """Convert MessagePriority to AMQP priority (0-9)."""
        mapping = {
            MessagePriority.LOW: 1,
            MessagePriority.NORMAL: 5,
            MessagePriority.HIGH: 7,
            MessagePriority.URGENT: 9,
        }
        return mapping.get(priority, 5)

    async def health_check(self) -> Dict[str, Any]:
        """Check health of message bus connections."""
        health = {
            "status": "healthy",
            "rabbitmq": {"status": "disconnected"},
            "redis": {"status": "disconnected"},
        }

        # Check RabbitMQ
        if self._rabbitmq_connection and not self._rabbitmq_connection.is_closed:
            health["rabbitmq"] = {"status": "connected"}
        elif self.config.use_rabbitmq:
            health["status"] = "degraded"

        # Check Redis
        if self._redis:
            try:
                await self._redis.ping()
                health["redis"] = {"status": "connected"}
            except Exception:
                if self.config.use_redis:
                    health["status"] = "degraded"

        return health


# Singleton instance
_event_bus: Optional[CKCEventBus] = None
_event_bus_lock = asyncio.Lock()


async def get_event_bus(config: Optional[MessageBusConfig] = None) -> CKCEventBus:
    """
    Get the singleton event bus instance.

    Args:
        config: Optional configuration

    Returns:
        CKCEventBus instance
    """
    global _event_bus

    async with _event_bus_lock:
        if _event_bus is None:
            _event_bus = CKCEventBus(config)
            await _event_bus.initialize()

        return _event_bus


async def close_event_bus() -> None:
    """Close the singleton event bus."""
    global _event_bus

    async with _event_bus_lock:
        if _event_bus is not None:
            await _event_bus.close()
            _event_bus = None
