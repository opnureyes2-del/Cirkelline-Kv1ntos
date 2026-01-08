"""
CKC Integrations Module
=======================

Integration connectors for the CKC ecosystem.

Components:
- CosmicLibraryConnector: Auto-arkivering til Cosmic Library
- CreativeHITL: Human-in-the-Loop for kreative opgaver
- MastermindIntegration: MASTERMIND session integration

Eksempel:
    from cirkelline.ckc.integrations import (
        create_cosmic_connector,
        create_creative_hitl_handler,
        CreativeHITLRequest,
        CreativeHITLType,
    )

    # Setup Cosmic Library connector
    connector = await create_cosmic_connector()

    # Archive creative result
    asset = await connector.archive_creative_result(result, session_id)

    # Setup Creative HITL
    hitl_handler = create_creative_hitl_handler()
    request = await hitl_handler.request_selection(options, context)
"""

__version__ = "1.0.0"
__author__ = "CKC Development Team"

# =============================================================================
# COSMIC LIBRARY INTEGRATION
# =============================================================================

from .cosmic_library import (
    # Enums
    AssetType,
    ArchiveStatus,

    # Data classes
    CreativeAsset,
    ArchiveResult,
    AssetMetadata,
    AssetVersion,

    # Main classes
    CosmicLibraryConnector,
    AssetRegistry,

    # Factory
    create_cosmic_connector,
    get_cosmic_connector,
)

# =============================================================================
# CREATIVE HITL
# =============================================================================

from .hitl_creative import (
    # Enums
    CreativeHITLType,
    CreativeDecision,

    # Data classes
    CreativeOption,
    CreativeHITLRequest,
    CreativeHITLResponse,

    # Main classes
    CreativeHITLHandler,
    CreativeSelectionManager,

    # Factory
    create_creative_hitl_handler,
    get_creative_hitl_handler,
)

# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Version
    "__version__",

    # Cosmic Library
    "AssetType",
    "ArchiveStatus",
    "CreativeAsset",
    "ArchiveResult",
    "AssetMetadata",
    "AssetVersion",
    "CosmicLibraryConnector",
    "AssetRegistry",
    "create_cosmic_connector",
    "get_cosmic_connector",

    # Creative HITL
    "CreativeHITLType",
    "CreativeDecision",
    "CreativeOption",
    "CreativeHITLRequest",
    "CreativeHITLResponse",
    "CreativeHITLHandler",
    "CreativeSelectionManager",
    "create_creative_hitl_handler",
    "get_creative_hitl_handler",
]
