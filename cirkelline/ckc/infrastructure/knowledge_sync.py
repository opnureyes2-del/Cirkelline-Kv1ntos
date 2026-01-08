"""
CKC Knowledge Sync Manager
==========================

Manages bidirectional synchronization between knowledge sources:
- CKC's internal knowledge graph (PostgreSQL)
- Notion workspaces
- External documents
- Platform-specific knowledge banks

Supports conflict resolution, versioning, and incremental sync.
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import json

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Sync direction."""
    PUSH = "push"      # Local -> Remote
    PULL = "pull"      # Remote -> Local
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(Enum):
    """Status of sync operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ConflictResolution(Enum):
    """Strategy for resolving conflicts."""
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    NEWEST_WINS = "newest_wins"
    MERGE = "merge"
    MANUAL = "manual"


@dataclass
class KnowledgeEntry:
    """
    A knowledge entry that can be synced across sources.

    Represents a piece of knowledge with metadata for tracking
    changes and enabling sync operations.
    """
    entry_id: str
    title: str
    content: str
    category: str
    tags: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    content_hash: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source: str = "local"  # local, notion, document, etc.
    source_id: Optional[str] = None  # ID in source system

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = self._compute_hash()
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = self.created_at

    def _compute_hash(self) -> str:
        """Compute content hash for change detection."""
        content = f"{self.title}:{self.content}:{json.dumps(self.tags, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def has_changed(self, other: "KnowledgeEntry") -> bool:
        """Check if content has changed compared to another entry."""
        return self.content_hash != other.content_hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "source_refs": self.source_refs,
            "metadata": self.metadata,
            "version": self.version,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source": self.source,
            "source_id": self.source_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEntry":
        """Create from dictionary."""
        return cls(
            entry_id=data["entry_id"],
            title=data["title"],
            content=data["content"],
            category=data["category"],
            tags=data.get("tags", []),
            source_refs=data.get("source_refs", []),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
            content_hash=data.get("content_hash", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            source=data.get("source", "local"),
            source_id=data.get("source_id")
        )


@dataclass
class SyncResult:
    """Result of a sync operation."""
    status: SyncStatus
    source: str
    target: str
    direction: SyncDirection
    entries_synced: int = 0
    entries_created: int = 0
    entries_updated: int = 0
    entries_deleted: int = 0
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "source": self.source,
            "target": self.target,
            "direction": self.direction.value,
            "entries_synced": self.entries_synced,
            "entries_created": self.entries_created,
            "entries_updated": self.entries_updated,
            "entries_deleted": self.entries_deleted,
            "conflicts": self.conflicts,
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }


@dataclass
class SyncState:
    """State of sync between two sources."""
    source: str
    target: str
    last_sync: Optional[datetime] = None
    last_sync_hash: Optional[str] = None
    entries_count: int = 0
    pending_changes: int = 0
    status: SyncStatus = SyncStatus.PENDING


class KnowledgeSyncManager:
    """
    Manages bidirectional sync between knowledge sources.

    Features:
    - Incremental sync based on content hashes
    - Conflict detection and resolution
    - Multi-source support (local DB, Notion, documents)
    - Audit trail of sync operations
    """

    def __init__(self):
        self._sources: Dict[str, "KnowledgeSource"] = {}
        self._sync_states: Dict[str, SyncState] = {}
        self._conflict_resolution = ConflictResolution.NEWEST_WINS
        self._sync_history: List[SyncResult] = []

        logger.info("Knowledge Sync Manager initialized")

    def register_source(self, source: "KnowledgeSource") -> None:
        """Register a knowledge source."""
        self._sources[source.source_id] = source
        logger.info(f"Registered knowledge source: {source.source_id}")

    def unregister_source(self, source_id: str) -> None:
        """Unregister a knowledge source."""
        if source_id in self._sources:
            del self._sources[source_id]
            logger.info(f"Unregistered knowledge source: {source_id}")

    def get_source(self, source_id: str) -> Optional["KnowledgeSource"]:
        """Get a registered source."""
        return self._sources.get(source_id)

    def list_sources(self) -> List[str]:
        """List all registered sources."""
        return list(self._sources.keys())

    async def sync(
        self,
        source_id: str,
        target_id: str,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        conflict_resolution: Optional[ConflictResolution] = None
    ) -> SyncResult:
        """
        Sync between two sources.

        Args:
            source_id: Source to sync from
            target_id: Target to sync to
            direction: Sync direction
            conflict_resolution: How to resolve conflicts

        Returns:
            SyncResult with sync details
        """
        result = SyncResult(
            status=SyncStatus.IN_PROGRESS,
            source=source_id,
            target=target_id,
            direction=direction,
            started_at=datetime.utcnow()
        )

        try:
            source = self._sources.get(source_id)
            target = self._sources.get(target_id)

            if not source:
                result.status = SyncStatus.FAILED
                result.errors.append(f"Source not found: {source_id}")
                return result

            if not target:
                result.status = SyncStatus.FAILED
                result.errors.append(f"Target not found: {target_id}")
                return result

            resolution = conflict_resolution or self._conflict_resolution

            # Get entries from both sources
            source_entries = await source.list_entries()
            target_entries = await target.list_entries()

            # Create lookup maps
            source_map = {e.entry_id: e for e in source_entries}
            target_map = {e.entry_id: e for e in target_entries}

            # Determine operations
            if direction in (SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL):
                await self._sync_push(source, target, source_map, target_map, resolution, result)

            if direction in (SyncDirection.PULL, SyncDirection.BIDIRECTIONAL):
                await self._sync_pull(source, target, source_map, target_map, resolution, result)

            result.status = SyncStatus.COMPLETED if not result.errors else SyncStatus.PARTIAL
            result.completed_at = datetime.utcnow()

            # Update sync state
            self._update_sync_state(source_id, target_id, result)

        except Exception as e:
            logger.error(f"Sync error: {e}")
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()

        self._sync_history.append(result)
        return result

    async def _sync_push(
        self,
        source: "KnowledgeSource",
        target: "KnowledgeSource",
        source_map: Dict[str, KnowledgeEntry],
        target_map: Dict[str, KnowledgeEntry],
        resolution: ConflictResolution,
        result: SyncResult
    ) -> None:
        """Push changes from source to target."""
        for entry_id, source_entry in source_map.items():
            try:
                if entry_id not in target_map:
                    # Create new entry in target
                    await target.create_entry(source_entry)
                    result.entries_created += 1
                    result.entries_synced += 1
                else:
                    # Check for changes
                    target_entry = target_map[entry_id]
                    if source_entry.has_changed(target_entry):
                        # Conflict or update
                        resolved = await self._resolve_conflict(
                            source_entry, target_entry, resolution
                        )
                        if resolved:
                            await target.update_entry(resolved)
                            result.entries_updated += 1
                            result.entries_synced += 1
                        else:
                            result.conflicts.append({
                                "entry_id": entry_id,
                                "source_version": source_entry.version,
                                "target_version": target_entry.version
                            })
            except Exception as e:
                result.errors.append(f"Push error for {entry_id}: {e}")

    async def _sync_pull(
        self,
        source: "KnowledgeSource",
        target: "KnowledgeSource",
        source_map: Dict[str, KnowledgeEntry],
        target_map: Dict[str, KnowledgeEntry],
        resolution: ConflictResolution,
        result: SyncResult
    ) -> None:
        """Pull changes from target to source."""
        for entry_id, target_entry in target_map.items():
            try:
                if entry_id not in source_map:
                    # Create new entry in source
                    await source.create_entry(target_entry)
                    result.entries_created += 1
                    result.entries_synced += 1
                # Updates already handled in push for bidirectional
            except Exception as e:
                result.errors.append(f"Pull error for {entry_id}: {e}")

    async def _resolve_conflict(
        self,
        local: KnowledgeEntry,
        remote: KnowledgeEntry,
        resolution: ConflictResolution
    ) -> Optional[KnowledgeEntry]:
        """Resolve conflict between two entries."""
        if resolution == ConflictResolution.LOCAL_WINS:
            local.version = max(local.version, remote.version) + 1
            return local

        elif resolution == ConflictResolution.REMOTE_WINS:
            remote.version = max(local.version, remote.version) + 1
            return remote

        elif resolution == ConflictResolution.NEWEST_WINS:
            if local.updated_at and remote.updated_at:
                winner = local if local.updated_at > remote.updated_at else remote
            else:
                winner = local
            winner.version = max(local.version, remote.version) + 1
            return winner

        elif resolution == ConflictResolution.MERGE:
            # Simple merge: combine content
            merged = KnowledgeEntry(
                entry_id=local.entry_id,
                title=local.title,
                content=f"{local.content}\n\n---\n\n{remote.content}",
                category=local.category,
                tags=list(set(local.tags + remote.tags)),
                source_refs=list(set(local.source_refs + remote.source_refs)),
                metadata={**local.metadata, **remote.metadata},
                version=max(local.version, remote.version) + 1,
                source=local.source
            )
            return merged

        else:  # MANUAL
            return None

    def _update_sync_state(
        self,
        source_id: str,
        target_id: str,
        result: SyncResult
    ) -> None:
        """Update sync state after sync operation."""
        key = f"{source_id}:{target_id}"
        self._sync_states[key] = SyncState(
            source=source_id,
            target=target_id,
            last_sync=result.completed_at,
            entries_count=result.entries_synced,
            status=result.status
        )

    def get_sync_state(self, source_id: str, target_id: str) -> Optional[SyncState]:
        """Get sync state between two sources."""
        key = f"{source_id}:{target_id}"
        return self._sync_states.get(key)

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get overall sync status."""
        return {
            "sources": list(self._sources.keys()),
            "sync_states": {
                k: {
                    "source": v.source,
                    "target": v.target,
                    "last_sync": v.last_sync.isoformat() if v.last_sync else None,
                    "status": v.status.value
                }
                for k, v in self._sync_states.items()
            },
            "recent_syncs": [
                r.to_dict() for r in self._sync_history[-10:]
            ]
        }


class KnowledgeSource:
    """
    Abstract base for knowledge sources.

    Each source (local DB, Notion, documents) implements this interface
    to enable sync operations.
    """

    def __init__(self, source_id: str, name: str):
        self.source_id = source_id
        self.name = name

    async def list_entries(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        since: Optional[datetime] = None
    ) -> List[KnowledgeEntry]:
        """List entries from this source."""
        raise NotImplementedError

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a single entry."""
        raise NotImplementedError

    async def create_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Create a new entry."""
        raise NotImplementedError

    async def update_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Update an existing entry."""
        raise NotImplementedError

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry."""
        raise NotImplementedError

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[KnowledgeEntry]:
        """Search entries."""
        raise NotImplementedError


class LocalKnowledgeSource(KnowledgeSource):
    """Knowledge source backed by CKC PostgreSQL database."""

    def __init__(self, db=None):
        super().__init__("local", "CKC Local Database")
        self._db = db
        self._repo = None

    async def _get_repo(self):
        """Get or initialize repository."""
        if self._repo is None:
            from .repositories import KnowledgeEntryRepository
            if self._db is None:
                from .database import get_database
                self._db = await get_database()
            self._repo = KnowledgeEntryRepository(self._db)
        return self._repo

    async def list_entries(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        since: Optional[datetime] = None
    ) -> List[KnowledgeEntry]:
        """List entries from local database."""
        repo = await self._get_repo()
        entries = await repo.list_all(category=category, limit=1000)
        return [self._to_knowledge_entry(e) for e in entries]

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get entry by ID."""
        repo = await self._get_repo()
        entry = await repo.get_by_entry_id(entry_id)
        return self._to_knowledge_entry(entry) if entry else None

    async def create_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Create new entry in database."""
        repo = await self._get_repo()
        created = await repo.create(
            title=entry.title,
            content=entry.content,
            category=entry.category,
            tags=entry.tags,
            source_refs=entry.source_refs,
            metadata={**entry.metadata, "sync_source": entry.source}
        )
        return self._to_knowledge_entry(created)

    async def update_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Update existing entry."""
        repo = await self._get_repo()
        updated = await repo.update(
            entry.entry_id,
            title=entry.title,
            content=entry.content,
            tags=entry.tags,
            source_refs=entry.source_refs,
            metadata=entry.metadata
        )
        return self._to_knowledge_entry(updated)

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete entry."""
        repo = await self._get_repo()
        return await repo.delete(entry_id)

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[KnowledgeEntry]:
        """Search entries."""
        repo = await self._get_repo()
        entries = await repo.search(query, category=category, limit=limit)
        return [self._to_knowledge_entry(e) for e in entries]

    def _to_knowledge_entry(self, entity) -> KnowledgeEntry:
        """Convert database entity to KnowledgeEntry."""
        return KnowledgeEntry(
            entry_id=entity.entry_id,
            title=entity.title,
            content=entity.content,
            category=entity.category,
            tags=entity.tags,
            source_refs=entity.source_refs,
            metadata=entity.metadata,
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            source="local"
        )


class InMemoryKnowledgeSource(KnowledgeSource):
    """In-memory knowledge source for testing."""

    def __init__(self, source_id: str = "memory", name: str = "In-Memory"):
        super().__init__(source_id, name)
        self._entries: Dict[str, KnowledgeEntry] = {}

    async def list_entries(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        since: Optional[datetime] = None
    ) -> List[KnowledgeEntry]:
        entries = list(self._entries.values())
        if category:
            entries = [e for e in entries if e.category == category]
        if tags:
            entries = [e for e in entries if any(t in e.tags for t in tags)]
        if since:
            entries = [e for e in entries if e.updated_at and e.updated_at > since]
        return entries

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        return self._entries.get(entry_id)

    async def create_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        self._entries[entry.entry_id] = entry
        return entry

    async def update_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        if entry.entry_id in self._entries:
            entry.updated_at = datetime.utcnow()
            self._entries[entry.entry_id] = entry
        return entry

    async def delete_entry(self, entry_id: str) -> bool:
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[KnowledgeEntry]:
        query_lower = query.lower()
        results = []
        for entry in self._entries.values():
            if query_lower in entry.title.lower() or query_lower in entry.content.lower():
                if not category or entry.category == category:
                    results.append(entry)
        return results[:limit]


# Singleton instance
_sync_manager: Optional[KnowledgeSyncManager] = None


async def get_sync_manager() -> KnowledgeSyncManager:
    """Get or create singleton sync manager."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = KnowledgeSyncManager()
        # Register local source by default
        _sync_manager.register_source(LocalKnowledgeSource())
    return _sync_manager


async def close_sync_manager() -> None:
    """Close singleton sync manager."""
    global _sync_manager
    _sync_manager = None
