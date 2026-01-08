"""
User Subscription Management Endpoints
=======================================
User-facing endpoints for viewing and managing subscriptions.
(Admin subscription management is in cirkelline/admin/subscriptions.py)
"""

import os
from fastapi import APIRouter, Request, HTTPException
from cirkelline.config import logger
from cirkelline.middleware.middleware import log_activity, _shared_engine

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# PUBLIC TIERS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/tiers")
async def get_available_tiers():
    """
    Get all available tiers with pricing information.
    Public endpoint - no authentication required.
    """
    try:
        from services.tier_service import TierService

        tiers = await TierService.get_all_tiers(_shared_engine)

        return {
            "success": True,
            "tiers": tiers
        }
    except Exception as e:
        logger.error(f"Error fetching tiers: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════
# USER SUBSCRIPTION INFO
# ═══════════════════════════════════════════════════════════════

@router.get("/api/user/subscription")
async def get_user_subscription_info(request: Request):
    """Get current user's subscription and tier information"""
    user_id = getattr(request.state, 'user_id', None)

    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        from services.tier_service import TierService

        subscription = await TierService.get_user_subscription(_shared_engine, user_id)
        all_tiers = await TierService.get_all_tiers(_shared_engine)

        # Determine which tiers user can upgrade to
        current_level = subscription['tier']['level'] if subscription else 1
        available_upgrades = [
            tier for tier in all_tiers
            if tier['tier_level'] > current_level
        ]

        return {
            "success": True,
            "subscription": subscription,
            "available_tiers": all_tiers,
            "available_upgrades": available_upgrades,
            "can_upgrade": len(available_upgrades) > 0
        }
    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════
# SUBSCRIPTION UPGRADE
# ═══════════════════════════════════════════════════════════════

@router.post("/api/user/subscription/upgrade")
async def request_tier_upgrade(request: Request):
    """
    Request tier upgrade.
    Phase 1: Creates subscription, requires admin approval for payment
    Phase 2: Will redirect to payment processor
    """
    user_id = getattr(request.state, 'user_id', None)

    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        data = await request.json()
        new_tier = data.get('tier_slug')
        billing_cycle = data.get('billing_cycle', 'monthly')

        if not new_tier:
            raise HTTPException(status_code=400, detail="tier_slug required")

        from services.tier_service import TierService

        result = await TierService.upgrade_subscription(
            _shared_engine, user_id, new_tier, billing_cycle
        )

        # Log upgrade request
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="tier_upgrade_request",
            success=True,
            status_code=200,
            details={"new_tier": new_tier, "billing_cycle": billing_cycle}
        )

        return {
            "success": True,
            "message": "Upgrade request created. Contact admin for payment setup.",
            "upgrade": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════
# SUBSCRIPTION DOWNGRADE
# ═══════════════════════════════════════════════════════════════

@router.post("/api/user/subscription/downgrade")
async def request_tier_downgrade(request: Request):
    """Schedule tier downgrade at end of billing cycle"""
    user_id = getattr(request.state, 'user_id', None)

    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        data = await request.json()
        new_tier = data.get('tier_slug')
        reason = data.get('reason', '')

        if not new_tier:
            raise HTTPException(status_code=400, detail="tier_slug required")

        from services.tier_service import TierService

        result = await TierService.downgrade_subscription(
            _shared_engine, user_id, new_tier, reason
        )

        # Log downgrade request
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="tier_downgrade_request",
            success=True,
            status_code=200,
            details={"new_tier": new_tier, "effective_date": result['effective_date']}
        )

        return {
            "success": True,
            "message": f"Downgrade scheduled for {result['effective_date']}",
            "downgrade": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error downgrading subscription: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════
# SUBSCRIPTION CANCELLATION
# ═══════════════════════════════════════════════════════════════

@router.delete("/api/user/subscription/cancel")
async def cancel_user_subscription(request: Request):
    """Cancel subscription (reverts to free tier at period end)"""
    user_id = getattr(request.state, 'user_id', None)

    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        data = await request.json()
        reason = data.get('reason', '')

        from services.tier_service import TierService

        result = await TierService.cancel_subscription(_shared_engine, user_id, reason)

        # Log cancellation
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="subscription_cancel",
            success=True,
            status_code=200,
            details={"reason": reason}
        )

        return {
            "success": True,
            "message": "Subscription cancelled",
            "cancellation": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

logger.info("✅ User subscription endpoints loaded")
