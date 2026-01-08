"""initial_baseline_schema

Revision ID: 6d5c7fe4a665
Revises:
Create Date: 2025-12-12

This migration represents the baseline schema for Cirkelline.
It documents the existing database structure without making changes,
allowing future migrations to build upon it.

Existing tables (already created):
- public.users
- public.admin_profiles
- public.google_tokens
- public.notion_tokens
- public.notion_user_databases
- public.tiers
- public.user_feedback
- ai.agno_sessions
- ai.agno_memories
- ai.agno_knowledge
- ai.cirkelline_knowledge_vectors
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d5c7fe4a665'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Baseline migration - no changes needed.

    The database schema already exists. This migration serves as
    the starting point for version control. Run with:

        alembic stamp head

    To mark the current database state as migrated.
    """
    # Ensure 'ai' schema exists
    op.execute("CREATE SCHEMA IF NOT EXISTS ai")

    # Note: All tables already exist in production.
    # This migration documents the baseline state.
    # Future migrations will add changes incrementally.
    pass


def downgrade() -> None:
    """
    Cannot downgrade from baseline - this is the starting point.
    """
    raise NotImplementedError(
        "Cannot downgrade from baseline migration. "
        "This is the initial schema state."
    )
