"""
CKC MASTERMIND Messaging System
================================

Realtids kommunikation for MASTERMIND Tilstand.

Exchanges:
- ckc.mastermind.commands    - Super Admin kommandoer
- ckc.mastermind.directives  - Systems Dirigent instruktioner
- ckc.mastermind.results     - Agent delresultater
- ckc.mastermind.status      - Status opdateringer
- ckc.mastermind.feedback    - Realtids feedback loop
"""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


# =============================================================================
# MESSAGE TYPES & ENUMS
# =============================================================================

class MastermindMessageType(Enum):
    """Typer af MASTERMIND beskeder."""
    # Commands from Super Admin
    COMMAND_START = "command.start"
    COMMAND_PAUSE = "command.pause"
    COMMAND_RESUME = "command.resume"
    COMMAND_ABORT = "command.abort"
    COMMAND_ADJUST = "command.adjust"

    # Directives from Dirigent
    DIRECTIVE_ASSIGN = "directive.assign"
    DIRECTIVE_PRIORITIZE = "directive.prioritize"
    DIRECTIVE_FEEDBACK = "directive.feedback"
    DIRECTIVE_REALLOCATE = "directive.reallocate"

    # Status updates
    STATUS_AGENT_JOINED = "status.agent_joined"
    STATUS_AGENT_LEFT = "status.agent_left"
    STATUS_TASK_STARTED = "status.task_started"
    STATUS_TASK_PROGRESS = "status.task_progress"
    STATUS_TASK_COMPLETED = "status.task_completed"
    STATUS_TASK_FAILED = "status.task_failed"
    STATUS_SESSION_UPDATE = "status.session_update"

    # Results
    RESULT_PARTIAL = "result.partial"
    RESULT_FINAL = "result.final"

    # Feedback
    FEEDBACK_REPORT = "feedback.report"
    FEEDBACK_ALERT = "feedback.alert"
    FEEDBACK_RECOMMENDATION = "feedback.recommendation"

    # System
    HEARTBEAT = "system.heartbeat"
    ACK = "system.ack"
    ERROR = "system.error"


class MessagePriority(Enum):
    """Prioritet for beskeder."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class MessageDelivery(Enum):
    """Leveringsgaranti."""
    FIRE_AND_FORGET = "fire_and_forget"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


# =============================================================================
# MESSAGE DATA CLASSES
# =============================================================================

@dataclass
class MastermindMessage:
    """En besked i MASTERMIND systemet."""
    message_id: str
    session_id: str
    message_type: MastermindMessageType
    source: str  # "super_admin", "dirigent", agent_id
    destination: str  # "all", "dirigent", agent_id
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    requires_ack: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl_seconds: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "message_type": self.message_type.value,
            "source": self.source,
            "destination": self.destination,
            "payload": self.payload,
            "priority": self.priority.value,
            "requires_ack": self.requires_ack,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "ttl_seconds": self.ttl_seconds,
            "headers": self.headers
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MastermindMessage":
        return cls(
            message_id=data["message_id"],
            session_id=data["session_id"],
            message_type=MastermindMessageType(data["message_type"]),
            source=data["source"],
            destination=data["destination"],
            payload=data.get("payload", {}),
            priority=MessagePriority(data.get("priority", 2)),
            requires_ack=data.get("requires_ack", False),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            ttl_seconds=data.get("ttl_seconds"),
            headers=data.get("headers", {})
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "MastermindMessage":
        return cls.from_dict(json.loads(json_str))


@dataclass
class MessageAck:
    """Acknowledgement af en besked."""
    ack_id: str
    message_id: str
    session_id: str
    acknowledged_by: str
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ack_id": self.ack_id,
            "message_id": self.message_id,
            "session_id": self.session_id,
            "acknowledged_by": self.acknowledged_by,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error
        }


# =============================================================================
# MESSAGE HANDLERS
# =============================================================================

MessageHandler = Callable[[MastermindMessage], None]
AsyncMessageHandler = Callable[[MastermindMessage], Awaitable[None]]


@dataclass
class HandlerRegistration:
    """Registration af en message handler."""
    handler_id: str
    message_types: Set[MastermindMessageType]
    handler: Union[MessageHandler, AsyncMessageHandler]
    is_async: bool
    filter_source: Optional[str] = None
    filter_session: Optional[str] = None


# =============================================================================
# MESSAGE BUS (Abstract)
# =============================================================================

class MastermindMessageBus(ABC):
    """Abstract base for MASTERMIND message bus."""

    @abstractmethod
    async def connect(self) -> bool:
        """Forbind til message bus."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Afbryd forbindelse."""
        pass

    @abstractmethod
    async def publish(self, message: MastermindMessage) -> bool:
        """Publicér en besked."""
        pass

    @abstractmethod
    async def subscribe(
        self,
        message_types: List[MastermindMessageType],
        handler: Union[MessageHandler, AsyncMessageHandler],
        filter_source: Optional[str] = None,
        filter_session: Optional[str] = None
    ) -> str:
        """Abonner på beskeder. Returnerer handler_id."""
        pass

    @abstractmethod
    async def unsubscribe(self, handler_id: str) -> bool:
        """Afmeld abonnement."""
        pass

    @abstractmethod
    async def acknowledge(self, message: MastermindMessage, success: bool = True, error: Optional[str] = None) -> bool:
        """Bekræft modtagelse af besked."""
        pass


# =============================================================================
# IN-MEMORY MESSAGE BUS (For testing/development)
# =============================================================================

class InMemoryMessageBus(MastermindMessageBus):
    """
    In-memory implementation af message bus.

    Brugt til testing og development uden RabbitMQ.
    """

    def __init__(self):
        self._connected = False
        self._handlers: Dict[str, HandlerRegistration] = {}
        self._message_history: List[MastermindMessage] = []
        self._pending_acks: Dict[str, MastermindMessage] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        self._connected = True
        logger.info("InMemoryMessageBus forbundet")
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        logger.info("InMemoryMessageBus afbrudt")
        return True

    async def publish(self, message: MastermindMessage) -> bool:
        if not self._connected:
            raise RuntimeError("Message bus ikke forbundet")

        # Collect matching handlers while holding lock
        handlers_to_call = []
        async with self._lock:
            # Store in history
            self._message_history.append(message)

            # Track for ack if needed
            if message.requires_ack:
                self._pending_acks[message.message_id] = message

            # Collect handlers that match (copy to avoid holding lock during execution)
            for registration in self._handlers.values():
                if self._matches_handler(message, registration):
                    handlers_to_call.append(registration)

        # Call handlers OUTSIDE the lock to prevent deadlock
        for registration in handlers_to_call:
            try:
                if registration.is_async:
                    await registration.handler(message)
                else:
                    registration.handler(message)
            except Exception as e:
                logger.error(f"Handler fejl for {message.message_id}: {e}")

        logger.debug(f"Besked publiceret: {message.message_id} ({message.message_type.value})")
        return True

    async def subscribe(
        self,
        message_types: List[MastermindMessageType],
        handler: Union[MessageHandler, AsyncMessageHandler],
        filter_source: Optional[str] = None,
        filter_session: Optional[str] = None
    ) -> str:
        handler_id = f"hdl_{secrets.token_hex(6)}"

        is_async = asyncio.iscoroutinefunction(handler)

        registration = HandlerRegistration(
            handler_id=handler_id,
            message_types=set(message_types),
            handler=handler,
            is_async=is_async,
            filter_source=filter_source,
            filter_session=filter_session
        )

        async with self._lock:
            self._handlers[handler_id] = registration

        logger.debug(f"Handler registreret: {handler_id} for {[mt.value for mt in message_types]}")
        return handler_id

    async def unsubscribe(self, handler_id: str) -> bool:
        async with self._lock:
            if handler_id in self._handlers:
                del self._handlers[handler_id]
                logger.debug(f"Handler afmeldt: {handler_id}")
                return True
        return False

    async def acknowledge(
        self,
        message: MastermindMessage,
        success: bool = True,
        error: Optional[str] = None
    ) -> bool:
        # Remove from pending acks while holding lock
        async with self._lock:
            if message.message_id in self._pending_acks:
                del self._pending_acks[message.message_id]

        # Create ack message (no lock needed for creation)
        ack = MessageAck(
            ack_id=f"ack_{secrets.token_hex(6)}",
            message_id=message.message_id,
            session_id=message.session_id,
            acknowledged_by="self",  # Would be actual agent_id
            success=success,
            error=error
        )

        ack_message = MastermindMessage(
            message_id=f"msg_{secrets.token_hex(8)}",
            session_id=message.session_id,
            message_type=MastermindMessageType.ACK,
            source="self",
            destination=message.source,
            payload=ack.to_dict(),
            correlation_id=message.message_id
        )

        # Publish OUTSIDE the lock to prevent deadlock
        await self.publish(ack_message)
        return True

    def _matches_handler(
        self,
        message: MastermindMessage,
        registration: HandlerRegistration
    ) -> bool:
        """Check om besked matcher handler's filters."""
        # Check message type
        if message.message_type not in registration.message_types:
            return False

        # Check source filter
        if registration.filter_source and message.source != registration.filter_source:
            return False

        # Check session filter
        if registration.filter_session and message.session_id != registration.filter_session:
            return False

        return True

    def get_message_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[MastermindMessage]:
        """Hent beskedhistorik (til debugging)."""
        messages = self._message_history

        if session_id:
            messages = [m for m in messages if m.session_id == session_id]

        return messages[-limit:]

    def get_pending_acks(self) -> List[MastermindMessage]:
        """Hent ventende acks."""
        return list(self._pending_acks.values())


# =============================================================================
# RABBITMQ MESSAGE BUS (Production)
# =============================================================================

class RabbitMQMessageBus(MastermindMessageBus):
    """
    RabbitMQ-baseret message bus til production.

    Exchanges:
    - ckc.mastermind.commands (topic)
    - ckc.mastermind.directives (topic)
    - ckc.mastermind.results (topic)
    - ckc.mastermind.status (topic)
    - ckc.mastermind.feedback (topic)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        username: str = "guest",
        password: str = "guest",
        virtual_host: str = "/"
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host

        self._connection = None
        self._channel = None
        self._handlers: Dict[str, HandlerRegistration] = {}
        self._consumer_tags: Dict[str, str] = {}

        # Exchange names
        self.EXCHANGE_COMMANDS = "ckc.mastermind.commands"
        self.EXCHANGE_DIRECTIVES = "ckc.mastermind.directives"
        self.EXCHANGE_RESULTS = "ckc.mastermind.results"
        self.EXCHANGE_STATUS = "ckc.mastermind.status"
        self.EXCHANGE_FEEDBACK = "ckc.mastermind.feedback"

    async def connect(self) -> bool:
        """Forbind til RabbitMQ."""
        try:
            # Note: This requires aio-pika or similar library
            # For now, we'll use mock implementation
            logger.info(f"RabbitMQ forbindelse forsøgt til {self.host}:{self.port}")

            # In real implementation:
            # import aio_pika
            # self._connection = await aio_pika.connect_robust(
            #     f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/{self.virtual_host}"
            # )
            # self._channel = await self._connection.channel()
            # await self._setup_exchanges()

            # Mock success for development
            self._connection = True
            self._channel = True

            logger.info("RabbitMQ forbundet (mock)")
            return True

        except Exception as e:
            logger.error(f"RabbitMQ forbindelsesfejl: {e}")
            return False

    async def disconnect(self) -> bool:
        """Afbryd forbindelse til RabbitMQ."""
        try:
            if self._connection:
                # In real implementation:
                # await self._connection.close()
                self._connection = None
                self._channel = None

            logger.info("RabbitMQ afbrudt")
            return True

        except Exception as e:
            logger.error(f"RabbitMQ afbrydningsfejl: {e}")
            return False

    async def _setup_exchanges(self):
        """Setup RabbitMQ exchanges."""
        # In real implementation:
        # import aio_pika
        # for exchange_name in [
        #     self.EXCHANGE_COMMANDS,
        #     self.EXCHANGE_DIRECTIVES,
        #     self.EXCHANGE_RESULTS,
        #     self.EXCHANGE_STATUS,
        #     self.EXCHANGE_FEEDBACK
        # ]:
        #     await self._channel.declare_exchange(
        #         exchange_name,
        #         aio_pika.ExchangeType.TOPIC,
        #         durable=True
        #     )
        pass

    def _get_exchange_for_type(self, message_type: MastermindMessageType) -> str:
        """Bestem exchange baseret på message type."""
        type_value = message_type.value

        if type_value.startswith("command."):
            return self.EXCHANGE_COMMANDS
        elif type_value.startswith("directive."):
            return self.EXCHANGE_DIRECTIVES
        elif type_value.startswith("result."):
            return self.EXCHANGE_RESULTS
        elif type_value.startswith("status."):
            return self.EXCHANGE_STATUS
        elif type_value.startswith("feedback."):
            return self.EXCHANGE_FEEDBACK
        else:
            return self.EXCHANGE_STATUS  # Default

    async def publish(self, message: MastermindMessage) -> bool:
        """Publicér besked til RabbitMQ."""
        if not self._channel:
            raise RuntimeError("RabbitMQ ikke forbundet")

        try:
            exchange_name = self._get_exchange_for_type(message.message_type)
            routing_key = f"{message.session_id}.{message.message_type.value}.{message.destination}"

            # In real implementation:
            # import aio_pika
            # exchange = await self._channel.get_exchange(exchange_name)
            # await exchange.publish(
            #     aio_pika.Message(
            #         body=message.to_json().encode(),
            #         delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            #         priority=message.priority.value,
            #         expiration=str(message.ttl_seconds * 1000) if message.ttl_seconds else None,
            #         correlation_id=message.correlation_id,
            #         reply_to=message.reply_to,
            #         headers=message.headers
            #     ),
            #     routing_key=routing_key
            # )

            # For now, use in-memory fallback
            logger.debug(f"RabbitMQ publish (mock): {message.message_id} -> {exchange_name}")
            return True

        except Exception as e:
            logger.error(f"RabbitMQ publish fejl: {e}")
            return False

    async def subscribe(
        self,
        message_types: List[MastermindMessageType],
        handler: Union[MessageHandler, AsyncMessageHandler],
        filter_source: Optional[str] = None,
        filter_session: Optional[str] = None
    ) -> str:
        """Abonner på beskeder fra RabbitMQ."""
        handler_id = f"hdl_{secrets.token_hex(6)}"

        is_async = asyncio.iscoroutinefunction(handler)

        registration = HandlerRegistration(
            handler_id=handler_id,
            message_types=set(message_types),
            handler=handler,
            is_async=is_async,
            filter_source=filter_source,
            filter_session=filter_session
        )

        self._handlers[handler_id] = registration

        # In real implementation:
        # - Create queue for this handler
        # - Bind to relevant exchanges with routing patterns
        # - Start consuming

        logger.debug(f"RabbitMQ subscription (mock): {handler_id}")
        return handler_id

    async def unsubscribe(self, handler_id: str) -> bool:
        """Afmeld abonnement."""
        if handler_id in self._handlers:
            del self._handlers[handler_id]

            # In real implementation:
            # - Cancel consumer
            # - Delete queue

            return True

        return False

    async def acknowledge(
        self,
        message: MastermindMessage,
        success: bool = True,
        error: Optional[str] = None
    ) -> bool:
        """Bekræft modtagelse."""
        # In real implementation:
        # - Send ack via RabbitMQ message
        # - Update message state

        logger.debug(f"RabbitMQ ack (mock): {message.message_id}")
        return True


# =============================================================================
# MESSAGE BUILDER
# =============================================================================

class MastermindMessageBuilder:
    """Builder til at oprette MASTERMIND beskeder."""

    def __init__(self, session_id: str, source: str):
        self._session_id = session_id
        self._source = source
        self._message_id = f"msg_{secrets.token_hex(8)}"
        self._message_type: Optional[MastermindMessageType] = None
        self._destination = "all"
        self._payload: Dict[str, Any] = {}
        self._priority = MessagePriority.NORMAL
        self._requires_ack = False
        self._correlation_id: Optional[str] = None
        self._reply_to: Optional[str] = None
        self._ttl_seconds: Optional[int] = None
        self._headers: Dict[str, str] = {}

    def type(self, message_type: MastermindMessageType) -> "MastermindMessageBuilder":
        """Sæt beskedtype."""
        self._message_type = message_type
        return self

    def to(self, destination: str) -> "MastermindMessageBuilder":
        """Sæt destination."""
        self._destination = destination
        return self

    def payload(self, payload: Dict[str, Any]) -> "MastermindMessageBuilder":
        """Sæt payload."""
        self._payload = payload
        return self

    def priority(self, priority: MessagePriority) -> "MastermindMessageBuilder":
        """Sæt prioritet."""
        self._priority = priority
        return self

    def require_ack(self, require: bool = True) -> "MastermindMessageBuilder":
        """Kræv acknowledgement."""
        self._requires_ack = require
        return self

    def correlation(self, correlation_id: str) -> "MastermindMessageBuilder":
        """Sæt correlation ID."""
        self._correlation_id = correlation_id
        return self

    def reply_to(self, reply_to: str) -> "MastermindMessageBuilder":
        """Sæt reply-to."""
        self._reply_to = reply_to
        return self

    def ttl(self, seconds: int) -> "MastermindMessageBuilder":
        """Sæt TTL."""
        self._ttl_seconds = seconds
        return self

    def header(self, key: str, value: str) -> "MastermindMessageBuilder":
        """Tilføj header."""
        self._headers[key] = value
        return self

    def build(self) -> MastermindMessage:
        """Byg beskeden."""
        if not self._message_type:
            raise ValueError("Message type er påkrævet")

        return MastermindMessage(
            message_id=self._message_id,
            session_id=self._session_id,
            message_type=self._message_type,
            source=self._source,
            destination=self._destination,
            payload=self._payload,
            priority=self._priority,
            requires_ack=self._requires_ack,
            correlation_id=self._correlation_id,
            reply_to=self._reply_to,
            ttl_seconds=self._ttl_seconds,
            headers=self._headers
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_command_message(
    session_id: str,
    command_type: MastermindMessageType,
    payload: Dict[str, Any],
    priority: MessagePriority = MessagePriority.HIGH
) -> MastermindMessage:
    """Opret en command besked fra Super Admin."""
    return MastermindMessageBuilder(session_id, "super_admin") \
        .type(command_type) \
        .to("dirigent") \
        .payload(payload) \
        .priority(priority) \
        .require_ack(True) \
        .build()


def create_directive_message(
    session_id: str,
    directive_type: MastermindMessageType,
    target_agent: str,
    payload: Dict[str, Any]
) -> MastermindMessage:
    """Opret en direktiv besked fra Dirigent."""
    return MastermindMessageBuilder(session_id, "dirigent") \
        .type(directive_type) \
        .to(target_agent) \
        .payload(payload) \
        .priority(MessagePriority.NORMAL) \
        .require_ack(True) \
        .build()


def create_status_message(
    session_id: str,
    agent_id: str,
    status_type: MastermindMessageType,
    payload: Dict[str, Any]
) -> MastermindMessage:
    """Opret en status besked fra en agent."""
    return MastermindMessageBuilder(session_id, agent_id) \
        .type(status_type) \
        .to("all") \
        .payload(payload) \
        .build()


def create_result_message(
    session_id: str,
    agent_id: str,
    task_id: str,
    result: Any,
    is_final: bool = True
) -> MastermindMessage:
    """Opret en resultat besked."""
    return MastermindMessageBuilder(session_id, agent_id) \
        .type(MastermindMessageType.RESULT_FINAL if is_final else MastermindMessageType.RESULT_PARTIAL) \
        .to("dirigent") \
        .payload({
            "task_id": task_id,
            "result": result,
            "is_final": is_final
        }) \
        .require_ack(is_final) \
        .build()


# =============================================================================
# FACTORY
# =============================================================================

_message_bus_instance: Optional[MastermindMessageBus] = None


def create_message_bus(
    use_rabbitmq: bool = False,
    **kwargs
) -> MastermindMessageBus:
    """Opret message bus instance."""
    global _message_bus_instance

    if use_rabbitmq:
        _message_bus_instance = RabbitMQMessageBus(**kwargs)
    else:
        _message_bus_instance = InMemoryMessageBus()

    return _message_bus_instance


def get_message_bus() -> Optional[MastermindMessageBus]:
    """Hent den aktuelle message bus instance."""
    return _message_bus_instance
