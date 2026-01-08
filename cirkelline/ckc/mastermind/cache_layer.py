"""
CKC MASTERMIND Cache Layer (DEL AF)
====================================

Multi-tier caching system med L1 (memory) og L2 (Redis) support.

Features:
    - Multi-tier caching (L1 Memory + L2 Redis)
    - Cache warming og pre-population
    - Distributed invalidation
    - Cache namespacing per feature
    - Write-through og write-behind strategier
    - Cache decorators for nem brug

Arkitektur:
    Request --> L1 Cache (Memory) --> L2 Cache (Redis) --> Database
              ↓ hit                  ↓ hit               ↓ miss
            Return                 Return + L1 warm      Fetch + Cache warm

Brug:
    from cirkelline.ckc.mastermind.cache_layer import (
        create_cache_layer,
        get_cache_layer,
        cached,
        invalidate_cache,
    )

    # Opret cache layer
    cache = await create_cache_layer(
        enable_redis=True,
        redis_url="redis://localhost:6379/0"
    )

    # Cache decorator
    @cached(namespace="users", ttl_seconds=300)
    async def get_user(user_id: str) -> dict:
        return await db.fetch_user(user_id)

    # Manuel caching
    await cache.set("key", value, namespace="sessions")
    value = await cache.get("key", namespace="sessions")

    # Invalidation
    await invalidate_cache("users", pattern="user_*")
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import logging
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class CacheTier(Enum):
    """Cache tier levels."""
    L1_MEMORY = "l1_memory"     # In-process memory cache
    L2_REDIS = "l2_redis"       # Distributed Redis cache
    L3_DATABASE = "l3_database" # Database (cache miss)


class WriteStrategy(Enum):
    """Cache write strategies."""
    WRITE_THROUGH = "write_through"   # Write to cache + backend immediately
    WRITE_BEHIND = "write_behind"     # Write to cache, async to backend
    WRITE_AROUND = "write_around"     # Write only to backend, invalidate cache


class InvalidationStrategy(Enum):
    """Cache invalidation strategies."""
    IMMEDIATE = "immediate"     # Invalidate immediately
    LAZY = "lazy"               # Mark as stale, revalidate on access
    TTL_BASED = "ttl_based"     # Let entries expire naturally
    EVENT_DRIVEN = "event_driven"  # Invalidate on events


class CacheStatus(Enum):
    """Status for cache entries."""
    FRESH = "fresh"       # Entry is fresh and valid
    STALE = "stale"       # Entry is stale but usable
    EXPIRED = "expired"   # Entry has expired
    WARMING = "warming"   # Entry is being warmed/refreshed


class CompressionType(Enum):
    """Cache value compression types."""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CacheLayerConfig:
    """Konfiguration for cache layer."""
    # L1 Memory settings
    l1_enabled: bool = True
    l1_max_size_mb: float = 256.0
    l1_max_entries: int = 10000
    l1_default_ttl_seconds: int = 300

    # L2 Redis settings
    l2_enabled: bool = False
    l2_redis_url: str = "redis://localhost:6379/0"
    l2_default_ttl_seconds: int = 3600
    l2_connection_pool_size: int = 10
    l2_socket_timeout: float = 5.0

    # Write strategy
    write_strategy: WriteStrategy = WriteStrategy.WRITE_THROUGH
    write_behind_delay_seconds: float = 1.0
    write_behind_batch_size: int = 100

    # Invalidation
    invalidation_strategy: InvalidationStrategy = InvalidationStrategy.IMMEDIATE
    stale_while_revalidate_seconds: int = 60

    # Compression
    compression: CompressionType = CompressionType.NONE
    compression_threshold_bytes: int = 1024

    # Warming
    enable_cache_warming: bool = True
    warming_batch_size: int = 50
    warming_concurrency: int = 5

    # Namespaces
    default_namespace: str = "default"
    namespace_separator: str = ":"

    # Monitoring
    enable_metrics: bool = True
    slow_cache_threshold_ms: float = 50.0


@dataclass
class CacheEntry:
    """En cache entry med metadata."""
    key: str
    value: Any
    namespace: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    size_bytes: int = 0
    tier: CacheTier = CacheTier.L1_MEMORY
    status: CacheStatus = CacheStatus.FRESH
    version: int = 1
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check om entry er expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    @property
    def is_stale(self) -> bool:
        """Check om entry er stale."""
        return self.status == CacheStatus.STALE

    @property
    def ttl_remaining_seconds(self) -> Optional[float]:
        """Hent remaining TTL i sekunder."""
        if self.expires_at is None:
            return None
        remaining = (self.expires_at - datetime.now()).total_seconds()
        return max(0, remaining)


@dataclass
class CacheNamespace:
    """Namespace for cache entries."""
    name: str
    description: str = ""
    default_ttl_seconds: int = 3600
    max_entries: int = 1000
    tags: Set[str] = field(default_factory=set)
    write_strategy: Optional[WriteStrategy] = None
    compression: Optional[CompressionType] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WarmingTask:
    """Task for cache warming."""
    task_id: str
    namespace: str
    keys: List[str]
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items_warmed: int = 0
    items_failed: int = 0
    error: Optional[str] = None


@dataclass
class CacheMetrics:
    """Metrics for cache performance."""
    # Hit/miss stats
    total_requests: int = 0
    l1_hits: int = 0
    l2_hits: int = 0
    cache_misses: int = 0

    # Latency
    avg_get_latency_ms: float = 0.0
    avg_set_latency_ms: float = 0.0
    p99_get_latency_ms: float = 0.0
    p99_set_latency_ms: float = 0.0

    # Size
    l1_entries: int = 0
    l1_size_bytes: int = 0
    l2_entries: int = 0

    # Operations
    evictions: int = 0
    invalidations: int = 0
    warmings: int = 0

    # Errors
    l1_errors: int = 0
    l2_errors: int = 0

    # Time
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def hit_rate_percent(self) -> float:
        """Beregn overall hit rate."""
        if self.total_requests == 0:
            return 0.0
        hits = self.l1_hits + self.l2_hits
        return (hits / self.total_requests) * 100

    @property
    def l1_hit_rate_percent(self) -> float:
        """Beregn L1 hit rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.l1_hits / self.total_requests) * 100


@dataclass
class InvalidationEvent:
    """Event for cache invalidation."""
    event_id: str
    namespace: str
    pattern: Optional[str] = None
    keys: Optional[List[str]] = None
    tags: Optional[Set[str]] = None
    reason: str = "manual"
    timestamp: datetime = field(default_factory=datetime.now)
    affected_entries: int = 0


# =============================================================================
# CACHE BACKEND INTERFACE
# =============================================================================


T = TypeVar('T')


class CacheBackend(ABC, Generic[T]):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Hent værdi fra cache."""
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: T,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Sæt værdi i cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Slet værdi fra cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check om key eksisterer."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Ryd hele cachen."""
        pass

    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """Hent keys der matcher pattern."""
        pass


# =============================================================================
# L1 MEMORY CACHE BACKEND
# =============================================================================


class L1MemoryCache(CacheBackend[Any]):
    """
    In-memory cache backend (L1).

    Features:
        - Fast in-process caching
        - LRU eviction
        - TTL support
        - Size-based limits
    """

    def __init__(
        self,
        max_size_mb: float = 256.0,
        max_entries: int = 10000,
        default_ttl_seconds: int = 300,
    ) -> None:
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.max_entries = max_entries
        self.default_ttl = default_ttl_seconds

        self._cache: Dict[str, CacheEntry] = {}
        self._total_size = 0
        self._lock = asyncio.Lock()

        logger.info(
            f"L1 Memory Cache initialized: "
            f"max_size={max_size_mb}MB, max_entries={max_entries}"
        )

    async def get(self, key: str) -> Optional[Any]:
        """Hent værdi fra L1 cache."""
        async with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired:
                self._remove_entry(key)
                return None

            # Update access info
            entry.last_accessed = datetime.now()
            entry.access_count += 1

            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Sæt værdi i L1 cache."""
        try:
            async with self._lock:
                # Estimate size
                size = self._estimate_size(value)

                # Make room if needed
                while (
                    self._total_size + size > self.max_size_bytes
                    or len(self._cache) >= self.max_entries
                ):
                    if not self._evict_lru():
                        break

                ttl = ttl_seconds or self.default_ttl
                entry = CacheEntry(
                    key=key,
                    value=value,
                    namespace="",
                    expires_at=datetime.now() + timedelta(seconds=ttl) if ttl else None,
                    size_bytes=size,
                    tier=CacheTier.L1_MEMORY,
                )

                # Update size tracking
                if key in self._cache:
                    self._total_size -= self._cache[key].size_bytes

                self._cache[key] = entry
                self._total_size += size

                return True

        except Exception as e:
            logger.error(f"L1 set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Slet værdi fra L1 cache."""
        async with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check om key eksisterer i L1."""
        async with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            if entry.is_expired:
                self._remove_entry(key)
                return False
            return True

    async def clear(self) -> bool:
        """Ryd L1 cache."""
        async with self._lock:
            self._cache.clear()
            self._total_size = 0
            return True

    async def keys(self, pattern: str = "*") -> List[str]:
        """Hent keys der matcher pattern."""
        async with self._lock:
            if pattern == "*":
                return list(self._cache.keys())

            import fnmatch
            return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]

    def _remove_entry(self, key: str) -> None:
        """Fjern entry internt (caller skal holde lock)."""
        if key in self._cache:
            self._total_size -= self._cache[key].size_bytes
            del self._cache[key]

    def _evict_lru(self) -> bool:
        """Evict least recently used entry."""
        if not self._cache:
            return False

        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        self._remove_entry(lru_key)
        return True

    def _estimate_size(self, value: Any) -> int:
        """Estimér størrelse i bytes."""
        try:
            return len(json.dumps(value, default=str).encode('utf-8'))
        except (TypeError, ValueError):
            return 1024

    @property
    def entry_count(self) -> int:
        """Antal entries i cache."""
        return len(self._cache)

    @property
    def size_bytes(self) -> int:
        """Total størrelse i bytes."""
        return self._total_size


# =============================================================================
# L2 REDIS CACHE BACKEND
# =============================================================================


class L2RedisCache(CacheBackend[Any]):
    """
    Redis cache backend (L2).

    Features:
        - Distributed caching
        - Persistence
        - Pub/sub for invalidation
        - Connection pooling
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl_seconds: int = 3600,
        pool_size: int = 10,
        socket_timeout: float = 5.0,
    ) -> None:
        self.redis_url = redis_url
        self.default_ttl = default_ttl_seconds
        self.pool_size = pool_size
        self.socket_timeout = socket_timeout

        self._redis: Optional[Any] = None
        self._connected = False

        logger.info(f"L2 Redis Cache initialized: url={redis_url}")

    async def connect(self) -> bool:
        """Opret forbindelse til Redis."""
        try:
            # Try to import redis
            try:
                import redis.asyncio as aioredis
            except ImportError:
                logger.warning("redis package not installed, L2 cache disabled")
                return False

            self._redis = await aioredis.from_url(
                self.redis_url,
                max_connections=self.pool_size,
                socket_timeout=self.socket_timeout,
                decode_responses=False,
            )

            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info("L2 Redis Cache connected")
            return True

        except Exception as e:
            logger.error(f"L2 Redis connection failed: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Luk Redis forbindelse."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("L2 Redis Cache disconnected")

    async def get(self, key: str) -> Optional[Any]:
        """Hent værdi fra L2 Redis cache."""
        if not self._connected or not self._redis:
            return None

        try:
            data = await self._redis.get(key)
            if data is None:
                return None
            return json.loads(data)

        except Exception as e:
            logger.error(f"L2 get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Sæt værdi i L2 Redis cache."""
        if not self._connected or not self._redis:
            return False

        try:
            data = json.dumps(value, default=str)
            ttl = ttl_seconds or self.default_ttl

            if ttl:
                await self._redis.setex(key, ttl, data)
            else:
                await self._redis.set(key, data)

            return True

        except Exception as e:
            logger.error(f"L2 set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Slet værdi fra L2 Redis cache."""
        if not self._connected or not self._redis:
            return False

        try:
            result = await self._redis.delete(key)
            return result > 0

        except Exception as e:
            logger.error(f"L2 delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check om key eksisterer i L2."""
        if not self._connected or not self._redis:
            return False

        try:
            return await self._redis.exists(key) > 0

        except Exception as e:
            logger.error(f"L2 exists error for key {key}: {e}")
            return False

    async def clear(self) -> bool:
        """Ryd L2 Redis cache (FARLIGT!)."""
        if not self._connected or not self._redis:
            return False

        try:
            await self._redis.flushdb()
            return True

        except Exception as e:
            logger.error(f"L2 clear error: {e}")
            return False

    async def keys(self, pattern: str = "*") -> List[str]:
        """Hent keys der matcher pattern."""
        if not self._connected or not self._redis:
            return []

        try:
            keys = await self._redis.keys(pattern)
            return [k.decode() if isinstance(k, bytes) else k for k in keys]

        except Exception as e:
            logger.error(f"L2 keys error for pattern {pattern}: {e}")
            return []

    @property
    def is_connected(self) -> bool:
        """Check om Redis er connected."""
        return self._connected


# =============================================================================
# MULTI-TIER CACHE LAYER
# =============================================================================


class CacheLayer:
    """
    Multi-tier cache layer med L1 (memory) og L2 (Redis).

    Håndterer:
        - Cache hierarchy (L1 -> L2 -> Backend)
        - Namespacing
        - Warming
        - Invalidation
        - Metrics
    """

    def __init__(self, config: Optional[CacheLayerConfig] = None) -> None:
        self.config = config or CacheLayerConfig()

        # Initialize L1
        self._l1: Optional[L1MemoryCache] = None
        if self.config.l1_enabled:
            self._l1 = L1MemoryCache(
                max_size_mb=self.config.l1_max_size_mb,
                max_entries=self.config.l1_max_entries,
                default_ttl_seconds=self.config.l1_default_ttl_seconds,
            )

        # Initialize L2 (lazy connection)
        self._l2: Optional[L2RedisCache] = None
        if self.config.l2_enabled:
            self._l2 = L2RedisCache(
                redis_url=self.config.l2_redis_url,
                default_ttl_seconds=self.config.l2_default_ttl_seconds,
                pool_size=self.config.l2_connection_pool_size,
                socket_timeout=self.config.l2_socket_timeout,
            )

        # Namespaces
        self._namespaces: Dict[str, CacheNamespace] = {}

        # Metrics
        self._metrics = CacheMetrics()
        self._get_latencies: List[float] = []
        self._set_latencies: List[float] = []

        # Write-behind queue
        self._write_behind_queue: List[Tuple[str, Any, int]] = []
        self._write_behind_task: Optional[asyncio.Task] = None

        # Warming tasks
        self._warming_tasks: Dict[str, WarmingTask] = {}

        # Callbacks
        self._invalidation_callbacks: List[Callable[[InvalidationEvent], Awaitable[None]]] = []

        logger.info(
            f"CacheLayer initialized: L1={self.config.l1_enabled}, L2={self.config.l2_enabled}"
        )

    async def start(self) -> bool:
        """Start cache layer."""
        try:
            # Connect L2 if enabled
            if self._l2:
                await self._l2.connect()

            # Start write-behind task if needed
            if self.config.write_strategy == WriteStrategy.WRITE_BEHIND:
                self._write_behind_task = asyncio.create_task(
                    self._write_behind_loop()
                )

            logger.info("CacheLayer started")
            return True

        except Exception as e:
            logger.error(f"Failed to start CacheLayer: {e}")
            return False

    async def stop(self) -> None:
        """Stop cache layer."""
        # Stop write-behind
        if self._write_behind_task:
            self._write_behind_task.cancel()
            try:
                await self._write_behind_task
            except asyncio.CancelledError:
                pass

        # Disconnect L2
        if self._l2:
            await self._l2.disconnect()

        logger.info("CacheLayer stopped")

    def _make_key(self, key: str, namespace: Optional[str] = None) -> str:
        """Opret full cache key med namespace."""
        ns = namespace or self.config.default_namespace
        return f"{ns}{self.config.namespace_separator}{key}"

    async def get(
        self,
        key: str,
        namespace: Optional[str] = None,
        default: Optional[T] = None,
    ) -> Optional[T]:
        """
        Hent værdi fra cache (L1 -> L2 -> None).

        Args:
            key: Cache key
            namespace: Optional namespace
            default: Default værdi hvis ikke fundet

        Returns:
            Cached værdi eller default
        """
        start_time = time.perf_counter()
        full_key = self._make_key(key, namespace)
        self._metrics.total_requests += 1

        try:
            # Try L1
            if self._l1:
                value = await self._l1.get(full_key)
                if value is not None:
                    self._metrics.l1_hits += 1
                    self._record_latency("get", start_time)
                    return value

            # Try L2
            if self._l2 and self._l2.is_connected:
                value = await self._l2.get(full_key)
                if value is not None:
                    self._metrics.l2_hits += 1
                    # Warm L1
                    if self._l1:
                        await self._l1.set(full_key, value)
                    self._record_latency("get", start_time)
                    return value

            # Cache miss
            self._metrics.cache_misses += 1
            self._record_latency("get", start_time)
            return default

        except Exception as e:
            logger.error(f"Cache get error for {full_key}: {e}")
            self._metrics.l1_errors += 1
            return default

    async def set(
        self,
        key: str,
        value: Any,
        namespace: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None,
    ) -> bool:
        """
        Sæt værdi i cache (L1 + L2).

        Args:
            key: Cache key
            value: Værdi at cache
            namespace: Optional namespace
            ttl_seconds: TTL i sekunder
            tags: Tags for invalidation

        Returns:
            True hvis success
        """
        start_time = time.perf_counter()
        full_key = self._make_key(key, namespace)

        try:
            success = True

            # L1
            if self._l1:
                l1_success = await self._l1.set(
                    full_key, value, ttl_seconds or self.config.l1_default_ttl_seconds
                )
                success = success and l1_success

            # L2 (based on write strategy)
            if self._l2 and self._l2.is_connected:
                if self.config.write_strategy == WriteStrategy.WRITE_THROUGH:
                    l2_success = await self._l2.set(
                        full_key, value, ttl_seconds or self.config.l2_default_ttl_seconds
                    )
                    success = success and l2_success
                elif self.config.write_strategy == WriteStrategy.WRITE_BEHIND:
                    self._write_behind_queue.append((
                        full_key, value, ttl_seconds or self.config.l2_default_ttl_seconds
                    ))

            self._record_latency("set", start_time)
            return success

        except Exception as e:
            logger.error(f"Cache set error for {full_key}: {e}")
            self._metrics.l1_errors += 1
            return False

    async def delete(
        self,
        key: str,
        namespace: Optional[str] = None,
    ) -> bool:
        """Slet værdi fra cache."""
        full_key = self._make_key(key, namespace)

        try:
            success = True

            if self._l1:
                success = await self._l1.delete(full_key) and success

            if self._l2 and self._l2.is_connected:
                success = await self._l2.delete(full_key) and success

            self._metrics.invalidations += 1
            return success

        except Exception as e:
            logger.error(f"Cache delete error for {full_key}: {e}")
            return False

    async def invalidate(
        self,
        namespace: Optional[str] = None,
        pattern: Optional[str] = None,
        keys: Optional[List[str]] = None,
        tags: Optional[Set[str]] = None,
        reason: str = "manual",
    ) -> InvalidationEvent:
        """
        Invalider cache entries.

        Args:
            namespace: Namespace at invalidere
            pattern: Key pattern (wildcards allowed)
            keys: Specifikke keys
            tags: Tags at invalidere
            reason: Årsag til invalidation

        Returns:
            InvalidationEvent med detaljer
        """
        import uuid

        event = InvalidationEvent(
            event_id=f"inv_{uuid.uuid4().hex[:12]}",
            namespace=namespace or "*",
            pattern=pattern,
            keys=keys,
            tags=tags,
            reason=reason,
        )

        affected = 0

        try:
            # Build key pattern
            if keys:
                # Delete specific keys
                for key in keys:
                    full_key = self._make_key(key, namespace)
                    if await self.delete(key, namespace):
                        affected += 1
            elif pattern:
                # Delete by pattern
                full_pattern = self._make_key(pattern, namespace)

                if self._l1:
                    matching_keys = await self._l1.keys(full_pattern)
                    for key in matching_keys:
                        await self._l1.delete(key)
                        affected += 1

                if self._l2 and self._l2.is_connected:
                    matching_keys = await self._l2.keys(full_pattern)
                    for key in matching_keys:
                        await self._l2.delete(key)
            else:
                # Clear namespace
                ns_pattern = self._make_key("*", namespace)

                if self._l1:
                    matching_keys = await self._l1.keys(ns_pattern)
                    for key in matching_keys:
                        await self._l1.delete(key)
                        affected += 1

                if self._l2 and self._l2.is_connected:
                    matching_keys = await self._l2.keys(ns_pattern)
                    for key in matching_keys:
                        await self._l2.delete(key)

            event.affected_entries = affected
            self._metrics.invalidations += affected

            # Notify callbacks
            for callback in self._invalidation_callbacks:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Invalidation callback error: {e}")

            logger.info(
                f"Cache invalidated: namespace={namespace}, "
                f"pattern={pattern}, affected={affected}"
            )

            return event

        except Exception as e:
            logger.error(f"Invalidation error: {e}")
            event.affected_entries = affected
            return event

    async def warm(
        self,
        namespace: str,
        loader: Callable[[str], Awaitable[Any]],
        keys: List[str],
    ) -> WarmingTask:
        """
        Warm cache med data.

        Args:
            namespace: Namespace at varme
            loader: Async function til at loade data
            keys: Keys at varme

        Returns:
            WarmingTask med status
        """
        import uuid

        task = WarmingTask(
            task_id=f"warm_{uuid.uuid4().hex[:12]}",
            namespace=namespace,
            keys=keys,
            status="running",
            started_at=datetime.now(),
        )

        self._warming_tasks[task.task_id] = task

        try:
            # Batch warming
            for i in range(0, len(keys), self.config.warming_batch_size):
                batch = keys[i:i + self.config.warming_batch_size]

                # Concurrent warming within batch
                async def warm_key(key: str) -> bool:
                    try:
                        value = await loader(key)
                        if value is not None:
                            await self.set(key, value, namespace)
                            return True
                        return False
                    except Exception as e:
                        logger.error(f"Warming error for {key}: {e}")
                        return False

                results = await asyncio.gather(
                    *[warm_key(k) for k in batch],
                    return_exceptions=True
                )

                for result in results:
                    if result is True:
                        task.items_warmed += 1
                    else:
                        task.items_failed += 1

            task.status = "completed"
            task.completed_at = datetime.now()
            self._metrics.warmings += task.items_warmed

            logger.info(
                f"Cache warming completed: {task.items_warmed} warmed, "
                f"{task.items_failed} failed"
            )

            return task

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            logger.error(f"Cache warming failed: {e}")
            return task

    def register_namespace(
        self,
        name: str,
        description: str = "",
        default_ttl_seconds: int = 3600,
        max_entries: int = 1000,
        tags: Optional[Set[str]] = None,
    ) -> CacheNamespace:
        """Registrer en cache namespace."""
        namespace = CacheNamespace(
            name=name,
            description=description,
            default_ttl_seconds=default_ttl_seconds,
            max_entries=max_entries,
            tags=tags or set(),
        )
        self._namespaces[name] = namespace
        logger.info(f"Registered cache namespace: {name}")
        return namespace

    def on_invalidation(
        self,
        callback: Callable[[InvalidationEvent], Awaitable[None]],
    ) -> None:
        """Registrer callback for invalidation events."""
        self._invalidation_callbacks.append(callback)

    async def _write_behind_loop(self) -> None:
        """Background task for write-behind writes."""
        while True:
            try:
                await asyncio.sleep(self.config.write_behind_delay_seconds)

                if not self._write_behind_queue:
                    continue

                # Process batch
                batch = self._write_behind_queue[:self.config.write_behind_batch_size]
                self._write_behind_queue = self._write_behind_queue[
                    self.config.write_behind_batch_size:
                ]

                if self._l2 and self._l2.is_connected:
                    for key, value, ttl in batch:
                        await self._l2.set(key, value, ttl)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Write-behind error: {e}")

    def _record_latency(self, op: str, start_time: float) -> None:
        """Record operation latency."""
        latency_ms = (time.perf_counter() - start_time) * 1000

        if op == "get":
            self._get_latencies.append(latency_ms)
            if len(self._get_latencies) > 1000:
                self._get_latencies = self._get_latencies[-1000:]

            self._metrics.avg_get_latency_ms = sum(self._get_latencies) / len(self._get_latencies)
            if self._get_latencies:
                sorted_lat = sorted(self._get_latencies)
                p99_idx = int(len(sorted_lat) * 0.99)
                self._metrics.p99_get_latency_ms = sorted_lat[p99_idx] if p99_idx < len(sorted_lat) else sorted_lat[-1]

        elif op == "set":
            self._set_latencies.append(latency_ms)
            if len(self._set_latencies) > 1000:
                self._set_latencies = self._set_latencies[-1000:]

            self._metrics.avg_set_latency_ms = sum(self._set_latencies) / len(self._set_latencies)
            if self._set_latencies:
                sorted_lat = sorted(self._set_latencies)
                p99_idx = int(len(sorted_lat) * 0.99)
                self._metrics.p99_set_latency_ms = sorted_lat[p99_idx] if p99_idx < len(sorted_lat) else sorted_lat[-1]

    def get_metrics(self) -> CacheMetrics:
        """Hent cache metrics."""
        if self._l1:
            self._metrics.l1_entries = self._l1.entry_count
            self._metrics.l1_size_bytes = self._l1.size_bytes

        self._metrics.last_updated = datetime.now()
        return self._metrics

    def get_statistics(self) -> Dict[str, Any]:
        """Hent cache statistics som dict."""
        metrics = self.get_metrics()
        return {
            "total_requests": metrics.total_requests,
            "l1_hits": metrics.l1_hits,
            "l2_hits": metrics.l2_hits,
            "cache_misses": metrics.cache_misses,
            "hit_rate_percent": metrics.hit_rate_percent,
            "l1_hit_rate_percent": metrics.l1_hit_rate_percent,
            "avg_get_latency_ms": metrics.avg_get_latency_ms,
            "p99_get_latency_ms": metrics.p99_get_latency_ms,
            "avg_set_latency_ms": metrics.avg_set_latency_ms,
            "l1_entries": metrics.l1_entries,
            "l1_size_bytes": metrics.l1_size_bytes,
            "evictions": metrics.evictions,
            "invalidations": metrics.invalidations,
            "warmings": metrics.warmings,
            "namespaces": list(self._namespaces.keys()),
            "l2_connected": self._l2.is_connected if self._l2 else False,
        }


# =============================================================================
# CACHE DECORATOR
# =============================================================================


def cached(
    namespace: str = "default",
    ttl_seconds: int = 3600,
    key_builder: Optional[Callable[..., str]] = None,
) -> Callable:
    """
    Decorator for at cache function results.

    Args:
        namespace: Cache namespace
        ttl_seconds: TTL i sekunder
        key_builder: Optional custom key builder

    Example:
        @cached(namespace="users", ttl_seconds=300)
        async def get_user(user_id: str) -> dict:
            return await db.fetch_user(user_id)
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Default key from function name and args
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # Try to get from cache
            cache = get_cache_layer()
            if cache:
                cached_value = await cache.get(key, namespace)
                if cached_value is not None:
                    return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            if cache and result is not None:
                await cache.set(key, result, namespace, ttl_seconds)

            return result

        return wrapper
    return decorator


# =============================================================================
# SINGLETON MANAGEMENT
# =============================================================================


_cache_layer_instance: Optional[CacheLayer] = None


async def create_cache_layer(
    l1_enabled: bool = True,
    l1_max_size_mb: float = 256.0,
    l2_enabled: bool = False,
    l2_redis_url: str = "redis://localhost:6379/0",
    **kwargs: Any,
) -> CacheLayer:
    """
    Opret og start en ny CacheLayer instance.

    Args:
        l1_enabled: Aktiver L1 memory cache
        l1_max_size_mb: Max størrelse for L1
        l2_enabled: Aktiver L2 Redis cache
        l2_redis_url: Redis URL
        **kwargs: Ekstra config options

    Returns:
        CacheLayer instance
    """
    global _cache_layer_instance

    config = CacheLayerConfig(
        l1_enabled=l1_enabled,
        l1_max_size_mb=l1_max_size_mb,
        l2_enabled=l2_enabled,
        l2_redis_url=l2_redis_url,
        **kwargs,
    )

    _cache_layer_instance = CacheLayer(config)
    await _cache_layer_instance.start()

    logger.info("CacheLayer created and started")
    return _cache_layer_instance


def get_cache_layer() -> Optional[CacheLayer]:
    """Hent current CacheLayer instance."""
    return _cache_layer_instance


def set_cache_layer(cache: CacheLayer) -> None:
    """Sæt CacheLayer instance."""
    global _cache_layer_instance
    _cache_layer_instance = cache


async def invalidate_cache(
    namespace: str,
    pattern: Optional[str] = None,
    keys: Optional[List[str]] = None,
    reason: str = "manual",
) -> Optional[InvalidationEvent]:
    """
    Convenience function til cache invalidation.

    Args:
        namespace: Namespace at invalidere
        pattern: Key pattern
        keys: Specifikke keys
        reason: Årsag

    Returns:
        InvalidationEvent eller None
    """
    cache = get_cache_layer()
    if cache:
        return await cache.invalidate(
            namespace=namespace,
            pattern=pattern,
            keys=keys,
            reason=reason,
        )
    return None


async def create_mastermind_cache_layer() -> CacheLayer:
    """
    Opret CacheLayer konfigureret til MASTERMIND.

    Returns:
        CacheLayer med optimerede settings
    """
    cache = await create_cache_layer(
        l1_enabled=True,
        l1_max_size_mb=256.0,
        l1_max_entries=10000,
        l1_default_ttl_seconds=300,
        l2_enabled=False,  # Enable when Redis available
        write_strategy=WriteStrategy.WRITE_THROUGH,
        enable_cache_warming=True,
    )

    # Register standard namespaces
    cache.register_namespace(
        "sessions",
        description="User session data",
        default_ttl_seconds=3600,
    )
    cache.register_namespace(
        "queries",
        description="Database query results",
        default_ttl_seconds=300,
    )
    cache.register_namespace(
        "agents",
        description="Agent state and context",
        default_ttl_seconds=600,
    )
    cache.register_namespace(
        "decisions",
        description="Decision engine results",
        default_ttl_seconds=1800,
    )
    cache.register_namespace(
        "insights",
        description="Synthesized insights",
        default_ttl_seconds=3600,
    )

    logger.info("MASTERMIND CacheLayer created with standard namespaces")
    return cache


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "CacheTier",
    "WriteStrategy",
    "InvalidationStrategy",
    "CacheStatus",
    "CompressionType",
    # Config
    "CacheLayerConfig",
    # Data classes
    "CacheEntry",
    "CacheNamespace",
    "WarmingTask",
    "CacheMetrics",
    "InvalidationEvent",
    # Backends
    "CacheBackend",
    "L1MemoryCache",
    "L2RedisCache",
    # Main class
    "CacheLayer",
    # Decorator
    "cached",
    # Factory functions
    "create_cache_layer",
    "get_cache_layer",
    "set_cache_layer",
    "invalidate_cache",
    "create_mastermind_cache_layer",
]
