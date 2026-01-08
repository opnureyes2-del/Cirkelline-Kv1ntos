"""
Connection Pool
===============
Generic connection pooling for resources.

Responsibilities:
- Pool database connections
- Pool HTTP client connections
- Health checking and connection recycling
- Statistics and monitoring
"""

import logging
import asyncio
import time
import threading
from typing import Optional, Dict, Any, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ConnectionState(Enum):
    """Connection states."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    STALE = "stale"
    ERROR = "error"


@dataclass
class PoolConfig:
    """Connection pool configuration."""
    min_size: int = 2
    max_size: int = 10
    max_idle_seconds: int = 300  # 5 minutes
    max_lifetime_seconds: int = 3600  # 1 hour
    acquire_timeout_seconds: float = 30.0
    health_check_interval: int = 60
    retry_attempts: int = 3


@dataclass
class PoolStats:
    """Connection pool statistics."""
    total_connections: int = 0
    available_connections: int = 0
    in_use_connections: int = 0
    peak_connections: int = 0
    total_acquired: int = 0
    total_released: int = 0
    total_created: int = 0
    total_closed: int = 0
    failed_acquires: int = 0
    health_checks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_connections": self.total_connections,
            "available_connections": self.available_connections,
            "in_use_connections": self.in_use_connections,
            "peak_connections": self.peak_connections,
            "total_acquired": self.total_acquired,
            "total_released": self.total_released,
            "total_created": self.total_created,
            "total_closed": self.total_closed,
            "failed_acquires": self.failed_acquires,
            "health_checks": self.health_checks,
        }


@dataclass
class PooledConnection(Generic[T]):
    """A pooled connection wrapper."""
    connection: T
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    state: ConnectionState = ConnectionState.AVAILABLE
    connection_id: str = ""

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    @property
    def idle_seconds(self) -> float:
        return time.time() - self.last_used

    def mark_used(self) -> None:
        """Mark connection as used."""
        self.last_used = time.time()
        self.use_count += 1
        self.state = ConnectionState.IN_USE

    def mark_available(self) -> None:
        """Mark connection as available."""
        self.state = ConnectionState.AVAILABLE


# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTION FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

class ConnectionFactory(ABC, Generic[T]):
    """Abstract factory for creating connections."""

    @abstractmethod
    async def create(self) -> T:
        """Create a new connection."""
        pass

    @abstractmethod
    async def close(self, connection: T) -> None:
        """Close a connection."""
        pass

    @abstractmethod
    async def validate(self, connection: T) -> bool:
        """Validate a connection is healthy."""
        pass


class DummyConnectionFactory(ConnectionFactory[Dict[str, Any]]):
    """Dummy connection factory for testing."""

    def __init__(self):
        self._counter = 0

    async def create(self) -> Dict[str, Any]:
        self._counter += 1
        return {
            "id": self._counter,
            "created": time.time(),
            "valid": True,
        }

    async def close(self, connection: Dict[str, Any]) -> None:
        connection["valid"] = False

    async def validate(self, connection: Dict[str, Any]) -> bool:
        return connection.get("valid", False)


# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTION POOL
# ═══════════════════════════════════════════════════════════════════════════════

class ConnectionPool(Generic[T]):
    """
    Generic async connection pool.

    Manages a pool of reusable connections with health
    checking and automatic recycling.
    """

    def __init__(
        self,
        factory: ConnectionFactory[T],
        config: Optional[PoolConfig] = None,
    ):
        self._factory = factory
        self._config = config or PoolConfig()

        # Pool storage
        self._available: asyncio.Queue[PooledConnection[T]] = asyncio.Queue()
        self._in_use: Dict[str, PooledConnection[T]] = {}
        self._all_connections: Dict[str, PooledConnection[T]] = {}

        # State
        self._initialized = False
        self._closed = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._connection_counter = 0

        # Statistics
        self._stats = PoolStats()

        # Locks
        self._lock = asyncio.Lock()

    # ═══════════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════════

    async def initialize(self) -> None:
        """Initialize the pool with minimum connections."""
        if self._initialized:
            return

        async with self._lock:
            # Create minimum connections
            for _ in range(self._config.min_size):
                try:
                    conn = await self._create_connection()
                    await self._available.put(conn)
                except Exception as e:
                    logger.error(f"Failed to create initial connection: {e}")

            # Start health check task
            self._health_check_task = asyncio.create_task(
                self._health_check_loop()
            )

            self._initialized = True
            logger.info(
                f"Connection pool initialized with {self._available.qsize()} connections"
            )

    async def close(self) -> None:
        """Close the pool and all connections."""
        if self._closed:
            return

        self._closed = True

        # Stop health check
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        async with self._lock:
            for conn in self._all_connections.values():
                try:
                    await self._factory.close(conn.connection)
                    self._stats.total_closed += 1
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")

            self._all_connections.clear()
            self._in_use.clear()

        logger.info("Connection pool closed")

    # ═══════════════════════════════════════════════════════════════════════════
    # ACQUIRE / RELEASE
    # ═══════════════════════════════════════════════════════════════════════════

    async def acquire(self) -> PooledConnection[T]:
        """
        Acquire a connection from the pool.

        Returns:
            A pooled connection

        Raises:
            TimeoutError if no connection available within timeout
        """
        if self._closed:
            raise RuntimeError("Pool is closed")

        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= self._config.acquire_timeout_seconds:
                self._stats.failed_acquires += 1
                raise TimeoutError(
                    f"Could not acquire connection within {self._config.acquire_timeout_seconds}s"
                )

            # Try to get from available pool
            try:
                conn = self._available.get_nowait()

                # Validate connection
                if await self._is_connection_valid(conn):
                    conn.mark_used()
                    self._in_use[conn.connection_id] = conn
                    self._stats.total_acquired += 1
                    self._update_stats()
                    return conn
                else:
                    # Connection stale, close and create new
                    await self._close_connection(conn)
                    continue

            except asyncio.QueueEmpty:
                pass

            # Try to create new connection if pool not at max
            async with self._lock:
                if len(self._all_connections) < self._config.max_size:
                    try:
                        conn = await self._create_connection()
                        conn.mark_used()
                        self._in_use[conn.connection_id] = conn
                        self._stats.total_acquired += 1
                        self._update_stats()
                        return conn
                    except Exception as e:
                        logger.error(f"Failed to create connection: {e}")

            # Wait a bit and retry
            await asyncio.sleep(0.1)

    async def release(self, conn: PooledConnection[T]) -> None:
        """Release a connection back to the pool."""
        if conn.connection_id not in self._in_use:
            logger.warning(f"Releasing unknown connection: {conn.connection_id}")
            return

        del self._in_use[conn.connection_id]
        conn.mark_available()
        self._stats.total_released += 1

        # Check if connection should be recycled
        if self._should_recycle(conn):
            await self._close_connection(conn)
        else:
            await self._available.put(conn)

        self._update_stats()

    @asynccontextmanager
    async def connection(self):
        """
        Context manager for connection acquisition.

        Usage:
            async with pool.connection() as conn:
                # use conn.connection
        """
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

    # ═══════════════════════════════════════════════════════════════════════════
    # CONNECTION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def _create_connection(self) -> PooledConnection[T]:
        """Create a new pooled connection."""
        self._connection_counter += 1
        connection_id = f"conn-{self._connection_counter}"

        raw_connection = await self._factory.create()

        pooled = PooledConnection(
            connection=raw_connection,
            connection_id=connection_id,
        )

        self._all_connections[connection_id] = pooled
        self._stats.total_created += 1
        self._update_stats()

        logger.debug(f"Created connection: {connection_id}")
        return pooled

    async def _close_connection(self, conn: PooledConnection[T]) -> None:
        """Close and remove a connection."""
        if conn.connection_id in self._all_connections:
            del self._all_connections[conn.connection_id]

        try:
            await self._factory.close(conn.connection)
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

        self._stats.total_closed += 1
        logger.debug(f"Closed connection: {conn.connection_id}")

    async def _is_connection_valid(self, conn: PooledConnection[T]) -> bool:
        """Check if connection is valid and not stale."""
        # Check lifetime
        if conn.age_seconds > self._config.max_lifetime_seconds:
            return False

        # Check idle time
        if conn.idle_seconds > self._config.max_idle_seconds:
            return False

        # Validate with factory
        try:
            return await self._factory.validate(conn.connection)
        except Exception:
            return False

    def _should_recycle(self, conn: PooledConnection[T]) -> bool:
        """Check if connection should be recycled."""
        if conn.age_seconds > self._config.max_lifetime_seconds:
            return True
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # HEALTH CHECK
    # ═══════════════════════════════════════════════════════════════════════════

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while not self._closed:
            try:
                await asyncio.sleep(self._config.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _perform_health_check(self) -> None:
        """Perform health check on all connections."""
        self._stats.health_checks += 1

        # Check available connections
        to_check = []
        while not self._available.empty():
            try:
                conn = self._available.get_nowait()
                to_check.append(conn)
            except asyncio.QueueEmpty:
                break

        for conn in to_check:
            if await self._is_connection_valid(conn):
                await self._available.put(conn)
            else:
                await self._close_connection(conn)

        # Ensure minimum connections
        async with self._lock:
            current_total = len(self._all_connections)
            while current_total < self._config.min_size:
                try:
                    conn = await self._create_connection()
                    await self._available.put(conn)
                    current_total += 1
                except Exception as e:
                    logger.error(f"Failed to create replacement connection: {e}")
                    break

        self._update_stats()

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def _update_stats(self) -> None:
        """Update pool statistics."""
        self._stats.total_connections = len(self._all_connections)
        self._stats.available_connections = self._available.qsize()
        self._stats.in_use_connections = len(self._in_use)

        if self._stats.total_connections > self._stats.peak_connections:
            self._stats.peak_connections = self._stats.total_connections

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        self._update_stats()
        return {
            **self._stats.to_dict(),
            "config": {
                "min_size": self._config.min_size,
                "max_size": self._config.max_size,
                "max_idle_seconds": self._config.max_idle_seconds,
                "max_lifetime_seconds": self._config.max_lifetime_seconds,
            },
            "initialized": self._initialized,
            "closed": self._closed,
        }

    @property
    def size(self) -> int:
        """Current pool size."""
        return len(self._all_connections)

    @property
    def available(self) -> int:
        """Available connections."""
        return self._available.qsize()


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_pool_instances: Dict[str, ConnectionPool] = {}


def get_connection_pool(
    name: str = "default",
    factory: Optional[ConnectionFactory] = None,
    config: Optional[PoolConfig] = None,
) -> ConnectionPool:
    """Get or create a named connection pool."""
    if name not in _pool_instances:
        if factory is None:
            factory = DummyConnectionFactory()
        _pool_instances[name] = ConnectionPool(
            factory=factory,
            config=config or PoolConfig(),
        )
    return _pool_instances[name]


async def init_connection_pools() -> Dict[str, ConnectionPool]:
    """Initialize all registered connection pools."""
    for pool in _pool_instances.values():
        await pool.initialize()
    return _pool_instances


async def close_connection_pools() -> None:
    """Close all connection pools."""
    for pool in _pool_instances.values():
        await pool.close()
    _pool_instances.clear()
