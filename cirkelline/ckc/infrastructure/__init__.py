"""
CKC Infrastructure Layer
=========================

Database, Message Queue, og Connector infrastruktur for CKC.

Komponenter:
    - database: AsyncPG connection pool og repository pattern
    - message_bus: RabbitMQ/Redis hybrid event bus (Fase 1.2)
    - connector_registry: Platform connector management (Fase 1.3)
    - knowledge_sync: Knowledge sync interface (Fase 1.4)
"""

from .database import (
    CKCDatabase,
    get_database,
    close_database,
    DatabaseConfig,
)

from .repositories import (
    TaskContextRepository,
    WorkflowStepRepository,
    AgentMemoryRepository,
    LearningEventRepository,
    ILCPMessageRepository,
    KnowledgeEntryRepository,
    AuditTrailRepository,
    WorkLoopSequenceRepository,
    MemoryType,
)

from .message_bus import (
    CKCEventBus,
    get_event_bus,
    close_event_bus,
    MessageBusConfig,
    CKCMessage,
    MessagePriority,
    ExchangeNames,
)

from .connector_registry import (
    ConnectorRegistry,
    ConnectorInfo,
    RegistryEvent,
    get_connector_registry,
    close_connector_registry,
    initialize_default_connectors,
)

from .knowledge_sync import (
    KnowledgeSyncManager,
    KnowledgeEntry,
    KnowledgeSource,
    LocalKnowledgeSource,
    InMemoryKnowledgeSource,
    SyncDirection,
    SyncStatus,
    SyncResult,
    ConflictResolution,
    get_sync_manager,
    close_sync_manager,
)

from .knowledge_interface import (
    search_knowledge,
    get_entry,
    create_entry,
    update_entry,
    delete_entry,
    list_entries,
    sync_sources,
    list_sources,
    get_sync_status,
)

from .state_manager import (
    StateManager,
    TaskState,
    StateCheckpoint,
    SpecialistMetrics,
    TaskExecutionStatus,
    CheckpointType,
    get_state_manager,
    close_state_manager,
)

__all__ = [
    # Database
    "CKCDatabase",
    "get_database",
    "close_database",
    "DatabaseConfig",
    # Repositories
    "TaskContextRepository",
    "WorkflowStepRepository",
    "AgentMemoryRepository",
    "LearningEventRepository",
    "ILCPMessageRepository",
    "KnowledgeEntryRepository",
    "AuditTrailRepository",
    "WorkLoopSequenceRepository",
    "MemoryType",
    # Message Bus
    "CKCEventBus",
    "get_event_bus",
    "close_event_bus",
    "MessageBusConfig",
    "CKCMessage",
    "MessagePriority",
    "ExchangeNames",
    # Connector Registry
    "ConnectorRegistry",
    "ConnectorInfo",
    "RegistryEvent",
    "get_connector_registry",
    "close_connector_registry",
    "initialize_default_connectors",
    # Knowledge Sync
    "KnowledgeSyncManager",
    "KnowledgeEntry",
    "KnowledgeSource",
    "LocalKnowledgeSource",
    "InMemoryKnowledgeSource",
    "SyncDirection",
    "SyncStatus",
    "SyncResult",
    "ConflictResolution",
    "get_sync_manager",
    "close_sync_manager",
    # Knowledge Interface
    "search_knowledge",
    "get_entry",
    "create_entry",
    "update_entry",
    "delete_entry",
    "list_entries",
    "sync_sources",
    "list_sources",
    "get_sync_status",
    # State Manager
    "StateManager",
    "TaskState",
    "StateCheckpoint",
    "SpecialistMetrics",
    "TaskExecutionStatus",
    "CheckpointType",
    "get_state_manager",
    "close_state_manager",
]
