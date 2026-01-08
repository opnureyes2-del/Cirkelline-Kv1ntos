"""
CKC Kommandant Module
=====================

Kommandant-agenter til orkestrering af opgaver i lærerum.

Den centrale Kommandant koordinerer:
    - Opgavemodtagelse og analyse
    - Delegering til specialister
    - Overvågning af opgaveudførelse
    - Læring fra erfaringer
    - Audit trails

Usage:
    from cirkelline.ckc.kommandant import (
        create_kommandant,
        get_kommandant,
        list_kommandanter,
        Kommandant,
        KommandantStatus,
    )

    # Create a new Kommandant
    kommandant = await create_kommandant(
        room_id=1,
        name="Analyse Kommandant",
        description="Kommandant til dokumentanalyse"
    )

    # Execute a task
    result = await kommandant.receive_task(
        task_id="task_001",
        context_id="ctx_001",
        prompt="Analysér dette dokument"
    )
    await kommandant.execute_task("task_001")
"""

from .core import (
    # Main class
    Kommandant,
    # Enums
    KommandantStatus,
    TaskPriority,
    DelegationStrategy,
    TaskOutcome,
    # Data classes
    TaskAnalysis,
    DelegationRecord,
    Experience,
    AuditEntry,
    # Factory functions
    create_kommandant,
    get_kommandant,
    list_kommandanter,
    # Mappings
    CAPABILITY_TO_SPECIALIST,
    SPECIALIST_CAPABILITIES,
)

from .delegation import (
    # Classes
    SpecialistSelector,
    TaskPlanner,
    DelegationEngine,
    # Enums
    SpecialistAvailability,
    ExecutionMode,
    # Data classes
    SpecialistInfo,
    TaskPlan,
    DelegationResult,
    # Factory functions
    get_specialist_selector,
    get_task_planner,
    get_delegation_engine,
)

from .mvp_room import (
    # MVP Room functions
    create_mvp_room,
    get_mvp_room,
    get_mvp_kommandant,
    get_document_specialist,
    test_mvp_workflow,
    run_simple_journey,
    # Classes
    DocumentSpecialist,
    JourneyCommand,
    JourneyStep,
)

__all__ = [
    # Main class
    "Kommandant",
    # Core Enums
    "KommandantStatus",
    "TaskPriority",
    "DelegationStrategy",
    "TaskOutcome",
    # Core Data classes
    "TaskAnalysis",
    "DelegationRecord",
    "Experience",
    "AuditEntry",
    # Factory functions
    "create_kommandant",
    "get_kommandant",
    "list_kommandanter",
    # Mappings
    "CAPABILITY_TO_SPECIALIST",
    "SPECIALIST_CAPABILITIES",
    # Delegation classes
    "SpecialistSelector",
    "TaskPlanner",
    "DelegationEngine",
    # Delegation enums
    "SpecialistAvailability",
    "ExecutionMode",
    # Delegation data classes
    "SpecialistInfo",
    "TaskPlan",
    "DelegationResult",
    # Delegation factory functions
    "get_specialist_selector",
    "get_task_planner",
    "get_delegation_engine",
    # MVP Room functions
    "create_mvp_room",
    "get_mvp_room",
    "get_mvp_kommandant",
    "get_document_specialist",
    "test_mvp_workflow",
    "run_simple_journey",
    # MVP Classes
    "DocumentSpecialist",
    "JourneyCommand",
    "JourneyStep",
]
