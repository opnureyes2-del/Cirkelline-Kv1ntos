"""
Historiker-Kommandant Interface
===============================

FASE 6: Multi-Bibliotek Arkitektur

Historiker-Kommandanten er ansvarlig for historisk bevaring
og kontekstualisering af viden inden for en given domane.

Ansvar:
    - Vedligeholder temporal kontekst for viden
    - Tracker evolution af viden over tid
    - Identificerer patterns og trends
    - Preserverer historiske versioner

Hver videndomane har sin egen Historiker der specialiserer
sig i domanens unikke historiske behov.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class EventType(Enum):
    """Typer af videns-events"""
    CREATED = "created"
    UPDATED = "updated"
    DEPRECATED = "deprecated"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    MERGED = "merged"
    SPLIT = "split"
    REFERENCED = "referenced"
    TREND_DETECTED = "trend_detected"
    PATTERN_EMERGED = "pattern_emerged"


class PatternStrength(Enum):
    """Styrke af identificerede patterns"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    DOMINANT = "dominant"


@dataclass
class KnowledgeEvent:
    """
    Et videns-event der registreres af Historikeren.

    Attributes:
        id: Unik identifikator
        domain: Videndomane (fx 'web3', 'legal')
        topic: Emne for eventet
        event_type: Type af event
        data: Event-specifikke data
        occurred_at: Tidspunkt for eventet
        source: Kilden til eventet
        context: Yderligere kontekst
    """
    domain: str
    topic: str
    event_type: EventType
    data: Dict[str, Any]
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineEntry:
    """En enkelt entry i en tidslinje"""
    timestamp: datetime
    event: KnowledgeEvent
    significance: float  # 0.0 - 1.0
    notes: Optional[str] = None


@dataclass
class Timeline:
    """
    En tidslinje for et emne.

    Attributes:
        topic: Emnet for tidslinjen
        domain: Videndomane
        entries: Liste af tidslinje entries
        start_date: Startdato
        end_date: Slutdato
        summary: Opsummering af tidslinjen
    """
    topic: str
    domain: str
    entries: List[TimelineEntry]
    start_date: datetime
    end_date: datetime
    summary: Optional[str] = None

    @property
    def event_count(self) -> int:
        return len(self.entries)

    @property
    def duration(self) -> timedelta:
        return self.end_date - self.start_date


@dataclass
class EvolutionReport:
    """
    Rapport over hvordan viden har udviklet sig.

    Attributes:
        topic: Emnet for rapporten
        domain: Videndomane
        period: Tidsperiode for analysen
        key_milestones: Vigtige milepale
        trends: Identificerede trends
        predictions: Forudsigelser baseret pa udviklingen
        confidence: Confidence score for rapporten
    """
    topic: str
    domain: str
    period: timedelta
    key_milestones: List[Dict[str, Any]]
    trends: List[str]
    predictions: List[str]
    confidence: float
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Pattern:
    """
    Et identificeret pattern i videns-udvikling.

    Attributes:
        id: Unik identifikator
        domain: Videndomane
        name: Navn pa patternet
        description: Beskrivelse
        strength: Styrke af patternet
        occurrences: Antal forekomster
        first_seen: Forste gang set
        last_seen: Sidste gang set
        related_topics: Relaterede emner
    """
    name: str
    description: str
    domain: str
    strength: PatternStrength
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    related_topics: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HistorikerKommandant(ABC):
    """
    Abstract base class for Historiker-Kommandant.

    Hver videndomane har sin egen Historiker der:
    - Vedligeholder temporal kontekst
    - Tracker evolution af viden over tid
    - Identificerer patterns og trends
    - Preserverer historiske versioner

    Subclasses skal implementere alle abstracte metoder.
    """

    def __init__(self, domain: str):
        """
        Initialiser Historiker for en specifik domane.

        Args:
            domain: Videndomane (fx 'web3', 'legal')
        """
        self.domain = domain
        self._initialized = False

    async def initialize(self) -> None:
        """Initialiser Historikeren med nødvendige ressourcer."""
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @abstractmethod
    async def record_event(self, event: KnowledgeEvent) -> None:
        """
        Registrer et videns-event med timestamp og kontekst.

        Args:
            event: Eventet der skal registreres

        Raises:
            ValueError: Hvis event er invalid
        """
        pass

    @abstractmethod
    async def get_timeline(
        self,
        topic: str,
        start: datetime,
        end: datetime
    ) -> Timeline:
        """
        Hent tidslinje for et emne.

        Args:
            topic: Emnet at hente tidslinje for
            start: Startdato
            end: Slutdato

        Returns:
            Timeline objekt med alle events i perioden
        """
        pass

    @abstractmethod
    async def analyze_evolution(self, topic: str) -> EvolutionReport:
        """
        Analyser hvordan viden om et emne har udviklet sig.

        Args:
            topic: Emnet at analysere

        Returns:
            EvolutionReport med analyse af udviklingen
        """
        pass

    @abstractmethod
    async def find_patterns(
        self,
        window: timedelta
    ) -> List[Pattern]:
        """
        Identificer patterns i videns-udvikling.

        Args:
            window: Tidsvindue at soge i

        Returns:
            Liste af identificerede patterns
        """
        pass

    async def get_recent_events(
        self,
        limit: int = 100
    ) -> List[KnowledgeEvent]:
        """
        Hent de seneste events.

        Args:
            limit: Maksimalt antal events at returnere

        Returns:
            Liste af de seneste events
        """
        end = datetime.utcnow()
        start = end - timedelta(days=30)
        timeline = await self.get_timeline("*", start, end)
        return [entry.event for entry in timeline.entries[:limit]]

    async def get_topic_history(
        self,
        topic: str,
        max_entries: int = 50
    ) -> List[KnowledgeEvent]:
        """
        Hent historik for et specifikt emne.

        Args:
            topic: Emnet at hente historik for
            max_entries: Maksimalt antal entries

        Returns:
            Liste af events for emnet
        """
        end = datetime.utcnow()
        start = datetime.min  # Fra begyndelsen
        timeline = await self.get_timeline(topic, start, end)
        return [entry.event for entry in timeline.entries[:max_entries]]


# Registry for historiker instances
_historiker_registry: Dict[str, HistorikerKommandant] = {}


def register_historiker(domain: str, historiker: HistorikerKommandant) -> None:
    """Registrer en Historiker for en domane."""
    _historiker_registry[domain] = historiker


def get_historiker(domain: str) -> Optional[HistorikerKommandant]:
    """
    Fa Historiker for en domane.

    Args:
        domain: Videndomane

    Returns:
        HistorikerKommandant instance eller None
    """
    return _historiker_registry.get(domain)


def list_registered_historikere() -> List[str]:
    """List alle registrerede Historiker domaner."""
    return list(_historiker_registry.keys())
