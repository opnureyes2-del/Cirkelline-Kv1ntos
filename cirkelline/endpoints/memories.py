"""
User Memories API Endpoint
===========================
Handles user memory retrieval for authenticated users.

This endpoint retrieves all memories stored by the memory manager
for the authenticated user, including content, topics, and timestamps.
"""

import os
import json as json_lib
import jwt as pyjwt
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db
from cirkelline.middleware.middleware import log_activity

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# USER MEMORIES ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/user/memories")
async def get_user_memories(request: Request):
    """
    Get all memories for the authenticated user.
    Returns comprehensive memory data including content, topics, and timestamps.
    """
    # Get user_id from JWT
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

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

    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    # Fetch memories from database
    try:
        # Get database URL
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            # Query memories for this user
            result = session.execute(
                text("""
                    SELECT
                        memory_id,
                        memory,
                        input,
                        topics,
                        updated_at,
                        agent_id,
                        team_id
                    FROM ai.agno_memories
                    WHERE user_id = :user_id
                    ORDER BY updated_at DESC
                """),
                {"user_id": user_id}
            )

            memories = result.fetchall()

            # Format memories for frontend
            formatted_memories = []
            for mem in memories:
                # Parse JSON fields
                memory_text = mem[1] if isinstance(mem[1], str) else json_lib.dumps(mem[1])
                topics_list = mem[3] if isinstance(mem[3], list) else (json_lib.loads(mem[3]) if mem[3] else [])

                # Convert Unix timestamp to ISO format
                timestamp = datetime.fromtimestamp(mem[4]).isoformat() if mem[4] else None

                formatted_memories.append({
                    "memory_id": mem[0],
                    "memory": memory_text,
                    "input": mem[2],
                    "topics": topics_list,
                    "updated_at": timestamp,
                    "agent_id": mem[5],
                    "team_id": mem[6]
                })

            logger.info(f"✅ Retrieved {len(formatted_memories)} memories for user {user_id}")

            # Log successful memories retrieval
            await log_activity(
                request=request,
                user_id=user_id,
                action_type="memories_get",
                success=True,
                status_code=200,
                details={"count": len(formatted_memories)}
            )

            return {
                "success": True,
                "count": len(formatted_memories),
                "memories": formatted_memories
            }

    except Exception as e:
        logger.error(f"Memories fetch error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="memories_get",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__
        )

        raise HTTPException(status_code=500, detail=f"Error fetching memories: {str(e)}")

# ═══════════════════════════════════════════════════════════════
# DELETE INDIVIDUAL MEMORY ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.delete("/api/user/memories/{memory_id}")
async def delete_user_memory(request: Request, memory_id: str):
    """
    Delete a specific memory for the authenticated user.
    Memory hygiene best practice - allows users to manage their data (GDPR compliance).
    """
    # Get user_id from JWT
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

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

    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    # Delete memory from database (only if owned by this user)
    try:
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            # First verify the memory belongs to this user
            result = session.execute(
                text("""
                    SELECT memory_id FROM ai.agno_memories
                    WHERE memory_id = :memory_id AND user_id = :user_id
                """),
                {"memory_id": memory_id, "user_id": user_id}
            )

            memory = result.fetchone()
            if not memory:
                raise HTTPException(
                    status_code=404,
                    detail="Memory not found or not owned by this user"
                )

            # Delete the memory
            session.execute(
                text("""
                    DELETE FROM ai.agno_memories
                    WHERE memory_id = :memory_id AND user_id = :user_id
                """),
                {"memory_id": memory_id, "user_id": user_id}
            )
            session.commit()

            logger.info(f"✅ Deleted memory {memory_id} for user {user_id}")

            # Log successful memory deletion
            await log_activity(
                request=request,
                user_id=user_id,
                action_type="memory_delete",
                success=True,
                status_code=200,
                details={"memory_id": memory_id}
            )

            return {
                "success": True,
                "message": "Memory deleted successfully",
                "memory_id": memory_id
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory delete error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="memory_delete",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__
        )

        raise HTTPException(status_code=500, detail=f"Error deleting memory: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# MEMORY OPTIMIZATION WORKFLOW ENDPOINT (v1.3.0)
# ═══════════════════════════════════════════════════════════════

@router.post("/api/user/memories/optimize")
async def optimize_user_memories(request: Request):
    """
    Run the Memory Optimization Workflow for the authenticated user.

    This workflow:
    1. Normalizes topics (lowercase, standard categories)
    2. Merges duplicate memories
    3. Resolves contradictions (newest wins)
    4. Archives old memories (recoverable)

    Returns: Report with before/after stats
    """
    # Get user_id from JWT
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

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

    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    # Run the workflow
    try:
        from cirkelline.workflows.memory_optimization import run_memory_optimization

        logger.info(f"[API] Starting memory optimization for user {user_id}")
        result = await run_memory_optimization(user_id)

        # Log activity
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="memory_optimize",
            success=result.get("status") == "completed",
            status_code=200,
            details={"run_id": result.get("run_id")}
        )

        if result.get("status") == "completed":
            logger.info(f"[API] Memory optimization completed for user {user_id}")
            return {
                "success": True,
                "status": "completed",
                "run_id": result.get("run_id"),
                "report": result.get("report")
            }
        else:
            logger.error(f"[API] Memory optimization failed for user {user_id}: {result.get('error')}")
            return {
                "success": False,
                "status": "failed",
                "run_id": result.get("run_id"),
                "error": result.get("error")
            }

    except Exception as e:
        logger.error(f"Memory optimization error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="memory_optimize",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__
        )

        raise HTTPException(status_code=500, detail=f"Error optimizing memories: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# ADMIN BATCH INSERT MEMORIES ENDPOINT (v1.3.3)
# ═══════════════════════════════════════════════════════════════

@router.post("/api/admin/memories/batch-insert")
async def admin_batch_insert_memories(request: Request):
    """
    Admin endpoint to batch insert memories for memory recovery.
    Used for bug period Dec 3-14, 2025 recovery.

    Body: { "memories": [ { "user_id", "memory", "topics", "input", "created_at", "team_id" }, ... ] }
    """
    # Verify admin
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header[7:]
    try:
        payload = pyjwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"]
        )
        is_admin = payload.get("is_admin", False)
        user_id = payload.get("user_id")
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        body = await request.json()
        memories = body.get("memories", [])

        if not memories:
            raise HTTPException(status_code=400, detail="No memories provided")

        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        inserted_count = 0
        errors = []

        with Session(engine) as session:
            for mem in memories:
                try:
                    # Convert topics list to JSON string if needed
                    topics = mem.get("topics", [])
                    if isinstance(topics, list):
                        topics = json_lib.dumps(topics)

                    # Memory column is JSONB - serialize the string as JSON
                    memory_text = mem.get("memory", "")
                    memory_json = json_lib.dumps(memory_text)

                    session.execute(
                        text("""
                            INSERT INTO ai.agno_memories (memory_id, user_id, memory, topics, input, created_at, updated_at, team_id)
                            VALUES (gen_random_uuid()::text, :user_id, CAST(:memory AS jsonb), :topics, :input, :created_at, :created_at, :team_id)
                        """),
                        {
                            "user_id": mem.get("user_id"),
                            "memory": memory_json,
                            "topics": topics,
                            "input": mem.get("input", ""),
                            "created_at": mem.get("created_at"),
                            "team_id": mem.get("team_id", "cirkelline")
                        }
                    )
                    inserted_count += 1
                except Exception as e:
                    errors.append({"memory": mem.get("memory", "")[:50], "error": str(e)})
                    # Rollback the failed transaction to continue with next memory
                    session.rollback()

            session.commit()

        logger.info(f"✅ Admin batch inserted {inserted_count} memories")

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_batch_insert_memories",
            success=True,
            status_code=200,
            details={"inserted": inserted_count, "errors": len(errors)},
            is_admin=True
        )

        return {
            "success": True,
            "inserted": inserted_count,
            "errors": errors
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch insert error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error inserting memories: {str(e)}")


logger.info("✅ Memories endpoint configured")
