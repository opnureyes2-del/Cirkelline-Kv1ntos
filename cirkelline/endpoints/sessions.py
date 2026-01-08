"""
Session Management Endpoints
=============================
Handles session listing, state retrieval, and date filtering.
"""

import os
import math
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# SESSION STATE ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/sessions/{session_id}/state")
async def get_session_state(
    request: Request,
    session_id: str
):
    """
    Get current session state including deep_research flag.

    v1.2.24: Returns deep_research toggle state for frontend to restore UI.
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized"}
            )

        # ✅ v1.2.26 FIX: get_sessions() doesn't accept session_id parameter
        # Must filter manually after retrieving all sessions
        all_sessions_tuple = db.get_sessions(user_id=user_id, deserialize=False)
        all_sessions = all_sessions_tuple[0] if isinstance(all_sessions_tuple, tuple) else all_sessions_tuple
        matching_sessions = [s for s in all_sessions if s.get('session_id') == session_id]

        if not matching_sessions or len(matching_sessions) == 0:
            return JSONResponse(
                status_code=404,
                content={"error": "Session not found"}
            )

        session_data = matching_sessions[0]

        # Extract session_state from session_data
        deep_research = False
        if 'session_data' in session_data and session_data['session_data']:
            session_state = session_data['session_data'].get("session_state", {})
            deep_research = session_state.get("deep_research", False)

        logger.info(f"📊 Retrieved session state for {session_id}: deep_research={deep_research}")

        return JSONResponse(
            status_code=200,
            content={
                "session_id": session_id,
                "deep_research": deep_research
            }
        )

    except Exception as e:
        logger.error(f"❌ Error retrieving session state: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# ═══════════════════════════════════════════════════════════════
# SESSIONS LIST ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/sessions")
async def list_sessions(
    request: Request,
    type: Optional[str] = None,
    component_id: Optional[str] = None,
    db_id: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    session_name: Optional[str] = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    created_after: Optional[int] = None,  # Unix timestamp
    created_before: Optional[int] = None,  # Unix timestamp
):
    """
    Custom sessions endpoint with date filtering support.
    Intercepts AGNO's built-in /sessions endpoint to add created_after/created_before filters.
    """
    try:
        # Get user_id from JWT middleware
        jwt_user_id = getattr(request.state, 'user_id', None)
        user_id_filter = user_id or jwt_user_id

        if not user_id_filter:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized"}
            )

        # Database connection
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        engine = create_engine(database_url)

        with Session(engine) as session:
            # Build query
            query = """
                SELECT
                    session_id,
                    created_at,
                    updated_at,
                    session_data->>'session_name' as session_name
                FROM ai.agno_sessions
                WHERE user_id = :user_id
            """
            params = {"user_id": user_id_filter}

            # Add date filters
            if created_after is not None:
                query += " AND created_at >= :created_after"
                params["created_after"] = created_after
                logger.info(f"📅 Filtering sessions: created_after={created_after}")

            if created_before is not None:
                query += " AND created_at <= :created_before"
                params["created_before"] = created_before
                logger.info(f"📅 Filtering sessions: created_before={created_before}")

            # Add search filter
            if session_name:
                query += " AND session_name ILIKE :session_name"
                params["session_name"] = f"%{session_name}%"

            # Add sorting
            if sort_by in ["created_at", "updated_at", "session_name"]:
                order = "ASC" if sort_order.lower() == "asc" else "DESC"
                query += f" ORDER BY {sort_by} {order}"

            # Count total
            count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
            total_count = session.execute(text(count_query), params).scalar()

            # Add pagination
            offset = (page - 1) * limit
            query += f" LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            # Execute query
            result = session.execute(text(query), params)
            sessions = [
                {
                    "session_id": row[0],
                    "created_at": row[1],
                    "updated_at": row[2],
                    "session_name": row[3] if len(row) > 3 else None
                }
                for row in result
            ]

            total_pages = math.ceil(total_count / limit)

            return {
                "data": sessions,
                "meta": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": total_pages
                }
            }

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to list sessions: {str(e)}"}
        )


logger.info("✅ Session management endpoints loaded")
