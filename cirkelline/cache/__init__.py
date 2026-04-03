"""
Cirkelline Cache Module
=======================

Redis-based caching for:
- Session data
- API response caching
- Rate limit state (production)
- User preferences
"""

from cirkelline.cache.redis_cache import (
    CacheConfig,
    RedisCache,
    cache_response,
    get_cache,
    invalidate_cache,
)

__all__ = [
    'RedisCache',
    'get_cache',
    'cache_response',
    'invalidate_cache',
    'CacheConfig',
]
