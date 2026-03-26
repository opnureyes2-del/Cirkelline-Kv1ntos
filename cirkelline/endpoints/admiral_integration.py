"""
Admiral Integration Endpoint — Cirkelline ↔ ELLE.md Admiral

Forbinder Cirkelline til Admiral-systemet på ELLE.md.
Læs-kun: ingen modificering af Cirkellines data.

GET  /api/admiral/status               — Er Admiral nået? Hvad kører?
POST /api/admiral/event                — Modtag events fra ELLE.md Event Bus
GET  /api/admiral/agents               — Vis graduerede agenter fra Cosmic
GET  /api/admiral/learnings            — System-wide learning stats
GET  /api/admiral/learnings/recall     — Recall learnings for a topic
GET  /api/admiral/learnings/sessions   — List recent learning room sessions
POST /api/admiral/learnings/assemble   — Create new learning room
GET  /api/admiral/fleet                — Fleet dashboard (pulse data)
GET  /api/admiral/fleet/admirals       — All admirals with scores
GET  /api/admiral/fleet/history        — Recent skill execution history
GET  /api/admiral/guides               — Semantic system guide
"""

import logging
import urllib.error
import urllib.parse
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
ADMIRAL_PIPELINE = "http://localhost:5599"


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


# ---------------------------------------------------------------------------
# Admiral Learning Room Integration
# ---------------------------------------------------------------------------

def _admiral_get(path: str, timeout: int = 10) -> dict:
    """GET request to Admiral Engine (5596) and return parsed JSON."""
    url = f"{ADMIRAL_UNIFIED}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _admiral_post(path: str, data: dict, timeout: int = 10) -> dict:
    """POST JSON to Admiral Engine (5596) and return parsed JSON."""
    url = f"{ADMIRAL_UNIFIED}{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


class LearningAssembleRequest(BaseModel):
    topic: str
    admiral: str = "KV1NT"


@router.get("/api/admiral/learnings")
def admiral_learnings():
    """System-wide learning stats — counts per admiral, recent learnings."""
    try:
        data = _admiral_get("/learnings", timeout=10)
        return {"ok": True, "data": data, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Admiral learnings fetch failed: {e}")
        return {"ok": False, "error": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/api/admiral/learnings/recall")
def admiral_learnings_recall(topic: str, max: int = 5):
    """Recall learnings for a given topic — ranked results."""
    try:
        params = urllib.parse.urlencode({"topic": topic, "max": max})
        data = _admiral_get(f"/learning-room/recall?{params}", timeout=10)
        return {"ok": True, "data": data, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Admiral learnings recall failed (topic={topic}): {e}")
        return {"ok": False, "error": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/api/admiral/learnings/sessions")
def admiral_learnings_sessions():
    """List recent learning room sessions."""
    try:
        data = _admiral_get("/learning-room/sessions", timeout=10)
        return {"ok": True, "data": data, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Admiral learning sessions fetch failed: {e}")
        return {"ok": False, "error": str(e), "timestamp": datetime.now().isoformat()}


@router.post("/api/admiral/learnings/assemble")
def admiral_learnings_assemble(body: LearningAssembleRequest):
    """Create a new learning room — multi-model research, longer timeout."""
    try:
        data = _admiral_post(
            "/learning-room/assemble",
            {"topic": body.topic, "admiral": body.admiral},
            timeout=30,
        )
        logger.info(f"Learning room assembled: topic={body.topic}, admiral={body.admiral}")
        return {"ok": True, "data": data, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Admiral learning assemble failed (topic={body.topic}): {e}")
        return {"ok": False, "error": str(e), "timestamp": datetime.now().isoformat()}


# ---------------------------------------------------------------------------
# Fleet Dashboard Endpoints
# ---------------------------------------------------------------------------

def _pipeline_get(path: str, timeout: int = 10) -> dict:
    """GET request to DataPipeline (5599) and return parsed JSON."""
    url = f"{ADMIRAL_PIPELINE}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


@router.get("/api/admiral/fleet")
def admiral_fleet():
    """Fleet dashboard — proxies to DataPipeline /pulse and extracts fleet data."""
    try:
        pulse = _pipeline_get("/pulse", timeout=10)

        fleet_raw = pulse.get("fleet", {})
        engine_raw = pulse.get("engine", {})
        pipeline_raw = pulse.get("pipeline", {})
        council_raw = pulse.get("council", {})

        result = {
            "health_score": pulse.get("health_score"),
            "fleet": {
                "admiral_avg": fleet_raw.get("admiral_avg"),
                "skills_avg": fleet_raw.get("skills_avg"),
                "over_80_pct": fleet_raw.get("over_80_pct"),
                "under_70": fleet_raw.get("under_70"),
                "over_95": fleet_raw.get("over_95"),
                "skills_total": fleet_raw.get("skills_total"),
                "admirals": fleet_raw.get("admirals", {}),
                "under_70_skills": fleet_raw.get("under_70_skills", []),
                "excellence": fleet_raw.get("excellence", []),
                "movements": fleet_raw.get("movements", []),
            },
            "engine": {
                "total_executions": engine_raw.get("total_executions"),
                "status": engine_raw.get("status"),
            },
            "pipeline": {
                "version": pipeline_raw.get("version"),
                "events_ingested": pipeline_raw.get("events_ingested"),
            },
            "council": {
                "recent_decisions": (council_raw.get("recent_decisions") or [])[:5],
            },
        }

        return {"ok": True, "data": result, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Admiral fleet fetch failed: {e}")
        return {"ok": False, "error": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/api/admiral/fleet/admirals")
def admiral_fleet_admirals():
    """All admirals with scores — combines Engine /health and Pipeline /pulse."""
    try:
        # Fetch both sources in sequence (stdlib has no async gather)
        health_data = {}
        try:
            health_data = _admiral_get("/health", timeout=10)
        except Exception as he:
            logger.warning(f"Engine /health unavailable, using pulse only: {he}")

        pulse_data = {}
        try:
            pulse_data = _pipeline_get("/pulse", timeout=10)
        except Exception as pe:
            logger.warning(f"Pipeline /pulse unavailable: {pe}")

        fleet_admirals = pulse_data.get("fleet", {}).get("admirals", {})
        health_admirals = health_data.get("admirals", {})

        admirals_list = []
        # Merge keys from both sources
        all_names = set(list(fleet_admirals.keys()) + list(health_admirals.keys()))
        for name in sorted(all_names):
            fa = fleet_admirals.get(name, {})
            ha = health_admirals.get(name, {})
            admirals_list.append({
                "id": name,
                "score": fa.get("score") or ha.get("score"),
                "skills_count": fa.get("skills_count") or ha.get("skills_count"),
                "cycles": fa.get("cycles") or ha.get("cycles"),
                "status": fa.get("status") or ha.get("status", "unknown"),
                "last_active": fa.get("last_active") or ha.get("last_active"),
            })

        return {
            "ok": True,
            "data": {"admirals": admirals_list, "count": len(admirals_list)},
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Admiral fleet admirals fetch failed: {e}")
        return {"ok": False, "error": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/api/admiral/fleet/history")
def admiral_fleet_history():
    """Recent skill execution history from Engine."""
    try:
        data = _admiral_get("/recent-executions", timeout=10)
        return {"ok": True, "data": data, "timestamp": datetime.now().isoformat()}
    except urllib.error.HTTPError as he:
        if he.code == 404:
            logger.info("Engine /recent-executions not found — returning stub")
            return {
                "ok": True,
                "data": {
                    "executions": [],
                    "note": "Endpoint /recent-executions not available on Engine. "
                            "Execution history may be accessed via DataPipeline "
                            "or the admiral_ledger.db directly.",
                },
                "timestamp": datetime.now().isoformat(),
            }
        raise
    except Exception as e:
        logger.error(f"Admiral fleet history fetch failed: {e}")
        return {"ok": False, "error": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/api/admiral/guides")
def admiral_guides():
    """Semantic system guide — static structured reference for the fleet dashboard."""
    guide = {
        "system_overview": (
            "39 admiraler, 360 skills, 5 domæner. Health score beregnes via "
            "DataPipeline (port 5599). Hvert domæne har sin root, DB, frontend "
            "og forbindelser. Pipeline v6.0.0 med 31 lag inkl. L31 Push Engine."
        ),
        "scoring": (
            "Skills scores via EMA. Ratio path (checks_passed/checks_total) "
            "giver 92-95. Observation path giver 82-92. Statiske ratios + "
            "pipeline-learned baselines, volatility og predictions. ML Scoring "
            "v2: HistGradientBoosting (28 features, R²=0.963) + IsolationForest "
            "+ skill-failure prediction + early warnings."
        ),
        "learning": (
            "Learning Room assembler multi-model research. Recall søger ChromaDB "
            "semantisk. Pre-flight wisdom injiceres før hver skill execution. "
            "Cross-agent learning deler indsigter på tværs af admiraler."
        ),
        "council": (
            "Council delibererer via groq→sambanova→together→cerebras fallback. "
            "Gate verdicts auto-markeres af Executor. Critical decisions bruger "
            "anthropic→groq→cerebras kæden. Lukket loop: Council→Executor→Enforcer."
        ),
        "architecture": (
            "Engine(5596), RealCouncil(5597), DataPipeline(5599), Nexus(5592), "
            "Executor(5593), EventBridge(5594), HQ(5555). Caddy reverse-proxy "
            "på 7780+5580. ChromaDB(8001), RabbitMQ(5672), Prometheus(9090), "
            "Grafana(3030), Loki(3100)."
        ),
        "admirals_guide": (
            "STRØMMEN: flow_audit hvert 30 min — fordøjelsesadmiral. "
            "KV1NT: primær orchestrator. VAGTEN: sikkerhed og overvågning. "
            "ODINSOEJE: deep system insight. COMMANDO: deployment og drift. "
            "NAVIGATOR: routing og pathfinding. SKULD: kapacitetsplanlægning. "
            "COSMIC: træning og academy. SEJRLISTE: evidence tracking. "
            "BOB: byggeri og integration. BEAST: overblik — ser alt, husker alt. "
            "HERMOD: ASK→ANSWER→ACT kommunikation. LOKE: eksperimenter og kaos. "
            "ARKIVET: langtidshukommelse. LOTSEN: guider nye admiraler."
        ),
    }

    return {"ok": True, "data": guide, "timestamp": datetime.now().isoformat()}
