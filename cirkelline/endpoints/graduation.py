"""
Agent Graduation Endpoint — Cosmic Library → Cirkelline Pipeline

Receives trained agents from Cosmic Library when they reach mastery (80%+).
Validates, stores in graduated_agents table, and publishes event.

POST /api/agents/import-from-cosmic
"""

import logging
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from cirkelline.database import db

_engine = create_engine(db.db_url, pool_size=3, max_overflow=5, pool_pre_ping=True)

logger = logging.getLogger(__name__)

router = APIRouter()


class GraduatedAgentRequest(BaseModel):
    """Payload from Cosmic Library's export_agent_to_cirkelline()"""
    name: str
    specialty: str = ""
    role: str = ""
    system_prompt: str = ""
    skills: List[str] = Field(default_factory=list)
    mastery_score: int = 0
    model: str = "gemini-2.5-flash"
    tools: List[str] = Field(default_factory=list)
    cosmic_library_id: Optional[str] = None
    training_complete: bool = False
    ready_for_production: bool = False


# Ensure table exists on import
_TABLE_CREATED = False


def _ensure_table():
    global _TABLE_CREATED
    if _TABLE_CREATED:
        return
    try:
        with _engine.connect() as conn:
            conn.execute(text("""
                CREATE SCHEMA IF NOT EXISTS ai;
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai.graduated_agents (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    specialty VARCHAR(255),
                    role VARCHAR(255),
                    system_prompt TEXT,
                    skills JSONB DEFAULT '[]',
                    mastery_score INTEGER,
                    model VARCHAR(255),
                    tools JSONB DEFAULT '[]',
                    cosmic_library_id VARCHAR(255) UNIQUE,
                    status VARCHAR(50) DEFAULT 'imported',
                    team_assignment VARCHAR(255),
                    imported_at TIMESTAMP DEFAULT NOW(),
                    activated_at TIMESTAMP
                );
            """))
            conn.commit()
            _TABLE_CREATED = True
            logger.info("ai.graduated_agents table ready")
    except Exception as e:
        logger.warning(f"Could not create graduated_agents table: {e}")


def _assign_team(specialty: str, skills: List[str]) -> str:
    """Assign graduated agent to a Cirkelline team based on specialty"""
    specialty_lower = specialty.lower()
    skills_str = " ".join(s.lower() for s in skills)

    if any(k in specialty_lower for k in ["law", "legal", "contract", "compliance"]):
        return "law_team"
    elif any(k in specialty_lower for k in ["research", "analysis", "data"]):
        return "research_team"
    elif any(k in specialty_lower for k in ["code", "program", "develop", "software"]):
        return "development_team"
    elif any(k in skills_str for k in ["creative", "writing", "content"]):
        return "creative_team"
    else:
        return "general_team"


def _publish_graduation_event(agent_name: str, agent_id: int, team: str):
    """Publish graduation event to RabbitMQ if available"""
    try:
        import pika
        connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost", 5672, credentials=pika.PlainCredentials("guest", "guest"))
        )
        channel = connection.channel()
        channel.exchange_declare(exchange="elle_integration_hub", exchange_type="topic", durable=True)

        event = {
            "event": "ckc.agent.graduated",
            "agent_name": agent_name,
            "agent_id": agent_id,
            "team_assignment": team,
            "timestamp": datetime.now().isoformat(),
            "source": "cirkelline-graduation"
        }
        channel.basic_publish(
            exchange="elle_integration_hub",
            routing_key="ckc.agent.graduated",
            body=json.dumps(event),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2)
        )
        connection.close()
        logger.info(f"Published ckc.agent.graduated event for {agent_name}")
    except Exception as e:
        logger.warning(f"Could not publish graduation event: {e}")


@router.post("/api/agents/import-from-cosmic")
async def import_agent_from_cosmic(agent: GraduatedAgentRequest):
    """
    Receive a graduated agent from Cosmic Library.

    Validates mastery_score >= 80, stores in ai.graduated_agents,
    assigns to a team, and publishes ckc.agent.graduated event.
    """
    _ensure_table()

    # Validate mastery
    if agent.mastery_score < 80:
        raise HTTPException(
            status_code=400,
            detail=f"Agent mastery_score {agent.mastery_score} is below minimum 80. Keep training."
        )

    team = _assign_team(agent.specialty, agent.skills)

    try:
        with _engine.connect() as conn:
            # Check for duplicate
            if agent.cosmic_library_id:
                existing = conn.execute(text(
                    "SELECT id FROM ai.graduated_agents WHERE cosmic_library_id = :cid"
                ), {"cid": agent.cosmic_library_id}).fetchone()
                if existing:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Agent with cosmic_library_id '{agent.cosmic_library_id}' already graduated"
                    )

            result = conn.execute(text("""
                INSERT INTO ai.graduated_agents
                    (name, specialty, role, system_prompt, skills, mastery_score,
                     model, tools, cosmic_library_id, status, team_assignment)
                VALUES
                    (:name, :specialty, :role, :system_prompt, :skills, :mastery_score,
                     :model, :tools, :cosmic_library_id, 'imported', :team)
                RETURNING id
            """), {
                "name": agent.name,
                "specialty": agent.specialty,
                "role": agent.role,
                "system_prompt": agent.system_prompt,
                "skills": json.dumps(agent.skills),
                "mastery_score": agent.mastery_score,
                "model": agent.model,
                "tools": json.dumps(agent.tools),
                "cosmic_library_id": agent.cosmic_library_id,
                "team": team,
            })
            agent_id = result.fetchone()[0]
            conn.commit()

        # Publish event (fire-and-forget)
        _publish_graduation_event(agent.name, agent_id, team)

        logger.info(f"Agent '{agent.name}' graduated: id={agent_id}, team={team}")

        return {
            "agent_id": agent_id,
            "team": team,
            "status": "imported",
            "message": f"Agent '{agent.name}' successfully graduated to Cirkelline ({team})"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import agent: {str(e)}")


@router.get("/api/agents/graduated")
async def list_graduated_agents():
    """List all graduated agents"""
    _ensure_table()
    try:
        with _engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT id, name, specialty, role, mastery_score, model, status, team_assignment, imported_at "
                "FROM ai.graduated_agents ORDER BY imported_at DESC"
            )).fetchall()

        return {
            "count": len(rows),
            "agents": [
                {
                    "id": r[0], "name": r[1], "specialty": r[2], "role": r[3],
                    "mastery_score": r[4], "model": r[5], "status": r[6],
                    "team_assignment": r[7], "imported_at": r[8].isoformat() if r[8] else None
                }
                for r in rows
            ]
        }
    except Exception as e:
        return {"count": 0, "agents": [], "error": str(e)}
