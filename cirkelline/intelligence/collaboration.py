"""
Collaboration Engine
====================
Multi-agent collaborative problem solving.

Responsibilities:
- Coordinate multiple agents for complex tasks
- Facilitate inter-agent communication
- Aggregate and synthesize agent outputs
- Resolve conflicts in agent recommendations
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from cirkelline.headquarters.event_bus import (
    EventBus,
    Event,
    EventType,
    get_event_bus,
)
from cirkelline.headquarters.shared_memory import (
    SharedMemory,
    Mission,
    MissionStatus,
    get_shared_memory,
)
from cirkelline.context.agent_protocol import (
    AgentDescriptor,
    AgentCapability,
    AgentMessage,
    MessageType,
    create_agent_message,
    create_broadcast,
    get_capability_registry,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# COLLABORATION TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class CollaborationMode(Enum):
    """Modes of multi-agent collaboration."""
    SEQUENTIAL = "sequential"  # Agents work one after another
    PARALLEL = "parallel"  # Agents work simultaneously
    CONSENSUS = "consensus"  # Agents must agree
    VOTING = "voting"  # Majority decision
    EXPERT = "expert"  # Delegate to domain expert


class CollaborationStatus(Enum):
    """Status of a collaboration session."""
    PENDING = "pending"
    ACTIVE = "active"
    VOTING = "voting"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentContribution:
    """A contribution from an agent to a collaboration."""
    agent_id: str
    agent_name: str
    content: str
    confidence: float = 1.0
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "content": self.content,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class CollaborationSession:
    """A multi-agent collaboration session."""
    session_id: str
    problem: str
    mode: CollaborationMode
    status: CollaborationStatus = CollaborationStatus.PENDING
    participants: List[str] = field(default_factory=list)
    required_capabilities: List[AgentCapability] = field(default_factory=list)
    contributions: List[AgentContribution] = field(default_factory=list)
    synthesis: Optional[str] = None
    final_decision: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "problem": self.problem,
            "mode": self.mode.value,
            "status": self.status.value,
            "participants": self.participants,
            "required_capabilities": [c.value for c in self.required_capabilities],
            "contributions": [c.to_dict() for c in self.contributions],
            "synthesis": self.synthesis,
            "final_decision": self.final_decision,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SYNTHESIS STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════════

class SynthesisStrategy:
    """Base class for synthesis strategies."""

    def synthesize(
        self,
        contributions: List[AgentContribution],
    ) -> str:
        """Synthesize contributions into a final result."""
        raise NotImplementedError


class WeightedAverageSynthesis(SynthesisStrategy):
    """Synthesize by weighted average of confidence scores."""

    def synthesize(
        self,
        contributions: List[AgentContribution],
    ) -> str:
        if not contributions:
            return "No contributions to synthesize."

        # Sort by confidence
        sorted_contrib = sorted(
            contributions,
            key=lambda c: c.confidence,
            reverse=True,
        )

        # Use highest confidence contribution as base
        primary = sorted_contrib[0]
        result_parts = [f"Primary insight (confidence {primary.confidence:.0%}):\n{primary.content}"]

        # Add supporting perspectives
        if len(sorted_contrib) > 1:
            result_parts.append("\nSupporting perspectives:")
            for contrib in sorted_contrib[1:]:
                if contrib.confidence > 0.5:
                    result_parts.append(f"- {contrib.agent_name}: {contrib.content[:200]}...")

        return "\n".join(result_parts)


class ConsensusSynthesis(SynthesisStrategy):
    """Synthesize only when consensus is reached."""

    def __init__(self, agreement_threshold: float = 0.8):
        self.agreement_threshold = agreement_threshold

    def synthesize(
        self,
        contributions: List[AgentContribution],
    ) -> str:
        if not contributions:
            return "No contributions to synthesize."

        # Check for consensus (simplified: high average confidence)
        avg_confidence = sum(c.confidence for c in contributions) / len(contributions)

        if avg_confidence >= self.agreement_threshold:
            # Combine all contributions
            combined = "\n\n".join([
                f"**{c.agent_name}** (confidence: {c.confidence:.0%}):\n{c.content}"
                for c in contributions
            ])
            return f"CONSENSUS REACHED (avg confidence: {avg_confidence:.0%})\n\n{combined}"
        else:
            # No consensus
            return f"NO CONSENSUS (avg confidence: {avg_confidence:.0%}). Diverse perspectives:\n\n" + \
                   "\n".join([f"- {c.agent_name}: {c.content[:100]}..." for c in contributions])


class VotingSynthesis(SynthesisStrategy):
    """Synthesize by voting on similar conclusions."""

    def synthesize(
        self,
        contributions: List[AgentContribution],
    ) -> str:
        if not contributions:
            return "No contributions to synthesize."

        # Group by similarity (simplified: use first 50 chars)
        groups: Dict[str, List[AgentContribution]] = {}
        for contrib in contributions:
            key = contrib.content[:50].lower()
            found_group = None
            for existing_key in groups:
                # Check if similar enough
                if self._similar(key, existing_key):
                    found_group = existing_key
                    break
            if found_group:
                groups[found_group].append(contrib)
            else:
                groups[key] = [contrib]

        # Find majority
        sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
        winner_key, winner_group = sorted_groups[0]

        vote_count = len(winner_group)
        total = len(contributions)

        if vote_count >= total / 2:
            # Majority found
            result = f"MAJORITY DECISION ({vote_count}/{total} votes):\n"
            result += winner_group[0].content
            return result
        else:
            # No clear majority
            return f"NO MAJORITY. Top voted ({vote_count}/{total}):\n{winner_group[0].content}"

    def _similar(self, a: str, b: str) -> bool:
        """Check if two strings are similar (simplified)."""
        # Simple overlap check
        words_a = set(a.split())
        words_b = set(b.split())
        overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
        return overlap > 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# COLLABORATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class CollaborationEngine:
    """
    Coordinates multi-agent collaboration for complex problems.

    Supports various collaboration modes and synthesis strategies
    to combine agent perspectives into coherent solutions.
    """

    def __init__(self):
        self._event_bus: Optional[EventBus] = None
        self._memory: Optional[SharedMemory] = None

        # Active sessions
        self._sessions: Dict[str, CollaborationSession] = {}

        # Synthesis strategies
        self._strategies: Dict[CollaborationMode, SynthesisStrategy] = {
            CollaborationMode.PARALLEL: WeightedAverageSynthesis(),
            CollaborationMode.CONSENSUS: ConsensusSynthesis(),
            CollaborationMode.VOTING: VotingSynthesis(),
        }

        # Pending contribution callbacks
        self._pending_responses: Dict[str, asyncio.Event] = {}

    async def initialize(self) -> bool:
        """Initialize connections."""
        try:
            self._event_bus = get_event_bus()
            self._memory = get_shared_memory()

            # Subscribe to agent responses
            self._event_bus.subscribe(EventType.AGENT_RESPONSE, self._handle_agent_response)

            logger.info("CollaborationEngine initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CollaborationEngine: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_session(
        self,
        problem: str,
        mode: CollaborationMode = CollaborationMode.PARALLEL,
        required_capabilities: Optional[List[AgentCapability]] = None,
        specific_agents: Optional[List[str]] = None,
        timeout_seconds: int = 300,
    ) -> CollaborationSession:
        """
        Create a new collaboration session.

        Args:
            problem: The problem to solve collaboratively
            mode: Collaboration mode to use
            required_capabilities: Capabilities needed for this problem
            specific_agents: Specific agents to include (optional)
            timeout_seconds: Session timeout

        Returns:
            Created CollaborationSession
        """
        session_id = f"collab-{uuid.uuid4().hex[:8]}"

        # Find participants
        participants = []
        registry = get_capability_registry()

        if specific_agents:
            participants = specific_agents
        elif required_capabilities:
            for cap in required_capabilities:
                agents = registry.find_by_capability(cap)
                for agent in agents:
                    if agent.agent_id not in participants:
                        participants.append(agent.agent_id)

        session = CollaborationSession(
            session_id=session_id,
            problem=problem,
            mode=mode,
            participants=participants,
            required_capabilities=required_capabilities or [],
            timeout_seconds=timeout_seconds,
        )

        self._sessions[session_id] = session
        logger.info(f"Created collaboration session {session_id} with {len(participants)} participants")

        return session

    async def start_session(self, session_id: str) -> bool:
        """Start a collaboration session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if session.status != CollaborationStatus.PENDING:
            return False

        session.status = CollaborationStatus.ACTIVE

        # Send requests to all participants
        for agent_id in session.participants:
            await self._request_contribution(session, agent_id)

        # Create response event
        self._pending_responses[session_id] = asyncio.Event()

        logger.info(f"Started collaboration session {session_id}")
        return True

    async def _request_contribution(
        self,
        session: CollaborationSession,
        agent_id: str,
    ) -> None:
        """Request a contribution from an agent."""
        message = create_agent_message(
            sender="collaboration_engine",
            recipient=agent_id,
            content=session.problem,
            message_type=MessageType.REQUEST,
            context={
                "session_id": session.session_id,
                "collaboration_mode": session.mode.value,
                "instruction": "Please provide your perspective on this problem.",
            },
        )

        await self._event_bus.publish(Event(
            event_type=EventType.AGENT_REQUEST,
            source="collaboration_engine",
            payload=message.to_dict(),
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTRIBUTION HANDLING
    # ═══════════════════════════════════════════════════════════════════════════

    def add_contribution(
        self,
        session_id: str,
        agent_id: str,
        content: str,
        confidence: float = 1.0,
        reasoning: Optional[str] = None,
    ) -> bool:
        """Add a contribution to a session."""
        session = self._sessions.get(session_id)
        if not session or session.status != CollaborationStatus.ACTIVE:
            return False

        # Get agent info
        registry = get_capability_registry()
        agent = registry.get_agent(agent_id)
        agent_name = agent.name if agent else agent_id

        contribution = AgentContribution(
            agent_id=agent_id,
            agent_name=agent_name,
            content=content,
            confidence=confidence,
            reasoning=reasoning,
        )

        session.contributions.append(contribution)
        logger.debug(f"Added contribution from {agent_id} to session {session_id}")

        # Check if all participants have contributed
        contributor_ids = {c.agent_id for c in session.contributions}
        if contributor_ids >= set(session.participants):
            # All have contributed, signal completion
            if session_id in self._pending_responses:
                self._pending_responses[session_id].set()

        return True

    async def _handle_agent_response(self, event: Event) -> None:
        """Handle agent response events."""
        payload = event.payload
        context = payload.get("context", {})
        session_id = context.get("session_id")

        if not session_id or session_id not in self._sessions:
            return

        self.add_contribution(
            session_id=session_id,
            agent_id=event.source,
            content=payload.get("content", ""),
            confidence=payload.get("confidence", 1.0),
            reasoning=payload.get("reasoning"),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SYNTHESIS
    # ═══════════════════════════════════════════════════════════════════════════

    async def wait_and_synthesize(
        self,
        session_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[str]:
        """
        Wait for contributions and synthesize results.

        Args:
            session_id: Session to wait for
            timeout: Override session timeout

        Returns:
            Synthesized result or None on timeout
        """
        session = self._sessions.get(session_id)
        if not session:
            return None

        wait_time = timeout or session.timeout_seconds

        # Wait for all contributions
        try:
            if session_id in self._pending_responses:
                await asyncio.wait_for(
                    self._pending_responses[session_id].wait(),
                    timeout=wait_time,
                )
        except asyncio.TimeoutError:
            logger.warning(f"Collaboration session {session_id} timed out")
            # Continue with partial contributions

        # Synthesize
        return await self.synthesize_session(session_id)

    async def synthesize_session(self, session_id: str) -> Optional[str]:
        """Synthesize contributions into final result."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        if not session.contributions:
            session.status = CollaborationStatus.FAILED
            return "No contributions received."

        session.status = CollaborationStatus.SYNTHESIZING

        # Get synthesis strategy
        strategy = self._strategies.get(
            session.mode,
            WeightedAverageSynthesis(),
        )

        # Synthesize
        try:
            synthesis = strategy.synthesize(session.contributions)
            session.synthesis = synthesis
            session.final_decision = synthesis
            session.status = CollaborationStatus.COMPLETED
            session.completed_at = datetime.utcnow().isoformat()

            logger.info(f"Synthesized collaboration session {session_id}")
            return synthesis

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            session.status = CollaborationStatus.FAILED
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # QUICK COLLABORATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def collaborate(
        self,
        problem: str,
        capabilities: List[AgentCapability],
        mode: CollaborationMode = CollaborationMode.PARALLEL,
        timeout_seconds: int = 120,
    ) -> str:
        """
        One-shot collaboration: create, start, wait, and return result.

        Args:
            problem: Problem to solve
            capabilities: Required agent capabilities
            mode: Collaboration mode
            timeout_seconds: Timeout

        Returns:
            Synthesized result
        """
        session = await self.create_session(
            problem=problem,
            mode=mode,
            required_capabilities=capabilities,
            timeout_seconds=timeout_seconds,
        )

        await self.start_session(session.session_id)
        result = await self.wait_and_synthesize(session.session_id)

        return result or "Collaboration failed to produce a result."

    # ═══════════════════════════════════════════════════════════════════════════
    # SESSION QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_active_sessions(self) -> List[CollaborationSession]:
        """Get all active sessions."""
        return [
            s for s in self._sessions.values()
            if s.status in [CollaborationStatus.PENDING, CollaborationStatus.ACTIVE]
        ]

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about collaboration sessions."""
        total = len(self._sessions)
        by_status = {}
        by_mode = {}

        for session in self._sessions.values():
            status = session.status.value
            by_status[status] = by_status.get(status, 0) + 1

            mode = session.mode.value
            by_mode[mode] = by_mode.get(mode, 0) + 1

        return {
            "total_sessions": total,
            "by_status": by_status,
            "by_mode": by_mode,
            "active_count": len(self.get_active_sessions()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_engine_instance: Optional[CollaborationEngine] = None


def get_collaboration_engine() -> CollaborationEngine:
    """Get the singleton CollaborationEngine instance."""
    global _engine_instance

    if _engine_instance is None:
        _engine_instance = CollaborationEngine()

    return _engine_instance


async def init_collaboration() -> CollaborationEngine:
    """Initialize and return the collaboration engine."""
    engine = get_collaboration_engine()
    await engine.initialize()
    return engine
