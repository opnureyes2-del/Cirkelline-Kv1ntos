"""
CKC Web3 Module
===============

Web3 and blockchain integration concepts for CKC.

Provides conceptual models and stub implementations for:
- NFT minting and management
- Blockchain integration
- Royalty tracking
- Ownership verification

NOTE: This is a conceptual implementation providing the data models
and interfaces. Actual blockchain integration requires additional
configuration and API keys.

Eksempel:
    from cirkelline.ckc.web3 import (
        NFTMintRequest,
        NFTMintResult,
        create_nft_service,
        RoyaltyTracker,
    )

    # Create NFT mint request
    request = NFTMintRequest(
        asset_id="asset_123",
        blockchain="polygon",
        name="My Creative Work",
        description="A beautiful AI-generated artwork",
    )

    # Mint (stub)
    service = await create_nft_service()
    result = await service.mint_nft(request)
"""

__version__ = "1.0.0"
__author__ = "CKC Development Team"

# =============================================================================
# CONCEPTS
# =============================================================================

from .concepts import (
    # Enums
    Blockchain,
    NFTStandard,
    TokenType,
    MintStatus,
    OwnershipStatus,

    # Data classes
    NFTAttribute,
    NFTMetadata,
    NFTMintRequest,
    NFTMintResult,
    OwnershipInfo,
    TransferRecord,
    RoyaltyConfig,
    RoyaltyPayment,
)

# =============================================================================
# NFT SERVICE
# =============================================================================

from .nft_stubs import (
    # Main classes
    NFTService,
    BlockchainIntegration,
    EthereumIntegration,
    PolygonIntegration,
    SolanaIntegration,

    # Factory
    create_nft_service,
    get_nft_service,
)

# =============================================================================
# ROYALTY TRACKING
# =============================================================================

from .royalty_tracking import (
    # Data classes
    RoyaltyReport,
    RoyaltyPeriod,
    CreatorEarnings,

    # Main classes
    RoyaltyTracker,
    EarningsCalculator,

    # Factory
    create_royalty_tracker,
    get_royalty_tracker,
)

# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Version
    "__version__",

    # Concepts - Enums
    "Blockchain",
    "NFTStandard",
    "TokenType",
    "MintStatus",
    "OwnershipStatus",

    # Concepts - Data classes
    "NFTAttribute",
    "NFTMetadata",
    "NFTMintRequest",
    "NFTMintResult",
    "OwnershipInfo",
    "TransferRecord",
    "RoyaltyConfig",
    "RoyaltyPayment",

    # NFT Service
    "NFTService",
    "BlockchainIntegration",
    "EthereumIntegration",
    "PolygonIntegration",
    "SolanaIntegration",
    "create_nft_service",
    "get_nft_service",

    # Royalty Tracking
    "RoyaltyReport",
    "RoyaltyPeriod",
    "CreatorEarnings",
    "RoyaltyTracker",
    "EarningsCalculator",
    "create_royalty_tracker",
    "get_royalty_tracker",
]
