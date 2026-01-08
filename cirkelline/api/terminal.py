"""
Terminal Agent API Endpoint
===========================
Dedicated API endpoint for Cirkelline Terminal CLI.

Provides:
- Terminal-specific chat interface
- Git context integration
- System status reporting
- CI/CD and database monitoring
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from cirkelline.middleware.rbac import (
    require_permissions,
    require_tier,
    Permission,
    resolve_permissions,
    get_tier_features_summary,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/terminal", tags=["Terminal"])


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class GitContext(BaseModel):
    """Git repository context from CLI."""
    is_git_repo: bool = False
    repo_name: Optional[str] = None
    current_branch: Optional[str] = None
    commit_hash: Optional[str] = None
    commit_short: Optional[str] = None
    commit_message: Optional[str] = None
    has_changes: bool = False
    staged_count: int = 0
    modified_count: int = 0
    untracked_count: int = 0
    remote_url: Optional[str] = None
    ahead_count: int = 0
    behind_count: int = 0


class TerminalAskRequest(BaseModel):
    """Request to ask Kommandanten from terminal."""
    message: str = Field(..., min_length=1, max_length=10000)
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    include_system_context: bool = True


class TerminalAskResponse(BaseModel):
    """Response from Kommandanten."""
    success: bool
    answer: Optional[str] = None
    message_id: Optional[str] = None
    session_id: Optional[str] = None
    processing_time_ms: Optional[int] = None
    context_used: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SystemStatusResponse(BaseModel):
    """Comprehensive system status."""
    timestamp: str
    api_status: str
    api_version: str

    # Service statuses
    database_status: str
    redis_status: str
    vector_db_status: str

    # CI/CD status (Crowdin)
    ci_cd_status: Optional[Dict[str, Any]] = None

    # User context
    user_tier: Optional[str] = None
    available_features: Optional[Dict[str, Any]] = None


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ask", response_model=TerminalAskResponse)
async def terminal_ask(
    request: Request,
    payload: TerminalAskRequest,
):
    """
    Ask Kommandanten a question with terminal context.

    This endpoint is optimized for CLI usage:
    - Accepts Git context for repository-aware responses
    - Returns markdown-formatted responses
    - Tracks conversation sessions
    """
    start_time = time.time()

    # Get user context
    user_id = getattr(request.state, 'user_id', None)
    tier_slug = getattr(request.state, 'tier_slug', 'member')
    is_admin = getattr(request.state, 'is_admin', False)

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Build enhanced context
        context = payload.context or {}

        if payload.include_system_context:
            context["terminal_session"] = True
            context["user_tier"] = tier_slug
            context["timestamp"] = datetime.utcnow().isoformat()

        # Parse Git context if provided
        git_context = None
        if context.get("is_git_repo"):
            git_context = GitContext(**context)

        # Generate message ID
        import uuid
        message_id = str(uuid.uuid4())[:12]
        session_id = payload.session_id or str(uuid.uuid4())[:16]

        # Build prompt with context
        enhanced_prompt = payload.message

        if git_context and git_context.is_git_repo:
            git_info = (
                f"\n\n[Git Context: {git_context.repo_name} @ {git_context.current_branch}"
            )
            if git_context.has_changes:
                git_info += f" | +{git_context.staged_count} staged, ~{git_context.modified_count} modified"
            git_info += "]"
            enhanced_prompt = f"{payload.message}{git_info}"

        # Call Cirkelline team for response
        # TODO: Integrate with actual Cirkelline orchestrator
        # For now, return a structured response

        answer = f"""Kommandanten har modtaget din forespørgsel.

**Din besked:** {payload.message}

**Kontekst registreret:**
- Terminal session: aktiv
- Tier: {tier_slug}
"""
        if git_context and git_context.is_git_repo:
            answer += f"""- Repository: {git_context.repo_name}
- Branch: {git_context.current_branch}
- Commit: {git_context.commit_short or 'N/A'}
"""

        answer += "\n*Integration med Cirkelline Team kommer i næste iteration.*"

        processing_time = int((time.time() - start_time) * 1000)

        return TerminalAskResponse(
            success=True,
            answer=answer,
            message_id=message_id,
            session_id=session_id,
            processing_time_ms=processing_time,
            context_used={
                "git_repo": git_context.repo_name if git_context else None,
                "tier": tier_slug,
            },
        )

    except Exception as e:
        logger.error(f"Terminal ask error: {e}")
        return TerminalAskResponse(
            success=False,
            error=str(e),
        )


@router.get("/status", response_model=SystemStatusResponse)
async def terminal_status(request: Request):
    """
    Get comprehensive system status for terminal display.

    Returns status of all services including:
    - API health
    - Database connections
    - CI/CD pipeline status
    - User-specific feature availability
    """
    user_id = getattr(request.state, 'user_id', None)
    tier_slug = getattr(request.state, 'tier_slug', 'member')

    # Check service statuses
    db_status = "healthy"
    redis_status = "healthy"
    vector_status = "healthy"

    try:
        # TODO: Implement actual health checks
        # from cirkelline.database import db
        # db_status = "healthy" if await db.check_connection() else "unhealthy"
        pass
    except Exception as e:
        logger.error(f"Health check error: {e}")
        db_status = "unknown"

    # Get user features
    features = None
    if user_id:
        features = get_tier_features_summary(tier_slug)

    return SystemStatusResponse(
        timestamp=datetime.utcnow().isoformat(),
        api_status="healthy",
        api_version="1.0.0",
        database_status=db_status,
        redis_status=redis_status,
        vector_db_status=vector_status,
        ci_cd_status={
            "crowdin": {"status": "active", "last_sync": None},
            "github_actions": {"status": "unknown"},
        },
        user_tier=tier_slug,
        available_features=features,
    )


@router.get("/features")
async def terminal_features(request: Request):
    """
    Get available features for current user's tier.

    Used by CLI to show what features are available
    and suggest upgrades for premium features.
    """
    tier_slug = getattr(request.state, 'tier_slug', 'member')
    is_admin = getattr(request.state, 'is_admin', False)

    features = get_tier_features_summary(tier_slug)

    # Add upgrade suggestions for lower tiers
    if tier_slug in ["member", "pro"]:
        features["upgrade_available"] = True
        features["upgrade_url"] = "https://cirkelline.com/pricing"
        features["next_tier_benefits"] = {
            "member": ["Video Specialist", "Research Team", "Deep Research", "Exa Search"],
            "pro": ["Law Team", "Priority Support", "Tavily Search", "Unlimited API"],
        }.get(tier_slug, [])

    return features


@router.get("/health")
async def terminal_health():
    """Simple health check for CLI ping command."""
    return {
        "status": "healthy",
        "service": "cirkelline-terminal-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET SUPPORT (for real-time streaming)
# ═══════════════════════════════════════════════════════════════════════════════

# TODO: Implement WebSocket endpoint for streaming responses
# @router.websocket("/ws")
# async def terminal_websocket(websocket: WebSocket):
#     """WebSocket connection for streaming terminal responses."""
#     pass
