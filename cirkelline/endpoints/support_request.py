"""
Public Support Request Endpoint
================================
Handles public customer support requests WITHOUT authentication.
This is the customer-facing entry point for KV1NT Support.

Provides:
- POST /api/support/request - Submit support request (NO AUTH required)
- GET /api/support/request/{request_id} - Check request status (by ID only)

Session 92: Built for P3 KV1NT Support kundeformular.
"""

import os
import uuid
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db

router = APIRouter()

# Rate limiting (in-memory, simple)
_rate_limits: dict[str, list[float]] = {}
RATE_WINDOW = 3600  # 1 hour
MAX_REQUESTS = 5  # 5 per hour per IP

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _check_rate(ip: str) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    reqs = [t for t in _rate_limits.get(ip, []) if now - t < RATE_WINDOW]
    if len(reqs) >= MAX_REQUESTS:
        return False
    reqs.append(now)
    _rate_limits[ip] = reqs
    return True


def _get_engine():
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    return create_engine(db_url)


def _ensure_table(engine):
    """Create support_requests table if it doesn't exist."""
    with Session(engine) as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS support_requests (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                request_type VARCHAR(50) NOT NULL DEFAULT 'support',
                message TEXT NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'new',
                ai_triage VARCHAR(50),
                ai_summary TEXT,
                admin_notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        session.commit()


@router.post("/api/support/request")
async def submit_support_request(request: Request):
    """
    Submit a public support request. NO authentication required.
    Customers can submit: support, booking, or question.
    """
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    if not _check_rate(ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    message = (body.get("message") or "").strip()
    request_type = (body.get("type") or "support").strip().lower()

    # Validate
    if not name or len(name) < 2:
        raise HTTPException(status_code=400, detail="Name is required (min 2 characters)")
    if not email or not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Valid email is required")
    if not message or len(message) < 10:
        raise HTTPException(status_code=400, detail="Message is required (min 10 characters)")
    if len(message) > 5000:
        raise HTTPException(status_code=400, detail="Message too long (max 5000 characters)")
    if request_type not in ("support", "booking", "question"):
        request_type = "support"

    try:
        engine = _get_engine()
        _ensure_table(engine)

        request_id = f"SR-{uuid.uuid4().hex[:8].upper()}"

        with Session(engine) as session:
            session.execute(
                text("""
                    INSERT INTO support_requests (id, name, email, request_type, message, status, created_at, updated_at)
                    VALUES (:id, :name, :email, :type, :message, 'new', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {"id": request_id, "name": name, "email": email, "type": request_type, "message": message}
            )
            session.commit()

        logger.info(f"Support request {request_id}: {request_type} from {email}")

        return {
            "success": True,
            "request_id": request_id,
            "message": "Vi har modtaget din henvendelse. Du hoerer fra os snarest.",
            "message_en": "We received your request. We will get back to you shortly."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Support request error: {e}")
        raise HTTPException(status_code=500, detail="Could not process request. Please try again.")


@router.get("/api/support/request/{request_id}")
async def get_support_request_status(request_id: str):
    """Check status of a support request by ID. No auth needed."""
    if not request_id.startswith("SR-") or len(request_id) != 11:
        raise HTTPException(status_code=400, detail="Invalid request ID")

    try:
        engine = _get_engine()
        with Session(engine) as session:
            result = session.execute(
                text("SELECT id, request_type, status, created_at FROM support_requests WHERE id = :id"),
                {"id": request_id}
            ).first()

            if not result:
                raise HTTPException(status_code=404, detail="Request not found")

            return {
                "request_id": result[0],
                "type": result[1],
                "status": result[2],
                "submitted": str(result[3])
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Support status check error: {e}")
        raise HTTPException(status_code=500, detail="Could not check status")


logger.info("Support request endpoint configured (PUBLIC, no auth)")
