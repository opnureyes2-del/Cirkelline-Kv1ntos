"""
User Feedback API Endpoints
============================
Handles user feedback submission and admin management.

Provides:
- POST /api/feedback - Submit feedback (authenticated users only)
- GET /api/feedback - Get all feedback (admin only, with pagination)
- PATCH /api/feedback/{feedback_id}/status - Update feedback status (admin only)
- GET /api/feedback/unread-count - Get unread count (admin only)
"""

import os
import uuid
import jwt as pyjwt
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db
from cirkelline.middleware.middleware import log_activity

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# FEEDBACK SUBMISSION ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/api/feedback")
async def submit_feedback(request: Request):
    """
    Submit user feedback about a Cirkelline message.
    Only available for authenticated users (not anonymous).
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

    # Block anonymous users
    if user_id.startswith("anon-"):
        raise HTTPException(status_code=403, detail="Anonymous users cannot submit feedback. Please log in.")

    # Parse request body
    try:
        body = await request.json()
        message_content = body.get("message_content", "").strip()
        feedback_type = body.get("feedback_type", "").strip()
        user_comments = body.get("user_comments", "").strip() or None
        session_id = body.get("session_id") or None

        # Validation
        if not message_content:
            raise HTTPException(status_code=400, detail="message_content is required")
        if len(message_content) > 5000:
            raise HTTPException(status_code=400, detail="message_content too long (max 5000 chars)")
        if feedback_type not in ["positive", "negative"]:
            raise HTTPException(status_code=400, detail="feedback_type must be 'positive' or 'negative'")
        if user_comments and len(user_comments) > 2000:
            raise HTTPException(status_code=400, detail="user_comments too long (max 2000 chars)")

        # Insert into database
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            feedback_id = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO feedback_submissions
                    (id, user_id, session_id, message_content, feedback_type, user_comments, status, created_at, updated_at)
                    VALUES (:id, :user_id, :session_id, :message_content, :feedback_type, :user_comments, 'unread', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {
                    "id": feedback_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "message_content": message_content,
                    "feedback_type": feedback_type,
                    "user_comments": user_comments
                }
            )
            session.commit()

            logger.info(f"✅ Feedback submitted: {feedback_id} (type: {feedback_type}, user: {user_id})")

            # Log successful feedback submission
            await log_activity(
                request=request,
                user_id=user_id,
                action_type="feedback_submit",
                success=True,
                status_code=200,
                target_resource_id=feedback_id,
                resource_type="feedback",
                details={"feedback_type": feedback_type}
            )

            return {
                "success": True,
                "feedback_id": feedback_id
            }

    except HTTPException as he:
        # Log failed submission
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="feedback_submit",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException",
            resource_type="feedback"
        )
        raise
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="feedback_submit",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            resource_type="feedback"
        )

        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

logger.info("✅ Feedback submission endpoint configured")

# ═══════════════════════════════════════════════════════════════
# FEEDBACK LIST ENDPOINT (ADMIN)
# ═══════════════════════════════════════════════════════════════

@router.get("/api/feedback")
async def get_all_feedback(request: Request, status: str = None, page: int = 1, limit: int = 20, sort: str = "created_at"):
    """
    Get all feedback submissions (ADMIN ONLY).
    Supports filtering by status and pagination.
    """
    # Get user_id and is_admin from JWT
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
        is_admin = payload.get("is_admin", False)
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Build query with filters
    try:
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            # Build WHERE clause
            where_conditions = []
            params = {}

            if status and status in ["unread", "seen", "done"]:
                where_conditions.append("f.status = :status")
                params["status"] = status

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # Count total matching records
            count_result = session.execute(
                text(f"""
                    SELECT COUNT(*) as total
                    FROM feedback_submissions f
                    {where_clause}
                """),
                params
            ).first()

            total = count_result[0] if count_result else 0

            # Get unread count
            unread_result = session.execute(
                text("""
                    SELECT COUNT(*) as unread_count
                    FROM feedback_submissions
                    WHERE status = 'unread'
                """)
            ).first()

            unread_count = unread_result[0] if unread_result else 0

            # Get paginated data
            offset = (page - 1) * limit
            params["limit"] = limit
            params["offset"] = offset

            result = session.execute(
                text(f"""
                    SELECT
                        f.id,
                        f.user_id,
                        u.email as user_email,
                        f.session_id,
                        f.message_content,
                        f.feedback_type,
                        f.user_comments,
                        f.status,
                        EXTRACT(EPOCH FROM f.created_at) as created_at,
                        EXTRACT(EPOCH FROM f.updated_at) as updated_at
                    FROM feedback_submissions f
                    JOIN users u ON f.user_id = u.id
                    {where_clause}
                    ORDER BY f.{sort} DESC
                    LIMIT :limit OFFSET :offset
                """),
                params
            ).fetchall()

            feedback_list = []
            for row in result:
                feedback_list.append({
                    "id": str(row[0]),
                    "user_id": str(row[1]),
                    "user_email": row[2],
                    "session_id": row[3],
                    "message_content": row[4],
                    "feedback_type": row[5],
                    "user_comments": row[6],
                    "status": row[7],
                    "created_at": int(row[8]) if row[8] else 0,
                    "updated_at": int(row[9]) if row[9] else 0
                })

            logger.info(f"✅ Retrieved {len(feedback_list)} feedback submissions (total: {total}, unread: {unread_count})")

            return {
                "success": True,
                "data": feedback_list,
                "total": total,
                "unread_count": unread_count,
                "page": page,
                "limit": limit
            }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Feedback fetch error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching feedback: {str(e)}")

logger.info("✅ Feedback list endpoint configured")

# ═══════════════════════════════════════════════════════════════
# FEEDBACK STATUS UPDATE ENDPOINT (ADMIN)
# ═══════════════════════════════════════════════════════════════

@router.patch("/api/feedback/{feedback_id}/status")
async def update_feedback_status(request: Request, feedback_id: str):
    """
    Update feedback status (ADMIN ONLY).
    """
    # Get user_id and is_admin from JWT
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
        is_admin = payload.get("is_admin", False)
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Parse request body
    try:
        body = await request.json()
        new_status = body.get("status", "").strip()

        if new_status not in ["unread", "seen", "done"]:
            raise HTTPException(status_code=400, detail="status must be 'unread', 'seen', or 'done'")

        # Update in database
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            result = session.execute(
                text("""
                    UPDATE feedback_submissions
                    SET status = :status, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :feedback_id
                """),
                {
                    "status": new_status,
                    "feedback_id": feedback_id
                }
            )
            session.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Feedback not found")

            logger.info(f"✅ Feedback status updated: {feedback_id} -> {new_status}")

            # Log successful status update
            await log_activity(
                request=request,
                user_id=user_id,
                action_type="admin_update_feedback",
                success=True,
                status_code=200,
                target_resource_id=feedback_id,
                resource_type="feedback",
                details={"new_status": new_status},
                is_admin=True
            )

            return {
                "success": True,
                "feedback_id": feedback_id,
                "new_status": new_status
            }

    except HTTPException as he:
        # Log failed update
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="admin_update_feedback",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException",
            target_resource_id=feedback_id,
            resource_type="feedback",
            is_admin=is_admin if 'is_admin' in locals() else False
        )
        raise
    except Exception as e:
        logger.error(f"Feedback status update error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="admin_update_feedback",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            target_resource_id=feedback_id,
            resource_type="feedback",
            is_admin=is_admin if 'is_admin' in locals() else False
        )

        raise HTTPException(status_code=500, detail=f"Error updating feedback status: {str(e)}")

logger.info("✅ Feedback status update endpoint configured")

# ═══════════════════════════════════════════════════════════════
# FEEDBACK UNREAD COUNT ENDPOINT (ADMIN)
# ═══════════════════════════════════════════════════════════════

@router.get("/api/feedback/unread-count")
async def get_unread_feedback_count(request: Request):
    """
    Get count of unread feedback (ADMIN ONLY).
    Used for showing badge notification in UI.
    """
    # Get user_id and is_admin from JWT
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
        is_admin = payload.get("is_admin", False)
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT COUNT(*) as unread_count
                    FROM feedback_submissions
                    WHERE status = 'unread'
                """)
            ).first()

            unread_count = result[0] if result else 0

            return {
                "success": True,
                "unread_count": unread_count
            }

    except Exception as e:
        logger.error(f"Unread count fetch error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching unread count: {str(e)}")

logger.info("✅ Feedback unread count endpoint configured")
