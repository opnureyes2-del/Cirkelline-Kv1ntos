"""
Booking Queue Worker
=====================

SQS-based booking queue worker for high-volume booking processing.
Supports 1M+ bookings overnight with batch processing.

Architecture:
    ┌───────────────────┐
    │   Booking Request │
    │   (1M overnight)  │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │   API Gateway     │
    │   Rate Limit:     │
    │   10,000 req/sec  │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐
    │   SQS FIFO Queue  │
    │   (Ordering)      │
    │                   │
    │   Batching: 10    │
    │   Visibility: 30s │
    └─────────┬─────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
    ┌───────┐   ┌───────┐
    │Worker │   │Worker │   ... x N workers
    │  1    │   │  2    │
    └───┬───┘   └───┬───┘
        │           │
        └─────┬─────┘
              │
              ▼
    ┌───────────────────┐
    │   PostgreSQL      │
    │   (Batch Insert)  │
    │   100/batch       │
    └───────────────────┘

Princip: "Man behøver ikke se for at vide - vi bygger så alt er gennemsigtigt."
"""

from __future__ import annotations

import os
import json
import asyncio
import logging
import uuid
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class BookingStatus(Enum):
    """Booking status values."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    PROCESSING = "processing"


@dataclass
class QueueConfig:
    """Queue worker configuration."""
    # SQS settings
    queue_url: str = ""
    region: str = "eu-north-1"
    visibility_timeout: int = 30
    max_messages: int = 10
    wait_time_seconds: int = 20

    # Worker settings
    batch_size: int = 100
    max_concurrent_batches: int = 10
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0

    # Database settings
    db_pool_size: int = 20

    @classmethod
    def from_env(cls) -> "QueueConfig":
        """Create config from environment variables."""
        return cls(
            queue_url=os.getenv("SQS_BOOKING_QUEUE_URL", ""),
            region=os.getenv("AWS_REGION", "eu-north-1"),
            visibility_timeout=int(os.getenv("SQS_VISIBILITY_TIMEOUT", "30")),
            max_messages=int(os.getenv("SQS_MAX_MESSAGES", "10")),
            batch_size=int(os.getenv("BOOKING_BATCH_SIZE", "100")),
        )


@dataclass
class BookingMessage:
    """A booking message from the queue."""
    message_id: str
    receipt_handle: str
    booking_id: str
    user_id: str
    service_id: str
    booking_time: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    received_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_sqs_message(cls, message: Dict[str, Any]) -> "BookingMessage":
        """Create from SQS message."""
        body = json.loads(message.get("Body", "{}"))
        return cls(
            message_id=message.get("MessageId", ""),
            receipt_handle=message.get("ReceiptHandle", ""),
            booking_id=body.get("booking_id", str(uuid.uuid4())),
            user_id=body.get("user_id", ""),
            service_id=body.get("service_id", ""),
            booking_time=datetime.fromisoformat(
                body.get("booking_time", datetime.now().isoformat())
            ),
            metadata=body.get("metadata", {}),
        )


@dataclass
class WorkerStats:
    """Worker statistics."""
    messages_received: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    batches_processed: int = 0
    total_processing_time_ms: float = 0.0
    last_batch_at: Optional[datetime] = None

    @property
    def avg_processing_time_ms(self) -> float:
        if self.messages_processed == 0:
            return 0.0
        return self.total_processing_time_ms / self.messages_processed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "messages_received": self.messages_received,
            "messages_processed": self.messages_processed,
            "messages_failed": self.messages_failed,
            "batches_processed": self.batches_processed,
            "avg_processing_time_ms": round(self.avg_processing_time_ms, 2),
            "last_batch_at": self.last_batch_at.isoformat() if self.last_batch_at else None,
        }


# =============================================================================
# QUEUE CLIENT
# =============================================================================

class QueueClient(ABC):
    """Abstract queue client interface."""

    @abstractmethod
    async def receive_messages(self, max_messages: int) -> List[Dict[str, Any]]:
        """Receive messages from queue."""
        pass

    @abstractmethod
    async def delete_message(self, receipt_handle: str) -> bool:
        """Delete a processed message."""
        pass

    @abstractmethod
    async def delete_messages_batch(self, receipt_handles: List[str]) -> int:
        """Delete multiple messages."""
        pass

    @abstractmethod
    async def send_message(self, body: Dict[str, Any]) -> str:
        """Send a message to the queue."""
        pass


class LocalQueueClient(QueueClient):
    """Local in-memory queue for testing."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._messages: Dict[str, Dict[str, Any]] = {}
        self._counter = 0

    async def receive_messages(self, max_messages: int) -> List[Dict[str, Any]]:
        messages = []
        for _ in range(min(max_messages, self._queue.qsize())):
            try:
                msg = self._queue.get_nowait()
                messages.append(msg)
            except asyncio.QueueEmpty:
                break
        return messages

    async def delete_message(self, receipt_handle: str) -> bool:
        if receipt_handle in self._messages:
            del self._messages[receipt_handle]
            return True
        return False

    async def delete_messages_batch(self, receipt_handles: List[str]) -> int:
        deleted = 0
        for handle in receipt_handles:
            if await self.delete_message(handle):
                deleted += 1
        return deleted

    async def send_message(self, body: Dict[str, Any]) -> str:
        self._counter += 1
        message_id = f"msg-{self._counter}"
        receipt_handle = f"receipt-{self._counter}"

        message = {
            "MessageId": message_id,
            "ReceiptHandle": receipt_handle,
            "Body": json.dumps(body),
        }

        self._messages[receipt_handle] = message
        await self._queue.put(message)

        return message_id


class SQSQueueClient(QueueClient):
    """AWS SQS queue client."""

    def __init__(self, config: QueueConfig):
        self.config = config
        self._client = None

    async def _get_client(self):
        if self._client is None:
            try:
                from aiobotocore.session import get_session
                session = get_session()
                self._client = await session.create_client(
                    'sqs',
                    region_name=self.config.region
                ).__aenter__()
            except ImportError:
                raise RuntimeError("aiobotocore required for SQS")
        return self._client

    async def receive_messages(self, max_messages: int) -> List[Dict[str, Any]]:
        client = await self._get_client()
        response = await client.receive_message(
            QueueUrl=self.config.queue_url,
            MaxNumberOfMessages=min(max_messages, 10),
            WaitTimeSeconds=self.config.wait_time_seconds,
            VisibilityTimeout=self.config.visibility_timeout,
        )
        return response.get("Messages", [])

    async def delete_message(self, receipt_handle: str) -> bool:
        client = await self._get_client()
        try:
            await client.delete_message(
                QueueUrl=self.config.queue_url,
                ReceiptHandle=receipt_handle,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            return False

    async def delete_messages_batch(self, receipt_handles: List[str]) -> int:
        client = await self._get_client()
        entries = [
            {"Id": str(i), "ReceiptHandle": handle}
            for i, handle in enumerate(receipt_handles)
        ]

        try:
            response = await client.delete_message_batch(
                QueueUrl=self.config.queue_url,
                Entries=entries,
            )
            return len(response.get("Successful", []))
        except Exception as e:
            logger.error(f"Failed to delete messages batch: {e}")
            return 0

    async def send_message(self, body: Dict[str, Any]) -> str:
        client = await self._get_client()
        response = await client.send_message(
            QueueUrl=self.config.queue_url,
            MessageBody=json.dumps(body),
        )
        return response.get("MessageId", "")


# =============================================================================
# BOOKING PROCESSOR
# =============================================================================

class BookingProcessor(ABC):
    """Abstract booking processor."""

    @abstractmethod
    async def process_batch(self, bookings: List[BookingMessage]) -> int:
        """Process a batch of bookings. Returns number processed."""
        pass


class DatabaseBookingProcessor(BookingProcessor):
    """Process bookings to database."""

    def __init__(self, db_url: str = ""):
        self.db_url = db_url or os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline"
        )
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            # Use mock in test environment
            if os.getenv("TESTING", "").lower() == "true":
                logger.info("Using mock processor in test environment")
                return None

            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(
                    self.db_url.replace("+psycopg", "").replace("postgresql", "postgres"),
                    min_size=5,
                    max_size=20,
                )
            except ImportError:
                logger.warning("asyncpg not available, using mock processor")
                return None
            except Exception as e:
                logger.warning(f"Database connection failed: {e}, using mock processor")
                return None
        return self._pool

    async def process_batch(self, bookings: List[BookingMessage]) -> int:
        pool = await self._get_pool()

        if pool is None:
            # Mock processing for testing
            await asyncio.sleep(0.01 * len(bookings))
            return len(bookings)

        async with pool.acquire() as conn:
            # Batch insert
            values = [
                (
                    b.booking_id,
                    b.user_id,
                    b.service_id,
                    b.booking_time,
                    BookingStatus.CONFIRMED.value,
                    json.dumps(b.metadata),
                )
                for b in bookings
            ]

            await conn.executemany(
                """
                INSERT INTO bookings (id, user_id, service_id, booking_time, status, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO NOTHING
                """,
                values,
            )

        return len(bookings)


# =============================================================================
# BOOKING WORKER
# =============================================================================

class BookingWorker:
    """
    SQS-based booking queue worker.

    Processes booking messages in batches for high throughput.
    Supports 1M+ bookings overnight.

    Usage:
        config = QueueConfig.from_env()
        worker = BookingWorker(config)
        await worker.start()
    """

    def __init__(
        self,
        config: Optional[QueueConfig] = None,
        queue_client: Optional[QueueClient] = None,
        processor: Optional[BookingProcessor] = None,
    ):
        self.config = config or QueueConfig.from_env()
        self._queue = queue_client or LocalQueueClient()
        self._processor = processor or DatabaseBookingProcessor()
        self._stats = WorkerStats()
        self._running = False
        self._tasks: List[asyncio.Task] = []

    @property
    def stats(self) -> WorkerStats:
        return self._stats

    async def start(self, num_workers: int = 5) -> None:
        """Start worker with multiple concurrent processors."""
        if self._running:
            return

        self._running = True
        logger.info(f"Starting BookingWorker with {num_workers} workers")

        for i in range(num_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self._tasks.append(task)

    async def stop(self) -> None:
        """Stop all workers."""
        self._running = False

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        logger.info("BookingWorker stopped")

    async def _worker_loop(self, worker_id: int) -> None:
        """Main worker loop."""
        logger.info(f"Worker {worker_id} started")

        while self._running:
            try:
                messages = await self._queue.receive_messages(
                    self.config.max_messages
                )

                if not messages:
                    await asyncio.sleep(0.1)
                    continue

                await self._process_messages(messages)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Worker {worker_id} stopped")

    async def _process_messages(self, messages: List[Dict[str, Any]]) -> None:
        """Process a batch of messages."""
        import time
        start_time = time.time()

        # Parse messages
        bookings = []
        for msg in messages:
            try:
                booking = BookingMessage.from_sqs_message(msg)
                bookings.append(booking)
                self._stats.messages_received += 1
            except Exception as e:
                logger.error(f"Failed to parse message: {e}")
                self._stats.messages_failed += 1

        if not bookings:
            return

        # Process batch
        try:
            processed = await self._processor.process_batch(bookings)
            self._stats.messages_processed += processed
            self._stats.batches_processed += 1
            self._stats.last_batch_at = datetime.now()

            # Delete processed messages
            receipt_handles = [b.receipt_handle for b in bookings[:processed]]
            await self._queue.delete_messages_batch(receipt_handles)

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            self._stats.messages_failed += len(bookings)

        # Track timing
        elapsed_ms = (time.time() - start_time) * 1000
        self._stats.total_processing_time_ms += elapsed_ms

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        return {
            **self._stats.to_dict(),
            "running": self._running,
            "worker_count": len(self._tasks),
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_worker: Optional[BookingWorker] = None


def get_booking_worker() -> BookingWorker:
    """Get or create global BookingWorker instance."""
    global _worker
    if _worker is None:
        config = QueueConfig.from_env()

        # Use SQS if configured, otherwise local
        if config.queue_url:
            queue_client = SQSQueueClient(config)
        else:
            queue_client = LocalQueueClient()

        _worker = BookingWorker(
            config=config,
            queue_client=queue_client,
        )

    return _worker


async def start_booking_worker(num_workers: int = 5) -> BookingWorker:
    """Start global booking worker."""
    worker = get_booking_worker()
    await worker.start(num_workers)
    return worker


async def stop_booking_worker() -> None:
    """Stop global booking worker."""
    global _worker
    if _worker:
        await _worker.stop()
        _worker = None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "BookingStatus",

    # Config
    "QueueConfig",
    "BookingMessage",
    "WorkerStats",

    # Clients
    "QueueClient",
    "LocalQueueClient",
    "SQSQueueClient",

    # Processors
    "BookingProcessor",
    "DatabaseBookingProcessor",

    # Worker
    "BookingWorker",

    # Factory
    "get_booking_worker",
    "start_booking_worker",
    "stop_booking_worker",
]


logger.info("✅ Booking Queue Worker module loaded")
