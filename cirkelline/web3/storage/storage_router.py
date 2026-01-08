"""
Storage Router
==============
Intelligent routing for decentralized storage.

Responsibilities:
- Route data to optimal storage provider
- Manage redundancy across providers
- Handle failover and caching
- Cost optimization
"""

import logging
import hashlib
import secrets
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from cirkelline.web3.storage.ipfs_adapter import (
    IPFSAdapter,
    IPFSFile,
    get_ipfs_adapter,
)
from cirkelline.web3.storage.arweave_adapter import (
    ArweaveAdapter,
    ArweaveTransaction,
    get_arweave_adapter,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class StorageProvider(Enum):
    """Available storage providers."""
    IPFS = "ipfs"
    ARWEAVE = "arweave"
    FILECOIN = "filecoin"  # Future
    STORJ = "storj"        # Future
    SIA = "sia"            # Future


class StoragePolicy(Enum):
    """Storage policy types."""
    TEMPORARY = "temporary"     # IPFS only, no pinning
    PERSISTENT = "persistent"   # IPFS with pinning
    PERMANENT = "permanent"     # Arweave
    REDUNDANT = "redundant"     # Both IPFS and Arweave
    COST_OPTIMIZED = "cost_optimized"
    SPEED_OPTIMIZED = "speed_optimized"


class ContentCategory(Enum):
    """Content categorization for routing."""
    SMALL_FILE = "small_file"       # < 1KB
    MEDIUM_FILE = "medium_file"     # 1KB - 1MB
    LARGE_FILE = "large_file"       # 1MB - 100MB
    HUGE_FILE = "huge_file"         # > 100MB
    METADATA = "metadata"
    NFT_ASSET = "nft_asset"
    CONTRACT_DATA = "contract_data"
    USER_DATA = "user_data"
    ARCHIVE = "archive"


class ReplicationStatus(Enum):
    """Replication status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class StorageResult:
    """Result of a storage operation."""
    content_id: str  # Unified content identifier
    provider: StorageProvider
    reference: str   # Provider-specific reference (CID or TX ID)
    size: int
    content_type: str
    policy: StoragePolicy
    gateway_url: str = ""
    replication: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_id": self.content_id,
            "provider": self.provider.value,
            "reference": self.reference,
            "size": self.size,
            "content_type": self.content_type,
            "policy": self.policy.value,
            "gateway_url": self.gateway_url,
            "replication": self.replication,
        }


@dataclass
class ReplicationPlan:
    """Plan for content replication."""
    content_id: str
    source_provider: StorageProvider
    target_providers: List[StorageProvider]
    status: ReplicationStatus = ReplicationStatus.PENDING
    progress: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_id": self.content_id,
            "source": self.source_provider.value,
            "targets": [p.value for p in self.target_providers],
            "status": self.status.value,
            "progress": self.progress,
        }


@dataclass
class StorageCostEstimate:
    """Cost estimate for storage operation."""
    provider: StorageProvider
    storage_cost: float
    retrieval_cost: float
    total_cost: float
    currency: str = "USD"
    duration: str = "permanent"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider.value,
            "storage_cost": round(self.storage_cost, 6),
            "retrieval_cost": round(self.retrieval_cost, 6),
            "total_cost": round(self.total_cost, 6),
            "currency": self.currency,
            "duration": self.duration,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PROVIDER CHARACTERISTICS
# ═══════════════════════════════════════════════════════════════════════════════

PROVIDER_INFO = {
    StorageProvider.IPFS: {
        "name": "IPFS",
        "permanence": "content-addressed, not permanent without pinning",
        "speed": "fast",
        "cost_model": "pinning service fees",
        "max_file_size": None,  # No limit
        "best_for": ["real-time access", "mutable content", "large files"],
        "considerations": ["requires pinning", "garbage collected"],
    },
    StorageProvider.ARWEAVE: {
        "name": "Arweave",
        "permanence": "permanent (200+ years)",
        "speed": "medium",
        "cost_model": "one-time payment",
        "max_file_size": None,
        "best_for": ["permanent storage", "immutable records", "NFT metadata"],
        "considerations": ["higher upfront cost", "permanent = no deletion"],
    },
    StorageProvider.FILECOIN: {
        "name": "Filecoin",
        "permanence": "contract-based duration",
        "speed": "slow",
        "cost_model": "storage deals",
        "max_file_size": None,
        "best_for": ["large archives", "cold storage", "backup"],
        "considerations": ["deal duration", "retrieval complexity"],
    },
}

# Policy to provider mapping
POLICY_PROVIDERS = {
    StoragePolicy.TEMPORARY: [StorageProvider.IPFS],
    StoragePolicy.PERSISTENT: [StorageProvider.IPFS],
    StoragePolicy.PERMANENT: [StorageProvider.ARWEAVE],
    StoragePolicy.REDUNDANT: [StorageProvider.IPFS, StorageProvider.ARWEAVE],
    StoragePolicy.COST_OPTIMIZED: [StorageProvider.IPFS],
    StoragePolicy.SPEED_OPTIMIZED: [StorageProvider.IPFS],
}


# ═══════════════════════════════════════════════════════════════════════════════
# STORAGE ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

class StorageRouter:
    """
    Intelligent storage router.

    Routes content to optimal storage providers based on
    content characteristics, policies, and cost considerations.
    """

    def __init__(
        self,
        ipfs_adapter: Optional[IPFSAdapter] = None,
        arweave_adapter: Optional[ArweaveAdapter] = None,
    ):
        self._ipfs = ipfs_adapter or get_ipfs_adapter()
        self._arweave = arweave_adapter or get_arweave_adapter()

        # Content registry
        self._content_registry: Dict[str, StorageResult] = {}
        self._replication_plans: Dict[str, ReplicationPlan] = {}

        # Statistics
        self._stats = {
            "total_stored": 0,
            "total_retrieved": 0,
            "bytes_to_ipfs": 0,
            "bytes_to_arweave": 0,
            "replication_count": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # STORAGE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def store(
        self,
        content: bytes,
        content_type: str = "application/octet-stream",
        policy: StoragePolicy = StoragePolicy.PERSISTENT,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageResult:
        """
        Store content with specified policy.

        Args:
            content: Content bytes
            content_type: MIME type
            policy: Storage policy
            metadata: Optional metadata
        """
        self._stats["total_stored"] += 1

        # Generate content ID
        content_hash = hashlib.sha256(content).hexdigest()
        content_id = f"cid-{content_hash[:32]}"

        # Categorize content
        category = self._categorize_content(len(content), content_type)

        # Select provider(s) based on policy
        providers = self._select_providers(policy, category, len(content))
        primary_provider = providers[0]

        # Store to primary provider
        result = await self._store_to_provider(
            content, content_type, primary_provider, metadata
        )

        # Create storage result
        storage_result = StorageResult(
            content_id=content_id,
            provider=primary_provider,
            reference=result["reference"],
            size=len(content),
            content_type=content_type,
            policy=policy,
            gateway_url=result.get("gateway_url", ""),
            created_at=datetime.utcnow().isoformat() + "Z",
            metadata=metadata or {},
        )

        # Handle replication for redundant policy
        if len(providers) > 1:
            replication = {}
            for provider in providers[1:]:
                rep_result = await self._store_to_provider(
                    content, content_type, provider, metadata
                )
                replication[provider.value] = rep_result["reference"]
                self._stats["replication_count"] += 1

            storage_result.replication = replication

        # Register content
        self._content_registry[content_id] = storage_result

        return storage_result

    async def store_json(
        self,
        data: Dict[str, Any],
        policy: StoragePolicy = StoragePolicy.PERSISTENT,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageResult:
        """Store JSON data."""
        import json
        content = json.dumps(data, sort_keys=True).encode()
        return await self.store(
            content=content,
            content_type="application/json",
            policy=policy,
            metadata=metadata,
        )

    async def _store_to_provider(
        self,
        content: bytes,
        content_type: str,
        provider: StorageProvider,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, str]:
        """Store to specific provider."""
        if provider == StorageProvider.IPFS:
            self._stats["bytes_to_ipfs"] += len(content)
            ipfs_file = await self._ipfs.add(
                content=content,
                content_type=content_type,
                pin=True,
            )
            return {
                "reference": ipfs_file.cid,
                "gateway_url": ipfs_file.gateway_url,
            }

        elif provider == StorageProvider.ARWEAVE:
            self._stats["bytes_to_arweave"] += len(content)
            tags = []
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, str):
                        tags.append({"name": key, "value": value})

            tx = await self._arweave.upload(
                data=content,
                content_type=content_type,
                tags=tags,
            )
            return {
                "reference": tx.tx_id,
                "gateway_url": self._arweave.get_data_url(tx.tx_id),
            }

        return {"reference": "", "gateway_url": ""}

    async def retrieve(
        self,
        content_id: str,
        provider: Optional[StorageProvider] = None,
    ) -> Optional[bytes]:
        """
        Retrieve content by ID.

        Args:
            content_id: Content identifier
            provider: Optional preferred provider
        """
        self._stats["total_retrieved"] += 1

        # Check registry
        if content_id not in self._content_registry:
            return None

        result = self._content_registry[content_id]
        target_provider = provider or result.provider

        # Retrieve from provider
        if target_provider == StorageProvider.IPFS:
            return await self._ipfs.get(result.reference)
        elif target_provider == StorageProvider.ARWEAVE:
            return await self._arweave.get(result.reference)

        return None

    async def retrieve_json(
        self,
        content_id: str,
        provider: Optional[StorageProvider] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve JSON content."""
        import json
        content = await self.retrieve(content_id, provider)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # ROUTING LOGIC
    # ═══════════════════════════════════════════════════════════════════════════

    def _categorize_content(
        self,
        size: int,
        content_type: str,
    ) -> ContentCategory:
        """Categorize content for routing decisions."""
        # Size-based categorization
        if size < 1024:
            return ContentCategory.SMALL_FILE
        elif size < 1024 * 1024:
            return ContentCategory.MEDIUM_FILE
        elif size < 100 * 1024 * 1024:
            return ContentCategory.LARGE_FILE
        else:
            return ContentCategory.HUGE_FILE

    def _select_providers(
        self,
        policy: StoragePolicy,
        category: ContentCategory,
        size: int,
    ) -> List[StorageProvider]:
        """Select providers based on policy and content."""
        # Get policy-recommended providers
        providers = POLICY_PROVIDERS.get(policy, [StorageProvider.IPFS])

        # Adjust for content characteristics
        if category == ContentCategory.HUGE_FILE:
            # Prefer IPFS for huge files due to Arweave costs
            if StorageProvider.ARWEAVE in providers and policy != StoragePolicy.PERMANENT:
                providers = [StorageProvider.IPFS]

        return providers

    def recommend_policy(
        self,
        content_type: str,
        size: int,
        permanence_required: bool = False,
        budget_constrained: bool = False,
    ) -> StoragePolicy:
        """
        Recommend storage policy based on requirements.

        Args:
            content_type: MIME type of content
            size: Content size in bytes
            permanence_required: Whether content must be permanent
            budget_constrained: Whether to optimize for cost
        """
        # Permanence overrides other considerations
        if permanence_required:
            if size > 10 * 1024 * 1024:  # > 10MB
                # Large permanent files use redundant for failover
                return StoragePolicy.REDUNDANT
            return StoragePolicy.PERMANENT

        # Budget optimization
        if budget_constrained:
            return StoragePolicy.COST_OPTIMIZED

        # NFT and contract data should be permanent
        if "nft" in content_type.lower() or content_type == "application/json":
            return StoragePolicy.PERMANENT

        # Default to persistent (IPFS with pinning)
        return StoragePolicy.PERSISTENT

    # ═══════════════════════════════════════════════════════════════════════════
    # REPLICATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def replicate(
        self,
        content_id: str,
        target_providers: List[StorageProvider],
    ) -> ReplicationPlan:
        """
        Replicate content to additional providers.

        Args:
            content_id: Content to replicate
            target_providers: Target providers
        """
        if content_id not in self._content_registry:
            raise ValueError(f"Content {content_id} not found")

        result = self._content_registry[content_id]

        plan = ReplicationPlan(
            content_id=content_id,
            source_provider=result.provider,
            target_providers=target_providers,
            status=ReplicationStatus.IN_PROGRESS,
        )

        # Get content from source
        content = await self.retrieve(content_id)
        if not content:
            plan.status = ReplicationStatus.FAILED
            return plan

        # Replicate to each target
        for provider in target_providers:
            if provider == result.provider:
                continue

            try:
                rep_result = await self._store_to_provider(
                    content=content,
                    content_type=result.content_type,
                    provider=provider,
                    metadata=result.metadata,
                )
                plan.progress[provider.value] = rep_result["reference"]
                result.replication[provider.value] = rep_result["reference"]
                self._stats["replication_count"] += 1

            except Exception as e:
                plan.progress[provider.value] = f"failed: {str(e)}"

        # Update status
        if all(v and not v.startswith("failed") for v in plan.progress.values()):
            plan.status = ReplicationStatus.COMPLETE
        elif any(v and not v.startswith("failed") for v in plan.progress.values()):
            plan.status = ReplicationStatus.PARTIAL
        else:
            plan.status = ReplicationStatus.FAILED

        self._replication_plans[content_id] = plan
        return plan

    # ═══════════════════════════════════════════════════════════════════════════
    # COST ESTIMATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def estimate_cost(
        self,
        size: int,
        policy: StoragePolicy,
    ) -> List[StorageCostEstimate]:
        """
        Estimate storage costs for given size and policy.

        Args:
            size: Content size in bytes
            policy: Storage policy
        """
        estimates = []
        providers = POLICY_PROVIDERS.get(policy, [StorageProvider.IPFS])

        for provider in providers:
            if provider == StorageProvider.IPFS:
                # IPFS pinning costs (typical: $0.15/GB/month)
                gb = size / (1024 * 1024 * 1024)
                monthly_cost = gb * 0.15
                estimates.append(StorageCostEstimate(
                    provider=provider,
                    storage_cost=monthly_cost,
                    retrieval_cost=0,
                    total_cost=monthly_cost,
                    duration="per month",
                ))

            elif provider == StorageProvider.ARWEAVE:
                # Arweave one-time cost
                cost = await self._arweave.get_price(size)
                estimates.append(StorageCostEstimate(
                    provider=provider,
                    storage_cost=cost.usd_estimate,
                    retrieval_cost=0,
                    total_cost=cost.usd_estimate,
                    duration="permanent",
                ))

        return estimates

    def compare_providers(
        self,
        requirements: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Compare providers based on requirements.

        Args:
            requirements: Dictionary with requirements like:
                - permanence: bool
                - speed: "fast" | "medium" | "slow"
                - max_cost: float (USD)
        """
        comparisons = []

        for provider, info in PROVIDER_INFO.items():
            score = 0
            notes = []

            # Permanence
            if requirements.get("permanence"):
                if "permanent" in info["permanence"]:
                    score += 30
                    notes.append("Meets permanence requirement")
                else:
                    notes.append("Does not guarantee permanence")

            # Speed
            req_speed = requirements.get("speed", "medium")
            if info["speed"] == req_speed:
                score += 20
            elif info["speed"] == "fast":
                score += 15

            # Best use cases
            for use_case in requirements.get("use_cases", []):
                if use_case in info["best_for"]:
                    score += 10
                    notes.append(f"Good for {use_case}")

            comparisons.append({
                "provider": provider.value,
                "name": info["name"],
                "score": score,
                "permanence": info["permanence"],
                "speed": info["speed"],
                "best_for": info["best_for"],
                "considerations": info["considerations"],
                "notes": notes,
            })

        # Sort by score
        comparisons.sort(key=lambda x: x["score"], reverse=True)
        return comparisons

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_content(self, content_id: str) -> Optional[StorageResult]:
        """Get content info by ID."""
        return self._content_registry.get(content_id)

    def list_content(
        self,
        provider: Optional[StorageProvider] = None,
        policy: Optional[StoragePolicy] = None,
    ) -> List[StorageResult]:
        """List stored content with optional filters."""
        results = list(self._content_registry.values())

        if provider:
            results = [r for r in results if r.provider == provider]

        if policy:
            results = [r for r in results if r.policy == policy]

        return results

    def get_replication_status(
        self,
        content_id: str,
    ) -> Optional[ReplicationPlan]:
        """Get replication status for content."""
        return self._replication_plans.get(content_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        provider_counts = {}
        policy_counts = {}

        for result in self._content_registry.values():
            provider = result.provider.value
            policy = result.policy.value

            provider_counts[provider] = provider_counts.get(provider, 0) + 1
            policy_counts[policy] = policy_counts.get(policy, 0) + 1

        return {
            **self._stats,
            "content_count": len(self._content_registry),
            "by_provider": provider_counts,
            "by_policy": policy_counts,
            "replication_plans": len(self._replication_plans),
            "ipfs_stats": self._ipfs.get_stats(),
            "arweave_stats": self._arweave.get_stats(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_router_instance: Optional[StorageRouter] = None


def get_storage_router() -> StorageRouter:
    """Get singleton StorageRouter instance."""
    global _router_instance

    if _router_instance is None:
        _router_instance = StorageRouter()

    return _router_instance
