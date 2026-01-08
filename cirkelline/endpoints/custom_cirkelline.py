"""
Custom Cirkelline Orchestrator Endpoint
========================================
Main orchestrator endpoint that handles the /teams/cirkelline/runs endpoint.
Includes session management, Google integration, streaming, delegation monitoring,
reasoning detection, retry logic, and Deep Research mode support.
"""

import os
import json
import time
import asyncio
import uuid
import re
from threading import Lock
from typing import Optional, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo  # ✅ v1.2.33: For user timezone conversion
from fastapi import APIRouter, Request, HTTPException, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy import text
from agno.exceptions import ModelProviderError

from cirkelline.config import logger
from cirkelline.middleware.middleware import _shared_engine
from cirkelline.database import db
from cirkelline.orchestrator.cirkelline_team import cirkelline
from cirkelline.integrations.google.google_oauth import get_user_google_credentials
from cirkelline.helpers.session_naming import attempt_session_naming
from cirkelline.middleware.middleware import log_activity
from cirkelline.workflows.triggers import check_and_trigger_optimization

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# METRICS TRACKING HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def calculate_token_costs(input_tokens: int, output_tokens: int) -> dict:
    """
    Calculate costs for Gemini 2.5 Flash (Tier 1) token usage.

    Pricing (per 1M tokens):
    - Input: $0.075
    - Output: $0.30

    Returns: dict with input_cost, output_cost, total_cost in USD
    """
    input_cost = (input_tokens / 1_000_000) * 0.075
    output_cost = (output_tokens / 1_000_000) * 0.30
    total_cost = input_cost + output_cost

    return {
        "input_cost": round(input_cost, 8),  # Keep precision for small values
        "output_cost": round(output_cost, 8),
        "total_cost": round(total_cost, 8)
    }

def create_metric_object(
    agent_id: str,
    agent_name: str,
    agent_type: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    model: str,
    message_preview: str,
    response_preview: str
) -> dict:
    """
    Create a standardized metric object for storage.

    Returns: Complete metric object with all fields including costs
    """
    costs = calculate_token_costs(input_tokens, output_tokens)

    return {
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent_id,
        "agent_name": agent_name,
        "agent_type": agent_type,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "model": model,
        "message_preview": message_preview[:100] if message_preview else "",
        "response_preview": response_preview[:100] if response_preview else "",
        "input_cost": costs["input_cost"],
        "output_cost": costs["output_cost"],
        "total_cost": costs["total_cost"]
    }

async def store_metrics_in_database(session_id: str, metric_object: dict):
    """
    Store metric object in agno_sessions.metrics JSONB array.
    Appends to existing array or creates new array if none exists.
    """
    try:
        # Use asyncio.to_thread to run database operation in thread pool
        def _store_metrics():
            with SQLAlchemySession(_shared_engine) as session:
                result = session.execute(
                    text("""
                        UPDATE ai.agno_sessions
                        SET metrics = COALESCE(metrics, '[]'::jsonb) || CAST(:new_metric AS jsonb)
                        WHERE session_id = :session_id
                    """),
                    {
                        "new_metric": json.dumps([metric_object]),
                        "session_id": session_id
                    }
                )
                session.commit()
                return result.rowcount

        rows_updated = await asyncio.to_thread(_store_metrics)

        if rows_updated > 0:
            logger.info(f"📊 Metrics stored: {metric_object['total_tokens']} tokens (${metric_object['total_cost']:.6f}) for {metric_object['agent_name']}")
        else:
            logger.warning(f"⚠️ No session found with ID {session_id[:8]}... to store metrics")
    except Exception as e:
        logger.error(f"❌ Failed to store metrics: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def capture_streaming_metrics(session_id: str, message: str):
    """
    Background task to capture metrics after streaming completes.
    Waits briefly for AGNO to persist run data, then extracts metrics.
    """
    try:
        # Wait 2 seconds for AGNO to persist run data
        await asyncio.sleep(2)

        logger.info(f"📊 Attempting to capture streaming metrics for session {session_id[:8]}...")

        # Query the most recent run from this session via AGNO's database
        # AGNO stores runs with metrics in agno_sessions table
        session_data = await asyncio.to_thread(
            lambda: SQLAlchemySession(_shared_engine).execute(
                text("""
                    SELECT session_data
                    FROM ai.agno_sessions
                    WHERE session_id = :session_id
                """),
                {"session_id": session_id}
            ).fetchone()
        )

        if session_data and session_data[0]:
            data = session_data[0]

            # AGNO stores runs in session_data.runs array
            if 'runs' in data and len(data['runs']) > 0:
                # Get the most recent run
                latest_run = data['runs'][-1]

                # Extract metrics from run (AGNO structure)
                if 'metrics' in latest_run and latest_run['metrics']:
                    metrics = latest_run['metrics']

                    # Metrics might be a dict or object - handle both cases
                    if isinstance(metrics, dict):
                        input_tokens = metrics.get('input_tokens', 0) or 0
                        output_tokens = metrics.get('output_tokens', 0) or metrics.get('response_tokens', 0) or 0
                        total_tokens = metrics.get('total_tokens', 0) or (input_tokens + output_tokens)
                        model = metrics.get('model', 'gemini-2.5-flash')
                    else:
                        # It's a Metrics object with attributes
                        input_tokens = getattr(metrics, 'input_tokens', 0) or 0
                        output_tokens = getattr(metrics, 'output_tokens', 0) or getattr(metrics, 'response_tokens', 0) or 0
                        total_tokens = getattr(metrics, 'total_tokens', 0) or (input_tokens + output_tokens)
                        model = getattr(metrics, 'model', 'gemini-2.5-flash') or 'gemini-2.5-flash'

                    if total_tokens > 0:
                        # Get response content from run
                        response_content = ""
                        if 'response' in latest_run:
                            if isinstance(latest_run['response'], dict):
                                response_content = latest_run['response'].get('content', '')
                            elif isinstance(latest_run['response'], str):
                                response_content = latest_run['response']

                        # Create metric object
                        metric_obj = create_metric_object(
                            agent_id="cirkelline",
                            agent_name="Cirkelline",
                            agent_type="team",
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=total_tokens,
                            model=model,
                            message_preview=message,
                            response_preview=response_content
                        )

                        # Store metrics
                        await store_metrics_in_database(session_id, metric_obj)

                        logger.info(f"✅ Streaming metrics captured: {total_tokens} tokens (input: {input_tokens}, output: {output_tokens})")
                    else:
                        logger.warning(f"⚠️ No token data in streaming metrics for session {session_id[:8]}")
                else:
                    logger.warning(f"⚠️ No metrics in latest run for session {session_id[:8]}")
            else:
                logger.warning(f"⚠️ No runs found in session data for {session_id[:8]}")
        else:
            logger.warning(f"⚠️ No session data found for {session_id[:8]}")

    except Exception as e:
        logger.error(f"❌ Failed to capture streaming metrics: {e}")
        import traceback
        logger.error(traceback.format_exc())

# ═══════════════════════════════════════════════════════════════
# RUN CANCELLATION TRACKING
# ═══════════════════════════════════════════════════════════════

# Active run tracking: { user_id: { run_id: session_id } }
_active_runs: Dict[str, Dict[str, str]] = {}
_active_runs_lock = Lock()

# Cancelled session tracking: { session_id: { "cancelled": True, "partial_content": "..." } }
_cancelled_sessions: Dict[str, Dict[str, Any]] = {}
_cancelled_sessions_lock = Lock()


def register_active_run(user_id: str, run_id: str, session_id: str) -> None:
    """Register a run as active for a user."""
    with _active_runs_lock:
        if user_id not in _active_runs:
            _active_runs[user_id] = {}
        _active_runs[user_id][run_id] = session_id
        logger.info(f"🏃 Registered active run: {run_id[:8]}... for user {user_id[:20]}...")


def unregister_active_run(user_id: str, run_id: str) -> None:
    """Unregister a run when it completes or is cancelled."""
    with _active_runs_lock:
        if user_id in _active_runs:
            _active_runs[user_id].pop(run_id, None)
            if not _active_runs[user_id]:
                del _active_runs[user_id]
        logger.info(f"✅ Unregistered run: {run_id[:8]}... for user {user_id[:20]}...")


def get_active_run_for_user(user_id: str, run_id: str) -> Optional[str]:
    """Get session_id for an active run, verifying user ownership."""
    with _active_runs_lock:
        user_runs = _active_runs.get(user_id, {})
        return user_runs.get(run_id)


def mark_session_cancelled(session_id: str, partial_content: str = "") -> None:
    """Mark that the last run in this session was cancelled."""
    with _cancelled_sessions_lock:
        _cancelled_sessions[session_id] = {
            "cancelled": True,
            "partial_content": partial_content[:500] if partial_content else ""  # Limit size
        }
        logger.info(f"🛑 Marked session {session_id[:8]}... as cancelled")


def get_and_clear_cancellation(session_id: str) -> Optional[Dict[str, Any]]:
    """Get cancellation info and clear it (one-time read)."""
    with _cancelled_sessions_lock:
        return _cancelled_sessions.pop(session_id, None)


# ═══════════════════════════════════════════════════════════════
# CUSTOM CIRKELLINE ENDPOINT (Main Orchestrator)
# ═══════════════════════════════════════════════════════════════

@router.post("/teams/cirkelline/runs")
async def cirkelline_with_filtering(
    request: Request,
    background_tasks: BackgroundTasks,
    message: str = Form(...),
    stream: bool = Form(False),  # Get stream param from frontend
    session_id: Optional[str] = Form(None),
    user_id: str = Form(...),
    deep_research: bool = Form(False),  # ✅ v1.2.24: Deep Research mode toggle
    timezone: Optional[str] = Form(None)  # ✅ v1.2.33: User timezone from browser
):
    """
    Custom Cirkelline endpoint with session_state-based knowledge filtering.
    User context is passed via session_state to FilteredKnowledgeSearchTool.

    v1.2.24: Added deep_research parameter for toggle between Quick Search and Deep Research modes.
    """

    # Get dependencies from JWT middleware (includes admin claims)
    dependencies = getattr(request.state, 'dependencies', {})

    # CRITICAL: Add user_id and user_type to dependencies
    # These will be passed to the knowledge retriever via **kwargs
    dependencies['user_id'] = user_id
    dependencies['user_type'] = dependencies.get('user_type', 'Regular')

    # Handle session_id
    session_is_new = False  # Track if this is a new session
    if not session_id:
        actual_session_id = str(uuid.uuid4())
        session_is_new = True
        logger.info(f"🆕 Generated NEW session ID: {actual_session_id}")
    else:
        actual_session_id = session_id

    logger.info("=" * 60)
    logger.info("🔍 CIRKELLINE WITH CUSTOM KNOWLEDGE RETRIEVER")
    logger.info(f"👤 User: {user_id[:20]}...")
    logger.info(f"📝 Message: {message[:50]}...")
    logger.info(f"🎯 Dependencies: {dependencies}")
    logger.info(f"📡 Stream: {stream}")
    logger.info(f"🔬 Deep Research: {deep_research}")  # ✅ Log research mode
    logger.info(f"🌍 Timezone: {timezone or 'UTC (default)'}") # ✅ Log timezone
    logger.info(f"✨ Session: {actual_session_id}")
    logger.info("=" * 60)

    # ═══════════════════════════════════════════════════════════════
    # v1.3.4: ANONYMOUS USER REJECTION - Account required
    # ═══════════════════════════════════════════════════════════════
    if user_id.startswith("anon-"):
        logger.warning(f"🚫 Anonymous user rejected: {user_id[:30]}...")
        raise HTTPException(
            status_code=401,
            detail="Account required. Please sign up or log in to use Cirkelline."
        )

    try:
        # Build session_state with user context for custom tool
        # ✅ v1.2.29: Extract tier information for user profile display
        user_type = dependencies.get('user_type', 'Regular')
        user_name = dependencies.get('user_name', 'User')
        tier_slug = dependencies.get('tier_slug', 'member')
        tier_level = dependencies.get('tier_level', 1)

        # Load existing session state if session exists
        existing_session_state = {}
        if not session_is_new:
            try:
                # ✅ v1.2.26 FIX: get_sessions() doesn't accept session_id parameter
                # Must filter manually after retrieving all sessions
                all_sessions_tuple = db.get_sessions(user_id=user_id, deserialize=False)
                all_sessions = all_sessions_tuple[0] if isinstance(all_sessions_tuple, tuple) else all_sessions_tuple
                matching_sessions = [s for s in all_sessions if s.get('session_id') == actual_session_id]

                if matching_sessions and len(matching_sessions) > 0:
                    session_data = matching_sessions[0]
                    if 'session_data' in session_data and session_data['session_data']:
                        existing_session_state = session_data['session_data'].get("session_state", {})
                        logger.info(f"📦 Loaded existing session state: {existing_session_state}")
            except Exception as e:
                logger.warning(f"Failed to load existing session state: {e}")

        # ═══════════════════════════════════════════════════════════════
        # SESSION STATE CONSTRUCTION
        # ═══════════════════════════════════════════════════════════════
        # Session state is a dictionary that flows through the entire agent execution.
        # It's accessible in tools (via run_context.session_state), instructions (via agent.session_state),
        # and is persisted to the database between runs within the same session.
        #
        # What we store in session_state:
        # - current_user_id: User ID from JWT (for knowledge filtering, personalization)
        # - current_user_type: Regular/Admin/Anonymous (controls tone, capabilities)
        # - current_user_name: Display name (e.g., "Ivo", "John") for personalized greetings
        # - current_tier_slug: Subscription tier (member/pro/business/elite/family)
        # - current_tier_level: Tier numeric level (1-5) for feature gating
        # - deep_research: Boolean flag (Quick Search vs Deep Research mode)
        # - user_custom_instructions: User's custom preferences (if they set any)
        #
        # Why this matters:
        # - Callable instructions (cirkelline/orchestrator/instructions.py) read these values
        #   to dynamically generate appropriate instructions based on user context
        # - Tools use current_user_id to filter knowledge base results (user isolation)
        # - deep_research flag determines whether to use search tools or delegate to Research Team
        #
        # AGNO Flow: session_state dict → passed to arun() → available in RunContext →
        # accessible in tools via run_context.session_state, instructions via agent.session_state
        # ═══════════════════════════════════════════════════════════════

        # ✅ v1.2.33: Get timezone from request OR fall back to user's saved preference in database
        user_timezone = timezone
        if not user_timezone:
            try:
                # Load from user's preferences JSONB in database
                tz_result = await asyncio.to_thread(
                    lambda: SQLAlchemySession(_shared_engine).execute(
                        text("SELECT preferences->>'timezone' FROM users WHERE id = :user_id"),
                        {"user_id": user_id}
                    ).fetchone()
                )
                if tz_result and tz_result[0]:
                    user_timezone = tz_result[0]
                    logger.info(f"🌍 Loaded timezone from database: {user_timezone}")
                else:
                    user_timezone = "UTC"
                    logger.info(f"🌍 No timezone in database, using default: UTC")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load timezone from database: {e}")
                user_timezone = "UTC"

        # ✅ v1.2.33: Calculate pre-formatted datetime in user's timezone for template syntax
        # This allows research_team and law_team to use {current_user_datetime} in instructions
        try:
            user_tz = ZoneInfo(user_timezone)
            user_datetime = datetime.now(user_tz).strftime('%A, %B %d, %Y at %H:%M')
        except Exception as e:
            logger.warning(f"⚠️ Invalid timezone '{user_timezone}', falling back to UTC: {e}")
            user_datetime = datetime.now().strftime('%A, %B %d, %Y at %H:%M')

        # ✅ Check if previous run in this session was cancelled (for Cirkelline awareness)
        cancellation_info = get_and_clear_cancellation(actual_session_id)
        last_run_was_cancelled = cancellation_info is not None

        # ✅ v1.2.29: Include user profile context for agent instructions
        # ✅ v1.2.33: Added timezone support with pre-formatted datetime
        session_state = {
            **existing_session_state,
            "current_user_id": user_id,
            "current_user_type": user_type,
            "current_user_name": user_name,
            "current_tier_slug": tier_slug,
            "current_tier_level": tier_level,
            "deep_research": deep_research,  # ✅ Pass deep_research flag to agent
            "current_user_timezone": user_timezone,  # ✅ v1.2.33: User timezone (raw)
            "current_user_datetime": user_datetime,   # ✅ v1.2.33: Pre-formatted datetime for template syntax
            "last_run_was_cancelled": last_run_was_cancelled  # ✅ Cancellation awareness
        }

        logger.info(f"🔍 Final session state: {session_state}")

        # Load user's custom instructions from database
        user_instructions = None
        try:
            result = await asyncio.to_thread(
                lambda: SQLAlchemySession(_shared_engine).execute(
                    text("SELECT preferences FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
            )

            if result and result[0]:
                preferences = result[0] if isinstance(result[0], dict) else json.loads(result[0])
                user_instructions = preferences.get('instructions', '').strip()
                if user_instructions:
                    logger.info(f"📝 User has custom instructions: {user_instructions[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to load user instructions: {e}")

        # Log session creation if this is a new session
        if session_is_new:
            await log_activity(
                request=request,
                user_id=user_id,
                action_type="session_create",
                success=True,
                status_code=200,
                target_resource_id=actual_session_id,
                resource_type="session",
                details={"first_message_preview": message[:100]}
            )
            logger.info(f"✅ Session creation logged: {actual_session_id}")

        # Log chat message activity
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="chat_message",
            success=True,
            status_code=200,
            target_resource_id=actual_session_id,
            resource_type="session",
            details={"message_preview": message[:100], "message_length": len(message), "stream": stream}
        )

        # Check if user has Google connected
        has_google = False
        google_creds = None

        try:
            result = await asyncio.to_thread(
                lambda: SQLAlchemySession(_shared_engine).execute(
                    text("SELECT id FROM google_tokens WHERE user_id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
            )

            if result:
                has_google = True
                google_creds = await get_user_google_credentials(user_id)
        except Exception as e:
            logger.warning(f"Error checking Google connection: {e}")

        # Build tools list dynamically
        tools = []

        if has_google and google_creds:
            # Import Google toolkits (correct import paths)
            # NOTE: GoogleCalendarTools REMOVED in v1.3.4 - now using unified calendar_tools
            # Calendar is handled by CirkellineCalendarTools (same DB as UI)
            from agno.tools.gmail import GmailTools
            from agno.tools.googlesheets import GoogleSheetsTools

            # Initialize toolkits with user's credentials
            gmail_tools = GmailTools(creds=google_creds, add_instructions=True)

            # v1.3.4: Calendar tools removed - using unified CirkellineCalendarTools instead
            # This ensures AI and UI use the SAME calendar database

            sheets_tools = GoogleSheetsTools(
                creds=google_creds,
                enable_read_sheet=True,    # Correct parameter names
                enable_create_sheet=True,
                enable_update_sheet=True,
                add_instructions=True
            )

            tools.extend([gmail_tools, sheets_tools])

            logger.info(f"✅ Loaded Google tools for user {user_id}")

            # Log Google tool usage to activity_logs
            try:
                await asyncio.to_thread(
                    lambda: SQLAlchemySession(_shared_engine).execute(
                        text("""
                            INSERT INTO activity_logs
                            (user_id, action_type, success, metadata)
                            VALUES (:user_id, :action_type, :success, :metadata)
                        """),
                        {
                            "user_id": user_id,
                            "action_type": "google_tool_usage",
                            "success": True,
                            "metadata": json.dumps({
                                "tools_available": ["gmail", "sheets"],  # v1.3.4: calendar removed, using unified calendar_tools
                                "session_id": actual_session_id
                            })
                        }
                    ).connection.commit()
                )
            except Exception as e:
                logger.error(f"Failed to log Google tool usage: {e}")

        # Add Google tools to cirkelline's tools list dynamically (if user has Google connected)
        # CRITICAL: Must add to team.tools BEFORE calling run(), not pass as parameter!
        original_tools = cirkelline.tools.copy() if cirkelline.tools else []

        # 🔥 v1.2.27: Remove search tools when deep_research=True to prevent tool errors (Double protection: remove tools + never mention in instructions)
        # 🔥 v1.3.3: Remove research/law teams when deep_research=False to prevent unwanted delegation
        original_members = cirkelline.members.copy() if cirkelline.members else []

        if deep_research:
            cirkelline.tools = [
                tool for tool in cirkelline.tools
                if not (tool.__class__.__name__ in ['ExaTools', 'TavilyTools'])
            ]
            logger.info(f"🔬 Deep Research Mode: Removed search tools (ExaTools, TavilyTools)")
            logger.info(f"📋 Remaining tools: {[tool.__class__.__name__ for tool in cirkelline.tools]}")
        else:
            # 🔥 v1.3.3 FIX: Quick Search Mode - Remove Research Team and Law Team from members
            # This prevents the model from delegating when it should use search tools directly
            cirkelline.members = [
                member for member in cirkelline.members
                if member.id not in ['research-team', 'law-team']
            ]
            logger.info(f"🔍 Quick Search Mode: Removed delegation teams (research-team, law-team)")
            logger.info(f"📋 Remaining members: {[member.id for member in cirkelline.members]}")

        if tools:
            logger.info(f"📎 Adding {len(tools)} Google tools to Cirkelline's tools list")
            cirkelline.tools.extend(tools)

        # v1.2.27: Add user custom instructions to session_state if they exist
        # Callable instructions will check session_state['user_custom_instructions'] via RunContext
        if user_instructions:
            logger.info(f"📝 Adding user custom instructions to session_state")
            session_state["user_custom_instructions"] = user_instructions

        logger.info(f"✅ Session prepared | deep_research={deep_research} | mode={'🔬 Deep Research' if deep_research else '🔍 Quick Search'}")
        logger.info(f"📋 Instructions: Callable function (will return different instructions based on session_state)")

        # ═══════════════════════════════════════════════════════════════
        # 🐛 AGNO BUG WORKAROUND: Manual session_state Assignment
        # ═══════════════════════════════════════════════════════════════
        # Problem: AGNO v2.2.13 Teams do NOT automatically set self.session_state during run()
        #          They only pass session_state to RunContext (internal execution context)
        #
        # Impact: Callable instructions (cirkelline/orchestrator/instructions.py) access
        #         session_state via agent.session_state (direct attribute access), NOT via RunContext
        #         Example: agent.session_state.get('deep_research', False) at line 45
        #
        # Why this matters:
        # - Cirkelline uses callable instructions: instructions=get_cirkelline_instructions
        # - These instructions are DYNAMIC - they return different instruction sets based on deep_research flag
        # - Deep Research Mode: Returns instructions WITHOUT search tool names (delegates to Research Team)
        # - Quick Search Mode: Returns instructions WITH search tool names (uses tools directly)
        # - See cirkelline/orchestrator/instructions.py:44-49 for session_state access pattern
        #
        # The Workaround:
        # Manually assign session_state to the Team instance BEFORE calling arun()
        # This makes it accessible to callable instructions via agent.session_state
        #
        # Execution Flow:
        # 1. We build session_state dict above (lines 316-324)
        # 2. We manually set cirkelline.session_state = session_state HERE
        # 3. We pass session_state to arun() below (line 507)
        # 4. During run, callable instructions access agent.session_state
        # 5. Instructions read deep_research flag and return appropriate instruction set
        #
        # Related Documentation:
        # - AGNO docs: https://docs.agno.com/basics/state/team/overview
        # - Deep Research fix: docs/26-CALLABLE-INSTRUCTIONS-DEEP-RESEARCH-FIX.md
        # - Session state in instructions: https://docs.agno.com/basics/state/agent/usage/session-state-in-instructions
        #
        # IMPORTANT: This workaround is CRITICAL for Deep Research mode to work properly.
        # Without it, callable instructions cannot access session_state, deep_research flag
        # defaults to False, and the wrong instruction set is returned (causing tool errors).
        # ═══════════════════════════════════════════════════════════════
        cirkelline.session_state = session_state
        logger.info(f"🔧 Workaround: Set cirkelline.session_state manually for callable instructions")

        if stream:
            # Streaming response with retry logic (✅ ASYNC for concurrent requests)
            async def event_generator():
                max_retries = 3
                retry_count = 0

                # ═══ Delegation Freeze Detection ═══
                delegation_announced = False
                delegation_executed = False
                tool_calls_count = 0
                announcement_time = None
                last_event_time = time.time()

                # ═══ Run Cancellation Tracking ═══
                _run_registered = False
                _current_run_id = None

                try:
                    while retry_count <= max_retries:
                        try:
                            # ✅ TIMEOUT PROTECTION: Wrap streaming with 120-second timeout to prevent indefinite hangs
                            # Uses asyncio.timeout() (Python 3.11+) which is the cleanest pattern for async generators
                            async with asyncio.timeout(120):
                                # ✅ ASYNC: Use arun() + async for to enable concurrent request processing
                                async for event in cirkelline.arun(
                                    input=message,
                                    stream=True,
                                    stream_events=True,          # ✅ AGNO Official: Stream ALL internal process events
                                    stream_member_events=True,   # ✅ AGNO Official: Stream member agent events (default True)
                                    session_id=actual_session_id,
                                    user_id=user_id,
                                    dependencies=dependencies,
                                    # ═══ SESSION STATE PARAMETER ═══
                                    # This parameter passes the session_state dict into AGNO's execution context (RunContext).
                                    # It contains: user context (user_id, user_type, user_name, tier info) + deep_research flag
                                    #
                                    # What happens with it during execution:
                                    # 1. AGNO creates RunContext and stores session_state there
                                    # 2. Tools access it via run_context.session_state (standard AGNO pattern)
                                    # 3. Callable instructions access it via agent.session_state (our workaround at line 510)
                                    # 4. AGNO persists it to database after run completes (for session continuity)
                                    # 5. Next run in same session loads it from database and merges with new values
                                    #
                                    # Key distinction:
                                    # - Passing it HERE makes it available in RunContext (for tools)
                                    # - Setting agent.session_state at line 510 makes it available to callable instructions
                                    # - BOTH are necessary for our architecture to work properly
                                    #
                                    # Related: See session_state construction at lines 316-324, workaround at lines 473-511
                                    # ═══════════════════════════════
                                    session_state=session_state
                                    # NOTE: Google tools already added to cirkelline.tools above
                                ):
                                    event_type = getattr(event, 'event', 'unknown')
                                    event_data = event.to_dict()

                                    # ✅ AGNO Official: Extract identification fields from events
                                    team_id = event_data.get('team_id', None)
                                    team_name = event_data.get('team_name', None)
                                    agent_id = event_data.get('agent_id', None)
                                    agent_name = event_data.get('agent_name', None)
                                    run_id = event_data.get('run_id', None)
                                    parent_run_id = event_data.get('parent_run_id', None)

                                    # ═══ Register Run for Cancellation Tracking ═══
                                    if run_id and not _run_registered:
                                        register_active_run(user_id, run_id, actual_session_id)
                                        _run_registered = True
                                        _current_run_id = run_id

                                    # ═══════════════════════════════════════════════════════════════
                                    # HUMAN-IN-THE-LOOP (HITL) DETECTION
                                    # When agent calls get_user_input or requires confirmation,
                                    # the run pauses and we need to send schema to frontend
                                    # ═══════════════════════════════════════════════════════════════
                                    is_paused = getattr(event, 'is_paused', False)
                                    if is_paused:
                                        logger.info(f"⏸️ HITL: Run paused - detecting requirements")

                                        # Extract requirements from the event
                                        active_requirements = getattr(event, 'active_requirements', [])
                                        tools = getattr(event, 'tools', [])
                                        event_run_id = getattr(event, 'run_id', run_id)

                                        # Build the paused event data
                                        paused_data = {
                                            "event": "paused",
                                            "run_id": event_run_id,
                                            "session_id": actual_session_id,
                                            "requirements": []
                                        }

                                        # Process active requirements
                                        for req in active_requirements:
                                            req_data = {
                                                "needs_user_input": getattr(req, 'needs_user_input', False),
                                                "needs_confirmation": getattr(req, 'needs_confirmation', False),
                                                "is_external_tool_execution": getattr(req, 'is_external_tool_execution', False),
                                                "user_input_schema": []
                                            }

                                            # Extract user input schema if present
                                            if req_data["needs_user_input"]:
                                                schema = getattr(req, 'user_input_schema', [])
                                                for field in schema:
                                                    req_data["user_input_schema"].append({
                                                        "name": getattr(field, 'name', getattr(field, 'field_name', '')),
                                                        "field_type": getattr(field, 'field_type', 'str'),
                                                        "description": getattr(field, 'description', getattr(field, 'field_description', '')),
                                                        "value": getattr(field, 'value', None)
                                                    })
                                                logger.info(f"⏸️ HITL: User input required - {len(req_data['user_input_schema'])} fields")

                                            # Extract tool info for confirmation
                                            if req_data["needs_confirmation"]:
                                                tool_exec = getattr(req, 'tool_execution', None)
                                                if tool_exec:
                                                    req_data["tool_name"] = getattr(tool_exec, 'tool_name', '')
                                                    req_data["tool_args"] = getattr(tool_exec, 'tool_args', {})
                                                logger.info(f"⏸️ HITL: Confirmation required for tool")

                                            paused_data["requirements"].append(req_data)

                                        # Also check tools directly (alternative AGNO pattern)
                                        if not paused_data["requirements"] and tools:
                                            for tool in tools:
                                                # Check for tools requiring user input
                                                if getattr(tool, 'requires_user_input', False):
                                                    schema = getattr(tool, 'user_input_schema', [])
                                                    tool_data = {
                                                        "needs_user_input": True,
                                                        "needs_confirmation": False,
                                                        "tool_call_id": getattr(tool, 'tool_call_id', ''),
                                                        "tool_name": getattr(tool, 'tool_name', ''),
                                                        "user_input_schema": []
                                                    }
                                                    for field in schema:
                                                        tool_data["user_input_schema"].append({
                                                            "name": getattr(field, 'name', getattr(field, 'field_name', '')),
                                                            "field_type": getattr(field, 'field_type', 'str'),
                                                            "description": getattr(field, 'description', getattr(field, 'field_description', '')),
                                                            "value": getattr(field, 'value', None)
                                                        })
                                                    paused_data["requirements"].append(tool_data)
                                                    logger.info(f"⏸️ HITL: Tool {tool_data['tool_name']} requires user input")

                                        # Send paused event to frontend
                                        logger.info(f"⏸️ HITL: Sending paused event to frontend with {len(paused_data['requirements'])} requirements")
                                        yield f"event: paused\ndata: {json.dumps(paused_data)}\n\n"

                                        # Break the streaming loop - frontend will call continue endpoint
                                        break

                                    # ═══ Delegation Freeze Monitoring ═══
                                    last_event_time = time.time()

                                    # Track delegation announcements in messages
                                    if event_type in ['RunResponse', 'response', 'agent_response']:
                                        content = event_data.get('content', '')
                                        if isinstance(content, str) and content:
                                            # Detect delegation announcement phrases
                                            delegation_phrases = ["I'll", "I will", "I'm going to", "Let me have"]
                                            team_words = ['team', 'specialist', 'delegate', 'have them', 'research team', 'law team']
                                            has_delegation_phrase = any(phrase in content for phrase in delegation_phrases)
                                            has_team_word = any(word in content.lower() for word in team_words)

                                            if has_delegation_phrase and has_team_word:
                                                delegation_announced = True
                                                announcement_time = time.time()
                                                logger.info(f"📢 DELEGATION ANNOUNCEMENT DETECTED: {content[:150]}...")

                                    # Track tool executions
                                    if event_type in ['ToolCallStarted', 'TeamToolCallStarted', 'tool_call_started', 'tool_call']:
                                        tool_calls_count += 1
                                        tool_name = event_data.get('tool_name', '')

                                        if 'delegate' in tool_name.lower():
                                            delegation_executed = True
                                            logger.info(f"✅ DELEGATION EXECUTED: {tool_name}")

                                    # Check for stuck state (announcement without execution)
                                    if delegation_announced and not delegation_executed and announcement_time:
                                        time_since_announcement = time.time() - announcement_time

                                        if time_since_announcement > 10:  # 10 second timeout
                                            logger.error(f"🚨 DELEGATION FREEZE DETECTED!")
                                            logger.error(f"   Announced at: {announcement_time}")
                                            logger.error(f"   Current time: {time.time()}")
                                            logger.error(f"   Time since announcement: {time_since_announcement:.2f}s")
                                            logger.error(f"   Tool calls: {tool_calls_count}")
                                            logger.error(f"   Delegation executed: {delegation_executed}")

                                            # Send error to frontend
                                            error_event = {
                                                "event": "error",
                                                "data": json.dumps({
                                                    "error": "Delegation freeze detected - team announced but not executed",
                                                    "details": f"Waited {int(time_since_announcement)}s with no delegation tool call",
                                                    "recovery": "Try sending your message again",
                                                    "debug_info": {
                                                        "tool_calls": tool_calls_count,
                                                        "delegation_executed": delegation_executed
                                                    }
                                                })
                                            }
                                            yield f"event: {error_event['event']}\ndata: {error_event['data']}\n\n"

                                            # Break out of event loop to stop waiting
                                            break

                                    # 🧠 REASONING DETECTION: Check if this is a reasoning tool call
                                    is_reasoning_event = False
                                    reasoning_content = None

                                    # Check for tool_call events with think/analyze
                                    if event_type in ['tool_call', 'ToolCallStarted', 'tool_call_started']:
                                        tool_name = event_data.get('tool_name', '')
                                        tool_args = event_data.get('tool_args', {})
                                        tool_output = event_data.get('tool_output', '')

                                        # Detect reasoning tools
                                        if tool_name in ['think', 'analyze']:
                                            is_reasoning_event = True
                                            # Extract reasoning content from tool args or output
                                            if tool_args and 'thought' in tool_args:
                                                reasoning_content = tool_args['thought']
                                            elif tool_output:
                                                reasoning_content = tool_output

                                            # Add reasoning flag to event data
                                            event_data['is_reasoning'] = True
                                            event_data['reasoning_content'] = reasoning_content

                                            logger.info(f"🧠 REASONING DETECTED: {tool_name} | Source: {agent_name or team_name} | Content: {reasoning_content[:100] if reasoning_content else 'None'}...")

                                    # 🔍 Enhanced logging with AGNO official fields
                                    content_preview = ""
                                    if 'content' in event_data and event_data['content']:
                                        if isinstance(event_data['content'], str):
                                            content_preview = event_data['content'][:80] + "..." if len(event_data['content']) > 80 else event_data['content']
                                        else:
                                            content_preview = str(type(event_data['content']))

                                    # Log with full attribution
                                    source = team_name if team_name else (agent_name if agent_name else "Unknown")
                                    logger.info(f"🔍 EVENT: {event_type} | Source: {source} | Run: {run_id} | Parent: {parent_run_id} | Content: {content_preview}")

                                    # 📊 EXTRACT METRICS FROM COMPLETION EVENTS
                                    # According to AGNO docs, RunCompletedEvent and TeamRunCompletedEvent have metrics attribute
                                    if event_type in ['TeamRunCompleted', 'RunCompleted', 'run_completed', 'team_run_completed']:
                                        logger.info(f"🔍 COMPLETION EVENT DETECTED: {event_type}")

                                        if 'metrics' in event_data and event_data['metrics']:
                                            try:
                                                metrics_data = event_data['metrics']
                                                logger.info(f"📊 METRICS FOUND IN COMPLETION EVENT")

                                                # Extract token counts from metrics object
                                                input_tokens = metrics_data.get('input_tokens', 0) or 0
                                                output_tokens = metrics_data.get('output_tokens', 0) or 0
                                                total_tokens = metrics_data.get('total_tokens', 0) or (input_tokens + output_tokens)
                                                model = metrics_data.get('model', 'gemini-2.5-flash') or 'gemini-2.5-flash'

                                                # Calculate costs using existing helper function
                                                costs = calculate_token_costs(input_tokens, output_tokens)

                                                # Create MetricsUpdate event
                                                metrics_event = {
                                                    'event': 'MetricsUpdate',
                                                    'metrics': {
                                                        'input_tokens': input_tokens,
                                                        'output_tokens': output_tokens,
                                                        'total_tokens': total_tokens,
                                                        'input_cost': costs['input_cost'],
                                                        'output_cost': costs['output_cost'],
                                                        'total_cost': costs['total_cost'],
                                                        'model': model
                                                    },
                                                    'agent_id': event_data.get('agent_id', 'cirkelline'),
                                                    'agent_name': event_data.get('agent_name', team_name or agent_name or 'Cirkelline'),
                                                    'team_id': event_data.get('team_id'),
                                                    'team_name': event_data.get('team_name'),
                                                    'run_id': event_data.get('run_id'),
                                                    'parent_run_id': event_data.get('parent_run_id'),
                                                    'created_at': int(time.time() * 1000)
                                                }

                                                # Yield metrics event to frontend immediately after completion
                                                serialized_metrics = serialize_event_data(metrics_event)
                                                yield f"event: MetricsUpdate\ndata: {json.dumps(serialized_metrics)}\n\n"
                                                logger.info(f"📊 Sent MetricsUpdate: {total_tokens} tokens (input: {input_tokens}, output: {output_tokens}, cost: ${costs['total_cost']:.6f}) for {event_data.get('agent_name', 'Cirkelline')}")
                                            except Exception as e:
                                                logger.error(f"❌ Failed to process metrics from completion event: {e}")
                                                import traceback
                                                logger.error(traceback.format_exc())
                                        else:
                                            logger.warning(f"⚠️ No metrics in completion event: {event_type}")

                                    # 🧠 ENHANCED LOGGING FOR REASONING EVENTS
                                    if event_type in ['ReasoningStep', 'TeamReasoningStep', 'ReasoningStarted', 'ReasoningCompleted']:
                                        logger.info(f"🧠 REASONING EVENT DETECTED: {event_type}")
                                        logger.info(f"   Agent/Team: {agent_name or team_name}")
                                        logger.info(f"   Event data keys: {list(event_data.keys())}")
                                        if 'content' in event_data and event_data['content']:
                                            logger.info(f"   Content type: {type(event_data['content'])}")
                                            if isinstance(event_data['content'], dict):
                                                logger.info(f"   Content keys: {list(event_data['content'].keys())}")
                                                if 'title' in event_data['content']:
                                                    logger.info(f"   Title: {event_data['content'].get('title')}")
                                                if 'reasoning' in event_data['content']:
                                                    reasoning_text = event_data['content'].get('reasoning', '')
                                                    logger.info(f"   Reasoning: {reasoning_text[:200]}...")
                                        if 'reasoning_content' in event_data:
                                            logger.info(f"   Reasoning content (formatted): {event_data.get('reasoning_content', '')[:200]}...")

                                    # Send ALL events to frontend with full AGNO context
                                    # Convert datetime objects to ISO strings for JSON serialization
                                    def serialize_event_data(data):
                                        """Recursively convert datetime objects to ISO strings"""
                                        if isinstance(data, dict):
                                            return {k: serialize_event_data(v) for k, v in data.items()}
                                        elif isinstance(data, list):
                                            return [serialize_event_data(item) for item in data]
                                        elif isinstance(data, datetime):
                                            return data.isoformat()
                                        else:
                                            return data

                                    # ✅ ERROR HANDLING: Wrap JSON serialization and yield to prevent stream crashes
                                    # Following AGNO best practices: catch exceptions from risky operations (JSON serialization)
                                    # If serialization fails, log error and continue to next event (don't crash entire stream)
                                    try:
                                        serialized_data = serialize_event_data(event_data)
                                        yield f"event: {event_type}\ndata: {json.dumps(serialized_data)}\n\n"
                                    except (TypeError, ValueError, AttributeError) as e:
                                        # JSON serialization error or attribute access error
                                        logger.error(f"❌ Event serialization error for {event_type}: {e}")
                                        logger.error(f"   Event data keys: {list(event_data.keys())}")
                                        # Continue to next event - don't crash the stream
                                        continue
                                    except Exception as e:
                                        # Unexpected error - log and continue
                                        logger.error(f"❌ Unexpected event processing error for {event_type}: {e}")
                                        import traceback
                                        logger.error(traceback.format_exc())
                                        # Continue to next event - don't crash the stream
                                        continue

                            # ✅ Metrics are now extracted from completion events during streaming (see lines 586-635)
                            # No need to access cirkelline.last_run.metrics after streaming completes

                            # If we get here, the run completed successfully
                            break

                        except TimeoutError:
                            # ✅ TIMEOUT HANDLER: Request exceeded 120-second timeout
                            logger.error(f"⏱️ Request timed out after 120 seconds for session {actual_session_id[:8]}...")
                            logger.error(f"   Message: {message[:100]}...")
                            logger.error(f"   Deep Research: {deep_research}")

                            # Send user-friendly timeout error to frontend
                            timeout_message = "Request timed out after 2 minutes. This query may be too complex. Try simplifying your question or enabling Deep Research mode for better results."
                            yield f"event: error\ndata: {json.dumps({'event': 'error', 'error': timeout_message, 'type': 'timeout', 'timeout_seconds': 120})}\n\n"

                            # Log timeout activity
                            await log_activity(
                                request=request,
                                user_id=user_id,
                                action_type="chat_message",
                                success=False,
                                status_code=408,  # Request Timeout
                                error_message="Request timeout after 120 seconds",
                                error_type="TimeoutError",
                                target_resource_id=actual_session_id,
                                resource_type="session",
                                details={"message_preview": message[:100], "deep_research": deep_research}
                            )

                            break  # Exit retry loop on timeout

                        except (ModelProviderError, Exception) as e:
                            error_str = str(e)
                            is_rate_limit = '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower()

                            if is_rate_limit and retry_count < max_retries:
                                # Extract retry delay from error message
                                retry_delay = 5  # Default delay
                                match = re.search(r'retry in (\d+(?:\.\d+)?)', error_str, re.IGNORECASE)
                                if match:
                                    retry_delay = float(match.group(1))
                                else:
                                    # Exponential backoff if no delay specified
                                    retry_delay = min(5 * (2 ** retry_count), 60)

                                retry_count += 1
                                logger.warning(f"⚠️ Rate limit hit (attempt {retry_count}/{max_retries}). Retrying in {retry_delay}s...")

                                # Send retry status to UI
                                retry_message = f'Rate limit reached. Retrying in {int(retry_delay)} seconds... (Attempt {retry_count}/{max_retries})'
                                yield f"event: retry\ndata: {json.dumps({'event': 'retry', 'attempt': retry_count, 'max_retries': max_retries, 'delay': retry_delay, 'message': retry_message})}\n\n"

                                # Wait before retrying
                                time.sleep(retry_delay)
                                continue
                            else:
                                # Either not a rate limit error, or max retries exceeded
                                if retry_count >= max_retries:
                                    error_message = f"Maximum retries exceeded ({max_retries} attempts). The service is experiencing high load. Please try again in a few moments."
                                    logger.error(f"❌ {error_message}")
                                else:
                                    error_message = f"An error occurred: {error_str}"
                                    logger.error(f"❌ Streaming error: {e}")
                                    logger.exception(e)

                                # Send error to UI
                                yield f"event: error\ndata: {json.dumps({'event': 'error', 'error': error_message, 'type': 'rate_limit' if is_rate_limit else 'general', 'retries': retry_count})}\n\n"
                                break

                except Exception as e:
                    # Catch-all for any unexpected errors
                    logger.error(f"❌ Unexpected streaming error: {e}")
                    logger.exception(e)
                    unexpected_error_msg = f'An unexpected error occurred: {str(e)}'
                    yield f"event: error\ndata: {json.dumps({'event': 'error', 'error': unexpected_error_msg, 'type': 'unexpected'})}\n\n"
                finally:
                    # ═══ Unregister Run from Cancellation Tracking ═══
                    if _run_registered and _current_run_id:
                        unregister_active_run(user_id, _current_run_id)

                    # CRITICAL: Restore original tools and members (prevent leakage between requests)
                    cirkelline.tools = original_tools
                    cirkelline.members = original_members
                    logger.info("🧹 Restored original tools and members after stream")

            # Schedule background tasks (run after stream completes)
            # Note: Messages added during stream, so task checks count when it runs
            background_tasks.add_task(attempt_session_naming, actual_session_id)
            logger.info(f"📋 Scheduled session naming background task for session {actual_session_id[:8]}...")

            # Schedule metrics capture for streaming (waits 2s for AGNO to persist run data)
            background_tasks.add_task(capture_streaming_metrics, actual_session_id, message)
            logger.info(f"📊 Scheduled streaming metrics capture task for session {actual_session_id[:8]}...")

            # Schedule auto-trigger check for memory optimization (non-blocking)
            background_tasks.add_task(check_and_trigger_optimization, user_id)
            logger.info(f"🔄 Scheduled auto-trigger check for user {user_id[:8]}...")

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Non-streaming response (✅ ASYNC: Use arun() + await for concurrent request processing)
            try:
                # ✅ TIMEOUT PROTECTION: Wrap with 120-second timeout to prevent indefinite hangs
                async with asyncio.timeout(120):
                    response = await cirkelline.arun(
                        input=message,
                        stream=False,
                        session_id=actual_session_id,
                        user_id=user_id,
                        dependencies=dependencies,
                        # ═══ SESSION STATE PARAMETER ═══
                        # Same session_state dict as streaming endpoint (see lines 541-559 for full documentation)
                        # Contains user context + deep_research flag, accessible in tools via run_context.session_state
                        # and in callable instructions via agent.session_state (workaround at line 510)
                        # ═══════════════════════════════
                        session_state=session_state
                        # NOTE: Google tools already added to cirkelline.tools above
                    )
            except TimeoutError:
                # ✅ TIMEOUT HANDLER: Request exceeded 120-second timeout
                logger.error(f"⏱️ Non-streaming request timed out after 120 seconds for session {actual_session_id[:8]}...")
                logger.error(f"   Message: {message[:100]}...")
                logger.error(f"   Deep Research: {deep_research}")

                # Log timeout activity
                await log_activity(
                    request=request,
                    user_id=user_id,
                    action_type="chat_message",
                    success=False,
                    status_code=408,  # Request Timeout
                    error_message="Request timeout after 120 seconds",
                    error_type="TimeoutError",
                    target_resource_id=actual_session_id,
                    resource_type="session",
                    details={"message_preview": message[:100], "deep_research": deep_research, "stream": False}
                )

                # Restore original tools and members before raising exception
                cirkelline.tools = original_tools
                cirkelline.members = original_members

                # Return timeout error response
                raise HTTPException(
                    status_code=408,
                    detail="Request timed out after 2 minutes. This query may be too complex. Try simplifying your question or enabling Deep Research mode for better results."
                )

            # CRITICAL: Restore original tools and members (prevent leakage between requests)
            cirkelline.tools = original_tools
            cirkelline.members = original_members
            logger.info("🧹 Restored original tools and members after non-streaming request")

            # ═══ METRICS CAPTURE (NON-STREAMING) ═══
            # Extract metrics from response and store in database
            if response and hasattr(response, 'metrics') and response.metrics:
                try:
                    metrics = response.metrics

                    # Extract token counts (AGNO Metrics object has attributes, not dict keys)
                    input_tokens = getattr(metrics, 'input_tokens', 0) or 0
                    output_tokens = getattr(metrics, 'output_tokens', 0) or getattr(metrics, 'response_tokens', 0) or 0
                    total_tokens = getattr(metrics, 'total_tokens', 0) or (input_tokens + output_tokens)
                    model = getattr(metrics, 'model', 'gemini-2.5-flash') or 'gemini-2.5-flash'

                    # Only store if we have token data
                    if total_tokens > 0:
                        # Create metric object
                        metric_obj = create_metric_object(
                            agent_id="cirkelline",
                            agent_name="Cirkelline",
                            agent_type="team",
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=total_tokens,
                            model=model,
                            message_preview=message,
                            response_preview=response.content if hasattr(response, 'content') else ""
                        )

                        # Store in database
                        await store_metrics_in_database(actual_session_id, metric_obj)

                        logger.info(f"✅ Metrics captured: {total_tokens} tokens (input: {input_tokens}, output: {output_tokens})")
                    else:
                        logger.warning("⚠️ Metrics object exists but contains no token data")

                except Exception as e:
                    logger.error(f"❌ Failed to extract/store metrics: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Don't fail the request if metrics capture fails
            else:
                logger.warning("⚠️ No metrics available in response object")

            # Schedule session naming as background task (runs after response sent)
            # Note: Messages added after run(), so task checks count when it runs
            background_tasks.add_task(attempt_session_naming, actual_session_id)
            logger.info(f"📋 Scheduled session naming background task for session {actual_session_id[:8]}...")

            # Schedule auto-trigger check for memory optimization (non-blocking)
            background_tasks.add_task(check_and_trigger_optimization, user_id)
            logger.info(f"🔄 Scheduled auto-trigger check for user {user_id[:8]}...")

            # ═══ RESPONSE VALIDATION ═══
            # Validate response before returning to ensure data integrity
            # Following AGNO best practices: validate response object, status, and content

            # 1. Check if response object exists
            if not response:
                logger.error("❌ Response object is None")
                raise HTTPException(status_code=500, detail="Failed to generate response")

            # 2. Check response status (AGNO RunOutput has status attribute)
            # Status can be: RunStatus.completed, RunStatus.cancelled, RunStatus.failed, etc.
            if hasattr(response, 'status'):
                status_value = str(response.status) if response.status else "None"
                logger.info(f"📊 Response status: {status_value}")

                # Check if status indicates failure or cancellation
                if response.status and 'cancel' in status_value.lower():
                    logger.error(f"❌ Response was cancelled: {status_value}")
                    raise HTTPException(status_code=500, detail="Request was cancelled")

                if response.status and 'fail' in status_value.lower():
                    logger.error(f"❌ Response failed: {status_value}")
                    raise HTTPException(status_code=500, detail="Request failed during processing")

                # If status exists but is not completed/success, log warning
                if response.status and 'complet' not in status_value.lower() and 'success' not in status_value.lower():
                    logger.warning(f"⚠️ Unexpected response status (proceeding anyway): {status_value}")
            else:
                logger.warning("⚠️ Response object has no 'status' attribute (older AGNO version?)")

            # 3. Check if response has content attribute
            if not hasattr(response, 'content'):
                logger.error("❌ Response object has no 'content' attribute")
                logger.error(f"   Response attributes: {dir(response)}")
                raise HTTPException(status_code=500, detail="Invalid response format")

            # 4. Check if content is not empty
            if not response.content:
                logger.error("❌ Response content is empty")
                logger.error(f"   Response status: {getattr(response, 'status', 'unknown')}")
                raise HTTPException(status_code=500, detail="Empty response generated")

            # 5. Check if content is a string
            if not isinstance(response.content, str):
                logger.error(f"❌ Response content is not a string: {type(response.content)}")
                raise HTTPException(status_code=500, detail="Invalid response content type")

            # 6. Ensure content is JSON serializable
            try:
                json.dumps(response.content)
            except (TypeError, ValueError) as e:
                logger.error(f"❌ Response content is not JSON serializable: {e}")
                raise HTTPException(status_code=500, detail="Response content cannot be serialized")

            logger.info(f"✅ Response validation passed: {len(response.content)} characters")

            # ✅ v1.2.29: Extract serializable content from response (prevent function serialization error)
            # FastAPI's jsonable_encoder cannot serialize functions (agent.instructions is now callable)
            return {"content": response.content}

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error activity
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="chat_message",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            target_resource_id=actual_session_id if 'actual_session_id' in locals() else None,
            resource_type="session"
        )

        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# CANCEL RUN ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/teams/cirkelline/runs/{run_id}/cancel")
async def cancel_cirkelline_run(
    request: Request,
    run_id: str,
    user_id: str = Form(...)
):
    """
    Cancel a currently executing Cirkelline run.

    Security: Validates that the requesting user owns the run.
    Behavior: Graceful cancellation - current step completes before stopping.

    Returns:
        - 200: Cancellation initiated successfully
        - 404: Run not found or already completed
        - 409: Run cannot be cancelled (already completed)
        - 500: Cancellation failed
    """
    logger.info(f"🛑 Cancel request: run_id={run_id[:8]}..., user_id={user_id[:20]}...")

    # Security: Verify user owns this run
    session_id = get_active_run_for_user(user_id, run_id)

    if session_id is None:
        logger.warning(f"❌ Cancel failed: run {run_id[:8]}... not found for user")

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="run_cancel_attempt",
            success=False,
            status_code=404,
            target_resource_id=run_id,
            resource_type="run",
            error_message="Run not found or already completed",
            details={"reason": "not_found_or_completed"}
        )

        raise HTTPException(status_code=404, detail="Run not found or already completed")

    try:
        # Call AGNO's cancel_run method on the team
        success = cirkelline.cancel_run(run_id)

        if success:
            logger.info(f"✅ Cancellation initiated for run {run_id[:8]}...")
            unregister_active_run(user_id, run_id)

            # Mark session as having a cancelled run (for Cirkelline awareness)
            mark_session_cancelled(session_id, partial_content="")

            await log_activity(
                request=request,
                user_id=user_id,
                action_type="run_cancel",
                success=True,
                status_code=200,
                target_resource_id=run_id,
                resource_type="run",
                details={"session_id": session_id}
            )

            return {
                "success": True,
                "message": "Cancellation initiated",
                "run_id": run_id,
                "session_id": session_id
            }
        else:
            logger.warning(f"⚠️ AGNO cancel_run returned False for {run_id[:8]}...")
            unregister_active_run(user_id, run_id)

            await log_activity(
                request=request,
                user_id=user_id,
                action_type="run_cancel_attempt",
                success=False,
                status_code=409,
                target_resource_id=run_id,
                resource_type="run",
                error_message="Run already completed or cannot be cancelled"
            )

            raise HTTPException(status_code=409, detail="Run already completed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Cancel error for run {run_id[:8]}...: {e}")

        await log_activity(
            request=request,
            user_id=user_id,
            action_type="run_cancel_attempt",
            success=False,
            status_code=500,
            target_resource_id=run_id,
            resource_type="run",
            error_message=str(e),
            error_type=type(e).__name__
        )

        raise HTTPException(status_code=500, detail=f"Failed to cancel run: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# CONTINUE RUN ENDPOINT - Resume paused HITL runs
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/teams/cirkelline/runs/{run_id}/continue")
async def continue_cirkelline_run(
    request: Request,
    run_id: str,
    session_id: str = Form(...),
    user_input: str = Form(None),  # JSON string of filled user input fields
    confirmed: bool = Form(None),  # For confirmation flows
    stream: bool = Form(True)
):
    """
    Continue a paused Cirkelline run after HITL interaction.

    This endpoint is called when:
    1. User has filled in the requested input fields (user_input flow)
    2. User has confirmed/rejected a tool call (confirmation flow)

    The frontend should:
    1. Receive 'paused' event from the main run
    2. Show UI for user input or confirmation
    3. Collect user response
    4. POST to this endpoint with filled values
    5. Stream the continued response
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"▶️ HITL Continue: run_id={run_id[:8]}..., session_id={session_id[:8]}..., user_id={user_id[:8]}...")

    # Parse user input if provided
    filled_fields = {}
    if user_input:
        try:
            filled_fields = json.loads(user_input)
            logger.info(f"▶️ HITL: Received {len(filled_fields)} filled fields")
        except json.JSONDecodeError as e:
            logger.error(f"❌ HITL: Invalid user_input JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid user_input JSON")

    async def generate_continue_response():
        """Stream the continued run response."""
        try:
            from cirkelline.orchestrator.cirkelline_team import cirkelline

            # Build requirements with filled values
            # Note: AGNO continue_run expects either:
            # 1. requirements parameter with updated requirement objects
            # 2. updated_tools parameter with updated tool objects

            # For dynamic user input (get_user_input tool), we need to:
            # 1. Get the current run state
            # 2. Fill in the user_input_schema fields
            # 3. Call continue_run

            logger.info(f"▶️ HITL: Calling acontinue_run for run_id={run_id[:8]}...")

            # Use acontinue_run with the run_id
            # The filled_fields should be passed as part of the tool state
            async for event in cirkelline.acontinue_run(
                run_id=run_id,
                stream=True,
                stream_events=True
            ):
                event_type = getattr(event, 'event', 'unknown')
                event_data = event.to_dict()

                # Check if still paused (might need more input)
                is_paused = getattr(event, 'is_paused', False)
                if is_paused:
                    logger.info(f"⏸️ HITL: Run still paused after continue")
                    # Handle nested pause - send paused event again
                    active_requirements = getattr(event, 'active_requirements', [])
                    paused_data = {
                        "event": "paused",
                        "run_id": run_id,
                        "session_id": session_id,
                        "requirements": []
                    }
                    for req in active_requirements:
                        req_data = {
                            "needs_user_input": getattr(req, 'needs_user_input', False),
                            "needs_confirmation": getattr(req, 'needs_confirmation', False),
                            "user_input_schema": []
                        }
                        if req_data["needs_user_input"]:
                            schema = getattr(req, 'user_input_schema', [])
                            for field in schema:
                                req_data["user_input_schema"].append({
                                    "name": getattr(field, 'name', getattr(field, 'field_name', '')),
                                    "field_type": getattr(field, 'field_type', 'str'),
                                    "description": getattr(field, 'description', getattr(field, 'field_description', '')),
                                    "value": getattr(field, 'value', None)
                                })
                        paused_data["requirements"].append(req_data)

                    yield f"event: paused\ndata: {json.dumps(paused_data)}\n\n"
                    break

                # Forward the event to frontend
                try:
                    yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
                except (TypeError, ValueError) as e:
                    logger.error(f"❌ HITL Continue: Serialization error: {e}")
                    continue

            logger.info(f"✅ HITL: Continue completed for run_id={run_id[:8]}...")

        except Exception as e:
            logger.error(f"❌ HITL Continue error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            error_event = {
                "event": "error",
                "error": str(e),
                "type": "hitl_continue_error"
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

    if stream:
        return StreamingResponse(
            generate_continue_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Type": "text/event-stream"
            }
        )
    else:
        # Non-streaming mode - collect all events
        events = []
        async for event_str in generate_continue_response():
            events.append(event_str)
        return JSONResponse(content={"events": events})


logger.info("✅ Custom Cirkelline endpoint loaded")
