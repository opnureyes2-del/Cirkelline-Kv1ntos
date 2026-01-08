"""
IPFS Adapter
============
InterPlanetary File System integration.

Responsibilities:
- Store and retrieve content from IPFS
- Manage pinning and persistence
- Handle gateway access
- Support CAR file operations
"""

import logging
import hashlib
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class PinStatus(Enum):
    """Pinning status."""
    PINNED = "pinned"
    PINNING = "pinning"
    UNPINNED = "unpinned"
    FAILED = "failed"
    QUEUED = "queued"


class ContentType(Enum):
    """Content types for IPFS."""
    RAW = "raw"
    DAG_PB = "dag-pb"
    DAG_CBOR = "dag-cbor"
    DAG_JSON = "dag-json"


@dataclass
class IPFSFile:
    """An IPFS file reference."""
    cid: str  # Content Identifier
    name: str = ""
    size: int = 0
    content_type: str = ""
    pin_status: PinStatus = PinStatus.UNPINNED
    created_at: str = ""
    gateway_url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cid": self.cid,
            "name": self.name,
            "size": self.size,
            "content_type": self.content_type,
            "pin_status": self.pin_status.value,
            "gateway_url": self.gateway_url,
        }


@dataclass
class PinInfo:
    """Pin information."""
    cid: str
    status: PinStatus
    name: str = ""
    delegates: List[str] = field(default_factory=list)
    created: str = ""
    size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cid": self.cid,
            "status": self.status.value,
            "name": self.name,
            "size": self.size,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# IPFS ADAPTER
# ═══════════════════════════════════════════════════════════════════════════════

class IPFSAdapter:
    """
    IPFS storage adapter.

    Provides interface for storing and retrieving
    content from the InterPlanetary File System.
    """

    def __init__(
        self,
        gateway_url: str = "https://ipfs.io",
        api_url: Optional[str] = None,
        pinning_service: Optional[str] = None,
    ):
        self._gateway_url = gateway_url.rstrip("/")
        self._api_url = api_url or "http://127.0.0.1:5001"
        self._pinning_service = pinning_service

        # Cache
        self._file_cache: Dict[str, IPFSFile] = {}
        self._pin_cache: Dict[str, PinInfo] = {}

        # Statistics
        self._stats = {
            "files_added": 0,
            "files_retrieved": 0,
            "pins_created": 0,
            "total_bytes_stored": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # STORAGE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def add(
        self,
        content: bytes,
        name: str = "",
        pin: bool = True,
        content_type: str = "application/octet-stream",
    ) -> IPFSFile:
        """
        Add content to IPFS.

        Args:
            content: Content bytes
            name: Optional filename
            pin: Whether to pin the content
            content_type: MIME type
        """
        self._stats["files_added"] += 1
        self._stats["total_bytes_stored"] += len(content)

        # Calculate CID (simplified - real implementation uses multihash)
        content_hash = hashlib.sha256(content).hexdigest()
        cid = f"Qm{content_hash[:44]}"  # Mock CID format

        ipfs_file = IPFSFile(
            cid=cid,
            name=name,
            size=len(content),
            content_type=content_type,
            pin_status=PinStatus.PINNED if pin else PinStatus.UNPINNED,
            created_at=datetime.utcnow().isoformat() + "Z",
            gateway_url=f"{self._gateway_url}/ipfs/{cid}",
        )

        self._file_cache[cid] = ipfs_file

        if pin:
            await self._pin_content(cid)

        return ipfs_file

    async def add_json(
        self,
        data: Dict[str, Any],
        name: str = "",
        pin: bool = True,
    ) -> IPFSFile:
        """Add JSON data to IPFS."""
        import json
        content = json.dumps(data, sort_keys=True).encode()
        return await self.add(
            content=content,
            name=name or "data.json",
            pin=pin,
            content_type="application/json",
        )

    async def get(self, cid: str) -> Optional[bytes]:
        """
        Retrieve content from IPFS.

        Args:
            cid: Content Identifier
        """
        self._stats["files_retrieved"] += 1

        # Check cache
        if cid in self._file_cache:
            # In production, fetch from IPFS node or gateway
            return b"[cached content]"

        # In production, use aiohttp to fetch from gateway
        return None

    async def get_json(self, cid: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON from IPFS."""
        import json
        content = await self.get(cid)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
        return None

    async def cat(self, path: str) -> Optional[bytes]:
        """
        Cat file from IPFS path.

        Args:
            path: IPFS path (e.g., /ipfs/Qm.../file.txt)
        """
        # Extract CID from path
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "ipfs":
            cid = parts[1]
            return await self.get(cid)
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # PINNING
    # ═══════════════════════════════════════════════════════════════════════════

    async def pin(self, cid: str, name: str = "") -> PinInfo:
        """
        Pin content to ensure persistence.

        Args:
            cid: Content Identifier
            name: Optional pin name
        """
        self._stats["pins_created"] += 1
        return await self._pin_content(cid, name)

    async def unpin(self, cid: str) -> bool:
        """
        Unpin content.

        Args:
            cid: Content Identifier
        """
        if cid in self._pin_cache:
            self._pin_cache[cid].status = PinStatus.UNPINNED
            return True
        return False

    async def get_pin_status(self, cid: str) -> Optional[PinInfo]:
        """Get pin status for a CID."""
        return self._pin_cache.get(cid)

    async def list_pins(self) -> List[PinInfo]:
        """List all pins."""
        return [
            p for p in self._pin_cache.values()
            if p.status == PinStatus.PINNED
        ]

    async def _pin_content(self, cid: str, name: str = "") -> PinInfo:
        """Internal pin operation."""
        pin_info = PinInfo(
            cid=cid,
            status=PinStatus.PINNED,
            name=name,
            created=datetime.utcnow().isoformat() + "Z",
        )
        self._pin_cache[cid] = pin_info

        # Update file cache
        if cid in self._file_cache:
            self._file_cache[cid].pin_status = PinStatus.PINNED

        return pin_info

    # ═══════════════════════════════════════════════════════════════════════════
    # DIRECTORY OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def add_directory(
        self,
        files: Dict[str, bytes],
        name: str = "",
        pin: bool = True,
    ) -> IPFSFile:
        """
        Add a directory of files.

        Args:
            files: Mapping of filename to content
            name: Directory name
            pin: Whether to pin
        """
        # Add individual files
        entries = []
        total_size = 0

        for filename, content in files.items():
            file_obj = await self.add(content, filename, pin=False)
            entries.append({"name": filename, "cid": file_obj.cid})
            total_size += len(content)

        # Create directory CID (simplified)
        import json
        dir_content = json.dumps(entries, sort_keys=True).encode()
        dir_hash = hashlib.sha256(dir_content).hexdigest()
        dir_cid = f"Qm{dir_hash[:44]}"

        dir_file = IPFSFile(
            cid=dir_cid,
            name=name or "directory",
            size=total_size,
            content_type="application/x-directory",
            pin_status=PinStatus.PINNED if pin else PinStatus.UNPINNED,
            created_at=datetime.utcnow().isoformat() + "Z",
            gateway_url=f"{self._gateway_url}/ipfs/{dir_cid}",
            metadata={"entries": entries},
        )

        self._file_cache[dir_cid] = dir_file

        if pin:
            await self._pin_content(dir_cid)

        return dir_file

    async def ls(self, cid: str) -> List[Dict[str, Any]]:
        """
        List directory contents.

        Args:
            cid: Directory CID
        """
        if cid in self._file_cache:
            return self._file_cache[cid].metadata.get("entries", [])
        return []

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_gateway_url(self, cid: str) -> str:
        """Get public gateway URL for a CID."""
        return f"{self._gateway_url}/ipfs/{cid}"

    def get_ipns_url(self, name: str) -> str:
        """Get IPNS URL."""
        return f"{self._gateway_url}/ipns/{name}"

    def is_valid_cid(self, cid: str) -> bool:
        """Check if CID format is valid."""
        # Simplified validation
        return (
            (cid.startswith("Qm") and len(cid) == 46) or  # CIDv0
            (cid.startswith("bafy") and len(cid) > 50)     # CIDv1
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            **self._stats,
            "cached_files": len(self._file_cache),
            "active_pins": sum(
                1 for p in self._pin_cache.values()
                if p.status == PinStatus.PINNED
            ),
            "gateway": self._gateway_url,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_adapter_instance: Optional[IPFSAdapter] = None


def get_ipfs_adapter() -> IPFSAdapter:
    """Get singleton IPFSAdapter instance."""
    global _adapter_instance

    if _adapter_instance is None:
        _adapter_instance = IPFSAdapter()

    return _adapter_instance
