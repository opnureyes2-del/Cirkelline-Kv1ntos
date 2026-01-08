"""
Tests for CommanderTrainingRoom module (DEL K).

Tester Commander Training Room funktionalitet:
- Autonomi-beskyttelse
- Planlagte optimeringstidspunkter (03:33 og 21:21)
- Session management
- Indsigt-generering
- Vidensverifikation
"""

import pytest
from datetime import datetime, time, timezone, timedelta

# =============================================================================
# IMPORT TESTS
# =============================================================================

class TestTrainingRoomImports:
    """Test at alle training room komponenter kan importeres."""

    def test_import_training_room_module(self):
        """Test import af training_room modul."""
        from cirkelline.ckc.mastermind import training_room
        assert training_room is not None

    def test_import_enums(self):
        """Test import af enums."""
        from cirkelline.ckc.mastermind.training_room import (
            TrainingMode,
            AutonomyLevel,
            OptimizationTarget,
            TrainingStatus,
        )
        assert TrainingMode is not None
        assert AutonomyLevel is not None
        assert OptimizationTarget is not None
        assert TrainingStatus is not None

    def test_import_dataclasses(self):
        """Test import af dataclasses."""
        from cirkelline.ckc.mastermind.training_room import (
            TrainingObjective,
            TrainingSession,
            AutonomyGuard,
            OptimizationSchedule,
            SystemInsight,
        )
        assert TrainingObjective is not None
        assert TrainingSession is not None
        assert AutonomyGuard is not None
        assert OptimizationSchedule is not None
        assert SystemInsight is not None

    def test_import_main_class(self):
        """Test import af CommanderTrainingRoom."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom
        assert CommanderTrainingRoom is not None

    def test_import_factory_functions(self):
        """Test import af factory funktioner."""
        from cirkelline.ckc.mastermind.training_room import (
            create_training_room,
            get_training_room,
        )
        assert create_training_room is not None
        assert get_training_room is not None

    def test_import_from_mastermind_init(self):
        """Test import fra mastermind __init__.py."""
        from cirkelline.ckc.mastermind import (
            TrainingMode,
            AutonomyLevel,
            OptimizationTarget,
            TrainingStatus,
            TrainingObjective,
            TrainingSession,
            AutonomyGuard,
            OptimizationSchedule,
            SystemInsight,
            CommanderTrainingRoom,
            create_training_room,
            get_training_room,
        )
        assert all([
            TrainingMode, AutonomyLevel, OptimizationTarget, TrainingStatus,
            TrainingObjective, TrainingSession, AutonomyGuard,
            OptimizationSchedule, SystemInsight, CommanderTrainingRoom,
            create_training_room, get_training_room
        ])


# =============================================================================
# ENUM TESTS
# =============================================================================

class TestTrainingModeEnum:
    """Test TrainingMode enum."""

    def test_training_mode_values(self):
        """Test at alle TrainingMode værdier eksisterer."""
        from cirkelline.ckc.mastermind.training_room import TrainingMode

        assert TrainingMode.MORNING_OPTIMIZATION.value == "morning_optimization"
        assert TrainingMode.EVENING_INTEGRATION.value == "evening_integration"
        assert TrainingMode.ON_DEMAND.value == "on_demand"
        assert TrainingMode.CONTINUOUS.value == "continuous"
        assert TrainingMode.EMERGENCY.value == "emergency"

    def test_training_mode_count(self):
        """Test antal TrainingMode værdier."""
        from cirkelline.ckc.mastermind.training_room import TrainingMode
        assert len(TrainingMode) == 5


class TestAutonomyLevelEnum:
    """Test AutonomyLevel enum."""

    def test_autonomy_level_values(self):
        """Test at alle AutonomyLevel værdier eksisterer."""
        from cirkelline.ckc.mastermind.training_room import AutonomyLevel

        assert AutonomyLevel.FULL.value == "full"
        assert AutonomyLevel.GUIDED.value == "guided"
        assert AutonomyLevel.COLLABORATIVE.value == "collaborative"
        assert AutonomyLevel.SUPERVISED.value == "supervised"
        assert AutonomyLevel.MINIMAL.value == "minimal"

    def test_autonomy_level_count(self):
        """Test antal AutonomyLevel værdier."""
        from cirkelline.ckc.mastermind.training_room import AutonomyLevel
        assert len(AutonomyLevel) == 5


class TestOptimizationTargetEnum:
    """Test OptimizationTarget enum."""

    def test_optimization_target_values(self):
        """Test at alle OptimizationTarget værdier eksisterer."""
        from cirkelline.ckc.mastermind.training_room import OptimizationTarget

        assert OptimizationTarget.KNOWLEDGE_RECALL.value == "knowledge_recall"
        assert OptimizationTarget.AGENT_COORDINATION.value == "agent_coordination"
        assert OptimizationTarget.RESOURCE_EFFICIENCY.value == "resource_efficiency"
        assert OptimizationTarget.RESPONSE_QUALITY.value == "response_quality"
        assert OptimizationTarget.CONTEXT_UNDERSTANDING.value == "context_understanding"
        assert OptimizationTarget.ETHICAL_ALIGNMENT.value == "ethical_alignment"
        assert OptimizationTarget.USER_EXPERIENCE.value == "user_experience"

    def test_optimization_target_count(self):
        """Test antal OptimizationTarget værdier."""
        from cirkelline.ckc.mastermind.training_room import OptimizationTarget
        assert len(OptimizationTarget) == 7


class TestTrainingStatusEnum:
    """Test TrainingStatus enum."""

    def test_training_status_values(self):
        """Test at alle TrainingStatus værdier eksisterer."""
        from cirkelline.ckc.mastermind.training_room import TrainingStatus

        assert TrainingStatus.IDLE.value == "idle"
        assert TrainingStatus.PREPARING.value == "preparing"
        assert TrainingStatus.IN_PROGRESS.value == "in_progress"
        assert TrainingStatus.REFLECTING.value == "reflecting"
        assert TrainingStatus.COMPLETED.value == "completed"
        assert TrainingStatus.FAILED.value == "failed"

    def test_training_status_count(self):
        """Test antal TrainingStatus værdier."""
        from cirkelline.ckc.mastermind.training_room import TrainingStatus
        assert len(TrainingStatus) == 6


# =============================================================================
# DATACLASS TESTS
# =============================================================================

class TestTrainingObjectiveDataclass:
    """Test TrainingObjective dataclass."""

    def test_create_training_objective(self):
        """Test oprettelse af TrainingObjective."""
        from cirkelline.ckc.mastermind.training_room import (
            TrainingObjective,
            OptimizationTarget,
        )

        obj = TrainingObjective(
            objective_id="obj_test_123",
            target=OptimizationTarget.KNOWLEDGE_RECALL,
            description="Test opitmer vidensrekall",
        )

        assert obj.objective_id == "obj_test_123"
        assert obj.target == OptimizationTarget.KNOWLEDGE_RECALL
        assert obj.description == "Test opitmer vidensrekall"
        assert obj.priority == 1
        assert obj.completed is False
        assert obj.completed_at is None

    def test_training_objective_with_metrics(self):
        """Test TrainingObjective med metrics."""
        from cirkelline.ckc.mastermind.training_room import (
            TrainingObjective,
            OptimizationTarget,
        )

        obj = TrainingObjective(
            objective_id="obj_metrics",
            target=OptimizationTarget.RESPONSE_QUALITY,
            description="Test response quality",
            priority=3,
            metrics={"accuracy": 0.95, "latency_ms": 150.5},
        )

        assert obj.priority == 3
        assert obj.metrics["accuracy"] == 0.95
        assert obj.metrics["latency_ms"] == 150.5


class TestTrainingSessionDataclass:
    """Test TrainingSession dataclass."""

    def test_create_training_session(self):
        """Test oprettelse af TrainingSession."""
        from cirkelline.ckc.mastermind.training_room import (
            TrainingSession,
            TrainingMode,
            TrainingStatus,
        )

        session = TrainingSession(
            session_id="session_test_456",
            mode=TrainingMode.ON_DEMAND,
            status=TrainingStatus.PREPARING,
            started_at=datetime.now(timezone.utc),
        )

        assert session.session_id == "session_test_456"
        assert session.mode == TrainingMode.ON_DEMAND
        assert session.status == TrainingStatus.PREPARING
        assert len(session.objectives) == 0
        assert session.completed_at is None


class TestAutonomyGuardDataclass:
    """Test AutonomyGuard dataclass."""

    def test_create_autonomy_guard_default(self):
        """Test oprettelse af AutonomyGuard med defaults."""
        from cirkelline.ckc.mastermind.training_room import (
            AutonomyGuard,
            AutonomyLevel,
        )

        guard = AutonomyGuard()

        assert guard.level == AutonomyLevel.FULL
        assert len(guard.protected_decisions) == 0
        assert len(guard.override_required_for) == 0
        assert guard.last_autonomy_check is None

    def test_autonomy_guard_with_protected_decisions(self):
        """Test AutonomyGuard med beskyttede beslutninger."""
        from cirkelline.ckc.mastermind.training_room import (
            AutonomyGuard,
            AutonomyLevel,
        )

        guard = AutonomyGuard(
            level=AutonomyLevel.SUPERVISED,
            protected_decisions={"budget_allocation", "agent_termination"},
            override_required_for={"data_deletion"},
        )

        assert guard.level == AutonomyLevel.SUPERVISED
        assert "budget_allocation" in guard.protected_decisions
        assert "data_deletion" in guard.override_required_for


class TestOptimizationScheduleDataclass:
    """Test OptimizationSchedule dataclass."""

    def test_create_optimization_schedule_default(self):
        """Test oprettelse af OptimizationSchedule med defaults."""
        from cirkelline.ckc.mastermind.training_room import OptimizationSchedule

        schedule = OptimizationSchedule()

        assert schedule.morning_time == time(3, 33)
        assert schedule.evening_time == time(21, 21)
        assert schedule.enabled is True
        assert schedule.timezone == "Europe/Copenhagen"
        assert schedule.last_morning_run is None
        assert schedule.last_evening_run is None

    def test_optimization_schedule_custom_times(self):
        """Test OptimizationSchedule med custom tider."""
        from cirkelline.ckc.mastermind.training_room import OptimizationSchedule

        schedule = OptimizationSchedule(
            morning_time=time(4, 0),
            evening_time=time(20, 0),
            enabled=False,
        )

        assert schedule.morning_time == time(4, 0)
        assert schedule.evening_time == time(20, 0)
        assert schedule.enabled is False


class TestSystemInsightDataclass:
    """Test SystemInsight dataclass."""

    def test_create_system_insight(self):
        """Test oprettelse af SystemInsight."""
        from cirkelline.ckc.mastermind.training_room import SystemInsight

        insight = SystemInsight(
            insight_id="insight_test_789",
            category="performance",
            content="Latency forbedret med 15% efter cache-optimering",
            discovered_at=datetime.now(timezone.utc),
        )

        assert insight.insight_id == "insight_test_789"
        assert insight.category == "performance"
        assert "Latency forbedret" in insight.content
        assert insight.priority == 1
        assert insight.actionable is False
        assert insight.action_taken is False

    def test_system_insight_actionable(self):
        """Test actionable SystemInsight."""
        from cirkelline.ckc.mastermind.training_room import SystemInsight

        insight = SystemInsight(
            insight_id="insight_action",
            category="resource",
            content="Memory usage nærmer sig 90%",
            discovered_at=datetime.now(timezone.utc),
            priority=3,
            actionable=True,
        )

        assert insight.priority == 3
        assert insight.actionable is True


# =============================================================================
# COMMANDER TRAINING ROOM TESTS
# =============================================================================

class TestCommanderTrainingRoomCreation:
    """Test oprettelse af CommanderTrainingRoom."""

    def test_create_training_room_default(self):
        """Test oprettelse med defaults."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()

        assert room is not None
        status = room.get_status()
        assert status["autonomy"]["level"] == "full"
        assert status["schedule"]["enabled"] is True

    def test_create_training_room_custom_autonomy(self):
        """Test oprettelse med custom autonomi-niveau."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            AutonomyLevel,
        )

        room = CommanderTrainingRoom(autonomy_level=AutonomyLevel.SUPERVISED)

        status = room.get_status()
        assert status["autonomy"]["level"] == "supervised"

    def test_create_training_room_custom_schedule(self):
        """Test oprettelse med custom schedule."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            OptimizationSchedule,
        )

        schedule = OptimizationSchedule(
            morning_time=time(5, 0),
            evening_time=time(22, 0),
            enabled=False,
        )
        room = CommanderTrainingRoom(schedule=schedule)

        status = room.get_status()
        assert status["schedule"]["morning_time"] == "05:00:00"
        assert status["schedule"]["evening_time"] == "22:00:00"
        assert status["schedule"]["enabled"] is False


class TestCommanderTrainingRoomSessions:
    """Test session management i CommanderTrainingRoom."""

    def test_start_session(self):
        """Test start af træningssession."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            TrainingMode,
            TrainingStatus,
        )

        room = CommanderTrainingRoom()
        session = room.start_session(mode=TrainingMode.ON_DEMAND)

        assert session is not None
        assert session.mode == TrainingMode.ON_DEMAND
        assert session.status == TrainingStatus.PREPARING
        assert session.session_id.startswith("train_")

    def test_start_session_with_objectives(self):
        """Test start af session med objectives."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            TrainingMode,
            OptimizationTarget,
        )

        room = CommanderTrainingRoom()
        session = room.start_session(
            mode=TrainingMode.MORNING_OPTIMIZATION,
            objectives=[
                OptimizationTarget.KNOWLEDGE_RECALL,
                OptimizationTarget.RESOURCE_EFFICIENCY,
            ]
        )

        assert len(session.objectives) == 2
        assert session.objectives[0].target == OptimizationTarget.KNOWLEDGE_RECALL
        assert session.objectives[1].target == OptimizationTarget.RESOURCE_EFFICIENCY

    def test_get_current_session(self):
        """Test hentning af aktuel session."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            TrainingMode,
        )

        room = CommanderTrainingRoom()

        # Ingen session først
        assert room.get_current_session() is None

        # Start session
        session = room.start_session(mode=TrainingMode.CONTINUOUS)
        current = room.get_current_session()

        assert current is not None
        assert current.session_id == session.session_id

    def test_complete_session(self):
        """Test afslutning af session."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            TrainingMode,
            TrainingStatus,
        )

        room = CommanderTrainingRoom()
        session = room.start_session(mode=TrainingMode.ON_DEMAND)
        session_id = session.session_id

        completed = room.complete_session(session_id)

        assert completed.status == TrainingStatus.COMPLETED
        assert completed.completed_at is not None
        assert completed.duration_seconds >= 0
        assert room.get_current_session() is None

    def test_complete_nonexistent_session_raises(self):
        """Test at afslutning af ikke-eksisterende session giver fejl."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()

        with pytest.raises(ValueError, match="Session ikke fundet"):
            room.complete_session("nonexistent_session_123")


# =============================================================================
# AUTONOMY PROTECTION TESTS
# =============================================================================

class TestAutonomyProtection:
    """Test autonomi-beskyttelse funktionalitet."""

    def test_check_autonomy(self):
        """Test autonomi-check."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        guard = room.check_autonomy()

        assert guard is not None
        assert guard.last_autonomy_check is not None

    def test_protect_decision(self):
        """Test beskyttelse af beslutning."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        room.protect_decision("agent_creation")

        status = room.get_status()
        assert "agent_creation" in status["autonomy"]["protected_decisions"]

    def test_require_override(self):
        """Test markering af beslutning der kræver override."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        room.require_override("system_shutdown")

        # Test at beslutning ikke er tilladt
        assert not room.is_autonomous_decision_allowed("system_shutdown")

    def test_is_autonomous_decision_allowed_full_autonomy(self):
        """Test autonome beslutninger med fuld autonomi."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            AutonomyLevel,
        )

        room = CommanderTrainingRoom(autonomy_level=AutonomyLevel.FULL)

        assert room.is_autonomous_decision_allowed("budget_allocation")
        assert room.is_autonomous_decision_allowed("agent_creation")

    def test_is_autonomous_decision_allowed_minimal_autonomy(self):
        """Test autonome beslutninger med minimal autonomi."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            AutonomyLevel,
        )

        room = CommanderTrainingRoom(autonomy_level=AutonomyLevel.MINIMAL)

        assert not room.is_autonomous_decision_allowed("budget_allocation")
        assert not room.is_autonomous_decision_allowed("agent_creation")

    def test_is_autonomous_decision_allowed_supervised(self):
        """Test autonome beslutninger med supervised autonomi."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            AutonomyLevel,
        )

        room = CommanderTrainingRoom(autonomy_level=AutonomyLevel.SUPERVISED)
        room.protect_decision("low_risk_task")

        # Beskyttede beslutninger er tilladt
        assert room.is_autonomous_decision_allowed("low_risk_task")
        # Ikke-beskyttede beslutninger er ikke tilladt
        assert not room.is_autonomous_decision_allowed("high_risk_task")


# =============================================================================
# SCHEDULED OPTIMIZATION TESTS
# =============================================================================

class TestScheduledOptimization:
    """Test planlagt optimering (03:33 og 21:21)."""

    def test_should_run_morning_optimization_disabled(self):
        """Test at morgen-optimering ikke kører når disabled."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            OptimizationSchedule,
        )

        schedule = OptimizationSchedule(enabled=False)
        room = CommanderTrainingRoom(schedule=schedule)

        assert not room.should_run_morning_optimization()

    def test_should_run_evening_integration_disabled(self):
        """Test at aften-integration ikke kører når disabled."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            OptimizationSchedule,
        )

        schedule = OptimizationSchedule(enabled=False)
        room = CommanderTrainingRoom(schedule=schedule)

        assert not room.should_run_evening_integration()

    def test_run_scheduled_optimization_returns_none_when_not_time(self):
        """Test at scheduled optimization returnerer None når det ikke er tid."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        # Ved normal tid burde det returnere None
        result = room.run_scheduled_optimization()

        # Kan returnere session eller None afhængigt af aktuel tid
        # Vi tester bare at det ikke kaster en exception
        assert result is None or result.session_id is not None


# =============================================================================
# INSIGHT GENERATION TESTS
# =============================================================================

class TestInsightGeneration:
    """Test indsigt-generering."""

    def test_add_insight(self):
        """Test tilføjelse af indsigt."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        insight = room.add_insight(
            category="performance",
            content="Response time forbedret med 20%",
        )

        assert insight.insight_id.startswith("insight_")
        assert insight.category == "performance"
        assert "Response time" in insight.content

    def test_add_actionable_insight(self):
        """Test tilføjelse af actionable indsigt."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        insight = room.add_insight(
            category="resource",
            content="Disk space lav - overvej cleanup",
            actionable=True,
            priority=5,
        )

        assert insight.actionable is True
        assert insight.priority == 5

    def test_get_insights(self):
        """Test hentning af indsigter."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        room.add_insight(category="perf", content="Test 1")
        room.add_insight(category="resource", content="Test 2")
        room.add_insight(category="perf", content="Test 3")

        all_insights = room.get_insights()
        assert len(all_insights) == 3

        perf_insights = room.get_insights(category="perf")
        assert len(perf_insights) == 2

    def test_get_actionable_insights(self):
        """Test hentning af kun actionable indsigter."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        room.add_insight(category="info", content="Informativ", actionable=False)
        room.add_insight(category="action", content="Handling påkrævet", actionable=True)
        room.add_insight(category="action2", content="Også handling", actionable=True)

        actionable = room.get_insights(actionable_only=True)
        assert len(actionable) == 2


# =============================================================================
# KNOWLEDGE VERIFICATION TESTS
# =============================================================================

class TestKnowledgeVerification:
    """Test vidensverifikation."""

    def test_verify_knowledge_integrity(self):
        """Test verifikation af vidensintegritet."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        results = room.verify_knowledge_integrity()

        assert results["status"] == "verified"
        assert results["checks"]["modules_imported"] is True
        assert results["checks"]["configuration_consistent"] is True
        assert results["checks"]["test_coverage_sufficient"] is True
        assert "timestamp" in results

    def test_verify_context_recall(self):
        """Test verifikation af kontekst-genkaldelse."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        test_context = {
            "user_id": "test_user",
            "session_history": ["msg1", "msg2"],
        }

        results = room.verify_context_recall(test_context)

        assert results["status"] == "verified"
        assert results["recall_score"] == 1.0
        assert results["passed"] is True


# =============================================================================
# OPTIMIZATION CYCLE TESTS
# =============================================================================

class TestOptimizationCycle:
    """Test optimeringscyklus."""

    def test_register_optimization_callback(self):
        """Test registrering af callback."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        callback_executed = []

        def my_callback():
            callback_executed.append(True)

        room.register_optimization_callback(my_callback)
        assert len(room._optimization_callbacks) == 1

    @pytest.mark.asyncio
    async def test_run_optimization_cycle(self):
        """Test kørsel af optimeringscyklus."""
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        room = CommanderTrainingRoom()
        callback_count = []

        def sync_callback():
            callback_count.append("sync")

        async def async_callback():
            callback_count.append("async")

        room.register_optimization_callback(sync_callback)
        room.register_optimization_callback(async_callback)

        results = await room.run_optimization_cycle()

        assert results["success"] is True
        assert results["callbacks_executed"] == 2
        assert "cycle_id" in results
        assert len(callback_count) == 2


# =============================================================================
# STATUS & REPORTING TESTS
# =============================================================================

class TestStatusReporting:
    """Test status og rapportering."""

    def test_get_status(self):
        """Test hentning af komplet status."""
        from cirkelline.ckc.mastermind.training_room import (
            CommanderTrainingRoom,
            TrainingMode,
        )

        room = CommanderTrainingRoom()
        room.start_session(mode=TrainingMode.ON_DEMAND)
        room.add_insight(category="test", content="Test insight")

        status = room.get_status()

        assert "autonomy" in status
        assert "schedule" in status
        assert "sessions" in status
        assert "insights" in status

        assert status["sessions"]["total"] == 1
        assert status["sessions"]["current"] is not None
        assert status["insights"]["total"] == 1


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestFactoryFunctions:
    """Test factory funktioner."""

    def test_create_training_room(self):
        """Test create_training_room factory."""
        from cirkelline.ckc.mastermind.training_room import (
            create_training_room,
            AutonomyLevel,
        )

        room = create_training_room(autonomy_level=AutonomyLevel.GUIDED)

        assert room is not None
        status = room.get_status()
        assert status["autonomy"]["level"] == "guided"

    def test_get_training_room_singleton(self):
        """Test get_training_room returnerer singleton."""
        from cirkelline.ckc.mastermind.training_room import get_training_room

        room1 = get_training_room()
        room2 = get_training_room()

        # Begge referencer peger på samme instans
        assert room1 is room2

    def test_create_training_room_replaces_singleton(self):
        """Test at create_training_room erstatter singleton."""
        from cirkelline.ckc.mastermind.training_room import (
            create_training_room,
            get_training_room,
            AutonomyLevel,
        )

        # Opret ny instans
        new_room = create_training_room(autonomy_level=AutonomyLevel.MINIMAL)

        # get_training_room skal returnere den nye
        retrieved = get_training_room()

        assert retrieved is new_room
        status = retrieved.get_status()
        assert status["autonomy"]["level"] == "minimal"
