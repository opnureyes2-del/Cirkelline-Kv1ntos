"""
CIRKELLINE MASTERMIND - DEL Z: InsightSynthesizer
==================================================

Avanceret indsigt-syntetisering for MASTERMIND systemet.
Samler, korrelerer og destillerer indsigter fra multiple kilder
til handlingsbar viden og strategiske anbefalinger.

Forfatter: Cirkelline Team
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class InsightSourceType(Enum):
    """Typer af indsigt-kilder."""

    LEARNING_LOOP = "learning_loop"         # Fra LearningLoop
    COLLECTIVE_AWARENESS = "collective"     # Fra CollectiveAwareness
    PERFORMANCE_MONITOR = "performance"     # Fra PerformanceMonitor
    USER_FEEDBACK = "user_feedback"         # Fra brugerfeedback
    SYSTEM_EVENTS = "system_events"         # Fra systemhændelser
    EXTERNAL_DATA = "external"              # Fra eksterne kilder
    ANOMALY_DETECTION = "anomaly"           # Fra anomali-detektion
    PATTERN_RECOGNITION = "pattern"         # Fra mønstergenkendelse


class SynthesisMethod(Enum):
    """Metoder til indsigt-syntetisering."""

    AGGREGATION = "aggregation"             # Simpel sammenlægning
    CORRELATION = "correlation"             # Korrelationsanalyse
    CLUSTERING = "clustering"               # Gruppering af relaterede
    DISTILLATION = "distillation"           # Destillering til essens
    ABSTRACTION = "abstraction"             # Abstraktion til højere niveau
    CAUSAL_ANALYSIS = "causal"              # Årsag-virkning analyse
    TEMPORAL_SYNTHESIS = "temporal"         # Tidsbaseret syntese
    CROSS_DOMAIN = "cross_domain"           # På tværs af domæner


class InsightConfidence(Enum):
    """Tillidsniveau for syntetiserede indsigter."""

    SPECULATIVE = "speculative"       # < 30% confidence
    POSSIBLE = "possible"             # 30-50% confidence
    LIKELY = "likely"                 # 50-70% confidence
    CONFIDENT = "confident"           # 70-90% confidence
    CERTAIN = "certain"               # > 90% confidence


class ActionUrgency(Enum):
    """Hastighed for handling baseret på indsigt."""

    IMMEDIATE = "immediate"           # Kræver øjeblikkelig handling
    URGENT = "urgent"                 # Inden for timer
    SOON = "soon"                     # Inden for dage
    PLANNED = "planned"               # Kan planlægges
    INFORMATIONAL = "informational"   # Kun til information


class RecommendationCategory(Enum):
    """Kategorier af anbefalinger."""

    OPTIMIZATION = "optimization"     # Performance forbedring
    CORRECTION = "correction"         # Fejlrettelse
    PREVENTION = "prevention"         # Forebyggelse
    ENHANCEMENT = "enhancement"       # Funktionsforbedring
    STRATEGIC = "strategic"           # Strategisk ændring
    RESOURCE = "resource"             # Ressourceallokering
    PROCESS = "process"               # Procesændring
    TRAINING = "training"             # Træningsbehov


class ImpactLevel(Enum):
    """Impact niveau for indsigter."""

    TRIVIAL = "trivial"               # Minimal impact
    MINOR = "minor"                   # Lille impact
    MODERATE = "moderate"             # Moderat impact
    SIGNIFICANT = "significant"       # Betydelig impact
    CRITICAL = "critical"             # Kritisk impact


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SourceInsight:
    """En indsigt fra en kilde før syntetisering."""

    insight_id: str
    source_type: InsightSourceType
    source_id: str
    timestamp: datetime
    content: str
    data: Dict[str, Any]
    relevance_score: float = 0.5        # 0.0-1.0
    tags: List[str] = field(default_factory=list)
    related_insights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "data": self.data,
            "relevance_score": self.relevance_score,
            "tags": self.tags,
            "related_insights": self.related_insights,
        }


@dataclass
class SynthesisContext:
    """Kontekst for en syntetiserings-operation."""

    context_id: str
    focus_areas: List[str]
    time_window: timedelta
    min_sources: int = 2
    min_confidence: float = 0.5
    synthesis_methods: List[SynthesisMethod] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.synthesis_methods:
            self.synthesis_methods = [
                SynthesisMethod.AGGREGATION,
                SynthesisMethod.CORRELATION,
            ]


@dataclass
class SynthesizedInsight:
    """En syntetiseret indsigt fra multiple kilder."""

    synthesis_id: str
    timestamp: datetime
    title: str
    summary: str
    detailed_analysis: str

    # Kilder og data
    source_insights: List[str]              # IDs af kilde-indsigter
    source_types: Set[InsightSourceType]    # Hvilke typer kilder
    synthesis_methods: List[SynthesisMethod]

    # Vurdering
    confidence: InsightConfidence
    confidence_score: float                 # 0.0-1.0
    impact_level: ImpactLevel
    urgency: ActionUrgency

    # Kategorisering
    domains: List[str]                      # Relevante domæner
    tags: List[str]

    # Handlinger
    recommended_actions: List[str]
    potential_risks: List[str]
    expected_benefits: List[str]

    # Metadata
    synthesis_duration_ms: float = 0.0
    validation_status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "synthesis_id": self.synthesis_id,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "summary": self.summary,
            "detailed_analysis": self.detailed_analysis,
            "source_insights": self.source_insights,
            "source_types": [st.value for st in self.source_types],
            "synthesis_methods": [sm.value for sm in self.synthesis_methods],
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "impact_level": self.impact_level.value,
            "urgency": self.urgency.value,
            "domains": self.domains,
            "tags": self.tags,
            "recommended_actions": self.recommended_actions,
            "potential_risks": self.potential_risks,
            "expected_benefits": self.expected_benefits,
            "synthesis_duration_ms": self.synthesis_duration_ms,
            "validation_status": self.validation_status,
        }


@dataclass
class ActionRecommendation:
    """En konkret handlingsanbefaling baseret på syntetiserede indsigter."""

    recommendation_id: str
    timestamp: datetime
    title: str
    description: str

    # Kategorisering
    category: RecommendationCategory
    urgency: ActionUrgency
    impact_level: ImpactLevel

    # Grundlag
    source_syntheses: List[str]             # IDs af syntetiserede indsigter
    supporting_evidence: List[str]
    confidence_score: float

    # Implementering
    implementation_steps: List[str]
    estimated_effort: str                   # "low", "medium", "high"
    required_resources: List[str]
    dependencies: List[str]

    # Forventet resultat
    expected_outcome: str
    success_metrics: List[str]
    risk_mitigation: List[str]

    # Status
    status: str = "proposed"                # proposed, approved, implementing, completed, rejected
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "urgency": self.urgency.value,
            "impact_level": self.impact_level.value,
            "source_syntheses": self.source_syntheses,
            "supporting_evidence": self.supporting_evidence,
            "confidence_score": self.confidence_score,
            "implementation_steps": self.implementation_steps,
            "estimated_effort": self.estimated_effort,
            "required_resources": self.required_resources,
            "dependencies": self.dependencies,
            "expected_outcome": self.expected_outcome,
            "success_metrics": self.success_metrics,
            "risk_mitigation": self.risk_mitigation,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }


@dataclass
class InsightCorrelation:
    """Korrelation mellem to eller flere indsigter."""

    correlation_id: str
    insight_ids: List[str]
    correlation_type: str                   # "causal", "temporal", "thematic", "semantic"
    strength: float                         # 0.0-1.0
    direction: Optional[str] = None         # "positive", "negative", "bidirectional"
    lag_time: Optional[timedelta] = None    # Tidsforsinkelse mellem indsigter
    confidence: float = 0.5
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "insight_ids": self.insight_ids,
            "correlation_type": self.correlation_type,
            "strength": self.strength,
            "direction": self.direction,
            "lag_time": str(self.lag_time) if self.lag_time else None,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }


@dataclass
class KnowledgeNugget:
    """Et destilleret stykke viden fra multiple synteser."""

    nugget_id: str
    created_at: datetime
    updated_at: datetime

    title: str
    essence: str                            # Kort essens (< 100 chars)
    detailed_knowledge: str

    # Grundlag
    synthesis_count: int
    source_syntheses: List[str]
    validation_count: int

    # Vurdering
    certainty_level: InsightConfidence
    applicability: List[str]                # Hvor gælder denne viden
    limitations: List[str]                  # Kendte begrænsninger

    # Evolution
    version: int = 1
    previous_versions: List[str] = field(default_factory=list)
    is_superseded: bool = False
    superseded_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nugget_id": self.nugget_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "title": self.title,
            "essence": self.essence,
            "detailed_knowledge": self.detailed_knowledge,
            "synthesis_count": self.synthesis_count,
            "source_syntheses": self.source_syntheses,
            "validation_count": self.validation_count,
            "certainty_level": self.certainty_level.value,
            "applicability": self.applicability,
            "limitations": self.limitations,
            "version": self.version,
            "previous_versions": self.previous_versions,
            "is_superseded": self.is_superseded,
            "superseded_by": self.superseded_by,
        }


@dataclass
class SynthesizerStats:
    """Statistikker for InsightSynthesizer."""

    total_insights_received: int = 0
    total_syntheses_created: int = 0
    total_recommendations: int = 0
    total_knowledge_nuggets: int = 0

    insights_by_source: Dict[str, int] = field(default_factory=dict)
    syntheses_by_method: Dict[str, int] = field(default_factory=dict)
    recommendations_by_category: Dict[str, int] = field(default_factory=dict)

    average_synthesis_time_ms: float = 0.0
    average_confidence: float = 0.0
    average_source_count: float = 0.0

    correlations_found: int = 0
    high_impact_insights: int = 0

    last_synthesis_at: Optional[datetime] = None
    uptime_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_insights_received": self.total_insights_received,
            "total_syntheses_created": self.total_syntheses_created,
            "total_recommendations": self.total_recommendations,
            "total_knowledge_nuggets": self.total_knowledge_nuggets,
            "insights_by_source": self.insights_by_source,
            "syntheses_by_method": self.syntheses_by_method,
            "recommendations_by_category": self.recommendations_by_category,
            "average_synthesis_time_ms": self.average_synthesis_time_ms,
            "average_confidence": self.average_confidence,
            "average_source_count": self.average_source_count,
            "correlations_found": self.correlations_found,
            "high_impact_insights": self.high_impact_insights,
            "last_synthesis_at": self.last_synthesis_at.isoformat() if self.last_synthesis_at else None,
            "uptime_seconds": self.uptime_seconds,
        }


# ============================================================================
# SYNTHESIS STRATEGIES
# ============================================================================

class SynthesisStrategy:
    """Base class for synthesis strategies."""

    def __init__(self, method: SynthesisMethod):
        self.method = method

    async def synthesize(
        self,
        insights: List[SourceInsight],
        context: SynthesisContext,
    ) -> Optional[Dict[str, Any]]:
        """Syntetiser indsigter med denne strategi."""
        raise NotImplementedError


class AggregationStrategy(SynthesisStrategy):
    """Aggregerer relaterede indsigter til samlet indsigt."""

    def __init__(self):
        super().__init__(SynthesisMethod.AGGREGATION)

    async def synthesize(
        self,
        insights: List[SourceInsight],
        context: SynthesisContext,
    ) -> Optional[Dict[str, Any]]:
        if len(insights) < context.min_sources:
            return None

        # Find fælles tags
        all_tags = [set(i.tags) for i in insights]
        common_tags = set.intersection(*all_tags) if all_tags else set()

        # Beregn gennemsnitlig relevans
        avg_relevance = statistics.mean(i.relevance_score for i in insights)

        # Kombiner indhold
        combined_content = "\n".join(f"- {i.content}" for i in insights)

        # Find fælles data punkter
        common_data = {}
        for insight in insights:
            for key, value in insight.data.items():
                if key not in common_data:
                    common_data[key] = []
                common_data[key].append(value)

        # Aggreger numeriske værdier
        aggregated_data = {}
        for key, values in common_data.items():
            if all(isinstance(v, (int, float)) for v in values):
                aggregated_data[key] = {
                    "mean": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }
            else:
                # For ikke-numeriske, find mest almindelige
                aggregated_data[key] = max(set(values), key=values.count)

        return {
            "method": self.method.value,
            "common_tags": list(common_tags),
            "average_relevance": avg_relevance,
            "combined_content": combined_content,
            "aggregated_data": aggregated_data,
            "source_count": len(insights),
        }


class CorrelationStrategy(SynthesisStrategy):
    """Finder korrelationer mellem indsigter."""

    def __init__(self):
        super().__init__(SynthesisMethod.CORRELATION)

    async def synthesize(
        self,
        insights: List[SourceInsight],
        context: SynthesisContext,
    ) -> Optional[Dict[str, Any]]:
        if len(insights) < 2:
            return None

        correlations = []

        # Find tidsmæssige korrelationer
        sorted_by_time = sorted(insights, key=lambda x: x.timestamp)
        for i, insight1 in enumerate(sorted_by_time[:-1]):
            for insight2 in sorted_by_time[i+1:]:
                time_diff = (insight2.timestamp - insight1.timestamp).total_seconds()

                # Find tag overlap
                tag_overlap = len(set(insight1.tags) & set(insight2.tags))
                total_tags = len(set(insight1.tags) | set(insight2.tags))
                tag_similarity = tag_overlap / total_tags if total_tags > 0 else 0

                # Find data key overlap
                data_overlap = len(set(insight1.data.keys()) & set(insight2.data.keys()))
                total_keys = len(set(insight1.data.keys()) | set(insight2.data.keys()))
                data_similarity = data_overlap / total_keys if total_keys > 0 else 0

                # Beregn korrelationsstyrke
                strength = (tag_similarity * 0.4 + data_similarity * 0.4 +
                           (1.0 / (1 + time_diff / 3600)) * 0.2)  # Tidsnærhed

                if strength > 0.3:
                    correlations.append({
                        "insight_ids": [insight1.insight_id, insight2.insight_id],
                        "strength": strength,
                        "time_diff_seconds": time_diff,
                        "tag_similarity": tag_similarity,
                        "data_similarity": data_similarity,
                        "correlation_type": self._determine_type(
                            tag_similarity, data_similarity, time_diff
                        ),
                    })

        if not correlations:
            return None

        return {
            "method": self.method.value,
            "correlations": sorted(correlations, key=lambda x: x["strength"], reverse=True),
            "total_pairs_analyzed": len(insights) * (len(insights) - 1) // 2,
            "significant_correlations": len(correlations),
        }

    def _determine_type(
        self,
        tag_sim: float,
        data_sim: float,
        time_diff: float,
    ) -> str:
        if time_diff < 60:  # Under 1 minut
            return "temporal"
        elif tag_sim > 0.7:
            return "thematic"
        elif data_sim > 0.7:
            return "structural"
        else:
            return "weak"


class DistillationStrategy(SynthesisStrategy):
    """Destillerer indsigter til kerneesens."""

    def __init__(self):
        super().__init__(SynthesisMethod.DISTILLATION)

    async def synthesize(
        self,
        insights: List[SourceInsight],
        context: SynthesisContext,
    ) -> Optional[Dict[str, Any]]:
        if len(insights) < context.min_sources:
            return None

        # Find hyppigste tags
        tag_counts = defaultdict(int)
        for insight in insights:
            for tag in insight.tags:
                tag_counts[tag] += 1

        # Top tags
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Find hyppigste data keys og værdier
        data_frequency = defaultdict(lambda: defaultdict(int))
        for insight in insights:
            for key, value in insight.data.items():
                data_frequency[key][str(value)] += 1

        # Destilleret data
        distilled_data = {}
        for key, value_counts in data_frequency.items():
            most_common = max(value_counts.items(), key=lambda x: x[1])
            frequency_ratio = most_common[1] / len(insights)
            if frequency_ratio > 0.5:  # Mere end halvdelen har samme værdi
                distilled_data[key] = {
                    "value": most_common[0],
                    "frequency_ratio": frequency_ratio,
                }

        # Beregn samlet essens
        essence_parts = []
        for tag, count in top_tags[:3]:
            if count > len(insights) * 0.5:
                essence_parts.append(tag)

        return {
            "method": self.method.value,
            "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
            "distilled_data": distilled_data,
            "essence_tags": essence_parts,
            "distillation_ratio": len(distilled_data) / len(data_frequency) if data_frequency else 0,
            "coverage": len(insights),
        }


class CausalAnalysisStrategy(SynthesisStrategy):
    """Analyserer årsag-virkning relationer."""

    def __init__(self):
        super().__init__(SynthesisMethod.CAUSAL_ANALYSIS)

    async def synthesize(
        self,
        insights: List[SourceInsight],
        context: SynthesisContext,
    ) -> Optional[Dict[str, Any]]:
        if len(insights) < 2:
            return None

        causal_chains = []

        # Sortér efter tid
        sorted_insights = sorted(insights, key=lambda x: x.timestamp)

        # Find mulige kausale relationer
        for i, potential_cause in enumerate(sorted_insights[:-1]):
            for potential_effect in sorted_insights[i+1:]:
                # Tjek for kausal indikator i tags
                cause_indicators = {"error", "failure", "warning", "change", "update"}
                effect_indicators = {"result", "outcome", "response", "fixed", "resolved"}

                is_cause = bool(set(potential_cause.tags) & cause_indicators)
                is_effect = bool(set(potential_effect.tags) & effect_indicators)

                # Tjek tidsvindue (effekter bør komme kort efter årsager)
                time_diff = (potential_effect.timestamp - potential_cause.timestamp).total_seconds()

                if is_cause and is_effect and time_diff < 3600:  # Inden for 1 time
                    confidence = 0.5

                    # Højere confidence hvis samme tags
                    tag_overlap = len(set(potential_cause.tags) & set(potential_effect.tags))
                    confidence += tag_overlap * 0.1

                    # Højere confidence hvis kort tidsinterval
                    if time_diff < 60:
                        confidence += 0.2
                    elif time_diff < 300:
                        confidence += 0.1

                    causal_chains.append({
                        "cause_id": potential_cause.insight_id,
                        "effect_id": potential_effect.insight_id,
                        "time_lag_seconds": time_diff,
                        "confidence": min(confidence, 1.0),
                        "cause_tags": potential_cause.tags,
                        "effect_tags": potential_effect.tags,
                    })

        if not causal_chains:
            return None

        return {
            "method": self.method.value,
            "causal_chains": sorted(causal_chains, key=lambda x: x["confidence"], reverse=True),
            "total_chains_found": len(causal_chains),
            "average_confidence": statistics.mean(c["confidence"] for c in causal_chains),
        }


# ============================================================================
# INSIGHT SYNTHESIZER
# ============================================================================

class InsightSynthesizer:
    """
    Avanceret indsigt-syntetiserings-motor.

    Samler indsigter fra multiple kilder, finder korrelationer,
    og syntetiserer til handlingsbar viden.
    """

    def __init__(
        self,
        synthesizer_id: Optional[str] = None,
        max_insights_buffer: int = 1000,
        synthesis_threshold: int = 3,
        auto_synthesize_interval: float = 60.0,
        enable_auto_synthesis: bool = True,
    ):
        self.synthesizer_id = synthesizer_id or f"synth_{uuid4().hex[:12]}"
        self.max_insights_buffer = max_insights_buffer
        self.synthesis_threshold = synthesis_threshold
        self.auto_synthesize_interval = auto_synthesize_interval
        self.enable_auto_synthesis = enable_auto_synthesis

        # Buffers
        self._insights_buffer: List[SourceInsight] = []
        self._synthesized: Dict[str, SynthesizedInsight] = {}
        self._recommendations: Dict[str, ActionRecommendation] = {}
        self._knowledge_nuggets: Dict[str, KnowledgeNugget] = {}
        self._correlations: Dict[str, InsightCorrelation] = {}

        # Strategies
        self._strategies: Dict[SynthesisMethod, SynthesisStrategy] = {
            SynthesisMethod.AGGREGATION: AggregationStrategy(),
            SynthesisMethod.CORRELATION: CorrelationStrategy(),
            SynthesisMethod.DISTILLATION: DistillationStrategy(),
            SynthesisMethod.CAUSAL_ANALYSIS: CausalAnalysisStrategy(),
        }

        # Callbacks
        self._synthesis_listeners: List[Callable[[SynthesizedInsight], None]] = []
        self._recommendation_listeners: List[Callable[[ActionRecommendation], None]] = []
        self._knowledge_listeners: List[Callable[[KnowledgeNugget], None]] = []

        # Stats
        self._stats = SynthesizerStats()
        self._started_at: Optional[datetime] = None
        self._auto_task: Optional[asyncio.Task] = None

        # State
        self._is_running = False
        self._lock = asyncio.Lock()

        logger.info(f"InsightSynthesizer oprettet: {self.synthesizer_id}")

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    async def start(self) -> None:
        """Start synthesizer inkl. auto-syntese."""
        if self._is_running:
            logger.warning("InsightSynthesizer kører allerede")
            return

        self._is_running = True
        self._started_at = datetime.now()

        if self.enable_auto_synthesis:
            self._auto_task = asyncio.create_task(self._auto_synthesis_loop())

        logger.info(f"InsightSynthesizer startet: {self.synthesizer_id}")

    async def stop(self) -> None:
        """Stop synthesizer."""
        self._is_running = False

        if self._auto_task:
            self._auto_task.cancel()
            try:
                await self._auto_task
            except asyncio.CancelledError:
                pass
            self._auto_task = None

        logger.info(f"InsightSynthesizer stoppet: {self.synthesizer_id}")

    async def _auto_synthesis_loop(self) -> None:
        """Baggrunds-loop for automatisk syntese."""
        while self._is_running:
            try:
                await asyncio.sleep(self.auto_synthesize_interval)

                if len(self._insights_buffer) >= self.synthesis_threshold:
                    context = SynthesisContext(
                        context_id=f"auto_{uuid4().hex[:8]}",
                        focus_areas=[],
                        time_window=timedelta(hours=1),
                        min_sources=self.synthesis_threshold,
                    )
                    await self.synthesize(context)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Fejl i auto-syntese loop: {e}")

    # ========================================================================
    # INSIGHT INGESTION
    # ========================================================================

    async def ingest_insight(
        self,
        source_type: InsightSourceType,
        source_id: str,
        content: str,
        data: Dict[str, Any],
        relevance_score: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> SourceInsight:
        """
        Modtag en ny indsigt til syntetisering.

        Args:
            source_type: Type af kilde
            source_id: ID på kilden
            content: Tekstuelt indhold
            data: Struktureret data
            relevance_score: Relevansscore (0.0-1.0)
            tags: Tags til kategorisering

        Returns:
            Den oprettede SourceInsight
        """
        insight = SourceInsight(
            insight_id=f"ins_{uuid4().hex[:12]}",
            source_type=source_type,
            source_id=source_id,
            timestamp=datetime.now(),
            content=content,
            data=data,
            relevance_score=max(0.0, min(1.0, relevance_score)),
            tags=tags or [],
        )

        async with self._lock:
            self._insights_buffer.append(insight)

            # Trim buffer hvis nødvendigt
            if len(self._insights_buffer) > self.max_insights_buffer:
                self._insights_buffer = self._insights_buffer[-self.max_insights_buffer:]

            # Opdater stats
            self._stats.total_insights_received += 1
            source_key = source_type.value
            self._stats.insights_by_source[source_key] = \
                self._stats.insights_by_source.get(source_key, 0) + 1

        logger.debug(f"Indsigt modtaget: {insight.insight_id} fra {source_type.value}")

        return insight

    async def ingest_from_learning_loop(
        self,
        learning_insight: Any,  # LearningInsight fra learning_loop.py
    ) -> SourceInsight:
        """Konverter og modtag indsigt fra LearningLoop."""
        return await self.ingest_insight(
            source_type=InsightSourceType.LEARNING_LOOP,
            source_id=getattr(learning_insight, "insight_id", str(uuid4())),
            content=getattr(learning_insight, "content", ""),
            data=getattr(learning_insight, "data", {}),
            relevance_score=getattr(learning_insight, "relevance", 0.5),
            tags=getattr(learning_insight, "tags", []),
        )

    async def ingest_from_collective_awareness(
        self,
        collective_insight: Any,  # CollectiveInsight fra collective_awareness.py
    ) -> SourceInsight:
        """Konverter og modtag indsigt fra CollectiveAwareness."""
        return await self.ingest_insight(
            source_type=InsightSourceType.COLLECTIVE_AWARENESS,
            source_id=getattr(collective_insight, "insight_id", str(uuid4())),
            content=getattr(collective_insight, "content", ""),
            data=getattr(collective_insight, "data", {}),
            relevance_score=getattr(collective_insight, "relevance", 0.5),
            tags=getattr(collective_insight, "tags", []),
        )

    # ========================================================================
    # SYNTHESIS
    # ========================================================================

    async def synthesize(
        self,
        context: SynthesisContext,
        insights: Optional[List[SourceInsight]] = None,
    ) -> List[SynthesizedInsight]:
        """
        Syntetiser indsigter til højere-niveau forståelse.

        Args:
            context: Syntetiseringskontekst med parametre
            insights: Specifikke indsigter (eller brug buffer)

        Returns:
            Liste af syntetiserede indsigter
        """
        start_time = datetime.now()

        # Brug bufferen hvis ingen specifikke indsigter
        if insights is None:
            async with self._lock:
                # Filtrér efter tidsvindue
                cutoff = datetime.now() - context.time_window
                insights = [i for i in self._insights_buffer if i.timestamp > cutoff]

        if len(insights) < context.min_sources:
            logger.debug(f"For få indsigter til syntese: {len(insights)}")
            return []

        # Filtrér efter fokusområder hvis angivet
        if context.focus_areas:
            filtered = []
            for insight in insights:
                if any(tag in context.focus_areas for tag in insight.tags):
                    filtered.append(insight)
            if len(filtered) >= context.min_sources:
                insights = filtered

        # Kør hver syntese-strategi
        synthesis_results: Dict[SynthesisMethod, Any] = {}

        for method in context.synthesis_methods:
            strategy = self._strategies.get(method)
            if strategy:
                try:
                    result = await strategy.synthesize(insights, context)
                    if result:
                        synthesis_results[method] = result
                except Exception as e:
                    logger.error(f"Fejl i syntese-strategi {method}: {e}")

        if not synthesis_results:
            return []

        # Opret syntetiseret indsigt
        synthesized = await self._create_synthesized_insight(
            insights, synthesis_results, context
        )

        # Beregn varighed
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        synthesized.synthesis_duration_ms = duration_ms

        # Gem og notificér
        async with self._lock:
            self._synthesized[synthesized.synthesis_id] = synthesized
            self._stats.total_syntheses_created += 1
            self._stats.last_synthesis_at = datetime.now()

            # Opdater method stats
            for method in synthesis_results.keys():
                key = method.value
                self._stats.syntheses_by_method[key] = \
                    self._stats.syntheses_by_method.get(key, 0) + 1

        # Notificér listeners
        for listener in self._synthesis_listeners:
            try:
                listener(synthesized)
            except Exception as e:
                logger.error(f"Fejl i synthesis listener: {e}")

        logger.info(
            f"Syntetiseret indsigt oprettet: {synthesized.synthesis_id} "
            f"({len(insights)} kilder, {duration_ms:.1f}ms)"
        )

        # Generer anbefalinger hvis høj impact
        if synthesized.impact_level in [ImpactLevel.SIGNIFICANT, ImpactLevel.CRITICAL]:
            await self._generate_recommendation(synthesized)

        return [synthesized]

    async def _create_synthesized_insight(
        self,
        insights: List[SourceInsight],
        synthesis_results: Dict[SynthesisMethod, Any],
        context: SynthesisContext,
    ) -> SynthesizedInsight:
        """Opret en syntetiseret indsigt fra strategiresultater."""

        # Saml alle source types
        source_types = {i.source_type for i in insights}

        # Beregn confidence baseret på kilder og resultater
        confidence_score = self._calculate_confidence(insights, synthesis_results)
        confidence = self._score_to_confidence(confidence_score)

        # Vurder impact
        impact = self._assess_impact(insights, synthesis_results)

        # Vurder urgency
        urgency = self._assess_urgency(insights, synthesis_results)

        # Generer titel og opsummering
        title, summary = self._generate_title_summary(synthesis_results)

        # Saml alle tags
        all_tags = set()
        for insight in insights:
            all_tags.update(insight.tags)

        # Generér detaljeret analyse
        detailed = self._generate_detailed_analysis(synthesis_results)

        # Find anbefalede handlinger
        actions = self._suggest_actions(synthesis_results, impact, urgency)

        # Find potentielle risici
        risks = self._identify_risks(synthesis_results)

        # Find forventede fordele
        benefits = self._identify_benefits(synthesis_results, impact)

        return SynthesizedInsight(
            synthesis_id=f"synth_{uuid4().hex[:12]}",
            timestamp=datetime.now(),
            title=title,
            summary=summary,
            detailed_analysis=detailed,
            source_insights=[i.insight_id for i in insights],
            source_types=source_types,
            synthesis_methods=list(synthesis_results.keys()),
            confidence=confidence,
            confidence_score=confidence_score,
            impact_level=impact,
            urgency=urgency,
            domains=list(context.focus_areas) if context.focus_areas else [],
            tags=list(all_tags),
            recommended_actions=actions,
            potential_risks=risks,
            expected_benefits=benefits,
        )

    def _calculate_confidence(
        self,
        insights: List[SourceInsight],
        results: Dict[SynthesisMethod, Any],
    ) -> float:
        """Beregn confidence score for syntesen."""
        factors = []

        # Faktor 1: Antal kilder
        source_factor = min(len(insights) / 10, 1.0)
        factors.append(source_factor * 0.3)

        # Faktor 2: Kilde-diversitet
        source_types = {i.source_type for i in insights}
        diversity_factor = len(source_types) / len(InsightSourceType)
        factors.append(diversity_factor * 0.2)

        # Faktor 3: Gennemsnitlig relevans
        avg_relevance = statistics.mean(i.relevance_score for i in insights)
        factors.append(avg_relevance * 0.3)

        # Faktor 4: Syntese-metode resultater
        method_factor = len(results) / len(self._strategies)
        factors.append(method_factor * 0.2)

        return sum(factors)

    def _score_to_confidence(self, score: float) -> InsightConfidence:
        """Konverter numerisk score til confidence niveau."""
        if score < 0.3:
            return InsightConfidence.SPECULATIVE
        elif score < 0.5:
            return InsightConfidence.POSSIBLE
        elif score < 0.7:
            return InsightConfidence.LIKELY
        elif score < 0.9:
            return InsightConfidence.CONFIDENT
        else:
            return InsightConfidence.CERTAIN

    def _assess_impact(
        self,
        insights: List[SourceInsight],
        results: Dict[SynthesisMethod, Any],
    ) -> ImpactLevel:
        """Vurder impact niveau."""
        # Tjek for kritiske indikatorer
        critical_tags = {"critical", "error", "failure", "security", "data_loss"}
        significant_tags = {"performance", "cost", "user_experience", "reliability"}

        all_tags = set()
        for insight in insights:
            all_tags.update(insight.tags)

        if all_tags & critical_tags:
            return ImpactLevel.CRITICAL
        elif all_tags & significant_tags:
            return ImpactLevel.SIGNIFICANT
        elif len(insights) > 5:
            return ImpactLevel.MODERATE
        else:
            return ImpactLevel.MINOR

    def _assess_urgency(
        self,
        insights: List[SourceInsight],
        results: Dict[SynthesisMethod, Any],
    ) -> ActionUrgency:
        """Vurder handlings-hastighed."""
        urgent_tags = {"immediate", "urgent", "critical", "error", "failure"}
        soon_tags = {"warning", "degraded", "attention", "important"}

        all_tags = set()
        for insight in insights:
            all_tags.update(insight.tags)

        if all_tags & urgent_tags:
            return ActionUrgency.IMMEDIATE
        elif all_tags & soon_tags:
            return ActionUrgency.SOON
        else:
            return ActionUrgency.PLANNED

    def _generate_title_summary(
        self,
        results: Dict[SynthesisMethod, Any],
    ) -> Tuple[str, str]:
        """Generer titel og opsummering fra resultater."""
        # Simpel implementation - kan forbedres med LLM
        titles = []
        summaries = []

        if SynthesisMethod.AGGREGATION in results:
            agg = results[SynthesisMethod.AGGREGATION]
            if agg.get("essence_tags"):
                titles.append(f"Aggregeret indsigt: {', '.join(agg['essence_tags'][:3])}")
            summaries.append(f"Aggregeret fra {agg.get('source_count', 0)} kilder")

        if SynthesisMethod.CORRELATION in results:
            corr = results[SynthesisMethod.CORRELATION]
            sig_count = corr.get("significant_correlations", 0)
            if sig_count > 0:
                titles.append(f"Korrelationsanalyse ({sig_count} fundne)")
                summaries.append(f"Fundet {sig_count} signifikante korrelationer")

        if SynthesisMethod.CAUSAL_ANALYSIS in results:
            causal = results[SynthesisMethod.CAUSAL_ANALYSIS]
            chain_count = causal.get("total_chains_found", 0)
            if chain_count > 0:
                titles.append(f"Kausal analyse ({chain_count} kæder)")
                summaries.append(f"Identificeret {chain_count} årsag-virkning relationer")

        title = titles[0] if titles else "Syntetiseret indsigt"
        summary = " | ".join(summaries) if summaries else "Syntetisering gennemført"

        return title, summary

    def _generate_detailed_analysis(
        self,
        results: Dict[SynthesisMethod, Any],
    ) -> str:
        """Generer detaljeret analyse tekst."""
        parts = []

        for method, data in results.items():
            parts.append(f"## {method.value.upper()}\n")
            parts.append(json.dumps(data, indent=2, default=str))
            parts.append("\n")

        return "\n".join(parts)

    def _suggest_actions(
        self,
        results: Dict[SynthesisMethod, Any],
        impact: ImpactLevel,
        urgency: ActionUrgency,
    ) -> List[str]:
        """Foreslå handlinger baseret på resultater."""
        actions = []

        if urgency == ActionUrgency.IMMEDIATE:
            actions.append("Undersøg årsagen til den akutte situation")
            actions.append("Overvej midlertidig mitigering")

        if impact in [ImpactLevel.CRITICAL, ImpactLevel.SIGNIFICANT]:
            actions.append("Prioritér ressourcer til løsning")
            actions.append("Informér relevante stakeholders")

        if SynthesisMethod.CAUSAL_ANALYSIS in results:
            actions.append("Addressér rodårsagen identificeret i kausal analyse")

        if SynthesisMethod.CORRELATION in results:
            actions.append("Undersøg korrelerede faktorer for mulige forbedringer")

        return actions if actions else ["Gennemgå syntetiseret indsigt manuelt"]

    def _identify_risks(
        self,
        results: Dict[SynthesisMethod, Any],
    ) -> List[str]:
        """Identificer potentielle risici."""
        risks = []

        if SynthesisMethod.CAUSAL_ANALYSIS in results:
            causal = results[SynthesisMethod.CAUSAL_ANALYSIS]
            if causal.get("average_confidence", 0) < 0.5:
                risks.append("Lav confidence i kausal analyse - yderligere undersøgelse anbefales")

        if SynthesisMethod.CORRELATION in results:
            corr = results[SynthesisMethod.CORRELATION]
            total_analyzed = corr.get("total_pairs_analyzed", 0)
            significant = corr.get("significant_correlations", 0)
            if total_analyzed > 0 and significant / total_analyzed < 0.1:
                risks.append("Få signifikante korrelationer - data kan være for spredt")

        return risks

    def _identify_benefits(
        self,
        results: Dict[SynthesisMethod, Any],
        impact: ImpactLevel,
    ) -> List[str]:
        """Identificer forventede fordele."""
        benefits = []

        if impact in [ImpactLevel.CRITICAL, ImpactLevel.SIGNIFICANT]:
            benefits.append("Betydelig forbedring af systemperformance")

        if SynthesisMethod.AGGREGATION in results:
            benefits.append("Samlet overblik over multiple datapunkter")

        if SynthesisMethod.CAUSAL_ANALYSIS in results:
            benefits.append("Forståelse af årsag-virkning relationer")

        return benefits if benefits else ["Forbedret systemforståelse"]

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================

    async def _generate_recommendation(
        self,
        synthesis: SynthesizedInsight,
    ) -> ActionRecommendation:
        """Generer en handlingsanbefaling fra en syntetiseret indsigt."""

        # Bestem kategori
        category = self._determine_recommendation_category(synthesis)

        # Bestem effort
        effort = self._estimate_effort(synthesis)

        recommendation = ActionRecommendation(
            recommendation_id=f"rec_{uuid4().hex[:12]}",
            timestamp=datetime.now(),
            title=f"Anbefaling: {synthesis.title}",
            description=synthesis.summary,
            category=category,
            urgency=synthesis.urgency,
            impact_level=synthesis.impact_level,
            source_syntheses=[synthesis.synthesis_id],
            supporting_evidence=synthesis.recommended_actions,
            confidence_score=synthesis.confidence_score,
            implementation_steps=synthesis.recommended_actions,
            estimated_effort=effort,
            required_resources=[],
            dependencies=[],
            expected_outcome=synthesis.expected_benefits[0] if synthesis.expected_benefits else "Forbedret systemtilstand",
            success_metrics=["Reduktion i relaterede hændelser", "Forbedret performance metrics"],
            risk_mitigation=synthesis.potential_risks,
        )

        async with self._lock:
            self._recommendations[recommendation.recommendation_id] = recommendation
            self._stats.total_recommendations += 1

            cat_key = category.value
            self._stats.recommendations_by_category[cat_key] = \
                self._stats.recommendations_by_category.get(cat_key, 0) + 1

        # Notificér listeners
        for listener in self._recommendation_listeners:
            try:
                listener(recommendation)
            except Exception as e:
                logger.error(f"Fejl i recommendation listener: {e}")

        logger.info(f"Anbefaling genereret: {recommendation.recommendation_id}")

        return recommendation

    def _determine_recommendation_category(
        self,
        synthesis: SynthesizedInsight,
    ) -> RecommendationCategory:
        """Bestem anbefaling-kategori."""
        tag_mapping = {
            "performance": RecommendationCategory.OPTIMIZATION,
            "error": RecommendationCategory.CORRECTION,
            "security": RecommendationCategory.PREVENTION,
            "feature": RecommendationCategory.ENHANCEMENT,
            "resource": RecommendationCategory.RESOURCE,
            "process": RecommendationCategory.PROCESS,
        }

        for tag in synthesis.tags:
            if tag.lower() in tag_mapping:
                return tag_mapping[tag.lower()]

        return RecommendationCategory.ENHANCEMENT

    def _estimate_effort(self, synthesis: SynthesizedInsight) -> str:
        """Estimér implementeringsindsats."""
        if synthesis.impact_level == ImpactLevel.CRITICAL:
            return "high"
        elif synthesis.impact_level == ImpactLevel.SIGNIFICANT:
            return "medium"
        else:
            return "low"

    async def update_recommendation_status(
        self,
        recommendation_id: str,
        status: str,
        assigned_to: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> bool:
        """Opdater status for en anbefaling."""
        async with self._lock:
            if recommendation_id not in self._recommendations:
                return False

            rec = self._recommendations[recommendation_id]
            rec.status = status
            if assigned_to:
                rec.assigned_to = assigned_to
            if due_date:
                rec.due_date = due_date

        logger.info(f"Anbefaling {recommendation_id} opdateret til status: {status}")
        return True

    # ========================================================================
    # KNOWLEDGE NUGGETS
    # ========================================================================

    async def create_knowledge_nugget(
        self,
        title: str,
        essence: str,
        detailed_knowledge: str,
        source_syntheses: List[str],
        certainty: InsightConfidence,
        applicability: List[str],
        limitations: Optional[List[str]] = None,
    ) -> KnowledgeNugget:
        """
        Opret et knowledge nugget fra syntetiserede indsigter.

        Args:
            title: Titel på videnstykket
            essence: Kort essens (< 100 tegn)
            detailed_knowledge: Detaljeret forklaring
            source_syntheses: IDs af kilde-synteser
            certainty: Sikkerhedsniveau
            applicability: Hvor gælder denne viden
            limitations: Kendte begrænsninger

        Returns:
            Det oprettede KnowledgeNugget
        """
        now = datetime.now()

        nugget = KnowledgeNugget(
            nugget_id=f"know_{uuid4().hex[:12]}",
            created_at=now,
            updated_at=now,
            title=title,
            essence=essence[:100],  # Max 100 tegn
            detailed_knowledge=detailed_knowledge,
            synthesis_count=len(source_syntheses),
            source_syntheses=source_syntheses,
            validation_count=0,
            certainty_level=certainty,
            applicability=applicability,
            limitations=limitations or [],
        )

        async with self._lock:
            self._knowledge_nuggets[nugget.nugget_id] = nugget
            self._stats.total_knowledge_nuggets += 1

        # Notificér listeners
        for listener in self._knowledge_listeners:
            try:
                listener(nugget)
            except Exception as e:
                logger.error(f"Fejl i knowledge listener: {e}")

        logger.info(f"Knowledge nugget oprettet: {nugget.nugget_id}")

        return nugget

    async def validate_knowledge_nugget(
        self,
        nugget_id: str,
        is_valid: bool,
        notes: Optional[str] = None,
    ) -> bool:
        """Validér et knowledge nugget."""
        async with self._lock:
            if nugget_id not in self._knowledge_nuggets:
                return False

            nugget = self._knowledge_nuggets[nugget_id]
            nugget.validation_count += 1
            nugget.updated_at = datetime.now()

            if is_valid:
                # Forøg certainty
                current_idx = list(InsightConfidence).index(nugget.certainty_level)
                if current_idx < len(InsightConfidence) - 1:
                    nugget.certainty_level = list(InsightConfidence)[current_idx + 1]

        return True

    async def supersede_knowledge_nugget(
        self,
        old_nugget_id: str,
        new_nugget_id: str,
    ) -> bool:
        """Marker et knowledge nugget som erstattet af et nyere."""
        async with self._lock:
            if old_nugget_id not in self._knowledge_nuggets:
                return False
            if new_nugget_id not in self._knowledge_nuggets:
                return False

            old_nugget = self._knowledge_nuggets[old_nugget_id]
            old_nugget.is_superseded = True
            old_nugget.superseded_by = new_nugget_id
            old_nugget.updated_at = datetime.now()

            new_nugget = self._knowledge_nuggets[new_nugget_id]
            new_nugget.previous_versions.append(old_nugget_id)

        return True

    # ========================================================================
    # QUERIES
    # ========================================================================

    async def get_insights_buffer(
        self,
        source_type: Optional[InsightSourceType] = None,
        limit: int = 100,
    ) -> List[SourceInsight]:
        """Hent indsigter fra bufferen."""
        async with self._lock:
            insights = self._insights_buffer.copy()

        if source_type:
            insights = [i for i in insights if i.source_type == source_type]

        return sorted(insights, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def get_synthesized_insights(
        self,
        min_confidence: Optional[InsightConfidence] = None,
        min_impact: Optional[ImpactLevel] = None,
        limit: int = 50,
    ) -> List[SynthesizedInsight]:
        """Hent syntetiserede indsigter."""
        async with self._lock:
            insights = list(self._synthesized.values())

        if min_confidence:
            confidence_order = list(InsightConfidence)
            min_idx = confidence_order.index(min_confidence)
            insights = [
                i for i in insights
                if confidence_order.index(i.confidence) >= min_idx
            ]

        if min_impact:
            impact_order = list(ImpactLevel)
            min_idx = impact_order.index(min_impact)
            insights = [
                i for i in insights
                if impact_order.index(i.impact_level) >= min_idx
            ]

        return sorted(insights, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def get_recommendations(
        self,
        status: Optional[str] = None,
        category: Optional[RecommendationCategory] = None,
        limit: int = 50,
    ) -> List[ActionRecommendation]:
        """Hent anbefalinger."""
        async with self._lock:
            recs = list(self._recommendations.values())

        if status:
            recs = [r for r in recs if r.status == status]

        if category:
            recs = [r for r in recs if r.category == category]

        return sorted(recs, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def get_knowledge_nuggets(
        self,
        include_superseded: bool = False,
        min_certainty: Optional[InsightConfidence] = None,
        limit: int = 50,
    ) -> List[KnowledgeNugget]:
        """Hent knowledge nuggets."""
        async with self._lock:
            nuggets = list(self._knowledge_nuggets.values())

        if not include_superseded:
            nuggets = [n for n in nuggets if not n.is_superseded]

        if min_certainty:
            certainty_order = list(InsightConfidence)
            min_idx = certainty_order.index(min_certainty)
            nuggets = [
                n for n in nuggets
                if certainty_order.index(n.certainty_level) >= min_idx
            ]

        return sorted(nuggets, key=lambda x: x.updated_at, reverse=True)[:limit]

    async def search_insights(
        self,
        query: str,
        search_in: str = "all",  # "buffer", "synthesized", "knowledge", "all"
    ) -> Dict[str, List[Any]]:
        """Søg efter indsigter med en tekstforespørgsel."""
        query_lower = query.lower()
        results: Dict[str, List[Any]] = {
            "buffer": [],
            "synthesized": [],
            "knowledge": [],
        }

        if search_in in ["buffer", "all"]:
            async with self._lock:
                for insight in self._insights_buffer:
                    if query_lower in insight.content.lower():
                        results["buffer"].append(insight)
                    elif any(query_lower in tag.lower() for tag in insight.tags):
                        results["buffer"].append(insight)

        if search_in in ["synthesized", "all"]:
            async with self._lock:
                for synth in self._synthesized.values():
                    if query_lower in synth.title.lower():
                        results["synthesized"].append(synth)
                    elif query_lower in synth.summary.lower():
                        results["synthesized"].append(synth)
                    elif any(query_lower in tag.lower() for tag in synth.tags):
                        results["synthesized"].append(synth)

        if search_in in ["knowledge", "all"]:
            async with self._lock:
                for nugget in self._knowledge_nuggets.values():
                    if query_lower in nugget.title.lower():
                        results["knowledge"].append(nugget)
                    elif query_lower in nugget.essence.lower():
                        results["knowledge"].append(nugget)

        return results

    # ========================================================================
    # LISTENERS
    # ========================================================================

    def add_synthesis_listener(
        self,
        listener: Callable[[SynthesizedInsight], None],
    ) -> None:
        """Tilføj listener for nye syntetiserede indsigter."""
        self._synthesis_listeners.append(listener)

    def add_recommendation_listener(
        self,
        listener: Callable[[ActionRecommendation], None],
    ) -> None:
        """Tilføj listener for nye anbefalinger."""
        self._recommendation_listeners.append(listener)

    def add_knowledge_listener(
        self,
        listener: Callable[[KnowledgeNugget], None],
    ) -> None:
        """Tilføj listener for nye knowledge nuggets."""
        self._knowledge_listeners.append(listener)

    def remove_synthesis_listener(
        self,
        listener: Callable[[SynthesizedInsight], None],
    ) -> bool:
        """Fjern synthesis listener."""
        try:
            self._synthesis_listeners.remove(listener)
            return True
        except ValueError:
            return False

    # ========================================================================
    # STATS & STATUS
    # ========================================================================

    async def get_stats(self) -> SynthesizerStats:
        """Hent statistikker."""
        async with self._lock:
            stats = self._stats

            if self._started_at:
                stats.uptime_seconds = (datetime.now() - self._started_at).total_seconds()

            # Beregn gennemsnit
            if self._synthesized:
                synths = list(self._synthesized.values())
                stats.average_confidence = statistics.mean(s.confidence_score for s in synths)
                stats.average_source_count = statistics.mean(len(s.source_insights) for s in synths)
                stats.average_synthesis_time_ms = statistics.mean(s.synthesis_duration_ms for s in synths)
                stats.high_impact_insights = sum(
                    1 for s in synths
                    if s.impact_level in [ImpactLevel.SIGNIFICANT, ImpactLevel.CRITICAL]
                )

            return stats

    async def get_status(self) -> Dict[str, Any]:
        """Hent status for synthesizer."""
        stats = await self.get_stats()

        return {
            "synthesizer_id": self.synthesizer_id,
            "is_running": self._is_running,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "buffer_size": len(self._insights_buffer),
            "synthesized_count": len(self._synthesized),
            "recommendations_count": len(self._recommendations),
            "knowledge_nuggets_count": len(self._knowledge_nuggets),
            "auto_synthesis_enabled": self.enable_auto_synthesis,
            "stats": stats.to_dict(),
        }

    async def clear_buffer(self) -> int:
        """Ryd insights bufferen."""
        async with self._lock:
            count = len(self._insights_buffer)
            self._insights_buffer.clear()

        logger.info(f"Buffer ryddet: {count} indsigter fjernet")
        return count


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

# Global instance
_synthesizer_instance: Optional[InsightSynthesizer] = None


def create_insight_synthesizer(
    synthesizer_id: Optional[str] = None,
    max_insights_buffer: int = 1000,
    synthesis_threshold: int = 3,
    auto_synthesize_interval: float = 60.0,
    enable_auto_synthesis: bool = True,
) -> InsightSynthesizer:
    """
    Opret en ny InsightSynthesizer.

    Args:
        synthesizer_id: Unikt ID for synthesizer
        max_insights_buffer: Max antal indsigter i buffer
        synthesis_threshold: Min antal for auto-syntese
        auto_synthesize_interval: Sekunder mellem auto-syntese
        enable_auto_synthesis: Om auto-syntese er aktiveret

    Returns:
        Ny InsightSynthesizer instance
    """
    return InsightSynthesizer(
        synthesizer_id=synthesizer_id,
        max_insights_buffer=max_insights_buffer,
        synthesis_threshold=synthesis_threshold,
        auto_synthesize_interval=auto_synthesize_interval,
        enable_auto_synthesis=enable_auto_synthesis,
    )


def get_insight_synthesizer() -> Optional[InsightSynthesizer]:
    """Hent global InsightSynthesizer instance."""
    return _synthesizer_instance


def set_insight_synthesizer(synthesizer: InsightSynthesizer) -> None:
    """Sæt global InsightSynthesizer instance."""
    global _synthesizer_instance
    _synthesizer_instance = synthesizer


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def ingest_insight(
    source_type: InsightSourceType,
    source_id: str,
    content: str,
    data: Dict[str, Any],
    relevance_score: float = 0.5,
    tags: Optional[List[str]] = None,
) -> Optional[SourceInsight]:
    """Convenience: Modtag indsigt via global instance."""
    synth = get_insight_synthesizer()
    if synth:
        return await synth.ingest_insight(
            source_type, source_id, content, data, relevance_score, tags
        )
    return None


async def synthesize_insights(
    focus_areas: Optional[List[str]] = None,
    time_window_hours: float = 1.0,
) -> List[SynthesizedInsight]:
    """Convenience: Kør syntese via global instance."""
    synth = get_insight_synthesizer()
    if synth:
        context = SynthesisContext(
            context_id=f"manual_{uuid4().hex[:8]}",
            focus_areas=focus_areas or [],
            time_window=timedelta(hours=time_window_hours),
        )
        return await synth.synthesize(context)
    return []


async def get_actionable_recommendations(
    limit: int = 10,
) -> List[ActionRecommendation]:
    """Convenience: Hent aktive anbefalinger."""
    synth = get_insight_synthesizer()
    if synth:
        return await synth.get_recommendations(status="proposed", limit=limit)
    return []


# ============================================================================
# MASTERMIND INTEGRATION
# ============================================================================

async def create_mastermind_insight_synthesizer() -> InsightSynthesizer:
    """
    Opret InsightSynthesizer konfigureret til MASTERMIND.

    Returns:
        InsightSynthesizer klar til MASTERMIND brug
    """
    synthesizer = create_insight_synthesizer(
        synthesizer_id="mastermind_synthesizer",
        max_insights_buffer=2000,
        synthesis_threshold=5,
        auto_synthesize_interval=120.0,  # Hver 2. minut
        enable_auto_synthesis=True,
    )

    set_insight_synthesizer(synthesizer)

    await synthesizer.start()

    logger.info("MASTERMIND InsightSynthesizer initialiseret")

    return synthesizer
