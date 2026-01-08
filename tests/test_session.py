"""
CKC MASTERMIND Session Management Tests
========================================

Komplet test suite for Session modulet:
- SessionCheckpoint
- SessionStore (Abstract)
- FileSessionStore
- InMemorySessionStore
- SessionManager
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from cirkelline.ckc.mastermind.session import (
    # Data classes
    SessionCheckpoint,

    # Store classes
    SessionStore,
    FileSessionStore,
    InMemorySessionStore,

    # Main class
    SessionManager,

    # Factory functions
    create_session_manager,
    get_session_manager,
)

from cirkelline.ckc.mastermind.coordinator import (
    MastermindSession,
    MastermindStatus,
    MastermindPriority,
    MastermindTask,
    TaskStatus,
)


# =============================================================================
# TEST SESSION CHECKPOINT
# =============================================================================

class TestSessionCheckpoint:
    """Tests for SessionCheckpoint dataclass."""

    def test_checkpoint_creation(self):
        """Test creating a SessionCheckpoint."""
        checkpoint = SessionCheckpoint(
            checkpoint_id="cp_test123",
            session_id="mm_session456",
            label="Test checkpoint"
        )
        assert checkpoint.checkpoint_id == "cp_test123"
        assert checkpoint.session_id == "mm_session456"
        assert checkpoint.label == "Test checkpoint"
        assert checkpoint.is_auto is False
        assert isinstance(checkpoint.created_at, datetime)

    def test_checkpoint_with_snapshots(self):
        """Test checkpoint with state snapshots."""
        checkpoint = SessionCheckpoint(
            checkpoint_id="cp_snap001",
            session_id="mm_snap",
            state_snapshot={"status": "active", "budget": 100.0},
            tasks_snapshot={"task_1": {"title": "Test task"}},
            context_snapshot={"key": "value"}
        )
        assert checkpoint.state_snapshot["status"] == "active"
        assert checkpoint.tasks_snapshot["task_1"]["title"] == "Test task"
        assert checkpoint.context_snapshot["key"] == "value"

    def test_checkpoint_to_dict(self):
        """Test checkpoint serialization to dict."""
        checkpoint = SessionCheckpoint(
            checkpoint_id="cp_dict001",
            session_id="mm_dict",
            label="Serialization test",
            is_auto=True
        )
        data = checkpoint.to_dict()

        assert data["checkpoint_id"] == "cp_dict001"
        assert data["session_id"] == "mm_dict"
        assert data["label"] == "Serialization test"
        assert data["is_auto"] is True
        assert "created_at" in data
        assert isinstance(data["created_at"], str)  # ISO format

    def test_checkpoint_from_dict(self):
        """Test checkpoint deserialization from dict."""
        data = {
            "checkpoint_id": "cp_from001",
            "session_id": "mm_from",
            "created_at": "2025-12-11T12:00:00",
            "label": "From dict test",
            "state_snapshot": {"key": "value"},
            "tasks_snapshot": {},
            "context_snapshot": {},
            "is_auto": False
        }
        checkpoint = SessionCheckpoint.from_dict(data)

        assert checkpoint.checkpoint_id == "cp_from001"
        assert checkpoint.session_id == "mm_from"
        assert checkpoint.label == "From dict test"
        assert checkpoint.state_snapshot["key"] == "value"

    def test_checkpoint_roundtrip(self):
        """Test checkpoint serialization roundtrip."""
        original = SessionCheckpoint(
            checkpoint_id="cp_round001",
            session_id="mm_round",
            label="Roundtrip test",
            state_snapshot={"test": 123},
            is_auto=True
        )
        data = original.to_dict()
        restored = SessionCheckpoint.from_dict(data)

        assert restored.checkpoint_id == original.checkpoint_id
        assert restored.session_id == original.session_id
        assert restored.label == original.label
        assert restored.is_auto == original.is_auto
        assert restored.state_snapshot == original.state_snapshot


# =============================================================================
# TEST IN-MEMORY SESSION STORE
# =============================================================================

class TestInMemorySessionStore:
    """Tests for InMemorySessionStore."""

    @pytest.fixture
    def store(self):
        """Create fresh InMemorySessionStore."""
        return InMemorySessionStore()

    @pytest.fixture
    def sample_session(self):
        """Create a sample session."""
        return MastermindSession(
            session_id="mm_test123",
            status=MastermindStatus.ACTIVE,
            primary_objective="Test objective",
            budget_usd=100.0
        )

    @pytest.mark.asyncio
    async def test_save_session(self, store, sample_session):
        """Test saving a session."""
        result = await store.save(sample_session)
        assert result is True
        assert sample_session.session_id in store._sessions

    @pytest.mark.asyncio
    async def test_load_session(self, store, sample_session):
        """Test loading a session."""
        await store.save(sample_session)
        loaded = await store.load(sample_session.session_id)

        assert loaded is not None
        assert loaded.session_id == sample_session.session_id
        assert loaded.primary_objective == sample_session.primary_objective

    @pytest.mark.asyncio
    async def test_load_nonexistent_session(self, store):
        """Test loading non-existent session returns None."""
        loaded = await store.load("nonexistent_session")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_session(self, store, sample_session):
        """Test deleting a session."""
        await store.save(sample_session)
        result = await store.delete(sample_session.session_id)

        assert result is True
        assert sample_session.session_id not in store._sessions

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, store):
        """Test deleting non-existent session returns False."""
        result = await store.delete("nonexistent_session")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_sessions(self, store):
        """Test listing sessions."""
        # Create multiple sessions
        for i in range(5):
            session = MastermindSession(
                session_id=f"mm_list{i}",
                status=MastermindStatus.ACTIVE if i % 2 == 0 else MastermindStatus.COMPLETED,
                primary_objective=f"Objective {i}"
            )
            await store.save(session)

        all_sessions = await store.list_sessions()
        assert len(all_sessions) == 5

    @pytest.mark.asyncio
    async def test_list_sessions_with_status_filter(self, store):
        """Test listing sessions filtered by status."""
        for i in range(4):
            session = MastermindSession(
                session_id=f"mm_filter{i}",
                status=MastermindStatus.ACTIVE if i < 2 else MastermindStatus.COMPLETED,
                primary_objective=f"Objective {i}"
            )
            await store.save(session)

        active_sessions = await store.list_sessions(status=MastermindStatus.ACTIVE)
        assert len(active_sessions) == 2

    @pytest.mark.asyncio
    async def test_list_sessions_with_limit(self, store):
        """Test listing sessions with limit."""
        for i in range(10):
            session = MastermindSession(
                session_id=f"mm_limit{i}",
                status=MastermindStatus.ACTIVE,
                primary_objective=f"Objective {i}"
            )
            await store.save(session)

        limited = await store.list_sessions(limit=5)
        assert len(limited) == 5

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, store):
        """Test saving a checkpoint."""
        checkpoint = SessionCheckpoint(
            checkpoint_id="cp_save001",
            session_id="mm_cp",
            label="Save test"
        )
        result = await store.save_checkpoint(checkpoint)

        assert result is True
        assert "cp_save001" in store._checkpoints

    @pytest.mark.asyncio
    async def test_load_checkpoint(self, store):
        """Test loading a checkpoint."""
        checkpoint = SessionCheckpoint(
            checkpoint_id="cp_load001",
            session_id="mm_cp",
            label="Load test"
        )
        await store.save_checkpoint(checkpoint)

        loaded = await store.load_checkpoint("cp_load001")
        assert loaded is not None
        assert loaded.checkpoint_id == "cp_load001"
        assert loaded.label == "Load test"

    @pytest.mark.asyncio
    async def test_load_nonexistent_checkpoint(self, store):
        """Test loading non-existent checkpoint returns None."""
        loaded = await store.load_checkpoint("nonexistent_cp")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, store):
        """Test listing checkpoints for a session."""
        session_id = "mm_cplist"

        for i in range(3):
            cp = SessionCheckpoint(
                checkpoint_id=f"cp_list{i}",
                session_id=session_id,
                label=f"Checkpoint {i}"
            )
            await store.save_checkpoint(cp)

        # Add checkpoint for different session
        other_cp = SessionCheckpoint(
            checkpoint_id="cp_other",
            session_id="mm_other",
            label="Other session"
        )
        await store.save_checkpoint(other_cp)

        checkpoints = await store.list_checkpoints(session_id)
        assert len(checkpoints) == 3


# =============================================================================
# TEST FILE SESSION STORE
# =============================================================================

class TestFileSessionStore:
    """Tests for FileSessionStore."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def store(self, temp_dir):
        """Create FileSessionStore with temp directory."""
        return FileSessionStore(base_path=temp_dir)

    @pytest.fixture
    def sample_session(self):
        """Create a sample session."""
        return MastermindSession(
            session_id="mm_file001",
            status=MastermindStatus.ACTIVE,
            primary_objective="File store test",
            budget_usd=50.0
        )

    def test_store_initialization(self, store, temp_dir):
        """Test FileSessionStore creates directories."""
        assert store.sessions_path.exists()
        assert store.checkpoints_path.exists()

    @pytest.mark.asyncio
    async def test_save_and_load_session(self, store, sample_session):
        """Test saving and loading session to/from file."""
        await store.save(sample_session)

        # Check file exists
        filepath = store.sessions_path / f"{sample_session.session_id}.json"
        assert filepath.exists()

        # Load and verify
        loaded = await store.load(sample_session.session_id)
        assert loaded is not None
        assert loaded.session_id == sample_session.session_id

    @pytest.mark.asyncio
    async def test_delete_session_file(self, store, sample_session):
        """Test deleting session removes file."""
        await store.save(sample_session)
        filepath = store.sessions_path / f"{sample_session.session_id}.json"
        assert filepath.exists()

        result = await store.delete(sample_session.session_id)
        assert result is True
        assert not filepath.exists()

    @pytest.mark.asyncio
    async def test_list_sessions_from_files(self, store):
        """Test listing sessions from files."""
        for i in range(3):
            session = MastermindSession(
                session_id=f"mm_filelist{i}",
                status=MastermindStatus.ACTIVE,
                primary_objective=f"Objective {i}"
            )
            await store.save(session)

        sessions = await store.list_sessions()
        assert len(sessions) == 3

    @pytest.mark.asyncio
    async def test_checkpoint_file_operations(self, store):
        """Test checkpoint save/load with files."""
        checkpoint = SessionCheckpoint(
            checkpoint_id="cp_file001",
            session_id="mm_cpfile",
            label="File checkpoint test",
            state_snapshot={"test": "data"}
        )

        await store.save_checkpoint(checkpoint)
        filepath = store.checkpoints_path / f"{checkpoint.checkpoint_id}.json"
        assert filepath.exists()

        loaded = await store.load_checkpoint("cp_file001")
        assert loaded is not None
        assert loaded.label == "File checkpoint test"


# =============================================================================
# TEST SESSION MANAGER
# =============================================================================

class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.fixture
    def manager(self):
        """Create SessionManager with InMemoryStore."""
        return SessionManager(
            store=InMemorySessionStore(),
            auto_save=True,
            auto_checkpoint_interval_tasks=3
        )

    @pytest.fixture
    def sample_session(self):
        """Create a sample session with tasks."""
        session = MastermindSession(
            session_id="mm_mgr001",
            status=MastermindStatus.ACTIVE,
            primary_objective="Manager test",
            budget_usd=100.0
        )
        # Add some tasks
        for i in range(5):
            task = MastermindTask(
                task_id=f"task_{i}",
                title=f"Task {i}",
                description=f"Description {i}",
                status=TaskStatus.PENDING
            )
            session.tasks[task.task_id] = task
            session.task_queue.append(task.task_id)

        return session

    @pytest.mark.asyncio
    async def test_save_and_load_session(self, manager, sample_session):
        """Test saving and loading through manager."""
        await manager.save_session(sample_session)
        loaded = await manager.load_session(sample_session.session_id)

        assert loaded is not None
        assert loaded.session_id == sample_session.session_id

    @pytest.mark.asyncio
    async def test_delete_session(self, manager, sample_session):
        """Test deleting through manager."""
        await manager.save_session(sample_session)
        result = await manager.delete_session(sample_session.session_id)

        assert result is True
        loaded = await manager.load_session(sample_session.session_id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_list_sessions(self, manager):
        """Test listing sessions through manager."""
        for i in range(3):
            session = MastermindSession(
                session_id=f"mm_mgrlist{i}",
                status=MastermindStatus.ACTIVE,
                primary_objective=f"Objective {i}"
            )
            await manager.save_session(session)

        sessions = await manager.list_sessions()
        assert len(sessions) == 3

    @pytest.mark.asyncio
    async def test_create_checkpoint(self, manager, sample_session):
        """Test creating a checkpoint."""
        await manager.save_session(sample_session)

        checkpoint = await manager.create_checkpoint(
            sample_session,
            label="Manual checkpoint"
        )

        assert checkpoint is not None
        assert checkpoint.session_id == sample_session.session_id
        assert checkpoint.label == "Manual checkpoint"
        assert checkpoint.is_auto is False

    @pytest.mark.asyncio
    async def test_create_auto_checkpoint(self, manager, sample_session):
        """Test creating an auto checkpoint."""
        await manager.save_session(sample_session)

        checkpoint = await manager.create_checkpoint(
            sample_session,
            label="Auto checkpoint",
            is_auto=True
        )

        assert checkpoint.is_auto is True

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, manager, sample_session):
        """Test listing checkpoints for a session."""
        await manager.save_session(sample_session)

        for i in range(3):
            await manager.create_checkpoint(
                sample_session,
                label=f"Checkpoint {i}"
            )

        checkpoints = await manager.list_checkpoints(sample_session.session_id)
        assert len(checkpoints) == 3

    @pytest.mark.asyncio
    async def test_rollback_to_checkpoint(self, manager, sample_session):
        """Test rolling back to a checkpoint."""
        await manager.save_session(sample_session)

        # Create checkpoint
        checkpoint = await manager.create_checkpoint(
            sample_session,
            label="Before changes"
        )

        # Modify session
        sample_session.status = MastermindStatus.PAUSED
        sample_session.consumed_usd = 50.0
        await manager.save_session(sample_session)

        # Rollback
        result = await manager.rollback_to_checkpoint(
            sample_session,
            checkpoint.checkpoint_id
        )

        assert result is True
        assert sample_session.status == MastermindStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_rollback_to_invalid_checkpoint(self, manager, sample_session):
        """Test rollback with invalid checkpoint raises error."""
        await manager.save_session(sample_session)

        with pytest.raises(ValueError):
            await manager.rollback_to_checkpoint(
                sample_session,
                "nonexistent_checkpoint"
            )

    @pytest.mark.asyncio
    async def test_rollback_to_wrong_session_checkpoint(self, manager, sample_session):
        """Test rollback to checkpoint from different session raises error."""
        await manager.save_session(sample_session)

        # Create checkpoint for different session
        other_session = MastermindSession(
            session_id="mm_other",
            status=MastermindStatus.ACTIVE,
            primary_objective="Other"
        )
        await manager.save_session(other_session)
        other_cp = await manager.create_checkpoint(other_session, "Other checkpoint")

        with pytest.raises(ValueError):
            await manager.rollback_to_checkpoint(sample_session, other_cp.checkpoint_id)

    @pytest.mark.asyncio
    async def test_maybe_auto_checkpoint(self, manager, sample_session):
        """Test auto checkpoint creation based on task count."""
        await manager.save_session(sample_session)

        # Should not create (under threshold)
        cp1 = await manager.maybe_auto_checkpoint(sample_session, 2)
        assert cp1 is None

        # Should create (at threshold)
        cp2 = await manager.maybe_auto_checkpoint(sample_session, 3)
        assert cp2 is not None
        assert cp2.is_auto is True

        # Should not create again (not crossing new threshold)
        cp3 = await manager.maybe_auto_checkpoint(sample_session, 4)
        assert cp3 is None

        # Should create (crossing next threshold)
        cp4 = await manager.maybe_auto_checkpoint(sample_session, 6)
        assert cp4 is not None

    @pytest.mark.asyncio
    async def test_clone_session(self, manager, sample_session):
        """Test cloning a session."""
        await manager.save_session(sample_session)

        cloned = await manager.clone_session(sample_session)

        assert cloned.session_id != sample_session.session_id
        assert cloned.primary_objective == sample_session.primary_objective
        assert cloned.status == MastermindStatus.INITIALIZING
        assert cloned.consumed_usd == 0.0
        assert "cloned" in cloned.tags

    @pytest.mark.asyncio
    async def test_clone_session_with_new_objective(self, manager, sample_session):
        """Test cloning with new objective."""
        await manager.save_session(sample_session)

        cloned = await manager.clone_session(
            sample_session,
            new_objective="New objective"
        )

        assert cloned.primary_objective == "New objective"

    @pytest.mark.asyncio
    async def test_clone_session_reset_tasks(self, manager, sample_session):
        """Test cloning with task reset."""
        await manager.save_session(sample_session)

        cloned = await manager.clone_session(
            sample_session,
            reset_tasks=True
        )

        assert len(cloned.tasks) == 0

    @pytest.mark.asyncio
    async def test_find_recoverable_sessions(self, manager):
        """Test finding recoverable sessions."""
        # Create sessions with different statuses
        statuses = [
            MastermindStatus.ACTIVE,
            MastermindStatus.PAUSED,
            MastermindStatus.COMPLETED,
            MastermindStatus.FAILED,
            MastermindStatus.INITIALIZING
        ]

        for i, status in enumerate(statuses):
            session = MastermindSession(
                session_id=f"mm_recover{i}",
                status=status,
                primary_objective=f"Objective {i}"
            )
            await manager.save_session(session)

        recoverable = await manager.find_recoverable_sessions()

        # Should find ACTIVE, PAUSED, and INITIALIZING
        assert len(recoverable) == 3
        statuses_found = [s.status for s in recoverable]
        assert MastermindStatus.ACTIVE in statuses_found
        assert MastermindStatus.PAUSED in statuses_found
        assert MastermindStatus.INITIALIZING in statuses_found

    @pytest.mark.asyncio
    async def test_recover_session(self, manager, sample_session):
        """Test recovering a session."""
        # Set one task as in-progress
        sample_session.tasks["task_0"].status = TaskStatus.IN_PROGRESS
        sample_session.tasks["task_0"].assigned_to = "agent_1"
        await manager.save_session(sample_session)

        recovered = await manager.recover_session(sample_session)

        # In-progress task should be reset to pending
        assert recovered.tasks["task_0"].status == TaskStatus.PENDING
        assert recovered.tasks["task_0"].assigned_to is None
        # Active session should be paused
        assert recovered.status == MastermindStatus.PAUSED
        # Should have recovery note
        assert any("Genoptaget" in note for note in recovered.notes)

    @pytest.mark.asyncio
    async def test_recover_session_without_reset(self, manager, sample_session):
        """Test recovering without resetting in-progress tasks."""
        sample_session.tasks["task_0"].status = TaskStatus.IN_PROGRESS
        await manager.save_session(sample_session)

        recovered = await manager.recover_session(
            sample_session,
            reset_in_progress_tasks=False
        )

        # Task should remain in-progress
        assert recovered.tasks["task_0"].status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_get_session_statistics(self, manager, sample_session):
        """Test getting session statistics."""
        # Set up some completed tasks
        sample_session.tasks["task_0"].status = TaskStatus.COMPLETED
        sample_session.tasks["task_0"].actual_duration_seconds = 30
        sample_session.tasks["task_1"].status = TaskStatus.COMPLETED
        sample_session.tasks["task_1"].actual_duration_seconds = 45
        sample_session.tasks["task_2"].status = TaskStatus.FAILED
        sample_session.consumed_usd = 25.0
        sample_session.started_at = datetime.now() - timedelta(hours=1)

        await manager.save_session(sample_session)

        stats = await manager.get_session_statistics(sample_session)

        assert stats["session_id"] == sample_session.session_id
        assert stats["total_tasks"] == 5
        assert stats["completed_tasks"] == 2
        assert stats["failed_tasks"] == 1
        assert stats["pending_tasks"] == 2
        assert stats["success_rate_percent"] == pytest.approx(66.67, rel=0.01)
        assert stats["total_task_duration_seconds"] == 75
        assert stats["budget_usd"] == 100.0
        assert stats["consumed_usd"] == 25.0
        assert stats["budget_utilization_percent"] == 25.0


# =============================================================================
# TEST FACTORY FUNCTIONS
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_session_manager(self):
        """Test creating SessionManager via factory."""
        manager = create_session_manager(
            store=InMemorySessionStore(),
            auto_save=False,
            auto_checkpoint_interval_tasks=10
        )

        assert isinstance(manager, SessionManager)
        assert manager.auto_save is False
        assert manager.auto_checkpoint_interval_tasks == 10

    def test_get_session_manager(self):
        """Test getting singleton SessionManager."""
        manager1 = create_session_manager(store=InMemorySessionStore())
        manager2 = get_session_manager()

        assert manager1 is manager2

    def test_create_session_manager_default_store(self):
        """Test SessionManager with default FileSessionStore."""
        manager = create_session_manager()

        assert isinstance(manager, SessionManager)
        assert isinstance(manager.store, FileSessionStore)


# =============================================================================
# TEST IMPORTS
# =============================================================================

class TestImports:
    """Tests for module imports."""

    def test_import_from_session_module(self):
        """Test importing from session module."""
        from cirkelline.ckc.mastermind.session import (
            SessionCheckpoint,
            SessionStore,
            FileSessionStore,
            InMemorySessionStore,
            SessionManager,
            create_session_manager,
            get_session_manager,
        )

        assert SessionCheckpoint is not None
        assert SessionStore is not None
        assert FileSessionStore is not None
        assert InMemorySessionStore is not None
        assert SessionManager is not None

    def test_import_from_mastermind_package(self):
        """Test importing from mastermind package."""
        from cirkelline.ckc.mastermind import (
            SessionCheckpoint,
            SessionStore,
            FileSessionStore,
            InMemorySessionStore,
            SessionManager,
            create_session_manager,
            get_session_manager,
        )

        assert SessionCheckpoint is not None
        assert SessionManager is not None


# =============================================================================
# TEST CONCURRENT OPERATIONS
# =============================================================================

class TestConcurrentOperations:
    """Tests for concurrent session operations."""

    @pytest.mark.asyncio
    async def test_concurrent_saves(self):
        """Test multiple concurrent session saves."""
        store = InMemorySessionStore()

        async def save_session(i):
            session = MastermindSession(
                session_id=f"mm_concurrent{i}",
                status=MastermindStatus.ACTIVE,
                primary_objective=f"Objective {i}"
            )
            return await store.save(session)

        tasks = [save_session(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert all(results)
        assert len(store._sessions) == 10

    @pytest.mark.asyncio
    async def test_concurrent_checkpoint_operations(self):
        """Test concurrent checkpoint operations."""
        manager = SessionManager(store=InMemorySessionStore())

        session = MastermindSession(
            session_id="mm_ccops",
            status=MastermindStatus.ACTIVE,
            primary_objective="Concurrent checkpoints"
        )
        await manager.save_session(session)

        async def create_cp(i):
            return await manager.create_checkpoint(
                session,
                label=f"Checkpoint {i}"
            )

        tasks = [create_cp(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        checkpoints = await manager.list_checkpoints(session.session_id)
        assert len(checkpoints) == 5


# =============================================================================
# TEST EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_session_statistics(self):
        """Test statistics for session with no tasks."""
        manager = SessionManager(store=InMemorySessionStore())
        session = MastermindSession(
            session_id="mm_empty",
            status=MastermindStatus.ACTIVE,
            primary_objective="Empty session"
        )
        await manager.save_session(session)

        stats = await manager.get_session_statistics(session)

        assert stats["total_tasks"] == 0
        assert stats["success_rate_percent"] == 0
        assert stats["total_task_duration_seconds"] == 0

    @pytest.mark.asyncio
    async def test_session_with_zero_budget(self):
        """Test session with zero budget."""
        manager = SessionManager(store=InMemorySessionStore())
        session = MastermindSession(
            session_id="mm_nobudget",
            status=MastermindStatus.ACTIVE,
            primary_objective="No budget",
            budget_usd=0.0
        )
        await manager.save_session(session)

        stats = await manager.get_session_statistics(session)

        assert stats["budget_utilization_percent"] == 0

    @pytest.mark.asyncio
    async def test_checkpoint_empty_snapshots(self):
        """Test checkpoint with empty snapshots."""
        checkpoint = SessionCheckpoint(
            checkpoint_id="cp_empty",
            session_id="mm_empty"
        )
        data = checkpoint.to_dict()
        restored = SessionCheckpoint.from_dict(data)

        assert restored.state_snapshot == {}
        assert restored.tasks_snapshot == {}
        assert restored.context_snapshot == {}
