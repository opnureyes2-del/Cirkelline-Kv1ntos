"""
Coordinator Agent
=================
Central mission coordination for the Cirkelline system.

Responsibilities:
- Receive missions from terminal/web/API
- Break down complex tasks into sub-tasks
- Assign tasks to specialist agents
- Track progress via SharedMemory
- Report completion/failure
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
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
    get_shared_memory,
)
from cirkelline.headquarters.knowledge_graph import (
    KnowledgeGraph,
    NodeType,
    EdgeType,
    get_knowledge_graph,
)
from cirkelline.context.agent_protocol import (
    AgentMessage,
    MessageType,
    AgentCapability,
    AgentDescriptor,
    create_agent_message,
    create_delegation_request,
    get_capability_registry,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SubTask:
    """A sub-task within a mission."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    required_capability: Optional[AgentCapability] = None
    assigned_agent: Optional[str] = None
    status: str = "pending"
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "required_capability": self.required_capability.value if self.required_capability else None,
            "assigned_agent": self.assigned_agent,
            "status": self.status,
            "dependencies": self.dependencies,
            "result": self.result,
            "created_at": self.created_at,
        }


@dataclass
class MissionPlan:
    """Execution plan for a mission."""
    mission_id: str
    tasks: List[SubTask] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "execution_order": self.execution_order,
            "parallel_groups": self.parallel_groups,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COORDINATOR AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class CoordinatorAgent:
    """
    Coordinates missions across the Cirkelline agent ecosystem.

    The Coordinator is the brain of HQ - it receives high-level missions,
    breaks them into executable tasks, assigns them to capable agents,
    and tracks overall progress.
    """

    AGENT_ID = "hq:coordinator"
    AGENT_NAME = "Mission Coordinator"

    def __init__(self):
        self._event_bus: Optional[EventBus] = None
        self._memory: Optional[SharedMemory] = None
        self._graph: Optional[KnowledgeGraph] = None
        self._running = False
        self._active_missions: Dict[str, MissionPlan] = {}

    async def initialize(self) -> bool:
        """Initialize connections to HQ infrastructure."""
        try:
            self._event_bus = get_event_bus()
            self._memory = get_shared_memory()
            self._graph = get_knowledge_graph()

            # Register self in capability registry
            registry = get_capability_registry()
            registry.register(AgentDescriptor(
                agent_id=self.AGENT_ID,
                name=self.AGENT_NAME,
                role="Mission coordination and task breakdown",
                capabilities=[AgentCapability.CONVERSATION],
                max_concurrent_tasks=10,
            ))

            # Subscribe to relevant events
            self._event_bus.subscribe(EventType.MISSION_CREATED, self._handle_new_mission)
            self._event_bus.subscribe(EventType.AGENT_HEARTBEAT, self._handle_agent_heartbeat)

            # Register in knowledge graph
            from cirkelline.headquarters.knowledge_graph import GraphNode
            self._graph.add_node(GraphNode(
                node_id=self.AGENT_ID,
                node_type=NodeType.AGENT,
                name=self.AGENT_NAME,
                properties={"role": "coordinator", "status": "active"},
            ))

            logger.info(f"CoordinatorAgent initialized: {self.AGENT_ID}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CoordinatorAgent: {e}")
            return False

    async def start(self) -> None:
        """Start the coordinator's main loop."""
        self._running = True
        logger.info("CoordinatorAgent started")

        while self._running:
            try:
                # Check for stalled missions
                await self._check_stalled_missions()

                # Process pending assignments
                await self._process_pending_assignments()

                await asyncio.sleep(5)  # Check every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Coordinator loop error: {e}")
                await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the coordinator."""
        self._running = False
        logger.info("CoordinatorAgent stopped")

    # ═══════════════════════════════════════════════════════════════════════════
    # MISSION HANDLING
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_mission(
        self,
        title: str,
        description: str,
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        priority: MissionPriority = MissionPriority.NORMAL,
    ) -> Mission:
        """
        Create and register a new mission.

        Args:
            title: Mission title
            description: What needs to be done
            context: Additional context (git, user, etc.)
            user_id: User who initiated the mission
            priority: Mission priority level

        Returns:
            Created Mission object
        """
        mission = Mission(
            mission_id=f"mission-{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            priority=priority,
            created_by=user_id,
            context=context,
        )

        # Store in shared memory
        await self._memory.create_mission(mission)

        # Publish creation event
        await self._event_bus.publish(Event(
            event_type=EventType.MISSION_CREATED,
            source=self.AGENT_ID,
            payload=mission.to_dict(),
        ))

        logger.info(f"Created mission: {mission.mission_id} - {title}")
        return mission

    async def plan_mission(self, mission_id: str) -> Optional[MissionPlan]:
        """
        Analyze mission and create execution plan.

        Breaks down the mission into sub-tasks based on:
        - Required capabilities
        - Task dependencies
        - Available agents
        """
        mission = await self._memory.get_mission(mission_id)
        if not mission:
            logger.warning(f"Mission not found: {mission_id}")
            return None

        plan = MissionPlan(mission_id=mission_id)

        # Analyze description to identify required capabilities
        tasks = self._analyze_requirements(mission.description, mission.context)
        plan.tasks = tasks

        # Determine execution order based on dependencies
        plan.execution_order = self._determine_order(tasks)

        # Group parallelizable tasks
        plan.parallel_groups = self._group_parallel_tasks(tasks)

        # Store plan
        self._active_missions[mission_id] = plan

        # Update mission with checkpoints
        await self._memory.update_mission(mission_id, {
            "checkpoints": [t.to_dict() for t in tasks],
        })

        logger.info(f"Planned mission {mission_id}: {len(tasks)} tasks")
        return plan

    def _analyze_requirements(
        self,
        description: str,
        context: Dict[str, Any],
    ) -> List[SubTask]:
        """Analyze mission to identify required sub-tasks."""
        tasks = []
        desc_lower = description.lower()

        # Research tasks
        if any(kw in desc_lower for kw in ["research", "find", "search", "lookup"]):
            tasks.append(SubTask(
                title="Research",
                description=f"Research: {description}",
                required_capability=AgentCapability.WEB_SEARCH,
            ))

        # Document processing
        if any(kw in desc_lower for kw in ["document", "pdf", "file", "read"]):
            tasks.append(SubTask(
                title="Document Processing",
                description=f"Process document: {description}",
                required_capability=AgentCapability.DOCUMENT_PROCESSING,
            ))

        # Image analysis
        if any(kw in desc_lower for kw in ["image", "photo", "picture", "screenshot"]):
            tasks.append(SubTask(
                title="Image Analysis",
                description=f"Analyze image: {description}",
                required_capability=AgentCapability.IMAGE_ANALYSIS,
            ))

        # Audio processing
        if any(kw in desc_lower for kw in ["audio", "voice", "sound", "transcribe"]):
            tasks.append(SubTask(
                title="Audio Processing",
                description=f"Process audio: {description}",
                required_capability=AgentCapability.AUDIO_TRANSCRIPTION,
            ))

        # Legal analysis
        if any(kw in desc_lower for kw in ["legal", "law", "contract", "compliance"]):
            tasks.append(SubTask(
                title="Legal Analysis",
                description=f"Legal analysis: {description}",
                required_capability=AgentCapability.LEGAL_ANALYSIS,
            ))

        # Code tasks
        if any(kw in desc_lower for kw in ["code", "programming", "debug", "implement"]):
            tasks.append(SubTask(
                title="Code Task",
                description=f"Code task: {description}",
                required_capability=AgentCapability.CODE_GENERATION,
            ))

        # Default: general conversation
        if not tasks:
            tasks.append(SubTask(
                title="General Task",
                description=description,
                required_capability=AgentCapability.CONVERSATION,
            ))

        return tasks

    def _determine_order(self, tasks: List[SubTask]) -> List[str]:
        """Determine execution order based on dependencies."""
        # Simple topological sort
        order = []
        remaining = {t.task_id: t for t in tasks}

        while remaining:
            # Find tasks with no unmet dependencies
            ready = [
                tid for tid, task in remaining.items()
                if all(dep in order for dep in task.dependencies)
            ]

            if not ready:
                # Break cycle by picking any
                ready = [list(remaining.keys())[0]]

            order.extend(ready)
            for tid in ready:
                del remaining[tid]

        return order

    def _group_parallel_tasks(self, tasks: List[SubTask]) -> List[List[str]]:
        """Group tasks that can run in parallel."""
        groups = []
        processed = set()

        for task in tasks:
            if task.task_id in processed:
                continue

            # Find tasks with same dependencies that can run together
            group = [task.task_id]
            processed.add(task.task_id)

            for other in tasks:
                if other.task_id in processed:
                    continue
                if set(other.dependencies) == set(task.dependencies):
                    group.append(other.task_id)
                    processed.add(other.task_id)

            groups.append(group)

        return groups

    # ═══════════════════════════════════════════════════════════════════════════
    # TASK ASSIGNMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def assign_tasks(self, mission_id: str) -> int:
        """
        Assign pending tasks to available agents.

        Returns number of tasks assigned.
        """
        plan = self._active_missions.get(mission_id)
        if not plan:
            return 0

        registry = get_capability_registry()
        assigned_count = 0

        for task in plan.tasks:
            if task.status != "pending" or task.assigned_agent:
                continue

            if not task.required_capability:
                continue

            # Find capable agents
            candidates = registry.find_by_capability(
                task.required_capability,
                exclude=[self.AGENT_ID],
            )

            if not candidates:
                logger.warning(f"No agent found for capability: {task.required_capability}")
                continue

            # Select best agent (simple: first available)
            available = [a for a in candidates if a.status == "idle"]
            agent = available[0] if available else candidates[0]

            # Assign task
            task.assigned_agent = agent.agent_id
            task.status = "assigned"

            # Send delegation request
            msg = create_delegation_request(
                sender=self.AGENT_ID,
                recipient=agent.agent_id,
                task=task.description,
                context={"task_id": task.task_id, "mission_id": mission_id},
                mission_id=mission_id,
            )

            await self._event_bus.publish(Event(
                event_type=EventType.MISSION_ASSIGNED,
                source=self.AGENT_ID,
                payload=msg.to_dict(),
            ))

            assigned_count += 1
            logger.info(f"Assigned task {task.task_id} to {agent.agent_id}")

        return assigned_count

    async def _process_pending_assignments(self) -> None:
        """Process all missions with pending task assignments."""
        for mission_id in list(self._active_missions.keys()):
            await self.assign_tasks(mission_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # PROGRESS TRACKING
    # ═══════════════════════════════════════════════════════════════════════════

    async def update_task_status(
        self,
        mission_id: str,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update status of a specific task."""
        plan = self._active_missions.get(mission_id)
        if not plan:
            return False

        for task in plan.tasks:
            if task.task_id == task_id:
                task.status = status
                if result:
                    task.result = result

                # Check if mission is complete
                await self._check_mission_completion(mission_id)
                return True

        return False

    async def _check_mission_completion(self, mission_id: str) -> None:
        """Check if all tasks are complete and update mission status."""
        plan = self._active_missions.get(mission_id)
        if not plan:
            return

        completed = sum(1 for t in plan.tasks if t.status == "completed")
        failed = sum(1 for t in plan.tasks if t.status == "failed")
        total = len(plan.tasks)

        # Calculate progress
        progress = completed / total if total > 0 else 0

        await self._memory.update_mission(mission_id, {"progress": progress})

        # Check completion
        if completed == total:
            await self._memory.transition_mission(mission_id, MissionStatus.COMPLETED)
            await self._event_bus.publish(Event(
                event_type=EventType.MISSION_COMPLETED,
                source=self.AGENT_ID,
                payload={"mission_id": mission_id},
            ))
            del self._active_missions[mission_id]
            logger.info(f"Mission completed: {mission_id}")

        elif failed > 0 and completed + failed == total:
            await self._memory.transition_mission(
                mission_id,
                MissionStatus.FAILED,
                error=f"{failed}/{total} tasks failed",
            )
            await self._event_bus.publish(Event(
                event_type=EventType.MISSION_FAILED,
                source=self.AGENT_ID,
                payload={"mission_id": mission_id, "failed_tasks": failed},
            ))
            del self._active_missions[mission_id]
            logger.warning(f"Mission failed: {mission_id}")

    async def _check_stalled_missions(self) -> None:
        """Check for missions that haven't progressed."""
        # TODO: Implement timeout detection and retry logic
        pass

    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _handle_new_mission(self, event: Event) -> None:
        """Handle new mission creation events."""
        mission_data = event.payload
        mission_id = mission_data.get("mission_id")

        if mission_id and mission_id not in self._active_missions:
            # Auto-plan new missions
            await self.plan_mission(mission_id)

    async def _handle_agent_heartbeat(self, event: Event) -> None:
        """Handle agent heartbeat events for availability tracking."""
        # Update agent availability in registry
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_coordinator_instance: Optional[CoordinatorAgent] = None


def get_coordinator() -> CoordinatorAgent:
    """Get the singleton CoordinatorAgent instance."""
    global _coordinator_instance

    if _coordinator_instance is None:
        _coordinator_instance = CoordinatorAgent()

    return _coordinator_instance


async def init_coordinator() -> CoordinatorAgent:
    """Initialize and start the coordinator."""
    coordinator = get_coordinator()
    await coordinator.initialize()
    return coordinator
