"""
Admin Activity Logging Endpoints
==================================
Handles admin-only activity log viewing and real-time streaming.

Provides:
- GET /api/admin/activity - Get activity logs with filtering and pagination
- GET /api/admin/activity/stream - SSE stream for real-time activity updates
"""

import os
import json
import asyncio
import jwt as pyjwt
from typing import Set, Optional
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db
from cirkelline.middleware.middleware import log_activity

# Create router
router = APIRouter()

# Global set to track connected SSE clients for activity log streaming
activity_log_clients: Set[asyncio.Queue] = set()

# ═══════════════════════════════════════════════════════════════
# BROADCAST FUNCTION
# ═══════════════════════════════════════════════════════════════

async def broadcast_activity_log(log_data: dict):
    """Broadcast new activity log to all connected SSE clients"""
    if not activity_log_clients:
        return

    # Send to all connected clients
    disconnected = set()
    for client_queue in activity_log_clients:
        try:
            await asyncio.wait_for(client_queue.put(log_data), timeout=1.0)
        except (asyncio.TimeoutError, Exception):
            disconnected.add(client_queue)

    # Remove disconnected clients
    for client in disconnected:
        activity_log_clients.discard(client)

logger.info("✅ Activity log broadcasting function loaded")

# ═══════════════════════════════════════════════════════════════
# ACTIVITY LOGS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/activity")
async def get_activity_logs(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action_filter: Optional[str] = Query(None),
    success_filter: Optional[str] = Query(None),
    user_search: Optional[str] = Query(None),
    date_from: Optional[int] = Query(None),
    date_to: Optional[int] = Query(None),
    sort_by: str = Query("timestamp"),
    sort_order: str = Query("desc")
):
    """
    Get activity logs with filtering, pagination, and sorting.
    Admin-only endpoint.

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - action_filter: Filter by action type
    - success_filter: Filter by success/failure (success/failure)
    - user_search: Search by user email or user_id
    - date_from: Unix timestamp for start date
    - date_to: Unix timestamp for end date
    - sort_by: Sort column (timestamp/action_type/duration_ms/status_code)
    - sort_order: Sort direction (asc/desc)

    Returns:
    - data: List of activity logs
    - total: Total count matching filters
    - page: Current page
    - limit: Items per page
    - stats: Overall statistics
    """
    # JWT middleware extracts user_id
    user_id = getattr(request.state, 'user_id', None)

    if not user_id or user_id.startswith("anon-"):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Use synchronous session
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    # Check admin access
    try:
        with Session(engine) as session:
            admin_check = session.execute(
                text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id LIMIT 1"),
                {"user_id": user_id}
            )
            is_admin = admin_check.fetchone() is not None

        if not is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check admin status")

    try:
        # Build query with CAST for UUID to TEXT compatibility
        base_query = """
            SELECT
                al.id,
                al.timestamp,
                al.user_id,
                al.action_type,
                al.endpoint,
                al.http_method,
                al.status_code,
                al.success,
                al.error_message,
                al.error_type,
                al.target_user_id,
                al.target_resource_id,
                al.resource_type,
                al.details,
                al.duration_ms,
                al.ip_address,
                al.user_agent,
                al.is_admin,
                u.email as user_email,
                u.display_name as user_display_name
            FROM activity_logs al
            LEFT JOIN users u ON al.user_id = u.id::text
            WHERE 1=1
        """

        filters = []
        params = {}

        # Apply filters
        if action_filter:
            filters.append("al.action_type = :action_type")
            params["action_type"] = action_filter

        if success_filter:
            if success_filter.lower() == "success":
                filters.append("al.success = TRUE")
            elif success_filter.lower() == "failure":
                filters.append("al.success = FALSE")

        if user_search:
            filters.append("(u.email ILIKE :user_search OR al.user_id ILIKE :user_search)")
            params["user_search"] = f"%{user_search}%"

        if date_from:
            filters.append("al.timestamp >= to_timestamp(:date_from)")
            params["date_from"] = date_from

        if date_to:
            filters.append("al.timestamp <= to_timestamp(:date_to)")
            params["date_to"] = date_to

        # Add filters to query
        if filters:
            base_query += " AND " + " AND ".join(filters)

        # Add sorting
        sort_columns = {
            "timestamp": "al.timestamp",
            "action_type": "al.action_type",
            "duration_ms": "al.duration_ms",
            "status_code": "al.status_code"
        }
        sort_column = sort_columns.get(sort_by, "al.timestamp")
        sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"

        base_query += f" ORDER BY {sort_column} {sort_direction}"

        # Add pagination
        params["limit"] = limit
        params["offset"] = (page - 1) * limit
        base_query += " LIMIT :limit OFFSET :offset"

        # Count query
        count_query = """
            SELECT COUNT(*) FROM activity_logs al
            LEFT JOIN users u ON al.user_id = u.id::text
            WHERE 1=1
        """
        if filters:
            count_query += " AND " + " AND ".join(filters)

        # Execute queries
        with Session(engine) as session:
            # Get total count
            count_params = {k: v for k, v in params.items() if k not in ["limit", "offset"]}
            count_result = session.execute(text(count_query), count_params)
            total = count_result.scalar()

            # Get logs
            result = session.execute(text(base_query), params)
            rows = result.fetchall()

            logs = []
            for row in rows:
                log_dict = {
                    "id": str(row[0]),
                    "timestamp": int(row[1].timestamp()),
                    "user_id": row[2],
                    "action_type": row[3],
                    "endpoint": row[4],
                    "http_method": row[5],
                    "status_code": row[6],
                    "success": row[7],
                    "error_message": row[8],
                    "error_type": row[9],
                    "target_user_id": row[10],
                    "target_resource_id": row[11],
                    "resource_type": row[12],
                    "details": row[13],
                    "duration_ms": row[14],
                    "ip_address": str(row[15]) if row[15] else None,
                    "user_agent": row[16],
                    "is_admin": row[17],
                    "user_email": row[18],
                    "user_display_name": row[19]
                }
                logs.append(log_dict)

            # Get statistics
            stats_query = """
                SELECT
                    COUNT(*) as total_logs,
                    COUNT(CASE WHEN success = TRUE THEN 1 END) as successful_actions,
                    COUNT(CASE WHEN success = FALSE THEN 1 END) as failed_actions,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT action_type) as unique_action_types,
                    AVG(CASE WHEN duration_ms IS NOT NULL THEN duration_ms END) as avg_duration,
                    MAX(timestamp) as most_recent_activity,
                    COUNT(CASE WHEN is_admin = TRUE THEN 1 END) as admin_actions,
                    COUNT(CASE WHEN timestamp > NOW() - INTERVAL '24 hours' THEN 1 END) as logs_last_24h,
                    COUNT(CASE WHEN action_type = 'user_login' AND success = FALSE AND timestamp > NOW() - INTERVAL '1 hour' THEN 1 END) as failed_logins_last_hour
                FROM activity_logs
            """
            stats_result = session.execute(text(stats_query))
            stats_row = stats_result.fetchone()

            # Get action breakdown
            breakdown_query = """
                SELECT action_type, COUNT(*) as count
                FROM activity_logs
                GROUP BY action_type
                ORDER BY count DESC
            """
            breakdown_result = session.execute(text(breakdown_query))
            breakdown_rows = breakdown_result.fetchall()
            action_breakdown = [{"action": row[0], "count": row[1]} for row in breakdown_rows]

            stats = {
                "total_logs": stats_row[0] or 0,
                "successful_actions": stats_row[1] or 0,
                "failed_actions": stats_row[2] or 0,
                "unique_users": stats_row[3] or 0,
                "unique_action_types": stats_row[4] or 0,
                "avg_duration_ms": round(stats_row[5], 2) if stats_row[5] else 0,
                "most_recent_activity": int(stats_row[6].timestamp()) if stats_row[6] else 0,
                "admin_actions": stats_row[7] or 0,
                "logs_last_24h": stats_row[8] or 0,
                "failed_logins_last_hour": stats_row[9] or 0,
                "action_breakdown": action_breakdown
            }

        # Log admin viewing activity logs
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_view_activity_logs",
            success=True,
            status_code=200,
            details={
                "page": page,
                "limit": limit,
                "filters_applied": {
                    "action_filter": action_filter,
                    "success_filter": success_filter,
                    "user_search": user_search,
                    "date_from": date_from,
                    "date_to": date_to
                },
                "results_count": len(logs)
            },
            is_admin=True
        )

        return {
            "data": logs,  # Changed from "logs" to "data" to match frontend
            "total": total,
            "page": page,
            "limit": limit,
            "stats": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity logs: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("✅ Activity logs admin endpoint configured")

# ═══════════════════════════════════════════════════════════════
# ACTIVITY LOG SSE STREAM ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/activity/stream")
async def activity_log_stream(request: Request, token: str = Query(...)):
    """
    SSE endpoint for real-time activity log updates.
    Streams new activity logs to connected admin clients as they happen.

    Note: Token is passed as query param because EventSource doesn't support custom headers.

    Query Parameters:
    - token: JWT token for authentication (required)

    Returns: SSE stream with real-time activity logs
    """
    # Verify admin access
    try:
        payload = pyjwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"]
        )
        user_id = payload.get("user_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id or user_id.startswith("anon-"):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Use synchronous session
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    # Check if user is admin
    with Session(engine) as session:
        admin_check = session.execute(
            text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id LIMIT 1"),
            {"user_id": user_id}
        )
        is_admin = admin_check.fetchone() is not None

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Create queue for this client
    client_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    activity_log_clients.add(client_queue)

    async def event_generator():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"

            # Stream events to client
            while True:
                # Wait for new activity log
                log_data = await client_queue.get()

                # Send to client
                event_json = json.dumps({
                    'type': 'new_activity',
                    'data': log_data
                })
                yield f"data: {event_json}\n\n"

        except asyncio.CancelledError:
            # Client disconnected
            activity_log_clients.discard(client_queue)
            raise
        finally:
            # Cleanup
            activity_log_clients.discard(client_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

logger.info("✅ Activity logs SSE stream endpoint configured")
