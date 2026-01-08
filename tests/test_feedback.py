"""
Tests for CKC MASTERMIND Feedback System (cirkelline.ckc.mastermind.feedback)
=============================================================================

Tests covering:
- Enums: FeedbackSeverity, AlertType, RecommendationType
- Data Classes: FeedbackItem, Alert, Recommendation
- ResultCollector
- SynthesisEngine
- DecisionEngine
- AdjustmentDispatcher
- FeedbackAggregator
- Factory functions
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from cirkelline.ckc.mastermind.feedback import (
    # Enums
    FeedbackSeverity,
    AlertType,
    RecommendationType,
    # Data Classes
    FeedbackItem,
    Alert,
    Recommendation,
    # Classes
    ResultCollector,
    SynthesisEngine,
    DecisionEngine,
    AdjustmentDispatcher,
    FeedbackAggregator,
    # Factory functions
    create_feedback_aggregator,
    get_feedback_aggregator,
)
from cirkelline.ckc.mastermind.coordinator import (
    MastermindSession,
    MastermindStatus,
    TaskResult,
    TaskStatus,
    MastermindTask,
    MastermindPriority,
)


# =============================================================================
# TESTS FOR ENUMS
# =============================================================================

class TestFeedbackEnums:
    """Tests for feedback enums."""

    def test_feedback_severity_values(self):
        """Test FeedbackSeverity values."""
        assert FeedbackSeverity.INFO.value == "info"
        assert FeedbackSeverity.WARNING.value == "warning"
        assert FeedbackSeverity.ERROR.value == "error"
        assert FeedbackSeverity.CRITICAL.value == "critical"

    def test_alert_type_values(self):
        """Test AlertType values."""
        assert AlertType.PERFORMANCE.value == "performance"
        assert AlertType.RESOURCE.value == "resource"
        assert AlertType.QUALITY.value == "quality"
        assert AlertType.DEADLINE.value == "deadline"
        assert AlertType.AGENT_ISSUE.value == "agent_issue"

    def test_recommendation_type_values(self):
        """Test RecommendationType values."""
        assert RecommendationType.ADD_AGENT.value == "add_agent"
        assert RecommendationType.REMOVE_AGENT.value == "remove_agent"
        assert RecommendationType.REPRIORITIZE.value == "reprioritize"
        assert RecommendationType.REALLOCATE.value == "reallocate"
        assert RecommendationType.PAUSE.value == "pause"
        assert RecommendationType.ESCALATE.value == "escalate"


# =============================================================================
# TESTS FOR DATA CLASSES
# =============================================================================

class TestFeedbackItem:
    """Tests for FeedbackItem dataclass."""

    def test_feedback_item_creation_minimal(self):
        """Test creating feedback item with minimal parameters."""
        item = FeedbackItem(
            item_id="fb_001",
            session_id="s001",
            source="agent_001",
            category="performance",
            message="Task completed"
        )
        assert item.item_id == "fb_001"
        assert item.severity == FeedbackSeverity.INFO  # default
        assert item.acknowledged is False  # default

    def test_feedback_item_creation_full(self):
        """Test creating feedback item with all parameters."""
        now = datetime.now()
        item = FeedbackItem(
            item_id="fb_002",
            session_id="s002",
            source="system",
            category="alert",
            message="Resource warning",
            severity=FeedbackSeverity.WARNING,
            data={"cpu_usage": 90},
            timestamp=now,
            acknowledged=True
        )
        assert item.severity == FeedbackSeverity.WARNING
        assert item.data["cpu_usage"] == 90
        assert item.acknowledged is True

    def test_feedback_item_to_dict(self):
        """Test feedback item serialization."""
        item = FeedbackItem(
            item_id="fb_003",
            session_id="s003",
            source="agent_002",
            category="progress",
            message="50% complete"
        )
        data = item.to_dict()

        assert data["item_id"] == "fb_003"
        assert data["severity"] == "info"
        assert "timestamp" in data


class TestAlert:
    """Tests for Alert dataclass."""

    def test_alert_creation_minimal(self):
        """Test creating alert with minimal parameters."""
        alert = Alert(
            alert_id="alert_001",
            session_id="s001",
            alert_type=AlertType.PERFORMANCE,
            severity=FeedbackSeverity.WARNING,
            title="Slow performance",
            description="Task taking longer than expected"
        )
        assert alert.alert_id == "alert_001"
        assert alert.acknowledged_at is None
        assert alert.resolved_at is None

    def test_alert_to_dict(self):
        """Test alert serialization."""
        alert = Alert(
            alert_id="alert_002",
            session_id="s002",
            alert_type=AlertType.RESOURCE,
            severity=FeedbackSeverity.ERROR,
            title="Low memory",
            description="Memory usage critical"
        )
        data = alert.to_dict()

        assert data["alert_type"] == "resource"
        assert data["severity"] == "error"
        assert data["acknowledged_at"] is None


class TestRecommendation:
    """Tests for Recommendation dataclass."""

    def test_recommendation_creation_minimal(self):
        """Test creating recommendation with minimal parameters."""
        rec = Recommendation(
            rec_id="rec_001",
            session_id="s001",
            rec_type=RecommendationType.ADD_AGENT,
            priority=3,
            title="Add more agents",
            description="Workload is high",
            rationale="Current agents are overloaded",
            impact="Faster task completion"
        )
        assert rec.rec_id == "rec_001"
        assert rec.accepted is None  # default
        assert rec.executed_at is None  # default

    def test_recommendation_to_dict(self):
        """Test recommendation serialization."""
        rec = Recommendation(
            rec_id="rec_002",
            session_id="s002",
            rec_type=RecommendationType.PAUSE,
            priority=5,
            title="Pause session",
            description="Budget exceeded",
            rationale="No more budget",
            impact="Session stops"
        )
        data = rec.to_dict()

        assert data["rec_type"] == "pause"
        assert data["priority"] == 5
        assert data["accepted"] is None


# =============================================================================
# TESTS FOR RESULT COLLECTOR
# =============================================================================

class TestResultCollector:
    """Tests for ResultCollector."""

    @pytest.fixture
    def collector(self):
        """Create a fresh collector for each test."""
        return ResultCollector()

    @pytest.mark.asyncio
    async def test_collect_result(self, collector):
        """Test collecting a result."""
        result = TaskResult(
            task_id="t001",
            agent_id="agent_001",
            output={"data": "analysis complete"},
            success=True,
            confidence=0.95
        )
        success = await collector.collect("s001", result)

        assert success is True
        assert len(collector.get_results("s001")) == 1

    @pytest.mark.asyncio
    async def test_collect_with_validation_rule_pass(self, collector):
        """Test collecting with passing validation rule."""
        collector.add_validation_rule(lambda r: r.confidence >= 0.5)

        result = TaskResult(
            task_id="t001",
            agent_id="agent_001",
            output={},
            success=True,
            confidence=0.8
        )
        success = await collector.collect("s001", result)

        assert success is True

    @pytest.mark.asyncio
    async def test_collect_with_validation_rule_fail(self, collector):
        """Test collecting with failing validation rule."""
        collector.add_validation_rule(lambda r: r.confidence >= 0.5)

        result = TaskResult(
            task_id="t001",
            agent_id="agent_001",
            output={},
            success=True,
            confidence=0.3
        )
        success = await collector.collect("s001", result)

        assert success is False

    @pytest.mark.asyncio
    async def test_confidence_normalization(self, collector):
        """Test confidence is normalized to 0-1 range."""
        result = TaskResult(
            task_id="t001",
            agent_id="agent_001",
            output={},
            success=True,
            confidence=1.5  # Above 1
        )
        await collector.collect("s001", result)

        results = collector.get_results("s001")
        assert results[0].confidence == 1.0

    def test_get_results_with_min_confidence(self, collector):
        """Test getting results with minimum confidence filter."""
        # Manually add results to avoid async
        collector._results["s001"] = [
            TaskResult(task_id="t1", agent_id="a1", output={}, success=True, confidence=0.3),
            TaskResult(task_id="t2", agent_id="a2", output={}, success=True, confidence=0.7),
            TaskResult(task_id="t3", agent_id="a3", output={}, success=True, confidence=0.9),
        ]

        results = collector.get_results("s001", min_confidence=0.5)
        assert len(results) == 2

    def test_clear(self, collector):
        """Test clearing results."""
        collector._results["s001"] = [
            TaskResult(task_id="t1", agent_id="a1", output={}, success=True, confidence=0.5)
        ]

        collector.clear("s001")
        assert collector.get_results("s001") == []


# =============================================================================
# TESTS FOR SYNTHESIS ENGINE
# =============================================================================

class TestSynthesisEngine:
    """Tests for SynthesisEngine."""

    @pytest.fixture
    def engine(self):
        """Create a fresh engine for each test."""
        return SynthesisEngine()

    @pytest.mark.asyncio
    async def test_synthesize_empty(self, engine):
        """Test synthesizing empty results."""
        synthesis = await engine.synthesize([])

        assert synthesis["synthesis"] is None
        assert synthesis["count"] == 0

    @pytest.mark.asyncio
    async def test_synthesize_single_result(self, engine):
        """Test synthesizing single result."""
        results = [
            TaskResult(
                task_id="t1",
                agent_id="a1",
                output={"data": "result"},
                success=True,
                confidence=0.9
            )
        ]
        synthesis = await engine.synthesize(results)

        assert synthesis["total_results"] == 1
        assert synthesis["successful"] == 1
        assert synthesis["failed"] == 0
        assert synthesis["avg_confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_synthesize_multiple_results(self, engine):
        """Test synthesizing multiple results."""
        results = [
            TaskResult(task_id="t1", agent_id="a1", output={}, success=True, confidence=0.8, metrics={"category": "analysis"}),
            TaskResult(task_id="t2", agent_id="a2", output={}, success=True, confidence=0.9, metrics={"category": "analysis"}),
            TaskResult(task_id="t3", agent_id="a3", output={}, success=False, confidence=0.5, metrics={"category": "processing"}),
        ]
        synthesis = await engine.synthesize(results)

        assert synthesis["total_results"] == 3
        assert synthesis["successful"] == 2
        assert synthesis["failed"] == 1
        assert "analysis" in synthesis["categories"]
        assert "processing" in synthesis["categories"]

    @pytest.mark.asyncio
    async def test_detect_conflicts(self, engine):
        """Test conflict detection."""
        results = [
            TaskResult(task_id="t1", agent_id="a1", output="result_a", success=True, confidence=0.9),
            TaskResult(task_id="t1", agent_id="a2", output="result_b", success=True, confidence=0.8),  # Same task, different output
        ]
        synthesis = await engine.synthesize(results)

        assert len(synthesis["conflicts"]) == 1
        assert synthesis["conflicts"][0]["type"] == "contradicting_output"

    def test_register_merge_strategy(self, engine):
        """Test registering merge strategy."""
        def custom_strategy(results):
            return {"merged": True}

        engine.register_merge_strategy("custom", custom_strategy)
        assert "custom" in engine._merge_strategies


# =============================================================================
# TESTS FOR DECISION ENGINE
# =============================================================================

class TestDecisionEngine:
    """Tests for DecisionEngine."""

    @pytest.fixture
    def engine(self):
        """Create a fresh engine for each test."""
        return DecisionEngine()

    @pytest.fixture
    def session(self):
        """Create a test session."""
        return MastermindSession(
            session_id="test_session",
            primary_objective="Test",
            budget_usd=100.0,
            consumed_usd=50.0
        )

    def test_set_threshold(self, engine):
        """Test setting threshold."""
        engine.set_threshold("min_success_rate", 0.90)
        assert engine._thresholds["min_success_rate"] == 0.90

    @pytest.mark.asyncio
    async def test_evaluate_passing(self, engine, session):
        """Test evaluation with passing criteria."""
        synthesis = {
            "total_results": 10,
            "successful": 9,
            "failed": 1,
            "avg_confidence": 0.85,
            "conflicts": []
        }
        passed, issues, recommendations = await engine.evaluate(session, synthesis)

        assert passed is True
        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_evaluate_low_success_rate(self, engine, session):
        """Test evaluation with low success rate."""
        synthesis = {
            "total_results": 10,
            "successful": 5,
            "failed": 5,
            "avg_confidence": 0.9,
            "conflicts": []
        }
        passed, issues, recommendations = await engine.evaluate(session, synthesis)

        assert passed is False
        assert any("successrate" in issue.lower() for issue in issues)
        assert any(r.rec_type == RecommendationType.ESCALATE for r in recommendations)

    @pytest.mark.asyncio
    async def test_evaluate_with_conflicts(self, engine, session):
        """Test evaluation with conflicts."""
        synthesis = {
            "total_results": 5,
            "successful": 5,
            "failed": 0,
            "avg_confidence": 0.9,
            "conflicts": [{"type": "contradicting_output"}]
        }
        passed, issues, recommendations = await engine.evaluate(session, synthesis)

        assert passed is False
        assert any("konflikt" in issue.lower() for issue in issues)

    @pytest.mark.asyncio
    async def test_evaluate_budget_warning(self, engine, session):
        """Test evaluation with high budget usage."""
        session.consumed_usd = 95.0  # 95% of budget

        synthesis = {
            "total_results": 5,
            "successful": 5,
            "failed": 0,
            "avg_confidence": 0.9,
            "conflicts": []
        }
        passed, issues, recommendations = await engine.evaluate(session, synthesis)

        assert passed is False
        assert any("budget" in issue.lower() for issue in issues)
        assert any(r.rec_type == RecommendationType.PAUSE for r in recommendations)

    def test_identify_bottlenecks_stuck_task(self, engine, session):
        """Test identifying stuck tasks."""
        # Create a stuck task
        task = MastermindTask(
            task_id="t1",
            
            title="Stuck task",
            description="This task is stuck"
        )
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now() - timedelta(minutes=10)  # Started 10 mins ago
        session.tasks["t1"] = task

        bottlenecks = engine.identify_bottlenecks(session)

        assert any(b["type"] == "stuck_task" for b in bottlenecks)

    def test_identify_bottlenecks_pending_high_priority(self, engine, session):
        """Test identifying pending high priority tasks."""
        for i in range(6):
            task = MastermindTask(
                task_id=f"t{i}",
                
                title=f"Task {i}",
                description="High priority",
                priority=MastermindPriority.HIGH
            )
            task.status = TaskStatus.PENDING
            session.tasks[f"t{i}"] = task

        bottlenecks = engine.identify_bottlenecks(session)

        assert any(b["type"] == "pending_high_priority" for b in bottlenecks)


# =============================================================================
# TESTS FOR ADJUSTMENT DISPATCHER
# =============================================================================

class TestAdjustmentDispatcher:
    """Tests for AdjustmentDispatcher."""

    @pytest.fixture
    def dispatcher(self):
        """Create a fresh dispatcher for each test."""
        return AdjustmentDispatcher()

    @pytest.fixture
    def session(self):
        """Create a test session."""
        return MastermindSession(
            session_id="test_session",
            primary_objective="Test"
        )

    def test_register_handler(self, dispatcher):
        """Test registering a handler."""
        async def handler(rec, session):
            pass

        dispatcher.register_handler(RecommendationType.ADD_AGENT, handler)
        assert RecommendationType.ADD_AGENT in dispatcher._dispatch_handlers

    @pytest.mark.asyncio
    async def test_dispatch_with_handler(self, dispatcher, session):
        """Test dispatching with registered handler."""
        executed = {"called": False}

        async def handler(rec, session):
            executed["called"] = True

        dispatcher.register_handler(RecommendationType.PAUSE, handler)

        rec = Recommendation(
            rec_id="rec_001",
            session_id="test_session",
            rec_type=RecommendationType.PAUSE,
            priority=3,
            title="Pause",
            description="Pause session",
            rationale="Test",
            impact="Test"
        )

        result = await dispatcher.dispatch(rec, session)

        assert result is True
        assert executed["called"] is True
        assert rec.executed_at is not None

    @pytest.mark.asyncio
    async def test_dispatch_without_handler(self, dispatcher, session):
        """Test dispatching without registered handler."""
        rec = Recommendation(
            rec_id="rec_002",
            session_id="test_session",
            rec_type=RecommendationType.ESCALATE,
            priority=4,
            title="Escalate",
            description="Escalate issue",
            rationale="Test",
            impact="Test"
        )

        result = await dispatcher.dispatch(rec, session)

        assert result is False

    def test_get_dispatch_history(self, dispatcher):
        """Test getting dispatch history."""
        dispatcher._dispatch_history = [
            {"rec_id": "r1", "session_id": "s1"},
            {"rec_id": "r2", "session_id": "s2"},
            {"rec_id": "r3", "session_id": "s1"},
        ]

        history = dispatcher.get_dispatch_history(session_id="s1")
        assert len(history) == 2


# =============================================================================
# TESTS FOR FEEDBACK AGGREGATOR
# =============================================================================

class TestFeedbackAggregator:
    """Tests for FeedbackAggregator."""

    @pytest.fixture
    def aggregator(self):
        """Create a fresh aggregator for each test."""
        return FeedbackAggregator()

    @pytest.fixture
    def session(self):
        """Create a test session."""
        session = MastermindSession(
            session_id="test_session",
            primary_objective="Test",
            budget_usd=100.0
        )
        # Add some tasks
        for i in range(3):
            task = MastermindTask(
                task_id=f"t{i}",
                
                title=f"Task {i}",
                description="Test task"
            )
            task.status = TaskStatus.COMPLETED if i < 2 else TaskStatus.PENDING
            session.tasks[f"t{i}"] = task
        return session

    @pytest.mark.asyncio
    async def test_process_result(self, aggregator, session):
        """Test processing a result."""
        result = TaskResult(
            task_id="t0",
            agent_id="agent_001",
            output={"data": "result"},
            success=True,
            confidence=0.9
        )

        report = await aggregator.process_result(session, result)

        assert report.session_id == "test_session"
        assert report.completed_tasks == 2
        assert report.pending_tasks == 1

    @pytest.mark.asyncio
    async def test_generate_full_report(self, aggregator, session):
        """Test generating full report."""
        # Add some results first
        result = TaskResult(
            task_id="t0",
            agent_id="agent_001",
            output={},
            success=True,
            confidence=0.9
        )
        await aggregator.collector.collect(session.session_id, result)

        report = await aggregator.generate_full_report(session)

        assert report["session_id"] == "test_session"
        assert "synthesis" in report
        assert "evaluation" in report
        assert "bottlenecks" in report

    def test_add_feedback(self, aggregator):
        """Test adding feedback."""
        item = aggregator.add_feedback(
            session_id="s001",
            source="agent_001",
            category="progress",
            message="50% complete",
            severity=FeedbackSeverity.INFO
        )

        assert item.item_id.startswith("fb_")
        assert len(aggregator._feedback_items["s001"]) == 1

    def test_get_feedback(self, aggregator):
        """Test getting feedback."""
        aggregator.add_feedback("s001", "a1", "progress", "msg1", FeedbackSeverity.INFO)
        aggregator.add_feedback("s001", "a2", "alert", "msg2", FeedbackSeverity.WARNING)
        aggregator.add_feedback("s001", "a3", "error", "msg3", FeedbackSeverity.ERROR)

        # All feedback
        all_items = aggregator.get_feedback("s001")
        assert len(all_items) == 3

        # Filtered by severity
        warnings = aggregator.get_feedback("s001", severity=FeedbackSeverity.WARNING)
        assert len(warnings) == 1

    def test_get_alerts(self, aggregator):
        """Test getting alerts."""
        alert1 = Alert(
            alert_id="a1",
            session_id="s001",
            alert_type=AlertType.PERFORMANCE,
            severity=FeedbackSeverity.WARNING,
            title="Alert 1",
            description="Test"
        )
        alert2 = Alert(
            alert_id="a2",
            session_id="s001",
            alert_type=AlertType.QUALITY,
            severity=FeedbackSeverity.ERROR,
            title="Alert 2",
            description="Test",
            resolved_at=datetime.now()
        )
        aggregator._alerts["s001"] = [alert1, alert2]

        # All alerts
        all_alerts = aggregator.get_alerts("s001")
        assert len(all_alerts) == 2

        # Unresolved only
        unresolved = aggregator.get_alerts("s001", unresolved_only=True)
        assert len(unresolved) == 1

    def test_calculate_progress(self, aggregator, session):
        """Test progress calculation."""
        progress = aggregator._calculate_progress(session)

        # 2 completed out of 3 = 66.67%
        assert progress == pytest.approx(66.67, rel=0.01)


# =============================================================================
# TESTS FOR FACTORY FUNCTIONS
# =============================================================================

class TestFeedbackFactoryFunctions:
    """Tests for feedback factory functions."""

    def test_create_feedback_aggregator(self):
        """Test creating feedback aggregator."""
        aggregator = create_feedback_aggregator()

        assert isinstance(aggregator, FeedbackAggregator)
        assert aggregator.collector is not None
        assert aggregator.synthesis_engine is not None
        assert aggregator.decision_engine is not None
        assert aggregator.dispatcher is not None

    def test_get_feedback_aggregator(self):
        """Test getting current aggregator instance."""
        created = create_feedback_aggregator()
        retrieved = get_feedback_aggregator()

        assert retrieved is created


# =============================================================================
# TESTS FOR MODULE IMPORTS
# =============================================================================

class TestFeedbackModuleImports:
    """Tests for feedback module imports."""

    def test_all_exports_importable(self):
        """Test that all expected exports are available."""
        from cirkelline.ckc.mastermind import feedback

        # Enums
        assert hasattr(feedback, 'FeedbackSeverity')
        assert hasattr(feedback, 'AlertType')
        assert hasattr(feedback, 'RecommendationType')

        # Data classes
        assert hasattr(feedback, 'FeedbackItem')
        assert hasattr(feedback, 'Alert')
        assert hasattr(feedback, 'Recommendation')

        # Classes
        assert hasattr(feedback, 'ResultCollector')
        assert hasattr(feedback, 'SynthesisEngine')
        assert hasattr(feedback, 'DecisionEngine')
        assert hasattr(feedback, 'AdjustmentDispatcher')
        assert hasattr(feedback, 'FeedbackAggregator')

        # Factory functions
        assert hasattr(feedback, 'create_feedback_aggregator')
        assert hasattr(feedback, 'get_feedback_aggregator')
