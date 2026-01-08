"""
Tests for CKC MASTERMIND Context Management
===========================================

Tests for DEL D: DirigentContextManager, TaskTemplateEngine, AutoDocumentationTrigger.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta

from cirkelline.ckc.mastermind.context import (
    # Enums
    ContextSource,
    DocumentationType,
    TriggerEvent,
    # Data Classes
    ContextItem,
    ContextBundle,
    Reference,
    TaskTemplate,
    DocumentationEvent,
    # Classes
    DirigentContextManager,
    TaskTemplateEngine,
    AutoDocumentationTrigger,
    # Factory Functions
    create_context_manager,
    get_context_manager,
    create_template_engine,
    get_template_engine,
    create_doc_trigger,
    get_doc_trigger,
)


# =============================================================================
# TEST ENUMS
# =============================================================================

class TestContextEnums:
    """Tests for context enums."""

    def test_context_source_values(self):
        """Test ContextSource enum values."""
        assert ContextSource.CURRENT_SESSION.value == "current_session"
        assert ContextSource.PREVIOUS_SESSION.value == "previous_session"
        assert ContextSource.KNOWLEDGE_BANK.value == "knowledge_bank"
        assert ContextSource.NOTION_DOC.value == "notion_doc"
        assert ContextSource.AGENT_MEMORY.value == "agent_memory"
        assert ContextSource.USER_PREFERENCE.value == "user_preference"

    def test_documentation_type_values(self):
        """Test DocumentationType enum values."""
        assert DocumentationType.SESSION_REPORT.value == "session_report"
        assert DocumentationType.ASSET_DOCUMENTATION.value == "asset_documentation"
        assert DocumentationType.WORKFLOW_DOCUMENTATION.value == "workflow_documentation"
        assert DocumentationType.INCIDENT_REPORT.value == "incident_report"
        assert DocumentationType.PERFORMANCE_REPORT.value == "performance_report"

    def test_trigger_event_values(self):
        """Test TriggerEvent enum values."""
        assert TriggerEvent.SESSION_COMPLETED.value == "session_completed"
        assert TriggerEvent.ASSET_CREATED.value == "asset_created"
        assert TriggerEvent.WORKFLOW_COMPLETED.value == "workflow_completed"
        assert TriggerEvent.PERFORMANCE_ANOMALY.value == "performance_anomaly"
        assert TriggerEvent.ERROR_OCCURRED.value == "error_occurred"
        assert TriggerEvent.MILESTONE_REACHED.value == "milestone_reached"


# =============================================================================
# TEST DATA CLASSES
# =============================================================================

class TestContextDataClasses:
    """Tests for context data classes."""

    def test_context_item_creation(self):
        """Test ContextItem creation."""
        item = ContextItem(
            item_id="ctx_test123",
            source=ContextSource.CURRENT_SESSION,
            title="Test Context",
            content="Test content",
            relevance_score=0.85
        )
        assert item.item_id == "ctx_test123"
        assert item.source == ContextSource.CURRENT_SESSION
        assert item.title == "Test Context"
        assert item.relevance_score == 0.85

    def test_context_item_is_expired(self):
        """Test ContextItem expiration check."""
        # Not expired
        item = ContextItem(
            item_id="ctx_1",
            source=ContextSource.AGENT_MEMORY,
            title="Test",
            content="Content",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        assert item.is_expired() is False

        # Expired
        expired_item = ContextItem(
            item_id="ctx_2",
            source=ContextSource.AGENT_MEMORY,
            title="Test",
            content="Content",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        assert expired_item.is_expired() is True

        # No expiration
        no_expire_item = ContextItem(
            item_id="ctx_3",
            source=ContextSource.AGENT_MEMORY,
            title="Test",
            content="Content"
        )
        assert no_expire_item.is_expired() is False

    def test_context_item_to_dict(self):
        """Test ContextItem serialization."""
        item = ContextItem(
            item_id="ctx_dict",
            source=ContextSource.KNOWLEDGE_BANK,
            title="Dict Test",
            content="Content",
            relevance_score=0.5,
            tags=["tag1", "tag2"]
        )
        d = item.to_dict()
        assert d["item_id"] == "ctx_dict"
        assert d["source"] == "knowledge_bank"
        assert d["tags"] == ["tag1", "tag2"]

    def test_context_bundle_creation(self):
        """Test ContextBundle creation."""
        bundle = ContextBundle(
            bundle_id="bundle_test",
            task_description="Test task"
        )
        assert bundle.bundle_id == "bundle_test"
        assert bundle.task_description == "Test task"
        assert len(bundle.items) == 0

    def test_context_bundle_add_item(self):
        """Test adding items to ContextBundle."""
        bundle = ContextBundle(
            bundle_id="bundle_add",
            task_description="Adding items"
        )
        item = ContextItem(
            item_id="item1",
            source=ContextSource.CURRENT_SESSION,
            title="Item 1",
            content="Content 1",
            relevance_score=0.8
        )
        bundle.add_item(item)
        assert len(bundle.items) == 1
        assert bundle.total_relevance == 0.8

    def test_context_bundle_get_top_items(self):
        """Test getting top relevant items."""
        bundle = ContextBundle(
            bundle_id="bundle_top",
            task_description="Top items test"
        )
        for i, score in enumerate([0.3, 0.9, 0.5, 0.7]):
            bundle.add_item(ContextItem(
                item_id=f"item_{i}",
                source=ContextSource.AGENT_MEMORY,
                title=f"Item {i}",
                content=f"Content {i}",
                relevance_score=score
            ))

        top_2 = bundle.get_top_items(2)
        assert len(top_2) == 2
        assert top_2[0].relevance_score == 0.9
        assert top_2[1].relevance_score == 0.7

    def test_reference_creation(self):
        """Test Reference creation."""
        ref = Reference(
            reference_id="ref_test",
            reference_type="session",
            target_id="session_123",
            title="Related Session",
            description="A related session",
            relevance_score=0.75
        )
        assert ref.reference_id == "ref_test"
        assert ref.reference_type == "session"
        assert ref.relevance_score == 0.75

    def test_task_template_render(self):
        """Test TaskTemplate rendering."""
        template = TaskTemplate(
            template_id="tmpl_test",
            name="Test Template",
            template="Hello {name}, your task is {task}.",
            required_fields=["name", "task"]
        )
        result = template.render(name="Rasmus", task="build CKC")
        assert result == "Hello Rasmus, your task is build CKC."

    def test_documentation_event_creation(self):
        """Test DocumentationEvent creation."""
        event = DocumentationEvent(
            event_id="evt_test",
            event_type=TriggerEvent.SESSION_COMPLETED,
            doc_type=DocumentationType.SESSION_REPORT,
            session_id="sess_123"
        )
        assert event.event_id == "evt_test"
        assert event.event_type == TriggerEvent.SESSION_COMPLETED
        assert event.doc_type == DocumentationType.SESSION_REPORT


# =============================================================================
# TEST DIRIGENT CONTEXT MANAGER
# =============================================================================

class TestDirigentContextManager:
    """Tests for DirigentContextManager."""

    @pytest_asyncio.fixture
    async def manager(self):
        """Create fresh context manager for each test."""
        return DirigentContextManager()

    @pytest.mark.asyncio
    async def test_register_session_context(self, manager):
        """Test registering session context."""
        manager.register_session_context(
            session_id="session_reg",
            objective="Test CKC implementation",
            tags=["test", "ckc"]
        )
        stats = manager.get_statistics()
        assert stats["session_contexts"] == 1

    @pytest.mark.asyncio
    async def test_get_relevant_context(self, manager):
        """Test getting relevant context."""
        manager.register_session_context(
            session_id="session_ctx",
            objective="Build AI agent system",
            tags=["ai", "agent"]
        )

        bundle = await manager.get_relevant_context(
            task_description="Create new AI agent",
            session_id="session_ctx"
        )

        assert bundle is not None
        assert bundle.task_description == "Create new AI agent"
        assert len(bundle.items) >= 0

    @pytest.mark.asyncio
    async def test_create_context_summary(self, manager):
        """Test creating context summary."""
        manager.register_session_context(
            session_id="session_sum1",
            objective="First task",
            tags=["task1"]
        )
        manager.register_session_context(
            session_id="session_sum2",
            objective="Second task",
            tags=["task2"]
        )

        summary = await manager.create_context_summary(
            sources=["session_sum1", "session_sum2"],
            max_length=500
        )

        assert len(summary) <= 500
        assert "First task" in summary or "Second task" in summary

    @pytest.mark.asyncio
    async def test_cross_reference(self, manager):
        """Test finding cross-references."""
        manager.register_session_context(
            session_id="session_ref1",
            objective="AI agent development",
            tags=["ai", "agent"]
        )
        manager.register_session_context(
            session_id="session_ref2",
            objective="Machine learning model",
            tags=["ml", "ai"]
        )

        refs = await manager.cross_reference(
            task_description="AI development",
            current_session_id="session_ref1"
        )

        assert isinstance(refs, list)

    @pytest.mark.asyncio
    async def test_add_reference(self, manager):
        """Test adding reference to index."""
        ref = Reference(
            reference_id="ref_add",
            reference_type="document",
            target_id="doc_123",
            title="Related Document",
            description="A useful document"
        )
        manager.add_reference("ai_development", ref)

        stats = manager.get_statistics()
        assert stats["reference_keys"] == 1
        assert stats["total_references"] == 1

    def test_calculate_relevance(self, manager):
        """Test relevance calculation."""
        relevance = manager._calculate_relevance(
            query="AI agent development",
            text="Building AI agent systems"
        )
        assert relevance > 0

        # No overlap
        no_relevance = manager._calculate_relevance(
            query="cooking recipes",
            text="software engineering"
        )
        assert no_relevance == 0.0


# =============================================================================
# TEST TASK TEMPLATE ENGINE
# =============================================================================

class TestTaskTemplateEngine:
    """Tests for TaskTemplateEngine."""

    @pytest.fixture
    def engine(self):
        """Create task template engine."""
        return TaskTemplateEngine()

    def test_list_templates(self, engine):
        """Test listing available templates."""
        templates = engine.list_templates()
        assert "standard" in templates
        assert "creative" in templates
        assert "research" in templates

    def test_get_template(self, engine):
        """Test getting template by name."""
        template = engine.get_template("standard")
        assert template is not None
        assert template.template_id == "tmpl_standard"

    def test_get_nonexistent_template(self, engine):
        """Test getting non-existent template."""
        template = engine.get_template("nonexistent")
        assert template is None

    def test_render_standard_task(self, engine):
        """Test rendering standard task."""
        rendered = engine.render_task(
            "standard",
            title="Test Task",
            objective="Complete the test"
        )
        assert "Test Task" in rendered
        assert "Complete the test" in rendered

    def test_render_creative_task(self, engine):
        """Test rendering creative task."""
        rendered = engine.render_task(
            "creative",
            title="Creative Project",
            vision="Create beautiful art"
        )
        assert "Creative Project" in rendered
        assert "Create beautiful art" in rendered

    def test_render_research_task(self, engine):
        """Test rendering research task."""
        rendered = engine.render_task(
            "research",
            title="AI Research",
            research_question="How do agents collaborate?"
        )
        assert "AI Research" in rendered
        assert "How do agents collaborate?" in rendered

    def test_register_custom_template(self, engine):
        """Test registering custom template."""
        custom = TaskTemplate(
            template_id="tmpl_custom",
            name="Custom Template",
            template="Custom: {content}",
            required_fields=["content"]
        )
        engine.register_template("custom", custom)

        templates = engine.list_templates()
        assert "custom" in templates


# =============================================================================
# TEST AUTO-DOCUMENTATION TRIGGER
# =============================================================================

class TestAutoDocumentationTrigger:
    """Tests for AutoDocumentationTrigger."""

    @pytest_asyncio.fixture
    async def trigger(self):
        """Create auto-documentation trigger."""
        return AutoDocumentationTrigger()

    @pytest.mark.asyncio
    async def test_trigger_session_completed(self, trigger):
        """Test triggering session completed event."""
        event = await trigger.trigger(
            event_type=TriggerEvent.SESSION_COMPLETED,
            session_id="session_complete",
            source_data={
                "session_id": "session_complete",
                "status": "Completed",
                "objective": "Test CKC",
                "results_summary": "All tests passed",
                "duration": "1h 30m",
                "tasks_completed": 10,
                "budget_used": 5.50
            }
        )

        assert event.event_type == TriggerEvent.SESSION_COMPLETED
        assert event.doc_type == DocumentationType.SESSION_REPORT
        assert event.generated_doc is not None
        assert "Session Rapport" in event.generated_doc

    @pytest.mark.asyncio
    async def test_trigger_asset_created(self, trigger):
        """Test triggering asset created event."""
        event = await trigger.trigger(
            event_type=TriggerEvent.ASSET_CREATED,
            source_data={
                "asset_id": "asset_123",
                "asset_type": "Image",
                "created_at": "2025-01-01",
                "description": "A generated image"
            }
        )

        assert event.doc_type == DocumentationType.ASSET_DOCUMENTATION
        assert "Asset Dokumentation" in event.generated_doc

    @pytest.mark.asyncio
    async def test_trigger_error_occurred(self, trigger):
        """Test triggering error event."""
        event = await trigger.trigger(
            event_type=TriggerEvent.ERROR_OCCURRED,
            source_data={
                "severity": "High",
                "timestamp": "2025-01-01T12:00:00",
                "description": "Connection timeout",
                "cause": "Network issue",
                "action_taken": "Retry"
            }
        )

        assert event.doc_type == DocumentationType.INCIDENT_REPORT
        assert "Incident Rapport" in event.generated_doc

    @pytest.mark.asyncio
    async def test_get_history(self, trigger):
        """Test getting event history."""
        await trigger.trigger(
            event_type=TriggerEvent.SESSION_COMPLETED,
            session_id="sess1"
        )
        await trigger.trigger(
            event_type=TriggerEvent.ASSET_CREATED,
            session_id="sess2"
        )

        history = trigger.get_history()
        assert len(history) == 2

        # Filter by type
        session_history = trigger.get_history(event_type=TriggerEvent.SESSION_COMPLETED)
        assert len(session_history) == 1

    @pytest.mark.asyncio
    async def test_register_handler(self, trigger):
        """Test registering custom handler."""
        handler_called = []

        async def custom_handler(event):
            handler_called.append(event.event_id)

        trigger.register_handler(TriggerEvent.MILESTONE_REACHED, custom_handler)

        await trigger.trigger(
            event_type=TriggerEvent.MILESTONE_REACHED,
            source_data={"milestone": "Phase 1 complete"}
        )

        assert len(handler_called) == 1

    def test_get_statistics(self, trigger):
        """Test getting trigger statistics."""
        stats = trigger.get_statistics()
        assert "total_events" in stats
        assert "by_type" in stats
        assert "registered_handlers" in stats


# =============================================================================
# TEST FACTORY FUNCTIONS
# =============================================================================

class TestContextFactoryFunctions:
    """Tests for factory functions."""

    @pytest.mark.asyncio
    async def test_create_context_manager(self):
        """Test creating context manager."""
        manager = await create_context_manager()
        assert manager is not None
        assert isinstance(manager, DirigentContextManager)

    @pytest.mark.asyncio
    async def test_get_context_manager(self):
        """Test getting existing context manager."""
        await create_context_manager()
        manager = get_context_manager()
        assert manager is not None

    def test_create_template_engine(self):
        """Test creating template engine."""
        engine = create_template_engine()
        assert engine is not None
        assert isinstance(engine, TaskTemplateEngine)

    def test_get_template_engine(self):
        """Test getting existing template engine."""
        create_template_engine()
        engine = get_template_engine()
        assert engine is not None

    @pytest.mark.asyncio
    async def test_create_doc_trigger(self):
        """Test creating doc trigger."""
        trigger = await create_doc_trigger()
        assert trigger is not None
        assert isinstance(trigger, AutoDocumentationTrigger)

    @pytest.mark.asyncio
    async def test_get_doc_trigger(self):
        """Test getting existing doc trigger."""
        await create_doc_trigger()
        trigger = get_doc_trigger()
        assert trigger is not None


# =============================================================================
# TEST MODULE IMPORTS
# =============================================================================

class TestContextModuleImports:
    """Tests for module imports."""

    def test_all_exports_importable(self):
        """Test that all exports are importable."""
        from cirkelline.ckc.mastermind.context import (
            ContextSource,
            DocumentationType,
            TriggerEvent,
            ContextItem,
            ContextBundle,
            Reference,
            TaskTemplate,
            DocumentationEvent,
            DirigentContextManager,
            TaskTemplateEngine,
            AutoDocumentationTrigger,
            create_context_manager,
            get_context_manager,
            create_template_engine,
            get_template_engine,
            create_doc_trigger,
            get_doc_trigger,
        )
        assert True
