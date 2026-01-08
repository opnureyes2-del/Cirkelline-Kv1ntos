"""
CKC MASTERMIND Self-Optimization Scheduler
===========================================

DEL II.2: Automatisk selv-optimering med planlagte kørsler.

Kernefunktioner:
1. Baggrunds-scheduler der kører på 03:33 og 21:21
2. Integration med CommanderTrainingRoom
3. Automatisk indsigt-generering og handling
4. Autonomi-beskyttelse under optimering

Principper (fra Manifestet):
- "Organisk udvikling af viden"
- "Lav energi som default" - optimeringer køres kun når nødvendigt
- "Urokkelig autonomi-beskyttelse"
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .training_room import (
    CommanderTrainingRoom,
    TrainingMode,
    TrainingSession,
    OptimizationTarget,
    AutonomyLevel,
    get_training_room,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class SchedulerState(Enum):
    """Tilstande for scheduler."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class OptimizationPhase(Enum):
    """Faser i en optimeringscyklus."""
    ANALYSIS = "analysis"           # Analyserer system status
    PLANNING = "planning"           # Planlægger optimering
    EXECUTION = "execution"         # Udfører optimeringer
    VALIDATION = "validation"       # Validerer resultater
    REFLECTION = "reflection"       # Genererer indsigter


class ScheduleType(Enum):
    """Typer af planlagte kørsler."""
    MORNING = "morning"             # 03:33 - stille refleksion
    EVENING = "evening"             # 21:21 - daglig syntese
    HOURLY = "hourly"               # Hver time (let check)
    ON_DEMAND = "on_demand"         # Manuel udløsning


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class OptimizationRun:
    """En enkelt optimeringsrunde."""
    run_id: str
    schedule_type: ScheduleType
    phase: OptimizationPhase
    started_at: datetime
    training_session_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    success: bool = False
    insights_generated: int = 0
    actions_taken: int = 0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerConfig:
    """Konfiguration for scheduler."""
    morning_time: time = time(3, 33)
    evening_time: time = time(21, 21)
    hourly_enabled: bool = False
    timezone: str = "Europe/Copenhagen"
    max_concurrent_runs: int = 1
    run_timeout_seconds: int = 300  # 5 minutter
    retry_on_failure: bool = True
    max_retries: int = 3


@dataclass
class SchedulerStats:
    """Statistik for scheduler."""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    total_insights: int = 0
    total_actions: int = 0
    last_morning_run: Optional[datetime] = None
    last_evening_run: Optional[datetime] = None
    uptime_seconds: float = 0.0


# =============================================================================
# OPTIMIZATION PHASES
# =============================================================================

class AnalysisPhase:
    """Fase 1: Analyse af systemtilstand."""

    @staticmethod
    async def execute(training_room: CommanderTrainingRoom) -> Dict[str, Any]:
        """Kør analyse-fase."""
        results = {
            "phase": OptimizationPhase.ANALYSIS.value,
            "findings": [],
            "metrics": {},
        }

        # Check autonomi-status
        autonomy = training_room.check_autonomy()
        results["metrics"]["autonomy_level"] = autonomy.level.value

        # Verificer vidensintegritet
        knowledge_check = training_room.verify_knowledge_integrity()
        results["metrics"]["knowledge_status"] = knowledge_check["status"]

        # Saml eksisterende indsigter
        actionable_insights = training_room.get_insights(actionable_only=True)
        results["metrics"]["pending_actionable_insights"] = len(actionable_insights)

        if len(actionable_insights) > 0:
            results["findings"].append(
                f"{len(actionable_insights)} actionable insights kræver opmærksomhed"
            )

        logger.debug(f"Analyse-fase afsluttet: {results['metrics']}")
        return results


class PlanningPhase:
    """Fase 2: Planlægning af optimeringer."""

    @staticmethod
    async def execute(
        training_room: CommanderTrainingRoom,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Kør planlægnings-fase."""
        results = {
            "phase": OptimizationPhase.PLANNING.value,
            "planned_optimizations": [],
            "priority_targets": [],
        }

        # Baseret på analyse, planlæg optimeringsmål
        pending_insights = analysis_results["metrics"].get("pending_actionable_insights", 0)

        if pending_insights > 5:
            results["priority_targets"].append(OptimizationTarget.RESOURCE_EFFICIENCY)
            results["planned_optimizations"].append("Prioriter ressource-optimering pga. mange ventende insights")

        # Tilføj standard optimeringsmål
        results["priority_targets"].extend([
            OptimizationTarget.KNOWLEDGE_RECALL,
            OptimizationTarget.CONTEXT_UNDERSTANDING,
        ])

        logger.debug(f"Planlægnings-fase afsluttet: {len(results['priority_targets'])} mål planlagt")
        return results


class ExecutionPhase:
    """Fase 3: Udførelse af optimeringer."""

    @staticmethod
    async def execute(
        training_room: CommanderTrainingRoom,
        planning_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Kør udførelses-fase."""
        results = {
            "phase": OptimizationPhase.EXECUTION.value,
            "optimizations_executed": 0,
            "actions": [],
        }

        # Kør optimeringscyklus
        cycle_results = await training_room.run_optimization_cycle()

        results["optimizations_executed"] = cycle_results.get("callbacks_executed", 0)
        results["cycle_id"] = cycle_results.get("cycle_id")
        results["success"] = cycle_results.get("success", False)

        if results["success"]:
            results["actions"].append("Optimeringscyklus gennemført succesfuldt")

        logger.debug(f"Udførelses-fase afsluttet: {results['optimizations_executed']} optimeringer")
        return results


class ValidationPhase:
    """Fase 4: Validering af resultater."""

    @staticmethod
    async def execute(
        training_room: CommanderTrainingRoom,
        execution_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Kør validerings-fase."""
        results = {
            "phase": OptimizationPhase.VALIDATION.value,
            "validated": True,
            "validation_checks": [],
        }

        # Verificer kontekst-genkaldelse
        context_check = training_room.verify_context_recall({
            "post_optimization": True,
            "execution_cycle": execution_results.get("cycle_id"),
        })

        results["validation_checks"].append({
            "check": "context_recall",
            "passed": context_check.get("passed", False),
            "score": context_check.get("recall_score", 0),
        })

        # Check overordnet status
        status = training_room.get_status()
        results["validation_checks"].append({
            "check": "system_status",
            "passed": True,
            "sessions_total": status["sessions"]["total"],
            "insights_total": status["insights"]["total"],
        })

        logger.debug(f"Validerings-fase afsluttet: {len(results['validation_checks'])} checks")
        return results


class ReflectionPhase:
    """Fase 5: Generering af indsigter."""

    @staticmethod
    async def execute(
        training_room: CommanderTrainingRoom,
        all_phase_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Kør refleksions-fase."""
        results = {
            "phase": OptimizationPhase.REFLECTION.value,
            "insights_generated": 0,
            "insights": [],
        }

        # Generer indsigt baseret på kørslen
        execution = all_phase_results.get("execution", {})
        validation = all_phase_results.get("validation", {})

        if execution.get("success"):
            insight = training_room.add_insight(
                category="optimization",
                content=f"Optimeringscyklus {execution.get('cycle_id', 'unknown')} gennemført succesfuldt",
                actionable=False,
                priority=1,
            )
            results["insights"].append(insight.insight_id)
            results["insights_generated"] += 1

        # Check for actionable findings
        analysis = all_phase_results.get("analysis", {})
        findings = analysis.get("findings", [])

        for finding in findings:
            insight = training_room.add_insight(
                category="analysis",
                content=finding,
                actionable=True,
                priority=2,
            )
            results["insights"].append(insight.insight_id)
            results["insights_generated"] += 1

        logger.debug(f"Refleksions-fase afsluttet: {results['insights_generated']} indsigter genereret")
        return results


# =============================================================================
# SELF OPTIMIZATION SCHEDULER
# =============================================================================

class SelfOptimizationScheduler:
    """
    Scheduler for automatisk selv-optimering.

    Kører planlagte optimeringer på 03:33 og 21:21 samt
    on-demand optimeringer når påkrævet.
    """

    def __init__(
        self,
        training_room: Optional[CommanderTrainingRoom] = None,
        config: Optional[SchedulerConfig] = None,
    ):
        self._training_room = training_room or get_training_room()
        self._config = config or SchedulerConfig()
        self._state = SchedulerState.STOPPED
        self._stats = SchedulerStats()
        self._runs: Dict[str, OptimizationRun] = {}
        self._current_run: Optional[str] = None
        self._task: Optional[asyncio.Task] = None
        self._started_at: Optional[datetime] = None

        # Callbacks for extension
        self._pre_run_callbacks: List[Callable] = []
        self._post_run_callbacks: List[Callable] = []

        logger.info("SelfOptimizationScheduler initialiseret")

    # -------------------------------------------------------------------------
    # LIFECYCLE
    # -------------------------------------------------------------------------

    async def start(self) -> None:
        """Start scheduler."""
        if self._state == SchedulerState.RUNNING:
            logger.warning("Scheduler kører allerede")
            return

        self._state = SchedulerState.RUNNING
        self._started_at = datetime.now(timezone.utc)
        self._task = asyncio.create_task(self._scheduler_loop())

        logger.info("SelfOptimizationScheduler startet")

    async def stop(self) -> None:
        """Stop scheduler."""
        if self._state == SchedulerState.STOPPED:
            return

        self._state = SchedulerState.STOPPED

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._started_at:
            self._stats.uptime_seconds = (
                datetime.now(timezone.utc) - self._started_at
            ).total_seconds()

        logger.info("SelfOptimizationScheduler stoppet")

    def pause(self) -> None:
        """Pause scheduler midlertidigt."""
        if self._state == SchedulerState.RUNNING:
            self._state = SchedulerState.PAUSED
            logger.info("SelfOptimizationScheduler pauset")

    def resume(self) -> None:
        """Genoptag scheduler."""
        if self._state == SchedulerState.PAUSED:
            self._state = SchedulerState.RUNNING
            logger.info("SelfOptimizationScheduler genoptaget")

    # -------------------------------------------------------------------------
    # SCHEDULER LOOP
    # -------------------------------------------------------------------------

    async def _scheduler_loop(self) -> None:
        """Hoved-loop for scheduler."""
        logger.debug("Scheduler loop startet")

        while self._state in (SchedulerState.RUNNING, SchedulerState.PAUSED):
            try:
                if self._state == SchedulerState.PAUSED:
                    await asyncio.sleep(60)
                    continue

                # Check for planlagte kørsler
                schedule_type = self._check_scheduled_time()

                if schedule_type:
                    await self.run_optimization(schedule_type)

                # Vent til næste check (hver minut)
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop fejl: {e}")
                self._state = SchedulerState.ERROR
                await asyncio.sleep(60)
                self._state = SchedulerState.RUNNING

    def _check_scheduled_time(self) -> Optional[ScheduleType]:
        """Check om det er tid til en planlagt kørsel."""
        now = datetime.now(timezone.utc)
        current_time = now.time()

        # Check morgen (03:33)
        if self._is_time_match(current_time, self._config.morning_time):
            if self._can_run_schedule(ScheduleType.MORNING):
                return ScheduleType.MORNING

        # Check aften (21:21)
        if self._is_time_match(current_time, self._config.evening_time):
            if self._can_run_schedule(ScheduleType.EVENING):
                return ScheduleType.EVENING

        # Check hourly hvis enabled
        if self._config.hourly_enabled and current_time.minute == 0:
            if self._can_run_schedule(ScheduleType.HOURLY):
                return ScheduleType.HOURLY

        return None

    def _is_time_match(self, current: time, target: time) -> bool:
        """Check om tiden matcher (inden for 2 minutter)."""
        return (
            current.hour == target.hour and
            abs(current.minute - target.minute) <= 2
        )

    def _can_run_schedule(self, schedule_type: ScheduleType) -> bool:
        """Check om en planlagt kørsel kan udføres."""
        now = datetime.now(timezone.utc)

        if schedule_type == ScheduleType.MORNING:
            if self._stats.last_morning_run:
                # Kun én gang per dag
                return (now - self._stats.last_morning_run).days >= 1
            return True

        elif schedule_type == ScheduleType.EVENING:
            if self._stats.last_evening_run:
                return (now - self._stats.last_evening_run).days >= 1
            return True

        elif schedule_type == ScheduleType.HOURLY:
            # Kan køre hver time
            return True

        return True

    # -------------------------------------------------------------------------
    # OPTIMIZATION EXECUTION
    # -------------------------------------------------------------------------

    async def run_optimization(
        self,
        schedule_type: ScheduleType = ScheduleType.ON_DEMAND
    ) -> OptimizationRun:
        """Kør en komplet optimeringsrunde."""
        run_id = f"opt_{secrets.token_hex(8)}"

        run = OptimizationRun(
            run_id=run_id,
            schedule_type=schedule_type,
            phase=OptimizationPhase.ANALYSIS,
            started_at=datetime.now(timezone.utc),
        )

        self._runs[run_id] = run
        self._current_run = run_id

        logger.info(f"Starter optimeringsrunde: {run_id} ({schedule_type.value})")

        try:
            # Pre-run callbacks
            for callback in self._pre_run_callbacks:
                await self._execute_callback(callback, run)

            # Start træningssession
            mode = self._get_training_mode(schedule_type)
            session = self._training_room.start_session(mode=mode)
            run.training_session_id = session.session_id

            # Kør alle faser
            phase_results = {}

            # Fase 1: Analyse
            run.phase = OptimizationPhase.ANALYSIS
            phase_results["analysis"] = await AnalysisPhase.execute(self._training_room)

            # Fase 2: Planlægning
            run.phase = OptimizationPhase.PLANNING
            phase_results["planning"] = await PlanningPhase.execute(
                self._training_room, phase_results["analysis"]
            )

            # Fase 3: Udførelse
            run.phase = OptimizationPhase.EXECUTION
            phase_results["execution"] = await ExecutionPhase.execute(
                self._training_room, phase_results["planning"]
            )

            # Fase 4: Validering
            run.phase = OptimizationPhase.VALIDATION
            phase_results["validation"] = await ValidationPhase.execute(
                self._training_room, phase_results["execution"]
            )

            # Fase 5: Refleksion
            run.phase = OptimizationPhase.REFLECTION
            phase_results["reflection"] = await ReflectionPhase.execute(
                self._training_room, phase_results
            )

            # Afslut træningssession
            self._training_room.complete_session(session.session_id)

            # Opdater run
            run.success = True
            run.insights_generated = phase_results["reflection"]["insights_generated"]
            run.actions_taken = phase_results["execution"].get("optimizations_executed", 0)
            run.metrics = {
                "analysis": phase_results["analysis"]["metrics"],
                "validation_checks": len(phase_results["validation"]["validation_checks"]),
            }

        except Exception as e:
            logger.error(f"Optimeringsrunde fejlede: {e}")
            run.success = False
            run.error_message = str(e)

        finally:
            run.completed_at = datetime.now(timezone.utc)
            self._current_run = None

            # Opdater stats
            self._update_stats(run)

            # Post-run callbacks
            for callback in self._post_run_callbacks:
                await self._execute_callback(callback, run)

        logger.info(
            f"Optimeringsrunde afsluttet: {run_id} "
            f"(success={run.success}, insights={run.insights_generated})"
        )

        return run

    def _get_training_mode(self, schedule_type: ScheduleType) -> TrainingMode:
        """Konverter schedule type til training mode."""
        mapping = {
            ScheduleType.MORNING: TrainingMode.MORNING_OPTIMIZATION,
            ScheduleType.EVENING: TrainingMode.EVENING_INTEGRATION,
            ScheduleType.HOURLY: TrainingMode.CONTINUOUS,
            ScheduleType.ON_DEMAND: TrainingMode.ON_DEMAND,
        }
        return mapping.get(schedule_type, TrainingMode.ON_DEMAND)

    def _update_stats(self, run: OptimizationRun) -> None:
        """Opdater statistik efter kørsel."""
        self._stats.total_runs += 1

        if run.success:
            self._stats.successful_runs += 1
        else:
            self._stats.failed_runs += 1

        self._stats.total_insights += run.insights_generated
        self._stats.total_actions += run.actions_taken

        now = datetime.now(timezone.utc)
        if run.schedule_type == ScheduleType.MORNING:
            self._stats.last_morning_run = now
        elif run.schedule_type == ScheduleType.EVENING:
            self._stats.last_evening_run = now

    async def _execute_callback(self, callback: Callable, run: OptimizationRun) -> None:
        """Udfør callback sikkert."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(run)
            else:
                callback(run)
        except Exception as e:
            logger.error(f"Callback fejl: {e}")

    # -------------------------------------------------------------------------
    # CALLBACKS
    # -------------------------------------------------------------------------

    def register_pre_run_callback(self, callback: Callable) -> None:
        """Registrer callback før kørsel."""
        self._pre_run_callbacks.append(callback)

    def register_post_run_callback(self, callback: Callable) -> None:
        """Registrer callback efter kørsel."""
        self._post_run_callbacks.append(callback)

    # -------------------------------------------------------------------------
    # STATUS
    # -------------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Hent scheduler status."""
        return {
            "state": self._state.value,
            "config": {
                "morning_time": self._config.morning_time.isoformat(),
                "evening_time": self._config.evening_time.isoformat(),
                "hourly_enabled": self._config.hourly_enabled,
                "timezone": self._config.timezone,
            },
            "stats": {
                "total_runs": self._stats.total_runs,
                "successful_runs": self._stats.successful_runs,
                "failed_runs": self._stats.failed_runs,
                "success_rate": (
                    self._stats.successful_runs / self._stats.total_runs
                    if self._stats.total_runs > 0 else 0.0
                ),
                "total_insights": self._stats.total_insights,
                "total_actions": self._stats.total_actions,
                "last_morning_run": (
                    self._stats.last_morning_run.isoformat()
                    if self._stats.last_morning_run else None
                ),
                "last_evening_run": (
                    self._stats.last_evening_run.isoformat()
                    if self._stats.last_evening_run else None
                ),
                "uptime_seconds": self._stats.uptime_seconds,
            },
            "current_run": self._current_run,
            "runs_total": len(self._runs),
        }

    def get_run(self, run_id: str) -> Optional[OptimizationRun]:
        """Hent en specifik kørsel."""
        return self._runs.get(run_id)

    def get_recent_runs(self, limit: int = 10) -> List[OptimizationRun]:
        """Hent seneste kørsler."""
        runs = sorted(
            self._runs.values(),
            key=lambda r: r.started_at,
            reverse=True
        )
        return runs[:limit]


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_scheduler_instance: Optional[SelfOptimizationScheduler] = None


def create_scheduler(
    training_room: Optional[CommanderTrainingRoom] = None,
    config: Optional[SchedulerConfig] = None,
) -> SelfOptimizationScheduler:
    """Opret en ny SelfOptimizationScheduler."""
    global _scheduler_instance
    _scheduler_instance = SelfOptimizationScheduler(
        training_room=training_room,
        config=config,
    )
    return _scheduler_instance


def get_scheduler() -> SelfOptimizationScheduler:
    """Hent den globale scheduler instans."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SelfOptimizationScheduler()
    return _scheduler_instance


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "SchedulerState",
    "OptimizationPhase",
    "ScheduleType",

    # Data classes
    "OptimizationRun",
    "SchedulerConfig",
    "SchedulerStats",

    # Phase classes
    "AnalysisPhase",
    "PlanningPhase",
    "ExecutionPhase",
    "ValidationPhase",
    "ReflectionPhase",

    # Main class
    "SelfOptimizationScheduler",

    # Factory
    "create_scheduler",
    "get_scheduler",
]
