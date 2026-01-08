"""
Cirkelline Headquarters (HQ)
============================
Central coordination hub for all Cirkelline agents.

Components:
- Event Bus: Redis Streams for async agent communication
- Knowledge Graph: NetworkX for agent/knowledge relationships
- Shared Memory: Redis-backed state for missions & roadmaps
- Mission Control: Coordination of multi-agent tasks

Architecture:
    ┌──────────────────────────────────────────────────┐
    │                  HEADQUARTERS                     │
    │  ┌────────────────────────────────────────────┐  │
    │  │              Event Bus (Redis)              │  │
    │  │  publish() / subscribe() / broadcast()     │  │
    │  └────────────────────────────────────────────┘  │
    │  ┌────────────────────────────────────────────┐  │
    │  │           Knowledge Graph (NetworkX)        │  │
    │  │  agents / tools / knowledge connections    │  │
    │  └────────────────────────────────────────────┘  │
    │  ┌────────────────────────────────────────────┐  │
    │  │          Shared Memory (Redis)              │  │
    │  │  missions / roadmaps / agent states        │  │
    │  └────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────┘
"""

__version__ = "1.0.0"

from cirkelline.headquarters.event_bus import (
    EventBus,
    Event,
    EventType,
    get_event_bus,
)

from cirkelline.headquarters.knowledge_graph import (
    KnowledgeGraph,
    NodeType,
    EdgeType,
    get_knowledge_graph,
)

from cirkelline.headquarters.shared_memory import (
    SharedMemory,
    Mission,
    MissionStatus,
    get_shared_memory,
)

__all__ = [
    # Event Bus
    'EventBus',
    'Event',
    'EventType',
    'get_event_bus',

    # Knowledge Graph
    'KnowledgeGraph',
    'NodeType',
    'EdgeType',
    'get_knowledge_graph',

    # Shared Memory
    'SharedMemory',
    'Mission',
    'MissionStatus',
    'get_shared_memory',
]
