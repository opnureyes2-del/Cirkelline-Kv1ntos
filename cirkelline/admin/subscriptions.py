"""
Admin Subscription Management Endpoints
========================================
Handles admin-only subscription and tier management.

Provides:
- GET /api/admin/subscriptions - List all subscriptions with filters
- POST /api/admin/subscriptions/{target_user_id}/assign-tier - Assign tier to user
- GET /api/admin/subscription-stats - Subscription statistics
"""

import os
import jwt as pyjwt
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db
from cirkelline.middleware.middleware import log_activity

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# LIST SUBSCRIPTIONS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/subscriptions")
async def list_all_subscriptions(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tier_filter: str = Query("all"),
    status_filter: str = Query("all"),
    search: Optional[str] = Query(None)
):
    """
    List all subscriptions with filters (admin only).

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - tier_filter: Filter by tier slug (all/member/pro/business/elite/family)
    - status_filter: Filter by status (all/active/cancelled/expired)
    - search: Email or display name search

    Returns:
    - data: List of subscriptions with user and tier details
    - total: Total count matching filters
    - page: Current page
    - limit: Items per page
    """
    # Extract JWT manually like other admin endpoints
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
        logger.error(f"JWT decode error in list_subscriptions: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Use synchronous session
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Check admin
        admin_check = session.execute(
            text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchone()

        if not admin_check:
            raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Build base WHERE conditions
        where_conditions = []
        params = {}

        if tier_filter != 'all':
            where_conditions.append("s.tier_slug = :tier")
            params['tier'] = tier_filter

        if status_filter != 'all':
            where_conditions.append("s.status = :status")
            params['status'] = status_filter

        if search:
            where_conditions.append("(u.email ILIKE :search OR u.display_name ILIKE :search)")
            params['search'] = f"%{search}%"

        where_clause = "AND " + " AND ".join(where_conditions) if where_conditions else ""

        with Session(engine) as session:
            # Count total with proper query
            count_query = f"""
                SELECT COUNT(*)
                FROM user_subscriptions s
                JOIN users u ON s.user_id = u.id
                JOIN user_tiers t ON s.tier_slug = t.slug
                WHERE 1=1 {where_clause}
            """
            total = session.execute(text(count_query), params).scalar()

            logger.info(f"📊 Subscription query: tier_filter={tier_filter}, status_filter={status_filter}, search={search}, total={total}")

            # Get paginated results
            query = f"""
                SELECT
                    s.id, s.user_id, u.email, u.display_name,
                    s.tier_slug, t.name as tier_name, t.tier_level,
                    s.billing_cycle, s.status,
                    s.started_at, s.current_period_end, s.cancelled_at,
                    s.payment_provider
                FROM user_subscriptions s
                JOIN users u ON s.user_id = u.id
                JOIN user_tiers t ON s.tier_slug = t.slug
                WHERE 1=1 {where_clause}
                ORDER BY s.created_at DESC
                LIMIT :limit OFFSET :offset
            """

            params['limit'] = limit
            params['offset'] = (page - 1) * limit

            result = session.execute(text(query), params).fetchall()

            logger.info(f"📊 Returned {len(result)} subscriptions out of {total} total")

            subscriptions = []
            for row in result:
                subscriptions.append({
                    "id": str(row[0]),
                    "user_id": str(row[1]),
                    "user_email": row[2],
                    "user_display_name": row[3],
                    "tier_slug": row[4],
                    "tier_name": row[5],
                    "tier_level": row[6],
                    "billing_cycle": row[7],
                    "status": row[8],
                    "started_at": row[9].isoformat() if row[9] else None,
                    "current_period_end": row[10].isoformat() if row[10] else None,
                    "cancelled_at": row[11].isoformat() if row[11] else None,
                    "payment_provider": row[12]
                })

        return {
            "success": True,
            "data": subscriptions,
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("✅ Admin list subscriptions endpoint configured")

# ═══════════════════════════════════════════════════════════════
# ASSIGN TIER ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/api/admin/subscriptions/{target_user_id}/assign-tier")
async def admin_assign_tier(target_user_id: str, request: Request):
    """
    Admin assigns tier to user (bypasses payment).
    Used for promotions, manual upgrades, special cases.

    Request Body:
    - tier_slug: Target tier (member/pro/business/elite/family)
    - billing_cycle: monthly or annual (default: monthly)
    - reason: Optional reason for tier assignment

    Returns:
    - success: True/False
    - message: Confirmation message
    - subscription: Updated subscription object
    """
    # Extract JWT manually like other admin endpoints
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
        logger.error(f"JWT decode error in assign_tier: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Use synchronous session
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Check admin
        admin_check = session.execute(
            text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchone()

        if not admin_check:
            raise HTTPException(status_code=403, detail="Admin access required")

    try:
        data = await request.json()
        tier_slug = data.get('tier_slug')
        billing_cycle = data.get('billing_cycle', 'monthly')
        reason = data.get('reason', 'Admin tier assignment')

        if not tier_slug:
            raise HTTPException(status_code=400, detail="tier_slug required")

        from services.tier_service import TierService

        # Use admin_change_tier which allows ANY tier change (up, down, or same level)
        result = await TierService.admin_change_tier(
            engine,
            target_user_id,
            tier_slug,
            billing_cycle,
            admin_id=user_id,
            reason=reason
        )

        # Log admin action
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_assign_tier",
            success=True,
            status_code=200,
            target_user_id=target_user_id,
            details={"tier": tier_slug, "reason": reason},
            is_admin=True
        )

        return {
            "success": True,
            "message": f"Tier {tier_slug} assigned to user",
            "subscription": result
        }
    except Exception as e:
        logger.error(f"Error assigning tier: {e}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("✅ Admin assign tier endpoint configured")

# ═══════════════════════════════════════════════════════════════
# SUBSCRIPTION STATISTICS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/subscription-stats")
async def get_subscription_stats(request: Request):
    """
    Get subscription statistics (admin only).

    Returns:
    - total_subscriptions: Total count
    - active_subscriptions: Active count
    - by_tier: Breakdown by tier (member/pro/business/elite/family)
    - by_billing_cycle: Breakdown by billing cycle (monthly/annual)
    """
    # Extract JWT manually like other admin endpoints
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
        logger.error(f"JWT decode error in subscription_stats: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Use synchronous session
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    # Check admin
    try:
        with Session(engine) as session:
            admin_check = session.execute(
                text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchone()

            if not admin_check:
                raise HTTPException(status_code=403, detail="Admin access required")

            # Get statistics
            stats_query = """
            SELECT
                COUNT(*) as total_subscriptions,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_subscriptions,
                COUNT(CASE WHEN tier_slug = 'member' THEN 1 END) as free_users,
                COUNT(CASE WHEN tier_slug = 'pro' THEN 1 END) as pro_users,
                COUNT(CASE WHEN tier_slug = 'business' THEN 1 END) as business_users,
                COUNT(CASE WHEN tier_slug = 'elite' THEN 1 END) as elite_users,
                COUNT(CASE WHEN tier_slug = 'family' THEN 1 END) as family_users,
                COUNT(CASE WHEN billing_cycle = 'monthly' THEN 1 END) as monthly_billing,
                COUNT(CASE WHEN billing_cycle = 'annual' THEN 1 END) as annual_billing
            FROM user_subscriptions
            WHERE status = 'active'
        """

        result = session.execute(text(stats_query)).fetchone()

        return {
            "success": True,
            "stats": {
                "total_subscriptions": result[0],
                "active_subscriptions": result[1],
                "by_tier": {
                    "member": result[2],
                    "pro": result[3],
                    "business": result[4],
                    "elite": result[5],
                    "family": result[6]
                },
                "by_billing_cycle": {
                    "monthly": result[7],
                    "annual": result[8]
                }
            }
        }
    except Exception as e:
        logger.error(f"Error fetching subscription stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("✅ Admin subscription stats endpoint configured")
