"""
Cache Manager
=============
Multi-tier caching system for performance optimization.

Responsibilities:
- In-memory caching with LRU eviction
- TTL-based cache expiration
- Cache statistics and monitoring
- Decorator for easy caching
"""

import logging
import time
import hashlib
import threading
import functools
from typing import Optional, Dict, Any, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import OrderedDict

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live only


@dataclass
class CacheEntry:
    """A single cache entry."""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float]
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> Optional[float]:
        if self.expires_at is None:
            return None
        return max(0, self.expires_at - time.time())


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expired": self.expired,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": round(self.hit_rate, 3),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# LRU CACHE
# ═══════════════════════════════════════════════════════════════════════════════

class LRUCache:
    """
    Thread-safe LRU cache implementation.

    Uses OrderedDict for O(1) operations with LRU ordering.
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=max_size)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired:
                del self._cache[key]
                self._stats.expired += 1
                self._stats.misses += 1
                self._stats.size -= 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.access_count += 1
            entry.last_accessed = time.time()
            self._stats.hits += 1

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        with self._lock:
            # Remove if exists
            if key in self._cache:
                del self._cache[key]
                self._stats.size -= 1

            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
                self._stats.evictions += 1
                self._stats.size -= 1

            # Create entry
            now = time.time()
            expires_at = now + ttl_seconds if ttl_seconds else None

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=expires_at,
            )

            self._cache[key] = entry
            self._stats.size += 1

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.size -= 1
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats.size = 0

    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats.expired += 1
                self._stats.size -= 1
            return len(expired_keys)

    @property
    def stats(self) -> CacheStats:
        with self._lock:
            self._stats.size = len(self._cache)
            return self._stats


# ═══════════════════════════════════════════════════════════════════════════════
# CACHE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class CacheManager:
    """
    Multi-tier cache manager.

    Provides unified interface for caching with support for
    multiple cache tiers and strategies.
    """

    def __init__(
        self,
        strategy: CacheStrategy = CacheStrategy.LRU,
        max_size: int = 10000,
        default_ttl: int = 300,  # 5 minutes
    ):
        self._strategy = strategy
        self._max_size = max_size
        self._default_ttl = default_ttl

        # Primary cache
        self._cache = LRUCache(max_size=max_size)

        # Namespace caches
        self._namespaces: Dict[str, LRUCache] = {}

        # Statistics
        self._global_stats = CacheStats(max_size=max_size)

    # ═══════════════════════════════════════════════════════════════════════════
    # BASIC OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def get(
        self,
        key: str,
        namespace: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            namespace: Optional namespace

        Returns:
            Cached value or None
        """
        cache = self._get_cache(namespace)
        return cache.get(key)

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            namespace: Optional namespace
        """
        cache = self._get_cache(namespace)
        cache.set(key, value, ttl or self._default_ttl)

    def delete(
        self,
        key: str,
        namespace: Optional[str] = None,
    ) -> bool:
        """Delete key from cache."""
        cache = self._get_cache(namespace)
        return cache.delete(key)

    def exists(
        self,
        key: str,
        namespace: Optional[str] = None,
    ) -> bool:
        """Check if key exists in cache."""
        value = self.get(key, namespace)
        return value is not None

    def _get_cache(self, namespace: Optional[str]) -> LRUCache:
        """Get cache for namespace."""
        if namespace is None:
            return self._cache

        if namespace not in self._namespaces:
            self._namespaces[namespace] = LRUCache(
                max_size=self._max_size // 10  # Smaller namespace caches
            )
        return self._namespaces[namespace]

    # ═══════════════════════════════════════════════════════════════════════════
    # ADVANCED OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> Any:
        """
        Get value from cache or compute and cache it.

        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time to live in seconds
            namespace: Optional namespace

        Returns:
            Cached or computed value
        """
        value = self.get(key, namespace)
        if value is not None:
            return value

        value = factory()
        self.set(key, value, ttl, namespace)
        return value

    def mget(
        self,
        keys: List[str],
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get multiple values from cache."""
        return {
            key: self.get(key, namespace)
            for key in keys
            if self.get(key, namespace) is not None
        }

    def mset(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> None:
        """Set multiple values in cache."""
        for key, value in items.items():
            self.set(key, value, ttl, namespace)

    def clear(self, namespace: Optional[str] = None) -> None:
        """Clear cache (optionally by namespace)."""
        if namespace is None:
            self._cache.clear()
            for ns_cache in self._namespaces.values():
                ns_cache.clear()
        else:
            cache = self._get_cache(namespace)
            cache.clear()

    def clear_namespace(self, namespace: str) -> None:
        """Clear a specific namespace."""
        if namespace in self._namespaces:
            self._namespaces[namespace].clear()

    # ═══════════════════════════════════════════════════════════════════════════
    # MAINTENANCE
    # ═══════════════════════════════════════════════════════════════════════════

    def cleanup(self) -> int:
        """Remove all expired entries."""
        total = self._cache.cleanup_expired()
        for cache in self._namespaces.values():
            total += cache.cleanup_expired()
        return total

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        main_stats = self._cache.stats

        namespace_stats = {
            name: cache.stats.to_dict()
            for name, cache in self._namespaces.items()
        }

        return {
            "main": main_stats.to_dict(),
            "namespaces": namespace_stats,
            "strategy": self._strategy.value,
            "default_ttl": self._default_ttl,
            "total_namespaces": len(self._namespaces),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DECORATOR
# ═══════════════════════════════════════════════════════════════════════════════

def cached(
    ttl: int = 300,
    namespace: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        namespace: Optional cache namespace
        key_builder: Optional function to build cache key

    Usage:
        @cached(ttl=60)
        def expensive_function(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = ":".join(key_parts)
                # Hash if too long
                if len(key) > 200:
                    key = hashlib.md5(key.encode()).hexdigest()

            # Check cache
            cached_value = cache.get(key, namespace)
            if cached_value is not None:
                return cached_value

            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(key, result, ttl, namespace)
            return result

        return wrapper
    return decorator


def cached_async(
    ttl: int = 300,
    namespace: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator for caching async function results.

    Usage:
        @cached_async(ttl=60)
        async def expensive_async_function(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = ":".join(key_parts)
                if len(key) > 200:
                    key = hashlib.md5(key.encode()).hexdigest()

            # Check cache
            cached_value = cache.get(key, namespace)
            if cached_value is not None:
                return cached_value

            # Compute and cache
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl, namespace)
            return result

        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_cache_instance: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the singleton CacheManager instance."""
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = CacheManager(
            strategy=CacheStrategy.LRU,
            max_size=10000,
            default_ttl=300,
        )

    return _cache_instance


async def init_cache_manager(
    max_size: int = 10000,
    default_ttl: int = 300,
) -> CacheManager:
    """Initialize and return the cache manager."""
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = CacheManager(
            strategy=CacheStrategy.LRU,
            max_size=max_size,
            default_ttl=default_ttl,
        )

    return _cache_instance
