"""
Headquarters Agents
===================
Core agents for mission coordination and system management.

Agents:
- Coordinator: Mission breakdown and agent assignment
- Monitor: System health and metrics aggregation
- Scheduler: Task prioritization and workload balancing
- Dispatcher: Request routing and capability matching
"""

__version__ = "1.0.0"

from cirkelline.headquarters.agents.coordinator import (
    CoordinatorAgent,
    get_coordinator,
)

from cirkelline.headquarters.agents.monitor import (
    MonitorAgent,
    get_monitor,
)

from cirkelline.headquarters.agents.scheduler import (
    SchedulerAgent,
    get_scheduler,
)

from cirkelline.headquarters.agents.dispatcher import (
    DispatcherAgent,
    get_dispatcher,
)

__all__ = [
    'CoordinatorAgent',
    'get_coordinator',
    'MonitorAgent',
    'get_monitor',
    'SchedulerAgent',
    'get_scheduler',
    'DispatcherAgent',
    'get_dispatcher',
]
