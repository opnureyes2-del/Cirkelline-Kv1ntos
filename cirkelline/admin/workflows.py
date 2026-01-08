"""
Admin Workflow Management Endpoints
====================================
Handles admin-only workflow operations.

Provides:
- GET /api/admin/workflows - List all registered workflows
- GET /api/admin/workflows/runs - List all workflow runs
- GET /api/admin/workflows/runs/{run_id} - Get single run details
- POST /api/admin/workflows/{workflow_name}/run - Manually trigger workflow
- POST /api/admin/workflows/runs/{run_id}/cancel - Cancel running workflow
- GET /api/admin/workflows/stats - Get workflow statistics
- GET /api/admin/workflows/users-stats - Get all users with memory stats
- GET /api/admin/workflows/active - Get currently running workflows
- GET /api/admin/workflows/config - Get auto-trigger configuration
- PUT /api/admin/workflows/config - Update auto-trigger configuration

v1.3.0: Full implementation with users-stats, active runs, config endpoints, auto-trigger
"""

import os
import uuid
import json
import jwt as pyjwt
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
# HELPER: Check Admin
# ═══════════════════════════════════════════════════════════════

async def verify_admin(request: Request) -> str:
    """Verify the request is from an admin user. Returns user_id if valid."""
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
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id or user_id.startswith("anon-"):
        raise HTTPException(status_code=401, detail="Authentication required")

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        admin_check = session.execute(
            text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id LIMIT 1"),
            {"user_id": user_id}
        )
        is_admin = admin_check.fetchone() is not None

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user_id


# ═══════════════════════════════════════════════════════════════
# LIST ALL REGISTERED WORKFLOWS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/workflows")
async def list_workflows(request: Request):
    """
    List all registered workflows (admin only).

    Returns:
    - workflows: List of workflow definitions
    """
    user_id = await verify_admin(request)

    # Available workflows
    workflows = [
        {
            "name": "Memory Optimization",
            "description": "Merge duplicates, normalize topics, archive old memories",
            "schedule": "Daily 3:00 AM",
            "status": "idle",
            "steps": [
                "Fetch Memories",
                "Optimize All",
                "Validate",
                "Save & Archive",
                "Report"
            ]
        },
        {
            "name": "Daily Journal",
            "description": "Generate daily journal entry summarizing user interactions",
            "schedule": "Manual trigger",
            "status": "idle",
            "steps": [
                "Fetch Sessions",
                "Summarize",
                "Save Journal",
                "Report"
            ]
        }
    ]

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_list_workflows",
        success=True,
        status_code=200,
        is_admin=True
    )

    return {
        "success": True,
        "workflows": workflows
    }


logger.info("✅ Admin workflows list endpoint configured")


# ═══════════════════════════════════════════════════════════════
# LIST WORKFLOW RUNS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/workflows/runs")
async def list_workflow_runs(
    request: Request,
    workflow_name: str = Query(None),
    status: str = Query(None),
    target_user_id: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List all workflow runs with optional filters (admin only).

    Query params:
    - workflow_name: Filter by workflow name
    - status: Filter by status (pending, running, completed, failed)
    - target_user_id: Filter by target user
    - page: Page number
    - limit: Results per page

    Returns:
    - runs: List of workflow runs
    - total: Total count
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Build query - get runs from archive table grouped by run_id
        base_query = """
            SELECT
                a.optimization_run_id as run_id,
                'Memory Optimization' as workflow_name,
                a.user_id,
                u.email as user_email,
                COUNT(*) as archived_count,
                MIN(a.archived_at) as started_at,
                MAX(a.archived_at) as completed_at,
                'completed' as status
            FROM ai.agno_memories_archive a
            LEFT JOIN users u ON CASE WHEN a.user_id NOT LIKE 'anon-%' THEN CAST(a.user_id AS uuid) ELSE NULL END = u.id
            WHERE a.optimization_run_id IS NOT NULL
        """

        count_query = """
            SELECT COUNT(DISTINCT optimization_run_id)
            FROM ai.agno_memories_archive
            WHERE optimization_run_id IS NOT NULL
        """

        params = {}

        if target_user_id:
            base_query += " AND a.user_id = :target_user_id"
            count_query += " AND user_id = :target_user_id"
            params["target_user_id"] = target_user_id

        base_query += """
            GROUP BY a.optimization_run_id, a.user_id, u.email
            ORDER BY started_at DESC
            LIMIT :limit OFFSET :offset
        """
        params["limit"] = limit
        params["offset"] = (page - 1) * limit

        # Get total count
        count_result = session.execute(text(count_query), params)
        total = count_result.fetchone()[0]

        # Get runs
        result = session.execute(text(base_query), params)
        rows = result.fetchall()

        runs = []
        for row in rows:
            # Get current memory count for this user
            current_count_result = session.execute(
                text("SELECT COUNT(*) FROM ai.agno_memories WHERE user_id = :user_id"),
                {"user_id": row[2]}
            )
            current_count = current_count_result.fetchone()[0]

            runs.append({
                "run_id": row[0],
                "workflow_name": row[1],
                "user_id": row[2],
                "user_email": row[3],
                "archived_count": row[4],
                "current_count": current_count,
                "started_at": row[5].isoformat() if row[5] else None,
                "completed_at": row[6].isoformat() if row[6] else None,
                "status": row[7]
            })

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_list_workflow_runs",
            success=True,
            status_code=200,
            details={"total": total, "page": page},
            is_admin=True
        )

        return {
            "success": True,
            "runs": runs,
            "total": total,
            "page": page,
            "limit": limit
        }


logger.info("✅ Admin workflow runs endpoint configured")


# ═══════════════════════════════════════════════════════════════
# GET SINGLE WORKFLOW RUN DETAILS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/workflows/runs/{run_id}")
async def get_workflow_run(request: Request, run_id: str):
    """
    Get detailed information about a specific workflow run (admin only).

    Returns:
    - run: Full run details including archived memories
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Get run info from archive
        run_query = """
            SELECT
                a.optimization_run_id,
                a.user_id,
                u.email as user_email,
                COUNT(*) as archived_count,
                MIN(a.archived_at) as started_at,
                MAX(a.archived_at) as completed_at
            FROM ai.agno_memories_archive a
            LEFT JOIN users u ON CASE WHEN a.user_id NOT LIKE 'anon-%' THEN CAST(a.user_id AS uuid) ELSE NULL END = u.id
            WHERE a.optimization_run_id = :run_id
            GROUP BY a.optimization_run_id, a.user_id, u.email
        """

        result = session.execute(text(run_query), {"run_id": run_id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Workflow run not found")

        target_user_id = row[1]

        # Get ALL archived memories for this run (BEFORE)
        archived_query = """
            SELECT original_memory_id, memory, topics, created_at
            FROM ai.agno_memories_archive
            WHERE optimization_run_id = :run_id
            ORDER BY archived_at ASC
        """
        archived_result = session.execute(text(archived_query), {"run_id": run_id})
        archived_rows = archived_result.fetchall()

        archived_memories = []
        for ar in archived_rows:
            archived_memories.append({
                "memory_id": ar[0],
                "memory": ar[1],
                "topics": ar[2] if ar[2] else [],
                "created_at": ar[3].isoformat() if ar[3] else None
            })

        # Get ALL current memories for this user (AFTER)
        # v1.3.3: Handle both SECONDS and MILLISECONDS formats
        # Timestamps > 4102444800 (year 2100) are in milliseconds
        current_query = """
            SELECT memory_id, memory, topics,
                   TO_TIMESTAMP(CASE WHEN created_at > 4102444800 THEN created_at / 1000.0 ELSE created_at END) as created_at,
                   TO_TIMESTAMP(CASE WHEN updated_at > 4102444800 THEN updated_at / 1000.0 ELSE updated_at END) as updated_at
            FROM ai.agno_memories
            WHERE user_id = :user_id
            ORDER BY updated_at DESC
        """
        current_result = session.execute(text(current_query), {"user_id": target_user_id})
        current_rows = current_result.fetchall()

        current_memories = []
        for cr in current_rows:
            current_memories.append({
                "memory_id": cr[0],
                "memory": cr[1],
                "topics": cr[2] if cr[2] else [],
                "created_at": cr[3].isoformat() if cr[3] else None,
                "updated_at": cr[4].isoformat() if cr[4] else None
            })

        # Calculate topic stats
        original_topics = set()
        for m in archived_memories:
            if m["topics"]:
                original_topics.update(m["topics"])

        current_topics = set()
        for m in current_memories:
            if m["topics"]:
                current_topics.update(m["topics"])

        # ═══════════════════════════════════════════════════════════════
        # COMPUTE CHANGES - Show EXACTLY what changed
        # ═══════════════════════════════════════════════════════════════

        # Build content lookup (normalized) for current memories
        def normalize(text):
            # Strip whitespace and outer quotes
            text = text.strip().strip('"')
            # Convert escaped quotes to regular quotes
            text = text.replace('\\"', '"')
            text = text.replace("\\'", "'")
            # Remove ALL quote characters for comparison
            text = text.replace('"', '').replace("'", '')
            return text.lower()

        current_content_map = {}
        for m in current_memories:
            norm = normalize(m["memory"])
            current_content_map[norm] = m

        archived_content_map = {}
        for m in archived_memories:
            norm = normalize(m["memory"])
            archived_content_map[norm] = m

        # Find DELETED: in archive but NOT in current
        deleted_memories = []
        for norm, mem in archived_content_map.items():
            if norm not in current_content_map:
                deleted_memories.append(mem)

        # Find NEW/MERGED: in current but NOT in archive
        new_memories = []
        for norm, mem in current_content_map.items():
            if norm not in archived_content_map:
                new_memories.append(mem)

        # Topic changes
        topics_removed = sorted(list(original_topics - current_topics))
        topics_added = sorted(list(current_topics - original_topics))

        changes = {
            "summary": {
                "before": len(archived_memories),
                "after": len(current_memories),
                "net_change": len(current_memories) - len(archived_memories)
            },
            "deleted": deleted_memories,
            "new_or_merged": new_memories,
            "topics": {
                "removed": topics_removed,
                "added": topics_added
            }
        }

        run_details = {
            "run_id": row[0],
            "workflow_name": "Memory Optimization",
            "user_id": target_user_id,
            "user_email": row[2],
            "status": "completed",
            "started_at": row[4].isoformat() if row[4] else None,
            "completed_at": row[5].isoformat() if row[5] else None,
            "stats": {
                "memories_before": len(archived_memories),
                "memories_after": len(current_memories),
                "reduction_percent": round((1 - len(current_memories) / len(archived_memories)) * 100, 1) if len(archived_memories) > 0 else 0,
                "topics_before": len(original_topics),
                "topics_after": len(current_topics),
                "topics_removed": len(original_topics) - len(current_topics)
            },
            "changes": changes,
            "before": {
                "memories": archived_memories,
                "topics": sorted(list(original_topics))
            },
            "after": {
                "memories": current_memories,
                "topics": sorted(list(current_topics))
            }
        }

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_view_workflow_run",
            success=True,
            status_code=200,
            details={"run_id": run_id},
            is_admin=True
        )

        return {
            "success": True,
            "run": run_details
        }


logger.info("✅ Admin workflow run details endpoint configured")


# ═══════════════════════════════════════════════════════════════
# MANUALLY TRIGGER WORKFLOW
# ═══════════════════════════════════════════════════════════════

@router.post("/api/admin/workflows/{workflow_name}/run")
async def trigger_workflow(
    request: Request,
    workflow_name: str,
    target_user_id: str = Query(...),
    target_date: str = Query(None, description="Target date for journal workflow (YYYY-MM-DD). Defaults to today.")
):
    """
    Manually trigger a workflow for a specific user (admin only).

    NOW RUNS IN BACKGROUND - returns immediately with run_id.
    Poll /api/admin/workflows/active to see progress.

    Query params:
    - target_user_id: The user to run the workflow for
    - target_date: (optional) For daily-journal, specify date (YYYY-MM-DD)

    Returns:
    - run_id: The workflow run ID
    - status: "started" (poll /active for progress)
    """
    import asyncio

    admin_user_id = await verify_admin(request)

    # Validate workflow name
    valid_workflows = ["memory-optimization", "daily-journal"]
    if workflow_name not in valid_workflows:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found. Valid: {', '.join(valid_workflows)}")

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    # Verify target user exists
    with Session(engine) as session:
        user_check = session.execute(
            text("SELECT email FROM users WHERE id = CAST(:user_id AS uuid)"),
            {"user_id": target_user_id}
        )
        user_row = user_check.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="Target user not found")

        target_email = user_row[0]

    # Generate run_id upfront
    run_id = str(uuid.uuid4())

    # Route to appropriate workflow
    if workflow_name == "memory-optimization":
        # Start tracking in database BEFORE launching background task
        start_workflow_run(run_id, "Memory Optimization", target_user_id, {"triggered_by": admin_user_id})

        # Run the workflow in background (don't await!)
        from cirkelline.workflows.memory_optimization import run_memory_optimization

        logger.info(f"[Admin] Starting memory optimization in BACKGROUND for user {target_user_id} ({target_email})")

        # Create background task - returns immediately
        asyncio.create_task(run_memory_optimization(target_user_id, run_id))

    elif workflow_name == "daily-journal":
        # Start tracking in database
        start_workflow_run(run_id, "Daily Journal", target_user_id, {"triggered_by": admin_user_id, "target_date": target_date})

        # Run the workflow in background
        from cirkelline.workflows.daily_journal import run_daily_journal

        logger.info(f"[Admin] Starting daily journal in BACKGROUND for user {target_user_id} ({target_email}), date={target_date or 'today'}")

        # Create background task - returns immediately
        asyncio.create_task(run_daily_journal(target_user_id, target_date=target_date, run_id=run_id))

    await log_activity(
        request=request,
        user_id=admin_user_id,
        action_type="admin_trigger_workflow",
        success=True,
        status_code=200,
        target_user_id=target_user_id,
        details={
            "workflow_name": workflow_name,
            "target_email": target_email,
            "run_id": run_id,
            "status": "started"
        },
        is_admin=True
    )

    # Return immediately - frontend will poll for progress
    return {
        "success": True,
        "status": "started",
        "run_id": run_id,
        "message": "Workflow started in background. Poll /api/admin/workflows/active for progress.",
        "target_user": {
            "id": target_user_id,
            "email": target_email
        }
    }


logger.info("✅ Admin workflow trigger endpoint configured")


# ═══════════════════════════════════════════════════════════════
# CANCEL RUNNING WORKFLOW
# ═══════════════════════════════════════════════════════════════

@router.post("/api/admin/workflows/runs/{run_id}/cancel")
async def cancel_workflow_run(request: Request, run_id: str):
    """
    Cancel a running workflow (admin only).

    Note: Currently workflows run synchronously so this is a placeholder
    for future async workflow support.

    Returns:
    - status: cancelled/not_found/already_completed
    """
    user_id = await verify_admin(request)

    # For now, workflows run synchronously so we can't really cancel them
    # This is a placeholder for future async support

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_cancel_workflow",
        success=True,
        status_code=200,
        details={"run_id": run_id},
        is_admin=True
    )

    return {
        "success": True,
        "message": "Workflow cancellation not yet supported (workflows run synchronously)",
        "run_id": run_id
    }


logger.info("✅ Admin workflow cancel endpoint configured")


# ═══════════════════════════════════════════════════════════════
# GET WORKFLOW STATISTICS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/workflows/stats")
async def get_workflow_stats(request: Request, workflow_name: str = Query(None)):
    """
    Get workflow statistics (admin only).

    Query params:
    - workflow_name: Filter by workflow name (e.g., "Memory Optimization"). If not provided, returns Memory Optimization stats by default.

    Returns:
    - stats: Overall workflow statistics with real metrics
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    # Default to Memory Optimization for backwards compatibility
    filter_workflow = workflow_name or "Memory Optimization"

    with Session(engine) as session:
        # Get total runs from workflow_runs table
        total_runs_result = session.execute(
            text("SELECT COUNT(*) FROM ai.workflow_runs WHERE status = 'completed' AND workflow_name = :wf"),
            {"wf": filter_workflow}
        )
        total_runs = total_runs_result.fetchone()[0] or 0

        # Get runs today from workflow_runs table
        today_runs_result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM ai.workflow_runs
                WHERE status = 'completed'
                AND completed_at >= CURRENT_DATE
                AND workflow_name = :wf
            """),
            {"wf": filter_workflow}
        )
        runs_today = today_runs_result.fetchone()[0] or 0

        # Get aggregated metrics from workflow_runs.metrics JSONB
        # metrics contains: deleted, merged, kept, before, after, reduction
        metrics_result = session.execute(
            text("""
                SELECT
                    COALESCE(SUM((metrics->>'deleted')::int), 0) as total_deleted,
                    COALESCE(SUM((metrics->>'merged')::int), 0) as total_merged,
                    COALESCE(AVG((metrics->>'reduction')::float), 0) as avg_reduction,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_count
                FROM ai.workflow_runs
                WHERE metrics IS NOT NULL
                AND workflow_name = :wf
            """),
            {"wf": filter_workflow}
        )
        metrics_row = metrics_result.fetchone()
        total_deleted = metrics_row[0] or 0
        total_merged = metrics_row[1] or 0
        avg_reduction = round(metrics_row[2] or 0, 1)
        completed_count = metrics_row[3] or 0
        failed_count = metrics_row[4] or 0

        # Calculate success rate
        total_attempted = completed_count + failed_count
        success_rate = round((completed_count / total_attempted * 100), 1) if total_attempted > 0 else 100.0

        # Get current total memories
        current_memories_result = session.execute(
            text("SELECT COUNT(*) FROM ai.agno_memories")
        )
        current_memories = current_memories_result.fetchone()[0] or 0

        # Get users with memories
        users_with_memories_result = session.execute(
            text("SELECT COUNT(DISTINCT user_id) FROM ai.agno_memories")
        )
        users_with_memories = users_with_memories_result.fetchone()[0] or 0

        stats = {
            "total_runs": total_runs,
            "runs_today": runs_today,
            "total_deleted": total_deleted,
            "total_merged": total_merged,
            "avg_reduction": avg_reduction,
            "success_rate": success_rate,
            "current_memories": current_memories,
            "users_with_memories": users_with_memories,
            "workflows": {
                "Memory Optimization": {
                    "total_runs": total_runs,
                    "status": "idle",
                    "schedule": "Growth-based (+100)"
                }
            }
        }

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_workflow_stats",
            success=True,
            status_code=200,
            is_admin=True
        )

        return {
            "success": True,
            "stats": stats
        }


logger.info("✅ Admin workflow stats endpoint configured")


# ═══════════════════════════════════════════════════════════════
# GET ALL USERS WITH MEMORY STATS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/workflows/users-stats")
async def get_users_memory_stats(request: Request):
    """
    Get all users with their memory statistics (admin only).

    Enhanced v1.3.1: Includes intelligent trigger data:
    - total_runs: How many workflow runs for this user
    - post_optimization_count: Memory count after last successful run
    - growth: New memories since last optimization
    - should_trigger: Whether user should be triggered (growth >= 100)
    - run_history: List of runs with before/after stats

    Returns:
    - users: List of users with full memory and workflow stats
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    GROWTH_THRESHOLD = 100  # Trigger when user adds 100+ new memories

    with Session(engine) as session:
        # Main query: Get user base info + memory stats
        users_query = """
            SELECT
                u.id as user_id,
                u.email,
                COALESCE(m.memory_count, 0) as memory_count,
                COALESCE(t.topic_count, 0) as topic_count,
                a.last_optimization
            FROM users u
            LEFT JOIN (
                SELECT user_id, COUNT(*) as memory_count
                FROM ai.agno_memories
                GROUP BY user_id
            ) m ON CAST(u.id AS varchar) = m.user_id
            LEFT JOIN (
                SELECT user_id, COUNT(DISTINCT topic) as topic_count
                FROM ai.agno_memories, LATERAL jsonb_array_elements_text(topics::jsonb) as topic
                GROUP BY user_id
            ) t ON CAST(u.id AS varchar) = t.user_id
            LEFT JOIN (
                SELECT user_id, MAX(archived_at) as last_optimization
                FROM ai.agno_memories_archive
                WHERE optimization_run_id IS NOT NULL
                GROUP BY user_id
            ) a ON CAST(u.id AS varchar) = a.user_id
            ORDER BY memory_count DESC NULLS LAST
        """

        result = session.execute(text(users_query))
        rows = result.fetchall()

        # Get workflow runs for all users at once
        runs_query = """
            SELECT
                user_id,
                run_id,
                status,
                started_at,
                completed_at,
                output_data
            FROM ai.workflow_runs
            WHERE workflow_name = 'Memory Optimization'
            ORDER BY started_at DESC
        """
        runs_result = session.execute(text(runs_query))
        runs_rows = runs_result.fetchall()

        # Build a map of user_id -> runs
        # Normalize user_id to lowercase string to handle UUID/VARCHAR differences
        user_runs = {}
        for run in runs_rows:
            uid = str(run[0]).lower().strip() if run[0] else None
            if uid:
                if uid not in user_runs:
                    user_runs[uid] = []
                user_runs[uid].append({
                    "run_id": run[1],
                    "status": run[2],
                    "started_at": run[3].isoformat() if run[3] else None,
                    "completed_at": run[4].isoformat() if run[4] else None,
                    "output_data": run[5] if run[5] else {}
                })

        users = []
        for row in rows:
            uid = str(row[0]).lower().strip()  # Normalize to match user_runs keys
            memory_count = row[2] or 0
            topic_count = row[3] or 0
            last_optimization = row[4]

            # Get runs for this user (normalized lookup)
            runs = user_runs.get(uid, [])
            total_runs = len(runs)

            # Get post_optimization_count from last successful run
            post_optimization_count = None
            for run in runs:
                if run["status"] == "completed" and run["output_data"]:
                    output = run["output_data"]
                    # Handle both dict and JSON string (raw SQL returns strings for JSONB)
                    if isinstance(output, str):
                        try:
                            output = json.loads(output)
                        except:
                            output = {}
                    if isinstance(output, dict):
                        # Try direct field first
                        if "post_optimization_count" in output:
                            post_optimization_count = output["post_optimization_count"]
                            break
                        # Fallback: parse from report text for legacy runs
                        report = output.get("report", "")
                        if report and "Memories:" in report:
                            import re
                            match = re.search(r"Memories:\s*\d+\s*→\s*(\d+)", report)
                            if match:
                                post_optimization_count = int(match.group(1))
                                break

            # Calculate growth
            if post_optimization_count is not None:
                growth = memory_count - post_optimization_count
            else:
                growth = None  # Never optimized

            # Determine if should trigger
            if post_optimization_count is None:
                # Never optimized - trigger when hits threshold
                should_trigger = memory_count >= GROWTH_THRESHOLD
            else:
                # Optimized before - trigger when growth hits threshold
                should_trigger = growth >= GROWTH_THRESHOLD if growth else False

            # Build run history with before/after stats
            run_history = []
            for run in runs[:5]:  # Last 5 runs
                output = run.get("output_data", {}) or {}
                # Handle JSON string from raw SQL
                if isinstance(output, str):
                    try:
                        output = json.loads(output)
                    except:
                        output = {}
                # Parse before/after from report if available
                before_count = None
                after_count = None
                reduction_percent = None

                if isinstance(output, dict) and "post_optimization_count" in output:
                    after_count = output.get("post_optimization_count")

                # Try to parse from report text
                report = output.get("report", "")
                if report and "Memories:" in report:
                    try:
                        import re
                        match = re.search(r"Memories:\s*(\d+)\s*→\s*(\d+)\s*\(([0-9.]+)%", report)
                        if match:
                            before_count = int(match.group(1))
                            after_count = int(match.group(2))
                            reduction_percent = float(match.group(3))
                    except:
                        pass

                run_history.append({
                    "run_id": run["run_id"],
                    "status": run["status"],
                    "started_at": run["started_at"],
                    "completed_at": run["completed_at"],
                    "before_count": before_count,
                    "after_count": after_count,
                    "reduction_percent": reduction_percent
                })

            users.append({
                "user_id": uid,
                "email": row[1],
                "memory_count": memory_count,
                "topic_count": topic_count,
                "last_optimization": last_optimization.isoformat() if last_optimization else None,
                # New fields for intelligent triggering
                "total_runs": total_runs,
                "post_optimization_count": post_optimization_count,
                "growth": growth,
                "should_trigger": should_trigger,
                "run_history": run_history
            })

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_users_memory_stats",
            success=True,
            status_code=200,
            is_admin=True
        )

        return {
            "success": True,
            "users": users,
            "total": len(users),
            "growth_threshold": GROWTH_THRESHOLD
        }


logger.info("✅ Admin workflow users-stats endpoint configured")


# ═══════════════════════════════════════════════════════════════
# GET ACTIVE WORKFLOW RUNS
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# DATABASE-BACKED WORKFLOW RUN TRACKING
# ═══════════════════════════════════════════════════════════════

def _get_engine():
    """Get database engine."""
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    return create_engine(db_url)


def start_workflow_run(run_id: str, workflow_name: str, user_id: str, input_data: dict = None):
    """Start tracking a workflow run in the database."""
    engine = _get_engine()
    with Session(engine) as session:
        session.execute(
            text("""
                INSERT INTO ai.workflow_runs (run_id, workflow_name, user_id, status, current_step, steps_completed, input_data)
                VALUES (:run_id, :workflow_name, :user_id, 'running', 'Starting', '[]', :input_data)
                ON CONFLICT (run_id) DO UPDATE SET
                    status = 'running',
                    current_step = 'Starting',
                    started_at = NOW()
            """),
            {
                "run_id": run_id,
                "workflow_name": workflow_name,
                "user_id": user_id,
                "input_data": json.dumps(input_data or {})
            }
        )
        session.commit()
    logger.info(f"[Workflow Tracking] Started run {run_id} for user {user_id}")


def update_workflow_step(run_id: str, step_name: str, step_number: int, total_steps: int = 6, stats: dict = None):
    """Update the current step of a workflow run."""
    engine = _get_engine()
    with Session(engine) as session:
        # Get current steps_completed
        result = session.execute(
            text("SELECT steps_completed FROM ai.workflow_runs WHERE run_id = :run_id"),
            {"run_id": run_id}
        )
        row = result.fetchone()
        steps_completed = row[0] if row and row[0] else []

        # Add current step to completed list
        if step_name not in steps_completed:
            steps_completed.append(step_name)

        session.execute(
            text("""
                UPDATE ai.workflow_runs
                SET current_step = :step_name,
                    steps_completed = :steps_completed,
                    metrics = COALESCE(metrics, '{}'::jsonb) || :metrics
                WHERE run_id = :run_id
            """),
            {
                "run_id": run_id,
                "step_name": step_name,
                "steps_completed": json.dumps(steps_completed),
                "metrics": json.dumps({"step": step_number, "total_steps": total_steps, "progress": int((step_number / total_steps) * 100), **(stats or {})})
            }
        )
        session.commit()
    logger.info(f"[Workflow Tracking] Run {run_id} - Step {step_number}/{total_steps}: {step_name}")


def complete_workflow_run(run_id: str, status: str = "completed", output_data: dict = None, error_message: str = None):
    """Mark a workflow run as completed or failed."""
    engine = _get_engine()
    # Determine current_step based on status (avoid CASE with same param twice - psycopg type issue)
    current_step = "Done" if status == "completed" else "Failed"

    with Session(engine) as session:
        session.execute(
            text("""
                UPDATE ai.workflow_runs
                SET status = :status,
                    completed_at = NOW(),
                    current_step = :current_step,
                    output_data = :output_data,
                    error_message = :error_message
                WHERE run_id = :run_id
            """),
            {
                "run_id": run_id,
                "status": status,
                "current_step": current_step,
                "output_data": json.dumps(output_data or {}),
                "error_message": error_message
            }
        )
        session.commit()
    logger.info(f"[Workflow Tracking] Run {run_id} - {status}")


def get_active_runs_from_db(workflow_name: str = None):
    """Get currently running workflows from database.

    Args:
        workflow_name: Optional filter by workflow name (e.g., "Memory Optimization", "Daily Journal")
    """
    engine = _get_engine()
    with Session(engine) as session:
        query = """
            SELECT
                w.run_id,
                w.workflow_name,
                w.user_id,
                u.email as user_email,
                w.status,
                w.current_step,
                w.steps_completed,
                w.started_at,
                w.metrics
            FROM ai.workflow_runs w
            LEFT JOIN users u ON CASE WHEN w.user_id NOT LIKE 'anon-%' THEN CAST(w.user_id AS uuid) ELSE NULL END = u.id
            WHERE w.status = 'running'
        """
        params = {}

        if workflow_name:
            query += " AND w.workflow_name = :workflow_name"
            params["workflow_name"] = workflow_name

        query += " ORDER BY w.started_at DESC"

        result = session.execute(text(query), params)
        rows = result.fetchall()

        active_runs = []
        for row in rows:
            metrics = row[8] or {}
            active_runs.append({
                "run_id": row[0],
                "workflow_name": row[1],
                "user_id": row[2],
                "user_email": row[3] or "Unknown",
                "status": row[4],
                "current_step": row[5],
                "steps_completed": row[6] or [],
                "started_at": row[7].isoformat() if row[7] else None,
                "step": metrics.get("step", 0),
                "total_steps": metrics.get("total_steps", 6),
                "progress": metrics.get("progress", 0),
                "stats": {k: v for k, v in metrics.items() if k not in ["step", "total_steps", "progress"]}
            })

        return active_runs


# Keep legacy in-memory tracking for backwards compatibility
ACTIVE_WORKFLOW_RUNS = {}


def update_active_run(user_id: str, run_id: str, step: int, step_name: str, total_steps: int = 6, stats: dict = None):
    """Update the active run status - both in-memory and database."""
    # Update database
    update_workflow_step(run_id, step_name, step, total_steps, stats)

    # Also update in-memory for local/single-container use
    ACTIVE_WORKFLOW_RUNS[user_id] = {
        "run_id": run_id,
        "user_id": user_id,
        "step": step,
        "step_name": step_name,
        "total_steps": total_steps,
        "progress": int((step / total_steps) * 100),
        "started_at": datetime.utcnow().isoformat() if user_id not in ACTIVE_WORKFLOW_RUNS else ACTIVE_WORKFLOW_RUNS[user_id].get("started_at"),
        "stats": stats or {}
    }


def clear_active_run(user_id: str):
    """Clear the active run for a user."""
    if user_id in ACTIVE_WORKFLOW_RUNS:
        del ACTIVE_WORKFLOW_RUNS[user_id]


def get_active_run(user_id: str = None):
    """Get active run(s). If user_id provided, get for that user only."""
    if user_id:
        return ACTIVE_WORKFLOW_RUNS.get(user_id)
    return ACTIVE_WORKFLOW_RUNS


@router.get("/api/admin/workflows/active")
async def get_active_workflows(request: Request, workflow_name: str = Query(None)):
    """
    Get currently running workflows (admin only).

    Now uses database for cross-container visibility.

    Query params:
    - workflow_name: Filter by workflow name (e.g., "Memory Optimization", "Daily Journal")

    Returns:
    - active_runs: List of currently running workflows
    """
    user_id = await verify_admin(request)

    # Get active runs from database (works across all containers)
    active_runs = get_active_runs_from_db(workflow_name=workflow_name)

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_get_active_workflows",
        success=True,
        status_code=200,
        is_admin=True
    )

    return {
        "success": True,
        "active_runs": active_runs,
        "count": len(active_runs)
    }


logger.info("✅ Admin workflow active runs endpoint configured")


# ═══════════════════════════════════════════════════════════════
# WORKFLOW AUTO-TRIGGER CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Default configuration (in-memory, could be moved to database)
WORKFLOW_CONFIG = {
    "memory_optimization": {
        "enabled": True,
        "threshold": 100,        # Trigger when memories >= threshold
        "cooldown_hours": 24,    # Don't re-trigger within this period
    }
}


@router.get("/api/admin/workflows/config")
async def get_workflow_config(request: Request):
    """
    Get workflow auto-trigger configuration (admin only).

    Returns:
    - config: Current configuration
    """
    user_id = await verify_admin(request)

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_get_workflow_config",
        success=True,
        status_code=200,
        is_admin=True
    )

    return {
        "success": True,
        "config": WORKFLOW_CONFIG
    }


@router.put("/api/admin/workflows/config")
async def update_workflow_config(request: Request):
    """
    Update workflow auto-trigger configuration (admin only).

    Body:
    - workflow_name: Which workflow to configure
    - enabled: Enable/disable auto-trigger
    - threshold: Memory count threshold
    - cooldown_hours: Hours between triggers

    Returns:
    - config: Updated configuration
    """
    user_id = await verify_admin(request)

    body = await request.json()
    workflow_name = body.get("workflow_name", "memory_optimization")

    if workflow_name not in WORKFLOW_CONFIG:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

    # Update config
    if "enabled" in body:
        WORKFLOW_CONFIG[workflow_name]["enabled"] = bool(body["enabled"])
    if "threshold" in body:
        WORKFLOW_CONFIG[workflow_name]["threshold"] = max(10, int(body["threshold"]))  # Min 10
    if "cooldown_hours" in body:
        WORKFLOW_CONFIG[workflow_name]["cooldown_hours"] = max(1, int(body["cooldown_hours"]))  # Min 1 hour

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_update_workflow_config",
        success=True,
        status_code=200,
        details={"workflow_name": workflow_name, "new_config": WORKFLOW_CONFIG[workflow_name]},
        is_admin=True
    )

    return {
        "success": True,
        "config": WORKFLOW_CONFIG,
        "message": f"Configuration updated for {workflow_name}"
    }


@router.post("/api/admin/workflows/restore")
async def restore_memories_from_archive(request: Request):
    """
    Restore memories from archive (admin only).

    Body:
    - user_id: User ID to restore memories for
    - run_id: Optimization run ID to restore from

    Returns:
    - deleted: Number of current memories deleted
    - restored: Number of memories restored from archive
    """
    user_id = await verify_admin(request)

    body = await request.json()
    target_user_id = body.get("user_id")
    run_id = body.get("run_id")

    if not target_user_id or not run_id:
        raise HTTPException(status_code=400, detail="user_id and run_id required")

    engine = _get_engine()
    with Session(engine) as session:
        # Delete current memories
        result = session.execute(
            text("DELETE FROM ai.agno_memories WHERE user_id = :user_id"),
            {"user_id": target_user_id}
        )
        deleted_count = result.rowcount

        # Restore from archive
        result = session.execute(
            text("""
                INSERT INTO ai.agno_memories (memory_id, user_id, memory, topics, created_at, updated_at)
                SELECT
                    original_memory_id,
                    user_id,
                    memory::jsonb,
                    topics,
                    EXTRACT(EPOCH FROM created_at) * 1000,
                    EXTRACT(EPOCH FROM NOW()) * 1000
                FROM ai.agno_memories_archive
                WHERE optimization_run_id = :run_id
            """),
            {"run_id": run_id}
        )
        restored_count = result.rowcount
        session.commit()

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_restore_memories",
        success=True,
        status_code=200,
        details={"target_user_id": target_user_id, "run_id": run_id, "deleted": deleted_count, "restored": restored_count},
        is_admin=True
    )

    logger.info(f"[Admin] Restored {restored_count} memories for user {target_user_id} from run {run_id}")

    return {
        "success": True,
        "deleted": deleted_count,
        "restored": restored_count,
        "message": f"Restored {restored_count} memories from archive"
    }


logger.info("✅ Admin workflow config endpoint configured")


# ═══════════════════════════════════════════════════════════════
# JOURNAL WORKFLOW ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/workflows/journals/stats")
async def get_journal_workflow_stats(request: Request):
    """
    Get journal workflow statistics (admin only).

    Returns:
    - stats: Journal workflow statistics including total runs, journals, users
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Get total runs from workflow_runs table (Daily Journal workflows)
        total_runs_result = session.execute(
            text("SELECT COUNT(*) FROM ai.workflow_runs WHERE workflow_name = 'Daily Journal' AND status = 'completed'")
        )
        total_runs = total_runs_result.fetchone()[0] or 0

        # Get runs today
        today_runs_result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM ai.workflow_runs
                WHERE workflow_name = 'Daily Journal'
                AND status = 'completed'
                AND completed_at >= CURRENT_DATE
            """)
        )
        runs_today = today_runs_result.fetchone()[0] or 0

        # Get total journals from user_journals table
        total_journals_result = session.execute(
            text("SELECT COUNT(*) FROM ai.user_journals")
        )
        total_journals = total_journals_result.fetchone()[0] or 0

        # Get journals created today
        journals_today_result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM ai.user_journals
                WHERE created_at >= EXTRACT(EPOCH FROM CURRENT_DATE)::bigint * 1000
            """)
        )
        journals_today = journals_today_result.fetchone()[0] or 0

        # Get users with journals
        users_with_journals_result = session.execute(
            text("SELECT COUNT(DISTINCT user_id) FROM ai.user_journals")
        )
        users_with_journals = users_with_journals_result.fetchone()[0] or 0

        # Calculate success rate
        total_attempted_result = session.execute(
            text("SELECT COUNT(*) FROM ai.workflow_runs WHERE workflow_name = 'Daily Journal'")
        )
        total_attempted = total_attempted_result.fetchone()[0] or 0
        success_rate = round((total_runs / total_attempted * 100), 1) if total_attempted > 0 else 100.0

        stats = {
            "total_runs": total_runs,
            "runs_today": runs_today,
            "success_rate": success_rate,
            "total_journals": total_journals,
            "journals_today": journals_today,
            "users_with_journals": users_with_journals
        }

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_journal_workflow_stats",
            success=True,
            status_code=200,
            is_admin=True
        )

        return {
            "success": True,
            "stats": stats
        }


logger.info("✅ Admin journal workflow stats endpoint configured")


@router.get("/api/admin/workflows/journals/entries")
async def get_journal_entries(
    request: Request,
    user_id_filter: str = Query(None, alias="user_id"),
    date_from: str = Query(None),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get journal entries with optional filters (admin only).

    Query params:
    - user_id: Filter by user
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    - page: Page number
    - limit: Results per page

    Returns:
    - entries: List of journal entries
    - total: Total count
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Build query
        base_query = """
            SELECT
                j.id,
                j.user_id,
                u.email as user_email,
                j.journal_date,
                j.summary,
                j.topics,
                j.outcomes,
                j.sessions_processed,
                j.message_count,
                j.created_at
            FROM ai.user_journals j
            LEFT JOIN users u ON CASE WHEN j.user_id NOT LIKE 'anon-%' THEN CAST(j.user_id AS uuid) ELSE NULL END = u.id
            WHERE 1=1
        """

        count_query = "SELECT COUNT(*) FROM ai.user_journals j WHERE 1=1"
        params = {}

        if user_id_filter:
            base_query += " AND j.user_id = :user_id_filter"
            count_query += " AND j.user_id = :user_id_filter"
            params["user_id_filter"] = user_id_filter

        if date_from:
            base_query += " AND j.journal_date >= :date_from"
            count_query += " AND j.journal_date >= :date_from"
            params["date_from"] = date_from

        if date_to:
            base_query += " AND j.journal_date <= :date_to"
            count_query += " AND j.journal_date <= :date_to"
            params["date_to"] = date_to

        # Get total count
        count_result = session.execute(text(count_query), params)
        total = count_result.fetchone()[0]

        # Add pagination
        base_query += " ORDER BY j.journal_date DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = (page - 1) * limit

        # Get entries
        result = session.execute(text(base_query), params)
        rows = result.fetchall()

        entries = []
        for row in rows:
            entries.append({
                "id": row[0],
                "user_id": row[1],
                "user_email": row[2],
                "journal_date": row[3].isoformat() if row[3] else None,
                "summary": row[4],
                "topics": row[5] if row[5] else [],
                "outcomes": row[6] if row[6] else [],
                "sessions_processed": row[7] if row[7] else [],
                "message_count": row[8] or 0,
                "created_at": row[9]
            })

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_get_journal_entries",
            success=True,
            status_code=200,
            details={"total": total, "page": page},
            is_admin=True
        )

        return {
            "success": True,
            "journals": entries,  # Frontend expects "journals"
            "entries": entries,   # Keep for backwards compatibility
            "total": total,
            "page": page,
            "limit": limit
        }


logger.info("✅ Admin journal entries endpoint configured")


@router.get("/api/admin/workflows/journals/users")
async def get_journal_users_stats(request: Request):
    """
    Get all users with their journal statistics (admin only).

    Returns:
    - users: List of users with journal stats including registration date and days on platform
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Get all users with journal stats, registration date, session count, and days with activity
        users_query = """
            SELECT
                u.id as user_id,
                u.email,
                u.created_at,
                GREATEST(1, CURRENT_DATE - DATE(u.created_at) + 1) as days_on_platform,
                COALESCE(j.journal_count, 0) as journal_count,
                j.latest_journal,
                COALESCE(s.session_count, 0) as session_count,
                COALESCE(s.days_with_activity, 0) as days_with_activity
            FROM users u
            LEFT JOIN (
                SELECT
                    user_id,
                    COUNT(*) as journal_count,
                    MAX(journal_date) as latest_journal
                FROM ai.user_journals
                GROUP BY user_id
            ) j ON CAST(u.id AS varchar) = j.user_id
            LEFT JOIN (
                SELECT
                    user_id,
                    COUNT(*) as session_count,
                    COUNT(DISTINCT DATE(to_timestamp(created_at))) as days_with_activity
                FROM ai.agno_sessions
                GROUP BY user_id
            ) s ON CAST(u.id AS varchar) = s.user_id
            ORDER BY journal_count DESC NULLS LAST
        """

        result = session.execute(text(users_query))
        rows = result.fetchall()

        users = []
        for row in rows:
            days_on_platform = row[3] or 1
            days_with_activity = row[7] or 0
            users.append({
                "user_id": str(row[0]),
                "email": row[1],
                "created_at": row[2].isoformat() if row[2] else None,
                "days_on_platform": days_on_platform,
                "journal_count": row[4] or 0,
                "expected_journals": days_with_activity,  # Days with actual activity
                "last_journal": row[5].isoformat() if row[5] else None,
                "total_sessions": row[6] or 0
            })

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_get_journal_users_stats",
            success=True,
            status_code=200,
            is_admin=True
        )

        return {
            "success": True,
            "users": users,
            "total": len(users)
        }


logger.info("✅ Admin journal users stats endpoint configured")


@router.get("/api/admin/workflows/journals/runs")
async def get_journal_workflow_runs(
    request: Request,
    target_user_id: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get journal workflow runs with optional filters (admin only).

    Query params:
    - target_user_id: Filter by target user
    - page: Page number
    - limit: Results per page

    Returns:
    - runs: List of workflow runs
    - total: Total count
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Build query
        base_query = """
            SELECT
                w.run_id,
                w.user_id,
                u.email as user_email,
                w.status,
                w.current_step,
                w.steps_completed,
                w.started_at,
                w.completed_at,
                w.output_data,
                w.error_message,
                w.metrics
            FROM ai.workflow_runs w
            LEFT JOIN users u ON CASE WHEN w.user_id NOT LIKE 'anon-%' THEN CAST(w.user_id AS uuid) ELSE NULL END = u.id
            WHERE w.workflow_name = 'Daily Journal'
        """

        count_query = "SELECT COUNT(*) FROM ai.workflow_runs WHERE workflow_name = 'Daily Journal'"
        params = {}

        if target_user_id:
            base_query += " AND w.user_id = :target_user_id"
            count_query += " AND user_id = :target_user_id"
            params["target_user_id"] = target_user_id

        # Get total count
        count_result = session.execute(text(count_query), params)
        total = count_result.fetchone()[0]

        # Add pagination
        base_query += " ORDER BY w.started_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = (page - 1) * limit

        # Get runs
        result = session.execute(text(base_query), params)
        rows = result.fetchall()

        runs = []
        for row in rows:
            output_data = row[8] or {}
            metrics = row[10] or {}

            # Extract target_date from metrics or output_data report
            target_date = metrics.get("target_date")
            if not target_date and output_data.get("report"):
                # Try to extract date from report (e.g., "Date: 2025-12-01")
                import re
                date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', output_data.get("report", ""))
                if date_match:
                    target_date = date_match.group(1)

            runs.append({
                "run_id": row[0],
                "workflow_name": "daily_journal",
                "user_id": row[1],
                "user_email": row[2],
                "target_date": target_date,
                "status": row[3],
                "current_step": row[4],
                "steps_completed": row[5] or [],
                "started_at": row[6].isoformat() if row[6] else None,
                "completed_at": row[7].isoformat() if row[7] else None,
                "output_data": output_data,
                "error_message": row[9],
                "metrics": metrics
            })

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_get_journal_workflow_runs",
            success=True,
            status_code=200,
            details={"total": total, "page": page},
            is_admin=True
        )

        return {
            "success": True,
            "runs": runs,
            "total": total,
            "page": page,
            "limit": limit
        }


logger.info("✅ Admin journal workflow runs endpoint configured")


@router.get("/api/admin/workflows/journals/active")
async def get_active_journal_runs(request: Request):
    """
    Get currently active journal workflow runs (admin only).
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        query = """
            SELECT
                w.run_id,
                w.user_id,
                u.email as user_email,
                w.current_step,
                w.steps_completed,
                w.started_at,
                w.output_data,
                w.input_data
            FROM ai.workflow_runs w
            LEFT JOIN users u ON CASE WHEN w.user_id NOT LIKE 'anon-%' THEN CAST(w.user_id AS uuid) ELSE NULL END = u.id
            WHERE w.workflow_name = 'Daily Journal'
              AND w.status = 'running'
            ORDER BY w.started_at DESC
        """

        result = session.execute(text(query))
        rows = result.fetchall()

        active_runs = []
        for row in rows:
            steps_completed = row[4] or []
            output_data = row[6] or {}
            input_data = row[7] or {}

            # Calculate progress (4 steps total for journal workflow)
            total_steps = 4
            current_step = len(steps_completed) + 1
            progress = int((len(steps_completed) / total_steps) * 100)

            # target_date is stored in input_data when workflow starts
            target_date = input_data.get("target_date") or output_data.get("target_date")

            active_runs.append({
                "run_id": row[0],
                "user_id": row[1],
                "user_email": row[2],
                "step": current_step,
                "current_step": row[3] or "Processing...",
                "total_steps": total_steps,
                "progress": progress,
                "started_at": row[5].isoformat() if row[5] else None,
                "target_date": target_date
            })

        return {
            "success": True,
            "active_runs": active_runs
        }


logger.info("✅ Admin active journal runs endpoint configured")


@router.get("/api/admin/workflows/journals/runs/{run_id}")
async def get_journal_run_details(request: Request, run_id: str):
    """
    Get detailed information about a specific journal workflow run (admin only).
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        query = """
            SELECT
                w.run_id,
                w.user_id,
                u.email as user_email,
                w.status,
                w.current_step,
                w.steps_completed,
                w.started_at,
                w.completed_at,
                w.output_data,
                w.error_message,
                w.metrics
            FROM ai.workflow_runs w
            LEFT JOIN users u ON CASE WHEN w.user_id NOT LIKE 'anon-%' THEN CAST(w.user_id AS uuid) ELSE NULL END = u.id
            WHERE w.run_id = :run_id
              AND w.workflow_name = 'Daily Journal'
        """

        result = session.execute(text(query), {"run_id": run_id})
        row = result.fetchone()

        if not row:
            return {"success": False, "error": "Run not found"}

        output_data = row[8] or {}
        metrics = row[10] or {}

        # Extract target_date from metrics or parse from report
        target_date = metrics.get("target_date")
        if not target_date and output_data.get("report"):
            import re
            date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', output_data.get("report", ""))
            if date_match:
                target_date = date_match.group(1)

        # Get message and session counts from metrics (the actual source)
        message_count = metrics.get("messages", 0) or metrics.get("messages_summarized", 0)
        session_count = metrics.get("sessions_fetched", 0)

        # Parse topics and outcomes from report if available
        topics = []
        outcomes = []
        if output_data.get("report"):
            import re
            report_text = output_data.get("report", "")

            # Parse TOPICS section (format: "TOPICS:\n  - topic1\n  - topic2\n...")
            topics_match = re.search(r'TOPICS?:\s*\n((?:\s*[-•*]\s*[^\n]+\n?)+)', report_text, re.IGNORECASE)
            if topics_match:
                topics_text = topics_match.group(1)
                topics = [t.strip().lstrip('-•* ').strip() for t in topics_text.split('\n') if t.strip() and t.strip().startswith(('-', '•', '*'))]

            # Parse OUTCOMES section (format: "OUTCOMES:\n  - outcome1\n  - outcome2\n...")
            outcomes_match = re.search(r'OUTCOMES?:\s*\n((?:\s*[-•*]\s*[^\n]+\n?)+)', report_text, re.IGNORECASE)
            if outcomes_match:
                outcomes_text = outcomes_match.group(1)
                outcomes = [o.strip().lstrip('-•* ').strip() for o in outcomes_text.split('\n') if o.strip() and o.strip().startswith(('-', '•', '*'))]

        # Fetch the actual journal entry if we have a journal_id
        journal_entry = None
        journal_id = metrics.get("journal_id")
        if journal_id:
            journal_query = """
                SELECT summary, topics, outcomes, journal_date
                FROM ai.user_journals
                WHERE id = :journal_id
            """
            journal_result = session.execute(text(journal_query), {"journal_id": journal_id})
            journal_row = journal_result.fetchone()
            if journal_row:
                journal_entry = {
                    "content": journal_row[0],  # The actual journal text
                    "topics": journal_row[1] or [],
                    "outcomes": journal_row[2] or [],
                    "date": journal_row[3].isoformat() if journal_row[3] else None
                }

        run_details = {
            "run_id": row[0],
            "workflow_name": "Daily Journal",
            "user_id": row[1],
            "user_email": row[2],
            "status": row[3],
            "current_step": row[4],
            "steps_completed": row[5] or [],
            "started_at": row[6].isoformat() if row[6] else None,
            "completed_at": row[7].isoformat() if row[7] else None,
            "target_date": target_date,
            "metrics": metrics,
            "journal_entry": journal_entry,  # The actual journal content!
            "output_data": {
                "summary": output_data.get("summary"),
                "topics": topics if topics else output_data.get("topics", []),
                "outcomes": outcomes if outcomes else output_data.get("outcomes", []),
                "message_count": message_count,
                "session_count": session_count,
                "report": output_data.get("report")
            },
            "error": row[9]
        }

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_get_journal_run_details",
            success=True,
            status_code=200,
            details={"run_id": run_id},
            is_admin=True
        )

        return {
            "success": True,
            "run": run_details
        }


logger.info("✅ Admin journal run details endpoint configured")


@router.get("/api/admin/workflows/journals/user/{target_user_id}/calendar")
async def get_user_journal_calendar(request: Request, target_user_id: str):
    """
    Get calendar timeline data for a user showing activity and journal status per day.

    Returns:
    - user_id, email, registered_at
    - days: List of all days since registration with activity/journal status
    - summary: total_days, days_with_activity, days_with_journals, gap_days
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Get user registration date
        user_query = """
            SELECT id, email, created_at
            FROM users
            WHERE CAST(id AS varchar) = :user_id
        """
        user_result = session.execute(text(user_query), {"user_id": target_user_id})
        user_row = user_result.fetchone()

        if not user_row:
            return {"success": False, "error": "User not found"}

        user_email = user_row[1]
        registered_at = user_row[2]

        # Get sessions with names per day
        sessions_query = """
            SELECT
                DATE(to_timestamp(created_at)) as activity_date,
                session_id,
                session_data->>'session_name' as session_name,
                created_at,
                to_timestamp(created_at) as session_time
            FROM ai.agno_sessions
            WHERE user_id = :user_id
            ORDER BY created_at ASC
        """
        sessions_result = session.execute(text(sessions_query), {"user_id": target_user_id})
        sessions_rows = sessions_result.fetchall()

        # Build activity lookup: date -> {session_count, message_count, sessions: [{name, id}]}
        activity_by_date = {}
        for row in sessions_rows:
            date_str = row[0].isoformat() if row[0] else None
            if date_str:
                if date_str not in activity_by_date:
                    activity_by_date[date_str] = {
                        "session_count": 0,
                        "message_count": 0,
                        "sessions": []
                    }
                activity_by_date[date_str]["session_count"] += 1

                # Generate better default name if session_name is null
                session_name = row[2]
                if not session_name:
                    session_time = row[4]
                    if session_time:
                        time_str = session_time.strftime("%H:%M")
                        session_name = f"Session at {time_str}"
                    else:
                        session_num = activity_by_date[date_str]["session_count"]
                        session_name = f"Session #{session_num}"

                activity_by_date[date_str]["sessions"].append({
                    "id": row[1],
                    "name": session_name
                })

        # Get journals with details per day
        journals_query = """
            SELECT journal_date, id, topics, summary
            FROM ai.user_journals
            WHERE user_id = :user_id
        """
        journals_result = session.execute(text(journals_query), {"user_id": target_user_id})
        journals_rows = journals_result.fetchall()

        # Build journal lookup: date -> {id, topics, summary_preview}
        journals_by_date = {}
        for row in journals_rows:
            date_str = row[0].isoformat() if row[0] else None
            if date_str:
                summary = row[3] or ""
                journals_by_date[date_str] = {
                    "id": row[1],
                    "topics": row[2] or [],
                    "summary_preview": summary[:150] + "..." if len(summary) > 150 else summary
                }

        # Generate all days from registration to today
        from datetime import date, timedelta

        start_date = registered_at.date() if hasattr(registered_at, 'date') else registered_at
        end_date = date.today()

        days = []
        current = end_date

        # Stats counters
        days_with_activity = 0
        days_with_journals = 0
        gap_days = 0

        while current >= start_date:
            date_str = current.isoformat()

            has_activity = date_str in activity_by_date
            has_journal = date_str in journals_by_date

            activity_data = activity_by_date.get(date_str, {"session_count": 0, "message_count": 0, "sessions": []})
            journal_data = journals_by_date.get(date_str)

            # Determine status
            if has_activity and has_journal:
                status = "complete"
                days_with_activity += 1
                days_with_journals += 1
            elif has_activity and not has_journal:
                status = "gap"
                days_with_activity += 1
                gap_days += 1
            else:
                status = "no_activity"

            days.append({
                "date": date_str,
                "has_activity": has_activity,
                "session_count": activity_data["session_count"],
                "message_count": activity_data["message_count"],
                "sessions": activity_data["sessions"],  # All sessions
                "has_journal": has_journal,
                "journal": journal_data,  # Contains id, topics, summary_preview
                "status": status
            })

            current -= timedelta(days=1)

        total_days = (end_date - start_date).days + 1

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_get_user_journal_calendar",
            success=True,
            status_code=200,
            details={"target_user_id": target_user_id},
            is_admin=True
        )

        return {
            "success": True,
            "user_id": target_user_id,
            "email": user_email,
            "registered_at": registered_at.isoformat() if registered_at else None,
            "days": days,
            "summary": {
                "total_days": total_days,
                "days_with_activity": days_with_activity,
                "days_with_journals": days_with_journals,
                "gap_days": gap_days
            }
        }


logger.info("✅ Admin user journal calendar endpoint configured")


@router.get("/api/admin/workflows/journals/user/{target_user_id}/day/{target_date}")
async def get_user_journal_day_details(request: Request, target_user_id: str, target_date: str):
    """
    Get detailed session and journal data for a specific user and date.

    Returns:
    - date: The target date
    - sessions: List of sessions with names and message counts
    - journal: Journal content if exists (summary, topics, outcomes)
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    from datetime import datetime

    try:
        parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}

    with Session(engine) as session:
        # Get sessions for this date
        # Convert date to Unix timestamp range
        start_of_day = datetime.combine(parsed_date, datetime.min.time())
        end_of_day = datetime.combine(parsed_date, datetime.max.time())
        start_ts = int(start_of_day.timestamp())
        end_ts = int(end_of_day.timestamp())

        sessions_query = """
            SELECT
                session_id,
                session_data->>'session_name' as session_name,
                created_at,
                runs
            FROM ai.agno_sessions
            WHERE user_id = :user_id
              AND created_at >= :start_ts
              AND created_at <= :end_ts
            ORDER BY created_at ASC
        """

        sessions_result = session.execute(text(sessions_query), {
            "user_id": target_user_id,
            "start_ts": start_ts,
            "end_ts": end_ts
        })
        sessions_rows = sessions_result.fetchall()

        sessions_list = []
        for row in sessions_rows:
            # Count messages in runs
            runs = row[3] or []
            message_count = 0
            if isinstance(runs, list):
                for run in runs:
                    if isinstance(run, dict) and "messages" in run:
                        message_count += len(run.get("messages", []))

            # Extract messages from runs for memory recovery
            messages = []
            if isinstance(runs, list):
                for run in runs:
                    if isinstance(run, dict):
                        # Get user input
                        if "input" in run and isinstance(run["input"], dict):
                            user_msg = run["input"].get("input_content", "")
                            if user_msg:
                                messages.append({"role": "user", "content": user_msg})
                        # Get assistant response
                        if "content" in run:
                            messages.append({"role": "assistant", "content": run["content"]})

            sessions_list.append({
                "session_id": row[0],
                "session_name": row[1] or "Untitled Session",
                "message_count": message_count,
                "created_at": datetime.fromtimestamp(row[2]).isoformat() if row[2] else None,
                "messages": messages  # Added for memory recovery
            })

        # Get journal for this date
        journal_query = """
            SELECT
                id,
                summary,
                topics,
                outcomes,
                sessions_processed,
                message_count,
                created_at
            FROM ai.user_journals
            WHERE user_id = :user_id
              AND journal_date = :target_date
        """

        journal_result = session.execute(text(journal_query), {
            "user_id": target_user_id,
            "target_date": target_date
        })
        journal_row = journal_result.fetchone()

        journal_data = None
        if journal_row:
            journal_data = {
                "id": journal_row[0],
                "summary": journal_row[1],
                "topics": journal_row[2] or [],
                "outcomes": journal_row[3] or [],
                "sessions_processed": journal_row[4] or [],
                "message_count": journal_row[5] or 0,
                "created_at": (datetime.fromtimestamp(journal_row[6]).isoformat() if isinstance(journal_row[6], (int, float)) else journal_row[6].isoformat()) if journal_row[6] else None
            }

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_get_user_journal_day_details",
            success=True,
            status_code=200,
            details={"target_user_id": target_user_id, "target_date": target_date},
            is_admin=True
        )

        return {
            "success": True,
            "date": target_date,
            "sessions": sessions_list,
            "journal": journal_data
        }


logger.info("✅ Admin user journal day details endpoint configured")


# ═══════════════════════════════════════════════════════════════
# JOURNAL QUEUE MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/admin/workflows/journals/queue")
async def get_journal_queue(request: Request):
    """
    Get journal queue statistics and recent items (admin only).

    Returns:
    - stats: Queue statistics (pending, processing, completed, failed, total)
    - items: Recent queue items with status
    - worker: Worker status
    - scheduler: Scheduler status
    """
    user_id = await verify_admin(request)

    from cirkelline.workflows.journal_queue import get_queue_stats, get_recent_queue_items
    from cirkelline.workflows.journal_worker import get_worker_status
    from cirkelline.workflows.journal_scheduler import get_scheduler_status

    stats = get_queue_stats()
    items = get_recent_queue_items(limit=50)
    worker_status = get_worker_status()
    scheduler_status = get_scheduler_status()

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_get_journal_queue",
        success=True,
        status_code=200,
        is_admin=True
    )

    return {
        "success": True,
        "stats": stats,
        "items": items,
        "worker": worker_status,
        "scheduler": scheduler_status
    }


logger.info("✅ Admin journal queue endpoint configured")


@router.post("/api/admin/workflows/journals/backfill/{target_user_id}")
async def backfill_user_journals(request: Request, target_user_id: str):
    """
    Queue all gap days for a specific user (admin only).

    This finds all days where the user had activity but no journal
    and adds them to the processing queue.

    Returns:
    - user_id: The target user
    - gaps_found: Number of gap days found
    - jobs_added: Number of jobs added to queue (may be less if some already exist)
    """
    user_id = await verify_admin(request)

    from cirkelline.workflows.journal_queue import get_user_gap_days, add_to_queue

    # Find gap days
    gap_days = get_user_gap_days(target_user_id)

    # Add to queue
    jobs_added = 0
    for day in gap_days:
        if add_to_queue(target_user_id, day, priority=0):  # Low priority for backfill
            jobs_added += 1

    logger.info(f"[Admin] Backfill for user {target_user_id}: {len(gap_days)} gaps found, {jobs_added} jobs added")

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_backfill_user_journals",
        success=True,
        status_code=200,
        target_user_id=target_user_id,
        details={"gaps_found": len(gap_days), "jobs_added": jobs_added},
        is_admin=True
    )

    return {
        "success": True,
        "user_id": target_user_id,
        "gaps_found": len(gap_days),
        "jobs_added": jobs_added,
        "message": f"Added {jobs_added} journal jobs to queue for backfill"
    }


logger.info("✅ Admin backfill user journals endpoint configured")


@router.post("/api/admin/workflows/journals/backfill-all")
async def backfill_all_users_journals(request: Request):
    """
    Queue all gap days for ALL users (admin only).

    This finds all days where any user had activity but no journal
    and adds them to the processing queue.

    Returns:
    - total_users: Number of users with gaps
    - total_gaps: Total gap days found
    - total_jobs_added: Number of jobs added to queue
    """
    user_id = await verify_admin(request)

    from cirkelline.workflows.journal_queue import add_all_gaps_to_queue

    result = add_all_gaps_to_queue(priority=0)  # Low priority for backfill

    logger.info(f"[Admin] Global backfill: {result['total_users']} users, {result['total_jobs_added']} jobs added")

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_backfill_all_users_journals",
        success=True,
        status_code=200,
        details=result,
        is_admin=True
    )

    return {
        "success": True,
        "total_users": result["total_users"],
        "total_jobs_added": result["total_jobs_added"],
        "message": f"Added {result['total_jobs_added']} journal jobs for {result['total_users']} users"
    }


logger.info("✅ Admin backfill all users journals endpoint configured")


@router.post("/api/admin/workflows/journals/queue/retry-failed")
async def retry_failed_queue_jobs(request: Request):
    """
    Reset all failed queue jobs back to pending (admin only).

    Returns:
    - reset_count: Number of jobs reset
    """
    user_id = await verify_admin(request)

    from cirkelline.workflows.journal_queue import retry_failed_jobs

    reset_count = retry_failed_jobs()

    logger.info(f"[Admin] Reset {reset_count} failed jobs to pending")

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_retry_failed_queue_jobs",
        success=True,
        status_code=200,
        details={"reset_count": reset_count},
        is_admin=True
    )

    return {
        "success": True,
        "reset_count": reset_count,
        "message": f"Reset {reset_count} failed jobs to pending"
    }


logger.info("✅ Admin retry failed queue jobs endpoint configured")


@router.post("/api/admin/workflows/journals/queue/clear-completed")
async def clear_completed_queue_jobs(request: Request, days_old: int = Query(7)):
    """
    Clear completed queue jobs older than specified days (admin only).

    Query params:
    - days_old: Clear jobs older than this many days (default 7)

    Returns:
    - deleted_count: Number of jobs deleted
    """
    user_id = await verify_admin(request)

    from cirkelline.workflows.journal_queue import clear_completed_jobs

    deleted_count = clear_completed_jobs(days_old=days_old)

    logger.info(f"[Admin] Cleared {deleted_count} completed jobs older than {days_old} days")

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_clear_completed_queue_jobs",
        success=True,
        status_code=200,
        details={"deleted_count": deleted_count, "days_old": days_old},
        is_admin=True
    )

    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} completed jobs older than {days_old} days"
    }


logger.info("✅ Admin clear completed queue jobs endpoint configured")


@router.post("/api/admin/workflows/journals/scheduler/trigger")
async def trigger_daily_scheduler_now(request: Request):
    """
    Manually trigger the daily scheduler job (admin only).

    This runs the same logic that runs at 1 AM:
    - Finds users with activity yesterday but no journal
    - Adds them to the queue with high priority

    Returns:
    - message: Result message
    """
    user_id = await verify_admin(request)

    from cirkelline.workflows.journal_scheduler import trigger_daily_job_now

    await trigger_daily_job_now()

    logger.info(f"[Admin] Manually triggered daily scheduler job")

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_trigger_daily_scheduler",
        success=True,
        status_code=200,
        is_admin=True
    )

    return {
        "success": True,
        "message": "Daily scheduler job triggered manually. Check queue for new jobs."
    }


logger.info("✅ Admin trigger daily scheduler endpoint configured")


@router.post("/api/admin/workflows/journals/queue/{job_id}/cancel")
async def cancel_queue_job(request: Request, job_id: int):
    """
    Cancel a single queue job (admin only).

    This removes the job from the queue entirely.
    For running jobs, it marks them as failed (cannot truly cancel a running workflow).

    Returns:
    - success: Whether the job was cancelled
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Check job exists and get status
        check = session.execute(
            text("SELECT status FROM ai.journal_queue WHERE id = :job_id"),
            {"job_id": job_id}
        )
        row = check.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Job not found")

        status = row[0]

        if status == 'completed':
            raise HTTPException(status_code=400, detail="Cannot cancel completed job")

        if status == 'processing':
            # Mark as failed since we can't truly stop a running workflow
            session.execute(
                text("UPDATE ai.journal_queue SET status = 'failed', error_message = 'Cancelled by admin' WHERE id = :job_id"),
                {"job_id": job_id}
            )
        else:
            # Delete pending job entirely
            session.execute(
                text("DELETE FROM ai.journal_queue WHERE id = :job_id"),
                {"job_id": job_id}
            )

        session.commit()

    logger.info(f"[Admin] Cancelled queue job {job_id} (was: {status})")

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_cancel_queue_job",
        success=True,
        status_code=200,
        details={"job_id": job_id, "previous_status": status},
        is_admin=True
    )

    return {
        "success": True,
        "job_id": job_id,
        "previous_status": status,
        "message": f"Job {job_id} cancelled"
    }


logger.info("✅ Admin cancel queue job endpoint configured")


@router.post("/api/admin/workflows/journals/queue/cancel-pending")
async def cancel_all_pending_jobs(request: Request):
    """
    Cancel all pending queue jobs (admin only).

    This removes all jobs with status='pending' from the queue.
    Does NOT affect processing or completed jobs.

    Returns:
    - cancelled_count: Number of jobs cancelled
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        result = session.execute(
            text("DELETE FROM ai.journal_queue WHERE status = 'pending'")
        )
        cancelled_count = result.rowcount
        session.commit()

    logger.info(f"[Admin] Cancelled all pending queue jobs: {cancelled_count} jobs deleted")

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_cancel_all_pending_jobs",
        success=True,
        status_code=200,
        details={"cancelled_count": cancelled_count},
        is_admin=True
    )

    return {
        "success": True,
        "cancelled_count": cancelled_count,
        "message": f"Cancelled {cancelled_count} pending jobs"
    }


logger.info("✅ Admin cancel all pending jobs endpoint configured")


@router.post("/api/admin/workflows/journals/runs/{run_id}/cancel")
async def cancel_journal_run(request: Request, run_id: str):
    """
    Cancel an active journal workflow run (admin only).

    This marks the run as failed in the database.
    Note: Cannot truly stop a running async workflow, but this marks it for cleanup.

    Returns:
    - success: Whether the run was marked as cancelled
    """
    user_id = await verify_admin(request)

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Check run exists and is running
        check = session.execute(
            text("SELECT status FROM ai.workflow_runs WHERE run_id = :run_id AND workflow_name = 'Daily Journal'"),
            {"run_id": run_id}
        )
        row = check.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Run not found")

        status = row[0]

        if status != 'running':
            raise HTTPException(status_code=400, detail=f"Cannot cancel run with status '{status}'")

        # Mark as failed
        session.execute(
            text("""
                UPDATE ai.workflow_runs
                SET status = 'failed',
                    completed_at = NOW(),
                    current_step = 'Cancelled',
                    error_message = 'Cancelled by admin'
                WHERE run_id = :run_id
            """),
            {"run_id": run_id}
        )
        session.commit()

    logger.info(f"[Admin] Cancelled workflow run {run_id}")

    await log_activity(
        request=request,
        user_id=user_id,
        action_type="admin_cancel_journal_run",
        success=True,
        status_code=200,
        details={"run_id": run_id},
        is_admin=True
    )

    return {
        "success": True,
        "run_id": run_id,
        "message": "Run cancelled"
    }


logger.info("✅ Admin cancel journal run endpoint configured")
