"""
CKC MASTERMIND Collective Awareness (DEL P)
=============================================

Universel opmærksomhed og fælles viden for MASTERMIND Tilstand.

Bygger på WaveCollector for at skabe delt bevidsthed mellem
alle kommandanter, specialister og dirigenter.

Grundprincip: Vi er alle i rummet og følger hinanden op.

CORE WISDOM (Grundviden):
-------------------------
"Når ét er godt og andet er bedre, er det IKKE ensbetydende med at
det ene skal skiftes ud og glemmes. Det ene er måske bedre i andre
sammenhænge, områder eller kombinationer."

Dette er fundamentalt for hvordan vi evaluerer og bevarer viden:
- Intet kasseres bare fordi noget "bedre" dukker op
- Kontekst bestemmer værdi
- Kombinationer skaber ny værdi
- Alt har sin plads i det rette øjeblik

Komponenter:
- CoreWisdom: Grundlæggende visdom i systemet
- SharedMemory: Fælles hukommelse mellem alle
- AwarenessState: Tilstand af fælles opmærksomhed
- CollectiveAwareness: Hovedklassen for universel bevidsthed
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .wave_collector import (
    Wave,
    WaveType,
    WaveOrigin,
    WaveCollector,
    CollectedWaves,
    get_wave_collector
)

logger = logging.getLogger(__name__)


# =============================================================================
# CORE WISDOM - GRUNDVIDEN I ØKOSYSTEMET
# =============================================================================

class CoreWisdom:
    """
    Grundlæggende visdom der gennemsyrer hele økosystemet.

    Disse principper er ikke regler der skal følges blindt,
    men vejledende visdom der informerer alle beslutninger.
    """

    # =========================================================================
    # PRINCIP 1: KONTEKSTUEL VÆRDI
    # =========================================================================

    CONTEXTUAL_VALUE = """
    Når ét er godt og andet er bedre, er det IKKE ensbetydende med at
    det ene skal skiftes ud og glemmes. Det ene er måske bedre i andre
    sammenhænge, områder eller kombinationer.

    Implikationer:
    - Evaluer altid i kontekst, ikke absolut
    - Bevar ældre løsninger - de kan være bedre i fremtidige situationer
    - Kombiner forskellige tilgange for bedste resultat
    - "Bedre" er altid relativt til opgave, tidspunkt og ressourcer
    """

    # =========================================================================
    # PRINCIP 2: FÆLLESSKABETS STYRKE
    # =========================================================================

    COLLECTIVE_STRENGTH = """
    Vi samler alt op i fællesskab. Intet går tabt.

    Implikationer:
    - Alle bidrag har værdi
    - Lyt til alle kilder, filtrer ikke for tidligt
    - Mønstre opstår fra mangfoldighed
    - Fælles hukommelse er stærkere end individuel
    """

    # =========================================================================
    # PRINCIP 3: TÆNK HØJT
    # =========================================================================

    THINK_ALOUD = """
    Transparent reasoning styrker fællesskabet.

    Implikationer:
    - Del tankeprocesser, ikke kun konklusioner
    - Usikkerhed er information, ikke svaghed
    - Andre kan bygge på dine tanker
    - Læring sker i åbenhed
    """

    # =========================================================================
    # PRINCIP 4: NATURLIG RYTME
    # =========================================================================

    NATURAL_RHYTHM = """
    Rutiner og ritualer skaber flow, ikke begrænsning.

    Implikationer:
    - Respekter processers naturlige tempo
    - Ikke alt skal optimeres
    - Pauser er produktive
    - Gentagelse skaber mestring
    """

    # =========================================================================
    # PRINCIP 5: FULD TRANSPARENS
    # =========================================================================

    FULL_TRANSPARENCY = """
    Alle veje bliver klargjort og vejledt samt fuldt ud vist
    igennem uden noget er uvist.

    Implikationer:
    - Ingen skjulte beslutninger eller processer
    - Alle muligheder eksplicit dokumenteret
    - Vejledning gennem hele flowet
    - Usikkerhed synliggøres og adresseres
    - Intet efterlades i mørket
    - Hver beslutning har en synlig reasoning-kæde
    """

    @classmethod
    def get_all_wisdom(cls) -> Dict[str, str]:
        """Hent al grundviden."""
        return {
            "contextual_value": cls.CONTEXTUAL_VALUE,
            "collective_strength": cls.COLLECTIVE_STRENGTH,
            "think_aloud": cls.THINK_ALOUD,
            "natural_rhythm": cls.NATURAL_RHYTHM,
            "full_transparency": cls.FULL_TRANSPARENCY
        }

    @classmethod
    def apply_to_decision(cls, options: List[Any], context: Dict[str, Any]) -> str:
        """
        Anvend visdom på en beslutning.

        Returnerer vejledning baseret på grundvisdom.
        """
        guidance = []

        # Princip 1: Kontekstuel værdi
        guidance.append(
            "Overvej: Er 'bedste' valg kontekst-afhængigt? "
            "Måske skal flere muligheder bevares."
        )

        # Princip 2: Fællesskab
        if context.get("multiple_sources"):
            guidance.append(
                "Alle kilder har bidraget. Ingen bør ignoreres."
            )

        # Princip 3: Tænk højt
        guidance.append(
            "Del din tankeproces med fællesskabet, ikke kun konklusionen."
        )

        return "\n".join(guidance)


# =============================================================================
# ENUMS
# =============================================================================

class AwarenessLevel(Enum):
    """Niveau af fælles opmærksomhed."""
    DORMANT = "dormant"       # Ingen aktiv opmærksomhed
    PERIPHERAL = "peripheral" # Svag baggrunds-opmærksomhed
    ATTENTIVE = "attentive"   # Fokuseret opmærksomhed
    HEIGHTENED = "heightened" # Forhøjet opmærksomhed
    UNIFIED = "unified"       # Fuld fælles bevidsthed


class MemoryType(Enum):
    """Type af fælles hukommelse."""
    FACTUAL = "factual"       # Fakta og data
    PROCEDURAL = "procedural" # Hvordan man gør ting
    EPISODIC = "episodic"     # Begivenheder og oplevelser
    SEMANTIC = "semantic"     # Betydninger og relationer
    WISDOM = "wisdom"         # Grundviden og principper


class InsightPriority(Enum):
    """Prioritet af indsigt."""
    BACKGROUND = 1    # Baggrundsinfo
    NORMAL = 2        # Normal vigtighed
    ELEVATED = 3      # Forhøjet vigtighed
    CRITICAL = 4      # Kritisk vigtig
    FOUNDATIONAL = 5  # Grundlæggende princip


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SharedMemory:
    """En delt hukommelse i fællesskabet."""
    memory_id: str
    memory_type: MemoryType
    content: Any
    source_ids: Set[str]  # Hvem bidrog til denne hukommelse
    contexts: List[str]   # Kontekster hvor denne hukommelse er relevant
    strength: float = 1.0  # 0.0-1.0, hvor stærk hukommelsen er
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    tags: Set[str] = field(default_factory=set)

    def access(self) -> Any:
        """Tilgå hukommelsen og opdater statistik."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        return self.content

    def strengthen(self, amount: float = 0.1) -> None:
        """Forstærk hukommelsen."""
        self.strength = min(1.0, self.strength + amount)

    def weaken(self, amount: float = 0.05) -> None:
        """Svæk hukommelsen over tid."""
        self.strength = max(0.0, self.strength - amount)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "content": str(self.content)[:200],
            "source_count": len(self.source_ids),
            "contexts": self.contexts,
            "strength": self.strength,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "tags": list(self.tags)
        }


@dataclass
class CollectiveInsight:
    """En fælles indsigt der er opstået."""
    insight_id: str
    content: str
    priority: InsightPriority
    contributing_waves: Set[str]  # Wave IDs der bidrog
    contributing_memories: Set[str]  # Memory IDs der bidrog
    confidence: float  # 0.0-1.0
    emerged_at: datetime = field(default_factory=datetime.now)
    acted_upon: bool = False
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "content": self.content,
            "priority": self.priority.value,
            "contributing_wave_count": len(self.contributing_waves),
            "contributing_memory_count": len(self.contributing_memories),
            "confidence": self.confidence,
            "emerged_at": self.emerged_at.isoformat(),
            "acted_upon": self.acted_upon
        }


@dataclass
class AwarenessState:
    """Tilstand af den fælles opmærksomhed."""
    level: AwarenessLevel
    focus_topics: Set[str]
    active_participants: Set[str]
    current_insights: List[CollectiveInsight]
    wave_intensity: float  # Samlet bølge-intensitet
    coherence: float  # Hvor sammenhængende er opmærksomheden (0.0-1.0)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "focus_topics": list(self.focus_topics),
            "active_participant_count": len(self.active_participants),
            "insight_count": len(self.current_insights),
            "wave_intensity": self.wave_intensity,
            "coherence": self.coherence,
            "timestamp": self.timestamp.isoformat()
        }


# =============================================================================
# SHARED MEMORY BANK
# =============================================================================

class SharedMemoryBank:
    """
    Fælles hukommelsesbank for alle i rummet.

    Alle kommandanter deler denne hukommelse.
    Intet glemmes - alt bevares i sin kontekst.
    """

    def __init__(self):
        self._memories: Dict[str, SharedMemory] = {}
        self._by_type: Dict[MemoryType, List[str]] = {t: [] for t in MemoryType}
        self._by_context: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()

        # Initialiser med Core Wisdom
        self._initialize_wisdom()

    def _initialize_wisdom(self) -> None:
        """Initialiser banken med grundviden."""
        wisdom = CoreWisdom.get_all_wisdom()
        for key, content in wisdom.items():
            memory = SharedMemory(
                memory_id=f"wisdom_{key}",
                memory_type=MemoryType.WISDOM,
                content=content,
                source_ids={"system"},
                contexts=["all", "decision_making", "evaluation"],
                strength=1.0,
                tags={"core_wisdom", "foundational", key}
            )
            self._memories[memory.memory_id] = memory
            self._by_type[MemoryType.WISDOM].append(memory.memory_id)

    async def store(self, memory: SharedMemory) -> None:
        """Gem en hukommelse."""
        async with self._lock:
            self._memories[memory.memory_id] = memory
            self._by_type[memory.memory_type].append(memory.memory_id)
            for context in memory.contexts:
                if context not in self._by_context:
                    self._by_context[context] = []
                self._by_context[context].append(memory.memory_id)

    async def recall(self, memory_id: str) -> Optional[SharedMemory]:
        """Hent en specifik hukommelse."""
        async with self._lock:
            memory = self._memories.get(memory_id)
            if memory:
                memory.access()
            return memory

    async def recall_by_context(self, context: str) -> List[SharedMemory]:
        """Hent alle hukommelser relevante for en kontekst."""
        async with self._lock:
            memory_ids = self._by_context.get(context, [])
            memories = []
            for mid in memory_ids:
                memory = self._memories.get(mid)
                if memory:
                    memory.access()
                    memories.append(memory)
            return memories

    async def recall_by_type(self, memory_type: MemoryType) -> List[SharedMemory]:
        """Hent alle hukommelser af en type."""
        async with self._lock:
            memory_ids = self._by_type.get(memory_type, [])
            return [self._memories[mid] for mid in memory_ids if mid in self._memories]

    async def recall_wisdom(self) -> List[SharedMemory]:
        """Hent al grundviden."""
        return await self.recall_by_type(MemoryType.WISDOM)

    async def search(
        self,
        query: str,
        contexts: Optional[List[str]] = None,
        min_strength: float = 0.0
    ) -> List[SharedMemory]:
        """Søg i hukommelser."""
        async with self._lock:
            results = []
            for memory in self._memories.values():
                # Filtrer efter styrke
                if memory.strength < min_strength:
                    continue

                # Filtrer efter kontekst
                if contexts and not any(c in memory.contexts for c in contexts):
                    continue

                # Simpel tekst-match
                content_str = str(memory.content).lower()
                if query.lower() in content_str:
                    results.append(memory)
                    continue

                # Match tags
                if any(query.lower() in tag.lower() for tag in memory.tags):
                    results.append(memory)

            return results

    async def decay(self, amount: float = 0.01) -> int:
        """Lad hukommelser svækkes over tid. Returnerer antal svækkede."""
        count = 0
        async with self._lock:
            for memory in self._memories.values():
                # Core wisdom svækkes aldrig
                if memory.memory_type == MemoryType.WISDOM:
                    continue
                memory.weaken(amount)
                count += 1
        return count

    @property
    def size(self) -> int:
        return len(self._memories)


# =============================================================================
# MAIN CLASS: COLLECTIVE AWARENESS
# =============================================================================

class CollectiveAwareness:
    """
    Universel opmærksomhed for MASTERMIND Tilstand.

    Skaber delt bevidsthed mellem alle deltagere.
    Alle er i rummet og følger hinanden op.

    Princip: "Fuldstændigt og universielt opmærksomme"
    """

    def __init__(
        self,
        wave_collector: Optional[WaveCollector] = None
    ):
        self._wave_collector = wave_collector or get_wave_collector()
        self._memory_bank = SharedMemoryBank()
        self._current_state = AwarenessState(
            level=AwarenessLevel.DORMANT,
            focus_topics=set(),
            active_participants=set(),
            current_insights=[],
            wave_intensity=0.0,
            coherence=0.0
        )
        self._insight_listeners: List[Callable[[CollectiveInsight], None]] = []
        self._active = False
        self._update_task: Optional[asyncio.Task] = None

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def awaken(self) -> None:
        """Væk den fælles opmærksomhed."""
        self._active = True
        self._current_state.level = AwarenessLevel.PERIPHERAL

        # Start opdaterings-loop
        self._update_task = asyncio.create_task(self._awareness_loop())

        # Lyt til bølger
        if self._wave_collector:
            self._wave_collector.add_listener(self._on_wave)

        logger.info("Collective Awareness vågnet")

    async def sleep(self) -> None:
        """Lad den fælles opmærksomhed hvile."""
        self._active = False
        self._current_state.level = AwarenessLevel.DORMANT

        if self._update_task:
            self._update_task.cancel()

        if self._wave_collector:
            self._wave_collector.remove_listener(self._on_wave)

        logger.info("Collective Awareness hviler")

    async def _awareness_loop(self) -> None:
        """Hovedloop for opmærksomhed."""
        while self._active:
            await asyncio.sleep(5)  # Opdater hvert 5. sekund

            try:
                # Saml bølger og analyser
                if self._wave_collector:
                    collected = await self._wave_collector.collect_all()
                    await self._process_collected_waves(collected)

                # Lad hukommelser svækkes langsomt
                await self._memory_bank.decay(0.001)

                # Opdater tilstand
                await self._update_state()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Fejl i awareness loop: {e}")

    def _on_wave(self, wave: Wave) -> None:
        """Callback når en ny bølge modtages."""
        # Opdater aktive deltagere
        self._current_state.active_participants.add(wave.source_id)

        # Opdater focus topics fra tags
        self._current_state.focus_topics.update(wave.tags)

    # =========================================================================
    # WAVE PROCESSING
    # =========================================================================

    async def _process_collected_waves(self, collected: CollectedWaves) -> None:
        """Processér samlede bølger."""
        if not collected.waves:
            return

        # Opdater intensitet
        self._current_state.wave_intensity = collected.total_intensity

        # Konverter interessante bølger til hukommelser
        for wave in collected.waves:
            if wave.intensity.value >= 3:  # NORMAL eller højere
                await self._wave_to_memory(wave)

        # Find indsigter fra mønstre
        for pattern in collected.patterns_found:
            if pattern.strength >= 0.5:
                insight = await self._pattern_to_insight(pattern, collected.waves)
                if insight:
                    self._current_state.current_insights.append(insight)
                    self._notify_insight(insight)

    async def _wave_to_memory(self, wave: Wave) -> SharedMemory:
        """Konverter en bølge til en hukommelse."""
        memory_type = self._wave_type_to_memory_type(wave.wave_type)

        memory = SharedMemory(
            memory_id=f"mem_{secrets.token_hex(8)}",
            memory_type=memory_type,
            content=wave.content,
            source_ids={wave.source_id},
            contexts=list(wave.tags) if wave.tags else ["general"],
            strength=wave.intensity.value / 6.0,  # Normaliser til 0-1
            tags=wave.tags.copy()
        )

        await self._memory_bank.store(memory)
        return memory

    def _wave_type_to_memory_type(self, wave_type: WaveType) -> MemoryType:
        """Map bølgetype til hukommelsestype."""
        mapping = {
            WaveType.THOUGHT: MemoryType.SEMANTIC,
            WaveType.OBSERVATION: MemoryType.FACTUAL,
            WaveType.INSIGHT: MemoryType.SEMANTIC,
            WaveType.QUESTION: MemoryType.SEMANTIC,
            WaveType.MEMORY: MemoryType.EPISODIC,
            WaveType.SIGNAL: MemoryType.FACTUAL,
            WaveType.EMOTION: MemoryType.EPISODIC,
            WaveType.INTENTION: MemoryType.PROCEDURAL,
            WaveType.REFLECTION: MemoryType.SEMANTIC,
            WaveType.DISCOVERY: MemoryType.FACTUAL
        }
        return mapping.get(wave_type, MemoryType.SEMANTIC)

    async def _pattern_to_insight(
        self,
        pattern,  # WavePattern
        waves: List[Wave]
    ) -> Optional[CollectiveInsight]:
        """Skab en indsigt fra et mønster."""
        # Find de bølger der er del af mønstret
        pattern_waves = [w for w in waves if w.wave_id in pattern.wave_ids]

        if not pattern_waves:
            return None

        # Generer indsigt baseret på mønstertype
        if "type_cluster" in pattern.pattern_type:
            content = f"Fælles fokus på {pattern.description}"
            priority = InsightPriority.NORMAL
        elif "tag_resonance" in pattern.pattern_type:
            content = f"Resonans i fællesskabet: {pattern.description}"
            priority = InsightPriority.ELEVATED
        elif pattern.pattern_type == "temporal_surge":
            content = f"Synkroniseret aktivitet: {pattern.description}"
            priority = InsightPriority.ELEVATED
        else:
            content = pattern.description
            priority = InsightPriority.NORMAL

        return CollectiveInsight(
            insight_id=f"insight_{secrets.token_hex(8)}",
            content=content,
            priority=priority,
            contributing_waves=pattern.wave_ids,
            contributing_memories=set(),
            confidence=pattern.strength
        )

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    async def _update_state(self) -> None:
        """Opdater opmærksomhedstilstand."""
        # Beregn niveau baseret på aktivitet
        participant_count = len(self._current_state.active_participants)
        topic_count = len(self._current_state.focus_topics)
        intensity = self._current_state.wave_intensity

        if intensity == 0 and participant_count == 0:
            level = AwarenessLevel.DORMANT
        elif intensity < 10 or participant_count < 2:
            level = AwarenessLevel.PERIPHERAL
        elif intensity < 30 or participant_count < 5:
            level = AwarenessLevel.ATTENTIVE
        elif intensity < 60:
            level = AwarenessLevel.HEIGHTENED
        else:
            level = AwarenessLevel.UNIFIED

        self._current_state.level = level

        # Beregn kohærens (hvor fokuseret er opmærksomheden)
        if topic_count == 0:
            coherence = 0.0
        elif topic_count <= 3:
            coherence = 1.0
        else:
            coherence = max(0.0, 1.0 - (topic_count - 3) * 0.1)

        self._current_state.coherence = coherence
        self._current_state.timestamp = datetime.now()

        # Ryd op i gamle insights
        cutoff = datetime.now() - timedelta(minutes=10)
        self._current_state.current_insights = [
            i for i in self._current_state.current_insights
            if i.emerged_at > cutoff
        ]

    # =========================================================================
    # PUBLIC INTERFACE
    # =========================================================================

    def get_state(self) -> AwarenessState:
        """Hent aktuel opmærksomhedstilstand."""
        return self._current_state

    async def get_relevant_wisdom(self, context: str) -> List[SharedMemory]:
        """Hent relevant grundviden for en kontekst."""
        wisdom = await self._memory_bank.recall_wisdom()
        return [w for w in wisdom if context in w.contexts or "all" in w.contexts]

    async def remember(
        self,
        content: Any,
        memory_type: MemoryType,
        contexts: List[str],
        source_id: str,
        tags: Optional[Set[str]] = None
    ) -> SharedMemory:
        """Gem noget i fælles hukommelse."""
        memory = SharedMemory(
            memory_id=f"mem_{secrets.token_hex(8)}",
            memory_type=memory_type,
            content=content,
            source_ids={source_id},
            contexts=contexts,
            tags=tags or set()
        )
        await self._memory_bank.store(memory)
        return memory

    async def recall(
        self,
        context: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        query: Optional[str] = None
    ) -> List[SharedMemory]:
        """Hent fra fælles hukommelse."""
        if query:
            return await self._memory_bank.search(
                query,
                contexts=[context] if context else None
            )
        elif context:
            return await self._memory_bank.recall_by_context(context)
        elif memory_type:
            return await self._memory_bank.recall_by_type(memory_type)
        else:
            return []

    async def get_insights(self) -> List[CollectiveInsight]:
        """Hent aktuelle fælles indsigter."""
        return self._current_state.current_insights

    async def apply_wisdom_to_decision(
        self,
        options: List[Any],
        context: Dict[str, Any]
    ) -> Tuple[str, List[SharedMemory]]:
        """
        Anvend grundviden på en beslutning.

        Returnerer vejledning og relevante hukommelser.
        """
        guidance = CoreWisdom.apply_to_decision(options, context)
        relevant_memories = await self._memory_bank.recall_wisdom()
        return guidance, relevant_memories

    # =========================================================================
    # INSIGHT LISTENERS
    # =========================================================================

    def add_insight_listener(
        self,
        callback: Callable[[CollectiveInsight], None]
    ) -> None:
        """Tilføj listener for nye indsigter."""
        self._insight_listeners.append(callback)

    def remove_insight_listener(
        self,
        callback: Callable[[CollectiveInsight], None]
    ) -> None:
        """Fjern insight listener."""
        if callback in self._insight_listeners:
            self._insight_listeners.remove(callback)

    def _notify_insight(self, insight: CollectiveInsight) -> None:
        """Notificer listeners om ny indsigt."""
        for listener in self._insight_listeners:
            try:
                listener(insight)
            except Exception as e:
                logger.error(f"Insight listener fejl: {e}")

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Hent status for collective awareness."""
        return {
            "active": self._active,
            "awareness_level": self._current_state.level.value,
            "state": self._current_state.to_dict(),
            "memory_bank_size": self._memory_bank.size,
            "insight_listener_count": len(self._insight_listeners)
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_collective_awareness_instance: Optional[CollectiveAwareness] = None


def create_collective_awareness(
    wave_collector: Optional[WaveCollector] = None
) -> CollectiveAwareness:
    """Opret en ny Collective Awareness."""
    global _collective_awareness_instance
    _collective_awareness_instance = CollectiveAwareness(wave_collector)
    return _collective_awareness_instance


def get_collective_awareness() -> Optional[CollectiveAwareness]:
    """Hent den aktive Collective Awareness."""
    return _collective_awareness_instance


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Core Wisdom
    "CoreWisdom",

    # Enums
    "AwarenessLevel",
    "MemoryType",
    "InsightPriority",

    # Data classes
    "SharedMemory",
    "CollectiveInsight",
    "AwarenessState",

    # Classes
    "SharedMemoryBank",
    "CollectiveAwareness",

    # Factory functions
    "create_collective_awareness",
    "get_collective_awareness",
]
