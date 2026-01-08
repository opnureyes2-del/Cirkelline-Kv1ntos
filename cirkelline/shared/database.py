"""
Database Utilities
==================
Helper functions for database session management.
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from cirkelline.database import db
from cirkelline.config import logger


def get_db_engine():
    """
    Get SQLAlchemy engine for database operations.
    
    Returns:
        SQLAlchemy Engine instance
    """
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    return create_engine(db_url)


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    
    Yields:
        SQLAlchemy Session instance
    
    Example:
        with get_db_session() as session:
            result = session.execute(...)
            session.commit()
    """
    engine = get_db_engine()
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


logger.info("✅ Database utilities module loaded")
