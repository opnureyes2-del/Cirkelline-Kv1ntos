"""
CKC Orchestrator - Central Kommandant-Agent
============================================

Den centrale orkestrator for Cirkelline Kreativ Koordinator.
Styrer alle specialiserede agenter og validerings flows.

Features:
    - Task decomposition og prioritering
    - Agent routing og orkestrering
    - Validerings flow management
    - HITL (Human-in-the-Loop) med chat notifikationer
    - Akut notifikation ved kritiske hændelser
    - Zero-Oversight-Drift support

Flow: Observation -> Analyse -> Delegation -> Validering -> Respons
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set, Tuple, Union
from enum import Enum
import uuid
import asyncio
from collections import defaultdict
import traceback

from cirkelline.config import logger

# Forward reference for TaskContext
TaskContext = None

def _get_task_context():
    """Lazy import of TaskContext to avoid circular imports."""
    global TaskContext
    if TaskContext is None:
        from .context import TaskContext as TC, WorkflowStep, WorkflowStepStatus
        TaskContext = TC
    return TaskContext


class TaskPriority(Enum):
    """Prioritet for opgaver."""
    CRITICAL = 1    # Akut - skal behandles straks
    HIGH = 2        # Høj - næste i køen
    MEDIUM = 3      # Normal - standard behandling
    LOW = 4         # Lav - kan vente
    BACKGROUND = 5  # Baggrund - køres når der er tid


class TaskStatus(Enum):
    """Status for en opgave."""
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    AWAITING_VALIDATION = "awaiting_validation"
    AWAITING_USER = "awaiting_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(Enum):
    """Kapabiliteter som agenter kan have."""
    TOOL_DISCOVERY = "tool_discovery"
    TOOL_INTEGRATION = "tool_integration"
    CREATIVE_WRITING = "creative_writing"
    CONTENT_SYNTHESIS = "content_synthesis"
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    EDUCATION = "education"
    WORLD_BUILDING = "world_building"
    SIMULATION = "simulation"
    QUALITY_ASSURANCE = "quality_assurance"
    SELF_CORRECTION = "self_correction"
    HISTORY_TRACKING = "history_tracking"
    LIBRARY_MANAGEMENT = "library_management"


@dataclass
class ValidationFlow:
    """
    Et validerings flow fra læringsrum til bruger og tilbage.

    Flow: Læringsrum -> Kommandør -> Chat -> Bruger -> tilbage til læringsrum
    """
    id: str
    source_room_id: int
    source_room_name: str
    content: Any
    content_type: str

    # Flow state
    current_stage: str = "learning_room"  # learning_room -> commander -> chat -> user -> returning
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Commander analysis
    commander_analysis: Optional[str] = None
    commander_recommendation: Optional[str] = None
    risk_assessment: Optional[str] = None

    # User interaction
    user_notified: bool = False
    user_response: Optional[str] = None
    user_decision: Optional[str] = None  # approve, reject, modify

    # Result
    final_result: Optional[Any] = None
    validation_passed: bool = False

    # History
    stage_history: List[Dict[str, Any]] = field(default_factory=list)

    def advance_to(self, stage: str, notes: str = "") -> None:
        """Avancer til næste stage."""
        self.stage_history.append({
            "from": self.current_stage,
            "to": stage,
            "timestamp": datetime.utcnow().isoformat(),
            "notes": notes
        })
        self.current_stage = stage
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "id": self.id,
            "source_room_id": self.source_room_id,
            "source_room_name": self.source_room_name,
            "content_type": self.content_type,
            "current_stage": self.current_stage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "commander_recommendation": self.commander_recommendation,
            "risk_assessment": self.risk_assessment,
            "user_notified": self.user_notified,
            "user_decision": self.user_decision,
            "validation_passed": self.validation_passed
        }


@dataclass
class Task:
    """En opgave der skal udføres."""
    id: str
    description: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING

    # Assignment
    assigned_agent: Optional[str] = None
    required_capabilities: Set[AgentCapability] = field(default_factory=set)

    # Context
    source: str = ""
    user_id: Optional[str] = None
    learning_room_id: Optional[int] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None

    # Input/Output
    input_data: Any = None
    output_data: Any = None

    # Validation
    validation_flow_id: Optional[str] = None
    requires_validation: bool = True

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    subtasks: List[str] = field(default_factory=list)
    parent_task_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority.name,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "source": self.source,
            "user_id": self.user_id,
            "learning_room_id": self.learning_room_id,
            "created_at": self.created_at.isoformat(),
            "requires_validation": self.requires_validation,
            "subtasks": self.subtasks
        }


@dataclass
class AgentRegistration:
    """Registrering af en agent i orkestratoren."""
    agent_id: str
    name: str
    description: str
    capabilities: Set[AgentCapability]
    learning_room_id: int

    # Status
    is_active: bool = True
    is_available: bool = True
    current_task_id: Optional[str] = None

    # Performance
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_response_time: float = 0.0

    # Metadata
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "learning_room_id": self.learning_room_id,
            "is_active": self.is_active,
            "is_available": self.is_available,
            "current_task_id": self.current_task_id,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed
        }


# ═══════════════════════════════════════════════════════════════
# WORK-LOOP SEQUENCER (v1.1.0)
# ═══════════════════════════════════════════════════════════════

class WorkLoopStepType(Enum):
    """Type af work-loop step."""
    AGENT_CALL = "agent_call"         # Kald til en agent
    PARALLEL_CALL = "parallel_call"   # Parallelle kald
    VALIDATION = "validation"          # Validerings check
    CONDITION = "condition"            # Betinget forgrening
    TRANSFORM = "transform"            # Data transformation
    WAIT = "wait"                       # Vent på ekstern event
    ILCP_MESSAGE = "ilcp_message"      # Send ILCP besked


class WorkLoopStatus(Enum):
    """Status for en work-loop."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    AWAITING_INPUT = "awaiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkLoopStep:
    """
    Et trin i en work-loop sekvens.

    Definerer hvad der skal ske og med hvilke data.
    """
    step_id: str
    step_type: WorkLoopStepType
    agent_id: Optional[str] = None
    action: str = ""

    # For parallel calls
    parallel_steps: List['WorkLoopStep'] = field(default_factory=list)

    # For conditions
    condition_fn: Optional[Callable[[Any], bool]] = None
    on_true_step: Optional[str] = None  # Step ID to jump to if true
    on_false_step: Optional[str] = None  # Step ID to jump to if false

    # For transforms
    transform_fn: Optional[Callable[[Any], Any]] = None

    # Input/Output mapping
    input_mapping: Dict[str, str] = field(default_factory=dict)  # step_result -> input_key
    output_key: str = ""  # Key to store result in context

    # Metadata
    timeout_seconds: float = 300.0
    retry_on_failure: bool = True
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "agent_id": self.agent_id,
            "action": self.action,
            "output_key": self.output_key,
            "timeout_seconds": self.timeout_seconds,
            "has_parallel": len(self.parallel_steps) > 0
        }


@dataclass
class WorkLoop:
    """
    En work-loop der definerer en sekvens af operationer.

    Eksempel flow:
        Kommandant → Tool Explorer → Knowledge Architect → Kommandant
    """
    loop_id: str
    name: str
    description: str
    steps: List[WorkLoopStep] = field(default_factory=list)

    # State
    status: WorkLoopStatus = WorkLoopStatus.CREATED
    current_step_index: int = 0
    task_context_data: Optional[Dict[str, Any]] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Results
    step_results: Dict[str, Any] = field(default_factory=dict)
    final_result: Optional[Any] = None
    error: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_hitl: bool = False

    def get_current_step(self) -> Optional[WorkLoopStep]:
        """Hent nuværende step."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance(self) -> bool:
        """Avancer til næste step."""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return True
        return False

    def jump_to_step(self, step_id: str) -> bool:
        """Hop til et specifikt step."""
        for i, step in enumerate(self.steps):
            if step.step_id == step_id:
                self.current_step_index = i
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "total_steps": len(self.steps),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "requires_hitl": self.requires_hitl,
            "error": self.error
        }


class WorkLoopSequencer:
    """
    Work-Loop Sequencer for CKC.

    Håndterer:
    - Definition af work-loops med sekvenser af steps
    - Parallel og sekventiel eksekvering
    - TaskContext-bevarelse gennem hele flowet
    - Fejlhåndtering og retry-logik
    - HITL-integration ved kritiske punkter

    Eksempel brug:
        sequencer = WorkLoopSequencer()

        # Definer work-loop
        loop = sequencer.create_loop("analyze_task", "Analyser opgave", [
            WorkLoopStep(
                step_id="step_1",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="tool_explorer",
                action="discover_tools",
                output_key="discovered_tools"
            ),
            WorkLoopStep(
                step_id="step_2",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="knowledge_architect",
                action="analyze_tools",
                input_mapping={"discovered_tools": "tools"},
                output_key="analysis"
            )
        ])

        # Kør work-loop med TaskContext
        result = await sequencer.execute_loop(loop, context)
    """

    def __init__(self, orchestrator: Optional['CKCOrchestrator'] = None):
        self._orchestrator = orchestrator
        self._loops: Dict[str, WorkLoop] = {}
        self._templates: Dict[str, List[WorkLoopStep]] = {}
        self._agent_handlers: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()

        # Stats
        self._stats = {
            "loops_created": 0,
            "loops_completed": 0,
            "loops_failed": 0,
            "total_steps_executed": 0
        }

        logger.info("WorkLoopSequencer initialized")

    # ═══════════════════════════════════════════════════════════
    # LOOP CREATION & TEMPLATES
    # ═══════════════════════════════════════════════════════════

    def create_loop(
        self,
        name: str,
        description: str,
        steps: List[WorkLoopStep],
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkLoop:
        """Opret en ny work-loop."""
        loop_id = f"loop_{uuid.uuid4().hex[:12]}"

        loop = WorkLoop(
            loop_id=loop_id,
            name=name,
            description=description,
            steps=steps,
            metadata=metadata or {}
        )

        self._loops[loop_id] = loop
        self._stats["loops_created"] += 1

        logger.info(f"Work-loop created: {name} ({loop_id}) with {len(steps)} steps")
        return loop

    def register_template(self, template_name: str, steps: List[WorkLoopStep]) -> None:
        """Registrer en work-loop template til genbrug."""
        self._templates[template_name] = steps
        logger.info(f"Work-loop template registered: {template_name}")

    def create_from_template(
        self,
        template_name: str,
        loop_name: str,
        description: str = ""
    ) -> Optional[WorkLoop]:
        """Opret work-loop fra template."""
        template = self._templates.get(template_name)
        if not template:
            logger.warning(f"Template not found: {template_name}")
            return None

        # Deep copy af steps
        import copy
        steps = copy.deepcopy(template)

        return self.create_loop(loop_name, description or f"From template: {template_name}", steps)

    def register_agent_handler(
        self,
        agent_id: str,
        handler: Callable[[str, Dict[str, Any]], Any]
    ) -> None:
        """
        Registrer en handler-funktion for en agent.

        Handler signature: async (action: str, input_data: Dict) -> result
        """
        self._agent_handlers[agent_id] = handler
        logger.debug(f"Agent handler registered: {agent_id}")

    # ═══════════════════════════════════════════════════════════
    # LOOP EXECUTION
    # ═══════════════════════════════════════════════════════════

    async def execute_loop(
        self,
        loop: WorkLoop,
        context: Optional[Any] = None,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Any]:
        """
        Eksekver en work-loop.

        Args:
            loop: Work-loopen der skal køres
            context: Optional TaskContext
            input_data: Initial input data

        Returns:
            Tuple af (success, result)
        """
        async with self._lock:
            loop.status = WorkLoopStatus.RUNNING
            loop.started_at = datetime.utcnow()

            # Initialiser context
            if context:
                if hasattr(context, 'to_dict'):
                    loop.task_context_data = context.to_dict()
                else:
                    loop.task_context_data = context

            # Initialiser step results med input data
            if input_data:
                loop.step_results.update(input_data)

        logger.info(f"Starting work-loop: {loop.name} ({loop.loop_id})")

        try:
            while loop.current_step_index < len(loop.steps):
                step = loop.get_current_step()
                if not step:
                    break

                logger.debug(f"Executing step {step.step_id} ({step.step_type.value})")

                # Eksekver step
                success, result = await self._execute_step(loop, step)

                if not success:
                    # Check retry
                    if step.retry_on_failure and step.max_retries > 0:
                        step.max_retries -= 1
                        logger.warning(f"Step {step.step_id} failed, retrying ({step.max_retries} left)")
                        continue

                    # Fejl - stop loop
                    loop.status = WorkLoopStatus.FAILED
                    loop.error = str(result)
                    loop.completed_at = datetime.utcnow()
                    self._stats["loops_failed"] += 1
                    logger.error(f"Work-loop failed at step {step.step_id}: {result}")
                    return False, result

                # Gem resultat
                if step.output_key:
                    loop.step_results[step.output_key] = result

                self._stats["total_steps_executed"] += 1

                # Check for HITL requirement
                if loop.requires_hitl and step.step_type == WorkLoopStepType.VALIDATION:
                    loop.status = WorkLoopStatus.AWAITING_INPUT
                    logger.info(f"Work-loop paused for HITL at step {step.step_id}")
                    return True, {"awaiting_hitl": True, "step_id": step.step_id}

                # Avancer til næste step
                if not loop.advance():
                    break

            # Loop completed
            loop.status = WorkLoopStatus.COMPLETED
            loop.completed_at = datetime.utcnow()
            loop.final_result = loop.step_results
            self._stats["loops_completed"] += 1

            logger.info(f"Work-loop completed: {loop.name}")
            return True, loop.final_result

        except Exception as e:
            loop.status = WorkLoopStatus.FAILED
            loop.error = str(e)
            loop.completed_at = datetime.utcnow()
            self._stats["loops_failed"] += 1
            logger.error(f"Work-loop error: {e}\n{traceback.format_exc()}")
            return False, str(e)

    async def _execute_step(
        self,
        loop: WorkLoop,
        step: WorkLoopStep
    ) -> Tuple[bool, Any]:
        """Eksekver et enkelt step."""
        try:
            if step.step_type == WorkLoopStepType.AGENT_CALL:
                return await self._execute_agent_call(loop, step)

            elif step.step_type == WorkLoopStepType.PARALLEL_CALL:
                return await self._execute_parallel_calls(loop, step)

            elif step.step_type == WorkLoopStepType.VALIDATION:
                return await self._execute_validation(loop, step)

            elif step.step_type == WorkLoopStepType.CONDITION:
                return await self._execute_condition(loop, step)

            elif step.step_type == WorkLoopStepType.TRANSFORM:
                return await self._execute_transform(loop, step)

            elif step.step_type == WorkLoopStepType.WAIT:
                return True, {"waited": True}

            elif step.step_type == WorkLoopStepType.ILCP_MESSAGE:
                return await self._execute_ilcp_message(loop, step)

            else:
                return False, f"Unknown step type: {step.step_type}"

        except asyncio.TimeoutError:
            return False, f"Step {step.step_id} timed out after {step.timeout_seconds}s"
        except Exception as e:
            return False, str(e)

    async def _execute_agent_call(
        self,
        loop: WorkLoop,
        step: WorkLoopStep
    ) -> Tuple[bool, Any]:
        """Eksekver et agent-kald."""
        if not step.agent_id:
            return False, "No agent_id specified"

        # Build input data from mappings
        input_data = {}
        for source_key, target_key in step.input_mapping.items():
            if source_key in loop.step_results:
                input_data[target_key] = loop.step_results[source_key]

        # Check for handler
        handler = self._agent_handlers.get(step.agent_id)
        if handler:
            try:
                result = await asyncio.wait_for(
                    handler(step.action, input_data),
                    timeout=step.timeout_seconds
                )
                return True, result
            except Exception as e:
                return False, str(e)

        # Fallback: Simuleret respons
        logger.warning(f"No handler for agent {step.agent_id}, using simulated response")
        return True, {
            "agent_id": step.agent_id,
            "action": step.action,
            "input_data": input_data,
            "simulated": True,
            "result": f"Simulated result for {step.action}"
        }

    async def _execute_parallel_calls(
        self,
        loop: WorkLoop,
        step: WorkLoopStep
    ) -> Tuple[bool, Any]:
        """Eksekver parallelle agent-kald."""
        if not step.parallel_steps:
            return True, {}

        tasks = []
        for parallel_step in step.parallel_steps:
            task = asyncio.create_task(self._execute_step(loop, parallel_step))
            tasks.append((parallel_step.step_id, task))

        results = {}
        all_success = True

        for step_id, task in tasks:
            try:
                success, result = await asyncio.wait_for(
                    task,
                    timeout=step.timeout_seconds
                )
                results[step_id] = result
                if not success:
                    all_success = False
            except asyncio.TimeoutError:
                results[step_id] = {"error": "timeout"}
                all_success = False
            except Exception as e:
                results[step_id] = {"error": str(e)}
                all_success = False

        return all_success, results

    async def _execute_validation(
        self,
        loop: WorkLoop,
        step: WorkLoopStep
    ) -> Tuple[bool, Any]:
        """Eksekver validerings-step."""
        # Build context for validation
        validation_data = {
            "step_id": step.step_id,
            "loop_name": loop.name,
            "current_results": loop.step_results
        }

        # Check if HITL is required
        if loop.requires_hitl:
            return True, {"validation": "awaiting_hitl", "data": validation_data}

        # Auto-validate (simpel check)
        return True, {"validation": "passed", "auto_approved": True}

    async def _execute_condition(
        self,
        loop: WorkLoop,
        step: WorkLoopStep
    ) -> Tuple[bool, Any]:
        """Eksekver betinget forgrening."""
        if not step.condition_fn:
            # Ingen condition, fortsæt
            return True, {"condition": "no_condition"}

        try:
            result = step.condition_fn(loop.step_results)

            if result and step.on_true_step:
                loop.jump_to_step(step.on_true_step)
                return True, {"condition": True, "jumped_to": step.on_true_step}
            elif not result and step.on_false_step:
                loop.jump_to_step(step.on_false_step)
                return True, {"condition": False, "jumped_to": step.on_false_step}

            return True, {"condition": result}

        except Exception as e:
            return False, f"Condition error: {e}"

    async def _execute_transform(
        self,
        loop: WorkLoop,
        step: WorkLoopStep
    ) -> Tuple[bool, Any]:
        """Eksekver data-transformation."""
        if not step.transform_fn:
            return True, loop.step_results

        try:
            result = step.transform_fn(loop.step_results)
            return True, result
        except Exception as e:
            return False, f"Transform error: {e}"

    async def _execute_ilcp_message(
        self,
        loop: WorkLoop,
        step: WorkLoopStep
    ) -> Tuple[bool, Any]:
        """Send ILCP besked."""
        # Dette kræver adgang til ILCPManager - simuleret for nu
        return True, {"ilcp_message": "sent", "step_id": step.step_id}

    # ═══════════════════════════════════════════════════════════
    # LOOP CONTROL
    # ═══════════════════════════════════════════════════════════

    async def pause_loop(self, loop_id: str) -> bool:
        """Pause en work-loop."""
        loop = self._loops.get(loop_id)
        if not loop or loop.status != WorkLoopStatus.RUNNING:
            return False

        loop.status = WorkLoopStatus.PAUSED
        logger.info(f"Work-loop paused: {loop_id}")
        return True

    async def resume_loop(
        self,
        loop_id: str,
        hitl_response: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Any]:
        """Genoptag en pauseret work-loop."""
        loop = self._loops.get(loop_id)
        if not loop:
            return False, "Loop not found"

        if loop.status not in [WorkLoopStatus.PAUSED, WorkLoopStatus.AWAITING_INPUT]:
            return False, f"Loop cannot be resumed from status: {loop.status.value}"

        # Process HITL response if provided
        if hitl_response:
            loop.step_results["hitl_response"] = hitl_response

        # Continue execution
        loop.status = WorkLoopStatus.RUNNING
        if loop.advance():
            return await self.execute_loop(loop)
        else:
            loop.status = WorkLoopStatus.COMPLETED
            loop.completed_at = datetime.utcnow()
            return True, loop.step_results

    async def cancel_loop(self, loop_id: str, reason: str = "Cancelled") -> bool:
        """Annuller en work-loop."""
        loop = self._loops.get(loop_id)
        if not loop:
            return False

        loop.status = WorkLoopStatus.CANCELLED
        loop.error = reason
        loop.completed_at = datetime.utcnow()
        logger.info(f"Work-loop cancelled: {loop_id} - {reason}")
        return True

    # ═══════════════════════════════════════════════════════════
    # STATUS & QUERIES
    # ═══════════════════════════════════════════════════════════

    def get_loop(self, loop_id: str) -> Optional[WorkLoop]:
        """Hent en work-loop."""
        return self._loops.get(loop_id)

    def list_active_loops(self) -> List[WorkLoop]:
        """List aktive work-loops."""
        return [
            loop for loop in self._loops.values()
            if loop.status in [WorkLoopStatus.RUNNING, WorkLoopStatus.PAUSED, WorkLoopStatus.AWAITING_INPUT]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Hent sequencer statistik."""
        return {
            **self._stats,
            "active_loops": len(self.list_active_loops()),
            "registered_templates": len(self._templates),
            "registered_handlers": len(self._agent_handlers)
        }


class CKCOrchestrator:
    """
    Central Kommandant-Agent for CKC.

    Ansvar:
        - Modtage og analysere opgaver
        - Delegere til specialiserede agenter
        - Overvåge validerings flows
        - Håndtere HITL (Human-in-the-Loop)
        - Koordinere akutte notifikationer
        - Sikre Zero-Oversight-Drift

    Principper:
        - Aldrig handle uden brugerens vidende ved kritiske beslutninger
        - Transparens i alle handlinger
        - Etisk filter på alle outputs
        - Sandhed og fakta over alt andet
    """

    def __init__(self):
        self._agents: Dict[str, AgentRegistration] = {}
        self._tasks: Dict[str, Task] = {}
        self._validation_flows: Dict[str, ValidationFlow] = {}
        self._task_queue: List[str] = []  # Task IDs sorted by priority

        self._lock = asyncio.Lock()
        self._chat_callback: Optional[Callable] = None
        self._notification_callback: Optional[Callable] = None

        # Statistik
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_validations": 0,
            "user_interventions": 0
        }

        logger.info("CKC Orchestrator initialized")

    # ═══════════════════════════════════════════════════════════════
    # AGENT MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    async def register_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: Set[AgentCapability],
        learning_room_id: int
    ) -> AgentRegistration:
        """Registrer en agent i orkestratoren."""
        async with self._lock:
            registration = AgentRegistration(
                agent_id=agent_id,
                name=name,
                description=description,
                capabilities=capabilities,
                learning_room_id=learning_room_id
            )
            self._agents[agent_id] = registration
            logger.info(f"Agent registered: {name} ({agent_id})")
            return registration

    async def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Hent en registreret agent."""
        return self._agents.get(agent_id)

    async def list_agents(self, capability: Optional[AgentCapability] = None) -> List[AgentRegistration]:
        """List registrerede agenter, eventuelt filtreret efter kapabilitet."""
        agents = list(self._agents.values())
        if capability:
            agents = [a for a in agents if capability in a.capabilities]
        return agents

    async def find_agent_for_task(self, task: Task) -> Optional[AgentRegistration]:
        """Find den bedste agent til en opgave baseret på kapabiliteter."""
        candidates = []

        for agent in self._agents.values():
            if not agent.is_active or not agent.is_available:
                continue

            # Check kapabiliteter
            if task.required_capabilities.issubset(agent.capabilities):
                candidates.append(agent)

        if not candidates:
            return None

        # Sorter efter performance (færrest fejl, hurtigst)
        candidates.sort(key=lambda a: (a.tasks_failed, a.average_response_time))
        return candidates[0]

    # ═══════════════════════════════════════════════════════════════
    # TASK MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    async def create_task(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        required_capabilities: Optional[Set[AgentCapability]] = None,
        source: str = "",
        user_id: Optional[str] = None,
        learning_room_id: Optional[int] = None,
        input_data: Any = None,
        requires_validation: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Opret en ny opgave."""
        async with self._lock:
            task_id = f"task_{uuid.uuid4().hex[:12]}"

            task = Task(
                id=task_id,
                description=description,
                priority=priority,
                required_capabilities=required_capabilities or set(),
                source=source,
                user_id=user_id,
                learning_room_id=learning_room_id,
                input_data=input_data,
                requires_validation=requires_validation,
                metadata=metadata or {}
            )

            self._tasks[task_id] = task
            self._stats["total_tasks"] += 1

            # Tilføj til kø
            await self._enqueue_task(task_id)

            logger.info(f"Task created: {task_id} - {description[:50]}...")
            return task

    async def _enqueue_task(self, task_id: str) -> None:
        """Tilføj opgave til køen sorteret efter prioritet."""
        task = self._tasks.get(task_id)
        if not task:
            return

        task.status = TaskStatus.QUEUED

        # Indsæt sorteret efter prioritet
        insert_pos = len(self._task_queue)
        for i, queued_id in enumerate(self._task_queue):
            queued_task = self._tasks.get(queued_id)
            if queued_task and task.priority.value < queued_task.priority.value:
                insert_pos = i
                break

        self._task_queue.insert(insert_pos, task_id)

    async def decompose_task(
        self,
        task: Task,
        subtask_descriptions: List[str]
    ) -> List[Task]:
        """Dekomponér en opgave til mindre delopgaver."""
        subtasks = []

        for desc in subtask_descriptions:
            subtask = await self.create_task(
                description=desc,
                priority=task.priority,
                required_capabilities=task.required_capabilities,
                source=task.source,
                user_id=task.user_id,
                learning_room_id=task.learning_room_id,
                requires_validation=task.requires_validation,
                metadata={"parent_task_id": task.id}
            )
            subtask.parent_task_id = task.id
            task.subtasks.append(subtask.id)
            subtasks.append(subtask)

        logger.info(f"Task {task.id} decomposed into {len(subtasks)} subtasks")
        return subtasks

    async def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Tildel en opgave til en agent."""
        async with self._lock:
            task = self._tasks.get(task_id)
            agent = self._agents.get(agent_id)

            if not task or not agent:
                return False

            if not agent.is_available:
                logger.warning(f"Agent {agent_id} not available for task {task_id}")
                return False

            task.assigned_agent = agent_id
            task.status = TaskStatus.ASSIGNED
            agent.is_available = False
            agent.current_task_id = task_id

            # Fjern fra kø
            if task_id in self._task_queue:
                self._task_queue.remove(task_id)

            logger.info(f"Task {task_id} assigned to agent {agent_id}")
            return True

    async def start_task(self, task_id: str) -> bool:
        """Start udførelse af en opgave."""
        task = self._tasks.get(task_id)
        if not task or task.status != TaskStatus.ASSIGNED:
            return False

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()

        logger.info(f"Task {task_id} started")
        return True

    async def cancel_all_tasks(self, reason: str = "System cancellation") -> int:
        """
        Annuller alle igangværende opgaver.

        Bruges typisk ved nødstop eller system shutdown.

        Args:
            reason: Årsag til annullering

        Returns:
            Antal annullerede opgaver
        """
        async with self._lock:
            cancelled_count = 0

            for task_id, task in self._tasks.items():
                if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED,
                                   TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                    task.status = TaskStatus.CANCELLED
                    task.metadata["cancellation_reason"] = reason
                    task.completed_at = datetime.utcnow()
                    cancelled_count += 1

                    # Frigør agent hvis tildelt
                    if task.assigned_agent:
                        agent = self._agents.get(task.assigned_agent)
                        if agent:
                            agent.is_available = True
                            agent.current_task_id = None

            # Ryd køen
            self._task_queue.clear()

            logger.warning(f"Cancelled {cancelled_count} tasks: {reason}")
            return cancelled_count

    async def complete_task(
        self,
        task_id: str,
        output_data: Any,
        success: bool = True
    ) -> bool:
        """Fuldfør en opgave."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            task.output_data = output_data
            task.completed_at = datetime.utcnow()

            if success:
                if task.requires_validation:
                    task.status = TaskStatus.AWAITING_VALIDATION
                    # Start validerings flow
                    await self._start_validation_for_task(task)
                else:
                    task.status = TaskStatus.COMPLETED
                    self._stats["completed_tasks"] += 1
            else:
                task.status = TaskStatus.FAILED
                self._stats["failed_tasks"] += 1

            # Frigør agent
            if task.assigned_agent:
                agent = self._agents.get(task.assigned_agent)
                if agent:
                    agent.is_available = True
                    agent.current_task_id = None
                    agent.last_activity = datetime.utcnow()
                    if success:
                        agent.tasks_completed += 1
                    else:
                        agent.tasks_failed += 1

            logger.info(f"Task {task_id} completed: {'success' if success else 'failed'}")
            return True

    # ═══════════════════════════════════════════════════════════════
    # VALIDATION FLOW
    # ═══════════════════════════════════════════════════════════════

    async def _start_validation_for_task(self, task: Task) -> ValidationFlow:
        """Start validerings flow for en opgave."""
        flow_id = f"val_{uuid.uuid4().hex[:8]}"

        flow = ValidationFlow(
            id=flow_id,
            source_room_id=task.learning_room_id or 0,
            source_room_name=task.source or "unknown",
            content=task.output_data,
            content_type=type(task.output_data).__name__
        )

        self._validation_flows[flow_id] = flow
        task.validation_flow_id = flow_id
        self._stats["active_validations"] += 1

        # Start flow - analyser som kommandør
        await self._commander_analyze(flow)

        return flow

    async def create_validation_flow(
        self,
        content: Any,
        source_room_id: int,
        source_room_name: str,
        content_type: str = "unknown"
    ) -> ValidationFlow:
        """Opret et manuelt validerings flow."""
        flow_id = f"val_{uuid.uuid4().hex[:8]}"

        flow = ValidationFlow(
            id=flow_id,
            source_room_id=source_room_id,
            source_room_name=source_room_name,
            content=content,
            content_type=content_type
        )

        self._validation_flows[flow_id] = flow
        self._stats["active_validations"] += 1

        logger.info(f"Validation flow created: {flow_id}")
        return flow

    async def _commander_analyze(self, flow: ValidationFlow) -> None:
        """Kommandør analyserer indhold."""
        flow.advance_to("commander", "Starting commander analysis")

        # Simuler analyse (i produktion ville dette være en AI analyse)
        analysis_results = {
            "content_summary": f"Content of type {flow.content_type}",
            "risk_level": "low",
            "recommendation": "approve",
            "notes": "Standard content, no concerns identified"
        }

        flow.commander_analysis = str(analysis_results)
        flow.commander_recommendation = analysis_results["recommendation"]
        flow.risk_assessment = analysis_results["risk_level"]

        # Gå videre til chat/bruger
        await self._notify_user_via_chat(flow)

    async def _notify_user_via_chat(self, flow: ValidationFlow) -> None:
        """Notificer bruger via chat."""
        flow.advance_to("chat", "Notifying user via chat")
        flow.user_notified = True

        if self._chat_callback:
            try:
                message = {
                    "type": "validation_request",
                    "flow_id": flow.id,
                    "source": flow.source_room_name,
                    "content_type": flow.content_type,
                    "recommendation": flow.commander_recommendation,
                    "risk": flow.risk_assessment,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self._chat_callback(message)
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")

        flow.advance_to("user", "Awaiting user decision")

    async def user_respond_to_validation(
        self,
        flow_id: str,
        decision: str,  # approve, reject, modify
        response: Optional[str] = None
    ) -> bool:
        """Bruger svarer på validerings request."""
        flow = self._validation_flows.get(flow_id)
        if not flow or flow.current_stage != "user":
            return False

        flow.user_response = response
        flow.user_decision = decision
        self._stats["user_interventions"] += 1

        if decision == "approve":
            flow.validation_passed = True
            flow.advance_to("returning", f"User approved: {response}")
            await self._finalize_validation(flow, success=True)
        elif decision == "reject":
            flow.validation_passed = False
            flow.advance_to("returning", f"User rejected: {response}")
            await self._finalize_validation(flow, success=False)
        else:  # modify
            flow.advance_to("returning", f"User requested modification: {response}")
            # Her kunne vi starte en ny opgave med modifikationerne

        return True

    async def _finalize_validation(self, flow: ValidationFlow, success: bool) -> None:
        """Afslut validerings flow."""
        flow.final_result = {
            "passed": success,
            "decision": flow.user_decision,
            "timestamp": datetime.utcnow().isoformat()
        }

        self._stats["active_validations"] -= 1

        logger.info(f"Validation {flow.id} finalized: {'passed' if success else 'failed'}")

    async def get_validation_flow(self, flow_id: str) -> Optional[ValidationFlow]:
        """Hent et validerings flow."""
        return self._validation_flows.get(flow_id)

    async def list_pending_validations(self) -> List[ValidationFlow]:
        """List ventende validerings flows."""
        return [
            f for f in self._validation_flows.values()
            if f.current_stage == "user" and not f.validation_passed
        ]

    # ═══════════════════════════════════════════════════════════════
    # CALLBACKS & NOTIFICATIONS
    # ═══════════════════════════════════════════════════════════════

    def set_chat_callback(self, callback: Callable) -> None:
        """Sæt callback for chat notifikationer."""
        self._chat_callback = callback

    def set_notification_callback(self, callback: Callable) -> None:
        """Sæt callback for akutte notifikationer."""
        self._notification_callback = callback

    async def send_acute_notification(
        self,
        message: str,
        severity: str = "warning",
        source: Optional[str] = None
    ) -> None:
        """Send akut notifikation."""
        notification = {
            "id": f"notif_{uuid.uuid4().hex[:8]}",
            "message": message,
            "severity": severity,
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.warning(f"Acute notification: {message} ({severity})")

        if self._notification_callback:
            try:
                await self._notification_callback(notification)
            except Exception as e:
                logger.error(f"Failed to send acute notification: {e}")

    # ═══════════════════════════════════════════════════════════════
    # PROCESSING
    # ═══════════════════════════════════════════════════════════════

    async def process_next_task(self) -> Optional[Task]:
        """Behandl næste opgave i køen."""
        if not self._task_queue:
            return None

        task_id = self._task_queue[0]
        task = self._tasks.get(task_id)

        if not task:
            self._task_queue.pop(0)
            return None

        # Find agent
        agent = await self.find_agent_for_task(task)
        if not agent:
            logger.warning(f"No available agent for task {task_id}")
            return None

        # Tildel og start
        await self.assign_task(task_id, agent.agent_id)
        await self.start_task(task_id)

        return task

    async def run_processing_loop(self, interval: float = 1.0) -> None:
        """Kør kontinuerlig opgavebehandling."""
        logger.info("Starting CKC Orchestrator processing loop")

        while True:
            try:
                task = await self.process_next_task()
                if task:
                    logger.debug(f"Processing task: {task.id}")
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")

            await asyncio.sleep(interval)

    # ═══════════════════════════════════════════════════════════════
    # STATUS & REPORTING
    # ═══════════════════════════════════════════════════════════════

    async def get_status(self) -> Dict[str, Any]:
        """Hent samlet status for orkestratoren."""
        active_agents = sum(1 for a in self._agents.values() if a.is_active)
        available_agents = sum(1 for a in self._agents.values() if a.is_available)

        return {
            "orchestrator": "CKC Orchestrator",
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {
                "total": len(self._agents),
                "active": active_agents,
                "available": available_agents
            },
            "tasks": {
                "total": self._stats["total_tasks"],
                "completed": self._stats["completed_tasks"],
                "failed": self._stats["failed_tasks"],
                "queued": len(self._task_queue),
                "in_progress": sum(
                    1 for t in self._tasks.values()
                    if t.status == TaskStatus.IN_PROGRESS
                )
            },
            "validations": {
                "active": self._stats["active_validations"],
                "user_interventions": self._stats["user_interventions"]
            }
        }

    async def get_task_queue(self) -> List[Dict[str, Any]]:
        """Hent opgavekøen."""
        return [
            self._tasks[tid].to_dict()
            for tid in self._task_queue
            if tid in self._tasks
        ]


# ═══════════════════════════════════════════════════════════════
# SINGLETON & CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

_orchestrator: Optional[CKCOrchestrator] = None


def get_orchestrator() -> CKCOrchestrator:
    """Hent singleton CKCOrchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CKCOrchestrator()
    return _orchestrator


async def create_task(
    description: str,
    priority: TaskPriority = TaskPriority.MEDIUM,
    **kwargs
) -> Task:
    """Convenience function til at oprette opgave."""
    return await get_orchestrator().create_task(description, priority, **kwargs)


async def get_orchestrator_status() -> Dict[str, Any]:
    """Convenience function til at hente status."""
    return await get_orchestrator().get_status()


logger.info("CKC Orchestrator module loaded")
