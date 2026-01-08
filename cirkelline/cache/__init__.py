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
    RedisCache,
    get_cache,
    cache_response,
    invalidate_cache,
    CacheConfig,
)

__all__ = [
    'RedisCache',
    'get_cache',
    'cache_response',
    'invalidate_cache',
    'CacheConfig',
]
