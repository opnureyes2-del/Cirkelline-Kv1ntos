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

from cirkelline.context.collector import (
    ContextCollector,
    ContextSource,
    ContextType,
    get_context_collector,
)

from cirkelline.context.system_status import (
    SystemStatus,
    ServiceHealth,
    HealthStatus,
    get_system_status,
)

from cirkelline.context.agent_protocol import (
    AgentMessage,
    MessageType,
    AgentCapability,
    create_agent_message,
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
