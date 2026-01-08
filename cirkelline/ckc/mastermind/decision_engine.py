"""
DECISION ENGINE - DEL W
========================

Struktureret beslutningstagning for MASTERMIND.

This module provides:
- Decision workflows with multiple stages
- Option evaluation against weighted criteria
- Decision tracking and audit trail
- Think-aloud integration for transparent decisions
- Collective wisdom application to decisions
- Rollback and revision support

Follows CoreWisdom principle FULL_TRANSPARENCY:
"All paths clarified and guided, nothing unknown."
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class DecisionCategory(Enum):
    """Category of decision."""
    STRATEGIC = "strategic"       # Long-term impact
    TACTICAL = "tactical"         # Medium-term impact
    OPERATIONAL = "operational"   # Immediate impact
    EMERGENCY = "emergency"       # Urgent, time-critical


class DecisionComplexity(Enum):
    """Complexity level of decision."""
    TRIVIAL = "trivial"           # No analysis needed
    SIMPLE = "simple"             # Few factors
    MODERATE = "moderate"         # Multiple factors
    COMPLEX = "complex"           # Many interdependent factors
    CRITICAL = "critical"         # Requires extensive analysis


class DecisionStatus(Enum):
    """Status of a decision."""
    DRAFT = "draft"
    EVALUATING = "evaluating"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    REVOKED = "revoked"


class CriterionType(Enum):
    """Type of evaluation criterion."""
    BENEFIT = "benefit"           # Higher is better
    COST = "cost"                 # Lower is better
    THRESHOLD = "threshold"       # Must meet minimum
    BOOLEAN = "boolean"           # Yes/no criterion


class EvaluationMethod(Enum):
    """Method for evaluating options."""
    WEIGHTED_SUM = "weighted_sum"         # Sum of weighted scores
    PAIRWISE = "pairwise"                 # Compare pairs
    CONSENSUS = "consensus"               # Group agreement
    VETO = "veto"                         # Any veto rejects
    HYBRID = "hybrid"                     # Combination


class DecisionOutcome(Enum):
    """Outcome of a decision."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    PENDING = "pending"
    UNKNOWN = "unknown"


# =============================================================================
# TYPE ALIASES
# =============================================================================

DecisionCallback = Callable[[str], Coroutine[Any, Any, None]]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Criterion:
    """An evaluation criterion."""
    id: str
    name: str
    description: str
    weight: float = 1.0  # 0.0 to 1.0
    criterion_type: CriterionType = CriterionType.BENEFIT
    threshold: Optional[float] = None  # For THRESHOLD type
    required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Option:
    """An option to evaluate."""
    id: str
    name: str
    description: str
    scores: Dict[str, float] = field(default_factory=dict)  # criterion_id -> score
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    total_score: float = 0.0
    rank: int = 0
    selected: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionContext:
    """Context for a decision."""
    domain: str
    stakeholders: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    time_pressure: float = 0.5  # 0.0 = no pressure, 1.0 = urgent
    reversibility: float = 0.5  # 0.0 = irreversible, 1.0 = easily reversible
    impact_scope: str = "local"  # local, team, organization, system
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionRationale:
    """Rationale for a decision."""
    summary: str
    key_factors: List[str] = field(default_factory=list)
    wisdom_applied: List[str] = field(default_factory=list)
    trade_offs: List[str] = field(default_factory=list)
    alternatives_considered: int = 0
    confidence: float = 0.8


@dataclass
class DecisionRecord:
    """Complete record of a decision."""
    id: str
    title: str
    question: str
    category: DecisionCategory
    complexity: DecisionComplexity
    status: DecisionStatus
    context: DecisionContext
    criteria: List[Criterion]
    options: List[Option]
    selected_option: Optional[str] = None
    rationale: Optional[DecisionRationale] = None
    outcome: DecisionOutcome = DecisionOutcome.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    decided_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    approved_by: Optional[str] = None
    revision_of: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of option evaluation."""
    decision_id: str
    method: EvaluationMethod
    ranked_options: List[Tuple[str, float]]  # (option_id, score)
    recommended_option: str
    confidence: float
    evaluation_notes: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DecisionEngineStats:
    """Statistics for the decision engine."""
    decisions_made: int = 0
    decisions_pending: int = 0
    decisions_implemented: int = 0
    decisions_revoked: int = 0
    avg_decision_time_ms: float = 0.0
    avg_options_considered: float = 0.0
    success_rate: float = 0.0
    by_category: Dict[str, int] = field(default_factory=dict)
    by_complexity: Dict[str, int] = field(default_factory=dict)


# =============================================================================
# DECISION BUILDER
# =============================================================================

class DecisionBuilder:
    """Builder for creating decision records."""

    def __init__(self, title: str, question: str):
        self._id = f"dec_{uuid4().hex[:12]}"
        self._title = title
        self._question = question
        self._category = DecisionCategory.OPERATIONAL
        self._complexity = DecisionComplexity.MODERATE
        self._context = DecisionContext(domain="general")
        self._criteria: List[Criterion] = []
        self._options: List[Option] = []
        self._metadata: Dict[str, Any] = {}

    def with_category(self, category: DecisionCategory) -> "DecisionBuilder":
        """Set decision category."""
        self._category = category
        return self

    def with_complexity(self, complexity: DecisionComplexity) -> "DecisionBuilder":
        """Set decision complexity."""
        self._complexity = complexity
        return self

    def with_context(
        self,
        domain: str,
        stakeholders: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        time_pressure: float = 0.5,
        reversibility: float = 0.5,
        impact_scope: str = "local",
    ) -> "DecisionBuilder":
        """Set decision context."""
        self._context = DecisionContext(
            domain=domain,
            stakeholders=stakeholders or [],
            constraints=constraints or [],
            time_pressure=time_pressure,
            reversibility=reversibility,
            impact_scope=impact_scope,
        )
        return self

    def add_criterion(
        self,
        name: str,
        description: str,
        weight: float = 1.0,
        criterion_type: CriterionType = CriterionType.BENEFIT,
        threshold: Optional[float] = None,
        required: bool = False,
    ) -> "DecisionBuilder":
        """Add an evaluation criterion."""
        criterion = Criterion(
            id=f"crit_{uuid4().hex[:8]}",
            name=name,
            description=description,
            weight=weight,
            criterion_type=criterion_type,
            threshold=threshold,
            required=required,
        )
        self._criteria.append(criterion)
        return self

    def add_option(
        self,
        name: str,
        description: str,
        pros: Optional[List[str]] = None,
        cons: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
    ) -> "DecisionBuilder":
        """Add an option to evaluate."""
        option = Option(
            id=f"opt_{uuid4().hex[:8]}",
            name=name,
            description=description,
            pros=pros or [],
            cons=cons or [],
            risks=risks or [],
        )
        self._options.append(option)
        return self

    def with_metadata(self, key: str, value: Any) -> "DecisionBuilder":
        """Add metadata."""
        self._metadata[key] = value
        return self

    def build(self) -> DecisionRecord:
        """Build the decision record."""
        return DecisionRecord(
            id=self._id,
            title=self._title,
            question=self._question,
            category=self._category,
            complexity=self._complexity,
            status=DecisionStatus.DRAFT,
            context=self._context,
            criteria=self._criteria,
            options=self._options,
            metadata=self._metadata,
        )


# =============================================================================
# MAIN CLASS
# =============================================================================

class DecisionEngine:
    """
    Structured decision-making engine for MASTERMIND.

    Provides comprehensive decision support with:
    - Multi-criteria evaluation
    - Option ranking
    - Decision tracking
    - Think-aloud integration
    - Wisdom application

    Usage:
        engine = DecisionEngine()
        await engine.start()

        # Create decision
        decision = (
            DecisionBuilder("API Design", "Which API pattern to use?")
            .with_category(DecisionCategory.STRATEGIC)
            .add_criterion("Performance", "System performance impact", weight=0.4)
            .add_criterion("Maintainability", "Code maintenance cost", weight=0.3)
            .add_option("REST", "RESTful API", pros=["Simple"], cons=["Verbose"])
            .add_option("GraphQL", "GraphQL API", pros=["Flexible"], cons=["Complex"])
            .build()
        )

        # Submit and evaluate
        await engine.submit_decision(decision)
        result = await engine.evaluate_decision(decision.id)
        await engine.implement_decision(decision.id, result.recommended_option)
    """

    def __init__(
        self,
        name: str = "mastermind_decision_engine",
        auto_evaluate: bool = True,
        require_approval: bool = False,
        approval_threshold: float = 0.7,
    ):
        self.name = name
        self.auto_evaluate = auto_evaluate
        self.require_approval = require_approval
        self.approval_threshold = approval_threshold

        # Storage
        self._decisions: Dict[str, DecisionRecord] = {}
        self._evaluations: Dict[str, EvaluationResult] = {}

        # State
        self._running = False
        self._stats = DecisionEngineStats()

        # Callbacks
        self._on_decision_made: List[DecisionCallback] = []
        self._on_decision_implemented: List[DecisionCallback] = []

        logger.info(f"DecisionEngine initialized: {name}")

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._running

    @property
    def stats(self) -> DecisionEngineStats:
        """Get engine statistics."""
        return self._stats

    @property
    def pending_decisions(self) -> List[DecisionRecord]:
        """Get decisions pending evaluation or approval."""
        return [
            d for d in self._decisions.values()
            if d.status in [DecisionStatus.DRAFT, DecisionStatus.EVALUATING, DecisionStatus.PENDING_APPROVAL]
        ]

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def start(self) -> None:
        """Start the decision engine."""
        if self._running:
            return

        self._running = True
        logger.info(f"DecisionEngine started: {self.name}")

    async def stop(self) -> None:
        """Stop the decision engine."""
        if not self._running:
            return

        self._running = False
        logger.info(f"DecisionEngine stopped: {self.name}")

    # =========================================================================
    # DECISION MANAGEMENT
    # =========================================================================

    async def submit_decision(self, decision: DecisionRecord) -> str:
        """
        Submit a decision for evaluation.

        Args:
            decision: The decision to submit

        Returns:
            Decision ID
        """
        self._decisions[decision.id] = decision
        self._stats.decisions_pending += 1

        logger.info(f"Decision submitted: {decision.title} ({decision.id})")

        # Auto-evaluate if enabled
        if self.auto_evaluate and decision.criteria and decision.options:
            await self.evaluate_decision(decision.id)

        return decision.id

    async def evaluate_decision(
        self,
        decision_id: str,
        method: EvaluationMethod = EvaluationMethod.WEIGHTED_SUM,
        scores: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> EvaluationResult:
        """
        Evaluate a decision's options.

        Args:
            decision_id: ID of the decision to evaluate
            method: Evaluation method to use
            scores: Optional pre-computed scores (option_id -> criterion_id -> score)

        Returns:
            Evaluation result with ranked options
        """
        decision = self._decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision not found: {decision_id}")

        decision.status = DecisionStatus.EVALUATING
        start_time = datetime.now()

        # Apply scores if provided
        if scores:
            for option in decision.options:
                if option.id in scores:
                    option.scores = scores[option.id]

        # Evaluate based on method
        if method == EvaluationMethod.WEIGHTED_SUM:
            ranked = self._weighted_sum_evaluation(decision)
        elif method == EvaluationMethod.PAIRWISE:
            ranked = self._pairwise_evaluation(decision)
        else:
            ranked = self._weighted_sum_evaluation(decision)

        # Update option rankings
        for rank, (option_id, score) in enumerate(ranked, 1):
            for option in decision.options:
                if option.id == option_id:
                    option.total_score = score
                    option.rank = rank
                    break

        # Determine recommended option
        recommended = ranked[0][0] if ranked else None
        confidence = self._calculate_confidence(ranked)

        # Create result
        result = EvaluationResult(
            decision_id=decision_id,
            method=method,
            ranked_options=ranked,
            recommended_option=recommended or "",
            confidence=confidence,
            evaluation_notes=[
                f"Evaluated {len(decision.options)} options",
                f"Against {len(decision.criteria)} criteria",
                f"Top option: {ranked[0][0] if ranked else 'None'} (score: {ranked[0][1]:.2f})" if ranked else "",
            ],
        )

        self._evaluations[decision_id] = result

        # Update decision status
        if self.require_approval and confidence < self.approval_threshold:
            decision.status = DecisionStatus.PENDING_APPROVAL
        else:
            decision.status = DecisionStatus.APPROVED

        # Update stats
        eval_time = (datetime.now() - start_time).total_seconds() * 1000
        self._update_stats_for_evaluation(eval_time, len(decision.options))

        logger.info(
            f"Decision evaluated: {decision.title} - "
            f"Recommended: {recommended} (confidence: {confidence:.2f})"
        )

        return result

    def _weighted_sum_evaluation(
        self,
        decision: DecisionRecord
    ) -> List[Tuple[str, float]]:
        """Evaluate using weighted sum method."""
        results = []

        # Normalize weights
        total_weight = sum(c.weight for c in decision.criteria)
        if total_weight == 0:
            total_weight = 1

        for option in decision.options:
            score = 0.0

            for criterion in decision.criteria:
                raw_score = option.scores.get(criterion.id, 0.5)

                # Adjust for criterion type
                if criterion.criterion_type == CriterionType.COST:
                    raw_score = 1 - raw_score  # Invert for cost
                elif criterion.criterion_type == CriterionType.THRESHOLD:
                    if criterion.threshold and raw_score < criterion.threshold:
                        raw_score = 0  # Below threshold = 0

                # Apply weight
                weighted_score = raw_score * (criterion.weight / total_weight)
                score += weighted_score

            results.append((option.id, score))

        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _pairwise_evaluation(
        self,
        decision: DecisionRecord
    ) -> List[Tuple[str, float]]:
        """Evaluate using pairwise comparison."""
        wins: Dict[str, int] = {o.id: 0 for o in decision.options}
        total_comparisons = 0

        for i, opt1 in enumerate(decision.options):
            for opt2 in decision.options[i + 1:]:
                # Compare total scores
                score1 = sum(opt1.scores.values())
                score2 = sum(opt2.scores.values())

                if score1 > score2:
                    wins[opt1.id] += 1
                elif score2 > score1:
                    wins[opt2.id] += 1
                else:
                    # Tie - both get half point
                    wins[opt1.id] += 0.5
                    wins[opt2.id] += 0.5

                total_comparisons += 1

        # Convert wins to scores
        if total_comparisons > 0:
            results = [
                (opt_id, win_count / total_comparisons)
                for opt_id, win_count in wins.items()
            ]
        else:
            results = [(o.id, 0.5) for o in decision.options]

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _calculate_confidence(
        self,
        ranked: List[Tuple[str, float]]
    ) -> float:
        """Calculate confidence in the recommendation."""
        if not ranked or len(ranked) < 2:
            return 1.0

        top_score = ranked[0][1]
        second_score = ranked[1][1]

        # Confidence based on gap between top two
        if top_score == 0:
            return 0.5

        gap = (top_score - second_score) / top_score
        return min(0.5 + gap * 0.5, 1.0)

    async def implement_decision(
        self,
        decision_id: str,
        selected_option: str,
        decided_by: Optional[str] = None,
        rationale: Optional[DecisionRationale] = None,
    ) -> bool:
        """
        Implement a decision by selecting an option.

        Args:
            decision_id: ID of the decision
            selected_option: ID of the selected option
            decided_by: Who made the decision
            rationale: Rationale for the decision

        Returns:
            True if implemented successfully
        """
        decision = self._decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision not found: {decision_id}")

        if decision.status not in [DecisionStatus.APPROVED, DecisionStatus.PENDING_APPROVAL]:
            raise ValueError(f"Decision not ready for implementation: {decision.status}")

        # Validate option exists
        option_ids = {o.id for o in decision.options}
        if selected_option not in option_ids:
            raise ValueError(f"Option not found: {selected_option}")

        # Update decision
        decision.selected_option = selected_option
        decision.decided_at = datetime.now()
        decision.implemented_at = datetime.now()
        decision.decided_by = decided_by
        decision.status = DecisionStatus.IMPLEMENTED

        # Mark selected option
        for option in decision.options:
            option.selected = (option.id == selected_option)

        # Set rationale
        if rationale:
            decision.rationale = rationale
        else:
            # Auto-generate rationale
            evaluation = self._evaluations.get(decision_id)
            selected_opt = next((o for o in decision.options if o.id == selected_option), None)

            decision.rationale = DecisionRationale(
                summary=f"Selected '{selected_opt.name if selected_opt else selected_option}' based on evaluation",
                key_factors=[c.name for c in decision.criteria[:3]],
                alternatives_considered=len(decision.options),
                confidence=evaluation.confidence if evaluation else 0.8,
            )

        # Update stats
        self._stats.decisions_pending -= 1
        self._stats.decisions_made += 1
        self._stats.decisions_implemented += 1
        self._stats.by_category[decision.category.value] = \
            self._stats.by_category.get(decision.category.value, 0) + 1
        self._stats.by_complexity[decision.complexity.value] = \
            self._stats.by_complexity.get(decision.complexity.value, 0) + 1

        # Call callbacks
        for callback in self._on_decision_implemented:
            try:
                await callback(decision_id)
            except Exception as e:
                logger.warning(f"Decision callback failed: {e}")

        logger.info(f"Decision implemented: {decision.title} -> {selected_option}")

        return True

    async def revoke_decision(
        self,
        decision_id: str,
        reason: str,
        revoked_by: Optional[str] = None,
    ) -> bool:
        """
        Revoke a previously implemented decision.

        Args:
            decision_id: ID of the decision to revoke
            reason: Reason for revocation
            revoked_by: Who revoked the decision

        Returns:
            True if revoked successfully
        """
        decision = self._decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision not found: {decision_id}")

        if decision.status != DecisionStatus.IMPLEMENTED:
            raise ValueError(f"Cannot revoke decision with status: {decision.status}")

        decision.status = DecisionStatus.REVOKED
        decision.notes.append(f"REVOKED: {reason} (by {revoked_by or 'system'})")
        decision.outcome = DecisionOutcome.FAILURE

        self._stats.decisions_revoked += 1
        self._stats.decisions_implemented -= 1

        logger.warning(f"Decision revoked: {decision.title} - {reason}")

        return True

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """Get a decision by ID."""
        return self._decisions.get(decision_id)

    def get_evaluation(self, decision_id: str) -> Optional[EvaluationResult]:
        """Get evaluation result for a decision."""
        return self._evaluations.get(decision_id)

    def get_decisions_by_status(
        self,
        status: DecisionStatus
    ) -> List[DecisionRecord]:
        """Get decisions with a specific status."""
        return [d for d in self._decisions.values() if d.status == status]

    def get_decisions_by_category(
        self,
        category: DecisionCategory
    ) -> List[DecisionRecord]:
        """Get decisions in a specific category."""
        return [d for d in self._decisions.values() if d.category == category]

    def search_decisions(
        self,
        query: str,
        include_implemented: bool = True,
    ) -> List[DecisionRecord]:
        """Search decisions by title or question."""
        query_lower = query.lower()
        results = []

        for decision in self._decisions.values():
            if not include_implemented and decision.status == DecisionStatus.IMPLEMENTED:
                continue

            if query_lower in decision.title.lower() or query_lower in decision.question.lower():
                results.append(decision)

        return results

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def on_decision_made(self, callback: DecisionCallback) -> None:
        """Register callback for when a decision is made."""
        self._on_decision_made.append(callback)

    def on_decision_implemented(self, callback: DecisionCallback) -> None:
        """Register callback for when a decision is implemented."""
        self._on_decision_implemented.append(callback)

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def _update_stats_for_evaluation(
        self,
        eval_time_ms: float,
        options_count: int
    ) -> None:
        """Update statistics after evaluation."""
        n = self._stats.decisions_made + self._stats.decisions_pending

        if n > 0:
            # Running average for decision time
            self._stats.avg_decision_time_ms = (
                (self._stats.avg_decision_time_ms * (n - 1) + eval_time_ms) / n
            )

            # Running average for options considered
            self._stats.avg_options_considered = (
                (self._stats.avg_options_considered * (n - 1) + options_count) / n
            )

    def calculate_success_rate(self) -> float:
        """Calculate success rate of implemented decisions."""
        implemented = [
            d for d in self._decisions.values()
            if d.status == DecisionStatus.IMPLEMENTED
        ]

        if not implemented:
            return 0.0

        successful = sum(
            1 for d in implemented
            if d.outcome in [DecisionOutcome.SUCCESS, DecisionOutcome.PARTIAL]
        )

        return successful / len(implemented)

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize engine state to dictionary."""
        return {
            "name": self.name,
            "is_running": self._running,
            "total_decisions": len(self._decisions),
            "pending_decisions": len(self.pending_decisions),
            "stats": {
                "decisions_made": self._stats.decisions_made,
                "decisions_pending": self._stats.decisions_pending,
                "decisions_implemented": self._stats.decisions_implemented,
                "decisions_revoked": self._stats.decisions_revoked,
                "avg_decision_time_ms": self._stats.avg_decision_time_ms,
                "avg_options_considered": self._stats.avg_options_considered,
                "success_rate": self.calculate_success_rate(),
                "by_category": self._stats.by_category,
                "by_complexity": self._stats.by_complexity,
            },
        }


# =============================================================================
# SINGLETON MANAGEMENT
# =============================================================================

_decision_engine: Optional[DecisionEngine] = None


def create_decision_engine(
    name: str = "mastermind_decision_engine",
    auto_evaluate: bool = True,
    require_approval: bool = False,
    approval_threshold: float = 0.7,
) -> DecisionEngine:
    """
    Create a new DecisionEngine instance.

    Args:
        name: Engine name
        auto_evaluate: Auto-evaluate when decision is submitted
        require_approval: Require approval for low-confidence decisions
        approval_threshold: Confidence threshold for auto-approval

    Returns:
        New DecisionEngine instance
    """
    return DecisionEngine(
        name=name,
        auto_evaluate=auto_evaluate,
        require_approval=require_approval,
        approval_threshold=approval_threshold,
    )


def get_decision_engine() -> Optional[DecisionEngine]:
    """Get the global decision engine instance."""
    return _decision_engine


def set_decision_engine(engine: DecisionEngine) -> None:
    """Set the global decision engine instance."""
    global _decision_engine
    _decision_engine = engine


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def quick_decision(
    title: str,
    question: str,
    options: List[str],
    criteria: Optional[List[Tuple[str, float]]] = None,
) -> DecisionRecord:
    """
    Quickly create a simple decision.

    Args:
        title: Decision title
        question: Decision question
        options: List of option names
        criteria: Optional list of (criterion_name, weight) tuples

    Returns:
        Decision record ready for submission
    """
    builder = DecisionBuilder(title, question)

    # Add default criteria if not provided
    if criteria:
        for name, weight in criteria:
            builder.add_criterion(name, f"Evaluate {name}", weight=weight)
    else:
        builder.add_criterion("Effectiveness", "How effective is this option?", weight=0.5)
        builder.add_criterion("Feasibility", "How feasible is this option?", weight=0.5)

    # Add options
    for option_name in options:
        builder.add_option(option_name, f"Option: {option_name}")

    return builder.build()


def create_strategic_decision(
    title: str,
    question: str,
    domain: str,
    stakeholders: List[str],
) -> DecisionBuilder:
    """
    Create a builder for a strategic decision.

    Args:
        title: Decision title
        question: Decision question
        domain: Business domain
        stakeholders: List of stakeholders

    Returns:
        Configured DecisionBuilder
    """
    return (
        DecisionBuilder(title, question)
        .with_category(DecisionCategory.STRATEGIC)
        .with_complexity(DecisionComplexity.COMPLEX)
        .with_context(
            domain=domain,
            stakeholders=stakeholders,
            time_pressure=0.3,
            reversibility=0.2,
            impact_scope="organization",
        )
        .add_criterion("Strategic Alignment", "Alignment with goals", weight=0.3)
        .add_criterion("Long-term Value", "Long-term benefits", weight=0.25)
        .add_criterion("Risk", "Associated risks", weight=0.2, criterion_type=CriterionType.COST)
        .add_criterion("Resources", "Resource requirements", weight=0.15, criterion_type=CriterionType.COST)
        .add_criterion("Stakeholder Impact", "Impact on stakeholders", weight=0.1)
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "DecisionCategory",
    "DecisionComplexity",
    "DecisionStatus",
    "CriterionType",
    "EvaluationMethod",
    "DecisionOutcome",

    # Data classes
    "Criterion",
    "Option",
    "DecisionContext",
    "DecisionRationale",
    "DecisionRecord",
    "EvaluationResult",
    "DecisionEngineStats",

    # Builder
    "DecisionBuilder",

    # Main class
    "DecisionEngine",

    # Factory functions
    "create_decision_engine",
    "get_decision_engine",
    "set_decision_engine",

    # Helper functions
    "quick_decision",
    "create_strategic_decision",
]
