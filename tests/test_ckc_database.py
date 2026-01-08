"""
Test suite for CKC Database Infrastructure
==========================================

Tests database connection, repositories, and CRUD operations.
Requires CKC database (ckc_brain on port 5533) to be configured.
"""

import asyncio
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Skip all tests if CKC database is not available
pytestmark = pytest.mark.skipif(
    os.environ.get("CKC_DATABASE_READY") != "true",
    reason="CKC database infrastructure not configured. Set CKC_DATABASE_READY=true to run."
)

from cirkelline.ckc.infrastructure.database import CKCDatabase, DatabaseConfig
from cirkelline.ckc.infrastructure.repositories import (
    TaskContextRepository,
    WorkflowStepRepository,
    AgentMemoryRepository,
    KnowledgeEntryRepository,
    AuditTrailRepository,
    MemoryType,
)


# Shared database instance
_db = None


def get_db():
    """Get or create shared database."""
    global _db
    if _db is None:
        config = DatabaseConfig(
            host="localhost",
            port=5533,
            database="ckc_brain",
            user="ckc",
            password="ckc_secure_password_2025",
        )
        _db = CKCDatabase(config)
    return _db


class TestDatabaseConnection:
    """Test database connection and pool management."""

    @pytest.mark.asyncio
    async def test_database_initialize(self):
        """Test database initialization."""
        db = get_db()
        result = await db.initialize()
        assert result is True
        assert db.is_connected is True

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test database health check."""
        db = get_db()
        await db.initialize()

        health = await db.health_check()
        assert health["status"] == "healthy"
        assert "latency_ms" in health
        assert health["pool_size"] >= 2

    @pytest.mark.asyncio
    async def test_get_schema_version(self):
        """Test getting schema version."""
        db = get_db()
        await db.initialize()

        version = await db.get_schema_version()
        assert version == 1

    @pytest.mark.asyncio
    async def test_table_exists(self):
        """Test table existence check."""
        db = get_db()
        await db.initialize()

        assert await db.table_exists("task_contexts") is True
        assert await db.table_exists("nonexistent_table") is False


class TestTaskContextRepository:
    """Test TaskContextRepository CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_context(self):
        """Test creating a task context."""
        db = get_db()
        await db.initialize()
        repo = TaskContextRepository(db)

        context = await repo.create(
            task_id="test_task_001",
            prompt="Test prompt for database test",
            user_id="test_user",
            session_id="test_session",
            metadata={"source": "test"}
        )

        assert context is not None
        assert context.context_id.startswith("ctx_")
        assert context.task_id == "test_task_001"
        assert context.original_prompt == "Test prompt for database test"
        assert context.status == "active"

        # Cleanup
        await repo.delete(context.context_id)

    @pytest.mark.asyncio
    async def test_get_context_by_id(self):
        """Test retrieving context by ID."""
        db = get_db()
        await db.initialize()
        repo = TaskContextRepository(db)

        # Create
        context = await repo.create(
            task_id="test_task_002",
            prompt="Get by ID test",
        )

        # Get
        retrieved = await repo.get_by_context_id(context.context_id)
        assert retrieved is not None
        assert retrieved.task_id == "test_task_002"

        # Cleanup
        await repo.delete(context.context_id)

    @pytest.mark.asyncio
    async def test_update_context(self):
        """Test updating context."""
        db = get_db()
        await db.initialize()
        repo = TaskContextRepository(db)

        context = await repo.create(
            task_id="test_task_003",
            prompt="Update test",
        )

        # Update
        updated = await repo.update(
            context.context_id,
            status="completed",
            current_agent="tool_explorer"
        )

        assert updated.status == "completed"
        assert updated.current_agent == "tool_explorer"

        # Cleanup
        await repo.delete(context.context_id)

    @pytest.mark.asyncio
    async def test_list_active_contexts(self):
        """Test listing active contexts."""
        db = get_db()
        await db.initialize()
        repo = TaskContextRepository(db)

        # Create some contexts
        ctx1 = await repo.create(task_id="list_test_1", prompt="Test 1")
        ctx2 = await repo.create(task_id="list_test_2", prompt="Test 2")

        # List
        active = await repo.list_active(limit=100)
        assert len(active) >= 2

        # Cleanup
        await repo.delete(ctx1.context_id)
        await repo.delete(ctx2.context_id)


class TestWorkflowStepRepository:
    """Test WorkflowStepRepository operations."""

    @pytest.mark.asyncio
    async def test_create_and_update_step(self):
        """Test creating and updating workflow steps."""
        db = get_db()
        await db.initialize()
        context_repo = TaskContextRepository(db)
        step_repo = WorkflowStepRepository(db)

        # Create context first
        context = await context_repo.create(
            task_id="workflow_test",
            prompt="Workflow step test"
        )

        # Create step
        step = await step_repo.create(
            context_id=context.context_id,
            step_id="step_001",
            agent_id="tool_explorer",
            action="analyze_code",
            input_data={"file": "test.py"}
        )

        assert step.status == "pending"

        # Update to running
        step = await step_repo.update_status(
            context.context_id,
            "step_001",
            status="running"
        )
        assert step.status == "running"
        assert step.started_at is not None

        # Update to completed
        step = await step_repo.update_status(
            context.context_id,
            "step_001",
            status="completed",
            output_data={"result": "success"}
        )
        assert step.status == "completed"
        assert step.output_data == {"result": "success"}

        # Cleanup
        await context_repo.delete(context.context_id)


class TestAgentMemoryRepository:
    """Test AgentMemoryRepository operations."""

    @pytest.mark.asyncio
    async def test_create_memory(self):
        """Test creating agent memory."""
        db = get_db()
        await db.initialize()
        repo = AgentMemoryRepository(db)

        memory = await repo.create(
            agent_id="tool_explorer",
            memory_type=MemoryType.EPISODIC,
            content={"event": "analyzed file", "file": "test.py"},
            importance=0.8,
            tags=["analysis", "code"]
        )

        assert memory is not None
        assert memory.agent_id == "tool_explorer"
        assert memory.memory_type == MemoryType.EPISODIC
        assert memory.importance == 0.8

        # Cleanup
        await repo.soft_delete(memory.id)

    @pytest.mark.asyncio
    async def test_get_memories_by_agent(self):
        """Test getting memories for an agent."""
        db = get_db()
        await db.initialize()
        repo = AgentMemoryRepository(db)

        # Create some memories
        m1 = await repo.create(
            agent_id="test_agent_mem",
            memory_type=MemoryType.SEMANTIC,
            content={"fact": "Python is a programming language"},
            tags=["python"]
        )
        m2 = await repo.create(
            agent_id="test_agent_mem",
            memory_type=MemoryType.PROCEDURAL,
            content={"procedure": "How to analyze code"},
            tags=["procedure"]
        )

        # Get all for agent
        memories = await repo.get_by_agent("test_agent_mem")
        assert len(memories) >= 2

        # Get by type
        semantic = await repo.get_by_agent("test_agent_mem", MemoryType.SEMANTIC)
        assert all(m.memory_type == MemoryType.SEMANTIC for m in semantic)

        # Cleanup
        await repo.soft_delete(m1.id)
        await repo.soft_delete(m2.id)

    @pytest.mark.asyncio
    async def test_search_by_tags(self):
        """Test searching memories by tags."""
        db = get_db()
        await db.initialize()
        repo = AgentMemoryRepository(db)

        m1 = await repo.create(
            agent_id="search_test_agent",
            memory_type=MemoryType.SEMANTIC,
            content={"topic": "databases"},
            tags=["database", "sql", "postgresql"]
        )

        # Search
        results = await repo.search_by_tags("search_test_agent", ["sql"])
        assert len(results) >= 1
        assert "sql" in results[0].tags

        # Cleanup
        await repo.soft_delete(m1.id)


class TestKnowledgeEntryRepository:
    """Test KnowledgeEntryRepository operations."""

    @pytest.mark.asyncio
    async def test_search_knowledge(self):
        """Test searching knowledge entries."""
        db = get_db()
        await db.initialize()
        repo = KnowledgeEntryRepository(db)

        # Search for seeded entries
        results = await repo.search("CKC", category="system")
        assert len(results) >= 1


class TestAuditTrailRepository:
    """Test AuditTrailRepository operations."""

    @pytest.mark.asyncio
    async def test_log_audit_event(self):
        """Test logging audit events."""
        db = get_db()
        await db.initialize()
        repo = AuditTrailRepository(db)

        audit = await repo.log(
            entity_type="task_context",
            entity_id="ctx_test123",
            action="create",
            actor="system",
            actor_type="system",
            new_value={"status": "active"},
            metadata={"source": "test"}
        )

        assert audit is not None
        assert audit.action == "create"
        assert audit.entity_type == "task_context"

    @pytest.mark.asyncio
    async def test_get_audit_history(self):
        """Test getting audit history."""
        db = get_db()
        await db.initialize()
        repo = AuditTrailRepository(db)

        # Log some events
        await repo.log(
            entity_type="test_entity",
            entity_id="test_id_001",
            action="create",
            actor="test"
        )
        await repo.log(
            entity_type="test_entity",
            entity_id="test_id_001",
            action="update",
            actor="test"
        )

        # Get history
        history = await repo.get_for_entity("test_entity", "test_id_001")
        assert len(history) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
