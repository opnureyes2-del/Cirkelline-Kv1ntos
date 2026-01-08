"""
CKC MASTERMIND Feedback System
==============================

Realtids feedback aggregation og analyse.

Komponenter:
- ResultCollector: Indsaml og validér resultater
- SynthesisEngine: Sammenfat relaterede resultater
- DecisionEngine: Evaluér mod kriterier
- AdjustmentDispatcher: Distribuer justeringer
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .coordinator import (
    MastermindSession,
    MastermindStatus,
    TaskResult,
    FeedbackReport,
    TaskStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# FEEDBACK ENUMS
# =============================================================================

class FeedbackSeverity(Enum):
    """Sværhedsgrad for feedback."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Typer af alerts."""
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    QUALITY = "quality"
    DEADLINE = "deadline"
    AGENT_ISSUE = "agent_issue"


class RecommendationType(Enum):
    """Typer af anbefalinger."""
    ADD_AGENT = "add_agent"
    REMOVE_AGENT = "remove_agent"
    REPRIORITIZE = "reprioritize"
    REALLOCATE = "reallocate"
    PAUSE = "pause"
    ESCALATE = "escalate"


# =============================================================================
# FEEDBACK DATA CLASSES
# =============================================================================

@dataclass
class FeedbackItem:
    """En enkelt feedback item."""
    item_id: str
    session_id: str
    source: str  # agent_id eller "system"
    category: str
    message: str
    severity: FeedbackSeverity = FeedbackSeverity.INFO
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "session_id": self.session_id,
            "source": self.source,
            "category": self.category,
            "message": self.message,
            "severity": self.severity.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged
        }


@dataclass
class Alert:
    """En alert i systemet."""
    alert_id: str
    session_id: str
    alert_type: AlertType
    severity: FeedbackSeverity
    title: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "session_id": self.session_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class Recommendation:
    """En anbefaling fra systemet."""
    rec_id: str
    session_id: str
    rec_type: RecommendationType
    priority: int  # 1-5
    title: str
    description: str
    rationale: str
    impact: str
    action_params: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    accepted: Optional[bool] = None
    executed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rec_id": self.rec_id,
            "session_id": self.session_id,
            "rec_type": self.rec_type.value,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "impact": self.impact,
            "action_params": self.action_params,
            "created_at": self.created_at.isoformat(),
            "accepted": self.accepted,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None
        }


# =============================================================================
# RESULT COLLECTOR
# =============================================================================

class ResultCollector:
    """
    Indsamler og validerer resultater fra agenter.

    Features:
    - Validering af resultatformat
    - Normalisering
    - Confidence scoring
    """

    def __init__(self):
        self._results: Dict[str, List[TaskResult]] = {}  # session_id -> results
        self._validation_rules: List[Callable[[TaskResult], bool]] = []

    def add_validation_rule(
        self,
        rule: Callable[[TaskResult], bool]
    ) -> None:
        """Tilføj valideringsregel."""
        self._validation_rules.append(rule)

    async def collect(
        self,
        session_id: str,
        result: TaskResult
    ) -> bool:
        """
        Indsaml et resultat.

        Args:
            session_id: Session ID
            result: Resultat

        Returns:
            True hvis valideret og indsamlet
        """
        # Validate
        for rule in self._validation_rules:
            if not rule(result):
                logger.warning(f"Resultat {result.task_id} fejlede validering")
                return False

        # Normalize confidence
        result.confidence = max(0.0, min(1.0, result.confidence))

        # Store
        if session_id not in self._results:
            self._results[session_id] = []

        self._results[session_id].append(result)

        logger.debug(f"Resultat indsamlet: {result.task_id} (confidence: {result.confidence})")
        return True

    def get_results(
        self,
        session_id: str,
        min_confidence: float = 0.0
    ) -> List[TaskResult]:
        """Hent indsamlede resultater."""
        results = self._results.get(session_id, [])

        if min_confidence > 0:
            results = [r for r in results if r.confidence >= min_confidence]

        return results

    def clear(self, session_id: str) -> None:
        """Ryd resultater for session."""
        if session_id in self._results:
            del self._results[session_id]


# =============================================================================
# SYNTHESIS ENGINE
# =============================================================================

class SynthesisEngine:
    """
    Syntesiserer relaterede resultater.

    Features:
    - Merge relaterede resultater
    - Konflikt detektion
    - Composite view opbygning
    """

    def __init__(self):
        self._merge_strategies: Dict[str, Callable] = {}

    def register_merge_strategy(
        self,
        result_type: str,
        strategy: Callable[[List[TaskResult]], Any]
    ) -> None:
        """Registrer merge strategi for resultattype."""
        self._merge_strategies[result_type] = strategy

    async def synthesize(
        self,
        results: List[TaskResult]
    ) -> Dict[str, Any]:
        """
        Syntesiser resultater.

        Args:
            results: Liste af resultater

        Returns:
            Syntetiseret resultat
        """
        if not results:
            return {"synthesis": None, "count": 0}

        # Group by task category if available
        grouped: Dict[str, List[TaskResult]] = {}
        for result in results:
            category = result.metrics.get("category", "default")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(result)

        # Detect conflicts
        conflicts = self._detect_conflicts(results)

        # Build composite
        composite = {
            "synthesis_id": f"syn_{secrets.token_hex(6)}",
            "total_results": len(results),
            "categories": list(grouped.keys()),
            "successful": len([r for r in results if r.success]),
            "failed": len([r for r in results if not r.success]),
            "conflicts": conflicts,
            "avg_confidence": sum(r.confidence for r in results) / len(results),
            "synthesized_at": datetime.now().isoformat()
        }

        # Apply merge strategies
        for category, category_results in grouped.items():
            if category in self._merge_strategies:
                composite[f"merged_{category}"] = self._merge_strategies[category](category_results)
            else:
                composite[f"results_{category}"] = [r.output for r in category_results]

        return composite

    def _detect_conflicts(
        self,
        results: List[TaskResult]
    ) -> List[Dict[str, Any]]:
        """Detekter konflikter mellem resultater."""
        conflicts = []

        # Simple conflict detection based on contradicting outputs
        for i, r1 in enumerate(results):
            for r2 in results[i + 1:]:
                if r1.task_id == r2.task_id and r1.output != r2.output:
                    conflicts.append({
                        "result_1": r1.task_id,
                        "result_2": r2.task_id,
                        "type": "contradicting_output"
                    })

        return conflicts


# =============================================================================
# DECISION ENGINE
# =============================================================================

class DecisionEngine:
    """
    Evaluerer resultater mod succeskriterier.

    Features:
    - Evaluering mod kriterier
    - Flaskehals identifikation
    - Justering forslag
    """

    def __init__(self):
        self._thresholds = {
            "min_success_rate": 0.80,
            "max_avg_duration": 120,  # sekunder
            "min_confidence": 0.70,
            "budget_warning_threshold": 0.80
        }

    def set_threshold(self, key: str, value: float) -> None:
        """Sæt tærskelværdi."""
        self._thresholds[key] = value

    async def evaluate(
        self,
        session: MastermindSession,
        synthesis: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[Recommendation]]:
        """
        Evaluér session mod kriterier.

        Args:
            session: MASTERMIND session
            synthesis: Syntetiseret resultat

        Returns:
            Tuple af (passed, issues, recommendations)
        """
        issues = []
        recommendations = []

        # Check success rate
        total = synthesis.get("total_results", 0)
        if total > 0:
            success_rate = synthesis.get("successful", 0) / total

            if success_rate < self._thresholds["min_success_rate"]:
                issues.append(f"Lav successrate: {success_rate:.1%}")
                recommendations.append(Recommendation(
                    rec_id=f"rec_{secrets.token_hex(6)}",
                    session_id=session.session_id,
                    rec_type=RecommendationType.ESCALATE,
                    priority=4,
                    title="Lav successrate",
                    description=f"Successraten er {success_rate:.1%}, under grænsen på {self._thresholds['min_success_rate']:.1%}",
                    rationale="For mange fejlede opgaver kan indikere problemer",
                    impact="Sessionen kan muligvis ikke opfylde sine mål"
                ))

        # Check confidence
        avg_confidence = synthesis.get("avg_confidence", 1.0)
        if avg_confidence < self._thresholds["min_confidence"]:
            issues.append(f"Lav gennemsnitlig confidence: {avg_confidence:.1%}")

        # Check conflicts
        conflicts = synthesis.get("conflicts", [])
        if conflicts:
            issues.append(f"{len(conflicts)} konflikt(er) detekteret")
            recommendations.append(Recommendation(
                rec_id=f"rec_{secrets.token_hex(6)}",
                session_id=session.session_id,
                rec_type=RecommendationType.REALLOCATE,
                priority=3,
                title="Konflikter detekteret",
                description=f"Der er fundet {len(conflicts)} konflikter mellem resultater",
                rationale="Konflikter kan indikere overlap eller modstridende resultater",
                impact="Manual review kan være nødvendig"
            ))

        # Check budget
        if session.budget_usd > 0:
            budget_usage = session.consumed_usd / session.budget_usd
            if budget_usage >= self._thresholds["budget_warning_threshold"]:
                issues.append(f"Budget snart opbrugt: {budget_usage:.1%}")
                recommendations.append(Recommendation(
                    rec_id=f"rec_{secrets.token_hex(6)}",
                    session_id=session.session_id,
                    rec_type=RecommendationType.PAUSE,
                    priority=5,
                    title="Budget advarsel",
                    description=f"Budget er {budget_usage:.1%} brugt",
                    rationale="Overskridelse af budget kan forårsage uventet stop",
                    impact="Sessionen kan stoppes før fuldførelse"
                ))

        passed = len(issues) == 0

        return passed, issues, recommendations

    def identify_bottlenecks(
        self,
        session: MastermindSession
    ) -> List[Dict[str, Any]]:
        """
        Identificér flaskehalse i sessionen.

        Args:
            session: MASTERMIND session

        Returns:
            Liste af identificerede flaskehalse
        """
        bottlenecks = []

        # Check for stuck tasks
        for task in session.tasks.values():
            if task.status == TaskStatus.IN_PROGRESS and task.started_at:
                duration = (datetime.now() - task.started_at).total_seconds()
                if duration > self._thresholds["max_avg_duration"] * 2:
                    bottlenecks.append({
                        "type": "stuck_task",
                        "task_id": task.task_id,
                        "duration_seconds": duration,
                        "assigned_to": task.assigned_to
                    })

        # Check for unassigned high-priority tasks
        pending_high = [
            t for t in session.tasks.values()
            if t.status == TaskStatus.PENDING and t.priority.value >= 3
        ]
        if len(pending_high) > 5:
            bottlenecks.append({
                "type": "pending_high_priority",
                "count": len(pending_high)
            })

        # Check agent workload imbalance
        agent_loads: Dict[str, int] = {}
        for task in session.tasks.values():
            if task.assigned_to:
                agent_loads[task.assigned_to] = agent_loads.get(task.assigned_to, 0) + 1

        if agent_loads:
            max_load = max(agent_loads.values())
            min_load = min(agent_loads.values())
            if max_load > min_load * 3:
                bottlenecks.append({
                    "type": "workload_imbalance",
                    "max_load": max_load,
                    "min_load": min_load
                })

        return bottlenecks


# =============================================================================
# ADJUSTMENT DISPATCHER
# =============================================================================

class AdjustmentDispatcher:
    """
    Dispatcher for justeringer baseret på feedback.

    Features:
    - Route nye direktiver
    - Opdater agent prioriteter
    - Omallokér ressourcer
    """

    def __init__(self):
        self._dispatch_handlers: Dict[RecommendationType, Callable] = {}
        self._dispatch_history: List[Dict[str, Any]] = []

    def register_handler(
        self,
        rec_type: RecommendationType,
        handler: Callable
    ) -> None:
        """Registrer handler for anbefalingstype."""
        self._dispatch_handlers[rec_type] = handler

    async def dispatch(
        self,
        recommendation: Recommendation,
        session: MastermindSession
    ) -> bool:
        """
        Dispatch en anbefaling.

        Args:
            recommendation: Anbefaling
            session: Session

        Returns:
            True hvis dispatched succesfuldt
        """
        rec_type = recommendation.rec_type

        if rec_type in self._dispatch_handlers:
            try:
                await self._dispatch_handlers[rec_type](recommendation, session)
                recommendation.executed_at = datetime.now()

                self._dispatch_history.append({
                    "rec_id": recommendation.rec_id,
                    "rec_type": rec_type.value,
                    "session_id": session.session_id,
                    "dispatched_at": datetime.now().isoformat()
                })

                logger.info(f"Anbefaling dispatched: {recommendation.rec_id}")
                return True

            except Exception as e:
                logger.error(f"Dispatch fejl for {recommendation.rec_id}: {e}")
                return False

        logger.warning(f"Ingen handler for anbefalingstype: {rec_type.value}")
        return False

    def get_dispatch_history(
        self,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Hent dispatch historik."""
        history = self._dispatch_history

        if session_id:
            history = [h for h in history if h.get("session_id") == session_id]

        return history


# =============================================================================
# FEEDBACK AGGREGATOR (Main component)
# =============================================================================

class FeedbackAggregator:
    """
    Central feedback aggregator for MASTERMIND.

    Kombinerer:
    - ResultCollector
    - SynthesisEngine
    - DecisionEngine
    - AdjustmentDispatcher
    """

    def __init__(self):
        self.collector = ResultCollector()
        self.synthesis_engine = SynthesisEngine()
        self.decision_engine = DecisionEngine()
        self.dispatcher = AdjustmentDispatcher()

        self._feedback_items: Dict[str, List[FeedbackItem]] = {}
        self._alerts: Dict[str, List[Alert]] = {}

    async def process_result(
        self,
        session: MastermindSession,
        result: TaskResult
    ) -> FeedbackReport:
        """
        Behandl et resultat og generer feedback rapport.

        Args:
            session: MASTERMIND session
            result: Nyt resultat

        Returns:
            FeedbackReport
        """
        # Collect
        await self.collector.collect(session.session_id, result)

        # Get all results
        results = self.collector.get_results(session.session_id)

        # Synthesize
        synthesis = await self.synthesis_engine.synthesize(results)

        # Evaluate
        passed, issues, recommendations = await self.decision_engine.evaluate(
            session, synthesis
        )

        # Generate alerts for issues
        for issue in issues:
            alert = Alert(
                alert_id=f"alert_{secrets.token_hex(6)}",
                session_id=session.session_id,
                alert_type=AlertType.QUALITY,
                severity=FeedbackSeverity.WARNING,
                title="Evaluering issue",
                description=issue
            )
            self._add_alert(session.session_id, alert)

        # Generate report
        report = FeedbackReport(
            report_id=f"fb_{secrets.token_hex(6)}",
            session_id=session.session_id,
            progress_percent=self._calculate_progress(session),
            completed_tasks=len([t for t in session.tasks.values() if t.status == TaskStatus.COMPLETED]),
            pending_tasks=len([t for t in session.tasks.values() if t.status == TaskStatus.PENDING]),
            active_agents=len([a for a in session.active_agents.values() if a.status == "working"]),
            issues=issues,
            recommendations=[r.title for r in recommendations],
            resource_usage={
                "budget_used_percent": (session.consumed_usd / session.budget_usd * 100) if session.budget_usd > 0 else 0,
                "consumed_usd": session.consumed_usd
            }
        )

        return report

    async def generate_full_report(
        self,
        session: MastermindSession
    ) -> Dict[str, Any]:
        """
        Generer fuld feedback rapport.

        Args:
            session: MASTERMIND session

        Returns:
            Komplet rapport
        """
        results = self.collector.get_results(session.session_id)
        synthesis = await self.synthesis_engine.synthesize(results)
        passed, issues, recommendations = await self.decision_engine.evaluate(session, synthesis)
        bottlenecks = self.decision_engine.identify_bottlenecks(session)

        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "synthesis": synthesis,
            "evaluation": {
                "passed": passed,
                "issues": issues
            },
            "bottlenecks": bottlenecks,
            "recommendations": [r.to_dict() for r in recommendations],
            "alerts": [a.to_dict() for a in self._alerts.get(session.session_id, [])],
            "generated_at": datetime.now().isoformat()
        }

    def add_feedback(
        self,
        session_id: str,
        source: str,
        category: str,
        message: str,
        severity: FeedbackSeverity = FeedbackSeverity.INFO,
        data: Optional[Dict[str, Any]] = None
    ) -> FeedbackItem:
        """Tilføj feedback item."""
        item = FeedbackItem(
            item_id=f"fb_{secrets.token_hex(6)}",
            session_id=session_id,
            source=source,
            category=category,
            message=message,
            severity=severity,
            data=data or {}
        )

        if session_id not in self._feedback_items:
            self._feedback_items[session_id] = []

        self._feedback_items[session_id].append(item)
        return item

    def get_feedback(
        self,
        session_id: str,
        severity: Optional[FeedbackSeverity] = None
    ) -> List[FeedbackItem]:
        """Hent feedback items."""
        items = self._feedback_items.get(session_id, [])

        if severity:
            items = [i for i in items if i.severity == severity]

        return items

    def get_alerts(
        self,
        session_id: str,
        unresolved_only: bool = False
    ) -> List[Alert]:
        """Hent alerts."""
        alerts = self._alerts.get(session_id, [])

        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved_at]

        return alerts

    def _add_alert(self, session_id: str, alert: Alert) -> None:
        """Tilføj alert."""
        if session_id not in self._alerts:
            self._alerts[session_id] = []
        self._alerts[session_id].append(alert)

    def _calculate_progress(self, session: MastermindSession) -> float:
        """Beregn samlet fremskridt."""
        total = len(session.tasks)
        if total == 0:
            return 0.0

        completed = len([t for t in session.tasks.values() if t.status == TaskStatus.COMPLETED])
        return round(completed / total * 100, 2)


# =============================================================================
# FACTORY
# =============================================================================

_feedback_aggregator_instance: Optional[FeedbackAggregator] = None


def create_feedback_aggregator() -> FeedbackAggregator:
    """Opret FeedbackAggregator instance."""
    global _feedback_aggregator_instance
    _feedback_aggregator_instance = FeedbackAggregator()
    return _feedback_aggregator_instance


def get_feedback_aggregator() -> Optional[FeedbackAggregator]:
    """Hent den aktuelle FeedbackAggregator instance."""
    return _feedback_aggregator_instance
