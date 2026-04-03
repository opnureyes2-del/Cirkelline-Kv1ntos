"""
Landing Stats API — Public endpoint for myaddspace.com
========================================================
NO authentication required. Exposes aggregate system stats
without sensitive data. Cached for performance.
"""

import time

from fastapi import APIRouter

from cirkelline.config import logger
from cirkelline.database import db

router = APIRouter()

_cache = {"data": None, "ts": 0}
CACHE_TTL = 60  # seconds


@router.get("/api/landing/stats")
async def get_landing_stats():
    """Public landing page stats — cached, no auth."""
    now = time.time()
    if _cache["data"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["data"]

    stats = {
        "platform": "KV1NTOS",
        "status": "operational",
        "users": {"total": 0, "active_today": 0},
        "agents": {"total": 0, "graduated": 0},
        "training": {"rooms": 0, "sessions_completed": 0},
        "knowledge": {"documents": 0, "domains": 0},
        "uptime": True,
    }

    try:
        with db.get_session() as session:
            # User counts
            row = session.execute(
                db.text("SELECT COUNT(*) as total FROM users")
            ).fetchone()
            if row:
                stats["users"]["total"] = row[0]

            row = session.execute(
                db.text(
                    "SELECT COUNT(*) FROM sessions "
                    "WHERE created_at > NOW() - INTERVAL '24 hours'"
                )
            ).fetchone()
            if row:
                stats["users"]["active_today"] = row[0]

    except Exception as e:
        logger.debug(f"Landing stats users query: {e}")

    try:
        with db.get_session() as session:
            # Agent counts
            row = session.execute(
                db.text("SELECT COUNT(*) FROM agents")
            ).fetchone()
            if row:
                stats["agents"]["total"] = row[0]

            row = session.execute(
                db.text(
                    "SELECT COUNT(*) FROM agents WHERE status = 'graduated'"
                )
            ).fetchone()
            if row:
                stats["agents"]["graduated"] = row[0]

    except Exception as e:
        logger.debug(f"Landing stats agents query: {e}")

    try:
        # Training room stats from Cosmic (port 7778)
        import json
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:7778/api/training-rooms",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            rooms_data = json.loads(resp.read())
            rooms = rooms_data if isinstance(rooms_data, list) else rooms_data.get("rooms", [])
            stats["training"]["rooms"] = len(rooms)
            stats["training"]["sessions_completed"] = sum(
                r.get("sessions_completed", 0) for r in rooms
            )
    except Exception as e:
        logger.debug(f"Landing stats cosmic query: {e}")

    try:
        with db.get_session() as session:
            # Knowledge
            for table in ["documents", "knowledge_domains"]:
                try:
                    row = session.execute(
                        db.text(f"SELECT COUNT(*) FROM {table}")
                    ).fetchone()
                    if row:
                        key = "documents" if table == "documents" else "domains"
                        stats["knowledge"][key] = row[0]
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"Landing stats knowledge query: {e}")

    _cache["data"] = stats
    _cache["ts"] = now
    return stats
