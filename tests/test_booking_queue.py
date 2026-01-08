"""
Booking Queue Worker Tests
==========================

Tests for SQS-based booking queue worker.
Supports 1M+ bookings overnight with batch processing.

Princip: "Man behøver ikke se for at vide - vi bygger så alt er gennemsigtigt."
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from cirkelline.booking import (
    BookingStatus,
    QueueConfig,
    BookingMessage,
    WorkerStats,
    QueueClient,
    LocalQueueClient,
    SQSQueueClient,
    BookingProcessor,
    DatabaseBookingProcessor,
    BookingWorker,
    get_booking_worker,
    start_booking_worker,
    stop_booking_worker,
)


# =============================================================================
# BOOKING STATUS TESTS
# =============================================================================

class TestBookingStatus:
    """Test BookingStatus enum."""

    def test_pending_status(self):
        """Test pending status value."""
        assert BookingStatus.PENDING.value == "pending"

    def test_confirmed_status(self):
        """Test confirmed status value."""
        assert BookingStatus.CONFIRMED.value == "confirmed"

    def test_cancelled_status(self):
        """Test cancelled status value."""
        assert BookingStatus.CANCELLED.value == "cancelled"

    def test_failed_status(self):
        """Test failed status value."""
        assert BookingStatus.FAILED.value == "failed"

    def test_processing_status(self):
        """Test processing status value."""
        assert BookingStatus.PROCESSING.value == "processing"


# =============================================================================
# QUEUE CONFIG TESTS
# =============================================================================

class TestQueueConfig:
    """Test QueueConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = QueueConfig()
        assert config.queue_url == ""
        assert config.region == "eu-north-1"
        assert config.visibility_timeout == 30
        assert config.max_messages == 10
        assert config.wait_time_seconds == 20
        assert config.batch_size == 100
        assert config.max_concurrent_batches == 10
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 1.0
        assert config.db_pool_size == 20

    def test_custom_config(self):
        """Test custom configuration."""
        config = QueueConfig(
            queue_url="https://sqs.eu-north-1.amazonaws.com/123456789/test-queue",
            region="eu-west-1",
            visibility_timeout=60,
            max_messages=5,
            batch_size=50,
        )
        assert config.queue_url == "https://sqs.eu-north-1.amazonaws.com/123456789/test-queue"
        assert config.region == "eu-west-1"
        assert config.visibility_timeout == 60
        assert config.max_messages == 5
        assert config.batch_size == 50

    def test_from_env(self):
        """Test config from environment variables."""
        with patch.dict("os.environ", {
            "SQS_BOOKING_QUEUE_URL": "https://test-queue",
            "AWS_REGION": "us-east-1",
        }):
            config = QueueConfig.from_env()
            assert config.queue_url == "https://test-queue"
            assert config.region == "us-east-1"


# =============================================================================
# BOOKING MESSAGE TESTS
# =============================================================================

class TestBookingMessage:
    """Test BookingMessage dataclass."""

    def test_from_sqs_message(self):
        """Test creating BookingMessage from SQS message."""
        sqs_message = {
            "MessageId": "msg-123",
            "ReceiptHandle": "receipt-123",
            "Body": json.dumps({
                "booking_id": "booking-456",
                "user_id": "user-789",
                "service_id": "service-101",
                "booking_time": "2025-12-14T10:00:00",
                "metadata": {"notes": "Test booking"},
            }),
        }

        booking = BookingMessage.from_sqs_message(sqs_message)

        assert booking.message_id == "msg-123"
        assert booking.receipt_handle == "receipt-123"
        assert booking.booking_id == "booking-456"
        assert booking.user_id == "user-789"
        assert booking.service_id == "service-101"
        assert booking.booking_time == datetime(2025, 12, 14, 10, 0, 0)
        assert booking.metadata == {"notes": "Test booking"}

    def test_from_sqs_message_minimal(self):
        """Test with minimal SQS message."""
        sqs_message = {
            "MessageId": "msg-123",
            "ReceiptHandle": "receipt-123",
            "Body": "{}",
        }

        booking = BookingMessage.from_sqs_message(sqs_message)

        assert booking.message_id == "msg-123"
        assert booking.receipt_handle == "receipt-123"
        assert booking.user_id == ""
        assert booking.service_id == ""


# =============================================================================
# WORKER STATS TESTS
# =============================================================================

class TestWorkerStats:
    """Test WorkerStats dataclass."""

    def test_default_stats(self):
        """Test default stats values."""
        stats = WorkerStats()
        assert stats.messages_received == 0
        assert stats.messages_processed == 0
        assert stats.messages_failed == 0
        assert stats.batches_processed == 0
        assert stats.total_processing_time_ms == 0.0
        assert stats.last_batch_at is None

    def test_avg_processing_time_zero(self):
        """Test average processing time when no messages."""
        stats = WorkerStats()
        assert stats.avg_processing_time_ms == 0.0

    def test_avg_processing_time_calculated(self):
        """Test average processing time calculation."""
        stats = WorkerStats(
            messages_processed=10,
            total_processing_time_ms=1000.0,
        )
        assert stats.avg_processing_time_ms == 100.0

    def test_to_dict(self):
        """Test stats serialization."""
        now = datetime.now()
        stats = WorkerStats(
            messages_received=100,
            messages_processed=95,
            messages_failed=5,
            batches_processed=10,
            total_processing_time_ms=5000.0,
            last_batch_at=now,
        )

        result = stats.to_dict()

        assert result["messages_received"] == 100
        assert result["messages_processed"] == 95
        assert result["messages_failed"] == 5
        assert result["batches_processed"] == 10
        assert result["avg_processing_time_ms"] == 52.63
        assert result["last_batch_at"] == now.isoformat()


# =============================================================================
# LOCAL QUEUE CLIENT TESTS
# =============================================================================

class TestLocalQueueClient:
    """Test LocalQueueClient for testing."""

    @pytest.mark.asyncio
    async def test_send_and_receive(self):
        """Test sending and receiving messages."""
        client = LocalQueueClient()

        # Send message
        message_id = await client.send_message({
            "booking_id": "test-123",
            "user_id": "user-456",
        })

        assert message_id.startswith("msg-")

        # Receive message
        messages = await client.receive_messages(10)
        assert len(messages) == 1
        assert messages[0]["MessageId"] == message_id

    @pytest.mark.asyncio
    async def test_delete_message(self):
        """Test deleting a message."""
        client = LocalQueueClient()

        await client.send_message({"test": "data"})
        messages = await client.receive_messages(10)
        receipt_handle = messages[0]["ReceiptHandle"]

        result = await client.delete_message(receipt_handle)
        assert result is True

        # Should return False for non-existent handle
        result = await client.delete_message("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_messages_batch(self):
        """Test batch deletion."""
        client = LocalQueueClient()

        # Send multiple messages
        for i in range(5):
            await client.send_message({"id": i})

        messages = await client.receive_messages(10)
        handles = [m["ReceiptHandle"] for m in messages]

        deleted = await client.delete_messages_batch(handles)
        assert deleted == 5

    @pytest.mark.asyncio
    async def test_receive_empty_queue(self):
        """Test receiving from empty queue."""
        client = LocalQueueClient()
        messages = await client.receive_messages(10)
        assert messages == []


# =============================================================================
# SQS QUEUE CLIENT TESTS
# =============================================================================

class TestSQSQueueClient:
    """Test SQSQueueClient (mocked)."""

    def test_init(self):
        """Test SQS client initialization."""
        config = QueueConfig(
            queue_url="https://sqs.eu-north-1.amazonaws.com/123/test",
            region="eu-north-1",
        )
        client = SQSQueueClient(config)

        assert client.config == config
        assert client._client is None

    @pytest.mark.asyncio
    async def test_receive_messages_mocked(self):
        """Test receiving messages with mocked AWS client."""
        config = QueueConfig(queue_url="https://test-queue")
        client = SQSQueueClient(config)

        mock_aws_client = AsyncMock()
        mock_aws_client.receive_message = AsyncMock(return_value={
            "Messages": [
                {"MessageId": "msg-1", "Body": '{"test": 1}'},
                {"MessageId": "msg-2", "Body": '{"test": 2}'},
            ]
        })
        client._client = mock_aws_client

        messages = await client.receive_messages(10)

        assert len(messages) == 2
        mock_aws_client.receive_message.assert_called_once()


# =============================================================================
# BOOKING PROCESSOR TESTS
# =============================================================================

class TestDatabaseBookingProcessor:
    """Test DatabaseBookingProcessor."""

    @pytest.mark.asyncio
    async def test_process_batch_mock(self):
        """Test batch processing with mock (no DB)."""
        import os
        os.environ["TESTING"] = "true"

        processor = DatabaseBookingProcessor()

        # Create test bookings
        bookings = []
        for i in range(5):
            booking = BookingMessage(
                message_id=f"msg-{i}",
                receipt_handle=f"receipt-{i}",
                booking_id=f"booking-{i}",
                user_id="user-1",
                service_id="service-1",
                booking_time=datetime.now(),
            )
            bookings.append(booking)

        # Process (mock mode without asyncpg)
        processed = await processor.process_batch(bookings)

        assert processed == 5

        # Cleanup
        os.environ.pop("TESTING", None)


# =============================================================================
# BOOKING WORKER TESTS
# =============================================================================

class TestBookingWorker:
    """Test BookingWorker."""

    def test_init_default(self):
        """Test worker initialization with defaults."""
        worker = BookingWorker()

        assert isinstance(worker._queue, LocalQueueClient)
        assert isinstance(worker._processor, DatabaseBookingProcessor)
        assert worker._running is False

    def test_init_custom(self):
        """Test worker with custom components."""
        config = QueueConfig(batch_size=50)
        queue = LocalQueueClient()
        processor = DatabaseBookingProcessor()

        worker = BookingWorker(
            config=config,
            queue_client=queue,
            processor=processor,
        )

        assert worker.config.batch_size == 50
        assert worker._queue is queue
        assert worker._processor is processor

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Test starting and stopping worker."""
        worker = BookingWorker()

        await worker.start(num_workers=2)
        assert worker._running is True
        assert len(worker._tasks) == 2

        await worker.stop()
        assert worker._running is False
        assert len(worker._tasks) == 0

    @pytest.mark.asyncio
    async def test_process_messages(self):
        """Test processing messages end-to-end."""
        worker = BookingWorker()

        # Add messages to local queue
        for i in range(3):
            await worker._queue.send_message({
                "booking_id": f"booking-{i}",
                "user_id": "user-1",
                "service_id": "service-1",
                "booking_time": datetime.now().isoformat(),
            })

        # Start worker briefly
        await worker.start(num_workers=1)
        await asyncio.sleep(0.2)  # Let it process
        await worker.stop()

        # Check stats
        stats = worker.get_stats()
        assert stats["messages_received"] >= 3
        assert stats["running"] is False

    def test_get_stats(self):
        """Test getting worker stats."""
        worker = BookingWorker()
        stats = worker.get_stats()

        assert "messages_received" in stats
        assert "messages_processed" in stats
        assert "messages_failed" in stats
        assert "batches_processed" in stats
        assert "running" in stats
        assert "worker_count" in stats


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestFactoryFunctions:
    """Test factory functions."""

    def test_get_booking_worker_singleton(self):
        """Test get_booking_worker returns singleton."""
        # Reset global state
        import cirkelline.booking.queue_worker as qw
        qw._worker = None

        worker1 = get_booking_worker()
        worker2 = get_booking_worker()

        assert worker1 is worker2

        # Cleanup
        qw._worker = None

    @pytest.mark.asyncio
    async def test_start_and_stop_booking_worker(self):
        """Test start and stop global worker."""
        import cirkelline.booking.queue_worker as qw
        qw._worker = None

        worker = await start_booking_worker(num_workers=2)
        assert worker._running is True

        await stop_booking_worker()
        assert qw._worker is None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for booking queue system."""

    @pytest.fixture(autouse=True)
    def setup_test_env(self):
        """Set TESTING env var for all integration tests."""
        import os
        os.environ["TESTING"] = "true"
        yield
        os.environ.pop("TESTING", None)

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete booking workflow."""
        # Setup
        config = QueueConfig(batch_size=10)
        queue = LocalQueueClient()
        processor = DatabaseBookingProcessor()
        worker = BookingWorker(
            config=config,
            queue_client=queue,
            processor=processor,
        )

        # Send bookings
        for i in range(10):
            await queue.send_message({
                "booking_id": f"booking-{i}",
                "user_id": f"user-{i % 3}",
                "service_id": "service-main",
                "booking_time": datetime.now().isoformat(),
                "metadata": {"source": "test"},
            })

        # Process
        await worker.start(num_workers=2)
        await asyncio.sleep(0.3)
        await worker.stop()

        # Verify
        stats = worker.get_stats()
        assert stats["messages_received"] == 10
        assert stats["messages_processed"] == 10
        assert stats["messages_failed"] == 0

    @pytest.mark.asyncio
    async def test_high_volume(self):
        """Test high volume message processing."""
        queue = LocalQueueClient()
        worker = BookingWorker(queue_client=queue)

        # Send 100 messages
        for i in range(100):
            await queue.send_message({
                "booking_id": f"booking-{i}",
                "user_id": "user-1",
                "service_id": "service-1",
                "booking_time": datetime.now().isoformat(),
            })

        # Process with multiple workers
        await worker.start(num_workers=5)
        await asyncio.sleep(0.5)
        await worker.stop()

        stats = worker.get_stats()
        assert stats["messages_received"] == 100
        assert stats["messages_processed"] == 100

    @pytest.mark.asyncio
    async def test_worker_resilience(self):
        """Test worker continues after errors."""
        queue = LocalQueueClient()

        # Custom processor that fails sometimes
        class FailingProcessor(BookingProcessor):
            def __init__(self):
                self.call_count = 0

            async def process_batch(self, bookings):
                self.call_count += 1
                if self.call_count == 1:
                    raise Exception("Simulated failure")
                return len(bookings)

        processor = FailingProcessor()
        worker = BookingWorker(queue_client=queue, processor=processor)

        # Send messages
        for i in range(5):
            await queue.send_message({
                "booking_id": f"booking-{i}",
                "user_id": "user-1",
                "service_id": "service-1",
                "booking_time": datetime.now().isoformat(),
            })

        # Process - should recover from first failure
        await worker.start(num_workers=1)
        await asyncio.sleep(0.3)
        await worker.stop()

        # Worker should still have processed something
        assert processor.call_count >= 1


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance tests."""

    @pytest.fixture(autouse=True)
    def setup_test_env(self):
        """Set TESTING env var for performance tests."""
        import os
        os.environ["TESTING"] = "true"
        yield
        os.environ.pop("TESTING", None)

    @pytest.mark.asyncio
    async def test_message_throughput(self):
        """Test message throughput."""
        import time

        queue = LocalQueueClient()
        worker = BookingWorker(queue_client=queue)

        # Send 50 messages
        start = time.time()
        for i in range(50):
            await queue.send_message({
                "booking_id": f"booking-{i}",
                "user_id": "user-1",
                "service_id": "service-1",
                "booking_time": datetime.now().isoformat(),
            })

        await worker.start(num_workers=5)
        await asyncio.sleep(0.3)
        await worker.stop()
        elapsed = time.time() - start

        stats = worker.get_stats()
        throughput = stats["messages_processed"] / elapsed

        # Should process at least 100 messages/second
        assert throughput > 100, f"Throughput too low: {throughput:.1f} msg/s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
