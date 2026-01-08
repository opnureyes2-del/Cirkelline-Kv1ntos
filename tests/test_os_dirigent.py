"""
Tests for DEL E: OS-Dirigent (Local Agent Integration)
======================================================

Tests for the OS-Dirigent module that connects CLA with MASTERMIND.
"""

import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# TEST OS-DIRIGENT ENUMS
# =============================================================================


class TestOSDirigentEnums:
    """Tests for OS-Dirigent enums."""

    def test_local_agent_status_values(self):
        """Test LocalAgentStatus enum values."""
        from cirkelline.ckc.mastermind.os_dirigent import LocalAgentStatus

        assert LocalAgentStatus.OFFLINE.value == "offline"
        assert LocalAgentStatus.CONNECTING.value == "connecting"
        assert LocalAgentStatus.ONLINE.value == "online"
        assert LocalAgentStatus.BUSY.value == "busy"
        assert LocalAgentStatus.ERROR.value == "error"
        assert LocalAgentStatus.SUSPENDED.value == "suspended"

    def test_offload_decision_values(self):
        """Test OffloadDecision enum values."""
        from cirkelline.ckc.mastermind.os_dirigent import OffloadDecision

        assert OffloadDecision.LOCAL.value == "local"
        assert OffloadDecision.CLOUD.value == "cloud"
        assert OffloadDecision.HYBRID.value == "hybrid"
        assert OffloadDecision.QUEUE.value == "queue"
        assert OffloadDecision.REJECT.value == "reject"

    def test_local_capability_values(self):
        """Test LocalCapability enum values."""
        from cirkelline.ckc.mastermind.os_dirigent import LocalCapability

        assert LocalCapability.OCR.value == "ocr"
        assert LocalCapability.EMBEDDING.value == "embedding"
        assert LocalCapability.WHISPER.value == "whisper"
        assert LocalCapability.IMAGE_GENERATION.value == "image_generation"
        assert LocalCapability.FILE_PROCESSING.value == "file_processing"
        assert LocalCapability.RESEARCH.value == "research"
        assert LocalCapability.TASK_SCHEDULING.value == "task_scheduling"
        assert LocalCapability.SYNC.value == "sync"

    def test_task_priority_values(self):
        """Test TaskPriority enum values."""
        from cirkelline.ckc.mastermind.os_dirigent import TaskPriority

        assert TaskPriority.CRITICAL.value == "critical"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.NORMAL.value == "normal"
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.BACKGROUND.value == "background"

    def test_sync_direction_values(self):
        """Test SyncDirection enum values."""
        from cirkelline.ckc.mastermind.os_dirigent import SyncDirection

        assert SyncDirection.TO_LOCAL.value == "to_local"
        assert SyncDirection.TO_CLOUD.value == "to_cloud"
        assert SyncDirection.BIDIRECTIONAL.value == "bidirectional"


# =============================================================================
# TEST DATA CLASSES
# =============================================================================


class TestOSDirigentDataClasses:
    """Tests for OS-Dirigent data classes."""

    def test_local_agent_info_creation(self):
        """Test LocalAgentInfo dataclass creation."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalAgentInfo,
            LocalAgentStatus,
            LocalCapability,
        )

        agent = LocalAgentInfo(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            capabilities={LocalCapability.OCR, LocalCapability.EMBEDDING},
            cpu_available=0.75,
            memory_available_gb=8.0,
        )

        assert agent.agent_id == "cla_123"
        assert agent.device_id == "device_456"
        assert agent.user_id == "user_789"
        assert len(agent.capabilities) == 2
        assert agent.cpu_available == 0.75
        assert agent.memory_available_gb == 8.0
        assert agent.status == LocalAgentStatus.OFFLINE

    def test_local_agent_info_is_available(self):
        """Test LocalAgentInfo is_available property."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalAgentInfo,
            LocalAgentStatus,
        )

        agent = LocalAgentInfo(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            status=LocalAgentStatus.ONLINE,
            current_tasks=1,
            max_concurrent_tasks=3,
        )

        assert agent.is_available is True

        # Not available when busy
        agent.status = LocalAgentStatus.BUSY
        assert agent.is_available is False

        # Not available when at capacity
        agent.status = LocalAgentStatus.ONLINE
        agent.current_tasks = 3
        assert agent.is_available is False

    def test_local_agent_info_load_factor(self):
        """Test LocalAgentInfo load_factor property."""
        from cirkelline.ckc.mastermind.os_dirigent import LocalAgentInfo

        agent = LocalAgentInfo(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            current_tasks=1,
            max_concurrent_tasks=4,
        )

        assert agent.load_factor == 0.25

        agent.current_tasks = 2
        assert agent.load_factor == 0.5

        agent.current_tasks = 4
        assert agent.load_factor == 1.0

    def test_offload_task_creation(self):
        """Test OffloadTask dataclass creation."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            OffloadTask,
            LocalCapability,
            TaskPriority,
        )

        task = OffloadTask(
            task_id="task_123",
            mastermind_session_id="session_456",
            task_type="ocr",
            description="Extract text from image",
            required_capabilities={LocalCapability.OCR},
            priority=TaskPriority.HIGH,
        )

        assert task.task_id == "task_123"
        assert task.mastermind_session_id == "session_456"
        assert task.task_type == "ocr"
        assert LocalCapability.OCR in task.required_capabilities
        assert task.priority == TaskPriority.HIGH
        assert task.decision is None
        assert task.assigned_agent_id is None

    def test_sync_batch_creation(self):
        """Test SyncBatch dataclass creation."""
        from cirkelline.ckc.mastermind.os_dirigent import SyncBatch, SyncDirection

        batch = SyncBatch(
            batch_id="batch_123",
            direction=SyncDirection.TO_LOCAL,
            data_type="embeddings",
            items=[{"id": "1", "data": "test"}],
        )

        assert batch.batch_id == "batch_123"
        assert batch.direction == SyncDirection.TO_LOCAL
        assert batch.data_type == "embeddings"
        assert len(batch.items) == 1
        assert batch.items_synced == 0

    def test_resource_allocation_plan_creation(self):
        """Test ResourceAllocationPlan dataclass creation."""
        from cirkelline.ckc.mastermind.os_dirigent import ResourceAllocationPlan

        plan = ResourceAllocationPlan(
            plan_id="plan_123",
            session_id="session_456",
            local_tasks=["task_1", "task_2"],
            cloud_tasks=["task_3"],
            estimated_cost_usd=0.05,
        )

        assert plan.plan_id == "plan_123"
        assert plan.session_id == "session_456"
        assert len(plan.local_tasks) == 2
        assert len(plan.cloud_tasks) == 1
        assert plan.estimated_cost_usd == 0.05


# =============================================================================
# TEST LOCAL CAPABILITY REGISTRY
# =============================================================================


class TestLocalCapabilityRegistry:
    """Tests for LocalCapabilityRegistry."""

    @pytest_asyncio.fixture
    async def registry(self):
        """Create a test registry."""
        from cirkelline.ckc.mastermind.os_dirigent import LocalCapabilityRegistry
        return LocalCapabilityRegistry()

    @pytest.mark.asyncio
    async def test_register_agent(self, registry):
        """Test registering an agent."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalAgentInfo,
            LocalCapability,
            LocalAgentStatus,
        )

        agent = LocalAgentInfo(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            capabilities={LocalCapability.OCR, LocalCapability.EMBEDDING},
            status=LocalAgentStatus.ONLINE,
        )

        await registry.register_agent(agent)
        agents = await registry.get_all_agents()

        assert len(agents) == 1
        assert agents[0].agent_id == "cla_123"

    @pytest.mark.asyncio
    async def test_unregister_agent(self, registry):
        """Test unregistering an agent."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalAgentInfo,
            LocalCapability,
        )

        agent = LocalAgentInfo(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            capabilities={LocalCapability.OCR},
        )

        await registry.register_agent(agent)
        await registry.unregister_agent("cla_123")

        agents = await registry.get_all_agents()
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_get_agents_with_capability(self, registry):
        """Test finding agents with specific capability."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalAgentInfo,
            LocalCapability,
            LocalAgentStatus,
        )

        # Register agent with OCR
        agent1 = LocalAgentInfo(
            agent_id="cla_1",
            device_id="device_1",
            user_id="user_1",
            capabilities={LocalCapability.OCR},
            status=LocalAgentStatus.ONLINE,
        )
        await registry.register_agent(agent1)

        # Register agent with EMBEDDING
        agent2 = LocalAgentInfo(
            agent_id="cla_2",
            device_id="device_2",
            user_id="user_1",
            capabilities={LocalCapability.EMBEDDING},
            status=LocalAgentStatus.ONLINE,
        )
        await registry.register_agent(agent2)

        ocr_agents = await registry.get_agents_with_capability(LocalCapability.OCR)
        assert len(ocr_agents) == 1
        assert ocr_agents[0].agent_id == "cla_1"

        embedding_agents = await registry.get_agents_with_capability(LocalCapability.EMBEDDING)
        assert len(embedding_agents) == 1
        assert embedding_agents[0].agent_id == "cla_2"

    @pytest.mark.asyncio
    async def test_get_best_agent_for_task(self, registry):
        """Test finding best agent for a task."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalAgentInfo,
            LocalCapability,
            LocalAgentStatus,
            OffloadTask,
        )

        # Register two OCR-capable agents
        agent1 = LocalAgentInfo(
            agent_id="cla_1",
            device_id="device_1",
            user_id="user_1",
            capabilities={LocalCapability.OCR},
            status=LocalAgentStatus.ONLINE,
            current_tasks=2,
            max_concurrent_tasks=3,
            memory_available_gb=8.0,
        )
        await registry.register_agent(agent1)

        agent2 = LocalAgentInfo(
            agent_id="cla_2",
            device_id="device_2",
            user_id="user_1",
            capabilities={LocalCapability.OCR},
            status=LocalAgentStatus.ONLINE,
            current_tasks=0,  # Less loaded
            max_concurrent_tasks=3,
            memory_available_gb=8.0,
        )
        await registry.register_agent(agent2)

        task = OffloadTask(
            task_id="task_123",
            mastermind_session_id="session_456",
            task_type="ocr",
            description="Extract text",
            required_capabilities={LocalCapability.OCR},
            required_memory_gb=2.0,
        )

        best = await registry.get_best_agent_for_task(task)

        # Should choose agent2 (lower load)
        assert best is not None
        assert best.agent_id == "cla_2"

    @pytest.mark.asyncio
    async def test_update_agent_status(self, registry):
        """Test updating agent status."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalAgentInfo,
            LocalAgentStatus,
        )

        agent = LocalAgentInfo(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            status=LocalAgentStatus.OFFLINE,
        )
        await registry.register_agent(agent)

        await registry.update_agent_status("cla_123", LocalAgentStatus.ONLINE)

        updated = await registry.get_agent("cla_123")
        assert updated is not None
        assert updated.status == LocalAgentStatus.ONLINE


# =============================================================================
# TEST TASK OFFLOADER
# =============================================================================


class TestTaskOffloader:
    """Tests for TaskOffloader."""

    @pytest_asyncio.fixture
    async def offloader(self):
        """Create a test offloader."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalCapabilityRegistry,
            TaskOffloader,
        )
        registry = LocalCapabilityRegistry()
        return TaskOffloader(registry, prefer_local=True)

    @pytest.mark.asyncio
    async def test_decide_cloud_when_no_agents(self, offloader):
        """Test cloud decision when no local agents available."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            OffloadTask,
            OffloadDecision,
        )

        task = OffloadTask(
            task_id="task_123",
            mastermind_session_id="session_456",
            task_type="ocr",
            description="Extract text",
        )

        decision = await offloader.decide(task)
        assert decision == OffloadDecision.CLOUD

    @pytest.mark.asyncio
    async def test_decide_local_when_agent_available(self, offloader):
        """Test local decision when agent is available."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalAgentInfo,
            LocalCapability,
            LocalAgentStatus,
            OffloadTask,
            OffloadDecision,
        )

        # Register capable agent
        agent = LocalAgentInfo(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            capabilities={LocalCapability.OCR},
            status=LocalAgentStatus.ONLINE,
            memory_available_gb=8.0,
            connection_quality=0.9,
        )
        await offloader.registry.register_agent(agent)

        task = OffloadTask(
            task_id="task_123",
            mastermind_session_id="session_456",
            task_type="ocr",
            description="Extract text",
            required_capabilities={LocalCapability.OCR},
            required_memory_gb=2.0,
        )

        decision = await offloader.decide(task)
        assert decision == OffloadDecision.LOCAL
        assert task.assigned_agent_id == "cla_123"

    @pytest.mark.asyncio
    async def test_decide_cloud_for_critical_tasks(self, offloader):
        """Test cloud decision for critical priority tasks."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalAgentInfo,
            LocalCapability,
            LocalAgentStatus,
            OffloadTask,
            TaskPriority,
            OffloadDecision,
        )

        # Register capable agent
        agent = LocalAgentInfo(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            capabilities={LocalCapability.OCR},
            status=LocalAgentStatus.ONLINE,
            memory_available_gb=8.0,
            connection_quality=0.9,
        )
        await offloader.registry.register_agent(agent)

        # Critical task should go to cloud for reliability
        task = OffloadTask(
            task_id="task_123",
            mastermind_session_id="session_456",
            task_type="ocr",
            description="Critical OCR task",
            required_capabilities={LocalCapability.OCR},
            priority=TaskPriority.CRITICAL,
        )

        decision = await offloader.decide(task)
        assert decision == OffloadDecision.CLOUD


# =============================================================================
# TEST RESOURCE COORDINATOR
# =============================================================================


class TestResourceCoordinator:
    """Tests for ResourceCoordinator."""

    @pytest_asyncio.fixture
    async def coordinator(self):
        """Create a test coordinator."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalCapabilityRegistry,
            TaskOffloader,
            ResourceCoordinator,
        )
        registry = LocalCapabilityRegistry()
        offloader = TaskOffloader(registry, prefer_local=True)
        return ResourceCoordinator(registry, offloader)

    @pytest.mark.asyncio
    async def test_create_allocation_plan(self, coordinator):
        """Test creating an allocation plan."""
        from cirkelline.ckc.mastermind.os_dirigent import OffloadTask

        tasks = [
            OffloadTask(
                task_id="task_1",
                mastermind_session_id="session_456",
                task_type="ocr",
                description="Task 1",
            ),
            OffloadTask(
                task_id="task_2",
                mastermind_session_id="session_456",
                task_type="embedding",
                description="Task 2",
            ),
        ]

        plan = await coordinator.create_allocation_plan("session_456", tasks)

        assert plan.session_id == "session_456"
        assert len(plan.cloud_tasks) == 2  # All cloud since no agents
        assert plan.estimated_cost_usd >= 0


# =============================================================================
# TEST WEBSOCKET AGENT BRIDGE
# =============================================================================


class TestWebSocketAgentBridge:
    """Tests for WebSocketAgentBridge."""

    @pytest_asyncio.fixture
    async def bridge(self):
        """Create a test bridge."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            LocalCapabilityRegistry,
            WebSocketAgentBridge,
        )
        registry = LocalCapabilityRegistry()
        return WebSocketAgentBridge(registry)

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, bridge):
        """Test connect and disconnect."""
        result = await bridge.connect("cla_123")
        assert result is True
        assert await bridge.is_connected("cla_123")

        await bridge.disconnect("cla_123")
        assert not await bridge.is_connected("cla_123")

    @pytest.mark.asyncio
    async def test_send_task(self, bridge):
        """Test sending task to agent."""
        from cirkelline.ckc.mastermind.os_dirigent import OffloadTask

        await bridge.connect("cla_123")

        task = OffloadTask(
            task_id="task_123",
            mastermind_session_id="session_456",
            task_type="ocr",
            description="Extract text",
        )

        result = await bridge.send_task("cla_123", task)
        assert result is True
        assert task.started_at is not None

    @pytest.mark.asyncio
    async def test_send_task_fails_without_connection(self, bridge):
        """Test sending task fails without connection."""
        from cirkelline.ckc.mastermind.os_dirigent import OffloadTask

        task = OffloadTask(
            task_id="task_123",
            mastermind_session_id="session_456",
            task_type="ocr",
            description="Extract text",
        )

        result = await bridge.send_task("cla_123", task)
        assert result is False

    @pytest.mark.asyncio
    async def test_sync_data(self, bridge):
        """Test syncing data batch."""
        from cirkelline.ckc.mastermind.os_dirigent import SyncBatch, SyncDirection

        batch = SyncBatch(
            batch_id="batch_123",
            direction=SyncDirection.TO_LOCAL,
            data_type="embeddings",
            items=[{"id": "1"}, {"id": "2"}],
        )

        result = await bridge.sync_data(batch)

        assert result.synced_at is not None
        assert result.items_synced == 2


# =============================================================================
# TEST OS DIRIGENT MAIN CLASS
# =============================================================================


class TestOSDirigent:
    """Tests for OSDirigent main class."""

    @pytest_asyncio.fixture
    async def dirigent(self):
        """Create a test dirigent."""
        from cirkelline.ckc.mastermind.os_dirigent import OSDirigent

        dirigent = OSDirigent(
            prefer_local=True,
            enable_sync=False,  # Disable for tests
            heartbeat_interval_seconds=60,
        )
        await dirigent.start()
        yield dirigent
        await dirigent.stop()

    @pytest.mark.asyncio
    async def test_register_local_agent(self, dirigent):
        """Test registering a local agent."""
        agent = await dirigent.register_local_agent(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            capabilities=["ocr", "embedding"],
            memory_available_gb=8.0,
        )

        assert agent.agent_id == "cla_123"
        assert len(agent.capabilities) == 2

        agents = await dirigent.get_local_agents()
        assert len(agents) == 1

    @pytest.mark.asyncio
    async def test_unregister_local_agent(self, dirigent):
        """Test unregistering a local agent."""
        await dirigent.register_local_agent(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            capabilities=["ocr"],
        )

        await dirigent.unregister_local_agent("cla_123")

        agents = await dirigent.get_local_agents()
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_offload_task(self, dirigent):
        """Test offloading a task."""
        # Register agent first
        await dirigent.register_local_agent(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            capabilities=["ocr"],
            memory_available_gb=8.0,
        )

        task = await dirigent.offload_task(
            task_id="task_123",
            mastermind_session_id="session_456",
            task_type="ocr",
            description="Extract text from image",
            required_capabilities=["ocr"],
            parameters={"file": "test.png"},
        )

        assert task.task_id == "task_123"
        assert task.decision is not None

    @pytest.mark.asyncio
    async def test_queue_sync(self, dirigent):
        """Test queuing sync batch."""
        batch = await dirigent.queue_sync(
            data_type="embeddings",
            items=[{"id": "1", "vector": [0.1, 0.2]}],
            direction="to_local",
        )

        assert batch.batch_id is not None
        assert batch.data_type == "embeddings"
        assert len(batch.items) == 1

    @pytest.mark.asyncio
    async def test_get_agent_capabilities(self, dirigent):
        """Test getting agent capabilities."""
        from cirkelline.ckc.mastermind.os_dirigent import LocalCapability

        await dirigent.register_local_agent(
            agent_id="cla_123",
            device_id="device_456",
            user_id="user_789",
            capabilities=["ocr", "embedding"],
        )

        caps = await dirigent.get_agent_capabilities("cla_123")

        assert caps is not None
        assert LocalCapability.OCR in caps
        assert LocalCapability.EMBEDDING in caps

    @pytest.mark.asyncio
    async def test_create_allocation_plan(self, dirigent):
        """Test creating allocation plan."""
        from cirkelline.ckc.mastermind.os_dirigent import OffloadTask

        tasks = [
            OffloadTask(
                task_id="task_1",
                mastermind_session_id="session_456",
                task_type="ocr",
                description="Task 1",
            ),
        ]

        plan = await dirigent.create_allocation_plan("session_456", tasks)

        assert plan.session_id == "session_456"


# =============================================================================
# TEST FACTORY FUNCTIONS
# =============================================================================


class TestFactoryFunctions:
    """Tests for factory functions."""

    @pytest.mark.asyncio
    async def test_create_os_dirigent(self):
        """Test create_os_dirigent factory."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            create_os_dirigent,
            get_os_dirigent,
            OSDirigent,
        )

        dirigent = await create_os_dirigent(
            prefer_local=True,
            enable_sync=False,
        )

        assert isinstance(dirigent, OSDirigent)

        # Should be accessible via get
        retrieved = get_os_dirigent()
        assert retrieved is dirigent

        await dirigent.stop()

    @pytest.mark.asyncio
    async def test_create_local_agent_bridge(self):
        """Test create_local_agent_bridge factory."""
        from cirkelline.ckc.mastermind.os_dirigent import (
            create_local_agent_bridge,
            get_local_agent_bridge,
            LocalAgentBridge,
        )

        bridge = await create_local_agent_bridge()

        assert isinstance(bridge, LocalAgentBridge)

        # Should be accessible via get
        retrieved = get_local_agent_bridge()
        assert retrieved is bridge


# =============================================================================
# TEST MODULE IMPORTS
# =============================================================================


class TestModuleImports:
    """Tests for module imports from mastermind package."""

    def test_import_from_mastermind(self):
        """Test importing OS-Dirigent from mastermind package."""
        from cirkelline.ckc.mastermind import (
            # Enums
            LocalAgentStatus,
            OffloadDecision,
            LocalCapability,
            TaskPriority,
            SyncDirection,
            # Data classes
            LocalAgentInfo,
            OffloadTask,
            SyncBatch,
            ResourceAllocationPlan,
            # Classes
            LocalCapabilityRegistry,
            TaskOffloader,
            ResourceCoordinator,
            LocalAgentBridge,
            WebSocketAgentBridge,
            OSDirigent,
            # Factory functions
            create_os_dirigent,
            get_os_dirigent,
            create_local_agent_bridge,
            get_local_agent_bridge,
        )

        # Verify imports
        assert LocalAgentStatus is not None
        assert OffloadDecision is not None
        assert LocalCapability is not None
        assert OSDirigent is not None
        assert create_os_dirigent is not None

    def test_all_exports_accessible(self):
        """Test that all __all__ exports are accessible."""
        from cirkelline.ckc.mastermind import __all__

        # OS-Dirigent exports should be in __all__
        os_dirigent_exports = [
            "LocalAgentStatus",
            "OffloadDecision",
            "LocalCapability",
            "TaskPriority",
            "SyncDirection",
            "LocalAgentInfo",
            "OffloadTask",
            "SyncBatch",
            "ResourceAllocationPlan",
            "LocalCapabilityRegistry",
            "TaskOffloader",
            "ResourceCoordinator",
            "LocalAgentBridge",
            "WebSocketAgentBridge",
            "OSDirigent",
            "create_os_dirigent",
            "get_os_dirigent",
            "create_local_agent_bridge",
            "get_local_agent_bridge",
        ]

        for export in os_dirigent_exports:
            assert export in __all__, f"{export} not in __all__"
