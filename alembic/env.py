"""
Alembic Environment Configuration
=================================
Cirkelline Database Migrations

Supports:
- Loading DATABASE_URL from environment or .env
- Both online and offline migrations
- Schema versioning for ai.* and public.* schemas
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline"
)

# Set the sqlalchemy.url in config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# SQLAlchemy MetaData - we use raw SQL migrations for AGNO compatibility
# If you add SQLAlchemy ORM models later, import their Base.metadata here
target_metadata = None

# Schemas to include in migrations
SCHEMAS = ["public", "ai"]


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter which objects to include in autogenerate.

    Returns True to include, False to exclude.
    """
    # Include all tables from our schemas
    if type_ == "table":
        schema = getattr(object, 'schema', None) or 'public'
        return schema in SCHEMAS
    return True


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Useful for generating SQL scripts without database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    # Create engine directly with DATABASE_URL
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
