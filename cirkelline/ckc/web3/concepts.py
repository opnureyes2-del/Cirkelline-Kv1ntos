"""
CKC Web3 Concepts
=================

Data models and concepts for Web3 integration.

Defines:
- Blockchain types and standards
- NFT metadata structures
- Ownership and transfer records
- Royalty configurations
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class Blockchain(Enum):
    """Supported blockchains."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    SOLANA = "solana"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"


class NFTStandard(Enum):
    """NFT token standards."""
    ERC721 = "erc721"       # Standard NFT (Ethereum)
    ERC1155 = "erc1155"     # Multi-token (Ethereum)
    METAPLEX = "metaplex"   # Solana NFT standard
    SPL = "spl"             # Solana Program Library


class TokenType(Enum):
    """Types of tokens."""
    SINGLE = "single"           # Unique 1/1 NFT
    EDITION = "edition"         # Limited edition
    OPEN_EDITION = "open"       # Open edition
    COLLECTION = "collection"   # Part of collection


class MintStatus(Enum):
    """Status of minting operation."""
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OwnershipStatus(Enum):
    """Status of NFT ownership."""
    OWNED = "owned"
    TRANSFERRED = "transferred"
    BURNED = "burned"
    DISPUTED = "disputed"


# =============================================================================
# NFT DATA CLASSES
# =============================================================================

@dataclass
class NFTAttribute:
    """An attribute/trait for an NFT."""
    trait_type: str
    value: str
    display_type: Optional[str] = None  # "number", "date", "boost_percentage"
    max_value: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "trait_type": self.trait_type,
            "value": self.value,
        }
        if self.display_type:
            result["display_type"] = self.display_type
        if self.max_value is not None:
            result["max_value"] = self.max_value
        return result


@dataclass
class NFTMetadata:
    """
    NFT Metadata following OpenSea/ERC721 standards.

    Reference: https://docs.opensea.io/docs/metadata-standards
    """
    name: str
    description: str
    image: str  # IPFS URI or URL

    # Optional standard fields
    external_url: Optional[str] = None
    animation_url: Optional[str] = None  # For video/audio NFTs
    background_color: Optional[str] = None  # Hex color without #

    # Attributes
    attributes: List[NFTAttribute] = field(default_factory=list)

    # CKC-specific
    ckc_asset_id: Optional[str] = None
    ckc_session_id: Optional[str] = None
    prompt: Optional[str] = None
    generation_model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "description": self.description,
            "image": self.image,
        }

        if self.external_url:
            result["external_url"] = self.external_url
        if self.animation_url:
            result["animation_url"] = self.animation_url
        if self.background_color:
            result["background_color"] = self.background_color
        if self.attributes:
            result["attributes"] = [a.to_dict() for a in self.attributes]

        # CKC properties
        properties = {}
        if self.ckc_asset_id:
            properties["ckc_asset_id"] = self.ckc_asset_id
        if self.ckc_session_id:
            properties["ckc_session_id"] = self.ckc_session_id
        if self.prompt:
            properties["generation_prompt"] = self.prompt
        if self.generation_model:
            properties["generation_model"] = self.generation_model

        if properties:
            result["properties"] = properties

        return result


@dataclass
class RoyaltyConfig:
    """Royalty configuration for NFT."""
    creator_royalty_percent: float = 5.0      # 0-10%
    platform_royalty_percent: float = 2.5     # Platform fee
    split_recipients: Dict[str, float] = field(default_factory=dict)  # address -> percentage

    def validate(self) -> bool:
        """Validate royalty configuration."""
        if self.creator_royalty_percent < 0 or self.creator_royalty_percent > 10:
            return False
        if self.platform_royalty_percent < 0 or self.platform_royalty_percent > 5:
            return False

        # Check split totals
        if self.split_recipients:
            total = sum(self.split_recipients.values())
            if abs(total - 100.0) > 0.01:  # Allow small floating point error
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "creator_royalty_percent": self.creator_royalty_percent,
            "platform_royalty_percent": self.platform_royalty_percent,
            "split_recipients": self.split_recipients,
        }


@dataclass
class NFTMintRequest:
    """Request to mint an NFT."""
    # Asset reference
    asset_id: str

    # Blockchain config
    blockchain: str = "polygon"  # Default to Polygon for lower fees
    collection_id: Optional[str] = None

    # Metadata
    name: str = ""
    description: str = ""
    attributes: List[NFTAttribute] = field(default_factory=list)

    # Token config
    token_type: TokenType = TokenType.SINGLE
    edition_size: int = 1  # For editions
    reserve_price: Optional[float] = None

    # Royalties
    royalty_config: Optional[RoyaltyConfig] = None

    # Pricing
    initial_price: Optional[float] = None
    currency: str = "MATIC"  # Native currency

    # Files
    image_uri: str = ""       # IPFS URI
    animation_uri: str = ""   # For animated NFTs

    # Creator info
    creator_address: str = ""
    creator_id: str = ""

    # Request tracking
    request_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "blockchain": self.blockchain,
            "collection_id": self.collection_id,
            "name": self.name,
            "description": self.description,
            "attributes": [a.to_dict() for a in self.attributes],
            "token_type": self.token_type.value,
            "edition_size": self.edition_size,
            "reserve_price": self.reserve_price,
            "royalty_config": self.royalty_config.to_dict() if self.royalty_config else None,
            "initial_price": self.initial_price,
            "currency": self.currency,
            "image_uri": self.image_uri,
            "animation_uri": self.animation_uri,
            "creator_address": self.creator_address,
            "creator_id": self.creator_id,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class NFTMintResult:
    """Result of NFT minting operation."""
    success: bool
    status: MintStatus = MintStatus.PENDING

    # Token info
    token_id: Optional[str] = None
    contract_address: Optional[str] = None
    transaction_hash: Optional[str] = None

    # Metadata
    metadata_uri: Optional[str] = None  # IPFS URI

    # Blockchain info
    blockchain: str = ""
    block_number: Optional[int] = None
    gas_used: Optional[int] = None

    # Cost
    mint_cost_crypto: float = 0.0
    mint_cost_usd: float = 0.0

    # Error
    error: Optional[str] = None

    # Timestamps
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status.value,
            "token_id": self.token_id,
            "contract_address": self.contract_address,
            "transaction_hash": self.transaction_hash,
            "metadata_uri": self.metadata_uri,
            "blockchain": self.blockchain,
            "block_number": self.block_number,
            "gas_used": self.gas_used,
            "mint_cost_crypto": self.mint_cost_crypto,
            "mint_cost_usd": self.mint_cost_usd,
            "error": self.error,
            "requested_at": self.requested_at.isoformat(),
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
        }


# =============================================================================
# OWNERSHIP DATA CLASSES
# =============================================================================

@dataclass
class TransferRecord:
    """Record of NFT transfer."""
    transfer_id: str
    token_id: str
    from_address: str
    to_address: str
    transaction_hash: str
    block_number: int
    transfer_type: str = "sale"  # sale, gift, auction
    price_crypto: float = 0.0
    price_usd: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "token_id": self.token_id,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "transaction_hash": self.transaction_hash,
            "block_number": self.block_number,
            "transfer_type": self.transfer_type,
            "price_crypto": self.price_crypto,
            "price_usd": self.price_usd,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class OwnershipInfo:
    """Current ownership information for an NFT."""
    token_id: str
    contract_address: str
    blockchain: str
    current_owner: str
    status: OwnershipStatus = OwnershipStatus.OWNED

    # History
    total_transfers: int = 0
    transfer_history: List[TransferRecord] = field(default_factory=list)

    # Verification
    verified: bool = False
    verified_at: Optional[datetime] = None

    # Timestamps
    minted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_transfer_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "contract_address": self.contract_address,
            "blockchain": self.blockchain,
            "current_owner": self.current_owner,
            "status": self.status.value,
            "total_transfers": self.total_transfers,
            "verified": self.verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "minted_at": self.minted_at.isoformat(),
            "last_transfer_at": self.last_transfer_at.isoformat() if self.last_transfer_at else None,
        }


@dataclass
class RoyaltyPayment:
    """Record of a royalty payment."""
    payment_id: str
    token_id: str
    sale_transaction_hash: str
    sale_price_crypto: float
    sale_price_usd: float

    # Royalty amounts
    royalty_amount_crypto: float
    royalty_amount_usd: float
    royalty_percent: float

    # Recipient
    recipient_address: str
    recipient_type: str = "creator"  # creator, platform, collaborator

    # Status
    paid: bool = False
    payment_transaction_hash: Optional[str] = None

    # Timestamps
    sale_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payment_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "token_id": self.token_id,
            "sale_transaction_hash": self.sale_transaction_hash,
            "sale_price_crypto": self.sale_price_crypto,
            "sale_price_usd": self.sale_price_usd,
            "royalty_amount_crypto": self.royalty_amount_crypto,
            "royalty_amount_usd": self.royalty_amount_usd,
            "royalty_percent": self.royalty_percent,
            "recipient_address": self.recipient_address,
            "recipient_type": self.recipient_type,
            "paid": self.paid,
            "payment_transaction_hash": self.payment_transaction_hash,
            "sale_timestamp": self.sale_timestamp.isoformat(),
            "payment_timestamp": self.payment_timestamp.isoformat() if self.payment_timestamp else None,
        }


logger.info("CKC Web3 concepts module loaded")
