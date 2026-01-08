"""
Arweave Adapter
===============
Arweave permanent storage integration.

Responsibilities:
- Store data permanently on Arweave
- Manage transactions and bundling
- Handle AR token economics
- Support SmartWeave contracts
"""

import logging
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class TransactionStatus(Enum):
    """Arweave transaction status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    DROPPED = "dropped"


class BundleStatus(Enum):
    """Bundle upload status."""
    BUNDLING = "bundling"
    UPLOADING = "uploading"
    POSTED = "posted"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class ContentTag(Enum):
    """Standard Arweave tags."""
    CONTENT_TYPE = "Content-Type"
    APP_NAME = "App-Name"
    APP_VERSION = "App-Version"
    UNIX_TIME = "Unix-Time"
    TYPE = "Type"
    TITLE = "Title"


@dataclass
class ArweaveTag:
    """An Arweave transaction tag."""
    name: str
    value: str

    def to_dict(self) -> Dict[str, str]:
        return {"name": self.name, "value": self.value}


@dataclass
class ArweaveTransaction:
    """An Arweave transaction."""
    tx_id: str
    owner: str = ""
    data_size: int = 0
    data_root: str = ""
    reward: str = "0"  # Winston (AR smallest unit)
    tags: List[ArweaveTag] = field(default_factory=list)
    status: TransactionStatus = TransactionStatus.PENDING
    block_height: Optional[int] = None
    block_timestamp: Optional[int] = None
    confirmations: int = 0
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.tx_id,
            "owner": self.owner[:20] + "..." if self.owner else "",
            "data_size": self.data_size,
            "reward": self.reward,
            "status": self.status.value,
            "confirmations": self.confirmations,
            "tags": [t.to_dict() for t in self.tags],
        }

    def get_tag(self, name: str) -> Optional[str]:
        """Get tag value by name."""
        for tag in self.tags:
            if tag.name == name:
                return tag.value
        return None


@dataclass
class BundleItem:
    """An item in an ANS-104 bundle."""
    item_id: str
    data: bytes = field(default_factory=bytes)
    tags: List[ArweaveTag] = field(default_factory=list)
    target: str = ""
    anchor: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.item_id,
            "size": len(self.data),
            "tags": [t.to_dict() for t in self.tags],
        }


@dataclass
class Bundle:
    """An ANS-104 bundle for batched uploads."""
    bundle_id: str
    items: List[BundleItem] = field(default_factory=list)
    status: BundleStatus = BundleStatus.BUNDLING
    tx_id: Optional[str] = None
    total_size: int = 0
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.bundle_id,
            "items_count": len(self.items),
            "total_size": self.total_size,
            "status": self.status.value,
            "tx_id": self.tx_id,
        }


@dataclass
class StorageCost:
    """Cost estimate for storage."""
    bytes_size: int
    winston: int  # Cost in Winston
    ar: float  # Cost in AR
    usd_estimate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bytes": self.bytes_size,
            "winston": self.winston,
            "ar": round(self.ar, 12),
            "usd_estimate": round(self.usd_estimate, 4),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

WINSTON_PER_AR = 10**12
DEFAULT_GATEWAY = "https://arweave.net"
BUNDLR_NODES = [
    "https://node1.bundlr.network",
    "https://node2.bundlr.network",
]

# Current network parameters (simplified)
NETWORK_INFO = {
    "network": "arweave.N.1",
    "version": 5,
    "height": 1300000,
    "current": "block_hash_placeholder",
    "blocks": 1300000,
    "peers": 150,
}


# ═══════════════════════════════════════════════════════════════════════════════
# ARWEAVE ADAPTER
# ═══════════════════════════════════════════════════════════════════════════════

class ArweaveAdapter:
    """
    Arweave permanent storage adapter.

    Provides interface for storing data permanently
    on the Arweave permaweb.
    """

    def __init__(
        self,
        gateway_url: str = DEFAULT_GATEWAY,
        bundlr_node: Optional[str] = None,
        wallet_path: Optional[str] = None,
    ):
        self._gateway_url = gateway_url.rstrip("/")
        self._bundlr_node = bundlr_node or BUNDLR_NODES[0]
        self._wallet_path = wallet_path

        # Caches
        self._tx_cache: Dict[str, ArweaveTransaction] = {}
        self._bundle_cache: Dict[str, Bundle] = {}

        # Current bundle for batching
        self._current_bundle: Optional[Bundle] = None

        # Statistics
        self._stats = {
            "transactions_created": 0,
            "transactions_confirmed": 0,
            "bundles_created": 0,
            "total_bytes_stored": 0,
            "total_winston_spent": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # STORAGE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def upload(
        self,
        data: bytes,
        content_type: str = "application/octet-stream",
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> ArweaveTransaction:
        """
        Upload data to Arweave.

        Args:
            data: Data to upload
            content_type: MIME type
            tags: Additional tags
        """
        self._stats["transactions_created"] += 1
        self._stats["total_bytes_stored"] += len(data)

        # Generate transaction ID
        data_hash = hashlib.sha256(data).hexdigest()
        tx_id = data_hash[:43]  # Arweave TX IDs are 43 chars base64url

        # Calculate cost
        cost = await self.get_price(len(data))
        self._stats["total_winston_spent"] += cost.winston

        # Build tags
        tx_tags = [
            ArweaveTag(ContentTag.CONTENT_TYPE.value, content_type),
            ArweaveTag(ContentTag.APP_NAME.value, "Cirkelline"),
            ArweaveTag(ContentTag.APP_VERSION.value, "1.0.0"),
            ArweaveTag(ContentTag.UNIX_TIME.value, str(int(datetime.utcnow().timestamp()))),
        ]

        if tags:
            for tag in tags:
                tx_tags.append(ArweaveTag(tag["name"], tag["value"]))

        # Create transaction
        tx = ArweaveTransaction(
            tx_id=tx_id,
            owner="owner_address_placeholder",
            data_size=len(data),
            data_root=hashlib.sha256(data).hexdigest()[:43],
            reward=str(cost.winston),
            tags=tx_tags,
            status=TransactionStatus.PENDING,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        self._tx_cache[tx_id] = tx
        return tx

    async def upload_json(
        self,
        data: Dict[str, Any],
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> ArweaveTransaction:
        """Upload JSON data to Arweave."""
        import json
        content = json.dumps(data, sort_keys=True).encode()
        return await self.upload(
            data=content,
            content_type="application/json",
            tags=tags,
        )

    async def get(self, tx_id: str) -> Optional[bytes]:
        """
        Retrieve data from Arweave.

        Args:
            tx_id: Transaction ID
        """
        # Check cache
        if tx_id in self._tx_cache:
            # In production, fetch from gateway
            return b"[arweave data placeholder]"

        # In production, use aiohttp to fetch from gateway
        return None

    async def get_json(self, tx_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON from Arweave."""
        import json
        data = await self.get(tx_id)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # BUNDLING (ANS-104)
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_bundle(self) -> Bundle:
        """Create a new bundle for batched uploads."""
        self._stats["bundles_created"] += 1

        bundle = Bundle(
            bundle_id=f"bundle-{secrets.token_hex(16)}",
            status=BundleStatus.BUNDLING,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        self._current_bundle = bundle
        self._bundle_cache[bundle.bundle_id] = bundle

        return bundle

    async def add_to_bundle(
        self,
        data: bytes,
        content_type: str = "application/octet-stream",
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> BundleItem:
        """
        Add item to current bundle.

        Args:
            data: Data to add
            content_type: MIME type
            tags: Additional tags
        """
        if not self._current_bundle:
            await self.create_bundle()

        # Generate item ID
        item_id = hashlib.sha256(data).hexdigest()[:43]

        # Build tags
        item_tags = [
            ArweaveTag(ContentTag.CONTENT_TYPE.value, content_type),
        ]
        if tags:
            for tag in tags:
                item_tags.append(ArweaveTag(tag["name"], tag["value"]))

        item = BundleItem(
            item_id=item_id,
            data=data,
            tags=item_tags,
        )

        self._current_bundle.items.append(item)
        self._current_bundle.total_size += len(data)

        return item

    async def post_bundle(self) -> Optional[ArweaveTransaction]:
        """Post the current bundle to Arweave."""
        if not self._current_bundle or not self._current_bundle.items:
            return None

        bundle = self._current_bundle
        bundle.status = BundleStatus.UPLOADING

        # In production, serialize bundle and upload to Bundlr
        self._stats["total_bytes_stored"] += bundle.total_size

        # Create transaction for bundle
        bundle_data = b"[bundle data]"  # Simplified
        tx = await self.upload(
            data=bundle_data,
            content_type="application/x-ans104-bundle",
            tags=[{"name": "Bundle-Format", "value": "binary"}],
        )

        bundle.tx_id = tx.tx_id
        bundle.status = BundleStatus.POSTED

        # Reset current bundle
        self._current_bundle = None

        return tx

    # ═══════════════════════════════════════════════════════════════════════════
    # TRANSACTION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_transaction(self, tx_id: str) -> Optional[ArweaveTransaction]:
        """Get transaction details."""
        return self._tx_cache.get(tx_id)

    async def get_status(self, tx_id: str) -> Optional[TransactionStatus]:
        """Get transaction status."""
        tx = self._tx_cache.get(tx_id)
        if tx:
            return tx.status
        return None

    async def wait_for_confirmation(
        self,
        tx_id: str,
        min_confirmations: int = 10,
    ) -> bool:
        """
        Wait for transaction confirmation.

        In production, would poll until confirmed.
        """
        tx = self._tx_cache.get(tx_id)
        if tx:
            # Simulate confirmation
            tx.status = TransactionStatus.CONFIRMED
            tx.confirmations = min_confirmations
            tx.block_height = NETWORK_INFO["height"]
            self._stats["transactions_confirmed"] += 1
            return True
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # PRICING
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_price(self, bytes_size: int) -> StorageCost:
        """
        Get storage price for data size.

        Args:
            bytes_size: Size in bytes
        """
        # Simplified pricing model
        # Real Arweave pricing depends on network difficulty and endowment
        base_rate = 1000  # Winston per byte (simplified)
        winston = bytes_size * base_rate

        ar = winston / WINSTON_PER_AR

        # Rough USD estimate (AR price varies)
        ar_price_usd = 5.0  # Placeholder
        usd = ar * ar_price_usd

        return StorageCost(
            bytes_size=bytes_size,
            winston=winston,
            ar=ar,
            usd_estimate=usd,
        )

    async def get_balance(self, address: str) -> int:
        """Get wallet balance in Winston."""
        # In production, query gateway
        return 1000000000000  # 1 AR placeholder

    # ═══════════════════════════════════════════════════════════════════════════
    # GRAPHQL QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    async def query_transactions(
        self,
        owners: Optional[List[str]] = None,
        tags: Optional[List[Dict[str, str]]] = None,
        first: int = 10,
    ) -> List[ArweaveTransaction]:
        """
        Query transactions via GraphQL.

        Args:
            owners: Filter by owner addresses
            tags: Filter by tags
            first: Number of results
        """
        # In production, execute GraphQL query against gateway
        results = []

        # Return cached transactions matching criteria
        for tx in list(self._tx_cache.values())[:first]:
            if owners and tx.owner not in owners:
                continue

            if tags:
                match = True
                for tag_filter in tags:
                    tx_value = tx.get_tag(tag_filter["name"])
                    if tx_value != tag_filter.get("value"):
                        match = False
                        break
                if not match:
                    continue

            results.append(tx)

        return results

    async def search_by_app(
        self,
        app_name: str,
        first: int = 10,
    ) -> List[ArweaveTransaction]:
        """Search transactions by app name."""
        return await self.query_transactions(
            tags=[{"name": "App-Name", "value": app_name}],
            first=first,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SMARTWEAVE SUPPORT
    # ═══════════════════════════════════════════════════════════════════════════

    async def deploy_contract(
        self,
        source_code: str,
        initial_state: Dict[str, Any],
    ) -> ArweaveTransaction:
        """
        Deploy a SmartWeave contract.

        Args:
            source_code: Contract source code
            initial_state: Initial contract state
        """
        import json

        # Upload source code
        source_tx = await self.upload(
            data=source_code.encode(),
            content_type="application/javascript",
            tags=[
                {"name": "App-Name", "value": "SmartWeaveContract"},
                {"name": "Contract-Type", "value": "javascript"},
            ],
        )

        # Upload initial state with contract reference
        state_tx = await self.upload_json(
            data=initial_state,
            tags=[
                {"name": "App-Name", "value": "SmartWeaveContract"},
                {"name": "Contract-Src", "value": source_tx.tx_id},
                {"name": "Init-State", "value": json.dumps(initial_state)},
            ],
        )

        return state_tx

    async def interact_with_contract(
        self,
        contract_id: str,
        input_data: Dict[str, Any],
    ) -> ArweaveTransaction:
        """
        Create an interaction with a SmartWeave contract.

        Args:
            contract_id: Contract transaction ID
            input_data: Interaction input
        """
        import json

        return await self.upload_json(
            data={"function": input_data.get("function", ""), "input": input_data},
            tags=[
                {"name": "App-Name", "value": "SmartWeaveAction"},
                {"name": "Contract", "value": contract_id},
                {"name": "Input", "value": json.dumps(input_data)},
            ],
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_data_url(self, tx_id: str) -> str:
        """Get URL to retrieve data."""
        return f"{self._gateway_url}/{tx_id}"

    def get_graphql_url(self) -> str:
        """Get GraphQL endpoint URL."""
        return f"{self._gateway_url}/graphql"

    async def get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        return NETWORK_INFO.copy()

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            **self._stats,
            "cached_transactions": len(self._tx_cache),
            "cached_bundles": len(self._bundle_cache),
            "gateway": self._gateway_url,
            "bundlr_node": self._bundlr_node,
            "total_ar_spent": self._stats["total_winston_spent"] / WINSTON_PER_AR,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_adapter_instance: Optional[ArweaveAdapter] = None


def get_arweave_adapter() -> ArweaveAdapter:
    """Get singleton ArweaveAdapter instance."""
    global _adapter_instance

    if _adapter_instance is None:
        _adapter_instance = ArweaveAdapter()

    return _adapter_instance
