"""
Cirkelline Context Module
=========================
Context collection, aggregation, and injection for agents.

Components:
- Context Collector: Gathers context from multiple sources
- System Status: CI/CD, database, service health
- Agent Protocol: Communication standards between agents

Usage:
    from cirkelline.context import (
        ContextCollector,
        SystemStatus,
        AgentMessage,
        get_context_collector,
    )
"""

__version__ = "1.0.0"

from cirkelline.context.agent_protocol import (
    AgentCapability,
    AgentMessage,
    MessageType,
    create_agent_message,
)
from cirkelline.context.collector import (
    ContextCollector,
    ContextSource,
    ContextType,
    get_context_collector,
)
from cirkelline.context.system_status import (
    HealthStatus,
    ServiceHealth,
    SystemStatus,
    get_system_status,
)

__all__ = [
    # Context Collector
    'ContextCollector',
    'ContextSource',
    'ContextType',
    'get_context_collector',

    # System Status
    'SystemStatus',
    'ServiceHealth',
    'HealthStatus',
    'get_system_status',

    # Agent Protocol
    'AgentMessage',
    'MessageType',
    'AgentCapability',
    'create_agent_message',
]
