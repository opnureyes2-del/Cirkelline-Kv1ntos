"""
Tests for CKC MASTERMIND Resource Management (cirkelline.ckc.mastermind.resources)
==================================================================================

Tests covering:
- Enums: ResourceType, AllocationStrategy
- Data Classes: ResourcePool, ResourceAllocation, APIReservation
- ResourceAllocator
- LoadBalancer
- Factory functions
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from cirkelline.ckc.mastermind.resources import (
    # Enums
    ResourceType,
    AllocationStrategy,
    # Data Classes
    ResourcePool,
    ResourceAllocation,
    APIReservation,
    # Classes
    ResourceAllocator,
    LoadBalancer,
    # Factory functions
    create_resource_allocator,
    get_resource_allocator,
    create_load_balancer,
    get_load_balancer,
)
from cirkelline.ckc.mastermind.coordinator import (
    MastermindSession,
    MastermindTask,
    TaskStatus,
    AgentParticipation,
    ParticipantRole,
    MastermindPriority,
)


# =============================================================================
# TESTS FOR ENUMS
# =============================================================================

class TestResourceEnums:
    """Tests for resource enums."""

    def test_resource_type_values(self):
        """Test ResourceType values."""
        assert ResourceType.COMPUTE.value == "compute"
        assert ResourceType.API_CALLS.value == "api_calls"
        assert ResourceType.MEMORY.value == "memory"
        assert ResourceType.STORAGE.value == "storage"
        assert ResourceType.BUDGET.value == "budget"

    def test_allocation_strategy_values(self):
        """Test AllocationStrategy values."""
        assert AllocationStrategy.FAIR_SHARE.value == "fair_share"
        assert AllocationStrategy.PRIORITY_BASED.value == "priority"
        assert AllocationStrategy.DEMAND_BASED.value == "demand"
        assert AllocationStrategy.ROUND_ROBIN.value == "round_robin"


# =============================================================================
# TESTS FOR DATA CLASSES
# =============================================================================

class TestResourcePool:
    """Tests for ResourcePool dataclass."""

    def test_pool_creation(self):
        """Test creating a resource pool."""
        pool = ResourcePool(
            pool_id="pool_001",
            resource_type=ResourceType.COMPUTE,
            total_capacity=100.0,
            available=100.0
        )
        assert pool.pool_id == "pool_001"
        assert pool.total_capacity == 100.0
        assert pool.available == 100.0
        assert pool.unit == "units"  # default

    def test_pool_reserve_success(self):
        """Test successful reservation."""
        pool = ResourcePool(
            pool_id="pool_001",
            resource_type=ResourceType.COMPUTE,
            total_capacity=100.0,
            available=100.0
        )

        result = pool.reserve("res_001", 30.0)

        assert result is True
        assert pool.available == 70.0
        assert "res_001" in pool.reservations
        assert pool.reservations["res_001"] == 30.0

    def test_pool_reserve_insufficient(self):
        """Test reservation with insufficient capacity."""
        pool = ResourcePool(
            pool_id="pool_001",
            resource_type=ResourceType.COMPUTE,
            total_capacity=100.0,
            available=20.0
        )

        result = pool.reserve("res_001", 50.0)

        assert result is False
        assert pool.available == 20.0

    def test_pool_release(self):
        """Test releasing a reservation."""
        pool = ResourcePool(
            pool_id="pool_001",
            resource_type=ResourceType.COMPUTE,
            total_capacity=100.0,
            available=70.0,
            reservations={"res_001": 30.0}
        )

        released = pool.release("res_001")

        assert released == 30.0
        assert pool.available == 100.0
        assert "res_001" not in pool.reservations

    def test_pool_release_nonexistent(self):
        """Test releasing nonexistent reservation."""
        pool = ResourcePool(
            pool_id="pool_001",
            resource_type=ResourceType.COMPUTE,
            total_capacity=100.0,
            available=100.0
        )

        released = pool.release("nonexistent")

        assert released == 0.0

    def test_pool_to_dict(self):
        """Test pool serialization."""
        pool = ResourcePool(
            pool_id="pool_001",
            resource_type=ResourceType.API_CALLS,
            total_capacity=1000.0,
            available=800.0,
            unit="calls"
        )

        data = pool.to_dict()

        assert data["pool_id"] == "pool_001"
        assert data["resource_type"] == "api_calls"
        assert data["utilization_percent"] == 20.0


class TestResourceAllocation:
    """Tests for ResourceAllocation dataclass."""

    def test_allocation_creation(self):
        """Test creating a resource allocation."""
        allocation = ResourceAllocation(
            allocation_id="alloc_001",
            session_id="s001",
            agent_id="agent_001"
        )
        assert allocation.allocation_id == "alloc_001"
        assert allocation.status == "active"  # default

    def test_allocation_with_resources(self):
        """Test allocation with resource types."""
        allocation = ResourceAllocation(
            allocation_id="alloc_002",
            session_id="s002",
            agent_id="agent_002",
            allocations={
                ResourceType.COMPUTE: 10.0,
                ResourceType.MEMORY: 512.0
            }
        )

        assert allocation.allocations[ResourceType.COMPUTE] == 10.0
        assert allocation.allocations[ResourceType.MEMORY] == 512.0

    def test_allocation_to_dict(self):
        """Test allocation serialization."""
        allocation = ResourceAllocation(
            allocation_id="alloc_003",
            session_id="s003",
            agent_id="agent_003",
            allocations={ResourceType.COMPUTE: 5.0}
        )

        data = allocation.to_dict()

        assert data["allocation_id"] == "alloc_003"
        assert data["allocations"]["compute"] == 5.0


class TestAPIReservation:
    """Tests for APIReservation dataclass."""

    def test_reservation_creation(self):
        """Test creating an API reservation."""
        reservation = APIReservation(
            reservation_id="res_001",
            api_name="gemini",
            session_id="s001",
            calls_reserved=100
        )
        assert reservation.reservation_id == "res_001"
        assert reservation.calls_used == 0  # default

    def test_calls_remaining(self):
        """Test calls remaining property."""
        reservation = APIReservation(
            reservation_id="res_001",
            api_name="gemini",
            session_id="s001",
            calls_reserved=100,
            calls_used=30
        )

        assert reservation.calls_remaining == 70

    def test_estimated_cost(self):
        """Test estimated cost property."""
        reservation = APIReservation(
            reservation_id="res_001",
            api_name="gemini",
            session_id="s001",
            calls_reserved=100,
            calls_used=50,
            cost_per_call=0.01
        )

        assert reservation.estimated_cost == 0.50

    def test_reservation_to_dict(self):
        """Test reservation serialization."""
        reservation = APIReservation(
            reservation_id="res_001",
            api_name="openai",
            session_id="s001",
            calls_reserved=200,
            calls_used=50,
            cost_per_call=0.02
        )

        data = reservation.to_dict()

        assert data["api_name"] == "openai"
        assert data["calls_remaining"] == 150
        assert data["estimated_cost"] == 1.0


# =============================================================================
# TESTS FOR RESOURCE ALLOCATOR
# =============================================================================

class TestResourceAllocator:
    """Tests for ResourceAllocator."""

    @pytest.fixture
    def allocator(self):
        """Create a fresh allocator for each test."""
        return ResourceAllocator()

    @pytest.fixture
    def session(self):
        """Create a test session with agents."""
        session = MastermindSession(
            session_id="test_session",
            primary_objective="Test",
            budget_usd=100.0
        )

        # Add agents
        session.active_agents["agent_001"] = AgentParticipation(
            agent_id="agent_001",
            agent_name="Agent 001",
            role=ParticipantRole.SPECIALIST,
            capabilities=["task_execution"]
        )
        session.active_agents["agent_002"] = AgentParticipation(
            agent_id="agent_002",
            agent_name="Agent 002",
            role=ParticipantRole.SPECIALIST,
            capabilities=["task_execution"]
        )

        return session

    def test_default_pools_initialized(self, allocator):
        """Test that default pools are initialized."""
        assert ResourceType.COMPUTE in allocator._pools
        assert ResourceType.API_CALLS in allocator._pools
        assert ResourceType.MEMORY in allocator._pools

    @pytest.mark.asyncio
    async def test_allocate_for_session_fair_share(self, allocator, session):
        """Test fair share allocation."""
        allocations = await allocator.allocate_for_session(
            session,
            strategy=AllocationStrategy.FAIR_SHARE
        )

        assert len(allocations) == 2
        assert "agent_001" in allocations
        assert "agent_002" in allocations

    @pytest.mark.asyncio
    async def test_allocate_for_session_priority_based(self, allocator, session):
        """Test priority-based allocation."""
        # Add a kommandant
        session.active_kommandanter["cmd_001"] = AgentParticipation(
            agent_id="cmd_001",
            agent_name="Kommandant 001",
            role=ParticipantRole.KOMMANDANT,
            capabilities=["leadership", "coordination"]
        )

        allocations = await allocator.allocate_for_session(
            session,
            strategy=AllocationStrategy.PRIORITY_BASED
        )

        assert len(allocations) == 3
        # Kommandant should have more resources
        cmd_alloc = allocations["cmd_001"]
        agent_alloc = allocations["agent_001"]

        # Kommandant has 2x weight
        assert cmd_alloc.allocations[ResourceType.COMPUTE] > agent_alloc.allocations[ResourceType.COMPUTE]

    @pytest.mark.asyncio
    async def test_allocate_for_session_empty(self, allocator):
        """Test allocation with empty session."""
        session = MastermindSession(session_id="empty", primary_objective="Test")

        allocations = await allocator.allocate_for_session(session)

        assert len(allocations) == 0

    @pytest.mark.asyncio
    async def test_release_allocation(self, allocator, session):
        """Test releasing an allocation."""
        allocations = await allocator.allocate_for_session(session)

        for agent_id, allocation in allocations.items():
            allocator._allocations[allocation.allocation_id] = allocation

        # Release one allocation
        first_id = list(allocations.values())[0].allocation_id
        result = await allocator.release_allocation(first_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_reserve_api_capacity(self, allocator):
        """Test reserving API capacity."""
        reservation = await allocator.reserve_api_capacity(
            session_id="s001",
            api_name="gemini",
            calls=1000,
            cost_per_call=0.001,
            duration_minutes=30
        )

        assert reservation.api_name == "gemini"
        assert reservation.calls_reserved == 1000
        assert reservation.expires_at is not None

    @pytest.mark.asyncio
    async def test_use_api_call(self, allocator):
        """Test using API calls."""
        reservation = await allocator.reserve_api_capacity(
            session_id="s001",
            api_name="openai",
            calls=100
        )

        result = await allocator.use_api_call(reservation.reservation_id, 5)

        assert result is True
        assert allocator._api_reservations[reservation.reservation_id].calls_used == 5

    @pytest.mark.asyncio
    async def test_use_api_call_exceeds_limit(self, allocator):
        """Test using API calls exceeding limit."""
        reservation = await allocator.reserve_api_capacity(
            session_id="s001",
            api_name="openai",
            calls=10
        )

        result = await allocator.use_api_call(reservation.reservation_id, 20)

        assert result is False

    def test_set_session_budget(self, allocator):
        """Test setting session budget."""
        allocator.set_session_budget("s001", 500.0)

        budget = allocator.get_budget_status("s001")
        assert budget["total"] == 500.0
        assert budget["consumed"] == 0.0
        assert budget["available"] == 500.0

    def test_consume_budget(self, allocator):
        """Test consuming from budget."""
        allocator.set_session_budget("s001", 100.0)

        result = allocator.consume_budget("s001", 30.0)

        assert result is True
        budget = allocator.get_budget_status("s001")
        assert budget["consumed"] == 30.0
        assert budget["available"] == 70.0

    def test_consume_budget_exceeds(self, allocator):
        """Test consuming more than available."""
        allocator.set_session_budget("s001", 50.0)

        result = allocator.consume_budget("s001", 100.0)

        assert result is False

    def test_reserve_budget(self, allocator):
        """Test reserving budget."""
        allocator.set_session_budget("s001", 100.0)

        result = allocator.reserve_budget("s001", 40.0)

        assert result is True
        budget = allocator.get_budget_status("s001")
        assert budget["reserved"] == 40.0
        assert budget["available"] == 60.0

    def test_get_pool_status(self, allocator):
        """Test getting pool status."""
        status = allocator.get_pool_status(ResourceType.COMPUTE)

        assert status["resource_type"] == "compute"
        assert status["total_capacity"] == 100.0

    def test_add_to_pool(self, allocator):
        """Test adding to resource pool."""
        result = allocator.add_to_pool(ResourceType.COMPUTE, 50.0)

        assert result is True
        pool = allocator._pools[ResourceType.COMPUTE]
        assert pool.total_capacity == 150.0
        assert pool.available == 150.0


# =============================================================================
# TESTS FOR LOAD BALANCER
# =============================================================================

class TestLoadBalancer:
    """Tests for LoadBalancer."""

    @pytest.fixture
    def balancer(self):
        """Create a fresh load balancer for each test."""
        return LoadBalancer(max_load_per_agent=5)

    def test_get_least_loaded_agent_empty(self, balancer):
        """Test with empty agent list."""
        result = balancer.get_least_loaded_agent([])
        assert result is None

    def test_get_least_loaded_agent(self, balancer):
        """Test finding least loaded agent."""
        balancer._agent_loads = {
            "agent_001": 3,
            "agent_002": 1,
            "agent_003": 4
        }

        result = balancer.get_least_loaded_agent(["agent_001", "agent_002", "agent_003"])

        assert result == "agent_002"

    def test_get_least_loaded_agent_max_reached(self, balancer):
        """Test when all agents are at max load."""
        balancer._agent_loads = {
            "agent_001": 5,
            "agent_002": 5
        }

        result = balancer.get_least_loaded_agent(["agent_001", "agent_002"])

        assert result is None

    def test_assign_task(self, balancer):
        """Test assigning task to agent."""
        result = balancer.assign_task("agent_001")

        assert result is True
        assert balancer._agent_loads["agent_001"] == 1

    def test_assign_task_max_reached(self, balancer):
        """Test assigning when agent at max load."""
        balancer._agent_loads["agent_001"] = 5

        result = balancer.assign_task("agent_001")

        assert result is False

    def test_release_task(self, balancer):
        """Test releasing task from agent."""
        balancer._agent_loads["agent_001"] = 3

        balancer.release_task("agent_001")

        assert balancer._agent_loads["agent_001"] == 2

    def test_release_task_zero(self, balancer):
        """Test releasing doesn't go below zero."""
        balancer._agent_loads["agent_001"] = 0

        balancer.release_task("agent_001")

        assert balancer._agent_loads["agent_001"] == 0

    def test_get_agent_load(self, balancer):
        """Test getting agent load."""
        balancer._agent_loads["agent_001"] = 4

        load = balancer.get_agent_load("agent_001")

        assert load == 4

    def test_get_agent_load_unknown(self, balancer):
        """Test getting load for unknown agent."""
        load = balancer.get_agent_load("unknown")

        assert load == 0

    def test_get_all_loads(self, balancer):
        """Test getting all loads."""
        balancer._agent_loads = {
            "agent_001": 2,
            "agent_002": 3
        }

        loads = balancer.get_all_loads()

        assert loads["agent_001"] == 2
        assert loads["agent_002"] == 3

    def test_is_balanced_empty(self, balancer):
        """Test balance check with no agents."""
        assert balancer.is_balanced() is True

    def test_is_balanced_even(self, balancer):
        """Test balance check with even load."""
        balancer._agent_loads = {
            "agent_001": 3,
            "agent_002": 3,
            "agent_003": 3
        }

        assert balancer.is_balanced() is True

    def test_is_balanced_uneven(self, balancer):
        """Test balance check with uneven load."""
        balancer._agent_loads = {
            "agent_001": 1,
            "agent_002": 5
        }

        # Avg = 3, deviation from 1 is 66%, > 30% threshold
        assert balancer.is_balanced() is False


# =============================================================================
# TESTS FOR FACTORY FUNCTIONS
# =============================================================================

class TestResourceFactoryFunctions:
    """Tests for resource factory functions."""

    def test_create_resource_allocator(self):
        """Test creating resource allocator."""
        allocator = create_resource_allocator()

        assert isinstance(allocator, ResourceAllocator)
        assert allocator.default_strategy == AllocationStrategy.PRIORITY_BASED

    def test_create_resource_allocator_custom_strategy(self):
        """Test creating allocator with custom strategy."""
        allocator = create_resource_allocator(strategy=AllocationStrategy.FAIR_SHARE)

        assert allocator.default_strategy == AllocationStrategy.FAIR_SHARE

    def test_get_resource_allocator(self):
        """Test getting current allocator instance."""
        created = create_resource_allocator()
        retrieved = get_resource_allocator()

        assert retrieved is created

    def test_create_load_balancer(self):
        """Test creating load balancer."""
        balancer = create_load_balancer()

        assert isinstance(balancer, LoadBalancer)
        assert balancer.max_load_per_agent == 5

    def test_create_load_balancer_custom_max(self):
        """Test creating balancer with custom max."""
        balancer = create_load_balancer(max_load=10)

        assert balancer.max_load_per_agent == 10

    def test_get_load_balancer(self):
        """Test getting current balancer instance."""
        created = create_load_balancer()
        retrieved = get_load_balancer()

        assert retrieved is created


# =============================================================================
# TESTS FOR MODULE IMPORTS
# =============================================================================

class TestResourcesModuleImports:
    """Tests for resources module imports."""

    def test_all_exports_importable(self):
        """Test that all expected exports are available."""
        from cirkelline.ckc.mastermind import resources

        # Enums
        assert hasattr(resources, 'ResourceType')
        assert hasattr(resources, 'AllocationStrategy')

        # Data classes
        assert hasattr(resources, 'ResourcePool')
        assert hasattr(resources, 'ResourceAllocation')
        assert hasattr(resources, 'APIReservation')

        # Classes
        assert hasattr(resources, 'ResourceAllocator')
        assert hasattr(resources, 'LoadBalancer')

        # Factory functions
        assert hasattr(resources, 'create_resource_allocator')
        assert hasattr(resources, 'get_resource_allocator')
        assert hasattr(resources, 'create_load_balancer')
        assert hasattr(resources, 'get_load_balancer')
