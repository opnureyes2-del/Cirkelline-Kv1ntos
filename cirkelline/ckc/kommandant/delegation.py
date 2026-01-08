"""
CKC Delegation Module
=====================

Avanceret opgavedelegering og planlægning for Kommandanten.

Features:
    - Intelligent specialist-udvælgelse
    - Opgaveprioritering og -planlægning
    - Load balancing på tværs af specialister
    - Fallback-strategier ved fejl
    - Parallel vs. sekventiel udførelse

Usage:
    from cirkelline.ckc.kommandant.delegation import (
        TaskPlanner,
        DelegationEngine,
        SpecialistSelector,
    )
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import uuid

from .core import (
    DelegationStrategy,
    TaskPriority,
    TaskAnalysis,
    DelegationRecord,
    CAPABILITY_TO_SPECIALIST,
    SPECIALIST_CAPABILITIES,
)

logger = logging.getLogger(__name__)


# ========== Enums ==========

class SpecialistAvailability(Enum):
    """Specialist tilgængelighed."""
    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"


class ExecutionMode(Enum):
    """Opgaveudførelsesmode."""
    IMMEDIATE = "immediate"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    BATCHED = "batched"


# ========== Data Classes ==========

@dataclass
class SpecialistInfo:
    """Information om en specialist."""
    specialist_id: str
    specialist_type: str
    capabilities: List[str]
    availability: SpecialistAvailability
    current_load: int  # Number of active tasks
    max_load: int  # Maximum concurrent tasks
    performance_score: float  # 0.0 - 1.0
    last_task_time: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0

    @property
    def success_rate(self) -> float:
        total = self.failure_count + self.success_count
        return self.success_count / max(1, total)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specialist_id": self.specialist_id,
            "specialist_type": self.specialist_type,
            "capabilities": self.capabilities,
            "availability": self.availability.value,
            "current_load": self.current_load,
            "max_load": self.max_load,
            "performance_score": self.performance_score,
            "success_rate": self.success_rate
        }


@dataclass
class TaskPlan:
    """Plan for opgaveudførelse."""
    plan_id: str
    task_id: str
    execution_mode: ExecutionMode
    delegation_strategy: DelegationStrategy
    steps: List[Dict[str, Any]]
    estimated_duration_seconds: int
    priority: TaskPriority
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "execution_mode": self.execution_mode.value,
            "delegation_strategy": self.delegation_strategy.value,
            "steps": self.steps,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class DelegationResult:
    """Resultat af en delegering."""
    delegation_id: str
    specialist_id: str
    success: bool
    output: Optional[Dict[str, Any]]
    error: Optional[str]
    duration_seconds: float
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ========== Specialist Selector ==========

class SpecialistSelector:
    """
    Intelligent udvælgelse af specialister baseret på:
        - Kapabiliteter
        - Tilgængelighed
        - Performance historie
        - Load balancing
    """

    def __init__(self):
        self._specialists: Dict[str, SpecialistInfo] = {}
        self._capability_index: Dict[str, List[str]] = {}  # capability -> specialist_ids

        # Initialize default specialists
        self._init_default_specialists()

    def _init_default_specialists(self) -> None:
        """Initialize default specialist configurations."""
        for specialist_type, capabilities in SPECIALIST_CAPABILITIES.items():
            specialist_id = f"{specialist_type}_default"
            self.register_specialist(
                specialist_id=specialist_id,
                specialist_type=specialist_type,
                capabilities=capabilities,
                max_load=5
            )

    def register_specialist(
        self,
        specialist_id: str,
        specialist_type: str,
        capabilities: List[str],
        max_load: int = 5
    ) -> SpecialistInfo:
        """Registrer en ny specialist."""
        info = SpecialistInfo(
            specialist_id=specialist_id,
            specialist_type=specialist_type,
            capabilities=capabilities,
            availability=SpecialistAvailability.AVAILABLE,
            current_load=0,
            max_load=max_load,
            performance_score=0.8
        )

        self._specialists[specialist_id] = info

        # Update capability index
        for cap in capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            if specialist_id not in self._capability_index[cap]:
                self._capability_index[cap].append(specialist_id)

        logger.info(f"Registered specialist: {specialist_id} ({specialist_type})")
        return info

    def select_specialist(
        self,
        required_capability: str,
        prefer_performance: bool = True
    ) -> Optional[str]:
        """
        Select best specialist for a capability.

        Args:
            required_capability: Required capability
            prefer_performance: Prefer higher performing specialists

        Returns:
            specialist_id or None
        """
        # Find specialists with capability
        specialist_ids = self._capability_index.get(required_capability, [])

        if not specialist_ids:
            # Try to find via mapping
            specialist_type = CAPABILITY_TO_SPECIALIST.get(required_capability)
            if specialist_type:
                # Find any specialist of this type
                for sid, info in self._specialists.items():
                    if info.specialist_type == specialist_type:
                        specialist_ids.append(sid)

        if not specialist_ids:
            logger.warning(f"No specialist found for capability: {required_capability}")
            return None

        # Filter by availability
        available = []
        for sid in specialist_ids:
            info = self._specialists.get(sid)
            if info and info.availability in [SpecialistAvailability.AVAILABLE, SpecialistAvailability.BUSY]:
                if info.current_load < info.max_load:
                    available.append(info)

        if not available:
            logger.warning(f"No available specialist for: {required_capability}")
            # Return first one anyway (for MVP)
            return specialist_ids[0] if specialist_ids else None

        # Sort by criteria
        if prefer_performance:
            available.sort(key=lambda x: (-x.performance_score, x.current_load))
        else:
            available.sort(key=lambda x: x.current_load)

        selected = available[0]
        logger.debug(f"Selected specialist {selected.specialist_id} for {required_capability}")
        return selected.specialist_id

    def select_specialists_for_capabilities(
        self,
        capabilities: List[str]
    ) -> Dict[str, str]:
        """
        Select specialists for multiple capabilities.

        Returns:
            Dict mapping capability -> specialist_id
        """
        result = {}
        for cap in capabilities:
            specialist_id = self.select_specialist(cap)
            if specialist_id:
                result[cap] = specialist_id
        return result

    def update_load(self, specialist_id: str, delta: int) -> None:
        """Update specialist load."""
        if specialist_id in self._specialists:
            info = self._specialists[specialist_id]
            info.current_load = max(0, info.current_load + delta)

            # Update availability based on load
            if info.current_load >= info.max_load:
                info.availability = SpecialistAvailability.OVERLOADED
            elif info.current_load > 0:
                info.availability = SpecialistAvailability.BUSY
            else:
                info.availability = SpecialistAvailability.AVAILABLE

    def record_result(
        self,
        specialist_id: str,
        success: bool,
        duration_seconds: float
    ) -> None:
        """Record task result for specialist."""
        if specialist_id in self._specialists:
            info = self._specialists[specialist_id]
            if success:
                info.success_count += 1
            else:
                info.failure_count += 1
            info.last_task_time = datetime.now(timezone.utc)

            # Update performance score (exponential moving average)
            result_score = 1.0 if success else 0.0
            info.performance_score = 0.9 * info.performance_score + 0.1 * result_score

    def get_specialist_info(self, specialist_id: str) -> Optional[SpecialistInfo]:
        """Get specialist information."""
        return self._specialists.get(specialist_id)

    def list_specialists(self) -> List[Dict[str, Any]]:
        """List all registered specialists."""
        return [info.to_dict() for info in self._specialists.values()]


# ========== Task Planner ==========

class TaskPlanner:
    """
    Planlæg opgaveudførelse baseret på analyse.

    Ansvar:
        - Bestem udførelsesrækkefølge
        - Håndter afhængigheder
        - Optimer ressourceforbrug
    """

    def __init__(self, specialist_selector: Optional[SpecialistSelector] = None):
        self.selector = specialist_selector or SpecialistSelector()

    def create_plan(
        self,
        task_id: str,
        analysis: TaskAnalysis,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> TaskPlan:
        """
        Create execution plan for a task.

        Args:
            task_id: Task ID
            analysis: Task analysis
            priority: Task priority

        Returns:
            TaskPlan
        """
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        steps = []

        # Select specialists for each capability
        capability_specialists = self.selector.select_specialists_for_capabilities(
            analysis.required_capabilities
        )

        # Build steps based on strategy
        if analysis.delegation_strategy == DelegationStrategy.SINGLE_SPECIALIST:
            steps = self._create_single_steps(capability_specialists, analysis)
        elif analysis.delegation_strategy == DelegationStrategy.PARALLEL_SPECIALISTS:
            steps = self._create_parallel_steps(capability_specialists, analysis)
        elif analysis.delegation_strategy == DelegationStrategy.SEQUENTIAL_PIPELINE:
            steps = self._create_sequential_steps(capability_specialists, analysis)
        elif analysis.delegation_strategy == DelegationStrategy.COLLABORATIVE:
            steps = self._create_collaborative_steps(capability_specialists, analysis)

        # Determine execution mode
        if priority == TaskPriority.CRITICAL:
            execution_mode = ExecutionMode.IMMEDIATE
        elif len(steps) > 3:
            execution_mode = ExecutionMode.BATCHED
        else:
            execution_mode = ExecutionMode.QUEUED

        plan = TaskPlan(
            plan_id=plan_id,
            task_id=task_id,
            execution_mode=execution_mode,
            delegation_strategy=analysis.delegation_strategy,
            steps=steps,
            estimated_duration_seconds=analysis.estimated_duration_seconds,
            priority=priority
        )

        logger.info(f"Created plan {plan_id} with {len(steps)} steps")
        return plan

    def _create_single_steps(
        self,
        capability_specialists: Dict[str, str],
        analysis: TaskAnalysis
    ) -> List[Dict[str, Any]]:
        """Create steps for single specialist execution."""
        if not capability_specialists:
            return []

        # Use first capability's specialist
        cap = analysis.required_capabilities[0]
        specialist_id = capability_specialists.get(cap)

        if not specialist_id:
            return []

        return [{
            "step_id": f"step_{uuid.uuid4().hex[:8]}",
            "step_number": 1,
            "specialist_id": specialist_id,
            "capability": cap,
            "parallel": False,
            "depends_on": []
        }]

    def _create_parallel_steps(
        self,
        capability_specialists: Dict[str, str],
        analysis: TaskAnalysis
    ) -> List[Dict[str, Any]]:
        """Create steps for parallel execution."""
        steps = []
        for i, (cap, specialist_id) in enumerate(capability_specialists.items()):
            steps.append({
                "step_id": f"step_{uuid.uuid4().hex[:8]}",
                "step_number": 1,  # All same step number = parallel
                "specialist_id": specialist_id,
                "capability": cap,
                "parallel": True,
                "depends_on": []
            })
        return steps

    def _create_sequential_steps(
        self,
        capability_specialists: Dict[str, str],
        analysis: TaskAnalysis
    ) -> List[Dict[str, Any]]:
        """Create steps for sequential pipeline."""
        steps = []
        previous_step_id = None

        for i, (cap, specialist_id) in enumerate(capability_specialists.items()):
            step_id = f"step_{uuid.uuid4().hex[:8]}"
            steps.append({
                "step_id": step_id,
                "step_number": i + 1,
                "specialist_id": specialist_id,
                "capability": cap,
                "parallel": False,
                "depends_on": [previous_step_id] if previous_step_id else []
            })
            previous_step_id = step_id

        return steps

    def _create_collaborative_steps(
        self,
        capability_specialists: Dict[str, str],
        analysis: TaskAnalysis
    ) -> List[Dict[str, Any]]:
        """Create steps for collaborative execution."""
        # Collaborative: All work on same input, results merged
        steps = []
        step_ids = []

        # First: All specialists work in parallel
        for cap, specialist_id in capability_specialists.items():
            step_id = f"step_{uuid.uuid4().hex[:8]}"
            step_ids.append(step_id)
            steps.append({
                "step_id": step_id,
                "step_number": 1,
                "specialist_id": specialist_id,
                "capability": cap,
                "parallel": True,
                "depends_on": []
            })

        # Then: Merge step (virtual)
        steps.append({
            "step_id": f"step_{uuid.uuid4().hex[:8]}",
            "step_number": 2,
            "specialist_id": "merger",
            "capability": "merge_results",
            "parallel": False,
            "depends_on": step_ids
        })

        return steps


# ========== Delegation Engine ==========

class DelegationEngine:
    """
    Motor til at udføre delegerede opgaver.

    Features:
        - Udfør planer
        - Håndter fejl og retries
        - Rapportér fremskridt
    """

    def __init__(
        self,
        selector: Optional[SpecialistSelector] = None,
        planner: Optional[TaskPlanner] = None
    ):
        self.selector = selector or SpecialistSelector()
        self.planner = planner or TaskPlanner(self.selector)

        self._active_delegations: Dict[str, DelegationRecord] = {}
        self._results: Dict[str, DelegationResult] = {}

        # Callbacks
        self._on_progress: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None

    def set_callbacks(
        self,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None
    ) -> None:
        """Set event callbacks."""
        self._on_progress = on_progress
        self._on_complete = on_complete

    async def execute_plan(
        self,
        plan: TaskPlan,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a task plan.

        Args:
            plan: Task execution plan
            input_data: Input data for the task

        Returns:
            Dict with aggregated results
        """
        logger.info(f"Executing plan {plan.plan_id}")
        results = {}
        errors = []

        # Group steps by step_number for parallel execution
        step_groups: Dict[int, List[Dict]] = {}
        for step in plan.steps:
            step_num = step["step_number"]
            if step_num not in step_groups:
                step_groups[step_num] = []
            step_groups[step_num].append(step)

        # Execute in order
        for step_num in sorted(step_groups.keys()):
            steps = step_groups[step_num]

            if len(steps) > 1 and steps[0].get("parallel", False):
                # Execute in parallel
                step_results = await self._execute_parallel(steps, input_data, results)
            else:
                # Execute sequentially
                step_results = await self._execute_sequential(steps, input_data, results)

            results.update(step_results)

            # Check for errors
            for step in steps:
                result = step_results.get(step["step_id"])
                if result and not result.get("success", False):
                    errors.append({
                        "step_id": step["step_id"],
                        "specialist_id": step["specialist_id"],
                        "error": result.get("error")
                    })

            # Report progress
            if self._on_progress:
                progress = step_num / len(step_groups)
                await self._on_progress(plan.task_id, progress)

        # Aggregate final result
        success = len(errors) == 0 or len(errors) < len(plan.steps) / 2
        final_result = {
            "success": success,
            "results": results,
            "errors": errors if errors else None,
            "steps_completed": len(plan.steps) - len(errors),
            "steps_total": len(plan.steps)
        }

        if self._on_complete:
            await self._on_complete(plan.task_id, final_result)

        return final_result

    async def _execute_parallel(
        self,
        steps: List[Dict],
        input_data: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute steps in parallel."""
        tasks = []
        for step in steps:
            task = self._execute_step(step, input_data, previous_results)
            tasks.append(task)

        step_results = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for step, result in zip(steps, step_results):
            if isinstance(result, Exception):
                results[step["step_id"]] = {
                    "success": False,
                    "error": str(result)
                }
            else:
                results[step["step_id"]] = result

        return results

    async def _execute_sequential(
        self,
        steps: List[Dict],
        input_data: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute steps sequentially."""
        results = {}

        for step in steps:
            # Include previous step results for dependencies
            combined_input = {**input_data}
            for dep_id in step.get("depends_on", []):
                if dep_id in previous_results:
                    combined_input[f"from_{dep_id}"] = previous_results[dep_id]

            result = await self._execute_step(step, combined_input, previous_results)
            results[step["step_id"]] = result

        return results

    async def _execute_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single step."""
        step_id = step["step_id"]
        specialist_id = step["specialist_id"]

        # Special case: merger step
        if specialist_id == "merger":
            return await self._merge_results(step, previous_results)

        # Update load
        self.selector.update_load(specialist_id, 1)

        start_time = datetime.now(timezone.utc)

        try:
            # Execute specialist task (simulated for MVP)
            result = await self._invoke_specialist(specialist_id, input_data)

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Record success
            self.selector.record_result(specialist_id, True, duration)

            return {
                "success": True,
                "specialist_id": specialist_id,
                "output": result,
                "duration_seconds": duration
            }

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.selector.record_result(specialist_id, False, duration)

            logger.error(f"Step {step_id} failed: {e}")
            return {
                "success": False,
                "specialist_id": specialist_id,
                "error": str(e),
                "duration_seconds": duration
            }

        finally:
            self.selector.update_load(specialist_id, -1)

    async def _invoke_specialist(
        self,
        specialist_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke a specialist (simulated for MVP).

        In full implementation, this would:
        - Send message via Message Bus
        - Wait for response
        - Handle timeouts
        """
        # Simulate processing
        await asyncio.sleep(0.3)

        return {
            "type": specialist_id,
            "processed": True,
            "summary": f"Processed by {specialist_id}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def _merge_results(
        self,
        step: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge results from parallel steps."""
        merged = {}

        for dep_id in step.get("depends_on", []):
            if dep_id in previous_results:
                result = previous_results[dep_id]
                if isinstance(result, dict):
                    output = result.get("output", {})
                    specialist = result.get("specialist_id", "unknown")
                    merged[specialist] = output

        return {
            "success": True,
            "specialist_id": "merger",
            "output": {
                "merged_results": merged,
                "source_count": len(merged)
            }
        }


# ========== Module Factory ==========

_default_selector: Optional[SpecialistSelector] = None
_default_planner: Optional[TaskPlanner] = None
_default_engine: Optional[DelegationEngine] = None


def get_specialist_selector() -> SpecialistSelector:
    """Get or create default specialist selector."""
    global _default_selector
    if _default_selector is None:
        _default_selector = SpecialistSelector()
    return _default_selector


def get_task_planner() -> TaskPlanner:
    """Get or create default task planner."""
    global _default_planner
    if _default_planner is None:
        _default_planner = TaskPlanner(get_specialist_selector())
    return _default_planner


def get_delegation_engine() -> DelegationEngine:
    """Get or create default delegation engine."""
    global _default_engine
    if _default_engine is None:
        _default_engine = DelegationEngine(
            get_specialist_selector(),
            get_task_planner()
        )
    return _default_engine


logger.info("CKC Delegation module loaded")
