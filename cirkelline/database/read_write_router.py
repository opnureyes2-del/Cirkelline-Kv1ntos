"""
Database Read/Write Router
===========================

Intelligent routing af database queries til primary (write) eller
replicas (read) for skalerbarhed op til 1M+ brugere.

Arkitektur:
    ┌─────────────────────────────────────────┐
    │          DatabaseRouter                  │
    ├─────────────────────────────────────────┤
    │  get_read_session()  → Random Replica   │
    │  get_write_session() → Primary          │
    │  get_session(mode)   → Auto-routing     │
    └─────────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ Primary │  │Replica 1│  │Replica 2│
    │ (WRITE) │  │ (READ)  │  │ (READ)  │
    └─────────┘  └─────────┘  └─────────┘

Princip: "Man behøver ikke se for at vide - vi bygger så alt er gennemsigtigt."
"""

from __future__ import annotations

import os
import random
import logging
import asyncio
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class RouteMode(Enum):
    """Query routing mode."""
    READ = "read"
    WRITE = "write"
    AUTO = "auto"  # For future smart routing


@dataclass
class DatabaseNode:
    """Configuration for a database node."""
    name: str
    host: str
    port: int
    database: str
    user: str
    password: str
    is_primary: bool = False
    is_replica: bool = False
    weight: int = 1  # For weighted load balancing
    max_connections: int = 50

    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string."""
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def __repr__(self) -> str:
        role = "PRIMARY" if self.is_primary else "REPLICA"
        return f"<DatabaseNode {self.name} ({role}) @ {self.host}:{self.port}>"


@dataclass
class RouterConfig:
    """Database router configuration."""
    primary: DatabaseNode
    replicas: List[DatabaseNode] = field(default_factory=list)

    # Connection pool settings
    pool_size: int = 20
    max_overflow: int = 40
    pool_recycle: int = 1800  # 30 minutes
    pool_pre_ping: bool = True

    # Routing settings
    read_from_primary_on_empty: bool = True  # Fallback to primary if no replicas
    sticky_session_seconds: int = 0  # 0 = disabled

    @classmethod
    def from_env(cls) -> "RouterConfig":
        """Create config from environment variables."""
        # Primary database
        primary = DatabaseNode(
            name="primary",
            host=os.getenv("DB_PRIMARY_HOST", "localhost"),
            port=int(os.getenv("DB_PRIMARY_PORT", "5532")),
            database=os.getenv("DB_NAME", "cirkelline"),
            user=os.getenv("DB_USER", "cirkelline"),
            password=os.getenv("DB_PASSWORD", "cirkelline123"),
            is_primary=True,
        )

        # Read replicas (comma-separated hosts)
        replica_hosts = os.getenv("DB_REPLICA_HOSTS", "").split(",")
        replica_port = int(os.getenv("DB_REPLICA_PORT", "5432"))

        replicas = []
        for i, host in enumerate(replica_hosts):
            host = host.strip()
            if host:
                replicas.append(DatabaseNode(
                    name=f"replica-{i+1}",
                    host=host,
                    port=replica_port,
                    database=primary.database,
                    user=primary.user,
                    password=primary.password,
                    is_replica=True,
                ))

        return cls(primary=primary, replicas=replicas)

    @classmethod
    def localhost_single(cls) -> "RouterConfig":
        """Create localhost single-node config (development)."""
        return cls(
            primary=DatabaseNode(
                name="localhost-primary",
                host="localhost",
                port=5532,
                database="cirkelline",
                user="cirkelline",
                password="cirkelline123",
                is_primary=True,
            ),
            replicas=[],  # No replicas in dev
        )


# =============================================================================
# METRICS
# =============================================================================

@dataclass
class RouterMetrics:
    """Router performance metrics."""
    read_queries: int = 0
    write_queries: int = 0
    primary_reads: int = 0  # Reads that went to primary (no replicas)
    replica_reads: int = 0
    failovers: int = 0
    errors: int = 0
    avg_read_latency_ms: float = 0.0
    avg_write_latency_ms: float = 0.0
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "read_queries": self.read_queries,
            "write_queries": self.write_queries,
            "primary_reads": self.primary_reads,
            "replica_reads": self.replica_reads,
            "failovers": self.failovers,
            "errors": self.errors,
            "avg_read_latency_ms": round(self.avg_read_latency_ms, 2),
            "avg_write_latency_ms": round(self.avg_write_latency_ms, 2),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


# =============================================================================
# DATABASE ROUTER
# =============================================================================

class DatabaseRouter:
    """
    Intelligent database router for read/write splitting.

    Features:
    - Automatic routing to primary (writes) or replicas (reads)
    - Weighted round-robin for replica selection
    - Automatic failover to primary if replicas unavailable
    - Connection pooling per node
    - Metrics tracking

    Usage:
        router = DatabaseRouter(RouterConfig.from_env())
        await router.initialize()

        # For reads (goes to replica)
        async with router.read_session() as session:
            result = session.execute(select(User))

        # For writes (goes to primary)
        async with router.write_session() as session:
            session.add(new_user)
            session.commit()
    """

    def __init__(self, config: Optional[RouterConfig] = None):
        self.config = config or RouterConfig.localhost_single()
        self._primary_engine: Optional[Engine] = None
        self._replica_engines: List[Engine] = []
        self._replica_weights: List[int] = []
        self._initialized = False
        self._metrics = RouterMetrics()
        self._lock = asyncio.Lock()

    # =========================================================================
    # INITIALIZATION
    # =========================================================================

    async def initialize(self) -> None:
        """Initialize database connections."""
        if self._initialized:
            return

        async with self._lock:
            # Create primary engine
            self._primary_engine = self._create_engine(self.config.primary)
            logger.info(f"Primary database connected: {self.config.primary}")

            # Create replica engines
            for replica in self.config.replicas:
                try:
                    engine = self._create_engine(replica)
                    self._replica_engines.append(engine)
                    self._replica_weights.append(replica.weight)
                    logger.info(f"Replica connected: {replica}")
                except Exception as e:
                    logger.error(f"Failed to connect replica {replica}: {e}")

            self._initialized = True

            replica_count = len(self._replica_engines)
            logger.info(
                f"DatabaseRouter initialized: 1 primary, {replica_count} replicas"
            )

    def _create_engine(self, node: DatabaseNode) -> Engine:
        """Create SQLAlchemy engine for a node."""
        return create_engine(
            node.connection_string,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=self.config.pool_pre_ping,
            echo=False,
        )

    async def close(self) -> None:
        """Close all connections."""
        if self._primary_engine:
            self._primary_engine.dispose()

        for engine in self._replica_engines:
            engine.dispose()

        self._initialized = False
        logger.info("DatabaseRouter closed")

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    def _get_primary_session(self) -> Session:
        """Get session from primary database."""
        if not self._primary_engine:
            raise RuntimeError("Router not initialized")

        SessionLocal = sessionmaker(bind=self._primary_engine)
        return SessionLocal()

    def _get_replica_session(self) -> Session:
        """Get session from a replica (weighted random selection)."""
        if not self._replica_engines:
            if self.config.read_from_primary_on_empty:
                self._metrics.primary_reads += 1
                return self._get_primary_session()
            raise RuntimeError("No replicas available")

        # Weighted random selection
        engine = random.choices(
            self._replica_engines,
            weights=self._replica_weights,
            k=1
        )[0]

        self._metrics.replica_reads += 1
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()

    @asynccontextmanager
    async def read_session(self):
        """
        Context manager for read operations.
        Routes to replica if available, falls back to primary.
        """
        if not self._initialized:
            await self.initialize()

        session = self._get_replica_session()
        self._metrics.read_queries += 1

        try:
            yield session
        except Exception as e:
            self._metrics.errors += 1
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def write_session(self):
        """
        Context manager for write operations.
        Always routes to primary.
        """
        if not self._initialized:
            await self.initialize()

        session = self._get_primary_session()
        self._metrics.write_queries += 1

        try:
            yield session
        except Exception as e:
            self._metrics.errors += 1
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def session(self, mode: RouteMode = RouteMode.READ):
        """
        Generic session context manager with mode selection.

        Args:
            mode: READ for replicas, WRITE for primary
        """
        if mode == RouteMode.WRITE:
            async with self.write_session() as session:
                yield session
        else:
            async with self.read_session() as session:
                yield session

    # =========================================================================
    # HEALTH & METRICS
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all database nodes."""
        results = {"primary": False, "replicas": []}

        # Check primary
        try:
            with self._get_primary_session() as session:
                session.execute(text("SELECT 1"))
                results["primary"] = True
        except Exception as e:
            logger.error(f"Primary health check failed: {e}")

        # Check replicas
        for i, engine in enumerate(self._replica_engines):
            try:
                SessionLocal = sessionmaker(bind=engine)
                with SessionLocal() as session:
                    session.execute(text("SELECT 1"))
                    results["replicas"].append({"id": i, "healthy": True})
            except Exception as e:
                logger.error(f"Replica {i} health check failed: {e}")
                results["replicas"].append({"id": i, "healthy": False})

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Get router metrics."""
        self._metrics.last_updated = datetime.now()
        return {
            **self._metrics.to_dict(),
            "config": {
                "primary": str(self.config.primary),
                "replica_count": len(self.config.replicas),
                "pool_size": self.config.pool_size,
            },
            "status": {
                "initialized": self._initialized,
                "active_replicas": len(self._replica_engines),
            },
        }

    @property
    def has_replicas(self) -> bool:
        """Check if replicas are available."""
        return len(self._replica_engines) > 0


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_router: Optional[DatabaseRouter] = None


def get_database_router() -> DatabaseRouter:
    """Get or create global DatabaseRouter instance."""
    global _router
    if _router is None:
        _router = DatabaseRouter(RouterConfig.from_env())
    return _router


async def init_database_router() -> DatabaseRouter:
    """Initialize global database router."""
    router = get_database_router()
    await router.initialize()
    return router


async def close_database_router() -> None:
    """Close global database router."""
    global _router
    if _router:
        await _router.close()
        _router = None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RouteMode",

    # Config
    "DatabaseNode",
    "RouterConfig",

    # Metrics
    "RouterMetrics",

    # Main class
    "DatabaseRouter",

    # Global access
    "get_database_router",
    "init_database_router",
    "close_database_router",
]


logger.info("✅ Read/Write Router module loaded")
