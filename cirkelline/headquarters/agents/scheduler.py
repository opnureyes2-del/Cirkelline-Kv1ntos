"""
Scheduler Agent
===============
Task prioritization and workload balancing.

Responsibilities:
- Prioritize pending missions
- Balance agent workload
- Handle deadlines
- Retry failed tasks
- Queue management
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from heapq import heappush, heappop
import uuid

from cirkelline.headquarters.event_bus import (
    EventBus,
    Event,
    EventType,
    get_event_bus,
)
from cirkelline.headquarters.shared_memory import (
    SharedMemory,
    Mission,
    MissionStatus,
    MissionPriority,
    AgentState,
    get_shared_memory,
)
from cirkelline.context.agent_protocol import (
    AgentDescriptor,
    get_capability_registry,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEDULING STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ScheduledTask:
    """A task in the scheduling queue."""
    task_id: str
    mission_id: str
    priority: int  # Lower = higher priority
    scheduled_at: str
    deadline: Optional[str] = None
    retries: int = 0
    max_retries: int = 3

    def __lt__(self, other: "ScheduledTask") -> bool:
        """Comparison for heap ordering."""
        return self.priority < other.priority


@dataclass
class AgentWorkload:
    """Tracks workload for an agent."""
    agent_id: str
    current_tasks: int = 0
    max_tasks: int = 1
    completed_today: int = 0
    failed_today: int = 0
    avg_completion_time_ms: float = 0.0
    last_assignment: Optional[str] = None

    @property
    def utilization(self) -> float:
        """Calculate utilization percentage."""
        return self.current_tasks / self.max_tasks if self.max_tasks > 0 else 0.0

    @property
    def is_available(self) -> bool:
        """Check if agent can accept more tasks."""
        return self.current_tasks < self.max_tasks


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEDULER AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class SchedulerAgent:
    """
    Manages task scheduling and workload distribution.

    Uses priority queue for task ordering and tracks agent
    workload to ensure fair distribution.
    """

    AGENT_ID = "hq:scheduler"
    AGENT_NAME = "Task Scheduler"

    # Scheduling interval in seconds
    SCHEDULE_INTERVAL = 10

    # Priority weights
    PRIORITY_WEIGHTS = {
        MissionPriority.CRITICAL: 0,
        MissionPriority.HIGH: 10,
        MissionPriority.NORMAL: 50,
        MissionPriority.LOW: 100,
    }

    def __init__(self):
        self._event_bus: Optional[EventBus] = None
        self._memory: Optional[SharedMemory] = None
        self._running = False

        # Priority queue for tasks
        self._task_queue: List[ScheduledTask] = []

        # Agent workload tracking
        self._workloads: Dict[str, AgentWorkload] = {}

        # Retry queue
        self._retry_queue: List[Tuple[datetime, ScheduledTask]] = []

    async def initialize(self) -> bool:
        """Initialize connections."""
        try:
            self._event_bus = get_event_bus()
            self._memory = get_shared_memory()

            # Register self
            registry = get_capability_registry()
            registry.register(AgentDescriptor(
                agent_id=self.AGENT_ID,
                name=self.AGENT_NAME,
                role="Task scheduling and workload balancing",
                capabilities=[],
                max_concurrent_tasks=1,
            ))

            # Subscribe to events
            self._event_bus.subscribe(EventType.MISSION_CREATED, self._handle_mission_created)
            self._event_bus.subscribe(EventType.MISSION_COMPLETED, self._handle_mission_completed)
            self._event_bus.subscribe(EventType.MISSION_FAILED, self._handle_mission_failed)
            self._event_bus.subscribe(EventType.AGENT_REGISTERED, self._handle_agent_registered)

            logger.info(f"SchedulerAgent initialized: {self.AGENT_ID}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize SchedulerAgent: {e}")
            return False

    async def start(self) -> None:
        """Start the scheduling loop."""
        self._running = True
        logger.info("SchedulerAgent started")

        while self._running:
            try:
                await self._process_retry_queue()
                await self._schedule_pending_tasks()
                await self._rebalance_workloads()

                await asyncio.sleep(self.SCHEDULE_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop scheduling."""
        self._running = False
        logger.info("SchedulerAgent stopped")

    # ═══════════════════════════════════════════════════════════════════════════
    # QUEUE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def enqueue_task(
        self,
        mission_id: str,
        priority: MissionPriority = MissionPriority.NORMAL,
        deadline: Optional[str] = None,
    ) -> ScheduledTask:
        """Add a task to the scheduling queue."""
        task = ScheduledTask(
            task_id=f"task-{uuid.uuid4().hex[:8]}",
            mission_id=mission_id,
            priority=self.PRIORITY_WEIGHTS.get(priority, 50),
            scheduled_at=datetime.utcnow().isoformat(),
            deadline=deadline,
        )

        heappush(self._task_queue, task)
        logger.debug(f"Enqueued task {task.task_id} for mission {mission_id}")
        return task

    def dequeue_task(self) -> Optional[ScheduledTask]:
        """Get the highest priority task from queue."""
        if not self._task_queue:
            return None

        return heappop(self._task_queue)

    def peek_task(self) -> Optional[ScheduledTask]:
        """Look at highest priority task without removing."""
        if not self._task_queue:
            return None
        return self._task_queue[0]

    @property
    def queue_length(self) -> int:
        """Get current queue length."""
        return len(self._task_queue)

    # ═══════════════════════════════════════════════════════════════════════════
    # WORKLOAD MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def register_agent(
        self,
        agent_id: str,
        max_tasks: int = 1,
    ) -> AgentWorkload:
        """Register an agent for workload tracking."""
        if agent_id not in self._workloads:
            self._workloads[agent_id] = AgentWorkload(
                agent_id=agent_id,
                max_tasks=max_tasks,
            )
        return self._workloads[agent_id]

    def get_workload(self, agent_id: str) -> Optional[AgentWorkload]:
        """Get workload info for an agent."""
        return self._workloads.get(agent_id)

    def assign_to_agent(self, agent_id: str) -> bool:
        """Mark agent as having a new task."""
        workload = self._workloads.get(agent_id)
        if workload and workload.is_available:
            workload.current_tasks += 1
            workload.last_assignment = datetime.utcnow().isoformat()
            return True
        return False

    def release_agent(self, agent_id: str, success: bool = True) -> None:
        """Mark agent task as completed."""
        workload = self._workloads.get(agent_id)
        if workload:
            workload.current_tasks = max(0, workload.current_tasks - 1)
            if success:
                workload.completed_today += 1
            else:
                workload.failed_today += 1

    def get_available_agents(self) -> List[str]:
        """Get list of agents that can accept tasks."""
        return [
            agent_id for agent_id, workload in self._workloads.items()
            if workload.is_available
        ]

    def get_least_loaded_agent(self) -> Optional[str]:
        """Get the agent with lowest utilization."""
        available = [
            (workload.utilization, agent_id)
            for agent_id, workload in self._workloads.items()
            if workload.is_available
        ]

        if not available:
            return None

        available.sort()
        return available[0][1]

    # ═══════════════════════════════════════════════════════════════════════════
    # SCHEDULING LOGIC
    # ═══════════════════════════════════════════════════════════════════════════

    async def _schedule_pending_tasks(self) -> None:
        """Process queue and schedule tasks to available agents."""
        scheduled_count = 0

        while self._task_queue:
            # Check for available agents
            agent_id = self.get_least_loaded_agent()
            if not agent_id:
                break

            # Get next task
            task = self.dequeue_task()
            if not task:
                break

            # Check deadline
            if task.deadline:
                deadline = datetime.fromisoformat(task.deadline)
                if deadline < datetime.utcnow():
                    logger.warning(f"Task {task.task_id} missed deadline, skipping")
                    continue

            # Assign to agent
            if self.assign_to_agent(agent_id):
                await self._event_bus.publish(Event(
                    event_type=EventType.MISSION_ASSIGNED,
                    source=self.AGENT_ID,
                    payload={
                        "task_id": task.task_id,
                        "mission_id": task.mission_id,
                        "agent_id": agent_id,
                    },
                ))
                scheduled_count += 1
                logger.info(f"Scheduled task {task.task_id} to {agent_id}")
            else:
                # Re-queue if assignment failed
                heappush(self._task_queue, task)

        if scheduled_count > 0:
            logger.info(f"Scheduled {scheduled_count} tasks")

    async def _process_retry_queue(self) -> None:
        """Process tasks waiting for retry."""
        now = datetime.utcnow()

        while self._retry_queue:
            retry_at, task = self._retry_queue[0]
            if retry_at > now:
                break

            self._retry_queue.pop(0)

            if task.retries < task.max_retries:
                task.retries += 1
                heappush(self._task_queue, task)
                logger.info(f"Retrying task {task.task_id} (attempt {task.retries})")
            else:
                logger.warning(f"Task {task.task_id} exceeded max retries")

    async def _rebalance_workloads(self) -> None:
        """Rebalance work across agents if needed."""
        # Calculate average utilization
        if not self._workloads:
            return

        utilizations = [w.utilization for w in self._workloads.values()]
        avg_util = sum(utilizations) / len(utilizations)

        # Check for imbalance (>30% difference)
        max_util = max(utilizations)
        min_util = min(utilizations)

        if max_util - min_util > 0.3:
            logger.info(f"Workload imbalance detected: {min_util:.0%} - {max_util:.0%}")
            # TODO: Implement task redistribution

    # ═══════════════════════════════════════════════════════════════════════════
    # RETRY HANDLING
    # ═══════════════════════════════════════════════════════════════════════════

    def schedule_retry(
        self,
        task: ScheduledTask,
        delay_seconds: int = 30,
    ) -> None:
        """Schedule a task for retry after delay."""
        retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        self._retry_queue.append((retry_at, task))
        self._retry_queue.sort(key=lambda x: x[0])
        logger.info(f"Scheduled retry for task {task.task_id} in {delay_seconds}s")

    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _handle_mission_created(self, event: Event) -> None:
        """Handle new mission events."""
        mission_data = event.payload
        mission_id = mission_data.get("mission_id")
        priority_str = mission_data.get("priority", "normal")

        priority = MissionPriority(priority_str) if priority_str in [p.value for p in MissionPriority] else MissionPriority.NORMAL

        self.enqueue_task(
            mission_id=mission_id,
            priority=priority,
            deadline=mission_data.get("deadline"),
        )

    async def _handle_mission_completed(self, event: Event) -> None:
        """Handle mission completion."""
        agent_id = event.payload.get("agent_id")
        if agent_id:
            self.release_agent(agent_id, success=True)

    async def _handle_mission_failed(self, event: Event) -> None:
        """Handle mission failure."""
        agent_id = event.payload.get("agent_id")
        task_id = event.payload.get("task_id")

        if agent_id:
            self.release_agent(agent_id, success=False)

        # TODO: Find task and schedule retry if applicable

    async def _handle_agent_registered(self, event: Event) -> None:
        """Handle new agent registration."""
        agent_data = event.payload
        agent_id = agent_data.get("agent_id")
        max_tasks = agent_data.get("max_concurrent_tasks", 1)

        if agent_id:
            self.register_agent(agent_id, max_tasks)

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "queue_length": self.queue_length,
            "retry_queue_length": len(self._retry_queue),
            "agents_tracked": len(self._workloads),
            "available_agents": len(self.get_available_agents()),
            "total_utilization": sum(w.utilization for w in self._workloads.values()) / len(self._workloads) if self._workloads else 0,
            "workloads": {
                aid: {
                    "current": w.current_tasks,
                    "max": w.max_tasks,
                    "utilization": f"{w.utilization:.0%}",
                    "completed_today": w.completed_today,
                    "failed_today": w.failed_today,
                }
                for aid, w in self._workloads.items()
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_scheduler_instance: Optional[SchedulerAgent] = None


def get_scheduler() -> SchedulerAgent:
    """Get the singleton SchedulerAgent instance."""
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = SchedulerAgent()

    return _scheduler_instance


async def init_scheduler() -> SchedulerAgent:
    """Initialize and start the scheduler."""
    scheduler = get_scheduler()
    await scheduler.initialize()
    return scheduler
