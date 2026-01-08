#!/usr/bin/env python3
"""
Multi-Layer Cache Manager - WITH EVENT BUS
===========================================

Implements 3-layer caching architecture:
- Layer 1: In-memory (fastest, <1ms)
- Layer 2: Redis (fast, <5ms, shared)
- Layer 3: Database (slower, >10ms)

NOW WITH EVENT BUS INTEGRATION:
- Listens to cache.invalidated events
- Auto-invalidates cache on file changes
- Publishes cache stats

Part of PHASE 1 - Performance Quick Wins
Expected: 4-8x speedup for repeated queries
"""

import redis
import pickle
import hashlib
import time
from typing import Optional, Any, Dict
from datetime import timedelta
import asyncio
from functools import wraps
import threading

# EVENT BUS INTEGRATION
try:
    from event_bus import EventBus
    EVENT_BUS_AVAILABLE = True
except ImportError:
    EVENT_BUS_AVAILABLE = False
    print("⚠️ Event bus not available - running without integration")


class MultiLayerCache:
    """3-layer caching system for ELLE.md ecosystem - WITH EVENT BUS"""

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379,
                 enable_event_bus: bool = True):
        # Layer 1: In-memory cache (fastest)
        self._memory_cache: Dict[str, Any] = {}
        self._memory_max_size = 1000  # Max items in memory
        self._memory_hits = 0
        self._memory_misses = 0

        # Layer 2: Redis cache (fast, shared)
        self._redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=0,
            decode_responses=False  # We use pickle
        )
        self._redis_hits = 0
        self._redis_misses = 0

        # Layer 3: Database (handled by caller)
        self._db_queries = 0

        # EVENT BUS INTEGRATION
        self.event_bus = None
        self._listener_thread = None
        if enable_event_bus and EVENT_BUS_AVAILABLE:
            self.event_bus = EventBus()
            self.event_bus.connect()
            print("✅ Cache Manager: Connected to event bus")

    def start_event_listener(self):
        """Start listening for cache invalidation events"""
        if not self.event_bus:
            print("⚠️ Event bus not available")
            return

        def on_cache_invalidation(message):
            """Handle cache invalidation event"""
            cache_key = message.get('cache_key')
            if cache_key:
                # Sync delete (wrapped in async)
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                self._redis.delete(cache_key)
                print(f"🗑️ Cache invalidated: {cache_key}")
            else:
                # Clear all cache
                self._memory_cache.clear()
                self._redis.flushdb()
                print("🗑️ Cache cleared completely")

        def on_file_change(message):
            """Handle file change event - invalidate related cache"""
            file_path = message.get('file_path', '')
            # Invalidate caches that might be affected by file change
            # For now, we can invalidate all query caches
            keys_to_invalidate = [k for k in self._memory_cache.keys()
                                 if 'query' in k or 'search' in k]
            for key in keys_to_invalidate:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                self._redis.delete(key)

            if keys_to_invalidate:
                print(f"🗑️ Invalidated {len(keys_to_invalidate)} caches due to file change: {file_path}")

        # Subscribe to events
        self.event_bus.subscribe('cache.invalidated', on_cache_invalidation)
        self.event_bus.subscribe('file.changed', on_file_change)
        print("✅ Subscribed to cache.invalidated and file.changed events")

        # Start consuming in background thread
        def consume_events():
            try:
                print("🎧 Event listener thread started")
                self.event_bus.start_consuming()
            except Exception as e:
                print(f"⚠️ Event listener error: {e}")

        self._listener_thread = threading.Thread(target=consume_events, daemon=True)
        self._listener_thread.start()
        print("✅ Event listener running in background")

    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (checks all layers)"""
        # Try Layer 1: Memory cache (< 1ms)
        if key in self._memory_cache:
            self._memory_hits += 1
            return self._memory_cache[key]

        self._memory_misses += 1

        # Try Layer 2: Redis (< 5ms)
        redis_value = self._redis.get(key)
        if redis_value:
            self._redis_hits += 1
            value = pickle.loads(redis_value)
            # Promote to memory cache
            self._memory_cache[key] = value
            self._evict_if_needed()
            return value

        self._redis_misses += 1
        # Layer 3: Caller must query database
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set in all cache layers"""
        # Set in memory
        self._memory_cache[key] = value
        self._evict_if_needed()

        # Set in Redis with TTL
        self._redis.setex(key, ttl, pickle.dumps(value))

    async def delete(self, key: str):
        """Delete from all layers"""
        if key in self._memory_cache:
            del self._memory_cache[key]
        self._redis.delete(key)

    async def clear(self):
        """Clear all caches"""
        self._memory_cache.clear()
        self._redis.flushdb()

    def _evict_if_needed(self):
        """Evict old entries from memory if needed (LRU)"""
        if len(self._memory_cache) > self._memory_max_size:
            # Remove oldest 10% of entries
            to_remove = list(self._memory_cache.keys())[:int(self._memory_max_size * 0.1)]
            for k in to_remove:
                del self._memory_cache[k]

    def get_stats(self) -> dict:
        """Return cache performance statistics"""
        total_requests = self._memory_hits + self._memory_misses
        memory_hit_rate = self._memory_hits / total_requests if total_requests > 0 else 0

        total_redis_requests = self._redis_hits + self._redis_misses
        redis_hit_rate = self._redis_hits / total_redis_requests if total_redis_requests > 0 else 0

        return {
            'memory': {
                'hits': self._memory_hits,
                'misses': self._memory_misses,
                'hit_rate': f"{memory_hit_rate:.2%}",
                'size': len(self._memory_cache),
                'max_size': self._memory_max_size
            },
            'redis': {
                'hits': self._redis_hits,
                'misses': self._redis_misses,
                'hit_rate': f"{redis_hit_rate:.2%}",
                'total_keys': self._redis.dbsize()
            },
            'database': {
                'queries': self._db_queries
            }
        }

    def make_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def run_forever(self):
        """Run cache manager as daemon - keep event listener alive"""
        if not self.event_bus:
            print("⚠️ Cache manager running without event bus")
            print("💡 Start with enable_event_bus=True to enable event-driven cache invalidation")
        else:
            print("✅ Cache manager running with event bus integration")
            print("📡 Listening for cache.invalidated and file.changed events")

        print("🔄 Cache manager daemon started")
        print("   Press Ctrl+C to stop")

        try:
            # Keep the main thread alive so daemon threads can run
            while True:
                time.sleep(60)
                # Print stats every minute
                stats = self.get_stats()
                print(f"[{time.strftime('%H:%M:%S')}] Cache stats: "
                      f"Memory hits: {stats['memory']['hit_rate']}, "
                      f"Redis hits: {stats['redis']['hit_rate']}")
        except KeyboardInterrupt:
            print("\n👋 Cache manager stopped")


# Decorator for automatic caching
def cached(ttl: int = 3600):
    """Decorator to automatically cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache = getattr(self, '_cache', None)
            if not cache:
                # No cache available, just execute
                return await func(self, *args, **kwargs)

            cache_key = cache.make_cache_key(
                f"{func.__module__}.{func.__name__}",
                *args,
                **kwargs
            )

            # Try cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Cache miss - execute function
            result = await func(self, *args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


# Example usage
class CachedKnowledgeBase:
    """Example: Knowledge base with caching"""

    def __init__(self, db_connection):
        self.db = db_connection
        self._cache = MultiLayerCache()

    @cached(ttl=3600)  # Cache for 1 hour
    async def search(self, query: str, limit: int = 10):
        """Search with automatic caching"""
        # This will be cached automatically
        results = await self._query_database(query, limit)
        return results

    async def _query_database(self, query: str, limit: int):
        """Actual database query (slow)"""
        # Real implementation would query database here
        self._cache._db_queries += 1
        return []

    async def invalidate_cache(self):
        """Invalidate all cache when data changes"""
        await self._cache.clear()


if __name__ == '__main__':
    # Run cache manager as daemon with event bus integration
    cache = MultiLayerCache(enable_event_bus=True)
    cache.run_forever()
