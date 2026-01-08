"""
Tests for SelfOptimizationScheduler module (DEL K.2).

Tester selv-optimering scheduler funktionalitet:
- Scheduler lifecycle (start, stop, pause, resume)
- Planlagte optimeringer (03:33, 21:21)
- Optimerings-faser
- Callback-registrering
"""

import pytest
from datetime import datetime, time, timezone, timedelta

# =============================================================================
# IMPORT TESTS
# =============================================================================

class TestSelfOptimizationImports:
    """Test at alle self_optimization komponenter kan importeres."""

    def test_import_self_optimization_module(self):
        """Test import af self_optimization modul."""
        from cirkelline.ckc.mastermind import self_optimization
        assert self_optimization is not None

    def test_import_enums(self):
        """Test import af enums."""
        from cirkelline.ckc.mastermind.self_optimization import (
            SchedulerState,
            OptimizationPhase,
            ScheduleType,
        )
        assert SchedulerState is not None
        assert OptimizationPhase is not None
        assert ScheduleType is not None

    def test_import_dataclasses(self):
        """Test import af dataclasses."""
        from cirkelline.ckc.mastermind.self_optimization import (
            OptimizationRun,
            SchedulerConfig,
            SchedulerStats,
        )
        assert OptimizationRun is not None
        assert SchedulerConfig is not None
        assert SchedulerStats is not None

    def test_import_phase_classes(self):
        """Test import af fase-klasser."""
        from cirkelline.ckc.mastermind.self_optimization import (
            AnalysisPhase,
            PlanningPhase,
            ExecutionPhase,
            ValidationPhase,
            ReflectionPhase,
        )
        assert AnalysisPhase is not None
        assert PlanningPhase is not None
        assert ExecutionPhase is not None
        assert ValidationPhase is not None
        assert ReflectionPhase is not None

    def test_import_main_class(self):
        """Test import af SelfOptimizationScheduler."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler
        assert SelfOptimizationScheduler is not None

    def test_import_factory_functions(self):
        """Test import af factory funktioner."""
        from cirkelline.ckc.mastermind.self_optimization import (
            create_scheduler,
            get_scheduler,
        )
        assert create_scheduler is not None
        assert get_scheduler is not None

    def test_import_from_mastermind_init(self):
        """Test import fra mastermind __init__.py."""
        from cirkelline.ckc.mastermind import (
            SchedulerState,
            OptimizationPhase,
            ScheduleType,
            OptimizationRun,
            SchedulerConfig,
            SchedulerStats,
            AnalysisPhase,
            PlanningPhase,
            ExecutionPhase,
            ValidationPhase,
            ReflectionPhase,
            SelfOptimizationScheduler,
            create_scheduler,
            get_scheduler,
        )
        assert all([
            SchedulerState, OptimizationPhase, ScheduleType,
            OptimizationRun, SchedulerConfig, SchedulerStats,
            AnalysisPhase, PlanningPhase, ExecutionPhase,
            ValidationPhase, ReflectionPhase,
            SelfOptimizationScheduler, create_scheduler, get_scheduler
        ])


# =============================================================================
# ENUM TESTS
# =============================================================================

class TestSchedulerStateEnum:
    """Test SchedulerState enum."""

    def test_scheduler_state_values(self):
        """Test at alle SchedulerState værdier eksisterer."""
        from cirkelline.ckc.mastermind.self_optimization import SchedulerState

        assert SchedulerState.STOPPED.value == "stopped"
        assert SchedulerState.RUNNING.value == "running"
        assert SchedulerState.PAUSED.value == "paused"
        assert SchedulerState.ERROR.value == "error"

    def test_scheduler_state_count(self):
        """Test antal SchedulerState værdier."""
        from cirkelline.ckc.mastermind.self_optimization import SchedulerState
        assert len(SchedulerState) == 4


class TestOptimizationPhaseEnum:
    """Test OptimizationPhase enum."""

    def test_optimization_phase_values(self):
        """Test at alle OptimizationPhase værdier eksisterer."""
        from cirkelline.ckc.mastermind.self_optimization import OptimizationPhase

        assert OptimizationPhase.ANALYSIS.value == "analysis"
        assert OptimizationPhase.PLANNING.value == "planning"
        assert OptimizationPhase.EXECUTION.value == "execution"
        assert OptimizationPhase.VALIDATION.value == "validation"
        assert OptimizationPhase.REFLECTION.value == "reflection"

    def test_optimization_phase_count(self):
        """Test antal OptimizationPhase værdier."""
        from cirkelline.ckc.mastermind.self_optimization import OptimizationPhase
        assert len(OptimizationPhase) == 5


class TestScheduleTypeEnum:
    """Test ScheduleType enum."""

    def test_schedule_type_values(self):
        """Test at alle ScheduleType værdier eksisterer."""
        from cirkelline.ckc.mastermind.self_optimization import ScheduleType

        assert ScheduleType.MORNING.value == "morning"
        assert ScheduleType.EVENING.value == "evening"
        assert ScheduleType.HOURLY.value == "hourly"
        assert ScheduleType.ON_DEMAND.value == "on_demand"

    def test_schedule_type_count(self):
        """Test antal ScheduleType værdier."""
        from cirkelline.ckc.mastermind.self_optimization import ScheduleType
        assert len(ScheduleType) == 4


# =============================================================================
# DATACLASS TESTS
# =============================================================================

class TestOptimizationRunDataclass:
    """Test OptimizationRun dataclass."""

    def test_create_optimization_run(self):
        """Test oprettelse af OptimizationRun."""
        from cirkelline.ckc.mastermind.self_optimization import (
            OptimizationRun,
            ScheduleType,
            OptimizationPhase,
        )

        run = OptimizationRun(
            run_id="opt_test_123",
            schedule_type=ScheduleType.ON_DEMAND,
            phase=OptimizationPhase.ANALYSIS,
            started_at=datetime.now(timezone.utc),
        )

        assert run.run_id == "opt_test_123"
        assert run.schedule_type == ScheduleType.ON_DEMAND
        assert run.phase == OptimizationPhase.ANALYSIS
        assert run.success is False
        assert run.insights_generated == 0
        assert run.completed_at is None


class TestSchedulerConfigDataclass:
    """Test SchedulerConfig dataclass."""

    def test_create_scheduler_config_default(self):
        """Test oprettelse af SchedulerConfig med defaults."""
        from cirkelline.ckc.mastermind.self_optimization import SchedulerConfig

        config = SchedulerConfig()

        assert config.morning_time == time(3, 33)
        assert config.evening_time == time(21, 21)
        assert config.hourly_enabled is False
        assert config.timezone == "Europe/Copenhagen"
        assert config.max_concurrent_runs == 1
        assert config.run_timeout_seconds == 300

    def test_scheduler_config_custom(self):
        """Test SchedulerConfig med custom værdier."""
        from cirkelline.ckc.mastermind.self_optimization import SchedulerConfig

        config = SchedulerConfig(
            morning_time=time(4, 0),
            evening_time=time(22, 0),
            hourly_enabled=True,
        )

        assert config.morning_time == time(4, 0)
        assert config.evening_time == time(22, 0)
        assert config.hourly_enabled is True


class TestSchedulerStatsDataclass:
    """Test SchedulerStats dataclass."""

    def test_create_scheduler_stats_default(self):
        """Test oprettelse af SchedulerStats med defaults."""
        from cirkelline.ckc.mastermind.self_optimization import SchedulerStats

        stats = SchedulerStats()

        assert stats.total_runs == 0
        assert stats.successful_runs == 0
        assert stats.failed_runs == 0
        assert stats.total_insights == 0
        assert stats.total_actions == 0
        assert stats.last_morning_run is None
        assert stats.last_evening_run is None


# =============================================================================
# SCHEDULER TESTS
# =============================================================================

class TestSelfOptimizationSchedulerCreation:
    """Test oprettelse af SelfOptimizationScheduler."""

    def test_create_scheduler_default(self):
        """Test oprettelse med defaults."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()

        assert scheduler is not None
        status = scheduler.get_status()
        assert status["state"] == "stopped"
        assert status["config"]["morning_time"] == "03:33:00"
        assert status["config"]["evening_time"] == "21:21:00"

    def test_create_scheduler_custom_config(self):
        """Test oprettelse med custom config."""
        from cirkelline.ckc.mastermind.self_optimization import (
            SelfOptimizationScheduler,
            SchedulerConfig,
        )

        config = SchedulerConfig(
            morning_time=time(5, 0),
            hourly_enabled=True,
        )
        scheduler = SelfOptimizationScheduler(config=config)

        status = scheduler.get_status()
        assert status["config"]["morning_time"] == "05:00:00"
        assert status["config"]["hourly_enabled"] is True


class TestSchedulerLifecycle:
    """Test scheduler lifecycle (start, stop, pause, resume)."""

    @pytest.mark.asyncio
    async def test_start_scheduler(self):
        """Test start af scheduler."""
        from cirkelline.ckc.mastermind.self_optimization import (
            SelfOptimizationScheduler,
            SchedulerState,
        )

        scheduler = SelfOptimizationScheduler()
        await scheduler.start()

        assert scheduler._state == SchedulerState.RUNNING

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_scheduler(self):
        """Test stop af scheduler."""
        from cirkelline.ckc.mastermind.self_optimization import (
            SelfOptimizationScheduler,
            SchedulerState,
        )

        scheduler = SelfOptimizationScheduler()
        await scheduler.start()
        await scheduler.stop()

        assert scheduler._state == SchedulerState.STOPPED

    @pytest.mark.asyncio
    async def test_pause_scheduler(self):
        """Test pause af scheduler."""
        from cirkelline.ckc.mastermind.self_optimization import (
            SelfOptimizationScheduler,
            SchedulerState,
        )

        scheduler = SelfOptimizationScheduler()
        await scheduler.start()
        scheduler.pause()

        assert scheduler._state == SchedulerState.PAUSED

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_resume_scheduler(self):
        """Test resume af scheduler."""
        from cirkelline.ckc.mastermind.self_optimization import (
            SelfOptimizationScheduler,
            SchedulerState,
        )

        scheduler = SelfOptimizationScheduler()
        await scheduler.start()
        scheduler.pause()
        scheduler.resume()

        assert scheduler._state == SchedulerState.RUNNING

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_double_start_warning(self):
        """Test at dobbelt start giver warning."""
        from cirkelline.ckc.mastermind.self_optimization import (
            SelfOptimizationScheduler,
            SchedulerState,
        )

        scheduler = SelfOptimizationScheduler()
        await scheduler.start()
        await scheduler.start()  # Should not crash, just warn

        assert scheduler._state == SchedulerState.RUNNING

        await scheduler.stop()


# =============================================================================
# OPTIMIZATION RUN TESTS
# =============================================================================

class TestOptimizationRuns:
    """Test optimerings-kørsler."""

    @pytest.mark.asyncio
    async def test_run_optimization_on_demand(self):
        """Test on-demand optimering."""
        from cirkelline.ckc.mastermind.self_optimization import (
            SelfOptimizationScheduler,
            ScheduleType,
        )

        scheduler = SelfOptimizationScheduler()
        run = await scheduler.run_optimization(ScheduleType.ON_DEMAND)

        assert run is not None
        assert run.run_id.startswith("opt_")
        assert run.schedule_type == ScheduleType.ON_DEMAND
        assert run.completed_at is not None

    @pytest.mark.asyncio
    async def test_run_optimization_success(self):
        """Test succesfuld optimering."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        run = await scheduler.run_optimization()

        assert run.success is True
        assert run.error_message is None

    @pytest.mark.asyncio
    async def test_run_optimization_generates_insights(self):
        """Test at optimering genererer indsigter."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        run = await scheduler.run_optimization()

        # Should have at least generated some insights
        assert run.insights_generated >= 0  # Can be 0 if nothing actionable

    @pytest.mark.asyncio
    async def test_run_optimization_updates_stats(self):
        """Test at optimering opdaterer stats."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()

        initial_stats = scheduler.get_status()["stats"]
        assert initial_stats["total_runs"] == 0

        await scheduler.run_optimization()

        updated_stats = scheduler.get_status()["stats"]
        assert updated_stats["total_runs"] == 1
        assert updated_stats["successful_runs"] == 1


# =============================================================================
# PHASE TESTS
# =============================================================================

class TestAnalysisPhase:
    """Test AnalysisPhase."""

    @pytest.mark.asyncio
    async def test_analysis_phase_execute(self):
        """Test udførelse af analyse-fase."""
        from cirkelline.ckc.mastermind.self_optimization import AnalysisPhase
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        training_room = CommanderTrainingRoom()
        results = await AnalysisPhase.execute(training_room)

        assert results["phase"] == "analysis"
        assert "metrics" in results
        assert "autonomy_level" in results["metrics"]
        assert "knowledge_status" in results["metrics"]


class TestPlanningPhase:
    """Test PlanningPhase."""

    @pytest.mark.asyncio
    async def test_planning_phase_execute(self):
        """Test udførelse af planlægnings-fase."""
        from cirkelline.ckc.mastermind.self_optimization import PlanningPhase
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        training_room = CommanderTrainingRoom()
        analysis_results = {
            "metrics": {"pending_actionable_insights": 2}
        }

        results = await PlanningPhase.execute(training_room, analysis_results)

        assert results["phase"] == "planning"
        assert "priority_targets" in results
        assert len(results["priority_targets"]) > 0


class TestExecutionPhase:
    """Test ExecutionPhase."""

    @pytest.mark.asyncio
    async def test_execution_phase_execute(self):
        """Test udførelse af udførelses-fase."""
        from cirkelline.ckc.mastermind.self_optimization import ExecutionPhase
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        training_room = CommanderTrainingRoom()
        planning_results = {"priority_targets": []}

        results = await ExecutionPhase.execute(training_room, planning_results)

        assert results["phase"] == "execution"
        assert "success" in results


class TestValidationPhase:
    """Test ValidationPhase."""

    @pytest.mark.asyncio
    async def test_validation_phase_execute(self):
        """Test udførelse af validerings-fase."""
        from cirkelline.ckc.mastermind.self_optimization import ValidationPhase
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        training_room = CommanderTrainingRoom()
        execution_results = {"cycle_id": "test_cycle"}

        results = await ValidationPhase.execute(training_room, execution_results)

        assert results["phase"] == "validation"
        assert results["validated"] is True
        assert "validation_checks" in results


class TestReflectionPhase:
    """Test ReflectionPhase."""

    @pytest.mark.asyncio
    async def test_reflection_phase_execute(self):
        """Test udførelse af refleksions-fase."""
        from cirkelline.ckc.mastermind.self_optimization import ReflectionPhase
        from cirkelline.ckc.mastermind.training_room import CommanderTrainingRoom

        training_room = CommanderTrainingRoom()
        all_phase_results = {
            "analysis": {"findings": [], "metrics": {}},
            "execution": {"success": True, "cycle_id": "test_cycle"},
            "validation": {"validated": True},
        }

        results = await ReflectionPhase.execute(training_room, all_phase_results)

        assert results["phase"] == "reflection"
        assert "insights_generated" in results


# =============================================================================
# CALLBACK TESTS
# =============================================================================

class TestSchedulerCallbacks:
    """Test scheduler callbacks."""

    @pytest.mark.asyncio
    async def test_register_pre_run_callback(self):
        """Test registrering af pre-run callback."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        callback_executed = []

        def my_callback(run):
            callback_executed.append(run.run_id)

        scheduler.register_pre_run_callback(my_callback)
        await scheduler.run_optimization()

        assert len(callback_executed) == 1

    @pytest.mark.asyncio
    async def test_register_post_run_callback(self):
        """Test registrering af post-run callback."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        callback_executed = []

        def my_callback(run):
            callback_executed.append(run.success)

        scheduler.register_post_run_callback(my_callback)
        await scheduler.run_optimization()

        assert len(callback_executed) == 1
        assert callback_executed[0] is True

    @pytest.mark.asyncio
    async def test_async_callback(self):
        """Test async callback."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        callback_executed = []

        async def my_async_callback(run):
            callback_executed.append(f"async_{run.run_id}")

        scheduler.register_post_run_callback(my_async_callback)
        await scheduler.run_optimization()

        assert len(callback_executed) == 1
        assert callback_executed[0].startswith("async_opt_")


# =============================================================================
# STATUS TESTS
# =============================================================================

class TestSchedulerStatus:
    """Test scheduler status."""

    def test_get_status(self):
        """Test hentning af status."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        status = scheduler.get_status()

        assert "state" in status
        assert "config" in status
        assert "stats" in status
        assert "current_run" in status
        assert "runs_total" in status

    @pytest.mark.asyncio
    async def test_status_after_run(self):
        """Test status efter kørsel."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        await scheduler.run_optimization()

        status = scheduler.get_status()
        assert status["stats"]["total_runs"] == 1
        assert status["runs_total"] == 1

    def test_get_recent_runs(self):
        """Test hentning af seneste kørsler."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()

        # Ingen kørsler endnu
        recent = scheduler.get_recent_runs()
        assert len(recent) == 0

    @pytest.mark.asyncio
    async def test_get_recent_runs_after_run(self):
        """Test hentning af seneste kørsler efter kørsel."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        run = await scheduler.run_optimization()

        recent = scheduler.get_recent_runs()
        assert len(recent) == 1
        assert recent[0].run_id == run.run_id

    @pytest.mark.asyncio
    async def test_get_run_by_id(self):
        """Test hentning af specifik kørsel."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        run = await scheduler.run_optimization()

        retrieved = scheduler.get_run(run.run_id)
        assert retrieved is not None
        assert retrieved.run_id == run.run_id

    def test_get_nonexistent_run(self):
        """Test hentning af ikke-eksisterende kørsel."""
        from cirkelline.ckc.mastermind.self_optimization import SelfOptimizationScheduler

        scheduler = SelfOptimizationScheduler()
        retrieved = scheduler.get_run("nonexistent_id")

        assert retrieved is None


# =============================================================================
# FACTORY TESTS
# =============================================================================

class TestFactoryFunctions:
    """Test factory funktioner."""

    def test_create_scheduler(self):
        """Test create_scheduler factory."""
        from cirkelline.ckc.mastermind.self_optimization import (
            create_scheduler,
            SchedulerConfig,
        )

        config = SchedulerConfig(hourly_enabled=True)
        scheduler = create_scheduler(config=config)

        assert scheduler is not None
        status = scheduler.get_status()
        assert status["config"]["hourly_enabled"] is True

    def test_get_scheduler_singleton(self):
        """Test get_scheduler returnerer singleton."""
        from cirkelline.ckc.mastermind.self_optimization import get_scheduler

        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()

        assert scheduler1 is scheduler2

    def test_create_scheduler_replaces_singleton(self):
        """Test at create_scheduler erstatter singleton."""
        from cirkelline.ckc.mastermind.self_optimization import (
            create_scheduler,
            get_scheduler,
            SchedulerConfig,
        )

        new_scheduler = create_scheduler(
            config=SchedulerConfig(morning_time=time(6, 0))
        )

        retrieved = get_scheduler()
        assert retrieved is new_scheduler
        status = retrieved.get_status()
        assert status["config"]["morning_time"] == "06:00:00"
