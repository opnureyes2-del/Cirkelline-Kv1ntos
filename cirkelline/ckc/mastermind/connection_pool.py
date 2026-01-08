"""
CKC MASTERMIND Connection Pool (DEL AG)
========================================

Generic connection pooling system til database, HTTP, WebSocket forbindelser.

Features:
    - Generic connection pooling med factory pattern
    - Database connection pooling (PostgreSQL, SQLite)
    - HTTP client connection pooling
    - WebSocket connection pooling
    - Health monitoring og automatic reconnection
    - Load balancing strategier
    - Connection lifecycle management

Arkitektur:
    Application --> ConnectionPool --> [Connection1, Connection2, ...]
                          ↓
                   HealthMonitor (background)
                          ↓
                   Auto-reconnect/replace

Brug:
    from cirkelline.ckc.mastermind.connection_pool import (
        create_connection_pool,
        get_connection_pool,
        ConnectionPoolManager,
    )

    # Database pool
    db_pool = await create_connection_pool(
        pool_type="database",
        min_size=5,
        max_size=20,
        connection_factory=lambda: create_db_connection()
    )

    async with db_pool.acquire() as conn:
        await conn.execute("SELECT 1")
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    TypeVar,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class PoolState(Enum):
    """Connection pool tilstande."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    DRAINING = "draining"      # Waiting for connections to return
    STOPPED = "stopped"
    ERROR = "error"


class ConnectionState(Enum):
    """Connection tilstande."""
    IDLE = "idle"              # Available for use
    IN_USE = "in_use"          # Currently checked out
    CONNECTING = "connecting"   # Being established
    VALIDATING = "validating"   # Being health checked
    BROKEN = "broken"          # Failed, needs replacement
    CLOSED = "closed"          # Permanently closed


class LoadBalanceStrategy(Enum):
    """Load balancing strategier."""
    ROUND_ROBIN = "round_robin"     # Cycle through connections
    LEAST_USED = "least_used"       # Connection with fewest uses
    RANDOM = "random"               # Random selection
    LIFO = "lifo"                   # Last in, first out
    FIFO = "fifo"                   # First in, first out


class PoolEventType(Enum):
    """Pool events."""
    CONNECTION_CREATED = "connection_created"
    CONNECTION_ACQUIRED = "connection_acquired"
    CONNECTION_RELEASED = "connection_released"
    CONNECTION_CLOSED = "connection_closed"
    CONNECTION_BROKEN = "connection_broken"
    CONNECTION_REPLACED = "connection_replaced"
    POOL_RESIZED = "pool_resized"
    HEALTH_CHECK_FAILED = "health_check_failed"
    POOL_EXHAUSTED = "pool_exhausted"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ConnectionPoolConfig:
    """Konfiguration for connection pool."""
    # Pool sizing
    min_size: int = 1
    max_size: int = 10
    initial_size: int = 5

    # Timeouts
    acquire_timeout_seconds: float = 30.0
    connection_timeout_seconds: float = 10.0
    idle_timeout_seconds: float = 300.0
    max_lifetime_seconds: float = 3600.0

    # Health checks
    health_check_interval_seconds: float = 30.0
    health_check_timeout_seconds: float = 5.0

    # Behavior
    load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.LIFO
    validate_on_acquire: bool = True
    validate_on_release: bool = False

    # Auto-management
    auto_resize: bool = True
    resize_threshold_percent: float = 80.0

    # Retry
    max_retries: int = 3
    retry_delay_seconds: float = 1.0


@dataclass
class ConnectionInfo:
    """Information om en connection."""
    connection_id: str
    state: ConnectionState
    created_at: datetime
    last_used_at: Optional[datetime] = None
    last_validated_at: Optional[datetime] = None
    use_count: int = 0
    error_count: int = 0
    total_use_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        """Alder af connection i sekunder."""
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def idle_seconds(self) -> Optional[float]:
        """Sekunder siden sidste brug."""
        if self.last_used_at:
            return (datetime.now() - self.last_used_at).total_seconds()
        return None

    @property
    def avg_use_time_ms(self) -> float:
        """Gennemsnitlig brugstid i ms."""
        if self.use_count == 0:
            return 0.0
        return self.total_use_time_ms / self.use_count


@dataclass
class PoolMetrics:
    """Metrics for connection pool."""
    # Pool state
    total_connections: int = 0
    idle_connections: int = 0
    in_use_connections: int = 0
    pending_requests: int = 0

    # Counters
    total_acquires: int = 0
    total_releases: int = 0
    total_timeouts: int = 0
    total_errors: int = 0
    connections_created: int = 0
    connections_closed: int = 0

    # Latency
    avg_acquire_time_ms: float = 0.0
    avg_use_time_ms: float = 0.0
    p99_acquire_time_ms: float = 0.0

    # Utilization
    utilization_percent: float = 0.0
    peak_utilization_percent: float = 0.0

    # Time
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PoolEvent:
    """Event fra connection pool."""
    event_type: PoolEventType
    pool_id: str
    connection_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# CONNECTION WRAPPER
# =============================================================================


T = TypeVar('T')  # Connection type


class PooledConnection(Generic[T]):
    """
    Wrapper around en pooled connection.

    Håndterer:
        - Usage tracking
        - Automatic release
        - Error detection
    """

    def __init__(
        self,
        connection: T,
        info: ConnectionInfo,
        pool: "ConnectionPool[T]",
    ) -> None:
        self._connection = connection
        self._info = info
        self._pool = pool
        self._acquired_at = datetime.now()
        self._released = False

    @property
    def connection(self) -> T:
        """Få den underliggende connection."""
        return self._connection

    @property
    def connection_id(self) -> str:
        """Connection ID."""
        return self._info.connection_id

    @property
    def info(self) -> ConnectionInfo:
        """Connection info."""
        return self._info

    async def release(self) -> None:
        """Frigiv connection til pool."""
        if not self._released:
            self._released = True
            use_time = (datetime.now() - self._acquired_at).total_seconds() * 1000
            await self._pool._release_connection(self, use_time)

    def mark_broken(self) -> None:
        """Marker connection som broken."""
        self._info.state = ConnectionState.BROKEN
        self._info.error_count += 1


# =============================================================================
# ABSTRACT CONNECTION POOL
# =============================================================================


class ConnectionPool(ABC, Generic[T]):
    """
    Abstract base class for connection pools.

    Subklasser skal implementere:
        - _create_connection()
        - _close_connection()
        - _validate_connection()
    """

    def __init__(
        self,
        config: Optional[ConnectionPoolConfig] = None,
        pool_id: Optional[str] = None,
    ) -> None:
        self.config = config or ConnectionPoolConfig()
        self.pool_id = pool_id or f"pool_{uuid.uuid4().hex[:8]}"

        self._state = PoolState.INITIALIZING
        self._connections: Dict[str, PooledConnection[T]] = {}
        self._idle_connections: asyncio.Queue[str] = asyncio.Queue()
        self._pending_requests: int = 0
        self._lock = asyncio.Lock()

        # Metrics tracking
        self._metrics = PoolMetrics()
        self._acquire_times: List[float] = []
        self._use_times: List[float] = []

        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Event handlers
        self._event_handlers: List[Callable[[PoolEvent], Awaitable[None]]] = []

        logger.info(
            f"Connection pool created: {self.pool_id}, "
            f"min={self.config.min_size}, max={self.config.max_size}"
        )

    @abstractmethod
    async def _create_connection(self) -> T:
        """Opret ny connection. Skal implementeres af subklasser."""
        pass

    @abstractmethod
    async def _close_connection(self, connection: T) -> None:
        """Luk connection. Skal implementeres af subklasser."""
        pass

    @abstractmethod
    async def _validate_connection(self, connection: T) -> bool:
        """Valider connection. Skal implementeres af subklasser."""
        pass

    async def start(self) -> None:
        """Start connection pool."""
        try:
            self._shutdown_event.clear()

            # Create initial connections
            initial = min(self.config.initial_size, self.config.max_size)
            for _ in range(initial):
                await self._add_connection()

            self._state = PoolState.RUNNING

            # Start health check task
            if self.config.health_check_interval_seconds > 0:
                self._health_check_task = asyncio.create_task(
                    self._health_check_loop()
                )

            logger.info(f"Connection pool started: {self.pool_id}")

        except Exception as e:
            self._state = PoolState.ERROR
            logger.error(f"Failed to start connection pool: {e}")
            raise

    async def stop(self) -> None:
        """Stop connection pool og luk alle connections."""
        self._state = PoolState.DRAINING
        self._shutdown_event.set()

        # Cancel health check
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        async with self._lock:
            for conn_id, pooled_conn in list(self._connections.items()):
                try:
                    await self._close_connection(pooled_conn.connection)
                except Exception as e:
                    logger.error(f"Error closing connection {conn_id}: {e}")
            self._connections.clear()

        self._state = PoolState.STOPPED
        logger.info(f"Connection pool stopped: {self.pool_id}")

    async def _add_connection(self) -> str:
        """Tilføj ny connection til pool."""
        connection_id = f"conn_{uuid.uuid4().hex[:8]}"

        try:
            # Create connection with timeout
            connection = await asyncio.wait_for(
                self._create_connection(),
                timeout=self.config.connection_timeout_seconds
            )

            info = ConnectionInfo(
                connection_id=connection_id,
                state=ConnectionState.IDLE,
                created_at=datetime.now(),
            )

            pooled_conn = PooledConnection(
                connection=connection,
                info=info,
                pool=self,
            )

            self._connections[connection_id] = pooled_conn
            await self._idle_connections.put(connection_id)

            self._metrics.connections_created += 1
            await self._emit_event(
                PoolEventType.CONNECTION_CREATED,
                connection_id=connection_id
            )

            logger.debug(f"Connection created: {connection_id}")
            return connection_id

        except asyncio.TimeoutError:
            logger.error(f"Timeout creating connection in pool {self.pool_id}")
            raise
        except Exception as e:
            logger.error(f"Error creating connection: {e}")
            raise

    async def acquire(self) -> PooledConnection[T]:
        """
        Hent en connection fra pool.

        Returns:
            PooledConnection wrapper

        Raises:
            TimeoutError: Hvis ingen connection tilgængelig inden timeout
        """
        if self._state != PoolState.RUNNING:
            raise RuntimeError(f"Pool is not running: {self._state}")

        start_time = time.perf_counter()
        self._pending_requests += 1

        try:
            # Try to get an idle connection
            connection_id = await self._get_connection(
                timeout=self.config.acquire_timeout_seconds
            )

            pooled_conn = self._connections[connection_id]

            # Validate if configured
            if self.config.validate_on_acquire:
                if not await self._safe_validate(pooled_conn.connection):
                    # Connection is broken, replace it
                    await self._replace_connection(connection_id)
                    # Try again
                    return await self.acquire()

            # Update state
            pooled_conn._info.state = ConnectionState.IN_USE
            pooled_conn._info.last_used_at = datetime.now()
            pooled_conn._info.use_count += 1
            pooled_conn._acquired_at = datetime.now()
            pooled_conn._released = False

            # Record metrics
            acquire_time = (time.perf_counter() - start_time) * 1000
            self._record_acquire_time(acquire_time)

            self._metrics.total_acquires += 1
            await self._emit_event(
                PoolEventType.CONNECTION_ACQUIRED,
                connection_id=connection_id
            )

            return pooled_conn

        except asyncio.TimeoutError:
            self._metrics.total_timeouts += 1
            await self._emit_event(PoolEventType.POOL_EXHAUSTED)
            raise TimeoutError(f"No connection available after {self.config.acquire_timeout_seconds}s")

        finally:
            self._pending_requests -= 1

    async def _get_connection(self, timeout: float) -> str:
        """Get connection ID fra idle queue, med auto-resize."""
        try:
            # Check if we should create more connections
            if self._idle_connections.empty():
                async with self._lock:
                    if len(self._connections) < self.config.max_size:
                        await self._add_connection()

            # Wait for connection
            return await asyncio.wait_for(
                self._idle_connections.get(),
                timeout=timeout
            )

        except asyncio.TimeoutError:
            raise

    async def _release_connection(
        self,
        pooled_conn: PooledConnection[T],
        use_time_ms: float,
    ) -> None:
        """Frigiv connection tilbage til pool."""
        connection_id = pooled_conn.connection_id

        # Update info
        pooled_conn._info.total_use_time_ms += use_time_ms
        self._record_use_time(use_time_ms)

        # Check if connection is still valid
        if pooled_conn._info.state == ConnectionState.BROKEN:
            await self._replace_connection(connection_id)
            return

        # Check lifetime
        if pooled_conn._info.age_seconds > self.config.max_lifetime_seconds:
            await self._replace_connection(connection_id)
            return

        # Validate if configured
        if self.config.validate_on_release:
            if not await self._safe_validate(pooled_conn.connection):
                await self._replace_connection(connection_id)
                return

        # Return to pool
        pooled_conn._info.state = ConnectionState.IDLE
        await self._idle_connections.put(connection_id)

        self._metrics.total_releases += 1
        await self._emit_event(
            PoolEventType.CONNECTION_RELEASED,
            connection_id=connection_id
        )

    async def _replace_connection(self, connection_id: str) -> None:
        """Erstat en broken/expired connection."""
        async with self._lock:
            if connection_id in self._connections:
                old_conn = self._connections.pop(connection_id)
                try:
                    await self._close_connection(old_conn.connection)
                except Exception as e:
                    logger.warning(f"Error closing old connection: {e}")

                self._metrics.connections_closed += 1

            # Create replacement if we're below min_size
            if len(self._connections) < self.config.min_size:
                await self._add_connection()

        await self._emit_event(
            PoolEventType.CONNECTION_REPLACED,
            connection_id=connection_id
        )

    async def _safe_validate(self, connection: T) -> bool:
        """Validate connection med timeout og error handling."""
        try:
            return await asyncio.wait_for(
                self._validate_connection(connection),
                timeout=self.config.health_check_timeout_seconds
            )
        except Exception as e:
            logger.warning(f"Connection validation failed: {e}")
            return False

    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.health_check_interval_seconds)

                if self._shutdown_event.is_set():
                    break

                await self._perform_health_check()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _perform_health_check(self) -> None:
        """Udfør health check på idle connections."""
        broken_connections: List[str] = []

        # Check idle connections
        for conn_id, pooled_conn in list(self._connections.items()):
            if pooled_conn._info.state != ConnectionState.IDLE:
                continue

            # Check idle timeout
            idle_time = pooled_conn._info.idle_seconds
            if idle_time and idle_time > self.config.idle_timeout_seconds:
                if len(self._connections) > self.config.min_size:
                    broken_connections.append(conn_id)
                    continue

            # Validate connection
            if not await self._safe_validate(pooled_conn.connection):
                broken_connections.append(conn_id)
                await self._emit_event(
                    PoolEventType.HEALTH_CHECK_FAILED,
                    connection_id=conn_id
                )

        # Replace broken connections
        for conn_id in broken_connections:
            await self._replace_connection(conn_id)

        # Update metrics
        self._update_metrics()

    def _record_acquire_time(self, time_ms: float) -> None:
        """Record acquire latency."""
        self._acquire_times.append(time_ms)
        if len(self._acquire_times) > 1000:
            self._acquire_times = self._acquire_times[-1000:]

        self._metrics.avg_acquire_time_ms = (
            sum(self._acquire_times) / len(self._acquire_times)
        )
        if self._acquire_times:
            sorted_times = sorted(self._acquire_times)
            p99_idx = int(len(sorted_times) * 0.99)
            self._metrics.p99_acquire_time_ms = sorted_times[min(p99_idx, len(sorted_times) - 1)]

    def _record_use_time(self, time_ms: float) -> None:
        """Record connection use time."""
        self._use_times.append(time_ms)
        if len(self._use_times) > 1000:
            self._use_times = self._use_times[-1000:]

        self._metrics.avg_use_time_ms = (
            sum(self._use_times) / len(self._use_times)
        )

    def _update_metrics(self) -> None:
        """Opdater pool metrics."""
        idle = sum(
            1 for c in self._connections.values()
            if c._info.state == ConnectionState.IDLE
        )
        in_use = sum(
            1 for c in self._connections.values()
            if c._info.state == ConnectionState.IN_USE
        )

        self._metrics.total_connections = len(self._connections)
        self._metrics.idle_connections = idle
        self._metrics.in_use_connections = in_use
        self._metrics.pending_requests = self._pending_requests

        if self.config.max_size > 0:
            utilization = (in_use / self.config.max_size) * 100
            self._metrics.utilization_percent = utilization
            self._metrics.peak_utilization_percent = max(
                self._metrics.peak_utilization_percent,
                utilization
            )

        self._metrics.last_updated = datetime.now()

    async def _emit_event(
        self,
        event_type: PoolEventType,
        connection_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit pool event."""
        event = PoolEvent(
            event_type=event_type,
            pool_id=self.pool_id,
            connection_id=connection_id,
            details=details or {},
        )

        for handler in self._event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def on_event(
        self,
        handler: Callable[[PoolEvent], Awaitable[None]],
    ) -> None:
        """Registrer event handler."""
        self._event_handlers.append(handler)

    @asynccontextmanager
    async def connection(self) -> AsyncContextManager[T]:
        """
        Context manager for at bruge en connection.

        Example:
            async with pool.connection() as conn:
                await conn.execute("SELECT 1")
        """
        pooled_conn = await self.acquire()
        try:
            yield pooled_conn.connection
        except Exception as e:
            pooled_conn.mark_broken()
            raise
        finally:
            await pooled_conn.release()

    def get_metrics(self) -> PoolMetrics:
        """Hent pool metrics."""
        self._update_metrics()
        return self._metrics

    def get_statistics(self) -> Dict[str, Any]:
        """Hent pool statistics som dict."""
        metrics = self.get_metrics()
        return {
            "pool_id": self.pool_id,
            "state": self._state.value,
            "total_connections": metrics.total_connections,
            "idle_connections": metrics.idle_connections,
            "in_use_connections": metrics.in_use_connections,
            "pending_requests": metrics.pending_requests,
            "total_acquires": metrics.total_acquires,
            "total_releases": metrics.total_releases,
            "total_timeouts": metrics.total_timeouts,
            "avg_acquire_time_ms": metrics.avg_acquire_time_ms,
            "avg_use_time_ms": metrics.avg_use_time_ms,
            "utilization_percent": metrics.utilization_percent,
            "peak_utilization_percent": metrics.peak_utilization_percent,
            "config": {
                "min_size": self.config.min_size,
                "max_size": self.config.max_size,
                "load_balance": self.config.load_balance_strategy.value,
            },
        }


# =============================================================================
# GENERIC CONNECTION POOL (FACTORY-BASED)
# =============================================================================


class GenericConnectionPool(ConnectionPool[T]):
    """
    Generic connection pool med factory functions.

    Brug dette når du har custom connection types.
    """

    def __init__(
        self,
        create_func: Callable[[], Awaitable[T]],
        close_func: Callable[[T], Awaitable[None]],
        validate_func: Optional[Callable[[T], Awaitable[bool]]] = None,
        config: Optional[ConnectionPoolConfig] = None,
        pool_id: Optional[str] = None,
    ) -> None:
        super().__init__(config, pool_id)
        self._create_func = create_func
        self._close_func = close_func
        self._validate_func = validate_func or self._default_validate

    async def _create_connection(self) -> T:
        return await self._create_func()

    async def _close_connection(self, connection: T) -> None:
        await self._close_func(connection)

    async def _validate_connection(self, connection: T) -> bool:
        return await self._validate_func(connection)

    async def _default_validate(self, connection: T) -> bool:
        return connection is not None


# =============================================================================
# HTTP CONNECTION POOL
# =============================================================================


@dataclass
class HTTPClientConfig:
    """Konfiguration for HTTP client pool."""
    base_url: str = ""
    timeout_seconds: float = 30.0
    max_connections_per_host: int = 10
    verify_ssl: bool = True
    headers: Dict[str, str] = field(default_factory=dict)


class HTTPConnectionPool(ConnectionPool[Any]):
    """
    HTTP client connection pool.

    Holder en pool af HTTP client sessions.
    """

    def __init__(
        self,
        http_config: Optional[HTTPClientConfig] = None,
        pool_config: Optional[ConnectionPoolConfig] = None,
        pool_id: Optional[str] = None,
    ) -> None:
        super().__init__(pool_config, pool_id or "http_pool")
        self.http_config = http_config or HTTPClientConfig()

    async def _create_connection(self) -> Any:
        """Opret ny HTTP client session."""
        try:
            import httpx
            return httpx.AsyncClient(
                base_url=self.http_config.base_url,
                timeout=self.http_config.timeout_seconds,
                verify=self.http_config.verify_ssl,
                headers=self.http_config.headers,
            )
        except ImportError:
            # Fallback to aiohttp
            import aiohttp
            connector = aiohttp.TCPConnector(
                limit_per_host=self.http_config.max_connections_per_host,
                ssl=self.http_config.verify_ssl,
            )
            return aiohttp.ClientSession(
                base_url=self.http_config.base_url,
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self.http_config.timeout_seconds),
                headers=self.http_config.headers,
            )

    async def _close_connection(self, connection: Any) -> None:
        """Luk HTTP client session."""
        await connection.close()

    async def _validate_connection(self, connection: Any) -> bool:
        """Valider HTTP client (check if not closed)."""
        try:
            # Check if connection is still open
            if hasattr(connection, 'is_closed'):
                return not connection.is_closed
            if hasattr(connection, 'closed'):
                return not connection.closed
            return True
        except Exception:
            return False


# =============================================================================
# CONNECTION POOL MANAGER
# =============================================================================


class ConnectionPoolManager:
    """
    Manager for multiple connection pools.

    Holder styr på alle pools i systemet.
    """

    def __init__(self) -> None:
        self._pools: Dict[str, ConnectionPool] = {}
        self._lock = asyncio.Lock()

    async def register_pool(
        self,
        name: str,
        pool: ConnectionPool,
        start: bool = True,
    ) -> None:
        """Registrer en connection pool."""
        async with self._lock:
            if name in self._pools:
                raise ValueError(f"Pool already registered: {name}")

            self._pools[name] = pool

            if start:
                await pool.start()

        logger.info(f"Pool registered: {name}")

    async def unregister_pool(
        self,
        name: str,
        stop: bool = True,
    ) -> None:
        """Fjern en connection pool."""
        async with self._lock:
            if name not in self._pools:
                return

            pool = self._pools.pop(name)

            if stop:
                await pool.stop()

        logger.info(f"Pool unregistered: {name}")

    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """Hent pool ved navn."""
        return self._pools.get(name)

    async def stop_all(self) -> None:
        """Stop alle pools."""
        async with self._lock:
            for name, pool in list(self._pools.items()):
                try:
                    await pool.stop()
                except Exception as e:
                    logger.error(f"Error stopping pool {name}: {e}")
            self._pools.clear()

    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Hent statistics for alle pools."""
        return {
            name: pool.get_statistics()
            for name, pool in self._pools.items()
        }


# =============================================================================
# SINGLETON MANAGEMENT
# =============================================================================


_pool_manager: Optional[ConnectionPoolManager] = None


def get_pool_manager() -> ConnectionPoolManager:
    """Hent global pool manager."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager


def set_pool_manager(manager: ConnectionPoolManager) -> None:
    """Sæt global pool manager."""
    global _pool_manager
    _pool_manager = manager


async def create_connection_pool(
    create_func: Callable[[], Awaitable[T]],
    close_func: Callable[[T], Awaitable[None]],
    validate_func: Optional[Callable[[T], Awaitable[bool]]] = None,
    min_size: int = 1,
    max_size: int = 10,
    pool_id: Optional[str] = None,
    register: bool = True,
    **kwargs: Any,
) -> GenericConnectionPool[T]:
    """
    Opret en generic connection pool.

    Args:
        create_func: Factory function til at oprette connections
        close_func: Function til at lukke connections
        validate_func: Optional validation function
        min_size: Minimum antal connections
        max_size: Maximum antal connections
        pool_id: Optional pool ID
        register: Registrer pool i global manager
        **kwargs: Ekstra config options

    Returns:
        GenericConnectionPool instance
    """
    config = ConnectionPoolConfig(
        min_size=min_size,
        max_size=max_size,
        **kwargs,
    )

    pool = GenericConnectionPool(
        create_func=create_func,
        close_func=close_func,
        validate_func=validate_func,
        config=config,
        pool_id=pool_id,
    )

    await pool.start()

    if register:
        manager = get_pool_manager()
        await manager.register_pool(pool.pool_id, pool, start=False)

    return pool


async def create_http_pool(
    base_url: str = "",
    min_size: int = 1,
    max_size: int = 10,
    pool_id: Optional[str] = None,
    register: bool = True,
    **kwargs: Any,
) -> HTTPConnectionPool:
    """
    Opret en HTTP connection pool.

    Args:
        base_url: Base URL for requests
        min_size: Minimum antal connections
        max_size: Maximum antal connections
        pool_id: Optional pool ID
        register: Registrer pool i global manager
        **kwargs: Ekstra HTTP config options

    Returns:
        HTTPConnectionPool instance
    """
    http_config = HTTPClientConfig(
        base_url=base_url,
        **{k: v for k, v in kwargs.items() if hasattr(HTTPClientConfig, k)},
    )

    pool_config = ConnectionPoolConfig(
        min_size=min_size,
        max_size=max_size,
        **{k: v for k, v in kwargs.items() if hasattr(ConnectionPoolConfig, k)},
    )

    pool = HTTPConnectionPool(
        http_config=http_config,
        pool_config=pool_config,
        pool_id=pool_id or "http_pool",
    )

    await pool.start()

    if register:
        manager = get_pool_manager()
        await manager.register_pool(pool.pool_id, pool, start=False)

    return pool


async def create_mastermind_connection_pools() -> ConnectionPoolManager:
    """
    Opret standard connection pools for MASTERMIND.

    Returns:
        ConnectionPoolManager med pre-konfigurerede pools
    """
    manager = get_pool_manager()

    # HTTP pool for external APIs
    http_pool = await create_http_pool(
        min_size=2,
        max_size=10,
        pool_id="mastermind_http",
        register=False,
    )
    await manager.register_pool("http", http_pool, start=False)

    logger.info("MASTERMIND connection pools created")
    return manager


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "PoolState",
    "ConnectionState",
    "LoadBalanceStrategy",
    "PoolEventType",
    # Config
    "ConnectionPoolConfig",
    "HTTPClientConfig",
    # Data classes
    "ConnectionInfo",
    "PoolMetrics",
    "PoolEvent",
    # Connection wrapper
    "PooledConnection",
    # Pool classes
    "ConnectionPool",
    "GenericConnectionPool",
    "HTTPConnectionPool",
    # Manager
    "ConnectionPoolManager",
    # Factory functions
    "get_pool_manager",
    "set_pool_manager",
    "create_connection_pool",
    "create_http_pool",
    "create_mastermind_connection_pools",
]
