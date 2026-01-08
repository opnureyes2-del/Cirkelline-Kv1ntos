"""
CKC API Layer
=============

FastAPI routers for CKC Control Panel and related endpoints.

Usage:
    from fastapi import FastAPI
    from cirkelline.ckc.api import control_panel_router, folder_switcher_router

    app = FastAPI()
    app.include_router(control_panel_router, prefix="/api/ckc")
    app.include_router(folder_switcher_router, prefix="/api/ckc")

Version: v1.3.5 (Updated 2025-12-16 - Added Folder Switcher)
"""

from .control_panel import (
    router as control_panel_router,
    create_task,
    update_task_status,
    create_hitl_request,
    TaskStatus,
    AgentStatus,
    HITLStatus,
    TaskSummary,
    AgentSummary,
    RoomSummary,
    HITLRequest,
    SystemOverview,
)

from .folder_switcher import router as folder_switcher_router

__all__ = [
    # Routers
    "control_panel_router",
    "folder_switcher_router",
    # Functions
    "create_task",
    "update_task_status",
    "create_hitl_request",
    # Enums
    "TaskStatus",
    "AgentStatus",
    "HITLStatus",
    # Models
    "TaskSummary",
    "AgentSummary",
    "RoomSummary",
    "HITLRequest",
    "SystemOverview",
]
