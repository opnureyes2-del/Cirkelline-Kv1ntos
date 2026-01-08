"""
RITUAL SCHEDULER - DEL S
=========================

Planlægger og aktiverer daglige ritualer baseret på RitualExecutor.

Denne modul:
- Scheduler daglige start/slut ritualer
- Integrerer med system lifecycle
- Sikrer ritualer kører på rette tidspunkter
- Logger alle ritual-eksekveringer via KV1NT

Følger CoreWisdom princippet NATURAL_RHYTHM:
"Rutiner og ritualer skaber flow, ikke begrænsning."
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ScheduleType(Enum):
    """Type af planlagt ritual."""
    DAILY = "daily"
    WEEKLY = "weekly"
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"
    INTERVAL = "interval"
    CRON = "cron"


class SchedulerState(Enum):
    """Tilstand for scheduler."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"


class ScheduleStatus(Enum):
    """Status for en planlagt opgave."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ScheduleConfig:
    """Konfiguration for en planlagt opgave."""
    schedule_type: ScheduleType
    time_of_day: Optional[time] = None  # For DAILY
    days_of_week: List[int] = field(default_factory=list)  # For WEEKLY (0=mandag)
    interval_seconds: Optional[int] = None  # For INTERVAL
    cron_expression: Optional[str] = None  # For CRON
    enabled: bool = True
    priority: int = 5  # 1-10, højere = vigtigere
    retry_on_failure: bool = True
    max_retries: int = 3


@dataclass
class ScheduledRitual:
    """En planlagt ritual."""
    id: str
    name: str
    ritual_id: str
    config: ScheduleConfig
    callback: Optional[Callable] = None
    last_executed: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_count: int = 0
    failure_count: int = 0
    status: ScheduleStatus = ScheduleStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionRecord:
    """Record af en ritual-eksekvering."""
    id: str
    scheduled_ritual_id: str
    ritual_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: ScheduleStatus = ScheduleStatus.EXECUTING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


@dataclass
class SchedulerStats:
    """Statistik for scheduler."""
    total_scheduled: int = 0
    total_executed: int = 0
    total_successful: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    uptime_seconds: float = 0.0
    last_execution: Optional[datetime] = None
    next_scheduled: Optional[datetime] = None


# =============================================================================
# RITUAL SCHEDULER
# =============================================================================

class RitualScheduler:
    """
    Planlægger og eksekverer ritualer baseret på tidsplan.

    Eksempel:
        scheduler = RitualScheduler()

        # Tilføj daglig morgenrutine
        scheduler.schedule_daily(
            name="morgen_opstart",
            ritual_id="startup_ritual",
            time_of_day=time(8, 0),  # 08:00
        )

        # Start scheduler
        await scheduler.start()
    """

    def __init__(
        self,
        ritual_executor: Optional[Any] = None,
        auto_start: bool = False,
    ):
        self._id = str(uuid4())[:8]
        self._state = SchedulerState.IDLE
        self._ritual_executor = ritual_executor
        self._scheduled_rituals: Dict[str, ScheduledRitual] = {}
        self._execution_history: List[ExecutionRecord] = []
        self._stats = SchedulerStats()
        self._started_at: Optional[datetime] = None
        self._task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        if auto_start:
            asyncio.create_task(self.start())

        logger.info(f"RitualScheduler initialiseret (id={self._id})")

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def state(self) -> SchedulerState:
        """Nuværende tilstand."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Er scheduler i gang."""
        return self._state == SchedulerState.RUNNING

    @property
    def scheduled_count(self) -> int:
        """Antal planlagte ritualer."""
        return len(self._scheduled_rituals)

    @property
    def stats(self) -> SchedulerStats:
        """Scheduler statistik."""
        if self._started_at:
            self._stats.uptime_seconds = (
                datetime.now() - self._started_at
            ).total_seconds()
        return self._stats

    # =========================================================================
    # SCHEDULING METODER
    # =========================================================================

    def schedule_daily(
        self,
        name: str,
        ritual_id: str,
        time_of_day: time,
        callback: Optional[Callable] = None,
        enabled: bool = True,
        priority: int = 5,
    ) -> ScheduledRitual:
        """
        Planlæg et dagligt ritual.

        Args:
            name: Navn på det planlagte ritual
            ritual_id: ID på ritual fra RitualExecutor
            time_of_day: Tidspunkt for eksekvering
            callback: Optional callback efter eksekvering
            enabled: Om ritual er aktivt
            priority: Prioritet (1-10)

        Returns:
            Den planlagte ritual
        """
        config = ScheduleConfig(
            schedule_type=ScheduleType.DAILY,
            time_of_day=time_of_day,
            enabled=enabled,
            priority=priority,
        )

        return self._add_scheduled_ritual(name, ritual_id, config, callback)

    def schedule_on_startup(
        self,
        name: str,
        ritual_id: str,
        callback: Optional[Callable] = None,
        priority: int = 10,
    ) -> ScheduledRitual:
        """
        Planlæg et ritual der kører ved opstart.

        Args:
            name: Navn på det planlagte ritual
            ritual_id: ID på ritual
            callback: Optional callback
            priority: Prioritet (default 10 for startup)

        Returns:
            Den planlagte ritual
        """
        config = ScheduleConfig(
            schedule_type=ScheduleType.ON_STARTUP,
            enabled=True,
            priority=priority,
        )

        return self._add_scheduled_ritual(name, ritual_id, config, callback)

    def schedule_on_shutdown(
        self,
        name: str,
        ritual_id: str,
        callback: Optional[Callable] = None,
        priority: int = 10,
    ) -> ScheduledRitual:
        """
        Planlæg et ritual der kører ved nedlukning.

        Args:
            name: Navn på det planlagte ritual
            ritual_id: ID på ritual
            callback: Optional callback
            priority: Prioritet (default 10 for shutdown)

        Returns:
            Den planlagte ritual
        """
        config = ScheduleConfig(
            schedule_type=ScheduleType.ON_SHUTDOWN,
            enabled=True,
            priority=priority,
        )

        return self._add_scheduled_ritual(name, ritual_id, config, callback)

    def schedule_interval(
        self,
        name: str,
        ritual_id: str,
        interval_seconds: int,
        callback: Optional[Callable] = None,
        enabled: bool = True,
    ) -> ScheduledRitual:
        """
        Planlæg et ritual der kører med fast interval.

        Args:
            name: Navn på det planlagte ritual
            ritual_id: ID på ritual
            interval_seconds: Sekunder mellem eksekveringer
            callback: Optional callback
            enabled: Om ritual er aktivt

        Returns:
            Den planlagte ritual
        """
        config = ScheduleConfig(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=interval_seconds,
            enabled=enabled,
        )

        return self._add_scheduled_ritual(name, ritual_id, config, callback)

    def _add_scheduled_ritual(
        self,
        name: str,
        ritual_id: str,
        config: ScheduleConfig,
        callback: Optional[Callable] = None,
    ) -> ScheduledRitual:
        """Tilføj et planlagt ritual internt."""
        scheduled_id = f"sched_{str(uuid4())[:8]}"

        scheduled = ScheduledRitual(
            id=scheduled_id,
            name=name,
            ritual_id=ritual_id,
            config=config,
            callback=callback,
            status=ScheduleStatus.SCHEDULED,
        )

        # Beregn næste eksekvering
        scheduled.next_execution = self._calculate_next_execution(scheduled)

        self._scheduled_rituals[scheduled_id] = scheduled
        self._stats.total_scheduled += 1

        logger.info(
            f"Ritual planlagt: {name} ({config.schedule_type.value}) "
            f"-> næste: {scheduled.next_execution}"
        )

        return scheduled

    def _calculate_next_execution(
        self,
        scheduled: ScheduledRitual,
    ) -> Optional[datetime]:
        """Beregn næste eksekveringstidspunkt."""
        now = datetime.now()
        config = scheduled.config

        if config.schedule_type == ScheduleType.DAILY:
            if config.time_of_day:
                next_time = datetime.combine(now.date(), config.time_of_day)
                if next_time <= now:
                    next_time += timedelta(days=1)
                return next_time

        elif config.schedule_type == ScheduleType.INTERVAL:
            if config.interval_seconds:
                return now + timedelta(seconds=config.interval_seconds)

        elif config.schedule_type == ScheduleType.ON_STARTUP:
            return now  # Kører straks ved start

        elif config.schedule_type == ScheduleType.ON_SHUTDOWN:
            return None  # Kører ved shutdown

        return None

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def start(self) -> None:
        """Start scheduler."""
        if self._state == SchedulerState.RUNNING:
            logger.warning("Scheduler kører allerede")
            return

        self._state = SchedulerState.RUNNING
        self._started_at = datetime.now()
        self._shutdown_event.clear()

        logger.info("RitualScheduler starter...")

        # Kør startup ritualer
        await self._execute_startup_rituals()

        # Start scheduler loop
        self._task = asyncio.create_task(self._scheduler_loop())

        logger.info("RitualScheduler kører")

    async def stop(self) -> None:
        """Stop scheduler."""
        if self._state != SchedulerState.RUNNING:
            return

        self._state = SchedulerState.STOPPING
        logger.info("RitualScheduler stopper...")

        # Kør shutdown ritualer
        await self._execute_shutdown_rituals()

        # Signal shutdown
        self._shutdown_event.set()

        # Vent på task
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()

        self._state = SchedulerState.STOPPED
        logger.info("RitualScheduler stoppet")

    async def pause(self) -> None:
        """Pause scheduler midlertidigt."""
        if self._state == SchedulerState.RUNNING:
            self._state = SchedulerState.PAUSED
            logger.info("RitualScheduler sat på pause")

    async def resume(self) -> None:
        """Genoptag scheduler."""
        if self._state == SchedulerState.PAUSED:
            self._state = SchedulerState.RUNNING
            logger.info("RitualScheduler genoptaget")

    # =========================================================================
    # EXECUTION
    # =========================================================================

    async def _scheduler_loop(self) -> None:
        """Hovedloop for scheduler."""
        while not self._shutdown_event.is_set():
            if self._state == SchedulerState.RUNNING:
                await self._check_and_execute_rituals()

            # Vent 1 sekund mellem checks
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=1.0,
                )
                break
            except asyncio.TimeoutError:
                continue

    async def _check_and_execute_rituals(self) -> None:
        """Check og eksekver rituals der skal køre."""
        now = datetime.now()

        for scheduled in list(self._scheduled_rituals.values()):
            if not scheduled.config.enabled:
                continue

            if scheduled.config.schedule_type == ScheduleType.ON_SHUTDOWN:
                continue  # Håndteres separat

            if scheduled.next_execution and scheduled.next_execution <= now:
                await self._execute_ritual(scheduled)

    async def _execute_startup_rituals(self) -> None:
        """Eksekver alle startup ritualer."""
        startup_rituals = [
            s for s in self._scheduled_rituals.values()
            if s.config.schedule_type == ScheduleType.ON_STARTUP
            and s.config.enabled
        ]

        # Sortér efter prioritet (højest først)
        startup_rituals.sort(key=lambda x: x.config.priority, reverse=True)

        for scheduled in startup_rituals:
            await self._execute_ritual(scheduled)

    async def _execute_shutdown_rituals(self) -> None:
        """Eksekver alle shutdown ritualer."""
        shutdown_rituals = [
            s for s in self._scheduled_rituals.values()
            if s.config.schedule_type == ScheduleType.ON_SHUTDOWN
            and s.config.enabled
        ]

        # Sortér efter prioritet (højest først)
        shutdown_rituals.sort(key=lambda x: x.config.priority, reverse=True)

        for scheduled in shutdown_rituals:
            await self._execute_ritual(scheduled)

    async def _execute_ritual(self, scheduled: ScheduledRitual) -> None:
        """Eksekver et enkelt ritual."""
        record = ExecutionRecord(
            id=f"exec_{str(uuid4())[:8]}",
            scheduled_ritual_id=scheduled.id,
            ritual_id=scheduled.ritual_id,
            started_at=datetime.now(),
        )

        scheduled.status = ScheduleStatus.EXECUTING

        try:
            # Eksekver via RitualExecutor hvis tilgængelig
            if self._ritual_executor:
                result = await self._ritual_executor.execute(scheduled.ritual_id)
                record.result = result
            else:
                # Simuler eksekvering
                await asyncio.sleep(0.1)
                record.result = {"simulated": True}

            # Kør callback hvis defineret
            if scheduled.callback:
                if asyncio.iscoroutinefunction(scheduled.callback):
                    await scheduled.callback(scheduled, record.result)
                else:
                    scheduled.callback(scheduled, record.result)

            record.status = ScheduleStatus.COMPLETED
            scheduled.status = ScheduleStatus.COMPLETED
            self._stats.total_successful += 1

            logger.info(f"Ritual udført: {scheduled.name}")

        except Exception as e:
            record.status = ScheduleStatus.FAILED
            record.error = str(e)
            scheduled.status = ScheduleStatus.FAILED
            scheduled.failure_count += 1
            self._stats.total_failed += 1

            logger.error(f"Ritual fejlede: {scheduled.name} - {e}")

        finally:
            record.completed_at = datetime.now()
            record.duration_ms = int(
                (record.completed_at - record.started_at).total_seconds() * 1000
            )

            scheduled.last_executed = record.completed_at
            scheduled.execution_count += 1
            scheduled.next_execution = self._calculate_next_execution(scheduled)

            self._execution_history.append(record)
            self._stats.total_executed += 1
            self._stats.last_execution = record.completed_at

            # Opdater næste planlagte
            self._update_next_scheduled()

    def _update_next_scheduled(self) -> None:
        """Opdater stats med næste planlagte eksekvering."""
        next_times = [
            s.next_execution
            for s in self._scheduled_rituals.values()
            if s.next_execution and s.config.enabled
        ]
        self._stats.next_scheduled = min(next_times) if next_times else None

    # =========================================================================
    # QUERIES
    # =========================================================================

    def get_scheduled_ritual(self, scheduled_id: str) -> Optional[ScheduledRitual]:
        """Hent et planlagt ritual efter ID."""
        return self._scheduled_rituals.get(scheduled_id)

    def get_all_scheduled(self) -> List[ScheduledRitual]:
        """Hent alle planlagte ritualer."""
        return list(self._scheduled_rituals.values())

    def get_execution_history(
        self,
        limit: int = 50,
        scheduled_id: Optional[str] = None,
    ) -> List[ExecutionRecord]:
        """Hent eksekveringshistorik."""
        history = self._execution_history

        if scheduled_id:
            history = [
                r for r in history
                if r.scheduled_ritual_id == scheduled_id
            ]

        return history[-limit:]

    def remove_scheduled(self, scheduled_id: str) -> bool:
        """Fjern et planlagt ritual."""
        if scheduled_id in self._scheduled_rituals:
            del self._scheduled_rituals[scheduled_id]
            logger.info(f"Planlagt ritual fjernet: {scheduled_id}")
            return True
        return False

    def enable_scheduled(self, scheduled_id: str) -> bool:
        """Aktiver et planlagt ritual."""
        if scheduled_id in self._scheduled_rituals:
            self._scheduled_rituals[scheduled_id].config.enabled = True
            return True
        return False

    def disable_scheduled(self, scheduled_id: str) -> bool:
        """Deaktiver et planlagt ritual."""
        if scheduled_id in self._scheduled_rituals:
            self._scheduled_rituals[scheduled_id].config.enabled = False
            return True
        return False


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_scheduler_instance: Optional[RitualScheduler] = None


def create_ritual_scheduler(
    ritual_executor: Optional[Any] = None,
    auto_start: bool = False,
) -> RitualScheduler:
    """
    Opret en ny RitualScheduler.

    Args:
        ritual_executor: Optional RitualExecutor instans
        auto_start: Start scheduler automatisk

    Returns:
        Ny RitualScheduler instans
    """
    return RitualScheduler(
        ritual_executor=ritual_executor,
        auto_start=auto_start,
    )


def get_ritual_scheduler() -> Optional[RitualScheduler]:
    """Hent global RitualScheduler instans."""
    return _scheduler_instance


def set_ritual_scheduler(scheduler: RitualScheduler) -> None:
    """Sæt global RitualScheduler instans."""
    global _scheduler_instance
    _scheduler_instance = scheduler


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ScheduleType",
    "SchedulerState",
    "ScheduleStatus",
    # Data classes
    "ScheduleConfig",
    "ScheduledRitual",
    "ExecutionRecord",
    "SchedulerStats",
    # Main class
    "RitualScheduler",
    # Factory functions
    "create_ritual_scheduler",
    "get_ritual_scheduler",
    "set_ritual_scheduler",
]
