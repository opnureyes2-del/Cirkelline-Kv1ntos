"""
Dispatcher Agent
================
Request routing and capability-based agent matching.

Responsibilities:
- Route requests to appropriate agents
- Capability-based matching
- Load balancing
- Fallback handling
- Request queueing
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from collections import defaultdict

from cirkelline.headquarters.event_bus import (
    EventBus,
    Event,
    EventType,
    get_event_bus,
)
from cirkelline.headquarters.shared_memory import (
    SharedMemory,
    AgentState,
    get_shared_memory,
)
from cirkelline.context.agent_protocol import (
    AgentDescriptor,
    AgentCapability,
    AgentMessage,
    MessageType,
    create_agent_message,
    get_capability_registry,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTING STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RoutingRequest:
    """A request waiting to be routed."""
    request_id: str
    capability: AgentCapability
    payload: Dict[str, Any]
    priority: int = 1  # Higher = more important
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    timeout_seconds: int = 300
    retries: int = 0
    max_retries: int = 3
    preferred_agent: Optional[str] = None
    excluded_agents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "capability": self.capability.value,
            "payload": self.payload,
            "priority": self.priority,
            "created_at": self.created_at,
            "timeout_seconds": self.timeout_seconds,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "preferred_agent": self.preferred_agent,
            "excluded_agents": self.excluded_agents,
        }


@dataclass
class RoutingResult:
    """Result of a routing decision."""
    success: bool
    request_id: str
    agent_id: Optional[str] = None
    reason: Optional[str] = None
    fallback_used: bool = False
    routing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "reason": self.reason,
            "fallback_used": self.fallback_used,
            "routing_time_ms": self.routing_time_ms,
        }


@dataclass
class AgentScore:
    """Scoring for agent selection."""
    agent_id: str
    capability_match: float = 0.0  # 0-1
    availability_score: float = 0.0  # 0-1
    performance_score: float = 0.0  # 0-1
    load_score: float = 0.0  # 0-1 (higher = less loaded)

    @property
    def total_score(self) -> float:
        """Calculate weighted total score."""
        weights = {
            "capability": 0.4,
            "availability": 0.3,
            "performance": 0.2,
            "load": 0.1,
        }
        return (
            self.capability_match * weights["capability"] +
            self.availability_score * weights["availability"] +
            self.performance_score * weights["performance"] +
            self.load_score * weights["load"]
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DISPATCHER AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class DispatcherAgent:
    """
    Routes requests to appropriate agents based on capabilities.

    Uses scoring system to select the best agent for each request,
    with fallback handling when primary agents are unavailable.
    """

    AGENT_ID = "hq:dispatcher"
    AGENT_NAME = "Request Dispatcher"

    # Dispatch check interval in seconds
    DISPATCH_INTERVAL = 5

    # Fallback capabilities for common requests
    FALLBACK_MAP = {
        AgentCapability.CODE_GENERATION: AgentCapability.CONVERSATION,
        AgentCapability.CODE_REVIEW: AgentCapability.CONVERSATION,
        AgentCapability.LEGAL_ANALYSIS: AgentCapability.DOCUMENT_PROCESSING,
        AgentCapability.LEGAL_RESEARCH: AgentCapability.WEB_SEARCH,
        AgentCapability.CONTRACT_REVIEW: AgentCapability.DOCUMENT_PROCESSING,
        AgentCapability.DEEP_RESEARCH: AgentCapability.WEB_SEARCH,
        AgentCapability.SUMMARIZATION: AgentCapability.CONVERSATION,
    }

    def __init__(self):
        self._event_bus: Optional[EventBus] = None
        self._memory: Optional[SharedMemory] = None
        self._running = False

        # Pending requests queue
        self._pending_requests: Dict[str, RoutingRequest] = {}

        # Agent performance tracking
        self._agent_performance: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"success_rate": 1.0, "avg_response_ms": 0.0, "total_requests": 0}
        )

        # Recent routing decisions for analytics
        self._routing_history: List[RoutingResult] = []

    async def initialize(self) -> bool:
        """Initialize connections."""
        try:
            self._event_bus = get_event_bus()
            self._memory = get_shared_memory()

            # Register self
            registry = get_capability_registry()
            registry.register(AgentDescriptor(
                agent_id=self.AGENT_ID,
                name=self.AGENT_NAME,
                role="Request routing and capability matching",
                capabilities=[],
                max_concurrent_tasks=100,  # High concurrency for routing
            ))

            # Subscribe to events
            self._event_bus.subscribe(EventType.TERMINAL_REQUEST, self._handle_terminal_request)
            self._event_bus.subscribe(EventType.MISSION_ASSIGNED, self._handle_mission_assigned)
            self._event_bus.subscribe(EventType.AGENT_REGISTERED, self._handle_agent_registered)
            self._event_bus.subscribe(EventType.AGENT_RESPONSE, self._handle_agent_response)

            logger.info(f"DispatcherAgent initialized: {self.AGENT_ID}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize DispatcherAgent: {e}")
            return False

    async def start(self) -> None:
        """Start the dispatch loop."""
        self._running = True
        logger.info("DispatcherAgent started")

        while self._running:
            try:
                await self._process_pending_requests()
                await self._cleanup_expired_requests()

                await asyncio.sleep(self.DISPATCH_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Dispatcher loop error: {e}")
                await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop dispatching."""
        self._running = False
        logger.info("DispatcherAgent stopped")

    # ═══════════════════════════════════════════════════════════════════════════
    # REQUEST ROUTING
    # ═══════════════════════════════════════════════════════════════════════════

    async def route_request(
        self,
        capability: AgentCapability,
        payload: Dict[str, Any],
        priority: int = 1,
        preferred_agent: Optional[str] = None,
        timeout_seconds: int = 300,
    ) -> RoutingResult:
        """
        Route a request to an appropriate agent.

        Args:
            capability: Required capability
            payload: Request payload
            priority: Request priority (higher = more important)
            preferred_agent: Preferred agent ID if any
            timeout_seconds: Request timeout

        Returns:
            RoutingResult with selected agent or failure reason
        """
        start_time = datetime.utcnow()
        request_id = f"req-{uuid.uuid4().hex[:8]}"

        request = RoutingRequest(
            request_id=request_id,
            capability=capability,
            payload=payload,
            priority=priority,
            preferred_agent=preferred_agent,
            timeout_seconds=timeout_seconds,
        )

        # Try to find an agent
        agent_id, fallback_used = await self._find_best_agent(request)

        routing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        if agent_id:
            result = RoutingResult(
                success=True,
                request_id=request_id,
                agent_id=agent_id,
                fallback_used=fallback_used,
                routing_time_ms=routing_time,
            )

            # Dispatch to agent
            await self._dispatch_to_agent(request, agent_id)
            logger.info(f"Routed request {request_id} to {agent_id}")

        else:
            # Queue for later
            self._pending_requests[request_id] = request
            result = RoutingResult(
                success=False,
                request_id=request_id,
                reason="No available agents with required capability",
                routing_time_ms=routing_time,
            )
            logger.warning(f"Queued request {request_id}: no available agents")

        # Record history
        self._routing_history.append(result)
        if len(self._routing_history) > 1000:
            self._routing_history = self._routing_history[-1000:]

        return result

    async def _find_best_agent(
        self,
        request: RoutingRequest,
    ) -> Tuple[Optional[str], bool]:
        """
        Find the best agent for a request.

        Returns (agent_id, fallback_used) tuple.
        """
        registry = get_capability_registry()
        fallback_used = False

        # Check preferred agent first
        if request.preferred_agent:
            agent = registry.get_agent(request.preferred_agent)
            if agent and request.capability in agent.capabilities:
                if await self._is_agent_available(request.preferred_agent):
                    return request.preferred_agent, False

        # Find agents with required capability
        candidates = registry.find_by_capability(
            request.capability,
            exclude=request.excluded_agents + [self.AGENT_ID],
        )

        if not candidates:
            # Try fallback capability
            fallback_cap = self.FALLBACK_MAP.get(request.capability)
            if fallback_cap:
                candidates = registry.find_by_capability(
                    fallback_cap,
                    exclude=request.excluded_agents + [self.AGENT_ID],
                )
                if candidates:
                    fallback_used = True

        if not candidates:
            return None, False

        # Score all candidates
        scores = []
        for agent in candidates:
            score = await self._score_agent(agent, request)
            if score.availability_score > 0:  # Only consider available agents
                scores.append(score)

        if not scores:
            return None, False

        # Select highest scoring agent
        scores.sort(key=lambda s: s.total_score, reverse=True)
        return scores[0].agent_id, fallback_used

    async def _score_agent(
        self,
        agent: AgentDescriptor,
        request: RoutingRequest,
    ) -> AgentScore:
        """Score an agent for a request."""
        score = AgentScore(agent_id=agent.agent_id)

        # Capability match (exact = 1.0, fallback = 0.5)
        if request.capability in agent.capabilities:
            score.capability_match = 1.0
        else:
            score.capability_match = 0.5

        # Availability
        if await self._is_agent_available(agent.agent_id):
            score.availability_score = 1.0
        else:
            score.availability_score = 0.0

        # Performance (from history)
        perf = self._agent_performance[agent.agent_id]
        score.performance_score = perf["success_rate"]

        # Load (from shared memory)
        try:
            state = await self._memory.get_agent_state(agent.agent_id)
            if state:
                # Higher score for less loaded agents
                current_load = state.current_tasks / max(state.max_tasks, 1)
                score.load_score = 1.0 - current_load
            else:
                score.load_score = 0.5
        except Exception:
            score.load_score = 0.5

        return score

    async def _is_agent_available(self, agent_id: str) -> bool:
        """Check if an agent is currently available."""
        try:
            active_agents = await self._memory.get_active_agents(timeout_seconds=60)
            return any(a.agent_id == agent_id for a in active_agents)
        except Exception:
            return False

    async def _dispatch_to_agent(
        self,
        request: RoutingRequest,
        agent_id: str,
    ) -> None:
        """Send request to the selected agent."""
        message = create_agent_message(
            sender=self.AGENT_ID,
            recipient=agent_id,
            content=request.payload.get("message", ""),
            message_type=MessageType.REQUEST,
            context={
                "request_id": request.request_id,
                "capability": request.capability.value,
                **request.payload,
            },
        )

        await self._event_bus.publish(Event(
            event_type=EventType.AGENT_REQUEST,
            source=self.AGENT_ID,
            payload=message.to_dict(),
            priority=request.priority,
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # QUEUE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def _process_pending_requests(self) -> None:
        """Try to route pending requests."""
        for request_id in list(self._pending_requests.keys()):
            request = self._pending_requests[request_id]

            # Try to find an agent
            agent_id, fallback_used = await self._find_best_agent(request)

            if agent_id:
                # Route successfully
                await self._dispatch_to_agent(request, agent_id)
                del self._pending_requests[request_id]
                logger.info(f"Routed pending request {request_id} to {agent_id}")

    async def _cleanup_expired_requests(self) -> None:
        """Remove requests that have timed out."""
        now = datetime.utcnow()

        for request_id in list(self._pending_requests.keys()):
            request = self._pending_requests[request_id]
            created = datetime.fromisoformat(request.created_at)

            if (now - created).total_seconds() > request.timeout_seconds:
                # Check if we should retry
                if request.retries < request.max_retries:
                    request.retries += 1
                    request.created_at = now.isoformat()
                    logger.info(f"Retrying request {request_id} (attempt {request.retries})")
                else:
                    # Give up
                    del self._pending_requests[request_id]
                    logger.warning(f"Request {request_id} expired after {request.max_retries} retries")

                    # Notify failure
                    await self._event_bus.publish(Event(
                        event_type=EventType.SYSTEM_ERROR,
                        source=self.AGENT_ID,
                        payload={
                            "request_id": request_id,
                            "error": "Request routing timeout",
                            "capability": request.capability.value,
                        },
                    ))

    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _handle_terminal_request(self, event: Event) -> None:
        """Handle incoming terminal requests."""
        payload = event.payload
        capability_str = payload.get("capability", "conversation")

        # Map string to capability
        try:
            capability = AgentCapability(capability_str)
        except ValueError:
            capability = AgentCapability.CONVERSATION

        await self.route_request(
            capability=capability,
            payload=payload,
            priority=payload.get("priority", 1),
        )

    async def _handle_mission_assigned(self, event: Event) -> None:
        """Handle mission assignment events for routing."""
        # Could be used to pre-warm agents
        pass

    async def _handle_agent_registered(self, event: Event) -> None:
        """Handle new agent registration."""
        agent_id = event.payload.get("agent_id")
        if agent_id:
            # Initialize performance tracking
            self._agent_performance[agent_id] = {
                "success_rate": 1.0,
                "avg_response_ms": 0.0,
                "total_requests": 0,
            }

    async def _handle_agent_response(self, event: Event) -> None:
        """Handle agent responses to update performance metrics."""
        payload = event.payload
        agent_id = event.source
        success = payload.get("success", True)
        response_time = payload.get("response_time_ms", 0)

        perf = self._agent_performance[agent_id]
        total = perf["total_requests"]

        # Update running averages
        if total > 0:
            perf["success_rate"] = (
                (perf["success_rate"] * total + (1.0 if success else 0.0)) /
                (total + 1)
            )
            perf["avg_response_ms"] = (
                (perf["avg_response_ms"] * total + response_time) /
                (total + 1)
            )
        else:
            perf["success_rate"] = 1.0 if success else 0.0
            perf["avg_response_ms"] = response_time

        perf["total_requests"] = total + 1

    # ═══════════════════════════════════════════════════════════════════════════
    # LOAD BALANCING
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_agent_loads(self) -> Dict[str, Dict[str, Any]]:
        """Get current load for all agents."""
        registry = get_capability_registry()
        loads = {}

        for agent in registry.get_all_agents():
            if agent.agent_id.startswith("hq:"):
                continue

            state = await self._memory.get_agent_state(agent.agent_id)
            perf = self._agent_performance[agent.agent_id]

            loads[agent.agent_id] = {
                "name": agent.name,
                "status": state.status if state else "unknown",
                "current_tasks": state.current_tasks if state else 0,
                "max_tasks": state.max_tasks if state else 1,
                "utilization": (state.current_tasks / max(state.max_tasks, 1)) if state else 0,
                "success_rate": f"{perf['success_rate']:.0%}",
                "avg_response_ms": f"{perf['avg_response_ms']:.0f}",
                "total_requests": perf["total_requests"],
            }

        return loads

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics."""
        recent = self._routing_history[-100:] if self._routing_history else []

        success_count = sum(1 for r in recent if r.success)
        fallback_count = sum(1 for r in recent if r.fallback_used)

        return {
            "pending_requests": len(self._pending_requests),
            "total_routed": len(self._routing_history),
            "recent_success_rate": f"{success_count / len(recent):.0%}" if recent else "N/A",
            "fallback_rate": f"{fallback_count / len(recent):.0%}" if recent else "N/A",
            "avg_routing_time_ms": (
                sum(r.routing_time_ms for r in recent) / len(recent)
                if recent else 0
            ),
            "agents_tracked": len(self._agent_performance),
            "agent_performance": {
                aid: {
                    "success_rate": f"{p['success_rate']:.0%}",
                    "avg_response_ms": f"{p['avg_response_ms']:.0f}",
                    "total_requests": p["total_requests"],
                }
                for aid, p in self._agent_performance.items()
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_dispatcher_instance: Optional[DispatcherAgent] = None


def get_dispatcher() -> DispatcherAgent:
    """Get the singleton DispatcherAgent instance."""
    global _dispatcher_instance

    if _dispatcher_instance is None:
        _dispatcher_instance = DispatcherAgent()

    return _dispatcher_instance


async def init_dispatcher() -> DispatcherAgent:
    """Initialize and start the dispatcher."""
    dispatcher = get_dispatcher()
    await dispatcher.initialize()
    return dispatcher
