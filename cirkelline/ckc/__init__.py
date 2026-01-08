"""
Cirkelline Kreativ Koordinator (CKC)
====================================

Det ultimative multi-agent system med:
- Decentraliseret videnarkitektur
- Rollebaserede Biblioteks-Kommandanter
- Indbygget robusthed mod korruption
- Zero-Oversight-Drift

Komponenter:
    - CKC Orchestrator (Kommandant-Agent)
    - Learning Rooms (Læringsrum med navn/nummer)
    - 5 Specialiserede Agenter
    - Historiker & Bibliotekar Kommandanter
    - Dashboard med visual status

Avancerede Protokoller:
    - Dynamisk Sikkerhedsjustering (5.1)
    - ILCP - Inter-Læringsrum Kommunikation (5.2)
    - Super-Admin Terminal & EIAP (5.3)
"""

from .learning_rooms import (
    LearningRoom,
    LearningRoomManager,
    RoomStatus,
    create_learning_room,
    get_learning_room,
)

from .orchestrator import (
    CKCOrchestrator,
    ValidationFlow,
    TaskPriority,
    # Work-Loop Sequencer (v1.1.0)
    WorkLoopSequencer,
    WorkLoopStep,
    WorkLoop,
    WorkLoopStepType,
    WorkLoopStatus,
)

from .agents import (
    ToolExplorerAgent,
    CreativeSynthesizerAgent,
    KnowledgeArchitectAgent,
    VirtualWorldBuilderAgent,
    QualityAssuranceAgent,
)

from .kommandanter import (
    HistorikerKommandant,
    BibliotekarKommandant,
)

from .security import (
    InputSanitizer,
    CorruptionDetector,
    IntegrityValidator,
)

from .dashboard import (
    StatusDot,
    DashboardManager,
    AcuteNotificationPage,
)

from .advanced_protocols import (
    DynamicSecurityManager,
    SecurityLevel,
    ILCPManager,
    ILCPMessage,
    CKCSuperAdminTerminal,
    HITLApprovalRequest,
    get_security_manager,
    get_ilcp_manager,
    get_terminal,
    # New v1.1.0 exports
    ValidationMode,
    MessageType,
    MessagePriority,
    ILCP_MESSAGE_SCHEMA,
    ILCP_DATA_REQUEST_SCHEMA,
    ILCP_DATA_RESPONSE_SCHEMA,
    ILCP_KNOWLEDGE_SHARE_SCHEMA,
)

from .context import (
    TaskContext,
    WorkflowStep,
    WorkflowStepStatus,
    ContextSource,
    ContextValidationLevel,
    create_context_for_task,
    validate_context_schema,
    TASK_CONTEXT_SCHEMA,
)

__version__ = "1.3.5"
__all__ = [
    # Learning Rooms
    "LearningRoom",
    "LearningRoomManager",
    "RoomStatus",
    "create_learning_room",
    "get_learning_room",
    # Orchestrator
    "CKCOrchestrator",
    "ValidationFlow",
    "TaskPriority",
    # Work-Loop Sequencer (v1.1.0)
    "WorkLoopSequencer",
    "WorkLoopStep",
    "WorkLoop",
    "WorkLoopStepType",
    "WorkLoopStatus",
    # Agents
    "ToolExplorerAgent",
    "CreativeSynthesizerAgent",
    "KnowledgeArchitectAgent",
    "VirtualWorldBuilderAgent",
    "QualityAssuranceAgent",
    # Kommandanter
    "HistorikerKommandant",
    "BibliotekarKommandant",
    # Security
    "InputSanitizer",
    "CorruptionDetector",
    "IntegrityValidator",
    # Dashboard
    "StatusDot",
    "DashboardManager",
    "AcuteNotificationPage",
    # Advanced Protocols
    "DynamicSecurityManager",
    "SecurityLevel",
    "ILCPManager",
    "ILCPMessage",
    "CKCSuperAdminTerminal",
    "HITLApprovalRequest",
    "get_security_manager",
    "get_ilcp_manager",
    "get_terminal",
    # ILCP Validation (v1.1.0)
    "ValidationMode",
    "MessageType",
    "MessagePriority",
    "ILCP_MESSAGE_SCHEMA",
    "ILCP_DATA_REQUEST_SCHEMA",
    "ILCP_DATA_RESPONSE_SCHEMA",
    "ILCP_KNOWLEDGE_SHARE_SCHEMA",
    # Context (v1.1.0)
    "TaskContext",
    "WorkflowStep",
    "WorkflowStepStatus",
    "ContextSource",
    "ContextValidationLevel",
    "create_context_for_task",
    "validate_context_schema",
    "TASK_CONTEXT_SCHEMA",
]
