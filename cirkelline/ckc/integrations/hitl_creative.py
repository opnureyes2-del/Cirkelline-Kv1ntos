"""
CKC Creative HITL (Human-in-the-Loop)
=====================================

Human-in-the-Loop handling for creative tasks.

Enables Super Admin to:
- Select best option from multiple generations
- Approve/reject creative outputs
- Request refinements and modifications
- Guide creative iterations

Eksempel:
    handler = create_creative_hitl_handler()

    # Request selection from multiple options
    request = await handler.request_selection(
        options=[option1, option2, option3],
        context={"prompt": "A dragon", "style": "fantasy"}
    )

    # Wait for response
    response = await handler.wait_for_response(request.request_id)

    if response.decision == CreativeDecision.SELECT:
        selected = response.selected_option
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Awaitable
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class CreativeHITLType(Enum):
    """Types of creative HITL requests."""
    SELECT_BEST = "select_best"          # Select best from multiple options
    APPROVE_REJECT = "approve_reject"    # Approve or reject single output
    REFINE_REQUEST = "refine_request"    # Request refinements
    STYLE_CHOICE = "style_choice"        # Choose style direction
    COMPOSITION_GUIDE = "composition"    # Guide composition decisions
    ITERATE = "iterate"                  # Request iteration with feedback


class CreativeDecision(Enum):
    """Possible decisions for creative HITL."""
    APPROVE = "approve"
    REJECT = "reject"
    SELECT = "select"
    REFINE = "refine"
    ITERATE = "iterate"
    SKIP = "skip"
    TIMEOUT = "timeout"


class HITLPriority(Enum):
    """Priority levels for HITL requests."""
    CRITICAL = 1   # Requires immediate attention
    HIGH = 2       # Should be addressed promptly
    NORMAL = 3     # Standard priority
    LOW = 4        # Can wait


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CreativeOption:
    """An option presented for selection."""
    option_id: str
    label: str
    description: str
    preview_url: Optional[str] = None
    preview_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0  # AI-generated quality score
    cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "label": self.label,
            "description": self.description,
            "preview_url": self.preview_url,
            "preview_path": self.preview_path,
            "thumbnail_url": self.thumbnail_url,
            "metadata": self.metadata,
            "score": self.score,
            "cost_usd": self.cost_usd,
        }


@dataclass
class CreativeHITLRequest:
    """A creative HITL request awaiting human decision."""
    request_id: str
    request_type: CreativeHITLType
    title: str
    description: str
    options: List[CreativeOption] = field(default_factory=list)

    # Context
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    # Creative details
    prompt_used: str = ""
    style_applied: str = ""
    iterations: int = 0

    # Status
    status: str = "pending"  # pending, responded, expired
    priority: HITLPriority = HITLPriority.NORMAL

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None

    # Response (filled when responded)
    response: Optional["CreativeHITLResponse"] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "request_type": self.request_type.value,
            "title": self.title,
            "description": self.description,
            "options": [o.to_dict() for o in self.options],
            "session_id": self.session_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "context": self.context,
            "prompt_used": self.prompt_used,
            "style_applied": self.style_applied,
            "iterations": self.iterations,
            "status": self.status,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
        }


@dataclass
class CreativeHITLResponse:
    """Response to a creative HITL request."""
    request_id: str
    decision: CreativeDecision
    selected_option_id: Optional[str] = None
    feedback: str = ""
    modifications: Dict[str, Any] = field(default_factory=dict)
    responded_by: str = "super_admin"
    responded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "decision": self.decision.value,
            "selected_option_id": self.selected_option_id,
            "feedback": self.feedback,
            "modifications": self.modifications,
            "responded_by": self.responded_by,
            "responded_at": self.responded_at.isoformat(),
        }


@dataclass
class HITLCallback:
    """Callback registration for HITL events."""
    callback_id: str
    request_id: str
    callback: Callable[[CreativeHITLResponse], Awaitable[None]]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# CREATIVE SELECTION MANAGER
# =============================================================================

class CreativeSelectionManager:
    """
    Manages selection processes for creative outputs.

    Handles:
    - Multi-option presentation
    - Voting and scoring
    - Selection history
    """

    def __init__(self):
        self._selections: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def create_selection(
        self,
        options: List[CreativeOption],
        title: str = "Select Best Option",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new selection session."""
        selection_id = f"sel_{uuid.uuid4().hex[:12]}"

        self._selections[selection_id] = {
            "selection_id": selection_id,
            "title": title,
            "options": options,
            "context": context or {},
            "votes": {},  # option_id -> vote count
            "selected": None,
            "created_at": datetime.now(timezone.utc),
        }

        return selection_id

    def vote(self, selection_id: str, option_id: str, weight: float = 1.0) -> bool:
        """Cast a vote for an option."""
        if selection_id not in self._selections:
            return False

        selection = self._selections[selection_id]
        if option_id not in selection["votes"]:
            selection["votes"][option_id] = 0.0

        selection["votes"][option_id] += weight
        return True

    def finalize_selection(self, selection_id: str) -> Optional[str]:
        """Finalize selection and return winning option."""
        if selection_id not in self._selections:
            return None

        selection = self._selections[selection_id]
        votes = selection["votes"]

        if not votes:
            return None

        # Find winner (highest votes)
        winner = max(votes.keys(), key=lambda k: votes[k])
        selection["selected"] = winner

        # Add to history
        self._history.append({
            **selection,
            "finalized_at": datetime.now(timezone.utc),
        })

        return winner

    def get_selection(self, selection_id: str) -> Optional[Dict[str, Any]]:
        """Get selection details."""
        return self._selections.get(selection_id)

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get selection history."""
        return self._history[-limit:]


# =============================================================================
# CREATIVE HITL HANDLER
# =============================================================================

class CreativeHITLHandler:
    """
    Main handler for Creative HITL operations.

    Responsibilities:
    - Create and manage HITL requests
    - Handle responses and callbacks
    - Integrate with Control Panel
    - Track metrics and history
    """

    def __init__(self, default_timeout_minutes: int = 30):
        self._requests: Dict[str, CreativeHITLRequest] = {}
        self._callbacks: Dict[str, HITLCallback] = {}
        self._response_events: Dict[str, asyncio.Event] = {}
        self._selection_manager = CreativeSelectionManager()

        self._default_timeout = default_timeout_minutes

        # Statistics
        self._total_requests = 0
        self._total_responses = 0
        self._total_timeouts = 0

        # Pending request notification callback
        self._notify_callback: Optional[Callable[[CreativeHITLRequest], Awaitable[None]]] = None

        logger.info("CreativeHITLHandler initialized")

    # =========================================================================
    # REQUEST CREATION
    # =========================================================================

    async def request_selection(
        self,
        options: List[CreativeOption],
        title: str = "Select Best Creative Output",
        description: str = "",
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: str = "",
        timeout_minutes: Optional[int] = None,
        priority: HITLPriority = HITLPriority.NORMAL,
    ) -> CreativeHITLRequest:
        """
        Request human selection from multiple options.

        Args:
            options: List of CreativeOption to choose from
            title: Request title
            description: Request description
            context: Additional context
            session_id: MASTERMIND session ID
            task_id: Related task ID
            agent_id: Requesting agent ID
            timeout_minutes: Override default timeout
            priority: Request priority

        Returns:
            CreativeHITLRequest
        """
        request = await self._create_request(
            request_type=CreativeHITLType.SELECT_BEST,
            title=title,
            description=description or f"Please select the best option from {len(options)} alternatives",
            options=options,
            context=context,
            session_id=session_id,
            task_id=task_id,
            agent_id=agent_id,
            timeout_minutes=timeout_minutes,
            priority=priority,
        )

        return request

    async def request_approval(
        self,
        option: CreativeOption,
        title: str = "Approve Creative Output",
        description: str = "",
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: str = "",
        timeout_minutes: Optional[int] = None,
        priority: HITLPriority = HITLPriority.NORMAL,
    ) -> CreativeHITLRequest:
        """
        Request approval for a single creative output.

        Args:
            option: CreativeOption to approve/reject
            title: Request title
            description: Request description
            context: Additional context
            session_id: MASTERMIND session ID
            task_id: Related task ID
            agent_id: Requesting agent ID
            timeout_minutes: Override default timeout
            priority: Request priority

        Returns:
            CreativeHITLRequest
        """
        request = await self._create_request(
            request_type=CreativeHITLType.APPROVE_REJECT,
            title=title,
            description=description or "Please approve or reject this creative output",
            options=[option],
            context=context,
            session_id=session_id,
            task_id=task_id,
            agent_id=agent_id,
            timeout_minutes=timeout_minutes,
            priority=priority,
        )

        return request

    async def request_refinement(
        self,
        current_output: CreativeOption,
        title: str = "Request Refinements",
        description: str = "",
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: str = "",
        iterations: int = 0,
        timeout_minutes: Optional[int] = None,
        priority: HITLPriority = HITLPriority.NORMAL,
    ) -> CreativeHITLRequest:
        """
        Request refinement instructions for a creative output.

        Args:
            current_output: Current creative output
            title: Request title
            description: Request description
            context: Additional context
            session_id: MASTERMIND session ID
            task_id: Related task ID
            agent_id: Requesting agent ID
            iterations: Current iteration count
            timeout_minutes: Override default timeout
            priority: Request priority

        Returns:
            CreativeHITLRequest
        """
        request = await self._create_request(
            request_type=CreativeHITLType.REFINE_REQUEST,
            title=title,
            description=description or "Please provide refinement instructions",
            options=[current_output],
            context=context,
            session_id=session_id,
            task_id=task_id,
            agent_id=agent_id,
            timeout_minutes=timeout_minutes,
            priority=priority,
        )
        request.iterations = iterations

        return request

    async def request_style_choice(
        self,
        style_options: List[CreativeOption],
        title: str = "Choose Style Direction",
        description: str = "",
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: str = "",
        timeout_minutes: Optional[int] = None,
        priority: HITLPriority = HITLPriority.NORMAL,
    ) -> CreativeHITLRequest:
        """
        Request style direction choice.

        Args:
            style_options: Style options to choose from
            title: Request title
            description: Request description
            context: Additional context
            session_id: MASTERMIND session ID
            task_id: Related task ID
            agent_id: Requesting agent ID
            timeout_minutes: Override default timeout
            priority: Request priority

        Returns:
            CreativeHITLRequest
        """
        request = await self._create_request(
            request_type=CreativeHITLType.STYLE_CHOICE,
            title=title,
            description=description or "Please choose a style direction for the creative output",
            options=style_options,
            context=context,
            session_id=session_id,
            task_id=task_id,
            agent_id=agent_id,
            timeout_minutes=timeout_minutes,
            priority=priority,
        )

        return request

    async def _create_request(
        self,
        request_type: CreativeHITLType,
        title: str,
        description: str,
        options: List[CreativeOption],
        context: Optional[Dict[str, Any]],
        session_id: Optional[str],
        task_id: Optional[str],
        agent_id: str,
        timeout_minutes: Optional[int],
        priority: HITLPriority,
    ) -> CreativeHITLRequest:
        """Create a new HITL request."""
        request_id = f"hitl_creative_{uuid.uuid4().hex[:12]}"
        timeout = timeout_minutes or self._default_timeout

        request = CreativeHITLRequest(
            request_id=request_id,
            request_type=request_type,
            title=title,
            description=description,
            options=options,
            session_id=session_id,
            task_id=task_id,
            agent_id=agent_id,
            context=context or {},
            priority=priority,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=timeout),
        )

        # Extract creative details from context
        if context:
            request.prompt_used = context.get("prompt", "")
            request.style_applied = context.get("style", "")

        self._requests[request_id] = request
        self._response_events[request_id] = asyncio.Event()
        self._total_requests += 1

        # Notify listeners
        if self._notify_callback:
            try:
                await self._notify_callback(request)
            except Exception as e:
                logger.error(f"Error in notify callback: {e}")

        logger.info(f"Creative HITL request created: {request_id} ({request_type.value})")

        return request

    # =========================================================================
    # RESPONSE HANDLING
    # =========================================================================

    async def respond(
        self,
        request_id: str,
        decision: CreativeDecision,
        selected_option_id: Optional[str] = None,
        feedback: str = "",
        modifications: Optional[Dict[str, Any]] = None,
        responded_by: str = "super_admin",
    ) -> Optional[CreativeHITLResponse]:
        """
        Submit response to a HITL request.

        Args:
            request_id: Request ID to respond to
            decision: Decision made
            selected_option_id: ID of selected option (for SELECT decisions)
            feedback: Optional feedback text
            modifications: Optional modifications requested
            responded_by: Who responded

        Returns:
            CreativeHITLResponse or None if request not found
        """
        request = self._requests.get(request_id)
        if not request:
            logger.warning(f"HITL request not found: {request_id}")
            return None

        if request.status != "pending":
            logger.warning(f"HITL request already processed: {request_id}")
            return None

        response = CreativeHITLResponse(
            request_id=request_id,
            decision=decision,
            selected_option_id=selected_option_id,
            feedback=feedback,
            modifications=modifications or {},
            responded_by=responded_by,
        )

        request.response = response
        request.status = "responded"
        request.responded_at = datetime.now(timezone.utc)

        self._total_responses += 1

        # Signal waiting coroutines
        if request_id in self._response_events:
            self._response_events[request_id].set()

        # Execute callbacks
        if request_id in self._callbacks:
            callback = self._callbacks[request_id]
            try:
                await callback.callback(response)
            except Exception as e:
                logger.error(f"Error in HITL callback: {e}")

        logger.info(f"Creative HITL response: {request_id} -> {decision.value}")

        return response

    async def wait_for_response(
        self,
        request_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[CreativeHITLResponse]:
        """
        Wait for response to a HITL request.

        Args:
            request_id: Request ID to wait for
            timeout: Optional timeout in seconds

        Returns:
            CreativeHITLResponse or None if timeout/not found
        """
        request = self._requests.get(request_id)
        if not request:
            return None

        if request.response:
            return request.response

        event = self._response_events.get(request_id)
        if not event:
            return None

        # Calculate timeout
        if timeout is None and request.expires_at:
            timeout = (request.expires_at - datetime.now(timezone.utc)).total_seconds()
            timeout = max(timeout, 0)

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return request.response
        except asyncio.TimeoutError:
            request.status = "expired"
            self._total_timeouts += 1
            logger.warning(f"Creative HITL request expired: {request_id}")
            return CreativeHITLResponse(
                request_id=request_id,
                decision=CreativeDecision.TIMEOUT,
            )

    def register_callback(
        self,
        request_id: str,
        callback: Callable[[CreativeHITLResponse], Awaitable[None]],
    ) -> str:
        """Register callback for when response is received."""
        callback_id = f"cb_{uuid.uuid4().hex[:8]}"

        self._callbacks[request_id] = HITLCallback(
            callback_id=callback_id,
            request_id=request_id,
            callback=callback,
        )

        return callback_id

    def set_notify_callback(
        self,
        callback: Callable[[CreativeHITLRequest], Awaitable[None]],
    ) -> None:
        """Set callback for new request notifications."""
        self._notify_callback = callback

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def get_request(self, request_id: str) -> Optional[CreativeHITLRequest]:
        """Get a specific request."""
        return self._requests.get(request_id)

    def get_pending_requests(
        self,
        session_id: Optional[str] = None,
        priority: Optional[HITLPriority] = None,
    ) -> List[CreativeHITLRequest]:
        """
        Get all pending HITL requests.

        Args:
            session_id: Filter by session
            priority: Filter by priority

        Returns:
            List of pending requests, sorted by priority and creation time
        """
        pending = [
            r for r in self._requests.values()
            if r.status == "pending"
        ]

        if session_id:
            pending = [r for r in pending if r.session_id == session_id]

        if priority:
            pending = [r for r in pending if r.priority == priority]

        # Sort by priority (lower = higher), then by creation time
        pending.sort(key=lambda r: (r.priority.value, r.created_at))

        return pending

    def get_request_history(
        self,
        limit: int = 100,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get request history."""
        requests = list(self._requests.values())

        if session_id:
            requests = [r for r in requests if r.session_id == session_id]

        # Sort by creation time, most recent first
        requests.sort(key=lambda r: r.created_at, reverse=True)

        return [r.to_dict() for r in requests[:limit]]

    def get_statistics(self) -> Dict[str, Any]:
        """Get HITL statistics."""
        pending_count = len([r for r in self._requests.values() if r.status == "pending"])

        return {
            "total_requests": self._total_requests,
            "total_responses": self._total_responses,
            "total_timeouts": self._total_timeouts,
            "pending_count": pending_count,
            "response_rate": (
                self._total_responses / self._total_requests
                if self._total_requests > 0
                else 0.0
            ),
            "timeout_rate": (
                self._total_timeouts / self._total_requests
                if self._total_requests > 0
                else 0.0
            ),
        }

    # =========================================================================
    # CLEANUP
    # =========================================================================

    async def cleanup_expired(self) -> int:
        """Cleanup expired requests."""
        now = datetime.now(timezone.utc)
        cleaned = 0

        for request_id, request in list(self._requests.items()):
            if request.status == "pending" and request.expires_at and request.expires_at < now:
                request.status = "expired"
                self._total_timeouts += 1
                cleaned += 1

                # Signal waiters
                if request_id in self._response_events:
                    self._response_events[request_id].set()

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired HITL requests")

        return cleaned

    @property
    def selection_manager(self) -> CreativeSelectionManager:
        """Access the selection manager."""
        return self._selection_manager


# =============================================================================
# FACTORY
# =============================================================================

_handler: Optional[CreativeHITLHandler] = None


def create_creative_hitl_handler(
    default_timeout_minutes: int = 30,
) -> CreativeHITLHandler:
    """
    Create the Creative HITL handler singleton.

    Args:
        default_timeout_minutes: Default timeout for requests

    Returns:
        CreativeHITLHandler instance
    """
    global _handler
    _handler = CreativeHITLHandler(default_timeout_minutes=default_timeout_minutes)
    logger.info("CreativeHITLHandler created")
    return _handler


def get_creative_hitl_handler() -> Optional[CreativeHITLHandler]:
    """Get the existing Creative HITL handler."""
    return _handler


logger.info("CKC Creative HITL module loaded")
