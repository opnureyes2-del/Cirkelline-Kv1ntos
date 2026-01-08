"""
Admin User Management Endpoints
================================
Handles admin-only user management operations.

Provides:
- GET /api/admin/users - List all users with pagination and filters
- GET /api/admin/users/{user_id} - Get detailed user information
"""

import os
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Request, HTTPException, Query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db
from cirkelline.middleware.middleware import log_activity

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# USER MANAGEMENT LIST ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/users")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    status_filter: str = Query("all")  # all, online, offline, admin
):
    """
    List all users with pagination and filters (admin only).

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - search: Email search filter
    - status_filter: Filter by status (all/online/offline/admin)

    Returns:
    - data: List of users with details
    - total: Total count of users matching filters
    - page: Current page
    - limit: Items per page
    - stats: Overall statistics
    """
    try:
        # Extract and decode JWT token manually (like feedback endpoint)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")

        token = auth_header[7:]
        try:
            payload = pyjwt.decode(
                token,
                os.getenv("JWT_SECRET_KEY"),
                algorithms=["HS256"]
            )
            user_id = payload.get("user_id")
        except Exception as e:
            logger.error(f"JWT decode error in list_users: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        if not user_id or user_id.startswith("anon-"):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Use synchronous session like feedback endpoints
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            # Check if user is admin
            admin_check = session.execute(
                text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id LIMIT 1"),
                {"user_id": user_id}
            )
            is_admin = admin_check.fetchone() is not None

            if not is_admin:
                raise HTTPException(status_code=403, detail="Admin access required")

            # Build base query
            base_query = """
                SELECT
                    u.id,
                    u.email,
                    u.display_name,
                    u.created_at,
                    u.updated_at,
                    u.last_login,
                    u.preferences,
                    CASE WHEN ap.user_id IS NOT NULL THEN true ELSE false END as is_admin,
                    ap.name as admin_name,
                    ap.role as admin_role
                FROM users u
                LEFT JOIN admin_profiles ap ON u.id = ap.user_id
                WHERE 1=1
            """

            count_query = """
                SELECT COUNT(*) as total
                FROM users u
                LEFT JOIN admin_profiles ap ON u.id = ap.user_id
                WHERE 1=1
            """

            params = {}

            # Apply search filter
            if search:
                search_clause = " AND u.email ILIKE :search"
                base_query += search_clause
                count_query += search_clause
                params["search"] = f"%{search}%"

            # Apply status filter
            if status_filter == "online":
                # Consider users who logged in within last 15 minutes as "online"
                online_clause = " AND u.last_login > NOW() - INTERVAL '15 minutes'"
                base_query += online_clause
                count_query += online_clause
            elif status_filter == "offline":
                offline_clause = " AND (u.last_login IS NULL OR u.last_login <= NOW() - INTERVAL '15 minutes')"
                base_query += offline_clause
                count_query += offline_clause
            elif status_filter == "admin":
                admin_clause = " AND ap.user_id IS NOT NULL"
                base_query += admin_clause
                count_query += admin_clause

            # Get total count
            count_result = session.execute(text(count_query), params)
            total = count_result.fetchone()[0]

            # Add ordering and pagination
            base_query += " ORDER BY u.created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = (page - 1) * limit

            # Execute main query
            result = session.execute(text(base_query), params)
            rows = result.fetchall()

            # Get overall stats
            stats_query = """
                SELECT
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN u.last_login > NOW() - INTERVAL '15 minutes' THEN 1 END) as online_users,
                    COUNT(CASE WHEN ap.user_id IS NOT NULL THEN 1 END) as admin_users,
                    COUNT(CASE WHEN u.created_at > NOW() - INTERVAL '7 days' THEN 1 END) as new_users_week
                FROM users u
                LEFT JOIN admin_profiles ap ON u.id = ap.user_id
            """
            stats_result = session.execute(text(stats_query))
            stats_row = stats_result.fetchone()

            # Format results
            users = []
            for row in rows:
                # Determine online status
                is_online = False
                if row.last_login:
                    fifteen_min_ago = datetime.now(timezone.utc) - timedelta(minutes=15)
                    # Convert row.last_login to timezone-aware datetime
                    if row.last_login.tzinfo is None:
                        last_login_aware = row.last_login.replace(tzinfo=timezone.utc)
                    else:
                        last_login_aware = row.last_login
                    is_online = last_login_aware > fifteen_min_ago

                user_data = {
                    "id": str(row.id),
                    "email": row.email,
                    "display_name": row.display_name,
                    "is_admin": row.is_admin,
                    "admin_name": row.admin_name,
                    "admin_role": row.admin_role,
                    "is_online": is_online,
                    "created_at": int(row.created_at.timestamp()) if row.created_at else None,
                    "updated_at": int(row.updated_at.timestamp()) if row.updated_at else None,
                    "last_login": int(row.last_login.timestamp()) if row.last_login else None,
                    "preferences": row.preferences or {}
                }
                users.append(user_data)

            # Log successful users list
            await log_activity(
                request=request,
                user_id=user_id,
                action_type="admin_list_users",
                success=True,
                status_code=200,
                details={"total": total, "page": page, "limit": limit},
                is_admin=True
            )

            return {
                "success": True,
                "data": users,
                "total": total,
                "page": page,
                "limit": limit,
                "stats": {
                    "total_users": stats_row[0],
                    "online_users": stats_row[1],
                    "admin_users": stats_row[2],
                    "new_users_week": stats_row[3]
                }
            }

    except HTTPException as he:
        # Log failed list
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="admin_list_users",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException",
            is_admin=is_admin if 'is_admin' in locals() else False
        )
        raise
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="admin_list_users",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            is_admin=is_admin if 'is_admin' in locals() else False
        )

        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")

logger.info("✅ User management list endpoint configured")

# ═══════════════════════════════════════════════════════════════
# USER MANAGEMENT DETAILS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/users/{user_id}")
async def get_user_details(user_id: str, request: Request):
    """
    Get detailed information about a specific user (admin only).

    Returns:
    - User profile data
    - Admin profile data (if applicable)
    - Account statistics (sessions count, memories count, etc.)
    """
    try:
        # Extract and decode JWT token manually (like feedback endpoint)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")

        token = auth_header[7:]
        try:
            payload = pyjwt.decode(
                token,
                os.getenv("JWT_SECRET_KEY"),
                algorithms=["HS256"]
            )
            requesting_user_id = payload.get("user_id")
        except Exception as e:
            logger.error(f"JWT decode error in get_user_details: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        if not requesting_user_id or requesting_user_id.startswith("anon-"):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Use synchronous session
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            # Check if requesting user is admin
            admin_check = session.execute(
                text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id LIMIT 1"),
                {"user_id": requesting_user_id}
            )
            is_admin = admin_check.fetchone() is not None

            if not is_admin:
                raise HTTPException(status_code=403, detail="Admin access required")

            # Get user details (cast user_id to UUID for type safety)
            user_query = """
                SELECT
                    u.id,
                    u.email,
                    u.display_name,
                    u.created_at,
                    u.updated_at,
                    u.last_login,
                    u.preferences,
                    ap.name as admin_name,
                    ap.role as admin_role,
                    ap.personal_context,
                    ap.preferences as admin_preferences,
                    ap.custom_instructions
                FROM users u
                LEFT JOIN admin_profiles ap ON u.id = ap.user_id
                WHERE u.id = CAST(:user_id AS uuid)
            """

            result = session.execute(text(user_query), {"user_id": user_id})
            user_row = result.fetchone()

            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")

            # Get statistics (no casting needed - user_id is VARCHAR in all tables)
            stats_query = """
                SELECT
                    (SELECT COUNT(*) FROM ai.agno_sessions WHERE user_id = :user_id) as session_count,
                    (SELECT COUNT(*) FROM ai.agno_memories WHERE user_id = :user_id) as memory_count,
                    (SELECT COUNT(*) FROM feedback_submissions WHERE user_id = CAST(:user_id AS uuid)) as feedback_count
            """

            stats_result = session.execute(text(stats_query), {"user_id": user_id})
            stats_row = stats_result.fetchone()

            # Get recent sessions (last 10)
            recent_sessions_query = """
                SELECT session_id, created_at, updated_at
                FROM ai.agno_sessions
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 10
            """
            sessions_result = session.execute(text(recent_sessions_query), {"user_id": user_id})
            recent_sessions = [
                {
                    "session_id": row[0],
                    "created_at": row[1],
                    "updated_at": row[2]
                }
                for row in sessions_result.fetchall()
            ]

            # Get recent memories (last 10)
            recent_memories_query = """
                SELECT memory, updated_at
                FROM ai.agno_memories
                WHERE user_id = :user_id
                ORDER BY updated_at DESC
                LIMIT 10
            """
            memories_result = session.execute(text(recent_memories_query), {"user_id": user_id})
            recent_memories = [
                {
                    "memory": row[0],
                    "updated_at": row[1]
                }
                for row in memories_result.fetchall()
            ]

            # Get recent feedback (last 10)
            recent_feedback_query = """
                SELECT id, feedback_type, message_content, user_comments, status, created_at
                FROM feedback_submissions
                WHERE user_id = CAST(:user_id AS uuid)
                ORDER BY created_at DESC
                LIMIT 10
            """
            feedback_result = session.execute(text(recent_feedback_query), {"user_id": user_id})
            recent_feedback = [
                {
                    "id": str(row[0]),
                    "feedback_type": row[1],
                    "message_content": row[2][:100] + "..." if len(row[2]) > 100 else row[2],  # Truncate long messages
                    "user_comments": row[3],
                    "status": row[4],
                    "created_at": int(row[5].timestamp()) if row[5] else None
                }
                for row in feedback_result.fetchall()
            ]

            # Format response
            is_online = False
            if user_row.last_login:
                fifteen_min_ago = datetime.now(timezone.utc) - timedelta(minutes=15)
                if user_row.last_login.tzinfo is None:
                    last_login_aware = user_row.last_login.replace(tzinfo=timezone.utc)
                else:
                    last_login_aware = user_row.last_login
                is_online = last_login_aware > fifteen_min_ago

            # Calculate account age
            account_age_days = 0
            if user_row.created_at:
                now = datetime.now(timezone.utc)
                if user_row.created_at.tzinfo is None:
                    created_aware = user_row.created_at.replace(tzinfo=timezone.utc)
                else:
                    created_aware = user_row.created_at
                account_age_days = (now - created_aware).days

            user_data = {
                "id": str(user_row.id),
                "email": user_row.email,
                "display_name": user_row.display_name,
                "is_admin": user_row.admin_name is not None,
                "is_online": is_online,
                "created_at": int(user_row.created_at.timestamp()) if user_row.created_at else None,
                "updated_at": int(user_row.updated_at.timestamp()) if user_row.updated_at else None,
                "last_login": int(user_row.last_login.timestamp()) if user_row.last_login else None,
                "account_age_days": account_age_days,
                "preferences": user_row.preferences or {},
                "admin_profile": {
                    "name": user_row.admin_name,
                    "role": user_row.admin_role,
                    "personal_context": user_row.personal_context,
                    "preferences": user_row.admin_preferences,
                    "custom_instructions": user_row.custom_instructions
                } if user_row.admin_name else None,
                "statistics": {
                    "session_count": stats_row[0],
                    "memory_count": stats_row[1],
                    "feedback_count": stats_row[2]
                },
                "recent_sessions": recent_sessions,
                "recent_memories": recent_memories,
                "recent_feedback": recent_feedback
            }

            # Log successful user view
            await log_activity(
                request=request,
                user_id=requesting_user_id,
                action_type="admin_view_user",
                success=True,
                status_code=200,
                target_user_id=user_id,
                details={"viewed_user_email": user_row.email},
                is_admin=True
            )

            return {
                "success": True,
                "data": user_data
            }

    except HTTPException as he:
        # Log failed view
        await log_activity(
            request=request,
            user_id=requesting_user_id if 'requesting_user_id' in locals() else "unknown",
            action_type="admin_view_user",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException",
            target_user_id=user_id,
            is_admin=is_admin if 'is_admin' in locals() else False
        )
        raise
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")

        # Log error
        await log_activity(
            request=request,
            user_id=requesting_user_id if 'requesting_user_id' in locals() else "unknown",
            action_type="admin_view_user",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            target_user_id=user_id,
            is_admin=is_admin if 'is_admin' in locals() else False
        )

        raise HTTPException(status_code=500, detail=f"Failed to get user details: {str(e)}")

logger.info("✅ User management details endpoint configured")
