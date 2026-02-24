"""
Admiral Integration Endpoint — Cirkelline ↔ ELLE.md Admiral

Forbinder Cirkelline til Admiral-systemet på ELLE.md.
Læs-kun: ingen modificering af Cirkellines data.

GET  /api/admiral/status      — Er Admiral nået? Hvad kører?
POST /api/admiral/event       — Modtag events fra ELLE.md Event Bus
GET  /api/admiral/agents      — Vis graduerede agenter fra Cosmic
"""

import logging
import urllib.request
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

ADMIRAL_HQ = "http://localhost:5555"
ADMIRAL_NEXUS = "http://localhost:5592"
ADMIRAL_UNIFIED = "http://localhost:5596"


def _ping(url: str, timeout: int = 2) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 500
    except Exception:
        return False


@router.get("/api/admiral/status")
def admiral_status():
    """Cirkelline → Admiral health check."""
    hq_ok = _ping(f"{ADMIRAL_HQ}/")
    nexus_ok = _ping(f"{ADMIRAL_NEXUS}/health")
    unified_ok = _ping(f"{ADMIRAL_UNIFIED}/api/status")

    projects_data = None
    if unified_ok:
        try:
            req = urllib.request.Request(f"{ADMIRAL_UNIFIED}/api/status")
            with urllib.request.urlopen(req, timeout=3) as r:
                projects_data = json.loads(r.read()).get("summary")
        except Exception:
            pass

    return {
        "admiral_reachable": hq_ok or nexus_ok,
        "services": {
            "hq": hq_ok,
            "social_nexus": nexus_ok,
            "unified_projects": unified_ok,
        },
        "projects": projects_data,
        "timestamp": datetime.now().isoformat(),
    }


class AdmiralEvent(BaseModel):
    event_type: str
    source: str
    payload: dict = {}
    timestamp: Optional[str] = None


@router.post("/api/admiral/event")
async def receive_admiral_event(event: AdmiralEvent, request: Request):
    """Webhook: modtag events fra ELLE.md Event Bus (RabbitMQ → Admiral → Cirkelline)."""
    logger.info(f"Admiral event: {event.event_type} fra {event.source}")

    # Håndter graduation events automatisk
    if event.event_type in ("agent.graduated", "cosmic.agent.exported"):
        logger.info(f"Graduation event modtaget: {event.payload.get('name','?')}")
        return {"received": True, "action": "graduation_noted"}

    return {"received": True, "action": "logged"}
