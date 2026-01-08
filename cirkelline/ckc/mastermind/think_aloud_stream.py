"""
CKC MASTERMIND Think Aloud Stream (DEL Q)
==========================================

Realtids "tænk højt" broadcast for MASTERMIND Tilstand.

Transparent reasoning - alle deler tankeprocesser, ikke kun konklusioner.
Bygger på CollectiveAwareness for at dele reasoning i fællesskabet.

Princip: "Tænk højt princip - del processen, ikke kun resultatet"

Komponenter:
- ThoughtFragment: Et fragment af en tankeproces
- ReasoningChain: En kæde af forbundne tanker
- ThinkAloudBroadcaster: Broadcaster af tankeprocesser
- ThinkAloudStream: Hovedklassen for tænk højt strøm
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set

from .wave_collector import (
    Wave,
    WaveType,
    WaveOrigin,
    WaveIntensity,
    WaveCollector,
    get_wave_collector
)
from .collective_awareness import (
    CollectiveAwareness,
    get_collective_awareness,
    SharedMemory,
    MemoryType
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ThoughtType(Enum):
    """Type af tanke i en tankeproces."""
    OBSERVATION = "observation"       # Noget jeg ser/bemærker
    HYPOTHESIS = "hypothesis"         # En hypotese jeg danner
    INFERENCE = "inference"           # En slutning jeg drager
    QUESTION = "question"             # Et spørgsmål der opstår
    DOUBT = "doubt"                   # Tvivl eller usikkerhed
    REALIZATION = "realization"       # En pludselig erkendelse
    CONNECTION = "connection"         # En forbindelse jeg ser
    CONSIDERATION = "consideration"   # Noget jeg overvejer
    DECISION = "decision"             # En beslutning jeg tager
    REFLECTION = "reflection"         # Refleksion over processen


class ReasoningStyle(Enum):
    """Stil af reasoning."""
    ANALYTICAL = "analytical"     # Logisk, step-by-step
    INTUITIVE = "intuitive"       # Intuitiv, følelsesbaseret
    CREATIVE = "creative"         # Kreativ, uortodoks
    CRITICAL = "critical"         # Kritisk, udfordrende
    EXPLORATORY = "exploratory"   # Udforskende, nysgerrig
    SYNTHESIZING = "synthesizing" # Sammenfattende, integrerende


class StreamState(Enum):
    """Tilstand af think aloud stream."""
    SILENT = "silent"           # Ingen aktiv tankestrøm
    THINKING = "thinking"       # Aktiv tænkning
    EXPLAINING = "explaining"   # Forklarer noget
    EXPLORING = "exploring"     # Udforsker muligheder
    CONCLUDING = "concluding"   # Når frem til konklusion


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ThoughtFragment:
    """
    Et fragment af en tankeproces.

    Repræsenterer et enkelt skridt i "tænk højt" processen.
    """
    fragment_id: str
    thinker_id: str       # Hvem tænker
    thought_type: ThoughtType
    content: str          # Selve tanken
    confidence: float     # 0.0-1.0 sikkerhed
    style: ReasoningStyle
    relates_to: Set[str] = field(default_factory=set)  # Fragment IDs
    triggered_by: Optional[str] = None  # Hvad udløste denne tanke
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fragment_id": self.fragment_id,
            "thinker_id": self.thinker_id,
            "thought_type": self.thought_type.value,
            "content": self.content,
            "confidence": self.confidence,
            "style": self.style.value,
            "relates_to": list(self.relates_to),
            "triggered_by": self.triggered_by,
            "timestamp": self.timestamp.isoformat()
        }

    def to_wave(self) -> Wave:
        """Konverter til en Wave for broadcast."""
        return Wave(
            wave_id=f"thought_{self.fragment_id}",
            wave_type=WaveType.THOUGHT,
            origin=WaveOrigin.KOMMANDANT,
            source_id=self.thinker_id,
            content=self.content,
            intensity=self._confidence_to_intensity(),
            context={
                "thought_type": self.thought_type.value,
                "style": self.style.value,
                "confidence": self.confidence
            },
            tags={self.thought_type.value, self.style.value}
        )

    def _confidence_to_intensity(self) -> WaveIntensity:
        """Map confidence til wave intensity."""
        if self.confidence < 0.2:
            return WaveIntensity.WHISPER
        elif self.confidence < 0.4:
            return WaveIntensity.GENTLE
        elif self.confidence < 0.6:
            return WaveIntensity.NORMAL
        elif self.confidence < 0.8:
            return WaveIntensity.STRONG
        else:
            return WaveIntensity.SURGE


@dataclass
class ReasoningChain:
    """
    En kæde af forbundne tanker.

    Viser hele tankeprocessen fra start til konklusion.
    """
    chain_id: str
    thinker_id: str
    topic: str
    fragments: List[ThoughtFragment] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    conclusion: Optional[str] = None
    confidence_evolution: List[float] = field(default_factory=list)

    def add_fragment(self, fragment: ThoughtFragment) -> None:
        """Tilføj et fragment til kæden."""
        self.fragments.append(fragment)
        self.confidence_evolution.append(fragment.confidence)

    def complete(self, conclusion: str) -> None:
        """Afslut kæden med en konklusion."""
        self.conclusion = conclusion
        self.completed_at = datetime.now()

    def get_flow(self) -> str:
        """Hent tankeflowet som tekst."""
        flow_parts = []
        for i, fragment in enumerate(self.fragments, 1):
            prefix = self._get_thought_prefix(fragment.thought_type)
            flow_parts.append(f"{i}. {prefix}: {fragment.content}")
        if self.conclusion:
            flow_parts.append(f"=> Konklusion: {self.conclusion}")
        return "\n".join(flow_parts)

    def _get_thought_prefix(self, thought_type: ThoughtType) -> str:
        """Hent dansk prefix for tanketype."""
        prefixes = {
            ThoughtType.OBSERVATION: "Jeg ser",
            ThoughtType.HYPOTHESIS: "Måske",
            ThoughtType.INFERENCE: "Derfor",
            ThoughtType.QUESTION: "Jeg undrer mig",
            ThoughtType.DOUBT: "Men vent",
            ThoughtType.REALIZATION: "Ah, jeg forstår",
            ThoughtType.CONNECTION: "Dette minder om",
            ThoughtType.CONSIDERATION: "Jeg overvejer",
            ThoughtType.DECISION: "Jeg beslutter",
            ThoughtType.REFLECTION: "Ved eftertanke"
        }
        return prefixes.get(thought_type, "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "thinker_id": self.thinker_id,
            "topic": self.topic,
            "fragment_count": len(self.fragments),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "conclusion": self.conclusion,
            "confidence_evolution": self.confidence_evolution,
            "flow": self.get_flow()
        }


@dataclass
class ThinkAloudSession:
    """En session af tænk højt aktivitet."""
    session_id: str
    participants: Set[str]
    chains: List[ReasoningChain]
    started_at: datetime = field(default_factory=datetime.now)
    current_focus: Optional[str] = None
    shared_insights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "participant_count": len(self.participants),
            "chain_count": len(self.chains),
            "started_at": self.started_at.isoformat(),
            "current_focus": self.current_focus,
            "shared_insights": self.shared_insights
        }


# =============================================================================
# THINK ALOUD BROADCASTER
# =============================================================================

class ThinkAloudBroadcaster:
    """
    Broadcaster for tænk højt strømme.

    Sender tankeprocesser ud til fællesskabet i realtid.
    Andre kan følge med og bygge videre på tankerne.
    """

    def __init__(self, wave_collector: Optional[WaveCollector] = None):
        self._wave_collector = wave_collector or get_wave_collector()
        self._listeners: List[Callable[[ThoughtFragment], None]] = []
        self._active_chains: Dict[str, ReasoningChain] = {}

    async def broadcast(self, fragment: ThoughtFragment) -> None:
        """Broadcast et tankefragment til alle."""
        # Konverter til wave og send til collector
        if self._wave_collector:
            wave = fragment.to_wave()
            await self._wave_collector.inject_wave(wave)

        # Notificer lokale listeners
        for listener in self._listeners:
            try:
                listener(fragment)
            except Exception as e:
                logger.error(f"Broadcast listener fejl: {e}")

        logger.debug(
            f"[{fragment.thinker_id}] Tænker højt: "
            f"{fragment.thought_type.value} - {fragment.content[:50]}..."
        )

    async def broadcast_chain(self, chain: ReasoningChain) -> None:
        """Broadcast en hel reasoning chain."""
        for fragment in chain.fragments:
            await self.broadcast(fragment)
            await asyncio.sleep(0.1)  # Lille pause mellem fragmenter

    def add_listener(self, callback: Callable[[ThoughtFragment], None]) -> None:
        """Tilføj listener for tankefragmenter."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[ThoughtFragment], None]) -> None:
        """Fjern listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)


# =============================================================================
# MAIN CLASS: THINK ALOUD STREAM
# =============================================================================

class ThinkAloudStream:
    """
    Realtids tænk højt strøm for MASTERMIND Tilstand.

    Muliggør transparent reasoning - alle deler tankeprocesser.
    Andre kan følge med, udfordre og bygge videre.

    Princip: "Tænk højt - del processen, ikke kun resultatet"
    """

    def __init__(
        self,
        wave_collector: Optional[WaveCollector] = None,
        collective_awareness: Optional[CollectiveAwareness] = None
    ):
        self._wave_collector = wave_collector or get_wave_collector()
        self._awareness = collective_awareness or get_collective_awareness()
        self._broadcaster = ThinkAloudBroadcaster(self._wave_collector)
        self._active_sessions: Dict[str, ThinkAloudSession] = {}
        self._my_chains: Dict[str, ReasoningChain] = {}  # Chains by thinker_id
        self._state = StreamState.SILENT

    # =========================================================================
    # THINKING INTERFACE
    # =========================================================================

    async def start_thinking(
        self,
        thinker_id: str,
        topic: str
    ) -> ReasoningChain:
        """Start en ny tankeproces."""
        chain = ReasoningChain(
            chain_id=f"chain_{secrets.token_hex(8)}",
            thinker_id=thinker_id,
            topic=topic
        )
        self._my_chains[thinker_id] = chain
        self._state = StreamState.THINKING

        # Broadcast at vi starter
        opening = ThoughtFragment(
            fragment_id=f"frag_{secrets.token_hex(6)}",
            thinker_id=thinker_id,
            thought_type=ThoughtType.OBSERVATION,
            content=f"Jeg begynder at tænke over: {topic}",
            confidence=1.0,
            style=ReasoningStyle.EXPLORATORY
        )
        chain.add_fragment(opening)
        await self._broadcaster.broadcast(opening)

        logger.info(f"[{thinker_id}] Starter tankeproces: {topic}")
        return chain

    async def think(
        self,
        thinker_id: str,
        content: str,
        thought_type: ThoughtType = ThoughtType.CONSIDERATION,
        confidence: float = 0.7,
        style: ReasoningStyle = ReasoningStyle.ANALYTICAL
    ) -> ThoughtFragment:
        """
        Tænk højt - del en tanke med fællesskabet.

        Dette er hovedmetoden for at dele tanker.
        """
        fragment = ThoughtFragment(
            fragment_id=f"frag_{secrets.token_hex(6)}",
            thinker_id=thinker_id,
            thought_type=thought_type,
            content=content,
            confidence=confidence,
            style=style
        )

        # Tilføj til aktiv chain hvis den eksisterer
        if thinker_id in self._my_chains:
            chain = self._my_chains[thinker_id]
            if chain.fragments:
                fragment.relates_to.add(chain.fragments[-1].fragment_id)
            chain.add_fragment(fragment)

        # Broadcast til alle
        await self._broadcaster.broadcast(fragment)

        return fragment

    async def observe(self, thinker_id: str, observation: str, confidence: float = 0.8) -> ThoughtFragment:
        """Del en observation."""
        return await self.think(
            thinker_id, observation,
            ThoughtType.OBSERVATION, confidence,
            ReasoningStyle.ANALYTICAL
        )

    async def hypothesize(self, thinker_id: str, hypothesis: str, confidence: float = 0.5) -> ThoughtFragment:
        """Fremsæt en hypotese."""
        return await self.think(
            thinker_id, hypothesis,
            ThoughtType.HYPOTHESIS, confidence,
            ReasoningStyle.CREATIVE
        )

    async def infer(self, thinker_id: str, inference: str, confidence: float = 0.7) -> ThoughtFragment:
        """Drag en slutning."""
        return await self.think(
            thinker_id, inference,
            ThoughtType.INFERENCE, confidence,
            ReasoningStyle.ANALYTICAL
        )

    async def question(self, thinker_id: str, question: str) -> ThoughtFragment:
        """Stil et spørgsmål til fællesskabet."""
        return await self.think(
            thinker_id, question,
            ThoughtType.QUESTION, 1.0,
            ReasoningStyle.EXPLORATORY
        )

    async def doubt(self, thinker_id: str, doubt: str, confidence: float = 0.4) -> ThoughtFragment:
        """Udtryk tvivl."""
        return await self.think(
            thinker_id, doubt,
            ThoughtType.DOUBT, confidence,
            ReasoningStyle.CRITICAL
        )

    async def realize(self, thinker_id: str, realization: str, confidence: float = 0.9) -> ThoughtFragment:
        """Del en erkendelse."""
        return await self.think(
            thinker_id, realization,
            ThoughtType.REALIZATION, confidence,
            ReasoningStyle.INTUITIVE
        )

    async def connect(self, thinker_id: str, connection: str, confidence: float = 0.6) -> ThoughtFragment:
        """Del en forbindelse du ser."""
        return await self.think(
            thinker_id, connection,
            ThoughtType.CONNECTION, confidence,
            ReasoningStyle.SYNTHESIZING
        )

    async def decide(self, thinker_id: str, decision: str, confidence: float = 0.8) -> ThoughtFragment:
        """Del en beslutning."""
        return await self.think(
            thinker_id, decision,
            ThoughtType.DECISION, confidence,
            ReasoningStyle.ANALYTICAL
        )

    async def reflect(self, thinker_id: str, reflection: str) -> ThoughtFragment:
        """Del en refleksion over processen."""
        return await self.think(
            thinker_id, reflection,
            ThoughtType.REFLECTION, 0.9,
            ReasoningStyle.SYNTHESIZING
        )

    async def conclude(
        self,
        thinker_id: str,
        conclusion: str
    ) -> ReasoningChain:
        """Afslut tankeprocessen med en konklusion."""
        if thinker_id not in self._my_chains:
            # Ingen aktiv chain, opret en simpel
            chain = await self.start_thinking(thinker_id, "Ad hoc konklusion")
        else:
            chain = self._my_chains[thinker_id]

        # Tilføj konklusion som fragment
        await self.decide(thinker_id, conclusion, 0.9)

        # Afslut chain
        chain.complete(conclusion)

        # Gem i collective awareness hvis tilgængelig
        if self._awareness:
            await self._awareness.remember(
                content=chain.to_dict(),
                memory_type=MemoryType.PROCEDURAL,
                contexts=[chain.topic, "reasoning"],
                source_id=thinker_id,
                tags={"reasoning_chain", chain.topic}
            )

        self._state = StreamState.SILENT
        logger.info(f"[{thinker_id}] Afsluttede tankeproces: {conclusion}")
        return chain

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    async def start_session(self, initiator_id: str) -> ThinkAloudSession:
        """Start en fælles tænk højt session."""
        session = ThinkAloudSession(
            session_id=f"tas_{secrets.token_hex(8)}",
            participants={initiator_id},
            chains=[]
        )
        self._active_sessions[session.session_id] = session
        logger.info(f"Tænk højt session startet: {session.session_id}")
        return session

    async def join_session(self, session_id: str, participant_id: str) -> bool:
        """Deltag i en aktiv session."""
        if session_id in self._active_sessions:
            self._active_sessions[session_id].participants.add(participant_id)
            return True
        return False

    def get_active_sessions(self) -> List[ThinkAloudSession]:
        """Hent alle aktive sessions."""
        return list(self._active_sessions.values())

    # =========================================================================
    # LISTENING
    # =========================================================================

    async def listen(self) -> AsyncIterator[ThoughtFragment]:
        """Lyt til andres tanker i realtid."""
        queue: asyncio.Queue[ThoughtFragment] = asyncio.Queue()

        def on_thought(fragment: ThoughtFragment) -> None:
            queue.put_nowait(fragment)

        self._broadcaster.add_listener(on_thought)
        try:
            while True:
                fragment = await queue.get()
                yield fragment
        finally:
            self._broadcaster.remove_listener(on_thought)

    def add_thought_listener(
        self,
        callback: Callable[[ThoughtFragment], None]
    ) -> None:
        """Tilføj listener for tanker."""
        self._broadcaster.add_listener(callback)

    def remove_thought_listener(
        self,
        callback: Callable[[ThoughtFragment], None]
    ) -> None:
        """Fjern thought listener."""
        self._broadcaster.remove_listener(callback)

    # =========================================================================
    # RETRIEVAL
    # =========================================================================

    def get_chain(self, thinker_id: str) -> Optional[ReasoningChain]:
        """Hent en thinkers aktive chain."""
        return self._my_chains.get(thinker_id)

    def get_all_chains(self) -> List[ReasoningChain]:
        """Hent alle aktive chains."""
        return list(self._my_chains.values())

    def get_state(self) -> StreamState:
        """Hent strømmens tilstand."""
        return self._state

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Hent status for think aloud stream."""
        return {
            "state": self._state.value,
            "active_thinkers": len(self._my_chains),
            "active_sessions": len(self._active_sessions),
            "chains": [c.to_dict() for c in self._my_chains.values()],
            "sessions": [s.to_dict() for s in self._active_sessions.values()]
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_think_aloud_stream_instance: Optional[ThinkAloudStream] = None


def create_think_aloud_stream(
    wave_collector: Optional[WaveCollector] = None,
    collective_awareness: Optional[CollectiveAwareness] = None
) -> ThinkAloudStream:
    """Opret en ny Think Aloud Stream."""
    global _think_aloud_stream_instance
    _think_aloud_stream_instance = ThinkAloudStream(
        wave_collector,
        collective_awareness
    )
    return _think_aloud_stream_instance


def get_think_aloud_stream() -> Optional[ThinkAloudStream]:
    """Hent den aktive Think Aloud Stream."""
    return _think_aloud_stream_instance


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ThoughtType",
    "ReasoningStyle",
    "StreamState",

    # Data classes
    "ThoughtFragment",
    "ReasoningChain",
    "ThinkAloudSession",

    # Classes
    "ThinkAloudBroadcaster",
    "ThinkAloudStream",

    # Factory functions
    "create_think_aloud_stream",
    "get_think_aloud_stream",
]
