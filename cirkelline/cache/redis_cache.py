"""
Redis Cache Implementation
==========================

Provides caching functionality for the Cirkelline system.
Falls back to in-memory cache if Redis is unavailable.
"""

import os
import json
import hashlib
import asyncio
from typing import Optional, Any, Dict, Callable, Union
from datetime import timedelta
from functools import wraps
from dataclasses import dataclass
from collections import OrderedDict
import logging

logger = logging.getLogger("cirkelline.cache")


@dataclass
class CacheConfig:
    """Cache configuration settings."""

    # Redis connection
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))

    # Default TTLs (seconds)
    default_ttl: int = 300  # 5 minutes
    session_ttl: int = 3600  # 1 hour
    user_data_ttl: int = 1800  # 30 minutes
    config_ttl: int = 86400  # 24 hours

    # Cache key prefixes
    prefix: str = "cirkelline:"
    session_prefix: str = "session:"
    user_prefix: str = "user:"
    response_prefix: str = "response:"
    rate_limit_prefix: str = "rate:"

    # In-memory fallback
    memory_max_size: int = 1000


class InMemoryCache:
    """
    Simple in-memory LRU cache as fallback when Redis unavailable.
    Thread-safe for basic operations.
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._ttls: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                return None

            # Check TTL
            import time
            if key in self._ttls and time.time() > self._ttls[key]:
                del self._cache[key]
                del self._ttls[key]
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            return self._cache[key]

    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        async with self._lock:
            import time

            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
                if oldest in self._ttls:
                    del self._ttls[oldest]

            self._cache[key] = value
            self._ttls[key] = time.time() + ttl
            return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._ttls:
                    del self._ttls[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.get(key) is not None

    async def clear(self) -> bool:
        """Clear all cache."""
        async with self._lock:
            self._cache.clear()
            self._ttls.clear()
            return True


class RedisCache:
    """
    Redis cache with automatic fallback to in-memory.

    Usage:
        cache = RedisCache()
        await cache.connect()

        # Set/Get
        await cache.set("key", "value", ttl=300)
        value = await cache.get("key")

        # With prefix
        await cache.set_session("session_id", data)
        data = await cache.get_session("session_id")
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._redis = None
        self._memory_cache = InMemoryCache(self.config.memory_max_size)
        self._connected = False
        self._use_memory = False

    async def connect(self) -> bool:
        """Connect to Redis, fall back to memory if unavailable."""
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                self.config.redis_url,
                db=self.config.redis_db,
                max_connections=self.config.max_connections,
                decode_responses=True,
            )

            # Test connection
            await self._redis.ping()
            self._connected = True
            self._use_memory = False
            logger.info("✅ Redis cache connected")
            return True

        except ImportError:
            logger.warning("redis package not installed, using in-memory cache")
            self._use_memory = True
            self._connected = True
            return True

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory cache")
            self._use_memory = True
            self._connected = True
            return True

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Redis cache disconnected")

    def _make_key(self, key: str, prefix: str = "") -> str:
        """Create prefixed cache key."""
        return f"{self.config.prefix}{prefix}{key}"

    async def get(self, key: str, prefix: str = "") -> Optional[str]:
        """Get value from cache."""
        full_key = self._make_key(key, prefix)

        if self._use_memory:
            return await self._memory_cache.get(full_key)

        try:
            return await self._redis.get(full_key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return await self._memory_cache.get(full_key)

    async def set(
        self,
        key: str,
        value: Union[str, dict, list],
        ttl: int = None,
        prefix: str = ""
    ) -> bool:
        """Set value in cache."""
        full_key = self._make_key(key, prefix)
        ttl = ttl or self.config.default_ttl

        # Serialize if needed
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        if self._use_memory:
            return await self._memory_cache.set(full_key, value, ttl)

        try:
            await self._redis.setex(full_key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return await self._memory_cache.set(full_key, value, ttl)

    async def delete(self, key: str, prefix: str = "") -> bool:
        """Delete key from cache."""
        full_key = self._make_key(key, prefix)

        if self._use_memory:
            return await self._memory_cache.delete(full_key)

        try:
            await self._redis.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return await self._memory_cache.delete(full_key)

    async def exists(self, key: str, prefix: str = "") -> bool:
        """Check if key exists."""
        full_key = self._make_key(key, prefix)

        if self._use_memory:
            return await self._memory_cache.exists(full_key)

        try:
            return await self._redis.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return await self._memory_cache.exists(full_key)

    async def get_json(self, key: str, prefix: str = "") -> Optional[Any]:
        """Get and deserialize JSON value."""
        value = await self.get(key, prefix)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    # Convenience methods with specific prefixes and TTLs

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data."""
        return await self.get_json(session_id, self.config.session_prefix)

    async def set_session(self, session_id: str, data: dict) -> bool:
        """Set session data."""
        return await self.set(
            session_id, data,
            ttl=self.config.session_ttl,
            prefix=self.config.session_prefix
        )

    async def get_user(self, user_id: str) -> Optional[dict]:
        """Get user data."""
        return await self.get_json(user_id, self.config.user_prefix)

    async def set_user(self, user_id: str, data: dict) -> bool:
        """Set user data."""
        return await self.set(
            user_id, data,
            ttl=self.config.user_data_ttl,
            prefix=self.config.user_prefix
        )

    async def invalidate_user(self, user_id: str) -> bool:
        """Invalidate all user-related cache."""
        await self.delete(user_id, self.config.user_prefix)
        # Could also invalidate related sessions here
        return True

    # Rate limiting support (for distributed rate limiting)

    async def incr_rate_limit(self, key: str, window: int = 60) -> int:
        """Increment rate limit counter."""
        full_key = self._make_key(key, self.config.rate_limit_prefix)

        if self._use_memory:
            # Simple in-memory increment
            current = await self._memory_cache.get(full_key)
            new_value = int(current or 0) + 1
            await self._memory_cache.set(full_key, str(new_value), window)
            return new_value

        try:
            pipe = self._redis.pipeline()
            pipe.incr(full_key)
            pipe.expire(full_key, window)
            results = await pipe.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Rate limit incr error: {e}")
            return 0

    async def get_rate_limit(self, key: str) -> int:
        """Get current rate limit count."""
        full_key = self._make_key(key, self.config.rate_limit_prefix)

        if self._use_memory:
            value = await self._memory_cache.get(full_key)
            return int(value or 0)

        try:
            value = await self._redis.get(full_key)
            return int(value or 0)
        except Exception as e:
            logger.error(f"Rate limit get error: {e}")
            return 0


# Global cache instance
_cache: Optional[RedisCache] = None


async def get_cache() -> RedisCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
        await _cache.connect()
    return _cache


def cache_response(
    ttl: int = 300,
    key_prefix: str = "response:",
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache function responses.

    Usage:
        @cache_response(ttl=60)
        async def get_data(user_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = await get_cache()

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key from function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # Try cache first
            cached = await cache.get_json(cache_key, key_prefix)
            if cached is not None:
                return cached

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                await cache.set(cache_key, result, ttl=ttl, prefix=key_prefix)

            return result

        return wrapper
    return decorator


async def invalidate_cache(pattern: str):
    """Invalidate cache keys matching pattern."""
    cache = await get_cache()

    if cache._use_memory:
        # Can't do pattern matching in simple memory cache
        await cache._memory_cache.clear()
        return

    try:
        keys = []
        async for key in cache._redis.scan_iter(f"{cache.config.prefix}{pattern}*"):
            keys.append(key)

        if keys:
            await cache._redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching {pattern}")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")


logger.info("✅ Cache module loaded")
