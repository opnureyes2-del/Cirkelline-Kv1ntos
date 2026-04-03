"""
Performance Module
==================
Performance optimization components for the Cirkelline system.

Components:
- Cache Manager: Multi-tier caching system
- Async Utils: Async operation optimization
- Connection Pool: Database and resource pooling
"""

__version__ = "1.0.0"

from cirkelline.performance.async_utils import (
    AsyncBatcher,
    AsyncRetry,
    AsyncTimeout,
    BatchResult,
    batch_process,
    get_batcher,
    retry_async,
    run_with_timeout,
)
from cirkelline.performance.cache import (
    CacheEntry,
    CacheManager,
    CacheStats,
    CacheStrategy,
    cached,
    get_cache_manager,
)
from cirkelline.performance.connection_pool import (
    ConnectionPool,
    PoolConfig,
    PooledConnection,
    PoolStats,
    get_connection_pool,
)

__all__ = [
    # Cache
    'CacheManager',
    'CacheEntry',
    'CacheStrategy',
    'CacheStats',
    'get_cache_manager',
    'cached',
    # Async Utils
    'AsyncBatcher',
    'AsyncRetry',
    'AsyncTimeout',
    'BatchResult',
    'run_with_timeout',
    'retry_async',
    'batch_process',
    'get_batcher',
    # Connection Pool
    'ConnectionPool',
    'PooledConnection',
    'PoolConfig',
    'PoolStats',
    'get_connection_pool',
]
