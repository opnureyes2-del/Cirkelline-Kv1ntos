"""
CIRKELLINE MASTERMIND - DEL X: LearningLoop
============================================

Kontinuerlig lærings-motor til MASTERMIND systemet.
Samler erfaringer, identificerer mønstre, og foreslår forbedringer.

Forfatter: Cirkelline Team
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class ExperienceType(Enum):
    """Typer af erfaring systemet kan lære fra."""

    SUCCESS = "success"           # Vellykkede operationer
    FAILURE = "failure"           # Fejl og problemer
    USER_FEEDBACK = "user_feedback"  # Direkte brugerfeedback
    PERFORMANCE = "performance"   # Performance metrics
    DECISION = "decision"         # Beslutningsresultater
    INTERACTION = "interaction"   # Brugerinteraktioner
    ANOMALY = "anomaly"          # Uventede hændelser
    CORRECTION = "correction"     # Manuel korrektion


class PatternType(Enum):
    """Typer af mønstre der kan identificeres."""

    TEMPORAL = "temporal"         # Tidsmæssige mønstre
    BEHAVIORAL = "behavioral"     # Adfærdsmønstre
    CAUSAL = "causal"            # Årsag-virkning
    CORRELATIONAL = "correlational"  # Korrelationer
    SEQUENTIAL = "sequential"     # Sekvenser
    CLUSTERING = "clustering"     # Grupperinger
    TREND = "trend"              # Trends over tid


class InsightPriority(Enum):
    """Prioritet af lærings-indsigter."""

    CRITICAL = "critical"         # Kræver øjeblikkelig handling
    HIGH = "high"                # Vigtig forbedring
    MEDIUM = "medium"            # Moderat forbedring
    LOW = "low"                  # Nice-to-have
    INFORMATIONAL = "informational"  # Kun til info


class LearningPhase(Enum):
    """Faser i lærings-cyklussen."""

    COLLECTION = "collection"     # Samler data
    ANALYSIS = "analysis"         # Analyserer mønstre
    SYNTHESIS = "synthesis"       # Syntetiserer indsigter
    PROPOSAL = "proposal"         # Foreslår forbedringer
    IMPLEMENTATION = "implementation"  # Implementerer
    EVALUATION = "evaluation"     # Evaluerer effekt


class ImprovementStatus(Enum):
    """Status for en forbedring."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    IMPLEMENTING = "implementing"
    ACTIVE = "active"
    EVALUATING = "evaluating"
    PROVEN = "proven"
    REVERTED = "reverted"
    REJECTED = "rejected"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Experience:
    """En erfaring systemet kan lære fra."""

    experience_id: str
    experience_type: ExperienceType
    timestamp: datetime

    # Kontekst
    source: str                   # Hvor erfaringen kommer fra
    context: Dict[str, Any] = field(default_factory=dict)

    # Data
    data: Dict[str, Any] = field(default_factory=dict)
    outcome: Optional[str] = None
    outcome_value: Optional[float] = None  # -1.0 til 1.0

    # Metadata
    tags: List[str] = field(default_factory=list)
    related_experiences: List[str] = field(default_factory=list)

    # Læring
    learned: bool = False
    lessons: List[str] = field(default_factory=list)


@dataclass
class Pattern:
    """Et identificeret mønster."""

    pattern_id: str
    pattern_type: PatternType
    discovered_at: datetime

    # Beskrivelse
    name: str
    description: str

    # Statistik
    occurrences: int = 0
    confidence: float = 0.0       # 0.0 til 1.0
    significance: float = 0.0     # Statistisk signifikans

    # Data
    supporting_experiences: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)

    # Status
    validated: bool = False
    last_seen: Optional[datetime] = None


@dataclass
class LearningInsight:
    """En syntetiseret indsigt fra læring."""

    insight_id: str
    priority: InsightPriority
    created_at: datetime

    # Indhold
    title: str
    description: str
    evidence: List[str] = field(default_factory=list)  # Pattern/Experience IDs

    # Anbefaling
    recommendation: Optional[str] = None
    expected_impact: Optional[str] = None
    impact_score: float = 0.0     # 0.0 til 1.0

    # Status
    acknowledged: bool = False
    acted_upon: bool = False
    related_improvements: List[str] = field(default_factory=list)


@dataclass
class Improvement:
    """En foreslået eller aktiv forbedring."""

    improvement_id: str
    status: ImprovementStatus
    created_at: datetime

    # Beskrivelse
    title: str
    description: str
    insight_source: Optional[str] = None  # LearningInsight ID

    # Implementation
    implementation_plan: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)

    # Metrics
    baseline_metrics: Dict[str, float] = field(default_factory=dict)
    current_metrics: Dict[str, float] = field(default_factory=dict)
    target_metrics: Dict[str, float] = field(default_factory=dict)

    # Evaluering
    started_at: Optional[datetime] = None
    evaluation_period: timedelta = field(default_factory=lambda: timedelta(days=7))
    proven_at: Optional[datetime] = None

    # Resultat
    success_rate: Optional[float] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class LearningCycle:
    """En komplet lærings-cyklus."""

    cycle_id: str
    started_at: datetime
    current_phase: LearningPhase

    # Data
    experiences_collected: int = 0
    patterns_identified: int = 0
    insights_generated: int = 0
    improvements_proposed: int = 0

    # Timing
    phase_started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    # Resultater
    success: bool = False
    summary: Optional[str] = None


@dataclass
class LearningLoopStats:
    """Statistik for LearningLoop."""

    total_experiences: int = 0
    total_patterns: int = 0
    total_insights: int = 0
    total_improvements: int = 0

    proven_improvements: int = 0
    reverted_improvements: int = 0

    learning_cycles_completed: int = 0
    current_cycle: Optional[str] = None

    average_cycle_duration: Optional[float] = None  # Sekunder

    # Experience breakdown
    experiences_by_type: Dict[str, int] = field(default_factory=dict)

    # Pattern breakdown
    patterns_by_type: Dict[str, int] = field(default_factory=dict)

    last_learning_at: Optional[datetime] = None


# ============================================================================
# LEARNING LOOP KLASSE
# ============================================================================

class LearningLoop:
    """
    Kontinuerlig lærings-motor for MASTERMIND.

    Ansvar:
    - Samle erfaringer fra alle system-interaktioner
    - Identificere mønstre og trends
    - Syntetisere indsigter
    - Foreslå og tracke forbedringer
    - Evaluere forbedringers effekt
    """

    def __init__(
        self,
        experience_retention_days: int = 90,
        min_pattern_confidence: float = 0.7,
        min_pattern_occurrences: int = 3,
        auto_learning: bool = True,
        learning_interval_seconds: int = 3600,  # 1 time
    ):
        """
        Initialisér LearningLoop.

        Args:
            experience_retention_days: Hvor længe erfaringer gemmes
            min_pattern_confidence: Minimum confidence for mønstre
            min_pattern_occurrences: Minimum forekomster for mønster
            auto_learning: Automatisk kør lærings-cyklusser
            learning_interval_seconds: Interval mellem auto-læring
        """
        self._experience_retention = timedelta(days=experience_retention_days)
        self._min_confidence = min_pattern_confidence
        self._min_occurrences = min_pattern_occurrences
        self._auto_learning = auto_learning
        self._learning_interval = learning_interval_seconds

        # Data storage
        self._experiences: Dict[str, Experience] = {}
        self._patterns: Dict[str, Pattern] = {}
        self._insights: Dict[str, LearningInsight] = {}
        self._improvements: Dict[str, Improvement] = {}
        self._cycles: Dict[str, LearningCycle] = {}

        # Indekser for hurtig lookup
        self._experience_by_type: Dict[ExperienceType, Set[str]] = {
            t: set() for t in ExperienceType
        }
        self._experience_by_source: Dict[str, Set[str]] = {}
        self._pattern_by_type: Dict[PatternType, Set[str]] = {
            t: set() for t in PatternType
        }

        # Pattern detektorer
        self._pattern_detectors: Dict[PatternType, Callable] = {}
        self._register_default_detectors()

        # State
        self._running = False
        self._current_cycle: Optional[str] = None
        self._learning_task: Optional[asyncio.Task] = None

        # Callbacks
        self._insight_callbacks: List[Callable[[LearningInsight], None]] = []
        self._improvement_callbacks: List[Callable[[Improvement], None]] = []

        logger.info("LearningLoop initialiseret")

    # ========================================================================
    # ERFARING HÅNDTERING
    # ========================================================================

    async def record_experience(
        self,
        experience_type: ExperienceType,
        source: str,
        data: Dict[str, Any],
        outcome: Optional[str] = None,
        outcome_value: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Experience:
        """
        Registrér en ny erfaring.

        Args:
            experience_type: Type af erfaring
            source: Kilde til erfaringen
            data: Erfaring data
            outcome: Beskrivelse af resultat
            outcome_value: Numerisk værdi (-1.0 til 1.0)
            context: Yderligere kontekst
            tags: Tags for kategorisering

        Returns:
            Den oprettede Experience
        """
        experience = Experience(
            experience_id=f"exp_{uuid4().hex[:12]}",
            experience_type=experience_type,
            timestamp=datetime.now(),
            source=source,
            data=data,
            outcome=outcome,
            outcome_value=outcome_value,
            context=context or {},
            tags=tags or [],
        )

        # Gem erfaring
        self._experiences[experience.experience_id] = experience

        # Opdater indekser
        self._experience_by_type[experience_type].add(experience.experience_id)

        if source not in self._experience_by_source:
            self._experience_by_source[source] = set()
        self._experience_by_source[source].add(experience.experience_id)

        logger.debug(f"Erfaring registreret: {experience.experience_id} ({experience_type.value})")

        # Auto-cleanup gamle erfaringer
        await self._cleanup_old_experiences()

        return experience

    async def record_success(
        self,
        source: str,
        operation: str,
        details: Dict[str, Any],
        performance_ms: Optional[float] = None,
    ) -> Experience:
        """Convenience metode til at registrere succes."""
        data = {
            "operation": operation,
            "details": details,
        }
        if performance_ms is not None:
            data["performance_ms"] = performance_ms

        return await self.record_experience(
            experience_type=ExperienceType.SUCCESS,
            source=source,
            data=data,
            outcome="success",
            outcome_value=1.0,
        )

    async def record_failure(
        self,
        source: str,
        operation: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Experience:
        """Convenience metode til at registrere fejl."""
        data = {
            "operation": operation,
            "error": error,
            "details": details or {},
        }

        return await self.record_experience(
            experience_type=ExperienceType.FAILURE,
            source=source,
            data=data,
            outcome="failure",
            outcome_value=-1.0,
            tags=["error", "requires_attention"],
        )

    async def record_user_feedback(
        self,
        source: str,
        user_id: str,
        feedback_type: str,
        content: str,
        sentiment: float,  # -1.0 til 1.0
        context: Optional[Dict[str, Any]] = None,
    ) -> Experience:
        """Registrér brugerfeedback."""
        return await self.record_experience(
            experience_type=ExperienceType.USER_FEEDBACK,
            source=source,
            data={
                "user_id": user_id,
                "feedback_type": feedback_type,
                "content": content,
                "sentiment": sentiment,
            },
            outcome_value=sentiment,
            context=context or {},
            tags=["user_feedback"],
        )

    async def get_experience(self, experience_id: str) -> Optional[Experience]:
        """Hent en specifik erfaring."""
        return self._experiences.get(experience_id)

    async def get_experiences(
        self,
        experience_type: Optional[ExperienceType] = None,
        source: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Experience]:
        """
        Hent erfaringer med filtrering.

        Args:
            experience_type: Filtrer efter type
            source: Filtrer efter kilde
            since: Kun erfaringer efter denne tid
            limit: Maksimum antal

        Returns:
            Liste af Experience objekter
        """
        # Start med alle eller filtreret sæt
        if experience_type and source:
            exp_ids = self._experience_by_type[experience_type] & \
                     self._experience_by_source.get(source, set())
        elif experience_type:
            exp_ids = self._experience_by_type[experience_type]
        elif source:
            exp_ids = self._experience_by_source.get(source, set())
        else:
            exp_ids = set(self._experiences.keys())

        # Hent og filtrer
        experiences = []
        for exp_id in exp_ids:
            exp = self._experiences.get(exp_id)
            if exp:
                if since and exp.timestamp < since:
                    continue
                experiences.append(exp)

        # Sortér efter tid (nyeste først) og begræns
        experiences.sort(key=lambda e: e.timestamp, reverse=True)
        return experiences[:limit]

    # ========================================================================
    # MØNSTER DETEKTION
    # ========================================================================

    def _register_default_detectors(self):
        """Registrér standard mønster-detektorer."""
        self._pattern_detectors[PatternType.TEMPORAL] = self._detect_temporal_patterns
        self._pattern_detectors[PatternType.CORRELATIONAL] = self._detect_correlational_patterns
        self._pattern_detectors[PatternType.SEQUENTIAL] = self._detect_sequential_patterns
        self._pattern_detectors[PatternType.TREND] = self._detect_trend_patterns

    def register_pattern_detector(
        self,
        pattern_type: PatternType,
        detector: Callable[[List[Experience]], List[Pattern]],
    ):
        """Registrér en custom mønster-detektor."""
        self._pattern_detectors[pattern_type] = detector
        logger.info(f"Pattern detector registreret for: {pattern_type.value}")

    async def detect_patterns(
        self,
        experiences: Optional[List[Experience]] = None,
        pattern_types: Optional[List[PatternType]] = None,
    ) -> List[Pattern]:
        """
        Detektér mønstre i erfaringer.

        Args:
            experiences: Erfaringer at analysere (default: alle)
            pattern_types: Typer at søge efter (default: alle)

        Returns:
            Liste af opdagede Pattern objekter
        """
        if experiences is None:
            experiences = list(self._experiences.values())

        if pattern_types is None:
            pattern_types = list(self._pattern_detectors.keys())

        if not experiences:
            return []

        discovered = []

        for pattern_type in pattern_types:
            detector = self._pattern_detectors.get(pattern_type)
            if detector:
                try:
                    patterns = await asyncio.to_thread(detector, experiences)
                    for pattern in patterns:
                        # Validér mod minimumskrav
                        if pattern.confidence >= self._min_confidence and \
                           pattern.occurrences >= self._min_occurrences:
                            # Gem mønster
                            self._patterns[pattern.pattern_id] = pattern
                            self._pattern_by_type[pattern_type].add(pattern.pattern_id)
                            discovered.append(pattern)
                except Exception as e:
                    logger.error(f"Fejl i pattern detector {pattern_type.value}: {e}")

        logger.info(f"Opdagede {len(discovered)} nye mønstre")
        return discovered

    def _detect_temporal_patterns(self, experiences: List[Experience]) -> List[Pattern]:
        """Detektér tidsmæssige mønstre."""
        patterns = []

        # Gruppér efter time-of-day
        hour_counts: Dict[int, Dict[ExperienceType, int]] = {}
        for exp in experiences:
            hour = exp.timestamp.hour
            if hour not in hour_counts:
                hour_counts[hour] = {}
            if exp.experience_type not in hour_counts[hour]:
                hour_counts[hour][exp.experience_type] = 0
            hour_counts[hour][exp.experience_type] += 1

        # Find peak hours for failures
        failure_hours = []
        for hour, type_counts in hour_counts.items():
            failure_count = type_counts.get(ExperienceType.FAILURE, 0)
            total = sum(type_counts.values())
            if total >= self._min_occurrences and failure_count / total > 0.3:
                failure_hours.append((hour, failure_count / total))

        if failure_hours:
            patterns.append(Pattern(
                pattern_id=f"pat_{uuid4().hex[:8]}",
                pattern_type=PatternType.TEMPORAL,
                discovered_at=datetime.now(),
                name="Peak Failure Hours",
                description=f"Højere fejlrate i timer: {[h for h, _ in failure_hours]}",
                occurrences=sum(1 for h, _ in failure_hours),
                confidence=statistics.mean([r for _, r in failure_hours]),
                conditions={"failure_hours": failure_hours},
            ))

        return patterns

    def _detect_correlational_patterns(self, experiences: List[Experience]) -> List[Pattern]:
        """Detektér korrelationer mellem variabler."""
        patterns = []

        # Find korrelation mellem source og outcome
        source_outcomes: Dict[str, List[float]] = {}
        for exp in experiences:
            if exp.outcome_value is not None:
                if exp.source not in source_outcomes:
                    source_outcomes[exp.source] = []
                source_outcomes[exp.source].append(exp.outcome_value)

        # Find sources med konsistent negative outcomes
        for source, outcomes in source_outcomes.items():
            if len(outcomes) >= self._min_occurrences:
                avg = statistics.mean(outcomes)
                if avg < -0.3:  # Generelt negative
                    patterns.append(Pattern(
                        pattern_id=f"pat_{uuid4().hex[:8]}",
                        pattern_type=PatternType.CORRELATIONAL,
                        discovered_at=datetime.now(),
                        name=f"Problematic Source: {source}",
                        description=f"Source '{source}' har konsistent negative outcomes",
                        occurrences=len(outcomes),
                        confidence=abs(avg),
                        conditions={"source": source, "avg_outcome": avg},
                    ))

        return patterns

    def _detect_sequential_patterns(self, experiences: List[Experience]) -> List[Pattern]:
        """Detektér sekvenser af hændelser."""
        patterns = []

        # Sortér efter tid
        sorted_exp = sorted(experiences, key=lambda e: e.timestamp)

        # Find gentagne sekvenser af typer
        sequences: Dict[Tuple[str, ...], int] = {}
        window_size = 3

        for i in range(len(sorted_exp) - window_size + 1):
            window = sorted_exp[i:i + window_size]
            seq = tuple(e.experience_type.value for e in window)
            sequences[seq] = sequences.get(seq, 0) + 1

        # Find hyppige sekvenser
        for seq, count in sequences.items():
            if count >= self._min_occurrences:
                patterns.append(Pattern(
                    pattern_id=f"pat_{uuid4().hex[:8]}",
                    pattern_type=PatternType.SEQUENTIAL,
                    discovered_at=datetime.now(),
                    name=f"Recurring Sequence",
                    description=f"Sekvens {' -> '.join(seq)} forekommer hyppigt",
                    occurrences=count,
                    confidence=min(count / 10, 1.0),
                    conditions={"sequence": seq},
                ))

        return patterns

    def _detect_trend_patterns(self, experiences: List[Experience]) -> List[Pattern]:
        """Detektér trends over tid."""
        patterns = []

        if len(experiences) < 10:
            return patterns

        # Sortér og opdel i perioder
        sorted_exp = sorted(experiences, key=lambda e: e.timestamp)
        mid = len(sorted_exp) // 2
        first_half = sorted_exp[:mid]
        second_half = sorted_exp[mid:]

        # Sammenlign outcome values
        first_outcomes = [e.outcome_value for e in first_half if e.outcome_value is not None]
        second_outcomes = [e.outcome_value for e in second_half if e.outcome_value is not None]

        if first_outcomes and second_outcomes:
            first_avg = statistics.mean(first_outcomes)
            second_avg = statistics.mean(second_outcomes)
            change = second_avg - first_avg

            if abs(change) > 0.2:  # Signifikant ændring
                direction = "forbedring" if change > 0 else "forværring"
                patterns.append(Pattern(
                    pattern_id=f"pat_{uuid4().hex[:8]}",
                    pattern_type=PatternType.TREND,
                    discovered_at=datetime.now(),
                    name=f"Outcome Trend: {direction}",
                    description=f"Outcomes viser {direction} over tid ({change:+.2f})",
                    occurrences=len(experiences),
                    confidence=min(abs(change) * 2, 1.0),
                    conditions={
                        "direction": direction,
                        "change": change,
                        "first_avg": first_avg,
                        "second_avg": second_avg,
                    },
                ))

        return patterns

    async def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """Hent et specifikt mønster."""
        return self._patterns.get(pattern_id)

    async def get_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        min_confidence: Optional[float] = None,
    ) -> List[Pattern]:
        """Hent mønstre med filtrering."""
        if pattern_type:
            pattern_ids = self._pattern_by_type.get(pattern_type, set())
        else:
            pattern_ids = set(self._patterns.keys())

        patterns = []
        for pid in pattern_ids:
            pattern = self._patterns.get(pid)
            if pattern:
                if min_confidence and pattern.confidence < min_confidence:
                    continue
                patterns.append(pattern)

        return sorted(patterns, key=lambda p: p.confidence, reverse=True)

    # ========================================================================
    # INDSIGT SYNTESE
    # ========================================================================

    async def synthesize_insights(
        self,
        patterns: Optional[List[Pattern]] = None,
    ) -> List[LearningInsight]:
        """
        Syntetisér indsigter fra mønstre.

        Args:
            patterns: Mønstre at analysere (default: alle)

        Returns:
            Liste af genererede LearningInsight objekter
        """
        if patterns is None:
            patterns = list(self._patterns.values())

        insights = []

        for pattern in patterns:
            insight = await self._create_insight_from_pattern(pattern)
            if insight:
                self._insights[insight.insight_id] = insight
                insights.append(insight)

                # Notify callbacks
                for callback in self._insight_callbacks:
                    try:
                        callback(insight)
                    except Exception as e:
                        logger.error(f"Insight callback fejl: {e}")

        logger.info(f"Syntetiserede {len(insights)} indsigter")
        return insights

    async def _create_insight_from_pattern(
        self,
        pattern: Pattern,
    ) -> Optional[LearningInsight]:
        """Opret indsigt fra et mønster."""
        # Bestem prioritet baseret på pattern type og confidence
        if pattern.pattern_type == PatternType.TREND:
            conditions = pattern.conditions
            if conditions.get("direction") == "forværring":
                priority = InsightPriority.HIGH
            else:
                priority = InsightPriority.MEDIUM
        elif pattern.pattern_type == PatternType.CORRELATIONAL:
            priority = InsightPriority.HIGH if pattern.confidence > 0.8 else InsightPriority.MEDIUM
        else:
            priority = InsightPriority.LOW if pattern.confidence < 0.7 else InsightPriority.MEDIUM

        # Generer anbefaling
        recommendation = self._generate_recommendation(pattern)

        insight = LearningInsight(
            insight_id=f"ins_{uuid4().hex[:8]}",
            priority=priority,
            created_at=datetime.now(),
            title=pattern.name,
            description=pattern.description,
            evidence=[pattern.pattern_id],
            recommendation=recommendation,
            impact_score=pattern.confidence * 0.8,
        )

        return insight

    def _generate_recommendation(self, pattern: Pattern) -> str:
        """Generer anbefaling baseret på mønster."""
        if pattern.pattern_type == PatternType.TEMPORAL:
            hours = pattern.conditions.get("failure_hours", [])
            return f"Overvej at øge ressourcer eller overvågning i timer: {[h for h, _ in hours]}"

        elif pattern.pattern_type == PatternType.CORRELATIONAL:
            source = pattern.conditions.get("source", "unknown")
            return f"Undersøg og optimer source '{source}' som viser konsistente problemer"

        elif pattern.pattern_type == PatternType.SEQUENTIAL:
            seq = pattern.conditions.get("sequence", [])
            return f"Undersøg årsag til gentagne sekvenser: {' -> '.join(seq)}"

        elif pattern.pattern_type == PatternType.TREND:
            direction = pattern.conditions.get("direction", "unknown")
            if direction == "forværring":
                return "Identificér og adresser årsag til faldende performance"
            else:
                return "Fortsæt nuværende strategi som viser forbedring"

        return "Yderligere analyse anbefales"

    async def get_insight(self, insight_id: str) -> Optional[LearningInsight]:
        """Hent en specifik indsigt."""
        return self._insights.get(insight_id)

    async def get_insights(
        self,
        priority: Optional[InsightPriority] = None,
        unacknowledged_only: bool = False,
    ) -> List[LearningInsight]:
        """Hent indsigter med filtrering."""
        insights = []
        for insight in self._insights.values():
            if priority and insight.priority != priority:
                continue
            if unacknowledged_only and insight.acknowledged:
                continue
            insights.append(insight)

        return sorted(insights, key=lambda i: (
            i.priority.value,
            -i.impact_score,
        ))

    async def acknowledge_insight(self, insight_id: str) -> bool:
        """Markér indsigt som set."""
        insight = self._insights.get(insight_id)
        if insight:
            insight.acknowledged = True
            return True
        return False

    # ========================================================================
    # FORBEDRINGER
    # ========================================================================

    async def propose_improvement(
        self,
        title: str,
        description: str,
        insight_id: Optional[str] = None,
        implementation_plan: Optional[List[str]] = None,
        affected_components: Optional[List[str]] = None,
        target_metrics: Optional[Dict[str, float]] = None,
    ) -> Improvement:
        """
        Foreslå en forbedring.

        Args:
            title: Titel på forbedring
            description: Beskrivelse
            insight_id: Relateret indsigt
            implementation_plan: Trin til implementation
            affected_components: Komponenter der påvirkes
            target_metrics: Målsætninger

        Returns:
            Den oprettede Improvement
        """
        improvement = Improvement(
            improvement_id=f"imp_{uuid4().hex[:8]}",
            status=ImprovementStatus.PROPOSED,
            created_at=datetime.now(),
            title=title,
            description=description,
            insight_source=insight_id,
            implementation_plan=implementation_plan or [],
            affected_components=affected_components or [],
            target_metrics=target_metrics or {},
        )

        self._improvements[improvement.improvement_id] = improvement

        # Link til indsigt
        if insight_id:
            insight = self._insights.get(insight_id)
            if insight:
                insight.related_improvements.append(improvement.improvement_id)

        # Notify callbacks
        for callback in self._improvement_callbacks:
            try:
                callback(improvement)
            except Exception as e:
                logger.error(f"Improvement callback fejl: {e}")

        logger.info(f"Forbedring foreslået: {improvement.improvement_id}")
        return improvement

    async def approve_improvement(
        self,
        improvement_id: str,
        baseline_metrics: Optional[Dict[str, float]] = None,
    ) -> bool:
        """Godkend en forbedring til implementation."""
        improvement = self._improvements.get(improvement_id)
        if not improvement or improvement.status != ImprovementStatus.PROPOSED:
            return False

        improvement.status = ImprovementStatus.APPROVED
        if baseline_metrics:
            improvement.baseline_metrics = baseline_metrics

        logger.info(f"Forbedring godkendt: {improvement_id}")
        return True

    async def start_improvement(
        self,
        improvement_id: str,
    ) -> bool:
        """Start implementation af forbedring."""
        improvement = self._improvements.get(improvement_id)
        if not improvement or improvement.status != ImprovementStatus.APPROVED:
            return False

        improvement.status = ImprovementStatus.IMPLEMENTING
        improvement.started_at = datetime.now()

        logger.info(f"Forbedring startet: {improvement_id}")
        return True

    async def activate_improvement(
        self,
        improvement_id: str,
    ) -> bool:
        """Aktivér forbedring og start evaluering."""
        improvement = self._improvements.get(improvement_id)
        if not improvement or improvement.status != ImprovementStatus.IMPLEMENTING:
            return False

        improvement.status = ImprovementStatus.ACTIVE

        logger.info(f"Forbedring aktiveret: {improvement_id}")
        return True

    async def update_improvement_metrics(
        self,
        improvement_id: str,
        metrics: Dict[str, float],
    ) -> bool:
        """Opdater metrics for en aktiv forbedring."""
        improvement = self._improvements.get(improvement_id)
        if not improvement or improvement.status not in [
            ImprovementStatus.ACTIVE,
            ImprovementStatus.EVALUATING,
        ]:
            return False

        improvement.current_metrics.update(metrics)
        return True

    async def evaluate_improvement(
        self,
        improvement_id: str,
    ) -> Optional[bool]:
        """
        Evaluér om forbedring har haft effekt.

        Returns:
            True hvis forbedring har positiv effekt, False hvis negativ, None hvis uafklaret
        """
        improvement = self._improvements.get(improvement_id)
        if not improvement:
            return None

        improvement.status = ImprovementStatus.EVALUATING

        # Sammenlign baseline med current
        if not improvement.baseline_metrics or not improvement.current_metrics:
            return None

        improvements_count = 0
        regressions_count = 0

        for metric, baseline in improvement.baseline_metrics.items():
            current = improvement.current_metrics.get(metric)
            target = improvement.target_metrics.get(metric)

            if current is not None:
                if target is not None:
                    # Har vi nået target?
                    if (target > baseline and current >= target) or \
                       (target < baseline and current <= target):
                        improvements_count += 1
                    elif (target > baseline and current < baseline) or \
                         (target < baseline and current > baseline):
                        regressions_count += 1
                else:
                    # Generel forbedring (antag højere er bedre)
                    if current > baseline:
                        improvements_count += 1
                    elif current < baseline:
                        regressions_count += 1

        total = improvements_count + regressions_count
        if total == 0:
            return None

        success_rate = improvements_count / total
        improvement.success_rate = success_rate

        return success_rate > 0.5

    async def prove_improvement(self, improvement_id: str) -> bool:
        """Markér forbedring som bevist."""
        improvement = self._improvements.get(improvement_id)
        if not improvement:
            return False

        improvement.status = ImprovementStatus.PROVEN
        improvement.proven_at = datetime.now()

        logger.info(f"Forbedring bevist: {improvement_id}")
        return True

    async def revert_improvement(
        self,
        improvement_id: str,
        reason: str,
    ) -> bool:
        """Tilbagerul en forbedring."""
        improvement = self._improvements.get(improvement_id)
        if not improvement:
            return False

        improvement.status = ImprovementStatus.REVERTED
        improvement.notes.append(f"Reverted: {reason}")

        logger.info(f"Forbedring tilbagerullet: {improvement_id} - {reason}")
        return True

    async def get_improvement(self, improvement_id: str) -> Optional[Improvement]:
        """Hent en specifik forbedring."""
        return self._improvements.get(improvement_id)

    async def get_improvements(
        self,
        status: Optional[ImprovementStatus] = None,
    ) -> List[Improvement]:
        """Hent forbedringer med filtrering."""
        improvements = []
        for imp in self._improvements.values():
            if status and imp.status != status:
                continue
            improvements.append(imp)

        return sorted(improvements, key=lambda i: i.created_at, reverse=True)

    # ========================================================================
    # LÆRINGS-CYKLUS
    # ========================================================================

    async def run_learning_cycle(self) -> LearningCycle:
        """
        Kør en komplet lærings-cyklus.

        Faser:
        1. Collection - Samle nylige erfaringer
        2. Analysis - Detektér mønstre
        3. Synthesis - Syntetisér indsigter
        4. Proposal - Foreslå forbedringer
        5. Evaluation - Evaluér aktive forbedringer
        """
        cycle = LearningCycle(
            cycle_id=f"cyc_{uuid4().hex[:8]}",
            started_at=datetime.now(),
            current_phase=LearningPhase.COLLECTION,
        )
        self._cycles[cycle.cycle_id] = cycle
        self._current_cycle = cycle.cycle_id

        logger.info(f"Lærings-cyklus startet: {cycle.cycle_id}")

        try:
            # FASE 1: Collection
            cycle.current_phase = LearningPhase.COLLECTION
            cycle.phase_started_at = datetime.now()

            recent_experiences = await self.get_experiences(
                since=datetime.now() - timedelta(hours=24),
                limit=1000,
            )
            cycle.experiences_collected = len(recent_experiences)

            # FASE 2: Analysis
            cycle.current_phase = LearningPhase.ANALYSIS
            cycle.phase_started_at = datetime.now()

            patterns = await self.detect_patterns(recent_experiences)
            cycle.patterns_identified = len(patterns)

            # FASE 3: Synthesis
            cycle.current_phase = LearningPhase.SYNTHESIS
            cycle.phase_started_at = datetime.now()

            insights = await self.synthesize_insights(patterns)
            cycle.insights_generated = len(insights)

            # FASE 4: Proposal (for high priority insights)
            cycle.current_phase = LearningPhase.PROPOSAL
            cycle.phase_started_at = datetime.now()

            for insight in insights:
                if insight.priority in [InsightPriority.CRITICAL, InsightPriority.HIGH]:
                    await self.propose_improvement(
                        title=f"Auto: {insight.title}",
                        description=insight.recommendation or insight.description,
                        insight_id=insight.insight_id,
                    )
                    cycle.improvements_proposed += 1

            # FASE 5: Evaluation
            cycle.current_phase = LearningPhase.EVALUATION
            cycle.phase_started_at = datetime.now()

            active_improvements = await self.get_improvements(
                status=ImprovementStatus.ACTIVE
            )
            for imp in active_improvements:
                if imp.started_at:
                    time_active = datetime.now() - imp.started_at
                    if time_active >= imp.evaluation_period:
                        result = await self.evaluate_improvement(imp.improvement_id)
                        if result is True:
                            await self.prove_improvement(imp.improvement_id)

            # Færdig
            cycle.ended_at = datetime.now()
            cycle.success = True
            cycle.summary = (
                f"Cyklus færdig: {cycle.experiences_collected} erfaringer, "
                f"{cycle.patterns_identified} mønstre, {cycle.insights_generated} indsigter, "
                f"{cycle.improvements_proposed} forbedringer foreslået"
            )

            logger.info(cycle.summary)

        except Exception as e:
            cycle.ended_at = datetime.now()
            cycle.success = False
            cycle.summary = f"Cyklus fejlede: {str(e)}"
            logger.error(cycle.summary)

        self._current_cycle = None
        return cycle

    async def start(self):
        """Start automatisk lærings-loop."""
        if self._running:
            return

        self._running = True

        if self._auto_learning:
            self._learning_task = asyncio.create_task(self._auto_learning_loop())

        logger.info("LearningLoop startet")

    async def stop(self):
        """Stop automatisk lærings-loop."""
        self._running = False

        if self._learning_task:
            self._learning_task.cancel()
            try:
                await self._learning_task
            except asyncio.CancelledError:
                pass
            self._learning_task = None

        logger.info("LearningLoop stoppet")

    async def _auto_learning_loop(self):
        """Baggrunds-task til automatisk læring."""
        while self._running:
            try:
                await asyncio.sleep(self._learning_interval)
                if self._running:
                    await self.run_learning_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-learning fejl: {e}")
                await asyncio.sleep(60)  # Vent før næste forsøg

    # ========================================================================
    # CALLBACKS
    # ========================================================================

    def on_insight(self, callback: Callable[[LearningInsight], None]):
        """Registrér callback for nye indsigter."""
        self._insight_callbacks.append(callback)

    def on_improvement(self, callback: Callable[[Improvement], None]):
        """Registrér callback for nye forbedringer."""
        self._improvement_callbacks.append(callback)

    # ========================================================================
    # STATISTIK OG VEDLIGEHOLDELSE
    # ========================================================================

    async def get_stats(self) -> LearningLoopStats:
        """Hent statistik for LearningLoop."""
        # Experience breakdown
        exp_by_type = {}
        for exp_type in ExperienceType:
            exp_by_type[exp_type.value] = len(self._experience_by_type[exp_type])

        # Pattern breakdown
        pat_by_type = {}
        for pat_type in PatternType:
            pat_by_type[pat_type.value] = len(self._pattern_by_type.get(pat_type, set()))

        # Improvement stats
        proven = sum(1 for i in self._improvements.values()
                     if i.status == ImprovementStatus.PROVEN)
        reverted = sum(1 for i in self._improvements.values()
                       if i.status == ImprovementStatus.REVERTED)

        # Cycle stats
        completed_cycles = [c for c in self._cycles.values() if c.success]
        avg_duration = None
        if completed_cycles:
            durations = [
                (c.ended_at - c.started_at).total_seconds()
                for c in completed_cycles if c.ended_at
            ]
            if durations:
                avg_duration = statistics.mean(durations)

        # Last learning
        last_learning = None
        if completed_cycles:
            last_learning = max(c.ended_at for c in completed_cycles if c.ended_at)

        return LearningLoopStats(
            total_experiences=len(self._experiences),
            total_patterns=len(self._patterns),
            total_insights=len(self._insights),
            total_improvements=len(self._improvements),
            proven_improvements=proven,
            reverted_improvements=reverted,
            learning_cycles_completed=len(completed_cycles),
            current_cycle=self._current_cycle,
            average_cycle_duration=avg_duration,
            experiences_by_type=exp_by_type,
            patterns_by_type=pat_by_type,
            last_learning_at=last_learning,
        )

    async def _cleanup_old_experiences(self):
        """Fjern gamle erfaringer."""
        cutoff = datetime.now() - self._experience_retention
        to_remove = []

        for exp_id, exp in self._experiences.items():
            if exp.timestamp < cutoff:
                to_remove.append(exp_id)

        for exp_id in to_remove:
            exp = self._experiences.pop(exp_id)
            self._experience_by_type[exp.experience_type].discard(exp_id)
            if exp.source in self._experience_by_source:
                self._experience_by_source[exp.source].discard(exp_id)

        if to_remove:
            logger.debug(f"Fjernet {len(to_remove)} gamle erfaringer")


# ============================================================================
# FACTORY FUNKTIONER
# ============================================================================

_learning_loop_instance: Optional[LearningLoop] = None


def create_learning_loop(**kwargs) -> LearningLoop:
    """
    Opret en ny LearningLoop instans.

    Args:
        **kwargs: Parametre til LearningLoop

    Returns:
        Ny LearningLoop instans
    """
    global _learning_loop_instance
    _learning_loop_instance = LearningLoop(**kwargs)
    return _learning_loop_instance


def get_learning_loop() -> Optional[LearningLoop]:
    """Hent global LearningLoop instans."""
    return _learning_loop_instance


def set_learning_loop(instance: LearningLoop):
    """Sæt global LearningLoop instans."""
    global _learning_loop_instance
    _learning_loop_instance = instance


# ============================================================================
# CONVENIENCE FUNKTIONER
# ============================================================================

async def learn_from_success(
    source: str,
    operation: str,
    details: Dict[str, Any],
    performance_ms: Optional[float] = None,
) -> Optional[Experience]:
    """
    Convenience: Registrér succes erfaring.

    Args:
        source: Kilde til succes
        operation: Operation der lykkedes
        details: Detaljer
        performance_ms: Performance i millisekunder

    Returns:
        Experience hvis LearningLoop er aktiv, ellers None
    """
    loop = get_learning_loop()
    if loop:
        return await loop.record_success(source, operation, details, performance_ms)
    return None


async def learn_from_failure(
    source: str,
    operation: str,
    error: str,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[Experience]:
    """
    Convenience: Registrér fejl erfaring.

    Args:
        source: Kilde til fejl
        operation: Operation der fejlede
        error: Fejlmeddelelse
        details: Yderligere detaljer

    Returns:
        Experience hvis LearningLoop er aktiv, ellers None
    """
    loop = get_learning_loop()
    if loop:
        return await loop.record_failure(source, operation, error, details)
    return None


async def learn_from_feedback(
    source: str,
    user_id: str,
    feedback_type: str,
    content: str,
    sentiment: float,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Experience]:
    """
    Convenience: Registrér brugerfeedback.

    Args:
        source: Kilde
        user_id: Bruger ID
        feedback_type: Type af feedback
        content: Feedback indhold
        sentiment: Sentiment score (-1.0 til 1.0)
        context: Kontekst

    Returns:
        Experience hvis LearningLoop er aktiv, ellers None
    """
    loop = get_learning_loop()
    if loop:
        return await loop.record_user_feedback(
            source, user_id, feedback_type, content, sentiment, context
        )
    return None


# ============================================================================
# INTEGRATION MED MASTERMIND
# ============================================================================

async def create_mastermind_learning_loop(
    auto_start: bool = True,
    **kwargs,
) -> LearningLoop:
    """
    Opret og konfigurér LearningLoop til MASTERMIND.

    Args:
        auto_start: Start automatisk
        **kwargs: Yderligere konfiguration

    Returns:
        Konfigureret LearningLoop
    """
    loop = create_learning_loop(**kwargs)

    # Registrér callbacks for logging
    def log_insight(insight: LearningInsight):
        logger.info(f"Ny indsigt [{insight.priority.value}]: {insight.title}")

    def log_improvement(improvement: Improvement):
        logger.info(f"Ny forbedring foreslået: {improvement.title}")

    loop.on_insight(log_insight)
    loop.on_improvement(log_improvement)

    if auto_start:
        await loop.start()

    return loop
