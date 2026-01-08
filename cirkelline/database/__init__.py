"""
Cirkelline Database Module
==========================

Database infrastructure for scalability:
- Read/Write splitting
- Connection pooling
- Replica support
- Health monitoring

Princip: "Man behøver ikke se for at vide - vi bygger så alt er gennemsigtigt."
"""

import os
from agno.db.postgres import PostgresDb
from agno.vectordb.pgvector import PgVector, SearchType
from agno.knowledge.embedder.google import GeminiEmbedder
from sqlalchemy import create_engine

# Legacy exports (backwards compatibility)
db = PostgresDb(
    db_url=os.getenv("DATABASE_URL", "postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline"),
    session_table="agno_sessions",
    memory_table="agno_memories"
)

vector_db = PgVector(
    db_url=os.getenv("DATABASE_URL", "postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline"),
    table_name="cirkelline_knowledge_vectors",
    embedder=GeminiEmbedder(),
    search_type=SearchType.hybrid
)

# Shared SQLAlchemy engine for activity logging
_shared_engine = create_engine(
    db.db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

from cirkelline.database.read_write_router import (
    # Enums
    RouteMode,

    # Config
    DatabaseNode,
    RouterConfig,

    # Metrics
    RouterMetrics,

    # Main class
    DatabaseRouter,

    # Global access
    get_database_router,
    init_database_router,
    close_database_router,
)

__all__ = [
    # Legacy exports
    "db",
    "vector_db",
    "_shared_engine",

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

__version__ = "1.0.0"
