"""
Shared Memory (Redis)
=====================
Distributed state management for Cirkelline agents.

Uses Redis for:
- Mission state coordination
- Global roadmap storage
- Agent status caching
- Lock management

Data Structures:
- Missions: Active tasks with state machine
- Roadmaps: Multi-step plans with checkpoints
- Agent States: Real-time agent status
- Locks: Distributed mutex for coordination
"""

import json
import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import uuid

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# MISSION STATUS
# ═══════════════════════════════════════════════════════════════════════════════

class MissionStatus(str, Enum):
    """Status states for missions."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MissionPriority(str, Enum):
    """Priority levels for missions."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Mission:
    """
    A coordinated task in the Cirkelline system.

    Missions are multi-step tasks that may involve multiple agents
    and require state tracking and coordination.
    """
    mission_id: str
    title: str
    description: str
    status: MissionStatus = MissionStatus.PENDING
    priority: MissionPriority = MissionPriority.NORMAL
    assigned_agents: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deadline: Optional[str] = None
    progress: float = 0.0
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "mission_id": self.mission_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, MissionStatus) else self.status,
            "priority": self.priority.value if isinstance(self.priority, MissionPriority) else self.priority,
            "assigned_agents": self.assigned_agents,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "deadline": self.deadline,
            "progress": self.progress,
            "checkpoints": self.checkpoints,
            "context": self.context,
            "result": self.result,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mission":
        """Reconstruct from dictionary."""
        status = data.get("status", "pending")
        priority = data.get("priority", "normal")

        return cls(
            mission_id=data["mission_id"],
            title=data["title"],
            description=data.get("description", ""),
            status=MissionStatus(status) if status in [s.value for s in MissionStatus] else status,
            priority=MissionPriority(priority) if priority in [p.value for p in MissionPriority] else priority,
            assigned_agents=data.get("assigned_agents", []),
            created_by=data.get("created_by"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            deadline=data.get("deadline"),
            progress=data.get("progress", 0.0),
            checkpoints=data.get("checkpoints", []),
            context=data.get("context", {}),
            result=data.get("result"),
            error=data.get("error"),
        )


@dataclass
class Roadmap:
    """
    A multi-step plan for achieving a goal.

    Roadmaps define the sequence of actions and milestones
    required to complete a complex task.
    """
    roadmap_id: str
    name: str
    description: str
    owner: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    status: str = "draft"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "roadmap_id": self.roadmap_id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "steps": self.steps,
            "current_step": self.current_step,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Roadmap":
        """Reconstruct from dictionary."""
        return cls(
            roadmap_id=data["roadmap_id"],
            name=data["name"],
            description=data.get("description", ""),
            owner=data["owner"],
            steps=data.get("steps", []),
            current_step=data.get("current_step", 0),
            status=data.get("status", "draft"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AgentState:
    """Real-time state of an agent."""
    agent_id: str
    status: str = "idle"
    current_mission: Optional[str] = None
    workload: float = 0.0
    last_heartbeat: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_mission": self.current_mission,
            "workload": self.workload,
            "last_heartbeat": self.last_heartbeat,
            "metrics": self.metrics,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED MEMORY
# ═══════════════════════════════════════════════════════════════════════════════

class SharedMemory:
    """
    Redis-backed distributed state management.

    Provides:
    - Mission CRUD and state transitions
    - Roadmap storage and management
    - Agent state caching
    - Distributed locks
    - Pub/Sub for state changes
    """

    # Redis key prefixes
    MISSIONS_KEY = "cirkelline:missions"
    ROADMAPS_KEY = "cirkelline:roadmaps"
    AGENTS_KEY = "cirkelline:agents"
    LOCKS_KEY = "cirkelline:locks"
    COUNTERS_KEY = "cirkelline:counters"

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_lock_timeout: int = 30,
    ):
        self.redis_url = redis_url
        self.default_lock_timeout = default_lock_timeout
        self._redis: Optional[aioredis.Redis] = None
        self._local_cache: Dict[str, Any] = {}
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Redis."""
        if aioredis is None:
            logger.warning("redis.asyncio not available - using local memory")
            self._connected = False
            return False

        try:
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            self._connected = True
            logger.info(f"SharedMemory connected to Redis: {self.redis_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._connected = False
        logger.info("SharedMemory disconnected")

    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected and self._redis is not None

    # ═══════════════════════════════════════════════════════════════════════════
    # MISSION OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_mission(self, mission: Mission) -> str:
        """
        Create a new mission.

        Args:
            mission: Mission to create

        Returns:
            Mission ID
        """
        key = f"{self.MISSIONS_KEY}:{mission.mission_id}"

        if self.is_connected:
            await self._redis.hset(key, mapping={
                "data": json.dumps(mission.to_dict()),
            })
            await self._redis.sadd(f"{self.MISSIONS_KEY}:index", mission.mission_id)
        else:
            self._local_cache[key] = mission.to_dict()

        logger.info(f"Created mission: {mission.mission_id}")
        return mission.mission_id

    async def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Get a mission by ID."""
        key = f"{self.MISSIONS_KEY}:{mission_id}"

        if self.is_connected:
            data = await self._redis.hget(key, "data")
            if data:
                return Mission.from_dict(json.loads(data))
        else:
            if key in self._local_cache:
                return Mission.from_dict(self._local_cache[key])

        return None

    async def update_mission(
        self,
        mission_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update mission fields.

        Args:
            mission_id: Mission to update
            updates: Fields to update

        Returns:
            True if successful
        """
        mission = await self.get_mission(mission_id)
        if not mission:
            return False

        # Apply updates
        mission_dict = mission.to_dict()
        mission_dict.update(updates)
        mission_dict["updated_at"] = datetime.utcnow().isoformat()

        key = f"{self.MISSIONS_KEY}:{mission_id}"

        if self.is_connected:
            await self._redis.hset(key, mapping={
                "data": json.dumps(mission_dict),
            })
        else:
            self._local_cache[key] = mission_dict

        return True

    async def transition_mission(
        self,
        mission_id: str,
        new_status: MissionStatus,
        **kwargs,
    ) -> bool:
        """
        Transition mission to new status.

        Validates state transition and updates timestamps.
        """
        mission = await self.get_mission(mission_id)
        if not mission:
            return False

        # Valid transitions
        valid_transitions = {
            MissionStatus.PENDING: [MissionStatus.ASSIGNED, MissionStatus.CANCELLED],
            MissionStatus.ASSIGNED: [MissionStatus.IN_PROGRESS, MissionStatus.CANCELLED],
            MissionStatus.IN_PROGRESS: [MissionStatus.BLOCKED, MissionStatus.COMPLETED, MissionStatus.FAILED],
            MissionStatus.BLOCKED: [MissionStatus.IN_PROGRESS, MissionStatus.CANCELLED],
            MissionStatus.COMPLETED: [],
            MissionStatus.FAILED: [MissionStatus.PENDING],  # Allow retry
            MissionStatus.CANCELLED: [],
        }

        current = mission.status if isinstance(mission.status, MissionStatus) else MissionStatus(mission.status)

        if new_status not in valid_transitions.get(current, []):
            logger.warning(f"Invalid transition: {current} -> {new_status}")
            return False

        updates = {"status": new_status.value, **kwargs}

        # Set timestamps based on transition
        now = datetime.utcnow().isoformat()
        if new_status == MissionStatus.IN_PROGRESS and not mission.started_at:
            updates["started_at"] = now
        elif new_status in [MissionStatus.COMPLETED, MissionStatus.FAILED]:
            updates["completed_at"] = now

        return await self.update_mission(mission_id, updates)

    async def get_missions_by_status(
        self,
        status: MissionStatus,
        limit: int = 100,
    ) -> List[Mission]:
        """Get all missions with a specific status."""
        missions = []

        if self.is_connected:
            mission_ids = await self._redis.smembers(f"{self.MISSIONS_KEY}:index")

            for mid in mission_ids:
                mission = await self.get_mission(mid)
                if mission:
                    current = mission.status if isinstance(mission.status, MissionStatus) else MissionStatus(mission.status)
                    if current == status:
                        missions.append(mission)

                if len(missions) >= limit:
                    break
        else:
            for key, data in self._local_cache.items():
                if key.startswith(self.MISSIONS_KEY):
                    if data.get("status") == status.value:
                        missions.append(Mission.from_dict(data))

        return missions

    async def get_agent_missions(self, agent_id: str) -> List[Mission]:
        """Get all missions assigned to an agent."""
        missions = []

        if self.is_connected:
            mission_ids = await self._redis.smembers(f"{self.MISSIONS_KEY}:index")

            for mid in mission_ids:
                mission = await self.get_mission(mid)
                if mission and agent_id in mission.assigned_agents:
                    missions.append(mission)
        else:
            for key, data in self._local_cache.items():
                if key.startswith(self.MISSIONS_KEY):
                    if agent_id in data.get("assigned_agents", []):
                        missions.append(Mission.from_dict(data))

        return missions

    async def delete_mission(self, mission_id: str) -> bool:
        """Delete a mission."""
        key = f"{self.MISSIONS_KEY}:{mission_id}"

        if self.is_connected:
            await self._redis.delete(key)
            await self._redis.srem(f"{self.MISSIONS_KEY}:index", mission_id)
        else:
            self._local_cache.pop(key, None)

        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # ROADMAP OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_roadmap(self, roadmap: Roadmap) -> str:
        """Create a new roadmap."""
        key = f"{self.ROADMAPS_KEY}:{roadmap.roadmap_id}"

        if self.is_connected:
            await self._redis.hset(key, mapping={
                "data": json.dumps(roadmap.to_dict()),
            })
            await self._redis.sadd(f"{self.ROADMAPS_KEY}:index", roadmap.roadmap_id)
        else:
            self._local_cache[key] = roadmap.to_dict()

        return roadmap.roadmap_id

    async def get_roadmap(self, roadmap_id: str) -> Optional[Roadmap]:
        """Get a roadmap by ID."""
        key = f"{self.ROADMAPS_KEY}:{roadmap_id}"

        if self.is_connected:
            data = await self._redis.hget(key, "data")
            if data:
                return Roadmap.from_dict(json.loads(data))
        else:
            if key in self._local_cache:
                return Roadmap.from_dict(self._local_cache[key])

        return None

    async def update_roadmap(
        self,
        roadmap_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update roadmap fields."""
        roadmap = await self.get_roadmap(roadmap_id)
        if not roadmap:
            return False

        roadmap_dict = roadmap.to_dict()
        roadmap_dict.update(updates)
        roadmap_dict["updated_at"] = datetime.utcnow().isoformat()

        key = f"{self.ROADMAPS_KEY}:{roadmap_id}"

        if self.is_connected:
            await self._redis.hset(key, mapping={
                "data": json.dumps(roadmap_dict),
            })
        else:
            self._local_cache[key] = roadmap_dict

        return True

    async def advance_roadmap(self, roadmap_id: str) -> Optional[Dict[str, Any]]:
        """
        Advance roadmap to next step.

        Returns:
            Next step data or None if complete
        """
        roadmap = await self.get_roadmap(roadmap_id)
        if not roadmap:
            return None

        if roadmap.current_step >= len(roadmap.steps):
            await self.update_roadmap(roadmap_id, {"status": "completed"})
            return None

        next_step = roadmap.steps[roadmap.current_step]
        await self.update_roadmap(roadmap_id, {
            "current_step": roadmap.current_step + 1,
            "status": "in_progress",
        })

        return next_step

    # ═══════════════════════════════════════════════════════════════════════════
    # AGENT STATE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def update_agent_state(self, state: AgentState) -> bool:
        """Update an agent's state."""
        key = f"{self.AGENTS_KEY}:{state.agent_id}"

        if self.is_connected:
            await self._redis.hset(key, mapping={
                "data": json.dumps(state.to_dict()),
            })
            # Set TTL for auto-cleanup of stale agents
            await self._redis.expire(key, 300)  # 5 minutes
        else:
            self._local_cache[key] = state.to_dict()

        return True

    async def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get an agent's current state."""
        key = f"{self.AGENTS_KEY}:{agent_id}"

        if self.is_connected:
            data = await self._redis.hget(key, "data")
            if data:
                d = json.loads(data)
                return AgentState(
                    agent_id=d["agent_id"],
                    status=d.get("status", "idle"),
                    current_mission=d.get("current_mission"),
                    workload=d.get("workload", 0.0),
                    last_heartbeat=d.get("last_heartbeat", ""),
                    metrics=d.get("metrics", {}),
                )
        else:
            if key in self._local_cache:
                d = self._local_cache[key]
                return AgentState(
                    agent_id=d["agent_id"],
                    status=d.get("status", "idle"),
                    current_mission=d.get("current_mission"),
                    workload=d.get("workload", 0.0),
                    last_heartbeat=d.get("last_heartbeat", ""),
                    metrics=d.get("metrics", {}),
                )

        return None

    async def heartbeat(self, agent_id: str) -> bool:
        """Record agent heartbeat."""
        state = await self.get_agent_state(agent_id)

        if state:
            state.last_heartbeat = datetime.utcnow().isoformat()
            return await self.update_agent_state(state)
        else:
            # Create new state
            state = AgentState(agent_id=agent_id)
            return await self.update_agent_state(state)

    async def get_active_agents(self, timeout_seconds: int = 60) -> List[AgentState]:
        """Get all agents with recent heartbeats."""
        agents = []
        cutoff = datetime.utcnow() - timedelta(seconds=timeout_seconds)

        if self.is_connected:
            # Scan for agent keys
            async for key in self._redis.scan_iter(f"{self.AGENTS_KEY}:*"):
                data = await self._redis.hget(key, "data")
                if data:
                    d = json.loads(data)
                    last_hb = datetime.fromisoformat(d.get("last_heartbeat", "2000-01-01"))
                    if last_hb > cutoff:
                        agents.append(AgentState(
                            agent_id=d["agent_id"],
                            status=d.get("status", "idle"),
                            current_mission=d.get("current_mission"),
                            workload=d.get("workload", 0.0),
                            last_heartbeat=d.get("last_heartbeat", ""),
                            metrics=d.get("metrics", {}),
                        ))

        return agents

    # ═══════════════════════════════════════════════════════════════════════════
    # DISTRIBUTED LOCKS
    # ═══════════════════════════════════════════════════════════════════════════

    async def acquire_lock(
        self,
        lock_name: str,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """
        Acquire a distributed lock.

        Args:
            lock_name: Name of the lock
            timeout: Lock timeout in seconds

        Returns:
            Lock token if acquired, None otherwise
        """
        key = f"{self.LOCKS_KEY}:{lock_name}"
        token = str(uuid.uuid4())
        timeout = timeout or self.default_lock_timeout

        if self.is_connected:
            # Use SET NX EX for atomic lock
            acquired = await self._redis.set(
                key,
                token,
                nx=True,
                ex=timeout,
            )
            return token if acquired else None
        else:
            if key not in self._local_cache:
                self._local_cache[key] = token
                return token
            return None

    async def release_lock(self, lock_name: str, token: str) -> bool:
        """
        Release a distributed lock.

        Args:
            lock_name: Name of the lock
            token: Lock token from acquire_lock

        Returns:
            True if released successfully
        """
        key = f"{self.LOCKS_KEY}:{lock_name}"

        if self.is_connected:
            # Verify token before release
            current = await self._redis.get(key)
            if current == token:
                await self._redis.delete(key)
                return True
            return False
        else:
            if self._local_cache.get(key) == token:
                del self._local_cache[key]
                return True
            return False

    async def with_lock(
        self,
        lock_name: str,
        callback: Callable,
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Execute callback with lock held.

        Args:
            lock_name: Name of the lock
            callback: Async function to execute
            timeout: Lock timeout

        Returns:
            Callback result

        Raises:
            RuntimeError: If lock cannot be acquired
        """
        token = await self.acquire_lock(lock_name, timeout)
        if not token:
            raise RuntimeError(f"Failed to acquire lock: {lock_name}")

        try:
            return await callback()
        finally:
            await self.release_lock(lock_name, token)

    # ═══════════════════════════════════════════════════════════════════════════
    # COUNTERS & METRICS
    # ═══════════════════════════════════════════════════════════════════════════

    async def increment(self, counter_name: str, amount: int = 1) -> int:
        """Increment a counter atomically."""
        key = f"{self.COUNTERS_KEY}:{counter_name}"

        if self.is_connected:
            return await self._redis.incrby(key, amount)
        else:
            current = self._local_cache.get(key, 0)
            self._local_cache[key] = current + amount
            return self._local_cache[key]

    async def get_counter(self, counter_name: str) -> int:
        """Get current counter value."""
        key = f"{self.COUNTERS_KEY}:{counter_name}"

        if self.is_connected:
            value = await self._redis.get(key)
            return int(value) if value else 0
        else:
            return self._local_cache.get(key, 0)

    async def set_value(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set arbitrary key-value with optional TTL."""
        full_key = f"cirkelline:data:{key}"

        if self.is_connected:
            if ttl:
                await self._redis.setex(full_key, ttl, json.dumps(value))
            else:
                await self._redis.set(full_key, json.dumps(value))
        else:
            self._local_cache[full_key] = value

        return True

    async def get_value(self, key: str) -> Optional[Any]:
        """Get arbitrary value by key."""
        full_key = f"cirkelline:data:{key}"

        if self.is_connected:
            data = await self._redis.get(full_key)
            return json.loads(data) if data else None
        else:
            return self._local_cache.get(full_key)

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_stats(self) -> Dict[str, Any]:
        """Get shared memory statistics."""
        stats = {
            "connected": self.is_connected,
            "missions": {"total": 0, "by_status": {}},
            "roadmaps": {"total": 0},
            "agents": {"active": 0},
        }

        if self.is_connected:
            # Count missions
            mission_ids = await self._redis.smembers(f"{self.MISSIONS_KEY}:index")
            stats["missions"]["total"] = len(mission_ids)

            # Count by status
            for status in MissionStatus:
                count = len(await self.get_missions_by_status(status))
                if count > 0:
                    stats["missions"]["by_status"][status.value] = count

            # Count roadmaps
            roadmap_ids = await self._redis.smembers(f"{self.ROADMAPS_KEY}:index")
            stats["roadmaps"]["total"] = len(roadmap_ids)

            # Count active agents
            agents = await self.get_active_agents()
            stats["agents"]["active"] = len(agents)

        return stats


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_shared_memory_instance: Optional[SharedMemory] = None


def get_shared_memory(redis_url: Optional[str] = None) -> SharedMemory:
    """
    Get the singleton SharedMemory instance.

    Args:
        redis_url: Optional Redis URL

    Returns:
        SharedMemory singleton instance
    """
    global _shared_memory_instance

    if _shared_memory_instance is None:
        url = redis_url or "redis://localhost:6379/0"
        _shared_memory_instance = SharedMemory(redis_url=url)

    return _shared_memory_instance


async def init_shared_memory(redis_url: str = "redis://localhost:6379/0") -> SharedMemory:
    """Initialize and connect shared memory."""
    memory = get_shared_memory(redis_url)
    await memory.connect()
    return memory
