"""
Memory Optimization Auto-Trigger
================================
Automatic triggering of memory optimization workflow based on GROWTH threshold.

v2.0.0: Growth-Based Triggering
- Triggers when user adds 100+ NEW memories since last optimization
- For first-time users, triggers when they reach 100 memories total
- No max interval - purely growth-based

Respects cooldown period (default: 24 hours) to prevent re-triggering.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session as SQLAlchemySession

from cirkelline.config import logger
from cirkelline.middleware.middleware import _shared_engine
from cirkelline.admin.workflows import WORKFLOW_CONFIG, update_active_run, clear_active_run


async def check_and_trigger_optimization(user_id: str):
    """
    Check if user meets criteria for auto-optimization and trigger if so.

    v2.0.0 Growth-Based Criteria:
    1. Auto-trigger is enabled in config
    2. User has added 100+ NEW memories since last optimization (growth)
       - For first-time users: trigger when they reach 100 memories total
    3. User hasn't had optimization within cooldown period

    This function is NON-BLOCKING - runs as background task after chat.
    """
    try:
        # Get current config
        config = WORKFLOW_CONFIG.get("memory_optimization", {})

        if not config.get("enabled", True):
            logger.debug("[AutoTrigger] Disabled in config, skipping")
            return

        threshold = config.get("threshold", 100)
        cooldown_hours = config.get("cooldown_hours", 24)

        # Get user's current memory count
        memory_count = await get_user_memory_count(user_id)

        if memory_count == 0:
            logger.debug(f"[AutoTrigger] User {user_id[:8]}... has 0 memories, skipping")
            return

        # Get post_optimization_count from last successful run
        post_opt_count = await get_post_optimization_count(user_id)

        # Calculate growth
        if post_opt_count is not None:
            # User has been optimized before - check growth
            growth = memory_count - post_opt_count
            if growth < threshold:
                logger.debug(f"[AutoTrigger] User {user_id[:8]}... growth +{growth} (below threshold +{threshold})")
                return
            logger.info(f"[AutoTrigger] User {user_id[:8]}... growth +{growth} (>= +{threshold}), checking cooldown")
        else:
            # First-time user - check total count
            if memory_count < threshold:
                logger.debug(f"[AutoTrigger] User {user_id[:8]}... has {memory_count} memories (first-time, below threshold {threshold})")
                return
            logger.info(f"[AutoTrigger] User {user_id[:8]}... has {memory_count} memories (first-time, >= {threshold}), checking cooldown")
            growth = memory_count  # For logging

        # Check cooldown
        can_run = await check_cooldown(user_id, cooldown_hours)

        if not can_run:
            logger.info(f"[AutoTrigger] User {user_id[:8]}... is within cooldown period, skipping")
            return

        # All checks passed - trigger optimization
        if post_opt_count is not None:
            logger.info(f"[AutoTrigger] TRIGGERING: User {user_id[:8]}... has +{growth} new memories (post_opt: {post_opt_count}, current: {memory_count})")
        else:
            logger.info(f"[AutoTrigger] TRIGGERING: User {user_id[:8]}... has {memory_count} memories (first-time optimization)")

        # Create task for background execution (don't await - fire and forget)
        asyncio.create_task(run_optimization_background(user_id))

    except Exception as e:
        logger.error(f"[AutoTrigger] Error checking trigger for user {user_id[:8]}...: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def get_user_memory_count(user_id: str) -> int:
    """Get the current memory count for a user."""
    try:
        def _query():
            with SQLAlchemySession(_shared_engine) as session:
                result = session.execute(
                    text("SELECT COUNT(*) FROM ai.agno_memories WHERE user_id = :user_id"),
                    {"user_id": user_id}
                ).scalar()
                return result or 0

        count = await asyncio.to_thread(_query)
        return count
    except Exception as e:
        logger.error(f"[AutoTrigger] Error getting memory count: {e}")
        return 0


async def get_post_optimization_count(user_id: str) -> int | None:
    """
    Get the post_optimization_count from the last successful workflow run.

    This is the memory count immediately after the last optimization completed.
    Returns None if user has never been optimized.
    """
    try:
        def _query():
            with SQLAlchemySession(_shared_engine) as session:
                result = session.execute(
                    text("""
                        SELECT output_data->>'post_optimization_count'
                        FROM ai.workflow_runs
                        WHERE user_id = :user_id
                          AND workflow_name = 'Memory Optimization'
                          AND status = 'completed'
                          AND output_data->>'post_optimization_count' IS NOT NULL
                        ORDER BY completed_at DESC
                        LIMIT 1
                    """),
                    {"user_id": user_id}
                ).scalar()
                return int(result) if result else None

        return await asyncio.to_thread(_query)
    except Exception as e:
        logger.error(f"[AutoTrigger] Error getting post_optimization_count: {e}")
        return None


async def check_cooldown(user_id: str, cooldown_hours: int) -> bool:
    """
    Check if enough time has passed since user's last optimization.

    Returns True if OK to run (cooldown expired or never ran).
    Returns False if within cooldown period.
    """
    try:
        def _query():
            with SQLAlchemySession(_shared_engine) as session:
                result = session.execute(
                    text("""
                        SELECT MAX(archived_at) as last_run
                        FROM ai.agno_memories_archive
                        WHERE user_id = :user_id
                        AND optimization_run_id IS NOT NULL
                    """),
                    {"user_id": user_id}
                ).fetchone()
                return result[0] if result else None

        last_run = await asyncio.to_thread(_query)

        if not last_run:
            # Never ran before
            return True

        # Check if cooldown has expired
        cooldown_end = last_run + timedelta(hours=cooldown_hours)
        now = datetime.utcnow()

        if now >= cooldown_end:
            return True

        remaining = cooldown_end - now
        logger.debug(f"[AutoTrigger] Cooldown remaining: {remaining}")
        return False

    except Exception as e:
        logger.error(f"[AutoTrigger] Error checking cooldown: {e}")
        # On error, allow run (fail open)
        return True


async def run_optimization_background(user_id: str):
    """
    Run memory optimization in background.

    This is a fire-and-forget task - exceptions are logged but don't propagate.
    """
    run_id = str(uuid.uuid4())

    try:
        logger.info(f"[AutoTrigger] Starting background optimization for user {user_id[:8]}..., run_id: {run_id[:8]}...")

        # Update active run status (for dashboard)
        update_active_run(
            user_id=user_id,
            run_id=run_id,
            step=1,
            step_name="Initializing",
            total_steps=6,
            stats={}
        )

        # Import here to avoid circular dependency
        from cirkelline.workflows.memory_optimization import run_memory_optimization

        # Run the workflow
        result = await run_memory_optimization(user_id, run_id)

        if result.get("status") == "completed":
            logger.info(f"[AutoTrigger] Background optimization completed for user {user_id[:8]}...")
        else:
            logger.warning(f"[AutoTrigger] Background optimization failed for user {user_id[:8]}...: {result.get('error')}")

    except Exception as e:
        logger.error(f"[AutoTrigger] Background optimization error for user {user_id[:8]}...: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Clear active run
        clear_active_run(user_id)


logger.info("Memory Optimization Auto-Trigger loaded (v2.0.0 - Growth-Based)")
