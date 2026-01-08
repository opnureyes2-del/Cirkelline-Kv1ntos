"""
Test suite for CKC Knowledge Sync and Interface
================================================

Tests knowledge entry management, sync operations, and unified interface.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_knowledge_entry():
    """Test KnowledgeEntry dataclass."""
    print("=== Test 1: KnowledgeEntry ===")

    from cirkelline.ckc.infrastructure.knowledge_sync import KnowledgeEntry

    # Create entry
    entry = KnowledgeEntry(
        entry_id="kb_test001",
        title="Python Best Practices",
        content="Always use virtual environments and type hints.",
        category="programming",
        tags=["python", "best-practices"],
        source_refs=["https://python.org"]
    )

    assert entry.entry_id == "kb_test001"
    assert entry.category == "programming"
    assert "python" in entry.tags
    assert entry.version == 1
    assert entry.content_hash != ""
    print("  - Entry creation: OK")

    # Test to_dict/from_dict
    entry_dict = entry.to_dict()
    restored = KnowledgeEntry.from_dict(entry_dict)
    assert restored.entry_id == entry.entry_id
    assert restored.title == entry.title
    print("  - Serialization: OK")

    # Test has_changed
    entry2 = KnowledgeEntry(
        entry_id="kb_test001",
        title="Python Best Practices UPDATED",
        content="Always use virtual environments and type hints.",
        category="programming",
        tags=["python", "best-practices"]
    )
    assert entry.has_changed(entry2)
    print("  - Change detection: OK")

    print("  All KnowledgeEntry tests OK!")
    return True


async def test_in_memory_source():
    """Test InMemoryKnowledgeSource."""
    print("\n=== Test 2: InMemoryKnowledgeSource ===")

    from cirkelline.ckc.infrastructure.knowledge_sync import (
        KnowledgeEntry,
        InMemoryKnowledgeSource,
    )

    source = InMemoryKnowledgeSource("test_memory", "Test Memory")
    assert source.source_id == "test_memory"
    print("  - Source creation: OK")

    # Create entries
    entry1 = KnowledgeEntry(
        entry_id="kb_001",
        title="Python Basics",
        content="Python is a programming language.",
        category="programming",
        tags=["python", "basics"]
    )
    entry2 = KnowledgeEntry(
        entry_id="kb_002",
        title="JavaScript Basics",
        content="JavaScript runs in browsers.",
        category="programming",
        tags=["javascript", "basics"]
    )

    await source.create_entry(entry1)
    await source.create_entry(entry2)
    print("  - Create entries: OK")

    # List entries
    entries = await source.list_entries()
    assert len(entries) == 2
    print("  - List entries: OK")

    # Get entry
    retrieved = await source.get_entry("kb_001")
    assert retrieved.title == "Python Basics"
    print("  - Get entry: OK")

    # Search
    results = await source.search("Python")
    assert len(results) >= 1
    assert any(e.entry_id == "kb_001" for e in results)
    print("  - Search: OK")

    # Update
    entry1.content = "Python is an awesome programming language."
    updated = await source.update_entry(entry1)
    assert "awesome" in updated.content
    print("  - Update entry: OK")

    # Delete
    deleted = await source.delete_entry("kb_002")
    assert deleted is True
    entries_after = await source.list_entries()
    assert len(entries_after) == 1
    print("  - Delete entry: OK")

    print("  All InMemoryKnowledgeSource tests OK!")
    return True


async def test_sync_manager():
    """Test KnowledgeSyncManager."""
    print("\n=== Test 3: KnowledgeSyncManager ===")

    from cirkelline.ckc.infrastructure.knowledge_sync import (
        KnowledgeEntry,
        KnowledgeSyncManager,
        InMemoryKnowledgeSource,
        SyncDirection,
        SyncStatus,
    )

    manager = KnowledgeSyncManager()
    print("  - Manager creation: OK")

    # Register sources
    source1 = InMemoryKnowledgeSource("source1", "Source 1")
    source2 = InMemoryKnowledgeSource("source2", "Source 2")
    manager.register_source(source1)
    manager.register_source(source2)

    assert len(manager.list_sources()) == 2
    print("  - Register sources: OK")

    # Add entries to source1
    await source1.create_entry(KnowledgeEntry(
        entry_id="kb_shared_001",
        title="Shared Knowledge",
        content="This should sync to source2.",
        category="general",
        tags=["shared"]
    ))
    await source1.create_entry(KnowledgeEntry(
        entry_id="kb_only_s1",
        title="Source 1 Only",
        content="This is only in source 1.",
        category="specific",
        tags=["source1"]
    ))

    # Sync push
    result = await manager.sync("source1", "source2", SyncDirection.PUSH)
    assert result.status in (SyncStatus.COMPLETED, SyncStatus.PARTIAL)
    assert result.entries_created >= 2
    print(f"  - Sync push: OK (created {result.entries_created})")

    # Verify sync
    s2_entries = await source2.list_entries()
    assert len(s2_entries) == 2
    print("  - Sync verification: OK")

    # Get sync status
    status = await manager.get_sync_status()
    assert "source1" in status["sources"]
    assert "source2" in status["sources"]
    print("  - Sync status: OK")

    print("  All KnowledgeSyncManager tests OK!")
    return True


async def test_knowledge_interface():
    """Test unified knowledge interface."""
    print("\n=== Test 4: Knowledge Interface ===")

    from cirkelline.ckc.infrastructure.knowledge_sync import (
        InMemoryKnowledgeSource,
        close_sync_manager,
    )
    from cirkelline.ckc.infrastructure import knowledge_interface as ki

    # Reset sync manager for clean test
    await close_sync_manager()

    # Register a test source
    test_source = InMemoryKnowledgeSource("test", "Test Source")
    await ki.register_source(test_source)

    sources = await ki.list_sources()
    assert "test" in sources
    print("  - Register source: OK")

    # Create entry via interface
    entry = await ki.create_entry(
        title="Interface Test Entry",
        content="Created via unified interface.",
        category="test",
        tags=["interface", "test"],
        target="test"
    )
    assert entry.entry_id.startswith("kb_")
    print("  - Create entry: OK")

    # Get entry
    retrieved = await ki.get_entry(entry.entry_id, source="test")
    assert retrieved.title == "Interface Test Entry"
    print("  - Get entry: OK")

    # Search
    results = await ki.search_knowledge("Interface", sources=["test"])
    assert len(results) >= 1
    print("  - Search: OK")

    # Update entry
    updated = await ki.update_entry(
        entry.entry_id,
        content="Updated via unified interface.",
        target="test"
    )
    assert "Updated" in updated.content
    print("  - Update entry: OK")

    # List entries
    entries = await ki.list_entries(source="test")
    assert len(entries) >= 1
    print("  - List entries: OK")

    # Delete entry
    deleted = await ki.delete_entry(entry.entry_id, target="test")
    assert deleted is True
    print("  - Delete entry: OK")

    # Clean up
    await ki.unregister_source("test")

    print("  All Knowledge Interface tests OK!")
    return True


async def test_conflict_resolution():
    """Test conflict resolution during sync."""
    print("\n=== Test 5: Conflict Resolution ===")

    from cirkelline.ckc.infrastructure.knowledge_sync import (
        KnowledgeEntry,
        KnowledgeSyncManager,
        InMemoryKnowledgeSource,
        SyncDirection,
        ConflictResolution,
    )
    from datetime import datetime, timedelta

    manager = KnowledgeSyncManager()

    source1 = InMemoryKnowledgeSource("conflict_s1", "Conflict Source 1")
    source2 = InMemoryKnowledgeSource("conflict_s2", "Conflict Source 2")
    manager.register_source(source1)
    manager.register_source(source2)

    # Create same entry in both sources with different content
    now = datetime.utcnow()
    older = now - timedelta(hours=1)

    entry1 = KnowledgeEntry(
        entry_id="kb_conflict",
        title="Conflicting Entry",
        content="Source 1 version",
        category="test",
        version=1,
        updated_at=older  # Older
    )
    entry2 = KnowledgeEntry(
        entry_id="kb_conflict",
        title="Conflicting Entry",
        content="Source 2 version",
        category="test",
        version=2,
        updated_at=now  # Newer
    )

    await source1.create_entry(entry1)
    await source2.create_entry(entry2)

    # Sync with NEWEST_WINS
    result = await manager.sync(
        "conflict_s1", "conflict_s2",
        SyncDirection.PUSH,
        ConflictResolution.NEWEST_WINS
    )

    # Source 2 should keep its newer version
    s2_entry = await source2.get_entry("kb_conflict")
    assert s2_entry.content == "Source 2 version"
    print("  - NEWEST_WINS resolution: OK")

    # Test LOCAL_WINS
    source3 = InMemoryKnowledgeSource("conflict_s3", "Conflict Source 3")
    manager.register_source(source3)

    entry3 = KnowledgeEntry(
        entry_id="kb_conflict2",
        title="Another Conflict",
        content="Source 1 local",
        category="test"
    )
    entry4 = KnowledgeEntry(
        entry_id="kb_conflict2",
        title="Another Conflict",
        content="Source 3 remote",
        category="test"
    )

    await source1.create_entry(entry3)
    await source3.create_entry(entry4)

    result = await manager.sync(
        "conflict_s1", "conflict_s3",
        SyncDirection.PUSH,
        ConflictResolution.LOCAL_WINS
    )

    s3_entry = await source3.get_entry("kb_conflict2")
    assert s3_entry.content == "Source 1 local"
    print("  - LOCAL_WINS resolution: OK")

    print("  All Conflict Resolution tests OK!")
    return True


async def test_bulk_operations():
    """Test bulk operations."""
    print("\n=== Test 6: Bulk Operations ===")

    from cirkelline.ckc.infrastructure.knowledge_sync import (
        InMemoryKnowledgeSource,
        close_sync_manager,
    )
    from cirkelline.ckc.infrastructure import knowledge_interface as ki

    # Reset
    await close_sync_manager()

    test_source = InMemoryKnowledgeSource("bulk", "Bulk Test")
    await ki.register_source(test_source)

    # Bulk create
    entries_data = [
        {"title": f"Bulk Entry {i}", "content": f"Content {i}", "category": "bulk"}
        for i in range(5)
    ]
    created = await ki.bulk_create(entries_data, target="bulk")
    assert len(created) == 5
    print("  - Bulk create: OK")

    # Export
    exported = await ki.export_entries(source="bulk")
    assert len(exported) == 5
    print("  - Export entries: OK")

    # Bulk delete
    entry_ids = [e.entry_id for e in created]
    delete_results = await ki.bulk_delete(entry_ids, target="bulk")
    assert all(delete_results.values())
    print("  - Bulk delete: OK")

    # Import
    import_results = await ki.import_entries(exported, target="bulk")
    assert import_results["created"] == 5
    print("  - Import entries: OK")

    await ki.unregister_source("bulk")

    print("  All Bulk Operations tests OK!")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("CKC Knowledge Sync & Interface Test Suite")
    print("=" * 60)

    tests = [
        test_knowledge_entry,
        test_in_memory_source,
        test_sync_manager,
        test_knowledge_interface,
        test_conflict_resolution,
        test_bulk_operations,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
