"""
CKC MASTERMIND Resource Management
===================================

Dynamisk allokering og styring af ressourcer.

Features:
- Resource allocation baseret på behov
- API kapacitetsreservation
- Budget tracking
- Load balancing
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .coordinator import (
    MastermindSession,
    MastermindPriority,
    MastermindTask,
    TaskStatus,
    AgentParticipation,
)

logger = logging.getLogger(__name__)


# =============================================================================
# RESOURCE ENUMS
# =============================================================================

class ResourceType(Enum):
    """Typer af ressourcer."""
    COMPUTE = "compute"
    API_CALLS = "api_calls"
    MEMORY = "memory"
    STORAGE = "storage"
    BUDGET = "budget"


class AllocationStrategy(Enum):
    """Strategier for ressourceallokering."""
    FAIR_SHARE = "fair_share"       # Lige fordeling
    PRIORITY_BASED = "priority"      # Baseret på prioritet
    DEMAND_BASED = "demand"          # Baseret på efterspørgsel
    ROUND_ROBIN = "round_robin"      # Cirkulær fordeling


# =============================================================================
# RESOURCE DATA CLASSES
# =============================================================================

@dataclass
class ResourcePool:
    """En pulje af ressourcer."""
    pool_id: str
    resource_type: ResourceType
    total_capacity: float
    available: float
    unit: str = "units"
    reservations: Dict[str, float] = field(default_factory=dict)

    def reserve(self, reservation_id: str, amount: float) -> bool:
        """Reservér ressourcer."""
        if amount > self.available:
            return False

        self.available -= amount
        self.reservations[reservation_id] = amount
        return True

    def release(self, reservation_id: str) -> float:
        """Frigiv reservation."""
        if reservation_id not in self.reservations:
            return 0.0

        amount = self.reservations.pop(reservation_id)
        self.available += amount
        return amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pool_id": self.pool_id,
            "resource_type": self.resource_type.value,
            "total_capacity": self.total_capacity,
            "available": self.available,
            "unit": self.unit,
            "utilization_percent": ((self.total_capacity - self.available) / self.total_capacity * 100) if self.total_capacity > 0 else 0,
            "reservations": self.reservations
        }


@dataclass
class ResourceAllocation:
    """En ressourceallokering."""
    allocation_id: str
    session_id: str
    agent_id: str
    allocations: Dict[ResourceType, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allocation_id": self.allocation_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "allocations": {k.value: v for k, v in self.allocations.items()},
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status
        }


@dataclass
class APIReservation:
    """Reservation af API kapacitet."""
    reservation_id: str
    api_name: str
    session_id: str
    calls_reserved: int
    calls_used: int = 0
    cost_per_call: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    @property
    def calls_remaining(self) -> int:
        return self.calls_reserved - self.calls_used

    @property
    def estimated_cost(self) -> float:
        return self.calls_used * self.cost_per_call

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "api_name": self.api_name,
            "session_id": self.session_id,
            "calls_reserved": self.calls_reserved,
            "calls_used": self.calls_used,
            "calls_remaining": self.calls_remaining,
            "cost_per_call": self.cost_per_call,
            "estimated_cost": self.estimated_cost,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


# =============================================================================
# RESOURCE ALLOCATOR
# =============================================================================

class ResourceAllocator:
    """
    Dynamisk allokering af ressourcer til MASTERMIND opgaver.

    Features:
    - Allokering baseret på opgavekompleksitet
    - Agent tilgængelighed
    - Budget begrænsninger
    - Prioritetsbaseret fordeling
    """

    def __init__(
        self,
        default_strategy: AllocationStrategy = AllocationStrategy.PRIORITY_BASED
    ):
        self.default_strategy = default_strategy

        # Resource pools
        self._pools: Dict[ResourceType, ResourcePool] = {}
        self._initialize_default_pools()

        # Allocations
        self._allocations: Dict[str, ResourceAllocation] = {}

        # API reservations
        self._api_reservations: Dict[str, APIReservation] = {}

        # Budget tracking per session
        self._session_budgets: Dict[str, Dict[str, float]] = {}

    def _initialize_default_pools(self) -> None:
        """Initialisér standard resource pools."""
        self._pools[ResourceType.COMPUTE] = ResourcePool(
            pool_id="pool_compute",
            resource_type=ResourceType.COMPUTE,
            total_capacity=100.0,
            available=100.0,
            unit="units"
        )

        self._pools[ResourceType.API_CALLS] = ResourcePool(
            pool_id="pool_api",
            resource_type=ResourceType.API_CALLS,
            total_capacity=10000.0,
            available=10000.0,
            unit="calls"
        )

        self._pools[ResourceType.MEMORY] = ResourcePool(
            pool_id="pool_memory",
            resource_type=ResourceType.MEMORY,
            total_capacity=8192.0,  # MB
            available=8192.0,
            unit="MB"
        )

    async def allocate_for_session(
        self,
        session: MastermindSession,
        strategy: Optional[AllocationStrategy] = None
    ) -> Dict[str, ResourceAllocation]:
        """
        Allokér ressourcer til en session.

        Args:
            session: MASTERMIND session
            strategy: Allokeringsstrategi

        Returns:
            Dict af allokeringer per agent
        """
        strategy = strategy or self.default_strategy
        allocations = {}

        # Beregn total ressourcebehov
        total_agents = len(session.active_agents) + len(session.active_kommandanter)

        if total_agents == 0:
            return allocations

        # Alloker baseret på strategi
        if strategy == AllocationStrategy.FAIR_SHARE:
            allocations = await self._allocate_fair_share(session, total_agents)
        elif strategy == AllocationStrategy.PRIORITY_BASED:
            allocations = await self._allocate_priority_based(session)
        elif strategy == AllocationStrategy.DEMAND_BASED:
            allocations = await self._allocate_demand_based(session)
        else:
            allocations = await self._allocate_round_robin(session, total_agents)

        logger.info(f"Ressourcer allokeret til session {session.session_id}: {len(allocations)} allokeringer")
        return allocations

    async def _allocate_fair_share(
        self,
        session: MastermindSession,
        total_agents: int
    ) -> Dict[str, ResourceAllocation]:
        """Fair share allokering - lige fordeling."""
        allocations = {}

        for pool in self._pools.values():
            share = pool.available / total_agents

            all_agents = {
                **session.active_agents,
                **session.active_kommandanter
            }

            for agent_id in all_agents:
                if agent_id not in allocations:
                    allocations[agent_id] = ResourceAllocation(
                        allocation_id=f"alloc_{secrets.token_hex(6)}",
                        session_id=session.session_id,
                        agent_id=agent_id
                    )

                allocations[agent_id].allocations[pool.resource_type] = share
                pool.reserve(allocations[agent_id].allocation_id, share)

        return allocations

    async def _allocate_priority_based(
        self,
        session: MastermindSession
    ) -> Dict[str, ResourceAllocation]:
        """Prioritetsbaseret allokering - mere til højprioritet."""
        allocations = {}

        # Beregn vægte baseret på prioritet
        weights: Dict[str, float] = {}
        total_weight = 0.0

        all_agents = {
            **session.active_agents,
            **session.active_kommandanter
        }

        for agent_id, agent in all_agents.items():
            # Kommandanter får højere vægt
            if agent.role.value == "kommandant":
                weight = 2.0
            else:
                weight = 1.0

            weights[agent_id] = weight
            total_weight += weight

        # Alloker baseret på vægte
        for pool in self._pools.values():
            for agent_id, weight in weights.items():
                share = (weight / total_weight) * pool.available

                if agent_id not in allocations:
                    allocations[agent_id] = ResourceAllocation(
                        allocation_id=f"alloc_{secrets.token_hex(6)}",
                        session_id=session.session_id,
                        agent_id=agent_id
                    )

                allocations[agent_id].allocations[pool.resource_type] = share
                pool.reserve(allocations[agent_id].allocation_id, share)

        return allocations

    async def _allocate_demand_based(
        self,
        session: MastermindSession
    ) -> Dict[str, ResourceAllocation]:
        """Efterspørgselsbaseret allokering."""
        allocations = {}

        # Beregn efterspørgsel baseret på ventende opgaver
        demand: Dict[str, int] = {}

        for task in session.tasks.values():
            if task.assigned_to and task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
                demand[task.assigned_to] = demand.get(task.assigned_to, 0) + 1

        total_demand = sum(demand.values()) or 1

        for pool in self._pools.values():
            all_agents = {
                **session.active_agents,
                **session.active_kommandanter
            }

            for agent_id in all_agents:
                agent_demand = demand.get(agent_id, 1)
                share = (agent_demand / total_demand) * pool.available

                if agent_id not in allocations:
                    allocations[agent_id] = ResourceAllocation(
                        allocation_id=f"alloc_{secrets.token_hex(6)}",
                        session_id=session.session_id,
                        agent_id=agent_id
                    )

                allocations[agent_id].allocations[pool.resource_type] = share
                pool.reserve(allocations[agent_id].allocation_id, share)

        return allocations

    async def _allocate_round_robin(
        self,
        session: MastermindSession,
        total_agents: int
    ) -> Dict[str, ResourceAllocation]:
        """Round robin allokering."""
        return await self._allocate_fair_share(session, total_agents)

    async def reallocate_on_feedback(
        self,
        session: MastermindSession,
        feedback: Dict[str, Any]
    ) -> bool:
        """
        Omallokér ressourcer baseret på feedback.

        Args:
            session: MASTERMIND session
            feedback: Feedback data

        Returns:
            True hvis succesfuldt
        """
        # Frigiv eksisterende allokeringer
        session_allocations = [
            a for a in self._allocations.values()
            if a.session_id == session.session_id
        ]

        for allocation in session_allocations:
            await self.release_allocation(allocation.allocation_id)

        # Reallokér med ny strategi baseret på feedback
        strategy = AllocationStrategy.DEMAND_BASED

        if feedback.get("issues"):
            # Hvis der er issues, brug prioritetsbaseret
            strategy = AllocationStrategy.PRIORITY_BASED

        await self.allocate_for_session(session, strategy)

        logger.info(f"Ressourcer omallokeret for session {session.session_id}")
        return True

    async def release_allocation(self, allocation_id: str) -> bool:
        """Frigiv en allokering."""
        allocation = self._allocations.get(allocation_id)

        if not allocation:
            return False

        for resource_type, amount in allocation.allocations.items():
            pool = self._pools.get(resource_type)
            if pool:
                pool.release(allocation_id)

        allocation.status = "released"
        del self._allocations[allocation_id]

        return True

    # -------------------------------------------------------------------------
    # API CAPACITY RESERVATION
    # -------------------------------------------------------------------------

    async def reserve_api_capacity(
        self,
        session_id: str,
        api_name: str,
        calls: int,
        cost_per_call: float = 0.0,
        duration_minutes: int = 60
    ) -> APIReservation:
        """
        Reservér API kapacitet.

        Args:
            session_id: Session ID
            api_name: API navn
            calls: Antal kald at reservere
            cost_per_call: Pris per kald
            duration_minutes: Varighed af reservation

        Returns:
            APIReservation
        """
        reservation = APIReservation(
            reservation_id=f"apires_{secrets.token_hex(6)}",
            api_name=api_name,
            session_id=session_id,
            calls_reserved=calls,
            cost_per_call=cost_per_call,
            expires_at=datetime.now() + timedelta(minutes=duration_minutes)
        )

        self._api_reservations[reservation.reservation_id] = reservation

        logger.info(f"API kapacitet reserveret: {calls} kald til {api_name}")
        return reservation

    async def use_api_call(
        self,
        reservation_id: str,
        calls: int = 1
    ) -> bool:
        """Brug API kald fra reservation."""
        reservation = self._api_reservations.get(reservation_id)

        if not reservation:
            return False

        if reservation.calls_remaining < calls:
            return False

        reservation.calls_used += calls
        return True

    async def release_api_reservation(self, reservation_id: str) -> float:
        """Frigiv API reservation. Returnerer faktisk forbrug."""
        reservation = self._api_reservations.get(reservation_id)

        if not reservation:
            return 0.0

        cost = reservation.estimated_cost
        del self._api_reservations[reservation_id]

        return cost

    def get_api_reservations(
        self,
        session_id: Optional[str] = None
    ) -> List[APIReservation]:
        """Hent API reservationer."""
        reservations = list(self._api_reservations.values())

        if session_id:
            reservations = [r for r in reservations if r.session_id == session_id]

        return reservations

    # -------------------------------------------------------------------------
    # BUDGET TRACKING
    # -------------------------------------------------------------------------

    def set_session_budget(
        self,
        session_id: str,
        budget_usd: float
    ) -> None:
        """Sæt budget for session."""
        self._session_budgets[session_id] = {
            "total": budget_usd,
            "consumed": 0.0,
            "reserved": 0.0
        }

    def consume_budget(
        self,
        session_id: str,
        amount: float,
        category: str = "general"
    ) -> bool:
        """Forbrug fra budget."""
        if session_id not in self._session_budgets:
            return False

        budget = self._session_budgets[session_id]
        remaining = budget["total"] - budget["consumed"] - budget["reserved"]

        if amount > remaining:
            return False

        budget["consumed"] += amount
        return True

    def reserve_budget(
        self,
        session_id: str,
        amount: float
    ) -> bool:
        """Reservér budget."""
        if session_id not in self._session_budgets:
            return False

        budget = self._session_budgets[session_id]
        remaining = budget["total"] - budget["consumed"] - budget["reserved"]

        if amount > remaining:
            return False

        budget["reserved"] += amount
        return True

    def release_budget_reservation(
        self,
        session_id: str,
        amount: float
    ) -> bool:
        """Frigiv budget reservation."""
        if session_id not in self._session_budgets:
            return False

        budget = self._session_budgets[session_id]
        budget["reserved"] = max(0, budget["reserved"] - amount)
        return True

    def get_budget_status(self, session_id: str) -> Dict[str, float]:
        """Hent budget status."""
        if session_id not in self._session_budgets:
            return {"total": 0, "consumed": 0, "reserved": 0, "available": 0}

        budget = self._session_budgets[session_id]
        return {
            **budget,
            "available": budget["total"] - budget["consumed"] - budget["reserved"]
        }

    # -------------------------------------------------------------------------
    # POOL MANAGEMENT
    # -------------------------------------------------------------------------

    def get_pool_status(
        self,
        resource_type: Optional[ResourceType] = None
    ) -> Dict[str, Any]:
        """Hent pool status."""
        if resource_type:
            pool = self._pools.get(resource_type)
            return pool.to_dict() if pool else {}

        return {
            rt.value: pool.to_dict()
            for rt, pool in self._pools.items()
        }

    def add_to_pool(
        self,
        resource_type: ResourceType,
        amount: float
    ) -> bool:
        """Tilføj til resource pool."""
        pool = self._pools.get(resource_type)

        if not pool:
            return False

        pool.total_capacity += amount
        pool.available += amount
        return True


# =============================================================================
# LOAD BALANCER
# =============================================================================

class LoadBalancer:
    """
    Load balancing for agent opgaver.

    Features:
    - Jævn fordeling af opgaver
    - Overvågning af agent belastning
    - Automatisk rebalancing
    """

    def __init__(self, max_load_per_agent: int = 5):
        self.max_load_per_agent = max_load_per_agent
        self._agent_loads: Dict[str, int] = {}

    def get_least_loaded_agent(
        self,
        available_agents: List[str]
    ) -> Optional[str]:
        """Find agent med lavest belastning."""
        if not available_agents:
            return None

        # Find mindst belastede agent
        min_load = float('inf')
        selected = None

        for agent_id in available_agents:
            load = self._agent_loads.get(agent_id, 0)

            if load < self.max_load_per_agent and load < min_load:
                min_load = load
                selected = agent_id

        return selected

    def assign_task(self, agent_id: str) -> bool:
        """Registrer opgavetildeling."""
        current_load = self._agent_loads.get(agent_id, 0)

        if current_load >= self.max_load_per_agent:
            return False

        self._agent_loads[agent_id] = current_load + 1
        return True

    def release_task(self, agent_id: str) -> None:
        """Frigiv opgave fra agent."""
        if agent_id in self._agent_loads:
            self._agent_loads[agent_id] = max(0, self._agent_loads[agent_id] - 1)

    def get_agent_load(self, agent_id: str) -> int:
        """Hent agent belastning."""
        return self._agent_loads.get(agent_id, 0)

    def get_all_loads(self) -> Dict[str, int]:
        """Hent alle agent belastninger."""
        return self._agent_loads.copy()

    def is_balanced(self, threshold: float = 0.3) -> bool:
        """Check om belastningen er balanceret."""
        if not self._agent_loads:
            return True

        loads = list(self._agent_loads.values())
        avg = sum(loads) / len(loads)

        if avg == 0:
            return True

        for load in loads:
            deviation = abs(load - avg) / avg
            if deviation > threshold:
                return False

        return True


# =============================================================================
# FACTORY
# =============================================================================

_resource_allocator_instance: Optional[ResourceAllocator] = None
_load_balancer_instance: Optional[LoadBalancer] = None


def create_resource_allocator(
    strategy: AllocationStrategy = AllocationStrategy.PRIORITY_BASED
) -> ResourceAllocator:
    """Opret ResourceAllocator instance."""
    global _resource_allocator_instance
    _resource_allocator_instance = ResourceAllocator(default_strategy=strategy)
    return _resource_allocator_instance


def get_resource_allocator() -> Optional[ResourceAllocator]:
    """Hent den aktuelle ResourceAllocator instance."""
    return _resource_allocator_instance


def create_load_balancer(max_load: int = 5) -> LoadBalancer:
    """Opret LoadBalancer instance."""
    global _load_balancer_instance
    _load_balancer_instance = LoadBalancer(max_load_per_agent=max_load)
    return _load_balancer_instance


def get_load_balancer() -> Optional[LoadBalancer]:
    """Hent den aktuelle LoadBalancer instance."""
    return _load_balancer_instance
