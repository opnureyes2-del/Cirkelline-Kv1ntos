"""
Cirkelline Database Module
===========================
Database connections: PostgreSQL and PgVector.
"""

import os
from agno.db.postgres import PostgresDb
from agno.vectordb.pgvector import PgVector, SearchType
from agno.knowledge.embedder.ollama import OllamaEmbedder
from sqlalchemy import create_engine
from cirkelline.config import logger

# Database connection
# Note: SQLAlchemy provides automatic connection pooling (pool_size=5, max_overflow=10)
# Uses DATABASE_URL from environment (Secrets Manager in production)
# AGNO v2 Best Practice: Explicitly specify table names for clarity
db = PostgresDb(
    db_url=os.getenv("DATABASE_URL", "postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline"),
    session_table="agno_sessions",  # Agent/Team sessions and runs
    memory_table="agno_memories"    # User memories
)

logger.info("Database connection configured with automatic pooling")

# Vector database with LOCAL Ollama embedder (nomic-embed-text, 768d)
# PERMANENT FIX: No more Gemini API rate limits
# Uses same DATABASE_URL as above
vector_db = PgVector(
    db_url=os.getenv("DATABASE_URL", "postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline"),
    table_name="cirkelline_knowledge_vectors",
    embedder=OllamaEmbedder(id="nomic-embed-text", dimensions=768),
    search_type=SearchType.hybrid  # Combines semantic + keyword search
)

logger.info("Vector DB connection configured with automatic pooling")

# Create shared SQLAlchemy engine for activity logging
_shared_engine = create_engine(
    db.db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    echo=False
)

logger.info("Shared database engine created for activity logging")

# Export engine for direct SQL access (used by standalone calendar, etc.)
engine = _shared_engine

logger.info("✅ Database module loaded")
