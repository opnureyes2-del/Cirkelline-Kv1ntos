"""
CKC Unified Knowledge Interface
===============================

Provides a standardized interface for all knowledge operations across sources.
This is the primary API for agents and other components to access knowledge.

Usage:
    from cirkelline.ckc.infrastructure.knowledge_interface import (
        search_knowledge,
        get_entry,
        create_entry,
        update_entry,
    )

    # Search across all sources
    results = await search_knowledge("Python programming", sources=["local", "notion"])

    # Get specific entry
    entry = await get_entry("kb_123", source="local")
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .knowledge_sync import (
    KnowledgeEntry,
    KnowledgeSyncManager,
    KnowledgeSource,
    LocalKnowledgeSource,
    InMemoryKnowledgeSource,
    SyncDirection,
    ConflictResolution,
    SyncResult,
    get_sync_manager,
)

logger = logging.getLogger(__name__)


# ========== Unified Search ==========

async def search_knowledge(
    query: str,
    sources: Optional[List[str]] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50
) -> List[KnowledgeEntry]:
    """
    Search for knowledge entries across multiple sources.

    Args:
        query: Search query string
        sources: List of source IDs to search (default: all registered sources)
        category: Filter by category
        tags: Filter by tags
        limit: Maximum results per source

    Returns:
        Combined list of matching entries from all sources
    """
    manager = await get_sync_manager()
    source_ids = sources or manager.list_sources()

    all_results = []
    for source_id in source_ids:
        source = manager.get_source(source_id)
        if source:
            try:
                results = await source.search(query, category=category, limit=limit)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Search failed for source {source_id}: {e}")

    # Sort by relevance (simple: title match first, then content)
    query_lower = query.lower()
    all_results.sort(
        key=lambda e: (
            0 if query_lower in e.title.lower() else 1,
            e.updated_at or e.created_at or datetime.min
        ),
        reverse=True
    )

    return all_results[:limit]


async def get_entry(
    entry_id: str,
    source: str = "local"
) -> Optional[KnowledgeEntry]:
    """
    Get a specific knowledge entry.

    Args:
        entry_id: Entry ID
        source: Source ID

    Returns:
        KnowledgeEntry if found, None otherwise
    """
    manager = await get_sync_manager()
    source_obj = manager.get_source(source)
    if source_obj:
        return await source_obj.get_entry(entry_id)
    return None


async def get_entry_by_title(
    title: str,
    source: str = "local",
    exact: bool = False
) -> Optional[KnowledgeEntry]:
    """
    Get a knowledge entry by title.

    Args:
        title: Entry title
        source: Source ID
        exact: If True, require exact match

    Returns:
        First matching KnowledgeEntry
    """
    results = await search_knowledge(title, sources=[source], limit=10)
    for entry in results:
        if exact:
            if entry.title == title:
                return entry
        else:
            if title.lower() in entry.title.lower():
                return entry
    return None


async def list_entries(
    source: str = "local",
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 100
) -> List[KnowledgeEntry]:
    """
    List knowledge entries from a source.

    Args:
        source: Source ID
        category: Filter by category
        tags: Filter by tags
        limit: Maximum entries

    Returns:
        List of entries
    """
    manager = await get_sync_manager()
    source_obj = manager.get_source(source)
    if source_obj:
        return await source_obj.list_entries(category=category, tags=tags)
    return []


# ========== CRUD Operations ==========

async def create_entry(
    title: str,
    content: str,
    category: str,
    tags: Optional[List[str]] = None,
    source_refs: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    target: str = "local"
) -> KnowledgeEntry:
    """
    Create a new knowledge entry.

    Args:
        title: Entry title
        content: Entry content
        category: Category
        tags: Tags for indexing
        source_refs: Reference links
        metadata: Additional metadata
        target: Target source ID

    Returns:
        Created KnowledgeEntry
    """
    import uuid

    entry = KnowledgeEntry(
        entry_id=f"kb_{uuid.uuid4().hex[:12]}",
        title=title,
        content=content,
        category=category,
        tags=tags or [],
        source_refs=source_refs or [],
        metadata=metadata or {},
        source=target
    )

    manager = await get_sync_manager()
    source = manager.get_source(target)
    if source:
        return await source.create_entry(entry)
    else:
        raise ValueError(f"Unknown target source: {target}")


async def update_entry(
    entry_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    source_refs: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    target: str = "local"
) -> Optional[KnowledgeEntry]:
    """
    Update an existing knowledge entry.

    Args:
        entry_id: Entry ID to update
        title: New title (optional)
        content: New content (optional)
        category: New category (optional)
        tags: New tags (optional)
        source_refs: New references (optional)
        metadata: New metadata (optional)
        target: Target source ID

    Returns:
        Updated KnowledgeEntry or None if not found
    """
    manager = await get_sync_manager()
    source = manager.get_source(target)
    if not source:
        raise ValueError(f"Unknown target source: {target}")

    existing = await source.get_entry(entry_id)
    if not existing:
        return None

    # Update fields
    if title is not None:
        existing.title = title
    if content is not None:
        existing.content = content
    if category is not None:
        existing.category = category
    if tags is not None:
        existing.tags = tags
    if source_refs is not None:
        existing.source_refs = source_refs
    if metadata is not None:
        existing.metadata.update(metadata)

    existing.version += 1
    existing.updated_at = datetime.utcnow()
    existing.content_hash = existing._compute_hash()

    return await source.update_entry(existing)


async def delete_entry(
    entry_id: str,
    target: str = "local"
) -> bool:
    """
    Delete a knowledge entry.

    Args:
        entry_id: Entry ID to delete
        target: Target source ID

    Returns:
        True if deleted, False otherwise
    """
    manager = await get_sync_manager()
    source = manager.get_source(target)
    if source:
        return await source.delete_entry(entry_id)
    return False


# ========== Sync Operations ==========

async def sync_sources(
    source_id: str,
    target_id: str,
    direction: str = "bidirectional",
    conflict_resolution: str = "newest_wins"
) -> SyncResult:
    """
    Sync between two knowledge sources.

    Args:
        source_id: Source ID
        target_id: Target ID
        direction: "push", "pull", or "bidirectional"
        conflict_resolution: "local_wins", "remote_wins", "newest_wins", "merge", "manual"

    Returns:
        SyncResult with details
    """
    direction_enum = SyncDirection(direction)
    resolution_enum = ConflictResolution(conflict_resolution)

    manager = await get_sync_manager()
    return await manager.sync(source_id, target_id, direction_enum, resolution_enum)


async def register_source(source: KnowledgeSource) -> None:
    """Register a new knowledge source."""
    manager = await get_sync_manager()
    manager.register_source(source)


async def unregister_source(source_id: str) -> None:
    """Unregister a knowledge source."""
    manager = await get_sync_manager()
    manager.unregister_source(source_id)


async def list_sources() -> List[str]:
    """List all registered knowledge sources."""
    manager = await get_sync_manager()
    return manager.list_sources()


async def get_sync_status() -> Dict[str, Any]:
    """Get current sync status."""
    manager = await get_sync_manager()
    return await manager.get_sync_status()


# ========== Category & Tag Operations ==========

async def list_categories(source: str = "local") -> List[str]:
    """
    List all unique categories in a source.

    Args:
        source: Source ID

    Returns:
        List of category names
    """
    entries = await list_entries(source=source, limit=10000)
    categories = set(e.category for e in entries)
    return sorted(categories)


async def list_tags(source: str = "local") -> List[str]:
    """
    List all unique tags in a source.

    Args:
        source: Source ID

    Returns:
        List of tag names
    """
    entries = await list_entries(source=source, limit=10000)
    tags = set()
    for entry in entries:
        tags.update(entry.tags)
    return sorted(tags)


async def get_entries_by_category(
    category: str,
    source: str = "local",
    limit: int = 100
) -> List[KnowledgeEntry]:
    """Get all entries in a category."""
    return await list_entries(source=source, category=category, limit=limit)


async def get_entries_by_tag(
    tag: str,
    source: str = "local",
    limit: int = 100
) -> List[KnowledgeEntry]:
    """Get all entries with a specific tag."""
    return await list_entries(source=source, tags=[tag], limit=limit)


# ========== Bulk Operations ==========

async def bulk_create(
    entries: List[Dict[str, Any]],
    target: str = "local"
) -> List[KnowledgeEntry]:
    """
    Create multiple knowledge entries.

    Args:
        entries: List of entry dictionaries
        target: Target source ID

    Returns:
        List of created entries
    """
    created = []
    for entry_data in entries:
        entry = await create_entry(
            title=entry_data["title"],
            content=entry_data["content"],
            category=entry_data.get("category", "general"),
            tags=entry_data.get("tags"),
            source_refs=entry_data.get("source_refs"),
            metadata=entry_data.get("metadata"),
            target=target
        )
        created.append(entry)
    return created


async def bulk_delete(
    entry_ids: List[str],
    target: str = "local"
) -> Dict[str, bool]:
    """
    Delete multiple knowledge entries.

    Args:
        entry_ids: List of entry IDs to delete
        target: Target source ID

    Returns:
        Dict mapping entry_id to success status
    """
    results = {}
    for entry_id in entry_ids:
        results[entry_id] = await delete_entry(entry_id, target)
    return results


# ========== Export/Import ==========

async def export_entries(
    source: str = "local",
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Export entries as dictionaries.

    Args:
        source: Source ID
        category: Optional category filter

    Returns:
        List of entry dictionaries
    """
    entries = await list_entries(source=source, category=category, limit=10000)
    return [e.to_dict() for e in entries]


async def import_entries(
    entries: List[Dict[str, Any]],
    target: str = "local",
    overwrite: bool = False
) -> Dict[str, int]:
    """
    Import entries from dictionaries.

    Args:
        entries: List of entry dictionaries
        target: Target source ID
        overwrite: If True, overwrite existing entries

    Returns:
        Dict with counts of created, updated, skipped
    """
    manager = await get_sync_manager()
    source = manager.get_source(target)
    if not source:
        raise ValueError(f"Unknown target source: {target}")

    counts = {"created": 0, "updated": 0, "skipped": 0}

    for entry_data in entries:
        entry = KnowledgeEntry.from_dict(entry_data)
        existing = await source.get_entry(entry.entry_id)

        if existing:
            if overwrite:
                await source.update_entry(entry)
                counts["updated"] += 1
            else:
                counts["skipped"] += 1
        else:
            await source.create_entry(entry)
            counts["created"] += 1

    return counts
