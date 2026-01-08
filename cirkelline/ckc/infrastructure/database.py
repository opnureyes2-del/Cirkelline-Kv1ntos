"""
CKC Database Layer
==================

AsyncPG-baseret database connection pool med:
- Automatic connection management
- Transaction support
- Health checks
- Connection pooling

Usage:
    from cirkelline.ckc.infrastructure import get_database

    db = await get_database()
    async with db.transaction() as conn:
        result = await conn.fetchrow("SELECT * FROM ckc.task_contexts WHERE id = $1", id)
"""

import asyncio
import os
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from datetime import datetime

try:
    import asyncpg
    from asyncpg import Pool, Connection
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    asyncpg = None
    Pool = None
    Connection = None

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "localhost"
    port: int = 5533  # CKC-specific port
    database: str = "ckc_brain"
    user: str = "ckc"
    password: str = field(default_factory=lambda: os.getenv("CKC_DB_PASSWORD", "ckc_secure_password_2025"))

    # Pool settings
    min_pool_size: int = 2
    max_pool_size: int = 10
    max_inactive_connection_lifetime: float = 300.0

    # Timeouts
    command_timeout: float = 60.0
    connect_timeout: float = 10.0

    @property
    def dsn(self) -> str:
        """Return PostgreSQL DSN string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("CKC_DB_HOST", "localhost"),
            port=int(os.getenv("CKC_DB_PORT", "5533")),
            database=os.getenv("CKC_DB_NAME", "ckc_brain"),
            user=os.getenv("CKC_DB_USER", "ckc"),
            password=os.getenv("CKC_DB_PASSWORD", "ckc_secure_password_2025"),
            min_pool_size=int(os.getenv("CKC_DB_MIN_POOL", "2")),
            max_pool_size=int(os.getenv("CKC_DB_MAX_POOL", "10")),
        )


class CKCDatabase:
    """
    CKC Database connection manager.

    Provides async connection pooling with automatic cleanup.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self._pool: Optional[Pool] = None
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """
        Initialize the database connection pool.

        Returns:
            bool: True if initialization succeeded
        """
        if not HAS_ASYNCPG:
            logger.error("asyncpg not installed. Run: pip install asyncpg")
            return False

        async with self._lock:
            if self._initialized:
                return True

            try:
                self._pool = await asyncpg.create_pool(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.user,
                    password=self.config.password,
                    min_size=self.config.min_pool_size,
                    max_size=self.config.max_pool_size,
                    max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                    command_timeout=self.config.command_timeout,
                )

                # Verify connection
                async with self._pool.acquire() as conn:
                    version = await conn.fetchval("SELECT version()")
                    logger.info(f"CKC Database connected: {version[:50]}...")

                self._initialized = True
                return True

            except Exception as e:
                logger.error(f"Failed to initialize CKC database: {e}")
                return False

    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False
            logger.info("CKC Database connection closed")

    @property
    def pool(self) -> Optional[Pool]:
        """Get the connection pool."""
        return self._pool

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._initialized and self._pool is not None

    async def ensure_connected(self) -> None:
        """Ensure database is connected, initialize if needed."""
        if not self.is_connected:
            success = await self.initialize()
            if not success:
                raise ConnectionError("Could not connect to CKC database")

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Connection, None]:
        """
        Acquire a connection from the pool.

        Usage:
            async with db.acquire() as conn:
                result = await conn.fetch("SELECT * FROM ckc.task_contexts")
        """
        await self.ensure_connected()
        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Connection, None]:
        """
        Acquire a connection with transaction.

        Usage:
            async with db.transaction() as conn:
                await conn.execute("INSERT INTO ckc.task_contexts ...")
                await conn.execute("INSERT INTO ckc.workflow_steps ...")
                # Auto-commits on success, rolls back on exception
        """
        await self.ensure_connected()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """Execute a query and return status."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> List[asyncpg.Record]:
        """Execute a query and return all rows."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)

    async def fetchrow(self, query: str, *args, timeout: Optional[float] = None) -> Optional[asyncpg.Record]:
        """Execute a query and return a single row."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)

    async def fetchval(self, query: str, *args, column: int = 0, timeout: Optional[float] = None) -> Any:
        """Execute a query and return a single value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database.

        Returns:
            Dict with health status information
        """
        if not self.is_connected:
            return {
                "status": "disconnected",
                "error": "Database not initialized"
            }

        try:
            async with self.acquire() as conn:
                start = datetime.now()
                await conn.fetchval("SELECT 1")
                latency_ms = (datetime.now() - start).total_seconds() * 1000

                # Get pool stats
                pool_size = self._pool.get_size()
                pool_free = self._pool.get_idle_size()

                return {
                    "status": "healthy",
                    "latency_ms": round(latency_ms, 2),
                    "pool_size": pool_size,
                    "pool_free": pool_free,
                    "pool_in_use": pool_size - pool_free,
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def get_schema_version(self) -> Optional[int]:
        """Get the current schema version."""
        try:
            async with self.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT version FROM ckc.schema_version ORDER BY version DESC LIMIT 1"
                )
                return result
        except Exception:
            return None

    async def table_exists(self, table_name: str, schema: str = "ckc") -> bool:
        """Check if a table exists."""
        async with self.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = $1 AND table_name = $2
                )
                """,
                schema, table_name
            )
            return result


# Singleton instance
_database: Optional[CKCDatabase] = None
_database_lock = asyncio.Lock()


async def get_database(config: Optional[DatabaseConfig] = None) -> CKCDatabase:
    """
    Get the singleton database instance.

    Args:
        config: Optional database configuration

    Returns:
        CKCDatabase instance
    """
    global _database

    async with _database_lock:
        if _database is None:
            _database = CKCDatabase(config)
            await _database.initialize()

        return _database


async def close_database() -> None:
    """Close the singleton database instance."""
    global _database

    async with _database_lock:
        if _database is not None:
            await _database.close()
            _database = None
