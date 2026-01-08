"""
User Journals Endpoints
========================
Handles fetching journal entries for the current user.
"""

import os
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db

# Create router
router = APIRouter()


@router.get("/api/journals")
async def get_user_journals(
    request: Request,
    limit: int = 7,
    page: int = 1
):
    """
    Get journal entries for the current user.

    Returns the user's journal entries, sorted by date descending.
    Default limit is 7 (for sidebar display).
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized"}
            )

        # Database connection
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

        engine = create_engine(db_url)

        with Session(engine) as session:
            # Get total count
            count_query = """
                SELECT COUNT(*) FROM ai.user_journals
                WHERE user_id = :user_id
            """
            count_result = session.execute(text(count_query), {"user_id": user_id})
            total = count_result.fetchone()[0]

            # Get journal entries
            query = """
                SELECT
                    id,
                    journal_date,
                    summary,
                    topics,
                    outcomes,
                    message_count,
                    created_at
                FROM ai.user_journals
                WHERE user_id = :user_id
                ORDER BY journal_date DESC
                LIMIT :limit OFFSET :offset
            """

            offset = (page - 1) * limit
            result = session.execute(text(query), {
                "user_id": user_id,
                "limit": limit,
                "offset": offset
            })
            rows = result.fetchall()

            journals = []
            for row in rows:
                # Handle journal_date (date type) and created_at (unix timestamp)
                journal_date = row[1].isoformat() if hasattr(row[1], 'isoformat') else str(row[1]) if row[1] else None
                created_at = row[6] if isinstance(row[6], (int, float)) else (row[6].isoformat() if row[6] else None)

                journals.append({
                    "id": row[0],
                    "journal_date": journal_date,
                    "summary": row[2],
                    "topics": row[3] if row[3] else [],
                    "outcomes": row[4] if row[4] else [],
                    "message_count": row[5] or 0,
                    "created_at": created_at
                })

            logger.info(f"📔 Retrieved {len(journals)} journals for user {user_id[:8]}...")

            return {
                "success": True,
                "journals": journals,
                "total": total,
                "page": page,
                "limit": limit,
                "has_more": total > (page * limit)
            }

    except Exception as e:
        logger.error(f"❌ Error fetching user journals: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/api/journals/{journal_id}")
async def get_journal_detail(
    request: Request,
    journal_id: int
):
    """
    Get a specific journal entry by ID.
    Only returns the journal if it belongs to the current user.
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized"}
            )

        # Database connection
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")

        engine = create_engine(db_url)

        with Session(engine) as session:
            # Get the journal entry (only if it belongs to this user)
            query = """
                SELECT
                    id,
                    journal_date,
                    summary,
                    topics,
                    outcomes,
                    sessions_processed,
                    message_count,
                    created_at
                FROM ai.user_journals
                WHERE id = :journal_id AND user_id = :user_id
            """

            result = session.execute(text(query), {
                "journal_id": journal_id,
                "user_id": user_id
            })
            row = result.fetchone()

            if not row:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Journal not found"}
                )

            # Handle journal_date (date type) and created_at (unix timestamp)
            journal_date = row[1].isoformat() if hasattr(row[1], 'isoformat') else str(row[1]) if row[1] else None
            created_at = row[7] if isinstance(row[7], (int, float)) else (row[7].isoformat() if row[7] else None)

            journal = {
                "id": row[0],
                "journal_date": journal_date,
                "summary": row[2],
                "topics": row[3] if row[3] else [],
                "outcomes": row[4] if row[4] else [],
                "sessions_processed": row[5] if row[5] else [],
                "message_count": row[6] or 0,
                "created_at": created_at
            }

            return {
                "success": True,
                "journal": journal
            }

    except Exception as e:
        logger.error(f"❌ Error fetching journal detail: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


logger.info("✅ User journals endpoints loaded")
