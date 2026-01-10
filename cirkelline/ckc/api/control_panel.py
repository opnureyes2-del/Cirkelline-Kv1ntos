"""
CKC Control Panel API
=====================

Unified API for the CKC Control Panel (kommandocentral).
Provides endpoints for:
- System overview
- Task monitoring
- Agent status
- Learning room management
- HITL (Human-in-the-Loop) approvals
- Real-time event streaming

Usage:
    from fastapi import FastAPI
    from cirkelline.ckc.api.control_panel import router

    app = FastAPI()
    app.include_router(router, prefix="/api/ckc", tags=["CKC Control Panel"])
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== Pydantic Models ==========

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class HITLStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TaskSummary(BaseModel):
    task_id: str
    context_id: str
    prompt: str
    status: TaskStatus
    current_agent: Optional[str] = None
    progress: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentSummary(BaseModel):
    agent_id: str
    name: str
    role: str
    status: AgentStatus
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    uptime_seconds: float = 0.0
    last_active: Optional[datetime] = None


class RoomSummary(BaseModel):
    room_id: int
    name: str
    type: str
    status: str
    kommandant: Optional[str] = None
    agents_active: int = 0
    tasks_pending: int = 0
    last_activity: Optional[datetime] = None


class HITLRequest(BaseModel):
    request_id: str
    task_id: str
    agent_id: str
    action: str
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    status: HITLStatus = HITLStatus.PENDING
    created_at: datetime
    expires_at: Optional[datetime] = None


class HITLDecision(BaseModel):
    approved: bool
    reason: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


class SystemOverview(BaseModel):
    status: str
    version: str = "1.0.0"
    uptime_seconds: float
    active_tasks: int
    active_agents: int
    active_rooms: int
    pending_hitl: int
    database_status: str
    message_bus_status: str
    last_updated: datetime


# ========== In-Memory State (for demo - would use DB in production) ==========

class ControlPanelState:
    """In-memory state for the control panel."""

    def __init__(self):
        self._start_time = datetime.utcnow()
        self._tasks: Dict[str, TaskSummary] = {}
        self._agents: Dict[str, AgentSummary] = {}
        self._rooms: Dict[int, RoomSummary] = {}
        self._hitl_requests: Dict[str, HITLRequest] = {}
        self._event_subscribers: Set[WebSocket] = set()
        self._event_queue: asyncio.Queue = asyncio.Queue()

        # Initialize with demo data
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize with demo agent data."""
        agents = [
            ("tool_explorer", "Tool Explorer", "Analyserer og udforsker værktøjer"),
            ("creative_synthesizer", "Creative Synthesizer", "Kreativ problemløsning"),
            ("knowledge_architect", "Knowledge Architect", "Strukturerer viden"),
            ("virtual_world_builder", "Virtual World Builder", "Bygger virtuelle verdener"),
            ("quality_assurance", "Quality Assurance", "Sikrer kvalitet"),
        ]
        for agent_id, name, role in agents:
            self._agents[agent_id] = AgentSummary(
                agent_id=agent_id,
                name=name,
                role=role,
                status=AgentStatus.IDLE,
                tasks_completed=0,
                last_active=datetime.utcnow()
            )

        # Demo rooms
        rooms = [
            (1, "Projektledelse", "management"),
            (2, "Kreativ Zone", "creative"),
            (3, "Teknisk Lab", "technical"),
            (4, "Kvalitetskontrol", "qa"),
        ]
        for room_id, name, room_type in rooms:
            self._rooms[room_id] = RoomSummary(
                room_id=room_id,
                name=name,
                type=room_type,
                status="active",
                agents_active=0
            )

    @property
    def uptime(self) -> float:
        return (datetime.utcnow() - self._start_time).total_seconds()


# Global state
_state = ControlPanelState()


# ========== REST Endpoints ==========

@router.get("/overview", response_model=SystemOverview)
async def get_system_overview():
    """
    Get complete system overview.

    Returns high-level status of all CKC components.
    """
    # Get infrastructure status
    db_status = "connected"
    bus_status = "connected"

    try:
        from ..infrastructure import get_database
        db = await get_database()
        health = await db.health_check()
        db_status = health.get("status", "unknown")
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"

    try:
        from ..infrastructure import get_event_bus
        bus = await get_event_bus()
        health = await bus.health_check()
        bus_status = health.get("status", "unknown")
    except Exception as e:
        bus_status = f"error: {str(e)[:50]}"

    return SystemOverview(
        status="operational",
        uptime_seconds=_state.uptime,
        active_tasks=len([t for t in _state._tasks.values() if t.status == TaskStatus.RUNNING]),
        active_agents=len([a for a in _state._agents.values() if a.status == AgentStatus.BUSY]),
        active_rooms=len([r for r in _state._rooms.values() if r.status == "active"]),
        pending_hitl=len([h for h in _state._hitl_requests.values() if h.status == HITLStatus.PENDING]),
        database_status=db_status,
        message_bus_status=bus_status,
        last_updated=datetime.utcnow()
    )


@router.get("/tasks", response_model=List[TaskSummary])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    agent: Optional[str] = None,
    limit: int = Query(50, le=100)
):
    """
    List active and recent tasks.

    Args:
        status: Filter by status
        agent: Filter by current agent
        limit: Maximum number of tasks to return
    """
    tasks = list(_state._tasks.values())

    if status:
        tasks = [t for t in tasks if t.status == status]
    if agent:
        tasks = [t for t in tasks if t.current_agent == agent]

    # Sort by created_at descending
    tasks.sort(key=lambda t: t.created_at, reverse=True)

    return tasks[:limit]


@router.get("/tasks/{task_id}", response_model=TaskSummary)
async def get_task(task_id: str):
    """Get details of a specific task."""
    task = _state._tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """Pause a running task."""
    task = _state._tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Task is not running")

    task.status = TaskStatus.PAUSED
    task.updated_at = datetime.utcnow()

    # Persist to database
    try:
        from ..infrastructure import get_state_manager, TaskExecutionStatus
        state_mgr = await get_state_manager()
        await state_mgr.update_task_status(task_id, TaskExecutionStatus.PAUSED)
    except Exception as e:
        logger.warning(f"Failed to persist pause state: {e}")

    await _broadcast_event("task.paused", {"task_id": task_id})
    return {"status": "paused", "task_id": task_id}


@router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """Resume a paused task."""
    task = _state._tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Task is not paused")

    task.status = TaskStatus.RUNNING
    task.updated_at = datetime.utcnow()

    # Persist to database
    try:
        from ..infrastructure import get_state_manager, TaskExecutionStatus
        state_mgr = await get_state_manager()
        await state_mgr.update_task_status(task_id, TaskExecutionStatus.RUNNING)
    except Exception as e:
        logger.warning(f"Failed to persist resume state: {e}")

    await _broadcast_event("task.resumed", {"task_id": task_id})
    return {"status": "resumed", "task_id": task_id}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running or paused task."""
    task = _state._tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in (TaskStatus.RUNNING, TaskStatus.PAUSED, TaskStatus.PENDING):
        raise HTTPException(status_code=400, detail="Task cannot be cancelled")

    task.status = TaskStatus.FAILED  # Mark as failed (cancelled)
    task.updated_at = datetime.utcnow()

    # Persist to database
    try:
        from ..infrastructure import get_state_manager, TaskExecutionStatus
        state_mgr = await get_state_manager()
        await state_mgr.update_task_status(task_id, TaskExecutionStatus.CANCELLED, error="Cancelled by user")
    except Exception as e:
        logger.warning(f"Failed to persist cancel state: {e}")

    await _broadcast_event("task.cancelled", {"task_id": task_id})
    return {"status": "cancelled", "task_id": task_id}


@router.get("/agents", response_model=List[AgentSummary])
async def list_agents(
    status: Optional[AgentStatus] = None
):
    """
    List all agents with their current status.

    Args:
        status: Filter by status
    """
    agents = list(_state._agents.values())

    if status:
        agents = [a for a in agents if a.status == status]

    return agents


@router.get("/agents/{agent_id}", response_model=AgentSummary)
async def get_agent(agent_id: str):
    """Get details of a specific agent."""
    agent = _state._agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/agents/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """Get performance metrics for an agent."""
    agent = _state._agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "agent_id": agent_id,
        "tasks_completed": agent.tasks_completed,
        "tasks_failed": agent.tasks_failed,
        "success_rate": (
            agent.tasks_completed / (agent.tasks_completed + agent.tasks_failed)
            if (agent.tasks_completed + agent.tasks_failed) > 0
            else 0.0
        ),
        "uptime_seconds": agent.uptime_seconds,
        "status": agent.status.value
    }


@router.get("/rooms", response_model=List[RoomSummary])
async def list_rooms(
    status: Optional[str] = None
):
    """
    List all learning rooms.

    Args:
        status: Filter by status (active, inactive)
    """
    rooms = list(_state._rooms.values())

    if status:
        rooms = [r for r in rooms if r.status == status]

    return rooms


@router.get("/rooms/{room_id}", response_model=RoomSummary)
async def get_room(room_id: int):
    """Get details of a specific room."""
    room = _state._rooms.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


# ========== HITL Endpoints ==========

@router.get("/hitl/pending", response_model=List[HITLRequest])
async def list_pending_hitl():
    """List all pending HITL (Human-in-the-Loop) approval requests."""
    pending = [
        h for h in _state._hitl_requests.values()
        if h.status == HITLStatus.PENDING
    ]
    # Sort by created_at (oldest first)
    pending.sort(key=lambda h: h.created_at)
    return pending


@router.get("/hitl/{request_id}", response_model=HITLRequest)
async def get_hitl_request(request_id: str):
    """Get details of a specific HITL request."""
    request = _state._hitl_requests.get(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="HITL request not found")
    return request


@router.post("/hitl/{request_id}/approve")
async def approve_hitl(request_id: str, decision: HITLDecision):
    """
    Approve a HITL request.

    The agent will proceed with the action.
    """
    request = _state._hitl_requests.get(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="HITL request not found")
    if request.status != HITLStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is no longer pending")

    request.status = HITLStatus.APPROVED

    await _broadcast_event("hitl.approved", {
        "request_id": request_id,
        "task_id": request.task_id,
        "reason": decision.reason,
        "modifications": decision.modifications
    })

    return {
        "status": "approved",
        "request_id": request_id,
        "message": "Agent will proceed with the action"
    }


@router.post("/hitl/{request_id}/reject")
async def reject_hitl(request_id: str, decision: HITLDecision):
    """
    Reject a HITL request.

    The agent will not proceed and may request alternative actions.
    """
    request = _state._hitl_requests.get(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="HITL request not found")
    if request.status != HITLStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is no longer pending")

    request.status = HITLStatus.REJECTED

    await _broadcast_event("hitl.rejected", {
        "request_id": request_id,
        "task_id": request.task_id,
        "reason": decision.reason
    })

    return {
        "status": "rejected",
        "request_id": request_id,
        "message": "Agent will seek alternative approach"
    }


# ========== Infrastructure Endpoints ==========

@router.get("/infrastructure/status")
async def get_infrastructure_status():
    """Get status of all infrastructure components."""
    status = {
        "database": {"status": "unknown"},
        "message_bus": {"status": "unknown"},
        "connectors": {"status": "unknown"}
    }

    try:
        from ..infrastructure import get_database
        db = await get_database()
        status["database"] = await db.health_check()
    except Exception as e:
        status["database"] = {"status": "error", "error": str(e)}

    try:
        from ..infrastructure import get_event_bus
        bus = await get_event_bus()
        status["message_bus"] = await bus.health_check()
    except Exception as e:
        status["message_bus"] = {"status": "error", "error": str(e)}

    try:
        from ..infrastructure import get_connector_registry
        registry = await get_connector_registry()
        status["connectors"] = registry.get_overview()
    except Exception as e:
        status["connectors"] = {"status": "error", "error": str(e)}

    return status


@router.get("/infrastructure/connectors")
async def list_connectors():
    """List all registered connectors with their status."""
    try:
        from ..infrastructure import get_connector_registry
        registry = await get_connector_registry()
        return registry.list_connectors()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/status")
async def get_knowledge_status():
    """Get knowledge sync status."""
    try:
        from ..infrastructure import get_sync_status
        return await get_sync_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/stats")
async def get_state_stats():
    """Get state manager statistics."""
    try:
        from ..infrastructure import get_state_manager
        state_mgr = await get_state_manager()
        return await state_mgr.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/active-tasks")
async def get_active_persisted_tasks(kommandant_id: Optional[str] = None):
    """Get active tasks from persistent storage."""
    try:
        from ..infrastructure import get_state_manager
        state_mgr = await get_state_manager()
        tasks = await state_mgr.get_active_tasks(kommandant_id)
        return [task.to_dict() for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/state/recover/{kommandant_id}")
async def recover_tasks(kommandant_id: str):
    """Recover interrupted tasks for a kommandant."""
    try:
        from ..infrastructure import get_state_manager
        state_mgr = await get_state_manager()
        tasks = await state_mgr.recover_interrupted_tasks(kommandant_id)
        return {
            "recovered": len(tasks),
            "tasks": [task.to_dict() for task in tasks]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/checkpoints")
async def get_task_checkpoints(task_id: str, limit: int = Query(50, le=100)):
    """Get checkpoints for a specific task."""
    try:
        from ..infrastructure import get_state_manager
        state_mgr = await get_state_manager()
        checkpoints = await state_mgr.get_checkpoints(task_id, limit)
        return [cp.to_dict() for cp in checkpoints]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/specialists/metrics")
async def get_specialists_metrics(limit: int = Query(10, le=50)):
    """Get top performing specialists by success rate."""
    try:
        from ..infrastructure import get_state_manager
        state_mgr = await get_state_manager()
        specialists = await state_mgr.get_top_specialists(limit)
        return [s.to_dict() for s in specialists]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/specialists/{specialist_id}/metrics")
async def get_specialist_metrics(specialist_id: str):
    """Get metrics for a specific specialist."""
    try:
        from ..infrastructure import get_state_manager
        state_mgr = await get_state_manager()
        metrics = await state_mgr.get_specialist_metrics(specialist_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Specialist not found")
        return metrics.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== WebSocket Streaming ==========

async def _broadcast_event(event_type: str, data: Dict[str, Any]):
    """Broadcast event to all WebSocket subscribers."""
    message = json.dumps({
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    })

    disconnected = set()
    for ws in _state._event_subscribers:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)

    # Remove disconnected clients
    _state._event_subscribers -= disconnected


@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """
    Real-time event stream via WebSocket.

    Events include:
    - task.created, task.updated, task.completed, task.failed
    - agent.status_changed
    - hitl.requested, hitl.approved, hitl.rejected
    - room.activity
    """
    await websocket.accept()
    _state._event_subscribers.add(websocket)

    logger.info(f"WebSocket client connected. Total: {len(_state._event_subscribers)}")

    try:
        # Send initial state
        await websocket.send_json({
            "type": "connection.established",
            "data": {
                "uptime": _state.uptime,
                "active_tasks": len(_state._tasks),
                "active_agents": len([a for a in _state._agents.values() if a.status == AgentStatus.BUSY])
            },
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep connection alive and listen for commands
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle incoming commands
                try:
                    command = json.loads(data)
                    if command.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        pass
    finally:
        _state._event_subscribers.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(_state._event_subscribers)}")


# ========== Helper Functions ==========

async def create_task(
    task_id: str,
    context_id: str,
    prompt: str,
    kommandant_id: Optional[str] = None,
    room_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> TaskSummary:
    """Create a new task (called by orchestrator)."""
    task = TaskSummary(
        task_id=task_id,
        context_id=context_id,
        prompt=prompt[:200],  # Truncate for summary
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow(),
        metadata=metadata or {}
    )
    _state._tasks[task_id] = task

    # Persist to database
    try:
        from ..infrastructure import get_state_manager, TaskState, TaskExecutionStatus
        state_mgr = await get_state_manager()
        task_state = TaskState(
            task_id=task_id,
            kommandant_id=kommandant_id or context_id,
            room_id=room_id,
            status=TaskExecutionStatus.PENDING,
            prompt=prompt,
            context=metadata or {},
            started_at=datetime.utcnow(),
            metadata=metadata or {},
        )
        await state_mgr.save_task_state(task_state)
    except Exception as e:
        logger.warning(f"Failed to persist task state: {e}")

    await _broadcast_event("task.created", task.model_dump(mode="json"))
    return task


async def update_task_status(
    task_id: str,
    status: TaskStatus,
    current_agent: Optional[str] = None,
    progress: Optional[float] = None,
    error: Optional[str] = None
):
    """Update task status (called by agents)."""
    task = _state._tasks.get(task_id)
    if task:
        task.status = status
        task.updated_at = datetime.utcnow()
        if current_agent:
            task.current_agent = current_agent
        if progress is not None:
            task.progress = progress

        # Persist to database
        try:
            from ..infrastructure import get_state_manager, TaskExecutionStatus
            state_mgr = await get_state_manager()
            # Map TaskStatus to TaskExecutionStatus
            status_map = {
                TaskStatus.PENDING: TaskExecutionStatus.PENDING,
                TaskStatus.RUNNING: TaskExecutionStatus.RUNNING,
                TaskStatus.PAUSED: TaskExecutionStatus.PAUSED,
                TaskStatus.COMPLETED: TaskExecutionStatus.COMPLETED,
                TaskStatus.FAILED: TaskExecutionStatus.FAILED,
            }
            exec_status = status_map.get(status, TaskExecutionStatus.RUNNING)
            await state_mgr.update_task_status(task_id, exec_status, error)
        except Exception as e:
            logger.warning(f"Failed to persist task status: {e}")

        await _broadcast_event("task.updated", {
            "task_id": task_id,
            "status": status.value,
            "current_agent": current_agent,
            "progress": progress
        })


async def create_hitl_request(
    task_id: str,
    agent_id: str,
    action: str,
    description: str,
    context: Optional[Dict[str, Any]] = None,
    timeout_minutes: int = 30
) -> HITLRequest:
    """Create a HITL approval request."""
    import uuid
    request_id = f"hitl_{uuid.uuid4().hex[:12]}"

    request = HITLRequest(
        request_id=request_id,
        task_id=task_id,
        agent_id=agent_id,
        action=action,
        description=description,
        context=context or {},
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=timeout_minutes)
    )
    _state._hitl_requests[request_id] = request

    await _broadcast_event("hitl.requested", {
        "request_id": request_id,
        "task_id": task_id,
        "agent_id": agent_id,
        "action": action,
        "description": description
    })

    return request


# ========== MODEL SWITCHING ENDPOINTS (CKC-24) ==========
# Added 2026-01-09 by Kv1nt - Unblocks cirkelline-kv1ntos release

class ModelSwitchRequest(BaseModel):
    """Request to switch AI model."""
    provider: str = Field(..., description="Target model provider (gemini, claude, gpt4, llama, mistral)")
    reason: Optional[str] = Field(None, description="Reason for switch")
    initiated_by: str = Field("user", description="Who initiated: user, system, super_admin")


class ModelStatusResponse(BaseModel):
    """Status of a single AI model."""
    provider: str
    status: str
    is_active: bool
    health_score: float
    capabilities: List[str]
    gdpr_compliant: bool
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    rate_limit_rpm: int = 60


class ModelSwitchResponse(BaseModel):
    """Response after model switch."""
    success: bool
    previous_model: Optional[str]
    current_model: str
    switch_time_ms: float
    reason: Optional[str]


class ModelSwitchHistory(BaseModel):
    """History entry for model switch."""
    event_id: str
    from_model: Optional[str]
    to_model: str
    reason: str
    timestamp: datetime
    duration_ms: float
    success: bool
    initiated_by: str


# Model switching state (in-memory for now)
_model_state = {
    "current_model": "gemini",
    "switch_history": [],
    "models": {
        "gemini": {"status": "active", "health_score": 1.0, "gdpr_compliant": False},
        "claude": {"status": "available", "health_score": 1.0, "gdpr_compliant": True},
        "gpt4": {"status": "available", "health_score": 1.0, "gdpr_compliant": False},
        "llama": {"status": "available", "health_score": 0.9, "gdpr_compliant": True},
        "mistral": {"status": "available", "health_score": 0.95, "gdpr_compliant": True},
    }
}


@router.get("/models", response_model=List[ModelStatusResponse])
async def list_models():
    """List all available AI models with their status."""
    models = []
    for provider, data in _model_state["models"].items():
        models.append(ModelStatusResponse(
            provider=provider,
            status=data["status"],
            is_active=(provider == _model_state["current_model"]),
            health_score=data["health_score"],
            capabilities=["chat", "reasoning", "code"] if provider != "llama" else ["chat", "reasoning"],
            gdpr_compliant=data["gdpr_compliant"],
            cost_per_1k_input=0.075 if provider == "gemini" else 0.01,
            cost_per_1k_output=0.30 if provider == "gemini" else 0.03,
            rate_limit_rpm=1500 if provider == "gemini" else 60
        ))
    return models


@router.get("/models/current", response_model=ModelStatusResponse)
async def get_current_model():
    """Get the currently active AI model."""
    provider = _model_state["current_model"]
    data = _model_state["models"][provider]
    return ModelStatusResponse(
        provider=provider,
        status="active",
        is_active=True,
        health_score=data["health_score"],
        capabilities=["chat", "reasoning", "code"],
        gdpr_compliant=data["gdpr_compliant"],
        cost_per_1k_input=0.075,
        cost_per_1k_output=0.30,
        rate_limit_rpm=1500
    )


@router.post("/models/switch", response_model=ModelSwitchResponse)
async def switch_model(request: ModelSwitchRequest):
    """Switch to a different AI model (hot-swap)."""
    import uuid
    import time

    start_time = time.time()
    previous = _model_state["current_model"]
    target = request.provider.lower()

    # Validate target model
    if target not in _model_state["models"]:
        raise HTTPException(status_code=400, detail=f"Unknown model: {target}")

    if target == previous:
        return ModelSwitchResponse(
            success=True,
            previous_model=previous,
            current_model=target,
            switch_time_ms=0.0,
            reason="Already using this model"
        )

    # Perform switch
    _model_state["models"][previous]["status"] = "available"
    _model_state["models"][target]["status"] = "active"
    _model_state["current_model"] = target

    switch_time_ms = (time.time() - start_time) * 1000

    # Record history
    event = {
        "event_id": f"switch_{uuid.uuid4().hex[:8]}",
        "from_model": previous,
        "to_model": target,
        "reason": request.reason or request.initiated_by,
        "timestamp": datetime.utcnow().isoformat(),
        "duration_ms": switch_time_ms,
        "success": True,
        "initiated_by": request.initiated_by
    }
    _model_state["switch_history"].append(event)

    # Broadcast event
    await _broadcast_event("model.switched", {
        "from": previous,
        "to": target,
        "reason": request.reason,
        "initiated_by": request.initiated_by
    })

    logger.info(f"Model switched: {previous} -> {target} ({switch_time_ms:.2f}ms)")

    return ModelSwitchResponse(
        success=True,
        previous_model=previous,
        current_model=target,
        switch_time_ms=switch_time_ms,
        reason=request.reason
    )


@router.get("/models/{provider}", response_model=ModelStatusResponse)
async def get_model_status(provider: str):
    """Get status of a specific AI model."""
    provider = provider.lower()
    if provider not in _model_state["models"]:
        raise HTTPException(status_code=404, detail=f"Model not found: {provider}")

    data = _model_state["models"][provider]
    return ModelStatusResponse(
        provider=provider,
        status=data["status"],
        is_active=(provider == _model_state["current_model"]),
        health_score=data["health_score"],
        capabilities=["chat", "reasoning", "code"] if provider != "llama" else ["chat", "reasoning"],
        gdpr_compliant=data["gdpr_compliant"],
        cost_per_1k_input=0.075 if provider == "gemini" else 0.01,
        cost_per_1k_output=0.30 if provider == "gemini" else 0.03,
        rate_limit_rpm=1500 if provider == "gemini" else 60
    )


@router.get("/models/history", response_model=List[ModelSwitchHistory])
async def get_switch_history(limit: int = Query(50, le=100)):
    """Get history of model switches."""
    history = _model_state["switch_history"][-limit:]
    return [ModelSwitchHistory(
        event_id=e["event_id"],
        from_model=e["from_model"],
        to_model=e["to_model"],
        reason=e["reason"],
        timestamp=datetime.fromisoformat(e["timestamp"]),
        duration_ms=e["duration_ms"],
        success=e["success"],
        initiated_by=e["initiated_by"]
    ) for e in reversed(history)]


# ========== Module Exports ==========

__all__ = [
    "router",
    "create_task",
    "update_task_status",
    "create_hitl_request",
    "TaskStatus",
    "AgentStatus",
    "HITLStatus",
    "TaskSummary",
    "AgentSummary",
    "RoomSummary",
    "HITLRequest",
    "SystemOverview",
    # Model Switching (CKC-24)
    "ModelSwitchRequest",
    "ModelStatusResponse",
    "ModelSwitchResponse",
    "ModelSwitchHistory",
]
