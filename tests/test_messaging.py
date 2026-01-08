"""
Tests for CKC MASTERMIND Messaging System (cirkelline.ckc.mastermind.messaging)
===============================================================================

Tests covering:
- Enums: MastermindMessageType, MessagePriority, MessageDelivery
- Data Classes: MastermindMessage, MessageAck, HandlerRegistration
- Abstract Base: MastermindMessageBus
- InMemoryMessageBus implementation
- RabbitMQMessageBus implementation (mock)
- MastermindMessageBuilder
- Convenience functions
- Factory functions
"""

import pytest
import pytest_asyncio
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from cirkelline.ckc.mastermind.messaging import (
    # Enums
    MastermindMessageType,
    MessagePriority,
    MessageDelivery,
    # Data Classes
    MastermindMessage,
    MessageAck,
    HandlerRegistration,
    # Message Bus implementations
    InMemoryMessageBus,
    RabbitMQMessageBus,
    # Builder
    MastermindMessageBuilder,
    # Convenience functions
    create_command_message,
    create_directive_message,
    create_status_message,
    create_result_message,
    # Factory
    create_message_bus,
    get_message_bus,
)


# =============================================================================
# TESTS FOR ENUMS
# =============================================================================

class TestMessagingEnums:
    """Tests for messaging enums."""

    def test_mastermind_message_type_command_values(self):
        """Test command message types."""
        assert MastermindMessageType.COMMAND_START.value == "command.start"
        assert MastermindMessageType.COMMAND_PAUSE.value == "command.pause"
        assert MastermindMessageType.COMMAND_RESUME.value == "command.resume"
        assert MastermindMessageType.COMMAND_ABORT.value == "command.abort"
        assert MastermindMessageType.COMMAND_ADJUST.value == "command.adjust"

    def test_mastermind_message_type_directive_values(self):
        """Test directive message types."""
        assert MastermindMessageType.DIRECTIVE_ASSIGN.value == "directive.assign"
        assert MastermindMessageType.DIRECTIVE_PRIORITIZE.value == "directive.prioritize"
        assert MastermindMessageType.DIRECTIVE_FEEDBACK.value == "directive.feedback"
        assert MastermindMessageType.DIRECTIVE_REALLOCATE.value == "directive.reallocate"

    def test_mastermind_message_type_status_values(self):
        """Test status message types."""
        assert MastermindMessageType.STATUS_AGENT_JOINED.value == "status.agent_joined"
        assert MastermindMessageType.STATUS_AGENT_LEFT.value == "status.agent_left"
        assert MastermindMessageType.STATUS_TASK_STARTED.value == "status.task_started"
        assert MastermindMessageType.STATUS_TASK_PROGRESS.value == "status.task_progress"
        assert MastermindMessageType.STATUS_TASK_COMPLETED.value == "status.task_completed"
        assert MastermindMessageType.STATUS_TASK_FAILED.value == "status.task_failed"

    def test_mastermind_message_type_result_values(self):
        """Test result message types."""
        assert MastermindMessageType.RESULT_PARTIAL.value == "result.partial"
        assert MastermindMessageType.RESULT_FINAL.value == "result.final"

    def test_mastermind_message_type_feedback_values(self):
        """Test feedback message types."""
        assert MastermindMessageType.FEEDBACK_REPORT.value == "feedback.report"
        assert MastermindMessageType.FEEDBACK_ALERT.value == "feedback.alert"
        assert MastermindMessageType.FEEDBACK_RECOMMENDATION.value == "feedback.recommendation"

    def test_mastermind_message_type_system_values(self):
        """Test system message types."""
        assert MastermindMessageType.HEARTBEAT.value == "system.heartbeat"
        assert MastermindMessageType.ACK.value == "system.ack"
        assert MastermindMessageType.ERROR.value == "system.error"

    def test_message_priority_values(self):
        """Test message priority levels."""
        assert MessagePriority.LOW.value == 1
        assert MessagePriority.NORMAL.value == 2
        assert MessagePriority.HIGH.value == 3
        assert MessagePriority.URGENT.value == 4
        assert MessagePriority.CRITICAL.value == 5

    def test_message_delivery_values(self):
        """Test message delivery guarantees."""
        assert MessageDelivery.FIRE_AND_FORGET.value == "fire_and_forget"
        assert MessageDelivery.AT_LEAST_ONCE.value == "at_least_once"
        assert MessageDelivery.EXACTLY_ONCE.value == "exactly_once"


# =============================================================================
# TESTS FOR DATA CLASSES
# =============================================================================

class TestMastermindMessage:
    """Tests for MastermindMessage dataclass."""

    def test_message_creation_minimal(self):
        """Test creating message with minimal parameters."""
        msg = MastermindMessage(
            message_id="msg_001",
            session_id="session_001",
            message_type=MastermindMessageType.COMMAND_START,
            source="super_admin",
            destination="dirigent",
            payload={"command": "start"}
        )
        assert msg.message_id == "msg_001"
        assert msg.session_id == "session_001"
        assert msg.message_type == MastermindMessageType.COMMAND_START
        assert msg.priority == MessagePriority.NORMAL  # default
        assert msg.requires_ack is False  # default

    def test_message_creation_full(self):
        """Test creating message with all parameters."""
        now = datetime.now()
        msg = MastermindMessage(
            message_id="msg_002",
            session_id="session_002",
            message_type=MastermindMessageType.DIRECTIVE_ASSIGN,
            source="dirigent",
            destination="agent_001",
            payload={"task": "analyze"},
            priority=MessagePriority.HIGH,
            requires_ack=True,
            timestamp=now,
            correlation_id="corr_001",
            reply_to="reply_queue",
            ttl_seconds=300,
            headers={"X-Custom": "value"}
        )
        assert msg.priority == MessagePriority.HIGH
        assert msg.requires_ack is True
        assert msg.timestamp == now
        assert msg.correlation_id == "corr_001"
        assert msg.reply_to == "reply_queue"
        assert msg.ttl_seconds == 300
        assert msg.headers["X-Custom"] == "value"

    def test_message_to_dict(self):
        """Test message serialization to dict."""
        msg = MastermindMessage(
            message_id="msg_003",
            session_id="session_003",
            message_type=MastermindMessageType.STATUS_TASK_PROGRESS,
            source="agent_001",
            destination="all",
            payload={"progress": 50}
        )
        data = msg.to_dict()

        assert data["message_id"] == "msg_003"
        assert data["message_type"] == "status.task_progress"
        assert data["priority"] == 2  # NORMAL value
        assert "timestamp" in data

    def test_message_from_dict(self):
        """Test message deserialization from dict."""
        data = {
            "message_id": "msg_004",
            "session_id": "session_004",
            "message_type": "command.abort",
            "source": "super_admin",
            "destination": "all",
            "payload": {"reason": "timeout"},
            "priority": 5,
            "requires_ack": True,
            "timestamp": "2025-01-01T12:00:00"
        }
        msg = MastermindMessage.from_dict(data)

        assert msg.message_id == "msg_004"
        assert msg.message_type == MastermindMessageType.COMMAND_ABORT
        assert msg.priority == MessagePriority.CRITICAL
        assert msg.requires_ack is True

    def test_message_to_json(self):
        """Test message serialization to JSON."""
        msg = MastermindMessage(
            message_id="msg_005",
            session_id="session_005",
            message_type=MastermindMessageType.HEARTBEAT,
            source="system",
            destination="all",
            payload={}
        )
        json_str = msg.to_json()

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["message_id"] == "msg_005"

    def test_message_from_json(self):
        """Test message deserialization from JSON."""
        json_str = '{"message_id": "msg_006", "session_id": "s006", "message_type": "system.error", "source": "sys", "destination": "all", "payload": {"error": "test"}, "timestamp": "2025-01-01T00:00:00"}'
        msg = MastermindMessage.from_json(json_str)

        assert msg.message_id == "msg_006"
        assert msg.message_type == MastermindMessageType.ERROR


class TestMessageAck:
    """Tests for MessageAck dataclass."""

    def test_ack_creation_success(self):
        """Test creating a successful ack."""
        ack = MessageAck(
            ack_id="ack_001",
            message_id="msg_001",
            session_id="session_001",
            acknowledged_by="agent_001"
        )
        assert ack.success is True
        assert ack.error is None

    def test_ack_creation_failure(self):
        """Test creating a failed ack."""
        ack = MessageAck(
            ack_id="ack_002",
            message_id="msg_002",
            session_id="session_002",
            acknowledged_by="agent_002",
            success=False,
            error="Processing failed"
        )
        assert ack.success is False
        assert ack.error == "Processing failed"

    def test_ack_to_dict(self):
        """Test ack serialization."""
        ack = MessageAck(
            ack_id="ack_003",
            message_id="msg_003",
            session_id="session_003",
            acknowledged_by="agent_003"
        )
        data = ack.to_dict()

        assert data["ack_id"] == "ack_003"
        assert data["message_id"] == "msg_003"
        assert data["success"] is True


class TestHandlerRegistration:
    """Tests for HandlerRegistration dataclass."""

    def test_handler_registration_sync(self):
        """Test sync handler registration."""
        def sync_handler(msg):
            pass

        reg = HandlerRegistration(
            handler_id="hdl_001",
            message_types={MastermindMessageType.COMMAND_START},
            handler=sync_handler,
            is_async=False
        )
        assert reg.handler_id == "hdl_001"
        assert reg.is_async is False

    def test_handler_registration_async(self):
        """Test async handler registration."""
        async def async_handler(msg):
            pass

        reg = HandlerRegistration(
            handler_id="hdl_002",
            message_types={MastermindMessageType.STATUS_TASK_PROGRESS, MastermindMessageType.STATUS_TASK_COMPLETED},
            handler=async_handler,
            is_async=True,
            filter_session="session_001"
        )
        assert reg.is_async is True
        assert len(reg.message_types) == 2
        assert reg.filter_session == "session_001"


# =============================================================================
# TESTS FOR INMEMORY MESSAGE BUS
# =============================================================================

class TestInMemoryMessageBus:
    """Tests for InMemoryMessageBus implementation."""

    @pytest.fixture
    def bus(self):
        """Create a fresh message bus for each test."""
        return InMemoryMessageBus()

    @pytest.mark.asyncio
    async def test_connect(self, bus):
        """Test connecting to message bus."""
        result = await bus.connect()
        assert result is True
        assert bus._connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self, bus):
        """Test disconnecting from message bus."""
        await bus.connect()
        result = await bus.disconnect()
        assert result is True
        assert bus._connected is False

    @pytest.mark.asyncio
    async def test_publish_without_connect_raises(self, bus):
        """Test publishing without connection raises error."""
        msg = MastermindMessage(
            message_id="msg_001",
            session_id="s001",
            message_type=MastermindMessageType.HEARTBEAT,
            source="test",
            destination="all",
            payload={}
        )
        with pytest.raises(RuntimeError, match="ikke forbundet"):
            await bus.publish(msg)

    @pytest.mark.asyncio
    async def test_publish_message(self, bus):
        """Test publishing a message."""
        await bus.connect()

        msg = MastermindMessage(
            message_id="msg_001",
            session_id="s001",
            message_type=MastermindMessageType.COMMAND_START,
            source="super_admin",
            destination="dirigent",
            payload={"test": True}
        )
        result = await bus.publish(msg)

        assert result is True
        assert len(bus._message_history) == 1

    @pytest.mark.asyncio
    async def test_subscribe_sync_handler(self, bus):
        """Test subscribing with sync handler."""
        await bus.connect()

        received = []
        def handler(msg):
            received.append(msg)

        handler_id = await bus.subscribe(
            [MastermindMessageType.COMMAND_START],
            handler
        )

        assert handler_id.startswith("hdl_")
        assert handler_id in bus._handlers

    @pytest.mark.asyncio
    async def test_subscribe_async_handler(self, bus):
        """Test subscribing with async handler."""
        await bus.connect()

        received = []
        async def handler(msg):
            received.append(msg)

        handler_id = await bus.subscribe(
            [MastermindMessageType.STATUS_TASK_PROGRESS],
            handler
        )

        assert handler_id in bus._handlers
        assert bus._handlers[handler_id].is_async is True

    @pytest.mark.asyncio
    async def test_message_delivery_to_handler(self, bus):
        """Test that messages are delivered to matching handlers."""
        await bus.connect()

        received = []
        async def handler(msg):
            received.append(msg)

        await bus.subscribe([MastermindMessageType.COMMAND_START], handler)

        msg = MastermindMessage(
            message_id="msg_001",
            session_id="s001",
            message_type=MastermindMessageType.COMMAND_START,
            source="super_admin",
            destination="all",
            payload={}
        )
        await bus.publish(msg)

        assert len(received) == 1
        assert received[0].message_id == "msg_001"

    @pytest.mark.asyncio
    async def test_message_not_delivered_to_non_matching_handler(self, bus):
        """Test that non-matching messages are not delivered."""
        await bus.connect()

        received = []
        async def handler(msg):
            received.append(msg)

        await bus.subscribe([MastermindMessageType.COMMAND_PAUSE], handler)

        msg = MastermindMessage(
            message_id="msg_001",
            session_id="s001",
            message_type=MastermindMessageType.COMMAND_START,
            source="super_admin",
            destination="all",
            payload={}
        )
        await bus.publish(msg)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus):
        """Test unsubscribing from messages."""
        await bus.connect()

        handler_id = await bus.subscribe(
            [MastermindMessageType.HEARTBEAT],
            lambda m: None
        )

        result = await bus.unsubscribe(handler_id)
        assert result is True
        assert handler_id not in bus._handlers

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, bus):
        """Test unsubscribing with invalid handler_id."""
        await bus.connect()
        result = await bus.unsubscribe("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_acknowledge_message(self, bus):
        """Test acknowledging a message."""
        await bus.connect()

        msg = MastermindMessage(
            message_id="msg_001",
            session_id="s001",
            message_type=MastermindMessageType.COMMAND_START,
            source="super_admin",
            destination="dirigent",
            payload={},
            requires_ack=True
        )
        await bus.publish(msg)

        result = await bus.acknowledge(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_message_history(self, bus):
        """Test retrieving message history."""
        await bus.connect()

        for i in range(5):
            msg = MastermindMessage(
                message_id=f"msg_{i}",
                session_id="s001",
                message_type=MastermindMessageType.HEARTBEAT,
                source="system",
                destination="all",
                payload={}
            )
            await bus.publish(msg)

        history = bus.get_message_history()
        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_get_message_history_with_session_filter(self, bus):
        """Test message history with session filter."""
        await bus.connect()

        for i in range(3):
            msg = MastermindMessage(
                message_id=f"msg_s1_{i}",
                session_id="session_1",
                message_type=MastermindMessageType.HEARTBEAT,
                source="system",
                destination="all",
                payload={}
            )
            await bus.publish(msg)

        for i in range(2):
            msg = MastermindMessage(
                message_id=f"msg_s2_{i}",
                session_id="session_2",
                message_type=MastermindMessageType.HEARTBEAT,
                source="system",
                destination="all",
                payload={}
            )
            await bus.publish(msg)

        history = bus.get_message_history(session_id="session_1")
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_source_filter(self, bus):
        """Test message filtering by source."""
        await bus.connect()

        received = []
        async def handler(msg):
            received.append(msg)

        await bus.subscribe(
            [MastermindMessageType.COMMAND_START],
            handler,
            filter_source="super_admin"
        )

        # This should be delivered (matching source)
        msg1 = MastermindMessage(
            message_id="msg_001",
            session_id="s001",
            message_type=MastermindMessageType.COMMAND_START,
            source="super_admin",
            destination="all",
            payload={}
        )
        await bus.publish(msg1)

        # This should NOT be delivered (non-matching source)
        msg2 = MastermindMessage(
            message_id="msg_002",
            session_id="s001",
            message_type=MastermindMessageType.COMMAND_START,
            source="other_source",
            destination="all",
            payload={}
        )
        await bus.publish(msg2)

        assert len(received) == 1
        assert received[0].source == "super_admin"


# =============================================================================
# TESTS FOR RABBITMQ MESSAGE BUS
# =============================================================================

class TestRabbitMQMessageBus:
    """Tests for RabbitMQMessageBus implementation (mock)."""

    @pytest.fixture
    def bus(self):
        """Create RabbitMQ bus instance."""
        return RabbitMQMessageBus(
            host="localhost",
            port=5672,
            username="guest",
            password="guest"
        )

    @pytest.mark.asyncio
    async def test_connect(self, bus):
        """Test mock connect."""
        result = await bus.connect()
        assert result is True

    @pytest.mark.asyncio
    async def test_disconnect(self, bus):
        """Test mock disconnect."""
        await bus.connect()
        result = await bus.disconnect()
        assert result is True

    @pytest.mark.asyncio
    async def test_publish(self, bus):
        """Test mock publish."""
        await bus.connect()

        msg = MastermindMessage(
            message_id="msg_001",
            session_id="s001",
            message_type=MastermindMessageType.COMMAND_START,
            source="super_admin",
            destination="dirigent",
            payload={}
        )
        result = await bus.publish(msg)
        assert result is True

    @pytest.mark.asyncio
    async def test_subscribe(self, bus):
        """Test mock subscribe."""
        await bus.connect()

        handler_id = await bus.subscribe(
            [MastermindMessageType.DIRECTIVE_ASSIGN],
            lambda m: None
        )
        assert handler_id.startswith("hdl_")

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus):
        """Test mock unsubscribe."""
        await bus.connect()

        handler_id = await bus.subscribe(
            [MastermindMessageType.DIRECTIVE_ASSIGN],
            lambda m: None
        )
        result = await bus.unsubscribe(handler_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_acknowledge(self, bus):
        """Test mock acknowledge."""
        await bus.connect()

        msg = MastermindMessage(
            message_id="msg_001",
            session_id="s001",
            message_type=MastermindMessageType.COMMAND_START,
            source="super_admin",
            destination="dirigent",
            payload={}
        )
        result = await bus.acknowledge(msg)
        assert result is True

    def test_exchange_routing(self, bus):
        """Test exchange selection based on message type."""
        assert bus._get_exchange_for_type(MastermindMessageType.COMMAND_START) == bus.EXCHANGE_COMMANDS
        assert bus._get_exchange_for_type(MastermindMessageType.DIRECTIVE_ASSIGN) == bus.EXCHANGE_DIRECTIVES
        assert bus._get_exchange_for_type(MastermindMessageType.RESULT_FINAL) == bus.EXCHANGE_RESULTS
        assert bus._get_exchange_for_type(MastermindMessageType.STATUS_TASK_PROGRESS) == bus.EXCHANGE_STATUS
        assert bus._get_exchange_for_type(MastermindMessageType.FEEDBACK_ALERT) == bus.EXCHANGE_FEEDBACK


# =============================================================================
# TESTS FOR MESSAGE BUILDER
# =============================================================================

class TestMastermindMessageBuilder:
    """Tests for MastermindMessageBuilder."""

    def test_builder_minimal(self):
        """Test building message with minimal config."""
        msg = MastermindMessageBuilder("session_001", "super_admin") \
            .type(MastermindMessageType.COMMAND_START) \
            .payload({"command": "go"}) \
            .build()

        assert msg.session_id == "session_001"
        assert msg.source == "super_admin"
        assert msg.message_type == MastermindMessageType.COMMAND_START
        assert msg.destination == "all"  # default

    def test_builder_full_config(self):
        """Test building message with full configuration."""
        msg = MastermindMessageBuilder("session_002", "dirigent") \
            .type(MastermindMessageType.DIRECTIVE_ASSIGN) \
            .to("agent_001") \
            .payload({"task": "analyze"}) \
            .priority(MessagePriority.HIGH) \
            .require_ack(True) \
            .correlation("corr_001") \
            .reply_to("reply_queue") \
            .ttl(600) \
            .header("X-Custom", "value") \
            .build()

        assert msg.destination == "agent_001"
        assert msg.priority == MessagePriority.HIGH
        assert msg.requires_ack is True
        assert msg.correlation_id == "corr_001"
        assert msg.reply_to == "reply_queue"
        assert msg.ttl_seconds == 600
        assert msg.headers["X-Custom"] == "value"

    def test_builder_without_type_raises(self):
        """Test that building without type raises error."""
        with pytest.raises(ValueError, match="type er påkrævet"):
            MastermindMessageBuilder("s001", "test").build()

    def test_builder_method_chaining(self):
        """Test that all builder methods return self."""
        builder = MastermindMessageBuilder("s001", "test")

        assert builder.type(MastermindMessageType.HEARTBEAT) is builder
        assert builder.to("all") is builder
        assert builder.payload({}) is builder
        assert builder.priority(MessagePriority.LOW) is builder
        assert builder.require_ack() is builder
        assert builder.correlation("c1") is builder
        assert builder.reply_to("r1") is builder
        assert builder.ttl(100) is builder
        assert builder.header("k", "v") is builder


# =============================================================================
# TESTS FOR CONVENIENCE FUNCTIONS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for message creation convenience functions."""

    def test_create_command_message(self):
        """Test creating command message."""
        msg = create_command_message(
            session_id="s001",
            command_type=MastermindMessageType.COMMAND_START,
            payload={"target": "all_agents"}
        )

        assert msg.source == "super_admin"
        assert msg.destination == "dirigent"
        assert msg.message_type == MastermindMessageType.COMMAND_START
        assert msg.priority == MessagePriority.HIGH
        assert msg.requires_ack is True

    def test_create_directive_message(self):
        """Test creating directive message."""
        msg = create_directive_message(
            session_id="s002",
            directive_type=MastermindMessageType.DIRECTIVE_ASSIGN,
            target_agent="agent_001",
            payload={"task_id": "t001"}
        )

        assert msg.source == "dirigent"
        assert msg.destination == "agent_001"
        assert msg.message_type == MastermindMessageType.DIRECTIVE_ASSIGN
        assert msg.requires_ack is True

    def test_create_status_message(self):
        """Test creating status message."""
        msg = create_status_message(
            session_id="s003",
            agent_id="agent_002",
            status_type=MastermindMessageType.STATUS_TASK_PROGRESS,
            payload={"progress": 75}
        )

        assert msg.source == "agent_002"
        assert msg.destination == "all"
        assert msg.message_type == MastermindMessageType.STATUS_TASK_PROGRESS

    def test_create_result_message_final(self):
        """Test creating final result message."""
        msg = create_result_message(
            session_id="s004",
            agent_id="agent_003",
            task_id="task_001",
            result={"analysis": "complete"},
            is_final=True
        )

        assert msg.source == "agent_003"
        assert msg.destination == "dirigent"
        assert msg.message_type == MastermindMessageType.RESULT_FINAL
        assert msg.requires_ack is True
        assert msg.payload["is_final"] is True

    def test_create_result_message_partial(self):
        """Test creating partial result message."""
        msg = create_result_message(
            session_id="s005",
            agent_id="agent_004",
            task_id="task_002",
            result={"partial_data": "in_progress"},
            is_final=False
        )

        assert msg.message_type == MastermindMessageType.RESULT_PARTIAL
        assert msg.requires_ack is False
        assert msg.payload["is_final"] is False


# =============================================================================
# TESTS FOR FACTORY FUNCTIONS
# =============================================================================

class TestFactoryFunctions:
    """Tests for message bus factory functions."""

    def test_create_in_memory_bus(self):
        """Test creating in-memory bus."""
        bus = create_message_bus(use_rabbitmq=False)

        assert isinstance(bus, InMemoryMessageBus)

    def test_create_rabbitmq_bus(self):
        """Test creating RabbitMQ bus."""
        bus = create_message_bus(
            use_rabbitmq=True,
            host="rabbit.example.com",
            port=5673
        )

        assert isinstance(bus, RabbitMQMessageBus)
        assert bus.host == "rabbit.example.com"
        assert bus.port == 5673

    def test_get_message_bus(self):
        """Test getting current bus instance."""
        created = create_message_bus(use_rabbitmq=False)
        retrieved = get_message_bus()

        assert retrieved is created


# =============================================================================
# TESTS FOR MODULE IMPORTS
# =============================================================================

class TestMessagingModuleImports:
    """Tests for messaging module imports."""

    def test_all_exports_importable(self):
        """Test that all expected exports are available."""
        from cirkelline.ckc.mastermind import messaging

        # Enums
        assert hasattr(messaging, 'MastermindMessageType')
        assert hasattr(messaging, 'MessagePriority')
        assert hasattr(messaging, 'MessageDelivery')

        # Data classes
        assert hasattr(messaging, 'MastermindMessage')
        assert hasattr(messaging, 'MessageAck')
        assert hasattr(messaging, 'HandlerRegistration')

        # Classes
        assert hasattr(messaging, 'InMemoryMessageBus')
        assert hasattr(messaging, 'RabbitMQMessageBus')
        assert hasattr(messaging, 'MastermindMessageBuilder')

        # Functions
        assert hasattr(messaging, 'create_command_message')
        assert hasattr(messaging, 'create_directive_message')
        assert hasattr(messaging, 'create_status_message')
        assert hasattr(messaging, 'create_result_message')
        assert hasattr(messaging, 'create_message_bus')
        assert hasattr(messaging, 'get_message_bus')
