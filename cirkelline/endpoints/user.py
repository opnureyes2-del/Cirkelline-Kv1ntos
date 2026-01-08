"""
User Data Endpoints
===================
Handles user memories retrieval and health check.
"""

import json
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text

from cirkelline.config import logger
from cirkelline.middleware.middleware import log_activity
from cirkelline.shared import decode_jwt_token, get_db_session

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
    # Decode JWT to get user_id
    try:
        payload = decode_jwt_token(request)
        user_id = payload.get("user_id")
    except HTTPException:
        raise

    # Fetch memories from database
    try:
        with get_db_session() as session:
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
                memory_text = mem[1] if isinstance(mem[1], str) else json.dumps(mem[1])
                topics_list = mem[3] if isinstance(mem[3], list) else (json.loads(mem[3]) if mem[3] else [])

                # Convert Unix timestamp to ISO format
                # Handle both seconds (10 digits) and milliseconds (13 digits)
                if mem[4]:
                    ts = mem[4]
                    # If timestamp is in milliseconds (> year 2100 in seconds), convert to seconds
                    if ts > 4102444800:  # 2100-01-01 as Unix timestamp
                        ts = ts / 1000
                    timestamp = datetime.fromtimestamp(ts).isoformat()
                else:
                    timestamp = None

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


logger.info("✅ User data endpoints loaded")
