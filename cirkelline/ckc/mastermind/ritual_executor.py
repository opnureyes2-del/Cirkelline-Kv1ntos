"""
CKC MASTERMIND Ritual Executor (DEL R)
=======================================

Naturlig rutine-afvikling for MASTERMIND Tilstand.

Rutiner og ritualer skaber flow, ikke begrænsning.
Bygger på alle tre foregående komponenter:
- WaveCollector: Samler signaler om hvornår rutiner skal aktiveres
- CollectiveAwareness: Deler viden om rutiner på tværs af fællesskabet
- ThinkAloudStream: Eksekvererer rutiner med transparent reasoning

Princip: "Rutinerne, komplet beskrevet og eksekveret"

Komponenter:
- Ritual: Definition af en rutine/ritual
- RitualStep: Et enkelt trin i en rutine
- RitualExecution: En kørende eksekvering
- RitualExecutor: Hovedklassen for rutine-afvikling
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Union

from .wave_collector import (
    Wave,
    WaveType,
    WaveCollector,
    get_wave_collector
)
from .collective_awareness import (
    CollectiveAwareness,
    get_collective_awareness,
    SharedMemory,
    MemoryType
)
from .think_aloud_stream import (
    ThinkAloudStream,
    get_think_aloud_stream,
    ThoughtType,
    ReasoningStyle
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class RitualType(Enum):
    """Type af ritual/rutine."""
    DAILY = "daily"           # Daglig rutine
    STARTUP = "startup"       # Ved opstart
    SHUTDOWN = "shutdown"     # Ved nedlukning
    TRIGGERED = "triggered"   # Udløst af begivenhed
    PERIODIC = "periodic"     # Periodisk
    RESPONSIVE = "responsive" # Som svar på noget
    COLLABORATIVE = "collaborative"  # Fælles ritual


class RitualState(Enum):
    """Tilstand af et ritual."""
    DORMANT = "dormant"       # Hviler
    PENDING = "pending"       # Venter på start
    EXECUTING = "executing"   # Eksekverer
    PAUSED = "paused"         # Pauseret
    COMPLETED = "completed"   # Afsluttet
    FAILED = "failed"         # Fejlet
    CANCELLED = "cancelled"   # Annulleret


class StepType(Enum):
    """Type af trin i en rutine."""
    ACTION = "action"         # Udfør handling
    CHECK = "check"           # Tjek betingelse
    WAIT = "wait"             # Vent
    THINK = "think"           # Tænk/analyser
    BROADCAST = "broadcast"   # Send til fællesskab
    COLLECT = "collect"       # Saml information
    DECIDE = "decide"         # Tag beslutning
    LOOP = "loop"             # Gentag
    BRANCH = "branch"         # Forgren


class TriggerType(Enum):
    """Type af trigger for ritual."""
    TIME = "time"             # Tidspunkt
    EVENT = "event"           # Begivenhed
    WAVE = "wave"             # Bølge-mønster
    MANUAL = "manual"         # Manuel start
    CONDITION = "condition"   # Betingelse opfyldt
    COMPLETION = "completion" # Andet ritual afsluttet


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RitualStep:
    """Et enkelt trin i en rutine."""
    step_id: str
    step_type: StepType
    name: str
    description: str
    action: Optional[Callable[..., Awaitable[Any]]] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    on_success: Optional[str] = None  # Næste step ID
    on_failure: Optional[str] = None  # Step ID ved fejl
    timeout_seconds: Optional[int] = None
    think_aloud: bool = True  # Skal vi tænke højt under dette trin?

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "on_success": self.on_success,
            "on_failure": self.on_failure,
            "timeout_seconds": self.timeout_seconds,
            "think_aloud": self.think_aloud
        }


@dataclass
class RitualTrigger:
    """Trigger for et ritual."""
    trigger_id: str
    trigger_type: TriggerType
    conditions: Dict[str, Any]
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "trigger_type": self.trigger_type.value,
            "conditions": self.conditions,
            "active": self.active
        }


@dataclass
class Ritual:
    """Definition af en rutine/ritual."""
    ritual_id: str
    name: str
    description: str
    ritual_type: RitualType
    steps: List[RitualStep]
    triggers: List[RitualTrigger] = field(default_factory=list)
    owner_id: Optional[str] = None  # Hvem ejer dette ritual
    is_public: bool = True  # Synligt for alle?
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_step(self, step_id: str) -> Optional[RitualStep]:
        """Hent et specifikt trin."""
        return next((s for s in self.steps if s.step_id == step_id), None)

    def get_first_step(self) -> Optional[RitualStep]:
        """Hent første trin."""
        return self.steps[0] if self.steps else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ritual_id": self.ritual_id,
            "name": self.name,
            "description": self.description,
            "ritual_type": self.ritual_type.value,
            "step_count": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
            "triggers": [t.to_dict() for t in self.triggers],
            "owner_id": self.owner_id,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class StepResult:
    """Resultat af et trin."""
    step_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    thoughts: List[str] = field(default_factory=list)  # Tanker under trin


@dataclass
class RitualExecution:
    """En kørende eksekvering af et ritual."""
    execution_id: str
    ritual_id: str
    executor_id: str
    state: RitualState = RitualState.PENDING
    current_step_id: Optional[str] = None
    step_results: List[StepResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_output: Any = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "ritual_id": self.ritual_id,
            "executor_id": self.executor_id,
            "state": self.state.value,
            "current_step_id": self.current_step_id,
            "completed_steps": len(self.step_results),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


# =============================================================================
# RITUAL BUILDER
# =============================================================================

class RitualBuilder:
    """
    Builder for at konstruere ritualer.

    Gør det nemt at definere komplette rutiner
    med alle deres trin og triggers.
    """

    def __init__(self, name: str, ritual_type: RitualType = RitualType.TRIGGERED):
        self._ritual_id = f"ritual_{secrets.token_hex(8)}"
        self._name = name
        self._description = ""
        self._ritual_type = ritual_type
        self._steps: List[RitualStep] = []
        self._triggers: List[RitualTrigger] = []
        self._owner_id: Optional[str] = None
        self._is_public = True
        self._metadata: Dict[str, Any] = {}

    def description(self, desc: str) -> RitualBuilder:
        """Sæt beskrivelse."""
        self._description = desc
        return self

    def owner(self, owner_id: str) -> RitualBuilder:
        """Sæt ejer."""
        self._owner_id = owner_id
        return self

    def private(self) -> RitualBuilder:
        """Gør ritualet privat."""
        self._is_public = False
        return self

    def metadata(self, key: str, value: Any) -> RitualBuilder:
        """Tilføj metadata."""
        self._metadata[key] = value
        return self

    def step(
        self,
        name: str,
        step_type: StepType,
        description: str,
        action: Optional[Callable[..., Awaitable[Any]]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        think_aloud: bool = True
    ) -> RitualBuilder:
        """Tilføj et trin."""
        step = RitualStep(
            step_id=f"step_{len(self._steps)+1}_{secrets.token_hex(4)}",
            step_type=step_type,
            name=name,
            description=description,
            action=action,
            parameters=parameters or {},
            think_aloud=think_aloud
        )
        # Link til forrige step
        if self._steps:
            self._steps[-1].on_success = step.step_id
        self._steps.append(step)
        return self

    def action(
        self,
        name: str,
        description: str,
        action: Callable[..., Awaitable[Any]],
        **params
    ) -> RitualBuilder:
        """Tilføj et handlings-trin."""
        return self.step(name, StepType.ACTION, description, action, params)

    def check(
        self,
        name: str,
        description: str,
        condition: Callable[..., Awaitable[bool]],
        **params
    ) -> RitualBuilder:
        """Tilføj et check-trin."""
        return self.step(name, StepType.CHECK, description, condition, params)

    def think(
        self,
        name: str,
        description: str,
        **params
    ) -> RitualBuilder:
        """Tilføj et tænke-trin."""
        return self.step(name, StepType.THINK, description, parameters=params)

    def wait(
        self,
        name: str,
        seconds: int
    ) -> RitualBuilder:
        """Tilføj et vente-trin."""
        return self.step(
            name, StepType.WAIT,
            f"Vent {seconds} sekunder",
            parameters={"seconds": seconds}
        )

    def broadcast(
        self,
        name: str,
        message: str
    ) -> RitualBuilder:
        """Tilføj et broadcast-trin."""
        return self.step(
            name, StepType.BROADCAST,
            "Send til fællesskab",
            parameters={"message": message}
        )

    def collect(
        self,
        name: str,
        what: str
    ) -> RitualBuilder:
        """Tilføj et indsamlings-trin."""
        return self.step(
            name, StepType.COLLECT,
            f"Saml: {what}",
            parameters={"target": what}
        )

    def trigger_on_event(self, event_name: str) -> RitualBuilder:
        """Tilføj event-trigger."""
        trigger = RitualTrigger(
            trigger_id=f"trigger_{secrets.token_hex(4)}",
            trigger_type=TriggerType.EVENT,
            conditions={"event": event_name}
        )
        self._triggers.append(trigger)
        return self

    def trigger_on_time(self, time_pattern: str) -> RitualBuilder:
        """Tilføj tids-trigger (cron-lignende)."""
        trigger = RitualTrigger(
            trigger_id=f"trigger_{secrets.token_hex(4)}",
            trigger_type=TriggerType.TIME,
            conditions={"pattern": time_pattern}
        )
        self._triggers.append(trigger)
        return self

    def trigger_manual(self) -> RitualBuilder:
        """Tilføj manuel trigger."""
        trigger = RitualTrigger(
            trigger_id=f"trigger_{secrets.token_hex(4)}",
            trigger_type=TriggerType.MANUAL,
            conditions={}
        )
        self._triggers.append(trigger)
        return self

    def build(self) -> Ritual:
        """Byg det færdige ritual."""
        return Ritual(
            ritual_id=self._ritual_id,
            name=self._name,
            description=self._description,
            ritual_type=self._ritual_type,
            steps=self._steps,
            triggers=self._triggers if self._triggers else [
                RitualTrigger(
                    trigger_id=f"trigger_{secrets.token_hex(4)}",
                    trigger_type=TriggerType.MANUAL,
                    conditions={}
                )
            ],
            owner_id=self._owner_id,
            is_public=self._is_public,
            metadata=self._metadata
        )


# =============================================================================
# MAIN CLASS: RITUAL EXECUTOR
# =============================================================================

class RitualExecutor:
    """
    Naturlig rutine-afvikling for MASTERMIND Tilstand.

    Eksekverer ritualer med transparent reasoning,
    fælles opmærksomhed og naturlig flow.

    Princip: "Rutiner skaber flow, ikke begrænsning"
    """

    def __init__(
        self,
        wave_collector: Optional[WaveCollector] = None,
        collective_awareness: Optional[CollectiveAwareness] = None,
        think_aloud_stream: Optional[ThinkAloudStream] = None
    ):
        self._wave_collector = wave_collector or get_wave_collector()
        self._awareness = collective_awareness or get_collective_awareness()
        self._think_aloud = think_aloud_stream or get_think_aloud_stream()

        self._rituals: Dict[str, Ritual] = {}
        self._active_executions: Dict[str, RitualExecution] = {}
        self._execution_history: List[RitualExecution] = []

        self._active = False
        self._trigger_task: Optional[asyncio.Task] = None

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def start(self) -> None:
        """Start ritual executor."""
        self._active = True
        self._trigger_task = asyncio.create_task(self._trigger_loop())
        logger.info("Ritual Executor startet")

    async def stop(self) -> None:
        """Stop ritual executor."""
        self._active = False
        if self._trigger_task:
            self._trigger_task.cancel()
        logger.info("Ritual Executor stoppet")

    async def _trigger_loop(self) -> None:
        """Loop der tjekker triggers."""
        while self._active:
            await asyncio.sleep(1)
            try:
                await self._check_triggers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trigger loop fejl: {e}")

    async def _check_triggers(self) -> None:
        """Tjek om nogen triggers skal aktiveres."""
        now = datetime.now()

        for ritual in self._rituals.values():
            for trigger in ritual.triggers:
                if not trigger.active:
                    continue

                should_trigger = await self._evaluate_trigger(trigger, now)
                if should_trigger:
                    # Start ritual automatisk
                    logger.info(f"Trigger aktiveret for ritual: {ritual.name}")
                    await self.execute(
                        ritual.ritual_id,
                        executor_id="auto_trigger"
                    )

    async def _evaluate_trigger(
        self,
        trigger: RitualTrigger,
        now: datetime
    ) -> bool:
        """Evaluer om en trigger skal aktiveres."""
        if trigger.trigger_type == TriggerType.TIME:
            # Simpel time-matching (kan udvides med cron)
            pattern = trigger.conditions.get("pattern", "")
            if pattern == "hourly" and now.minute == 0 and now.second < 2:
                return True
            elif pattern == "daily" and now.hour == 0 and now.minute == 0:
                return True

        elif trigger.trigger_type == TriggerType.EVENT:
            # Events håndteres via on_event metoden
            pass

        return False

    # =========================================================================
    # RITUAL MANAGEMENT
    # =========================================================================

    def register(self, ritual: Ritual) -> None:
        """Registrer et nyt ritual."""
        self._rituals[ritual.ritual_id] = ritual
        logger.info(f"Registreret ritual: {ritual.name}")

    def unregister(self, ritual_id: str) -> bool:
        """Afregistrer et ritual."""
        if ritual_id in self._rituals:
            del self._rituals[ritual_id]
            return True
        return False

    def get_ritual(self, ritual_id: str) -> Optional[Ritual]:
        """Hent et ritual."""
        return self._rituals.get(ritual_id)

    def get_all_rituals(self) -> List[Ritual]:
        """Hent alle ritualer."""
        return list(self._rituals.values())

    def find_rituals(
        self,
        ritual_type: Optional[RitualType] = None,
        owner_id: Optional[str] = None
    ) -> List[Ritual]:
        """Find ritualer baseret på kriterier."""
        results = []
        for ritual in self._rituals.values():
            if ritual_type and ritual.ritual_type != ritual_type:
                continue
            if owner_id and ritual.owner_id != owner_id:
                continue
            results.append(ritual)
        return results

    # =========================================================================
    # EXECUTION
    # =========================================================================

    async def execute(
        self,
        ritual_id: str,
        executor_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RitualExecution:
        """
        Eksekvér et ritual.

        Med transparent reasoning og fælles opmærksomhed.
        """
        ritual = self._rituals.get(ritual_id)
        if not ritual:
            raise ValueError(f"Ritual ikke fundet: {ritual_id}")

        # Opret execution
        execution = RitualExecution(
            execution_id=f"exec_{secrets.token_hex(8)}",
            ritual_id=ritual_id,
            executor_id=executor_id,
            state=RitualState.EXECUTING,
            started_at=datetime.now(),
            context=context or {}
        )
        self._active_executions[execution.execution_id] = execution

        # Start tænk højt
        if self._think_aloud:
            await self._think_aloud.start_thinking(
                executor_id,
                f"Ritual: {ritual.name}"
            )
            await self._think_aloud.observe(
                executor_id,
                f"Jeg starter nu ritualet '{ritual.name}': {ritual.description}"
            )

        try:
            # Eksekvér trin for trin
            current_step = ritual.get_first_step()

            while current_step and execution.state == RitualState.EXECUTING:
                execution.current_step_id = current_step.step_id

                # Tænk højt om trinnet
                if current_step.think_aloud and self._think_aloud:
                    await self._think_aloud.think(
                        executor_id,
                        f"Trin: {current_step.name} - {current_step.description}",
                        ThoughtType.CONSIDERATION
                    )

                # Eksekvér trinnet
                result = await self._execute_step(
                    current_step,
                    execution,
                    executor_id
                )
                execution.step_results.append(result)

                # Bestem næste trin
                if result.success:
                    next_step_id = current_step.on_success
                else:
                    next_step_id = current_step.on_failure

                    if current_step.think_aloud and self._think_aloud:
                        await self._think_aloud.doubt(
                            executor_id,
                            f"Trin fejlede: {result.error}",
                            0.3
                        )

                current_step = ritual.get_step(next_step_id) if next_step_id else None

            # Afslut
            execution.state = RitualState.COMPLETED
            execution.completed_at = datetime.now()

            if self._think_aloud:
                await self._think_aloud.conclude(
                    executor_id,
                    f"Ritual '{ritual.name}' afsluttet succesfuldt"
                )

            # Gem i awareness
            if self._awareness:
                await self._awareness.remember(
                    content=execution.to_dict(),
                    memory_type=MemoryType.PROCEDURAL,
                    contexts=["ritual", ritual.name],
                    source_id=executor_id,
                    tags={"ritual_execution", ritual.name}
                )

        except Exception as e:
            execution.state = RitualState.FAILED
            execution.completed_at = datetime.now()
            logger.error(f"Ritual fejlede: {e}")

            if self._think_aloud:
                await self._think_aloud.doubt(
                    executor_id,
                    f"Ritualet fejlede med fejl: {str(e)}",
                    0.1
                )

        finally:
            # Flyt til historik
            del self._active_executions[execution.execution_id]
            self._execution_history.append(execution)

        return execution

    async def _execute_step(
        self,
        step: RitualStep,
        execution: RitualExecution,
        executor_id: str
    ) -> StepResult:
        """Eksekvér et enkelt trin."""
        start_time = datetime.now()
        thoughts: List[str] = []

        try:
            if step.step_type == StepType.ACTION:
                # Kør action
                if step.action:
                    output = await step.action(**step.parameters, **execution.context)
                else:
                    output = None

            elif step.step_type == StepType.CHECK:
                # Kør check
                if step.action:
                    output = await step.action(**step.parameters, **execution.context)
                else:
                    output = True

            elif step.step_type == StepType.WAIT:
                # Vent
                seconds = step.parameters.get("seconds", 1)
                await asyncio.sleep(seconds)
                output = f"Ventede {seconds} sekunder"

            elif step.step_type == StepType.THINK:
                # Tænk (bruger think_aloud)
                if self._think_aloud:
                    thought = step.parameters.get("thought", step.description)
                    await self._think_aloud.reflect(executor_id, thought)
                    thoughts.append(thought)
                output = thoughts

            elif step.step_type == StepType.BROADCAST:
                # Broadcast til fællesskab
                message = step.parameters.get("message", "")
                if self._wave_collector:
                    wave = Wave(
                        wave_id=f"ritual_{secrets.token_hex(6)}",
                        wave_type=WaveType.SIGNAL,
                        origin=WaveOrigin.KOMMANDANT if hasattr(WaveOrigin, 'KOMMANDANT') else 1,
                        source_id=executor_id,
                        content=message
                    )
                    # Import her for at undgå cirkulær import
                    from .wave_collector import WaveOrigin
                    wave.origin = WaveOrigin.KOMMANDANT
                    await self._wave_collector.inject_wave(wave)
                output = f"Broadcasted: {message}"

            elif step.step_type == StepType.COLLECT:
                # Saml fra wave collector
                if self._wave_collector:
                    waves = await self._wave_collector.get_recent_waves(seconds=60)
                    output = [w.to_dict() for w in waves]
                else:
                    output = []

            else:
                output = None

            duration = int((datetime.now() - start_time).total_seconds() * 1000)

            return StepResult(
                step_id=step.step_id,
                success=True,
                output=output,
                duration_ms=duration,
                thoughts=thoughts
            )

        except Exception as e:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)

            return StepResult(
                step_id=step.step_id,
                success=False,
                error=str(e),
                duration_ms=duration,
                thoughts=thoughts
            )

    # =========================================================================
    # CONTROL
    # =========================================================================

    async def pause(self, execution_id: str) -> bool:
        """Pauser en aktiv execution."""
        if execution_id in self._active_executions:
            self._active_executions[execution_id].state = RitualState.PAUSED
            return True
        return False

    async def resume(self, execution_id: str) -> bool:
        """Genoptag en pauseret execution."""
        if execution_id in self._active_executions:
            execution = self._active_executions[execution_id]
            if execution.state == RitualState.PAUSED:
                execution.state = RitualState.EXECUTING
                return True
        return False

    async def cancel(self, execution_id: str) -> bool:
        """Annuller en aktiv execution."""
        if execution_id in self._active_executions:
            execution = self._active_executions[execution_id]
            execution.state = RitualState.CANCELLED
            execution.completed_at = datetime.now()
            del self._active_executions[execution_id]
            self._execution_history.append(execution)
            return True
        return False

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Hent status for ritual executor."""
        return {
            "active": self._active,
            "registered_rituals": len(self._rituals),
            "active_executions": len(self._active_executions),
            "total_executions": len(self._execution_history),
            "rituals": [r.to_dict() for r in self._rituals.values()],
            "executions": [e.to_dict() for e in self._active_executions.values()]
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_ritual_executor_instance: Optional[RitualExecutor] = None


def create_ritual_executor(
    wave_collector: Optional[WaveCollector] = None,
    collective_awareness: Optional[CollectiveAwareness] = None,
    think_aloud_stream: Optional[ThinkAloudStream] = None
) -> RitualExecutor:
    """Opret en ny Ritual Executor."""
    global _ritual_executor_instance
    _ritual_executor_instance = RitualExecutor(
        wave_collector,
        collective_awareness,
        think_aloud_stream
    )
    return _ritual_executor_instance


def get_ritual_executor() -> Optional[RitualExecutor]:
    """Hent den aktive Ritual Executor."""
    return _ritual_executor_instance


# =============================================================================
# PRE-DEFINED RITUALS
# =============================================================================

def create_startup_ritual() -> Ritual:
    """Opret standard opstart-ritual."""
    return (
        RitualBuilder("Opstart Ritual", RitualType.STARTUP)
        .description("Standard opstart for MASTERMIND tilstand")
        .think("Initialiser", "Klargør alle systemer")
        .collect("Saml status", "system_status")
        .broadcast("Annoncer", "MASTERMIND tilstand aktiveret")
        .think("Reflekter", "Alle systemer klar til arbejde")
        .trigger_on_event("system_start")
        .build()
    )


def create_shutdown_ritual() -> Ritual:
    """Opret standard nedluknings-ritual."""
    return (
        RitualBuilder("Nedlukning Ritual", RitualType.SHUTDOWN)
        .description("Standard nedlukning for MASTERMIND tilstand")
        .think("Forbered", "Klargør til nedlukning")
        .collect("Gem status", "final_status")
        .broadcast("Annoncer", "MASTERMIND tilstand lukker ned")
        .wait("Vent på svar", 3)
        .think("Afslut", "Alle data gemt - klar til nedlukning")
        .trigger_on_event("system_shutdown")
        .build()
    )


def create_daily_reflection_ritual() -> Ritual:
    """Opret daglig refleksions-ritual."""
    return (
        RitualBuilder("Daglig Refleksion", RitualType.DAILY)
        .description("Daglig refleksion over dagens arbejde")
        .think("Start", "Lad os reflektere over dagens arbejde")
        .collect("Saml", "todays_activities")
        .think("Analyser", "Hvad gik godt? Hvad kan forbedres?")
        .think("Planlæg", "Hvad skal fokus være i morgen?")
        .broadcast("Del", "Daglig refleksion afsluttet")
        .trigger_on_time("daily")
        .build()
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RitualType",
    "RitualState",
    "StepType",
    "TriggerType",

    # Data classes
    "RitualStep",
    "RitualTrigger",
    "Ritual",
    "StepResult",
    "RitualExecution",

    # Classes
    "RitualBuilder",
    "RitualExecutor",

    # Pre-defined rituals
    "create_startup_ritual",
    "create_shutdown_ritual",
    "create_daily_reflection_ritual",

    # Factory functions
    "create_ritual_executor",
    "get_ritual_executor",
]
