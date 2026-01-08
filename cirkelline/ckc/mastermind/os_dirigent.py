"""
OS-DIRIGENT: Lokal Agent & MASTERMIND Integration Layer
========================================================

DEL E implementation for FASE 3.

Forbinder Cirkelline Local Agent (CLA) med MASTERMIND koordinatoren
for at muliggøre distribueret opgaveudførelse på brugerens lokale maskine.

Komponenter:
- OSDirigent: Hovedklasse for lokal agent orkestrering
- LocalAgentBridge: Kommunikationsprotokol mellem CLA og CKC
- TaskOffloader: Beslutter hvilke opgaver der skal køre lokalt
- ResourceCoordinator: Koordinerer lokale og cloud ressourcer
- LocalCapabilityRegistry: Registrerer CLA kapaciteter

Eksempel:
    from cirkelline.ckc.mastermind.os_dirigent import (
        create_os_dirigent,
        create_local_agent_bridge,
    )

    dirigent = await create_os_dirigent()
    bridge = await create_local_agent_bridge(dirigent)

    # Registrer lokal agent
    await bridge.register_agent(agent_id="cla_123", capabilities=["ocr", "embedding"])

    # Offload opgave til lokal agent
    result = await dirigent.offload_task(task_id="task_456", to_agent="cla_123")
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# =============================================================================
# ENUMS
# =============================================================================


class LocalAgentStatus(Enum):
    """Status for en lokal agent."""
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"
    SUSPENDED = "suspended"


class OffloadDecision(Enum):
    """Beslutning om hvor opgave skal køre."""
    LOCAL = "local"          # Kør på brugerens maskine
    CLOUD = "cloud"          # Kør i cloud (CKC)
    HYBRID = "hybrid"        # Delt udførelse
    QUEUE = "queue"          # Vent på ressourcer
    REJECT = "reject"        # Afvis opgaven


class LocalCapability(Enum):
    """Kapaciteter en lokal agent kan have."""
    OCR = "ocr"                          # Tekst-genkendelse
    EMBEDDING = "embedding"              # Lokal embedding-model
    WHISPER = "whisper"                  # Audio transskription
    IMAGE_GENERATION = "image_generation" # Lokal billede-generation
    FILE_PROCESSING = "file_processing"  # Lokal fil-behandling
    RESEARCH = "research"                # Lokal research (Commander)
    TASK_SCHEDULING = "task_scheduling"  # Opgave-planlægning
    SYNC = "sync"                        # Data synkronisering


class TaskPriority(Enum):
    """Prioritet for offloaded opgaver."""
    CRITICAL = "critical"    # Kør straks
    HIGH = "high"            # Høj prioritet
    NORMAL = "normal"        # Normal prioritet
    LOW = "low"              # Lav prioritet
    BACKGROUND = "background" # Baggrundsopgave


class SyncDirection(Enum):
    """Retning for synkronisering."""
    TO_LOCAL = "to_local"      # Fra cloud til lokal
    TO_CLOUD = "to_cloud"      # Fra lokal til cloud
    BIDIRECTIONAL = "bidirectional"  # Begge veje


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class LocalAgentInfo:
    """Information om en registreret lokal agent."""
    agent_id: str
    device_id: str
    user_id: str
    status: LocalAgentStatus = LocalAgentStatus.OFFLINE

    # Kapaciteter
    capabilities: Set[LocalCapability] = field(default_factory=set)
    models_loaded: List[str] = field(default_factory=list)

    # Ressourcer
    cpu_available: float = 0.0       # 0.0 - 1.0
    memory_available_gb: float = 0.0
    gpu_available: bool = False
    disk_free_gb: float = 0.0

    # Status
    current_tasks: int = 0
    max_concurrent_tasks: int = 3
    last_heartbeat: Optional[datetime] = None
    connection_quality: float = 1.0  # 0.0 - 1.0

    # Version info
    cla_version: str = "0.0.0"
    registered_at: datetime = field(default_factory=datetime.now)

    @property
    def is_available(self) -> bool:
        """Tjek om agent er tilgængelig for opgaver."""
        return (
            self.status == LocalAgentStatus.ONLINE and
            self.current_tasks < self.max_concurrent_tasks
        )

    @property
    def load_factor(self) -> float:
        """Beregn belastningsfaktor (0.0 = idle, 1.0 = fuldt belastet)."""
        if self.max_concurrent_tasks == 0:
            return 1.0
        return self.current_tasks / self.max_concurrent_tasks


@dataclass
class OffloadTask:
    """En opgave der skal offloades til lokal agent."""
    task_id: str
    mastermind_session_id: str

    # Opgavebeskrivelse
    task_type: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Krav
    required_capabilities: Set[LocalCapability] = field(default_factory=set)
    required_memory_gb: float = 0.0
    requires_gpu: bool = False

    # Prioritet og timing
    priority: TaskPriority = TaskPriority.NORMAL
    deadline: Optional[datetime] = None
    max_execution_time_seconds: int = 3600

    # Status
    decision: Optional[OffloadDecision] = None
    assigned_agent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Resultat
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class SyncBatch:
    """En batch af data der skal synkroniseres."""
    batch_id: str
    direction: SyncDirection

    # Data
    data_type: str  # "embeddings", "documents", "research", etc.
    items: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    source_agent_id: Optional[str] = None
    target_agent_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL

    # Status
    created_at: datetime = field(default_factory=datetime.now)
    synced_at: Optional[datetime] = None
    items_synced: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class ResourceAllocationPlan:
    """Plan for ressourceallokering mellem lokal og cloud."""
    plan_id: str
    session_id: str

    # Allokering
    local_tasks: List[str] = field(default_factory=list)
    cloud_tasks: List[str] = field(default_factory=list)

    # Estimater
    estimated_local_time_seconds: float = 0.0
    estimated_cloud_time_seconds: float = 0.0
    estimated_cost_usd: float = 0.0

    # Ressource usage
    local_cpu_allocation: float = 0.0
    local_memory_allocation_gb: float = 0.0
    cloud_api_calls: int = 0

    created_at: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None


# =============================================================================
# LOCAL CAPABILITY REGISTRY
# =============================================================================


class LocalCapabilityRegistry:
    """
    Registrerer og tracker kapaciteter fra lokale agenter.

    Holder styr på hvilke kapaciteter der er tilgængelige
    på tværs af alle registrerede lokale agenter.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, LocalAgentInfo] = {}
        self._capability_index: Dict[LocalCapability, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def register_agent(self, agent: LocalAgentInfo) -> None:
        """Registrer en ny lokal agent."""
        async with self._lock:
            self._agents[agent.agent_id] = agent

            # Opdater capability index
            for cap in agent.capabilities:
                if cap not in self._capability_index:
                    self._capability_index[cap] = set()
                self._capability_index[cap].add(agent.agent_id)

            logger.info(f"Registered local agent {agent.agent_id} with {len(agent.capabilities)} capabilities")

    async def unregister_agent(self, agent_id: str) -> None:
        """Afregistrer en lokal agent."""
        async with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]

                # Fjern fra capability index
                for cap in agent.capabilities:
                    if cap in self._capability_index:
                        self._capability_index[cap].discard(agent_id)

                del self._agents[agent_id]
                logger.info(f"Unregistered local agent {agent_id}")

    async def update_agent_status(
        self,
        agent_id: str,
        status: LocalAgentStatus,
        **kwargs
    ) -> None:
        """Opdater status for en agent."""
        async with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.status = status
                agent.last_heartbeat = datetime.now()

                # Opdater andre felter
                for key, value in kwargs.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)

    async def get_agents_with_capability(
        self,
        capability: LocalCapability
    ) -> List[LocalAgentInfo]:
        """Find alle agenter med en given kapacitet."""
        async with self._lock:
            agent_ids = self._capability_index.get(capability, set())
            return [
                self._agents[aid] for aid in agent_ids
                if aid in self._agents and self._agents[aid].is_available
            ]

    async def get_best_agent_for_task(
        self,
        task: OffloadTask
    ) -> Optional[LocalAgentInfo]:
        """Find den bedste agent til en given opgave."""
        async with self._lock:
            candidates: List[LocalAgentInfo] = []

            for agent in self._agents.values():
                # Check availability
                if not agent.is_available:
                    continue

                # Check capabilities
                if not task.required_capabilities.issubset(agent.capabilities):
                    continue

                # Check resources
                if task.required_memory_gb > agent.memory_available_gb:
                    continue

                if task.requires_gpu and not agent.gpu_available:
                    continue

                candidates.append(agent)

            if not candidates:
                return None

            # Vælg agent med lavest load factor
            return min(candidates, key=lambda a: a.load_factor)

    async def get_all_agents(self) -> List[LocalAgentInfo]:
        """Hent alle registrerede agenter."""
        async with self._lock:
            return list(self._agents.values())

    async def get_agent(self, agent_id: str) -> Optional[LocalAgentInfo]:
        """Hent en specifik agent."""
        async with self._lock:
            return self._agents.get(agent_id)


# =============================================================================
# TASK OFFLOADER
# =============================================================================


class TaskOffloader:
    """
    Beslutter om opgaver skal køre lokalt eller i cloud.

    Baserer beslutningen på:
    - Opgavens krav
    - Tilgængelige lokale ressourcer
    - Netværkskvalitet
    - Brugerindstillinger
    """

    def __init__(
        self,
        registry: LocalCapabilityRegistry,
        prefer_local: bool = True,
        min_connection_quality: float = 0.5,
    ) -> None:
        self.registry = registry
        self.prefer_local = prefer_local
        self.min_connection_quality = min_connection_quality

    async def decide(self, task: OffloadTask) -> OffloadDecision:
        """
        Bestem hvor opgaven skal køre.

        Returns:
            OffloadDecision indikerer hvor opgaven skal udføres.
        """
        # Tjek om der er en tilgængelig agent
        best_agent = await self.registry.get_best_agent_for_task(task)

        if best_agent is None:
            # Ingen lokal agent kan håndtere opgaven
            return OffloadDecision.CLOUD

        # Tjek forbindelseskvalitet
        if best_agent.connection_quality < self.min_connection_quality:
            logger.warning(
                f"Agent {best_agent.agent_id} has low connection quality: "
                f"{best_agent.connection_quality}"
            )
            return OffloadDecision.CLOUD

        # Kritiske opgaver går altid til cloud for reliability
        if task.priority == TaskPriority.CRITICAL:
            return OffloadDecision.CLOUD

        # Beregn cost/benefit
        local_score = self._calculate_local_score(task, best_agent)
        cloud_score = self._calculate_cloud_score(task)

        if self.prefer_local:
            local_score *= 1.2  # 20% bonus for lokal præference

        if local_score >= cloud_score:
            task.assigned_agent_id = best_agent.agent_id
            return OffloadDecision.LOCAL
        else:
            return OffloadDecision.CLOUD

    def _calculate_local_score(
        self,
        task: OffloadTask,
        agent: LocalAgentInfo
    ) -> float:
        """Beregn score for lokal udførelse."""
        score = 50.0  # Baseline

        # Bonus for lav agent load
        score += (1.0 - agent.load_factor) * 20

        # Bonus for god forbindelse
        score += agent.connection_quality * 15

        # Bonus for GPU hvis påkrævet
        if task.requires_gpu and agent.gpu_available:
            score += 10

        # Penalty for høj memory requirement
        if task.required_memory_gb > agent.memory_available_gb * 0.7:
            score -= 15

        return score

    def _calculate_cloud_score(self, task: OffloadTask) -> float:
        """Beregn score for cloud udførelse."""
        score = 60.0  # Baseline (slightly higher for reliability)

        # Bonus for kritiske opgaver
        if task.priority == TaskPriority.CRITICAL:
            score += 20

        # Bonus for opgaver uden deadline (kan queue)
        if task.deadline is None:
            score += 5

        return score


# =============================================================================
# RESOURCE COORDINATOR
# =============================================================================


class ResourceCoordinator:
    """
    Koordinerer ressourcer mellem lokale agenter og cloud.

    Opretter allokeringsplaner og balancerer load.
    """

    def __init__(
        self,
        registry: LocalCapabilityRegistry,
        offloader: TaskOffloader,
    ) -> None:
        self.registry = registry
        self.offloader = offloader
        self._active_plans: Dict[str, ResourceAllocationPlan] = {}

    async def create_allocation_plan(
        self,
        session_id: str,
        tasks: List[OffloadTask],
    ) -> ResourceAllocationPlan:
        """
        Opret en allokeringsplan for en serie opgaver.

        Optimerer for:
        - Minimering af total udførelsestid
        - Balancering af load på lokale agenter
        - Minimering af cloud costs
        """
        plan = ResourceAllocationPlan(
            plan_id=str(uuid.uuid4()),
            session_id=session_id,
        )

        for task in tasks:
            decision = await self.offloader.decide(task)
            task.decision = decision

            if decision == OffloadDecision.LOCAL:
                plan.local_tasks.append(task.task_id)
                plan.estimated_local_time_seconds += self._estimate_local_time(task)
                plan.local_cpu_allocation += 0.2  # Rough estimate
            else:
                plan.cloud_tasks.append(task.task_id)
                plan.estimated_cloud_time_seconds += self._estimate_cloud_time(task)
                plan.cloud_api_calls += 1

        # Estimér cost
        plan.estimated_cost_usd = self._estimate_cost(plan)

        self._active_plans[plan.plan_id] = plan
        logger.info(
            f"Created allocation plan {plan.plan_id}: "
            f"{len(plan.local_tasks)} local, {len(plan.cloud_tasks)} cloud tasks"
        )

        return plan

    def _estimate_local_time(self, task: OffloadTask) -> float:
        """Estimér tid for lokal udførelse."""
        base_time = 30.0  # 30 sekunder baseline

        # Juster baseret på opgavetype
        if LocalCapability.WHISPER in task.required_capabilities:
            base_time = 60.0
        elif LocalCapability.EMBEDDING in task.required_capabilities:
            base_time = 10.0
        elif LocalCapability.OCR in task.required_capabilities:
            base_time = 15.0

        return base_time

    def _estimate_cloud_time(self, task: OffloadTask) -> float:
        """Estimér tid for cloud udførelse."""
        # Cloud er generelt hurtigere, men har network latency
        return self._estimate_local_time(task) * 0.5 + 2.0  # +2s network

    def _estimate_cost(self, plan: ResourceAllocationPlan) -> float:
        """Estimér total cost for en plan."""
        # Rough estimates
        cloud_cost_per_call = 0.01  # $0.01 per API call
        return plan.cloud_api_calls * cloud_cost_per_call

    async def get_active_plans(self) -> List[ResourceAllocationPlan]:
        """Hent alle aktive allokeringsplaner."""
        return list(self._active_plans.values())


# =============================================================================
# LOCAL AGENT BRIDGE
# =============================================================================


class LocalAgentBridge(ABC):
    """
    Abstract base for kommunikation med lokale agenter.

    Implementerer protokol for:
    - Registration og heartbeat
    - Task assignment og status
    - Data synkronisering
    """

    @abstractmethod
    async def connect(self, agent_id: str) -> bool:
        """Opret forbindelse til lokal agent."""
        pass

    @abstractmethod
    async def disconnect(self, agent_id: str) -> None:
        """Afbryd forbindelse til lokal agent."""
        pass

    @abstractmethod
    async def send_task(self, agent_id: str, task: OffloadTask) -> bool:
        """Send opgave til lokal agent."""
        pass

    @abstractmethod
    async def get_task_status(self, agent_id: str, task_id: str) -> Dict[str, Any]:
        """Hent status for en opgave."""
        pass

    @abstractmethod
    async def sync_data(self, batch: SyncBatch) -> SyncBatch:
        """Synkroniser data med lokal agent."""
        pass


class WebSocketAgentBridge(LocalAgentBridge):
    """
    WebSocket-baseret bridge til lokale agenter.

    Bruger WebSocket for realtids kommunikation.
    """

    def __init__(self, registry: LocalCapabilityRegistry) -> None:
        self.registry = registry
        self._connections: Dict[str, Any] = {}  # agent_id -> ws connection
        self._pending_tasks: Dict[str, OffloadTask] = {}
        self._task_callbacks: Dict[str, Callable] = {}

    async def connect(self, agent_id: str) -> bool:
        """Opret WebSocket forbindelse til lokal agent."""
        # In real implementation, this would establish a WebSocket connection
        logger.info(f"Connecting to local agent {agent_id}")
        self._connections[agent_id] = {"connected": True, "connected_at": datetime.now()}
        return True

    async def disconnect(self, agent_id: str) -> None:
        """Afbryd WebSocket forbindelse."""
        if agent_id in self._connections:
            del self._connections[agent_id]
            logger.info(f"Disconnected from local agent {agent_id}")

    async def send_task(self, agent_id: str, task: OffloadTask) -> bool:
        """Send opgave via WebSocket."""
        if agent_id not in self._connections:
            logger.error(f"No connection to agent {agent_id}")
            return False

        self._pending_tasks[task.task_id] = task
        task.started_at = datetime.now()

        # In real implementation, serialize and send via WebSocket
        logger.info(f"Sent task {task.task_id} to agent {agent_id}")
        return True

    async def get_task_status(self, agent_id: str, task_id: str) -> Dict[str, Any]:
        """Hent task status via WebSocket."""
        task = self._pending_tasks.get(task_id)
        if task is None:
            return {"status": "not_found"}

        return {
            "task_id": task_id,
            "status": "running" if task.started_at else "pending",
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    async def sync_data(self, batch: SyncBatch) -> SyncBatch:
        """Synkroniser data batch via WebSocket."""
        # In real implementation, serialize and send batch
        batch.synced_at = datetime.now()
        batch.items_synced = len(batch.items)

        logger.info(
            f"Synced {batch.items_synced} items in batch {batch.batch_id} "
            f"({batch.direction.value})"
        )
        return batch

    async def is_connected(self, agent_id: str) -> bool:
        """Tjek om agent er forbundet."""
        return agent_id in self._connections


# =============================================================================
# OS DIRIGENT - MAIN CLASS
# =============================================================================


class OSDirigent:
    """
    OS-Dirigent: Hovedklasse for lokal agent orkestrering.

    Forbinder MASTERMIND med lokale agenter og koordinerer
    distribueret opgaveudførelse.

    Eksempel:
        dirigent = OSDirigent()
        await dirigent.start()

        # Registrer lokal agent
        await dirigent.register_local_agent(agent_info)

        # Offload opgave
        result = await dirigent.offload_task(task)
    """

    def __init__(
        self,
        prefer_local: bool = True,
        enable_sync: bool = True,
        heartbeat_interval_seconds: int = 30,
    ) -> None:
        self.registry = LocalCapabilityRegistry()
        self.offloader = TaskOffloader(self.registry, prefer_local=prefer_local)
        self.coordinator = ResourceCoordinator(self.registry, self.offloader)
        self.bridge = WebSocketAgentBridge(self.registry)

        self.enable_sync = enable_sync
        self.heartbeat_interval = heartbeat_interval_seconds

        self._running = False
        self._tasks: Dict[str, OffloadTask] = {}
        self._sync_queue: List[SyncBatch] = []
        self._callbacks: Dict[str, Callable] = {}

    async def start(self) -> None:
        """Start OS-Dirigent."""
        self._running = True
        logger.info("OS-Dirigent started")

        # Start background tasks
        asyncio.create_task(self._heartbeat_loop())
        if self.enable_sync:
            asyncio.create_task(self._sync_loop())

    async def stop(self) -> None:
        """Stop OS-Dirigent."""
        self._running = False

        # Disconnect all agents
        for agent in await self.registry.get_all_agents():
            await self.bridge.disconnect(agent.agent_id)

        logger.info("OS-Dirigent stopped")

    async def register_local_agent(
        self,
        agent_id: str,
        device_id: str,
        user_id: str,
        capabilities: List[str],
        **kwargs
    ) -> LocalAgentInfo:
        """
        Registrer en ny lokal agent.

        Args:
            agent_id: Unik ID for agenten
            device_id: ID for enheden
            user_id: Bruger-ID
            capabilities: Liste af kapacitetsnavne
            **kwargs: Yderligere agent information

        Returns:
            LocalAgentInfo objekt
        """
        # Parse capabilities
        caps = set()
        for cap_name in capabilities:
            try:
                caps.add(LocalCapability(cap_name))
            except ValueError:
                logger.warning(f"Unknown capability: {cap_name}")

        agent = LocalAgentInfo(
            agent_id=agent_id,
            device_id=device_id,
            user_id=user_id,
            capabilities=caps,
            status=LocalAgentStatus.CONNECTING,
            **{k: v for k, v in kwargs.items() if hasattr(LocalAgentInfo, k)}
        )

        await self.registry.register_agent(agent)

        # Establish connection
        if await self.bridge.connect(agent_id):
            await self.registry.update_agent_status(agent_id, LocalAgentStatus.ONLINE)
        else:
            await self.registry.update_agent_status(agent_id, LocalAgentStatus.ERROR)

        return agent

    async def unregister_local_agent(self, agent_id: str) -> None:
        """Afregistrer en lokal agent."""
        await self.bridge.disconnect(agent_id)
        await self.registry.unregister_agent(agent_id)

    async def offload_task(
        self,
        task_id: str,
        mastermind_session_id: str,
        task_type: str,
        description: str,
        required_capabilities: List[str],
        parameters: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        **kwargs
    ) -> OffloadTask:
        """
        Offload en opgave til lokal eller cloud udførelse.

        Args:
            task_id: Unik opgave-ID
            mastermind_session_id: MASTERMIND session ID
            task_type: Type af opgave
            description: Beskrivelse
            required_capabilities: Krævede kapaciteter
            parameters: Opgaveparametre
            priority: Prioritetsniveau

        Returns:
            OffloadTask med beslutning og tildelt agent
        """
        # Parse capabilities
        caps = set()
        for cap_name in required_capabilities:
            try:
                caps.add(LocalCapability(cap_name))
            except ValueError:
                logger.warning(f"Unknown capability: {cap_name}")

        # Parse priority
        try:
            task_priority = TaskPriority(priority)
        except ValueError:
            task_priority = TaskPriority.NORMAL

        task = OffloadTask(
            task_id=task_id,
            mastermind_session_id=mastermind_session_id,
            task_type=task_type,
            description=description,
            required_capabilities=caps,
            parameters=parameters or {},
            priority=task_priority,
        )

        # Get offload decision
        decision = await self.offloader.decide(task)
        task.decision = decision

        self._tasks[task_id] = task

        # If local, send to agent
        if decision == OffloadDecision.LOCAL and task.assigned_agent_id:
            await self.bridge.send_task(task.assigned_agent_id, task)

        logger.info(
            f"Task {task_id} offloaded: {decision.value} "
            f"(agent: {task.assigned_agent_id or 'cloud'})"
        )

        return task

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Hent status for en opgave."""
        task = self._tasks.get(task_id)
        if task is None:
            return None

        if task.assigned_agent_id:
            return await self.bridge.get_task_status(task.assigned_agent_id, task_id)

        return {
            "task_id": task_id,
            "decision": task.decision.value if task.decision else None,
            "status": "cloud" if task.decision == OffloadDecision.CLOUD else "unknown",
        }

    async def queue_sync(
        self,
        data_type: str,
        items: List[Dict[str, Any]],
        direction: str = "bidirectional",
        source_agent_id: Optional[str] = None,
        target_agent_id: Optional[str] = None,
    ) -> SyncBatch:
        """
        Sæt data i kø til synkronisering.

        Args:
            data_type: Type af data (embeddings, documents, etc.)
            items: Data items at synkronisere
            direction: Synkroniseringsretning
            source_agent_id: Kilde agent
            target_agent_id: Mål agent

        Returns:
            SyncBatch objekt
        """
        try:
            sync_direction = SyncDirection(direction)
        except ValueError:
            sync_direction = SyncDirection.BIDIRECTIONAL

        batch = SyncBatch(
            batch_id=str(uuid.uuid4()),
            direction=sync_direction,
            data_type=data_type,
            items=items,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
        )

        self._sync_queue.append(batch)
        logger.info(f"Queued sync batch {batch.batch_id} with {len(items)} items")

        return batch

    async def get_local_agents(self) -> List[LocalAgentInfo]:
        """Hent alle registrerede lokale agenter."""
        return await self.registry.get_all_agents()

    async def get_agent_capabilities(
        self,
        agent_id: str
    ) -> Optional[Set[LocalCapability]]:
        """Hent kapaciteter for en specifik agent."""
        agent = await self.registry.get_agent(agent_id)
        return agent.capabilities if agent else None

    async def create_allocation_plan(
        self,
        session_id: str,
        tasks: List[OffloadTask],
    ) -> ResourceAllocationPlan:
        """Opret en ressourceallokeringsplan."""
        return await self.coordinator.create_allocation_plan(session_id, tasks)

    # Background loops

    async def _heartbeat_loop(self) -> None:
        """Send heartbeat til alle agenter."""
        while self._running:
            await asyncio.sleep(self.heartbeat_interval)

            for agent in await self.registry.get_all_agents():
                if await self.bridge.is_connected(agent.agent_id):
                    await self.registry.update_agent_status(
                        agent.agent_id,
                        agent.status,
                        last_heartbeat=datetime.now()
                    )

    async def _sync_loop(self) -> None:
        """Process sync queue."""
        while self._running:
            await asyncio.sleep(5)  # Check every 5 seconds

            if self._sync_queue:
                batch = self._sync_queue.pop(0)
                try:
                    await self.bridge.sync_data(batch)
                except Exception as e:
                    batch.errors.append(str(e))
                    logger.error(f"Sync failed for batch {batch.batch_id}: {e}")


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

# Singleton instances
_os_dirigent_instance: Optional[OSDirigent] = None
_local_agent_bridge_instance: Optional[LocalAgentBridge] = None


async def create_os_dirigent(
    prefer_local: bool = True,
    enable_sync: bool = True,
    heartbeat_interval_seconds: int = 30,
) -> OSDirigent:
    """
    Factory funktion til oprettelse af OSDirigent.

    Args:
        prefer_local: Foretræk lokal udførelse når muligt
        enable_sync: Aktiver automatisk synkronisering
        heartbeat_interval_seconds: Interval for heartbeat

    Returns:
        Ny OSDirigent instance
    """
    global _os_dirigent_instance

    dirigent = OSDirigent(
        prefer_local=prefer_local,
        enable_sync=enable_sync,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
    )
    await dirigent.start()

    _os_dirigent_instance = dirigent
    return dirigent


def get_os_dirigent() -> Optional[OSDirigent]:
    """Hent eksisterende OSDirigent instance."""
    return _os_dirigent_instance


async def create_local_agent_bridge(
    registry: Optional[LocalCapabilityRegistry] = None
) -> LocalAgentBridge:
    """
    Factory funktion til oprettelse af LocalAgentBridge.

    Args:
        registry: Eksisterende registry (opretter ny hvis None)

    Returns:
        Ny LocalAgentBridge instance
    """
    global _local_agent_bridge_instance

    if registry is None:
        registry = LocalCapabilityRegistry()

    bridge = WebSocketAgentBridge(registry)
    _local_agent_bridge_instance = bridge
    return bridge


def get_local_agent_bridge() -> Optional[LocalAgentBridge]:
    """Hent eksisterende LocalAgentBridge instance."""
    return _local_agent_bridge_instance


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "LocalAgentStatus",
    "OffloadDecision",
    "LocalCapability",
    "TaskPriority",
    "SyncDirection",

    # Data classes
    "LocalAgentInfo",
    "OffloadTask",
    "SyncBatch",
    "ResourceAllocationPlan",

    # Classes
    "LocalCapabilityRegistry",
    "TaskOffloader",
    "ResourceCoordinator",
    "LocalAgentBridge",
    "WebSocketAgentBridge",
    "OSDirigent",

    # Factory functions
    "create_os_dirigent",
    "get_os_dirigent",
    "create_local_agent_bridge",
    "get_local_agent_bridge",
]
