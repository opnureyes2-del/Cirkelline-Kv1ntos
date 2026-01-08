"""
Async Utilities
===============
Async operation optimization utilities.

Responsibilities:
- Batch async operations
- Retry with exponential backoff
- Timeout management
- Concurrent execution helpers
"""

import logging
import asyncio
import time
import functools
from typing import (
    Optional, Dict, Any, List, Callable, TypeVar, Generic,
    Awaitable, Tuple, Union
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BatchResult(Generic[T]):
    """Result of a batch operation."""
    successful: List[T] = field(default_factory=list)
    failed: List[Tuple[Any, Exception]] = field(default_factory=list)
    total: int = 0
    duration_ms: float = 0

    @property
    def success_rate(self) -> float:
        return len(self.successful) / self.total if self.total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "successful_count": len(self.successful),
            "failed_count": len(self.failed),
            "total": self.total,
            "success_rate": round(self.success_rate, 3),
            "duration_ms": round(self.duration_ms, 2),
        }


class RetryStrategy(Enum):
    """Retry backoff strategies."""
    CONSTANT = "constant"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC TIMEOUT
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncTimeout:
    """Async operation timeout wrapper."""

    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds

    async def run(
        self,
        coro: Awaitable[T],
        default: Optional[T] = None,
    ) -> Optional[T]:
        """
        Run coroutine with timeout.

        Args:
            coro: Coroutine to run
            default: Default value if timeout

        Returns:
            Result or default value
        """
        try:
            return await asyncio.wait_for(coro, timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {self.timeout_seconds}s")
            return default


async def run_with_timeout(
    coro: Awaitable[T],
    timeout_seconds: float,
    default: Optional[T] = None,
) -> Optional[T]:
    """Run coroutine with timeout."""
    timeout = AsyncTimeout(timeout_seconds)
    return await timeout.run(coro, default)


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC RETRY
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncRetry:
    """Async operation retry with backoff."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        exceptions: Tuple[type, ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.exceptions = exceptions

    def _get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt."""
        if self.strategy == RetryStrategy.CONSTANT:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (attempt - 1))
        elif self.strategy == RetryStrategy.FIBONACCI:
            a, b = 1, 1
            for _ in range(attempt - 1):
                a, b = b, a + b
            delay = self.base_delay * a
        else:
            delay = self.base_delay

        return min(delay, self.max_delay)

    async def run(
        self,
        coro_factory: Callable[[], Awaitable[T]],
    ) -> T:
        """
        Run coroutine with retries.

        Args:
            coro_factory: Factory function that creates the coroutine

        Returns:
            Result of successful attempt

        Raises:
            Last exception if all attempts fail
        """
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await coro_factory()
            except self.exceptions as e:
                last_exception = e
                if attempt < self.max_attempts:
                    delay = self._get_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt}/{self.max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_attempts} attempts failed: {e}"
                    )

        raise last_exception or Exception("Retry failed")


async def retry_async(
    coro_factory: Callable[[], Awaitable[T]],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    exceptions: Tuple[type, ...] = (Exception,),
) -> T:
    """Retry async operation with backoff."""
    retry = AsyncRetry(
        max_attempts=max_attempts,
        base_delay=base_delay,
        strategy=strategy,
        exceptions=exceptions,
    )
    return await retry.run(coro_factory)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    exceptions: Tuple[type, ...] = (Exception,),
):
    """
    Decorator for async function retry.

    Usage:
        @retry(max_attempts=3)
        async def flaky_operation():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_async(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                base_delay=base_delay,
                strategy=strategy,
                exceptions=exceptions,
            )
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC BATCHER
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncBatcher(Generic[T, R]):
    """
    Batch async operations for efficiency.

    Collects items and processes them in batches,
    reducing overhead for many small operations.
    """

    def __init__(
        self,
        batch_size: int = 100,
        max_wait_seconds: float = 0.1,
        processor: Optional[Callable[[List[T]], Awaitable[List[R]]]] = None,
    ):
        self.batch_size = batch_size
        self.max_wait_seconds = max_wait_seconds
        self._processor = processor

        self._queue: asyncio.Queue[Tuple[T, asyncio.Future]] = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "batches_processed": 0,
            "items_processed": 0,
            "total_wait_time": 0.0,
        }

    def set_processor(
        self,
        processor: Callable[[List[T]], Awaitable[List[R]]],
    ) -> None:
        """Set the batch processor function."""
        self._processor = processor

    async def start(self) -> None:
        """Start the batcher."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.debug("AsyncBatcher started")

    async def stop(self) -> None:
        """Stop the batcher."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.debug("AsyncBatcher stopped")

    async def add(self, item: T) -> R:
        """
        Add item to batch queue.

        Returns the result when batch is processed.
        """
        future: asyncio.Future[R] = asyncio.get_event_loop().create_future()
        await self._queue.put((item, future))
        return await future

    async def _process_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            try:
                batch: List[Tuple[T, asyncio.Future]] = []
                start_time = time.time()

                # Collect batch
                while len(batch) < self.batch_size:
                    try:
                        remaining = self.max_wait_seconds - (time.time() - start_time)
                        if remaining <= 0:
                            break

                        item = await asyncio.wait_for(
                            self._queue.get(),
                            timeout=remaining,
                        )
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break

                if not batch:
                    continue

                # Process batch
                if self._processor:
                    try:
                        items = [item for item, _ in batch]
                        results = await self._processor(items)

                        # Distribute results
                        for (_, future), result in zip(batch, results):
                            if not future.done():
                                future.set_result(result)
                    except Exception as e:
                        # Set exception on all futures
                        for _, future in batch:
                            if not future.done():
                                future.set_exception(e)

                # Update stats
                self._stats["batches_processed"] += 1
                self._stats["items_processed"] += len(batch)
                self._stats["total_wait_time"] += time.time() - start_time

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batcher error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get batcher statistics."""
        return {
            **self._stats,
            "batch_size": self.batch_size,
            "max_wait_seconds": self.max_wait_seconds,
            "queue_size": self._queue.qsize(),
            "running": self._running,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

async def batch_process(
    items: List[T],
    processor: Callable[[T], Awaitable[R]],
    batch_size: int = 10,
    max_concurrency: int = 5,
) -> BatchResult[R]:
    """
    Process items in batches with concurrency control.

    Args:
        items: Items to process
        processor: Async function to process each item
        batch_size: Items per batch
        max_concurrency: Max concurrent operations

    Returns:
        BatchResult with successful and failed items
    """
    start_time = time.time()
    result = BatchResult(total=len(items))

    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_item(item: T) -> Tuple[bool, Union[R, Exception]]:
        async with semaphore:
            try:
                return True, await processor(item)
            except Exception as e:
                return False, e

    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        tasks = [process_item(item) for item in batch]
        batch_results = await asyncio.gather(*tasks)

        for item, (success, value) in zip(batch, batch_results):
            if success:
                result.successful.append(value)
            else:
                result.failed.append((item, value))

    result.duration_ms = (time.time() - start_time) * 1000
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# CONCURRENT EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

async def gather_with_concurrency(
    coros: List[Awaitable[T]],
    max_concurrency: int = 10,
    return_exceptions: bool = False,
) -> List[Union[T, Exception]]:
    """
    Execute coroutines with concurrency limit.

    Args:
        coros: Coroutines to execute
        max_concurrency: Maximum concurrent operations
        return_exceptions: Return exceptions instead of raising

    Returns:
        List of results (or exceptions if return_exceptions=True)
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def limited_coro(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(
        *[limited_coro(c) for c in coros],
        return_exceptions=return_exceptions,
    )


async def first_completed(
    coros: List[Awaitable[T]],
    timeout: Optional[float] = None,
) -> Tuple[T, int]:
    """
    Return result of first completed coroutine.

    Args:
        coros: Coroutines to race
        timeout: Optional timeout

    Returns:
        Tuple of (result, index of winning coroutine)
    """
    tasks = [asyncio.create_task(c) for c in coros]

    try:
        done, pending = await asyncio.wait(
            tasks,
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )

        if not done:
            raise asyncio.TimeoutError("No task completed within timeout")

        # Get first completed
        completed_task = next(iter(done))
        index = tasks.index(completed_task)
        result = completed_task.result()

        # Cancel pending
        for task in pending:
            task.cancel()

        return result, index

    except Exception:
        # Cancel all tasks on error
        for task in tasks:
            task.cancel()
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_batcher_instances: Dict[str, AsyncBatcher] = {}


def get_batcher(
    name: str = "default",
    batch_size: int = 100,
    max_wait_seconds: float = 0.1,
) -> AsyncBatcher:
    """Get or create a named AsyncBatcher instance."""
    if name not in _batcher_instances:
        _batcher_instances[name] = AsyncBatcher(
            batch_size=batch_size,
            max_wait_seconds=max_wait_seconds,
        )
    return _batcher_instances[name]


async def init_batchers() -> Dict[str, AsyncBatcher]:
    """Initialize and start all batchers."""
    for batcher in _batcher_instances.values():
        await batcher.start()
    return _batcher_instances
