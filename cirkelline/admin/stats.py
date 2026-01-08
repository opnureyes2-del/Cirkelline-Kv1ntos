"""
Admin System Statistics Endpoint
==================================
Handles admin-only system statistics.

Provides:
- GET /api/admin/stats - Get comprehensive system statistics
- GET /api/admin/token-usage - Get detailed token usage and cost analytics
"""

import os
import jwt as pyjwt
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db
from cirkelline.middleware.middleware import log_activity

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# ADMIN SYSTEM STATISTICS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/stats")
async def get_admin_stats(request: Request):
    """
    Get overall system statistics (admin only).

    Returns:
    - User statistics
    - Session statistics
    - Feedback statistics
    - Recent activity
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
            logger.error(f"JWT decode error in get_admin_stats: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        if not user_id or user_id.startswith("anon-"):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Use synchronous session
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

            # Get comprehensive stats (using subqueries to avoid ambiguity)
            # ⚠️ TIMESTAMP WARNING: ai.agno_sessions.created_at is BIGINT (Unix seconds)
            # Must use EXTRACT(EPOCH FROM NOW()) to compare, NOT direct timestamp comparison
            stats_query = """
                SELECT
                    -- User stats (users.created_at is TIMESTAMP, can compare directly)
                    (SELECT COUNT(*) FROM users) as total_users,
                    (SELECT COUNT(*) FROM users WHERE users.last_login > NOW() - INTERVAL '15 minutes') as online_users,
                    (SELECT COUNT(*) FROM admin_profiles) as admin_users,
                    (SELECT COUNT(*) FROM users WHERE users.created_at > NOW() - INTERVAL '7 days') as new_users_week,
                    (SELECT COUNT(*) FROM users WHERE users.created_at > NOW() - INTERVAL '30 days') as new_users_month,

                    -- Session stats (ai.agno_sessions.created_at is BIGINT Unix seconds!)
                    (SELECT COUNT(*) FROM ai.agno_sessions) as total_sessions,
                    (SELECT COUNT(*) FROM ai.agno_sessions WHERE ai.agno_sessions.created_at > EXTRACT(EPOCH FROM NOW() - INTERVAL '24 hours')) as sessions_today,
                    (SELECT COUNT(*) FROM ai.agno_sessions WHERE ai.agno_sessions.created_at > EXTRACT(EPOCH FROM NOW() - INTERVAL '7 days')) as sessions_week,

                    -- Memory stats
                    (SELECT COUNT(*) FROM ai.agno_memories) as total_memories,

                    -- Feedback stats
                    (SELECT COUNT(*) FROM feedback_submissions) as total_feedback,
                    (SELECT COUNT(*) FROM feedback_submissions WHERE feedback_submissions.status = 'unread') as unread_feedback,
                    (SELECT COUNT(*) FROM feedback_submissions WHERE feedback_submissions.feedback_type = 'positive') as positive_feedback,
                    (SELECT COUNT(*) FROM feedback_submissions WHERE feedback_submissions.feedback_type = 'negative') as negative_feedback
            """

            result = session.execute(text(stats_query))
            stats = result.fetchone()

            # Get recent registrations (last 5)
            recent_users_query = """
                SELECT id, email, display_name, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT 5
            """
            recent_users_result = session.execute(text(recent_users_query))
            recent_users = [
                {
                    "id": str(row.id),
                    "email": row.email,
                    "display_name": row.display_name,
                    "created_at": int(row.created_at.timestamp()) if row.created_at else None
                }
                for row in recent_users_result.fetchall()
            ]

            # Log successful stats view
            await log_activity(
                request=request,
                user_id=user_id,
                action_type="admin_view_stats",
                success=True,
                status_code=200,
                details={"total_users": stats[0], "total_sessions": stats[5]},
                is_admin=True
            )

            return {
                "success": True,
                "data": {
                    "users": {
                        "total": stats[0],
                        "online": stats[1],
                        "admins": stats[2],
                        "new_week": stats[3],
                        "new_month": stats[4]
                    },
                    "sessions": {
                        "total": stats[5],
                        "today": stats[6],
                        "week": stats[7]
                    },
                    "memories": {
                        "total": stats[8]
                    },
                    "feedback": {
                        "total": stats[9],
                        "unread": stats[10],
                        "positive": stats[11],
                        "negative": stats[12]
                    },
                    "recent_users": recent_users
                }
            }

    except HTTPException as he:
        # Log failed stats view
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="admin_view_stats",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException",
            is_admin=is_admin if 'is_admin' in locals() else False
        )
        raise
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="admin_view_stats",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            is_admin=is_admin if 'is_admin' in locals() else False
        )

        raise HTTPException(status_code=500, detail=f"Failed to get admin stats: {str(e)}")

# ═══════════════════════════════════════════════════════════════
# ADMIN TOKEN USAGE ANALYTICS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/token-usage")
async def get_token_usage(
    request: Request,
    agent_id: Optional[str] = Query(None, description="Filter by specific agent ID"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    group_by: Optional[str] = Query(None, description="Group by: agent, user, day, week, month")
):
    """
    Get comprehensive token usage analytics (admin only).

    Features:
    - Total usage statistics (all agents aggregated)
    - Breakdown by individual agent/team
    - Per-user statistics
    - Timeline data for charts
    - Cost calculations and projections
    - Flexible filtering and grouping

    Query Parameters:
    - agent_id: Filter by specific agent (e.g., "cirkelline", "research-team")
    - user_id: Filter by specific user UUID
    - start_date: Filter from date (ISO 8601 format)
    - end_date: Filter to date (ISO 8601 format)
    - group_by: Group results by 'agent', 'user', 'day', 'week', or 'month'

    Returns:
    - summary: Total tokens, cost, message count
    - by_agent: Breakdown per agent with individual stats
    - by_user: Top users by token usage
    - timeline: Time-series data for charting
    - projections: Daily/weekly/monthly cost estimates
    """
    try:
        # Extract and decode JWT token
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
            logger.error(f"JWT decode error in get_token_usage: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        if not requesting_user_id or requesting_user_id.startswith("anon-"):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Use synchronous session
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            # Check if user is admin
            admin_check = session.execute(
                text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id LIMIT 1"),
                {"user_id": requesting_user_id}
            )
            is_admin = admin_check.fetchone() is not None

            if not is_admin:
                raise HTTPException(status_code=403, detail="Admin access required")

            # Build WHERE clause for filters
            where_conditions = ["metrics IS NOT NULL", "jsonb_array_length(metrics) > 0"]
            params = {}

            if start_date:
                where_conditions.append("created_at >= :start_date")
                params["start_date"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

            if end_date:
                where_conditions.append("created_at <= :end_date")
                params["end_date"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            if user_id:
                where_conditions.append("user_id = :user_id")
                params["user_id"] = user_id

            where_clause = " AND ".join(where_conditions)

            # ═══ 1. SUMMARY STATISTICS ═══
            summary_query = f"""
                WITH metric_items AS (
                    SELECT
                        jsonb_array_elements(metrics) as metric
                    FROM ai.agno_sessions
                    WHERE {where_clause}
                )
                SELECT
                    COUNT(*) as message_count,
                    SUM((metric->>'total_tokens')::bigint) as total_tokens,
                    SUM((metric->>'input_tokens')::bigint) as total_input_tokens,
                    SUM((metric->>'output_tokens')::bigint) as total_output_tokens,
                    SUM((metric->>'total_cost')::numeric) as total_cost,
                    SUM((metric->>'input_cost')::numeric) as total_input_cost,
                    SUM((metric->>'output_cost')::numeric) as total_output_cost
                FROM metric_items
            """

            if agent_id:
                summary_query += " WHERE metric->>'agent_id' = :agent_id"
                params["agent_id"] = agent_id

            summary_result = session.execute(text(summary_query), params)
            summary_row = summary_result.fetchone()

            summary = {
                "message_count": int(summary_row[0] or 0),
                "total_tokens": int(summary_row[1] or 0),
                "input_tokens": int(summary_row[2] or 0),
                "output_tokens": int(summary_row[3] or 0),
                "total_cost": float(summary_row[4] or 0),
                "input_cost": float(summary_row[5] or 0),
                "output_cost": float(summary_row[6] or 0)
            }

            # ═══ 2. BREAKDOWN BY AGENT ═══
            by_agent_query = f"""
                WITH metric_items AS (
                    SELECT
                        jsonb_array_elements(metrics) as metric
                    FROM ai.agno_sessions
                    WHERE {where_clause}
                )
                SELECT
                    metric->>'agent_id' as agent_id,
                    metric->>'agent_name' as agent_name,
                    metric->>'agent_type' as agent_type,
                    COUNT(*) as message_count,
                    SUM((metric->>'total_tokens')::bigint) as total_tokens,
                    SUM((metric->>'input_tokens')::bigint) as input_tokens,
                    SUM((metric->>'output_tokens')::bigint) as output_tokens,
                    SUM((metric->>'total_cost')::numeric) as total_cost,
                    AVG((metric->>'total_tokens')::bigint) as avg_tokens_per_message
                FROM metric_items
                GROUP BY metric->>'agent_id', metric->>'agent_name', metric->>'agent_type'
                ORDER BY total_tokens DESC
            """

            by_agent_result = session.execute(text(by_agent_query), params)
            by_agent = [
                {
                    "agent_id": row[0],
                    "agent_name": row[1],
                    "agent_type": row[2],
                    "message_count": int(row[3]),
                    "total_tokens": int(row[4] or 0),
                    "input_tokens": int(row[5] or 0),
                    "output_tokens": int(row[6] or 0),
                    "total_cost": float(row[7] or 0),
                    "avg_tokens_per_message": float(row[8] or 0)
                }
                for row in by_agent_result.fetchall()
            ]

            # ═══ 3. BREAKDOWN BY USER (if no user_id filter) ═══
            by_user = []
            if not user_id:  # Only show user breakdown if not filtering by specific user
                by_user_query = f"""
                    WITH metric_items AS (
                        SELECT
                            s.user_id,
                            u.email,
                            u.display_name,
                            jsonb_array_elements(s.metrics) as metric
                        FROM ai.agno_sessions s
                        LEFT JOIN users u ON s.user_id::uuid = u.id
                        WHERE {where_clause}
                    )
                    SELECT
                        user_id,
                        email,
                        display_name,
                        COUNT(*) as message_count,
                        SUM((metric->>'total_tokens')::bigint) as total_tokens,
                        SUM((metric->>'total_cost')::numeric) as total_cost
                    FROM metric_items
                    GROUP BY user_id, email, display_name
                    ORDER BY total_tokens DESC
                    LIMIT 20
                """

                by_user_result = session.execute(text(by_user_query), params)
                by_user = [
                    {
                        "user_id": str(row[0]),
                        "email": row[1],
                        "display_name": row[2],
                        "message_count": int(row[3]),
                        "total_tokens": int(row[4] or 0),
                        "total_cost": float(row[5] or 0)
                    }
                    for row in by_user_result.fetchall()
                ]

            # ═══ 4. TIMELINE DATA (for charting) ═══
            timeline = []
            if group_by in ['day', 'week', 'month']:
                # Determine date truncation based on grouping
                trunc_format = {
                    'day': 'day',
                    'week': 'week',
                    'month': 'month'
                }[group_by]

                timeline_query = f"""
                    WITH metric_items AS (
                        SELECT
                            s.created_at,
                            jsonb_array_elements(s.metrics) as metric
                        FROM ai.agno_sessions s
                        WHERE {where_clause}
                    )
                    SELECT
                        date_trunc('{trunc_format}', created_at) as period,
                        COUNT(*) as message_count,
                        SUM((metric->>'total_tokens')::bigint) as total_tokens,
                        SUM((metric->>'total_cost')::numeric) as total_cost
                    FROM metric_items
                    GROUP BY period
                    ORDER BY period ASC
                """

                timeline_result = session.execute(text(timeline_query), params)
                timeline = [
                    {
                        "period": row[0].isoformat(),
                        "message_count": int(row[1]),
                        "total_tokens": int(row[2] or 0),
                        "total_cost": float(row[3] or 0)
                    }
                    for row in timeline_result.fetchall()
                ]

            # ═══ 5. COST PROJECTIONS ═══
            # Calculate daily average and project forward
            projections = {}
            if summary["total_cost"] > 0:
                # Get date range
                range_query = f"""
                    SELECT
                        MIN(created_at) as min_date,
                        MAX(created_at) as max_date
                    FROM ai.agno_sessions
                    WHERE {where_clause}
                """
                range_result = session.execute(text(range_query), params)
                range_row = range_result.fetchone()

                if range_row[0] and range_row[1]:
                    min_date = range_row[0]
                    max_date = range_row[1]

                    # Handle both datetime and timestamp types
                    if isinstance(min_date, (int, float)):
                        min_date = datetime.fromtimestamp(min_date)
                    if isinstance(max_date, (int, float)):
                        max_date = datetime.fromtimestamp(max_date)

                    days_span = (max_date - min_date).days + 1
                    daily_avg = summary["total_cost"] / max(days_span, 1)

                    projections = {
                        "daily_average": round(daily_avg, 4),
                        "weekly_projection": round(daily_avg * 7, 4),
                        "monthly_projection": round(daily_avg * 30, 4),
                        "yearly_projection": round(daily_avg * 365, 2)
                    }

            # Log successful token usage view
            await log_activity(
                request=request,
                user_id=requesting_user_id,
                action_type="admin_view_token_usage",
                success=True,
                status_code=200,
                details={
                    "total_tokens": summary["total_tokens"],
                    "total_cost": summary["total_cost"],
                    "filters": {
                        "agent_id": agent_id,
                        "user_id": user_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "group_by": group_by
                    }
                },
                is_admin=True
            )

            return {
                "success": True,
                "data": {
                    "summary": summary,
                    "by_agent": by_agent,
                    "by_user": by_user,
                    "timeline": timeline,
                    "projections": projections,
                    "filters_applied": {
                        "agent_id": agent_id,
                        "user_id": user_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "group_by": group_by
                    }
                }
            }

    except HTTPException as he:
        # Log failed token usage view
        await log_activity(
            request=request,
            user_id=requesting_user_id if 'requesting_user_id' in locals() else "unknown",
            action_type="admin_view_token_usage",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException",
            is_admin=is_admin if 'is_admin' in locals() else False
        )
        raise
    except Exception as e:
        logger.error(f"Error getting token usage: {str(e)}")

        # Log error
        await log_activity(
            request=request,
            user_id=requesting_user_id if 'requesting_user_id' in locals() else "unknown",
            action_type="admin_view_token_usage",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            is_admin=is_admin if 'is_admin' in locals() else False
        )

        raise HTTPException(status_code=500, detail=f"Failed to get token usage: {str(e)}")

logger.info("✅ Admin stats endpoint configured")
