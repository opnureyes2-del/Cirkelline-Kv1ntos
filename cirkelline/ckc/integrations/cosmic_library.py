"""
CKC Cosmic Library Connector
============================

Auto-arkivering og integration med Cosmic Library.

Enables:
- Automatic archiving of creative outputs
- Asset versioning and history
- Metadata extraction and tagging
- Search and retrieval
- MASTERMIND session context linking

Eksempel:
    connector = await create_cosmic_connector()

    # Archive a creative result
    asset = await connector.archive_creative_result(
        result=creative_result,
        session_id="mastermind_123",
        tags=["dragon", "fantasy"]
    )

    # Search assets
    assets = await connector.search_assets(
        query="dragon",
        asset_type=AssetType.IMAGE
    )
"""

import asyncio
import logging
import uuid
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class AssetType(Enum):
    """Types of creative assets."""
    IMAGE = "image"
    ANIMATION = "animation"
    VIDEO = "video"
    VECTOR = "vector"
    AUDIO = "audio"
    DOCUMENT = "document"
    COMPOSITE = "composite"  # Multi-asset bundle


class ArchiveStatus(Enum):
    """Status of archive operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class AssetVisibility(Enum):
    """Asset visibility levels."""
    PRIVATE = "private"      # Only owner can see
    TEAM = "team"            # Team members can see
    ORGANIZATION = "org"     # Organization-wide
    PUBLIC = "public"        # Publicly accessible


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AssetMetadata:
    """Metadata for a creative asset."""
    # Core
    title: str
    description: str
    tags: List[str] = field(default_factory=list)

    # Creative details
    prompt: str = ""
    negative_prompt: str = ""
    style: str = ""
    model: str = ""

    # Technical
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0
    file_size_bytes: int = 0
    format: str = ""
    color_profile: str = ""

    # Generation params
    seed: Optional[int] = None
    guidance_scale: float = 7.5
    inference_steps: int = 30

    # Quality
    quality_score: float = 0.0
    aesthetic_score: float = 0.0

    # Custom
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "style": self.style,
            "model": self.model,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "file_size_bytes": self.file_size_bytes,
            "format": self.format,
            "color_profile": self.color_profile,
            "seed": self.seed,
            "guidance_scale": self.guidance_scale,
            "inference_steps": self.inference_steps,
            "quality_score": self.quality_score,
            "aesthetic_score": self.aesthetic_score,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetMetadata":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AssetVersion:
    """A version of an asset."""
    version_id: str
    version_number: int
    file_path: str
    file_url: Optional[str] = None
    file_hash: str = ""
    file_size_bytes: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    changelog: str = ""
    metadata_changes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "file_hash": self.file_hash,
            "file_size_bytes": self.file_size_bytes,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "changelog": self.changelog,
        }


@dataclass
class CreativeAsset:
    """A creative asset in the Cosmic Library."""
    asset_id: str
    asset_type: AssetType
    owner_id: str
    metadata: AssetMetadata

    # Files
    primary_file_path: str
    primary_file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None

    # Versioning
    current_version: int = 1
    versions: List[AssetVersion] = field(default_factory=list)

    # Context
    session_id: Optional[str] = None  # MASTERMIND session
    task_id: Optional[str] = None
    source_request_id: Optional[str] = None

    # Access
    visibility: AssetVisibility = AssetVisibility.PRIVATE
    shared_with: List[str] = field(default_factory=list)

    # Statistics
    view_count: int = 0
    download_count: int = 0
    favorite_count: int = 0

    # Cost tracking
    generation_cost_usd: float = 0.0

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    archived_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type.value,
            "owner_id": self.owner_id,
            "metadata": self.metadata.to_dict(),
            "primary_file_path": self.primary_file_path,
            "primary_file_url": self.primary_file_url,
            "thumbnail_url": self.thumbnail_url,
            "preview_url": self.preview_url,
            "current_version": self.current_version,
            "versions": [v.to_dict() for v in self.versions],
            "session_id": self.session_id,
            "task_id": self.task_id,
            "source_request_id": self.source_request_id,
            "visibility": self.visibility.value,
            "shared_with": self.shared_with,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "favorite_count": self.favorite_count,
            "generation_cost_usd": self.generation_cost_usd,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }


@dataclass
class ArchiveResult:
    """Result of an archive operation."""
    success: bool
    asset_id: Optional[str] = None
    status: ArchiveStatus = ArchiveStatus.PENDING
    message: str = ""
    error: Optional[str] = None
    asset: Optional[CreativeAsset] = None
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "asset_id": self.asset_id,
            "status": self.status.value,
            "message": self.message,
            "error": self.error,
            "processing_time_ms": self.processing_time_ms,
        }


# =============================================================================
# ASSET REGISTRY
# =============================================================================

class AssetRegistry:
    """
    Registry for creative assets.

    Manages asset indexing and search.
    """

    def __init__(self):
        self._assets: Dict[str, CreativeAsset] = {}
        self._by_owner: Dict[str, Set[str]] = {}
        self._by_session: Dict[str, Set[str]] = {}
        self._by_tag: Dict[str, Set[str]] = {}
        self._by_type: Dict[AssetType, Set[str]] = {}

    def register(self, asset: CreativeAsset) -> None:
        """Register an asset."""
        self._assets[asset.asset_id] = asset

        # Index by owner
        if asset.owner_id not in self._by_owner:
            self._by_owner[asset.owner_id] = set()
        self._by_owner[asset.owner_id].add(asset.asset_id)

        # Index by session
        if asset.session_id:
            if asset.session_id not in self._by_session:
                self._by_session[asset.session_id] = set()
            self._by_session[asset.session_id].add(asset.asset_id)

        # Index by type
        if asset.asset_type not in self._by_type:
            self._by_type[asset.asset_type] = set()
        self._by_type[asset.asset_type].add(asset.asset_id)

        # Index by tags
        for tag in asset.metadata.tags:
            tag_lower = tag.lower()
            if tag_lower not in self._by_tag:
                self._by_tag[tag_lower] = set()
            self._by_tag[tag_lower].add(asset.asset_id)

    def get(self, asset_id: str) -> Optional[CreativeAsset]:
        """Get an asset by ID."""
        return self._assets.get(asset_id)

    def get_by_owner(self, owner_id: str) -> List[CreativeAsset]:
        """Get all assets for an owner."""
        asset_ids = self._by_owner.get(owner_id, set())
        return [self._assets[aid] for aid in asset_ids if aid in self._assets]

    def get_by_session(self, session_id: str) -> List[CreativeAsset]:
        """Get all assets for a session."""
        asset_ids = self._by_session.get(session_id, set())
        return [self._assets[aid] for aid in asset_ids if aid in self._assets]

    def get_by_type(self, asset_type: AssetType) -> List[CreativeAsset]:
        """Get all assets of a type."""
        asset_ids = self._by_type.get(asset_type, set())
        return [self._assets[aid] for aid in asset_ids if aid in self._assets]

    def search_by_tag(self, tag: str) -> List[CreativeAsset]:
        """Search assets by tag."""
        tag_lower = tag.lower()
        asset_ids = self._by_tag.get(tag_lower, set())
        return [self._assets[aid] for aid in asset_ids if aid in self._assets]

    def search(
        self,
        query: str,
        asset_type: Optional[AssetType] = None,
        owner_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[CreativeAsset]:
        """
        Search assets.

        Args:
            query: Search query (matches title, description, prompt)
            asset_type: Filter by type
            owner_id: Filter by owner
            tags: Filter by tags
            limit: Maximum results

        Returns:
            List of matching assets
        """
        results = []
        query_lower = query.lower()

        for asset in self._assets.values():
            # Apply filters
            if asset_type and asset.asset_type != asset_type:
                continue
            if owner_id and asset.owner_id != owner_id:
                continue
            if tags:
                asset_tags = {t.lower() for t in asset.metadata.tags}
                if not all(t.lower() in asset_tags for t in tags):
                    continue

            # Search in text fields
            searchable = " ".join([
                asset.metadata.title,
                asset.metadata.description,
                asset.metadata.prompt,
                " ".join(asset.metadata.tags),
            ]).lower()

            if query_lower in searchable:
                results.append(asset)

            if len(results) >= limit:
                break

        return results

    def count(self) -> int:
        """Get total asset count."""
        return len(self._assets)

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        type_counts = {
            asset_type.value: len(asset_ids)
            for asset_type, asset_ids in self._by_type.items()
        }

        return {
            "total_assets": self.count(),
            "owners": len(self._by_owner),
            "sessions": len(self._by_session),
            "unique_tags": len(self._by_tag),
            "by_type": type_counts,
        }


# =============================================================================
# COSMIC LIBRARY CONNECTOR
# =============================================================================

class CosmicLibraryConnector:
    """
    Connector for Cosmic Library integration.

    Handles:
    - Auto-archiving of creative outputs
    - Asset management
    - Version control
    - Search and retrieval
    - MASTERMIND context linking
    """

    def __init__(
        self,
        storage_path: str = "/tmp/cosmic_library",
        base_url: str = "https://cosmic.cirkelline.com",
        api_key: Optional[str] = None,
    ):
        self._storage_path = Path(storage_path)
        self._base_url = base_url
        self._api_key = api_key

        self._registry = AssetRegistry()

        # Statistics
        self._total_archived = 0
        self._total_bytes = 0
        self._total_cost_usd = 0.0

        # Auto-archive settings
        self._auto_archive_enabled = True
        self._auto_archive_min_quality = 0.5  # Minimum quality score to auto-archive

        # Ensure storage directory exists
        self._storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"CosmicLibraryConnector initialized (storage: {storage_path})")

    # =========================================================================
    # ARCHIVE OPERATIONS
    # =========================================================================

    async def archive_creative_result(
        self,
        result: Any,  # CreativeResult from tegne_enhed
        owner_id: str = "system",
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: AssetVisibility = AssetVisibility.PRIVATE,
    ) -> ArchiveResult:
        """
        Archive a creative result to Cosmic Library.

        Args:
            result: CreativeResult from tegne_enhed
            owner_id: Owner of the asset
            session_id: MASTERMIND session ID
            task_id: Related task ID
            title: Override title
            description: Override description
            tags: Additional tags
            visibility: Asset visibility

        Returns:
            ArchiveResult
        """
        import time
        start_time = time.time()

        try:
            # Check quality threshold
            quality_score = getattr(result, 'quality_score', 0.0)
            if self._auto_archive_enabled and quality_score < self._auto_archive_min_quality:
                return ArchiveResult(
                    success=False,
                    status=ArchiveStatus.FAILED,
                    message=f"Quality score {quality_score} below threshold {self._auto_archive_min_quality}",
                )

            # Determine asset type
            asset_type = self._determine_asset_type(result)

            # Extract metadata
            metadata = self._extract_metadata(result, title, description, tags)

            # Get primary file
            file_path = ""
            file_url = None

            if hasattr(result, 'output_paths') and result.output_paths:
                file_path = result.output_paths[0]
            if hasattr(result, 'output_urls') and result.output_urls:
                file_url = result.output_urls[0]

            # Generate asset ID
            asset_id = f"asset_{uuid.uuid4().hex[:16]}"

            # Create asset
            asset = CreativeAsset(
                asset_id=asset_id,
                asset_type=asset_type,
                owner_id=owner_id,
                metadata=metadata,
                primary_file_path=file_path,
                primary_file_url=file_url,
                thumbnail_url=file_url,  # Use same for now
                preview_url=file_url,
                session_id=session_id,
                task_id=task_id,
                source_request_id=getattr(result, 'request_id', None),
                visibility=visibility,
                generation_cost_usd=getattr(result, 'cost_usd', 0.0),
            )

            # Create initial version
            version = AssetVersion(
                version_id=f"v_{uuid.uuid4().hex[:8]}",
                version_number=1,
                file_path=file_path,
                file_url=file_url,
                created_by=owner_id,
                changelog="Initial version",
            )
            asset.versions.append(version)

            # Register asset
            self._registry.register(asset)

            # Update statistics
            self._total_archived += 1
            self._total_cost_usd += asset.generation_cost_usd

            processing_time = (time.time() - start_time) * 1000

            logger.info(f"Archived creative asset: {asset_id} ({asset_type.value})")

            return ArchiveResult(
                success=True,
                asset_id=asset_id,
                status=ArchiveStatus.COMPLETED,
                message=f"Successfully archived {asset_type.value} asset",
                asset=asset,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Archive failed: {e}")
            return ArchiveResult(
                success=False,
                status=ArchiveStatus.FAILED,
                error=str(e),
            )

    async def archive_file(
        self,
        file_path: str,
        asset_type: AssetType,
        owner_id: str = "system",
        title: str = "",
        description: str = "",
        tags: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        visibility: AssetVisibility = AssetVisibility.PRIVATE,
    ) -> ArchiveResult:
        """Archive a file directly."""
        try:
            # Create metadata
            metadata = AssetMetadata(
                title=title or Path(file_path).stem,
                description=description,
                tags=tags or [],
                format=Path(file_path).suffix.lstrip('.'),
            )

            # Get file size
            path = Path(file_path)
            if path.exists():
                metadata.file_size_bytes = path.stat().st_size

            # Generate asset ID
            asset_id = f"asset_{uuid.uuid4().hex[:16]}"

            # Create asset
            asset = CreativeAsset(
                asset_id=asset_id,
                asset_type=asset_type,
                owner_id=owner_id,
                metadata=metadata,
                primary_file_path=file_path,
                session_id=session_id,
                visibility=visibility,
            )

            # Create initial version
            version = AssetVersion(
                version_id=f"v_{uuid.uuid4().hex[:8]}",
                version_number=1,
                file_path=file_path,
                file_size_bytes=metadata.file_size_bytes,
                created_by=owner_id,
                changelog="Initial version",
            )
            asset.versions.append(version)

            # Register
            self._registry.register(asset)
            self._total_archived += 1
            self._total_bytes += metadata.file_size_bytes

            return ArchiveResult(
                success=True,
                asset_id=asset_id,
                status=ArchiveStatus.COMPLETED,
                asset=asset,
            )

        except Exception as e:
            return ArchiveResult(
                success=False,
                status=ArchiveStatus.FAILED,
                error=str(e),
            )

    # =========================================================================
    # VERSION MANAGEMENT
    # =========================================================================

    async def create_version(
        self,
        asset_id: str,
        file_path: str,
        changelog: str = "",
        created_by: str = "system",
    ) -> Optional[AssetVersion]:
        """Create a new version of an asset."""
        asset = self._registry.get(asset_id)
        if not asset:
            return None

        version_number = asset.current_version + 1

        version = AssetVersion(
            version_id=f"v_{uuid.uuid4().hex[:8]}",
            version_number=version_number,
            file_path=file_path,
            created_by=created_by,
            changelog=changelog,
        )

        asset.versions.append(version)
        asset.current_version = version_number
        asset.primary_file_path = file_path
        asset.updated_at = datetime.now(timezone.utc)

        logger.info(f"Created version {version_number} for asset {asset_id}")

        return version

    async def get_version_history(
        self,
        asset_id: str,
    ) -> List[Dict[str, Any]]:
        """Get version history for an asset."""
        asset = self._registry.get(asset_id)
        if not asset:
            return []

        return [v.to_dict() for v in asset.versions]

    # =========================================================================
    # QUERY OPERATIONS
    # =========================================================================

    async def get_asset(self, asset_id: str) -> Optional[CreativeAsset]:
        """Get an asset by ID."""
        return self._registry.get(asset_id)

    async def search_assets(
        self,
        query: str = "",
        asset_type: Optional[AssetType] = None,
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[CreativeAsset]:
        """
        Search for assets.

        Args:
            query: Search query
            asset_type: Filter by type
            owner_id: Filter by owner
            session_id: Filter by MASTERMIND session
            tags: Filter by tags
            limit: Maximum results

        Returns:
            List of matching assets
        """
        if session_id:
            # Direct session lookup
            assets = self._registry.get_by_session(session_id)
            if asset_type:
                assets = [a for a in assets if a.asset_type == asset_type]
            return assets[:limit]

        if query:
            return self._registry.search(
                query=query,
                asset_type=asset_type,
                owner_id=owner_id,
                tags=tags,
                limit=limit,
            )

        # No query - return by type or owner
        if asset_type:
            return self._registry.get_by_type(asset_type)[:limit]

        if owner_id:
            return self._registry.get_by_owner(owner_id)[:limit]

        return []

    async def get_session_assets(
        self,
        session_id: str,
    ) -> List[CreativeAsset]:
        """Get all assets for a MASTERMIND session."""
        return self._registry.get_by_session(session_id)

    async def get_recent_assets(
        self,
        limit: int = 20,
        owner_id: Optional[str] = None,
    ) -> List[CreativeAsset]:
        """Get recent assets."""
        assets = list(self._registry._assets.values())

        if owner_id:
            assets = [a for a in assets if a.owner_id == owner_id]

        # Sort by creation time, newest first
        assets.sort(key=lambda a: a.created_at, reverse=True)

        return assets[:limit]

    # =========================================================================
    # METADATA OPERATIONS
    # =========================================================================

    async def update_metadata(
        self,
        asset_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update asset metadata."""
        asset = self._registry.get(asset_id)
        if not asset:
            return False

        if title is not None:
            asset.metadata.title = title
        if description is not None:
            asset.metadata.description = description
        if tags is not None:
            asset.metadata.tags = tags
        if custom is not None:
            asset.metadata.custom.update(custom)

        asset.updated_at = datetime.now(timezone.utc)

        return True

    async def add_tags(
        self,
        asset_id: str,
        tags: List[str],
    ) -> bool:
        """Add tags to an asset."""
        asset = self._registry.get(asset_id)
        if not asset:
            return False

        for tag in tags:
            if tag not in asset.metadata.tags:
                asset.metadata.tags.append(tag)

                # Update index
                tag_lower = tag.lower()
                if tag_lower not in self._registry._by_tag:
                    self._registry._by_tag[tag_lower] = set()
                self._registry._by_tag[tag_lower].add(asset_id)

        return True

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _determine_asset_type(self, result: Any) -> AssetType:
        """Determine asset type from creative result."""
        # Check capability
        capability = getattr(result, 'capability', None)
        if capability:
            capability_value = capability.value if hasattr(capability, 'value') else str(capability)

            if 'animation' in capability_value.lower():
                return AssetType.ANIMATION
            if 'vector' in capability_value.lower():
                return AssetType.VECTOR
            if 'image' in capability_value.lower():
                return AssetType.IMAGE

        # Check output format
        output_format = getattr(result, 'output_format', None)
        if output_format:
            format_value = output_format.value if hasattr(output_format, 'value') else str(output_format)

            if format_value in ['mp4', 'gif', 'webm']:
                return AssetType.ANIMATION
            if format_value in ['svg', 'pdf', 'eps']:
                return AssetType.VECTOR

        return AssetType.IMAGE

    def _extract_metadata(
        self,
        result: Any,
        title: Optional[str],
        description: Optional[str],
        tags: Optional[List[str]],
    ) -> AssetMetadata:
        """Extract metadata from creative result."""
        # Get from result metadata
        result_metadata = getattr(result, 'metadata', {})

        return AssetMetadata(
            title=title or result_metadata.get('title', f"Creative Output"),
            description=description or result_metadata.get('description', ''),
            tags=tags or result_metadata.get('tags', []),
            prompt=result_metadata.get('prompt_used', result_metadata.get('prompt', '')),
            negative_prompt=result_metadata.get('negative_prompt', ''),
            style=result_metadata.get('style', ''),
            model=getattr(result, 'model_used', ''),
            quality_score=getattr(result, 'quality_score', 0.0),
            aesthetic_score=getattr(result, 'aesthetic_score', 0.0),
        )

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def set_auto_archive(
        self,
        enabled: bool,
        min_quality: float = 0.5,
    ) -> None:
        """Configure auto-archiving."""
        self._auto_archive_enabled = enabled
        self._auto_archive_min_quality = min_quality

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get connector statistics."""
        return {
            "total_archived": self._total_archived,
            "total_bytes": self._total_bytes,
            "total_cost_usd": self._total_cost_usd,
            "auto_archive_enabled": self._auto_archive_enabled,
            "registry": self._registry.get_statistics(),
        }


# =============================================================================
# FACTORY
# =============================================================================

_connector: Optional[CosmicLibraryConnector] = None


async def create_cosmic_connector(
    storage_path: str = "/tmp/cosmic_library",
    base_url: str = "https://cosmic.cirkelline.com",
    api_key: Optional[str] = None,
) -> CosmicLibraryConnector:
    """
    Create the Cosmic Library connector singleton.

    Args:
        storage_path: Local storage path
        base_url: Cosmic Library API base URL
        api_key: API key for authentication

    Returns:
        CosmicLibraryConnector instance
    """
    global _connector
    _connector = CosmicLibraryConnector(
        storage_path=storage_path,
        base_url=base_url,
        api_key=api_key,
    )
    logger.info("CosmicLibraryConnector created")
    return _connector


def get_cosmic_connector() -> Optional[CosmicLibraryConnector]:
    """Get the existing Cosmic Library connector."""
    return _connector


logger.info("CKC Cosmic Library connector module loaded")
