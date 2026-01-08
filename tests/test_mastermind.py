"""
CKC MASTERMIND Module Tests
============================

Omfattende testsuite for MASTERMIND Tilstand.
"""

import asyncio
import pytest
from datetime import datetime, timedelta

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio(loop_scope="function")


# =============================================================================
# COORDINATOR TESTS
# =============================================================================

class TestMastermindCoordinator:
    """Tests for MastermindCoordinator."""

    @pytest.fixture
    def coordinator(self):
        from cirkelline.ckc.mastermind import create_mastermind_coordinator
        return create_mastermind_coordinator(
            max_concurrent_sessions=5,
            max_agents_per_session=20
        )

    async def test_create_session(self, coordinator):
        """Test session creation."""
        session = await coordinator.create_session(
            objective="Test objektiv",
            budget_usd=100.0
        )

        assert session is not None
        assert session.session_id.startswith("mm_")
        assert session.primary_objective == "Test objektiv"
        assert session.budget_usd == 100.0
        assert session.status.value == "initializing"

    async def test_start_session(self, coordinator):
        """Test starting a session."""
        session = await coordinator.create_session(objective="Start test")
        result = await coordinator.start_session(session.session_id)

        assert result is True
        assert coordinator.get_session(session.session_id).status.value == "active"

    async def test_pause_resume_session(self, coordinator):
        """Test pause and resume."""
        session = await coordinator.create_session(objective="Pause test")
        await coordinator.start_session(session.session_id)

        # Pause
        await coordinator.pause_session(session.session_id)
        assert coordinator.get_session(session.session_id).status.value == "paused"

        # Resume
        await coordinator.resume_session(session.session_id)
        assert coordinator.get_session(session.session_id).status.value == "active"

    async def test_complete_session(self, coordinator):
        """Test completing a session."""
        session = await coordinator.create_session(objective="Complete test")
        await coordinator.start_session(session.session_id)

        completed = await coordinator.complete_session(
            session.session_id,
            final_result={"summary": "Success"}
        )

        assert completed.status.value == "completed"
        assert completed.completed_at is not None

    async def test_abort_session(self, coordinator):
        """Test aborting a session."""
        session = await coordinator.create_session(objective="Abort test")
        await coordinator.start_session(session.session_id)

        result = await coordinator.abort_session(
            session.session_id,
            reason="Test abortion"
        )

        assert result is True
        assert coordinator.get_session(session.session_id).status.value == "aborted"

    async def test_create_task(self, coordinator):
        """Test task creation."""
        session = await coordinator.create_session(objective="Task test")

        task = await coordinator.create_task(
            session_id=session.session_id,
            title="Test opgave",
            description="Test beskrivelse"
        )

        assert task is not None
        assert task.task_id.startswith("task_")
        assert task.title == "Test opgave"
        assert task.status.value == "pending"

    async def test_assign_task(self, coordinator):
        """Test task assignment."""
        from cirkelline.ckc.mastermind import ParticipantRole

        session = await coordinator.create_session(objective="Assignment test")

        # Register agent
        await coordinator.register_agent(
            session_id=session.session_id,
            agent_id="agent_1",
            agent_name="Test Agent",
            role=ParticipantRole.SPECIALIST,
            capabilities=["test"]
        )

        # Create and assign task
        task = await coordinator.create_task(
            session_id=session.session_id,
            title="Assign test",
            description="Test"
        )

        result = await coordinator.assign_task(
            session_id=session.session_id,
            task_id=task.task_id,
            agent_id="agent_1"
        )

        assert result is True
        assert session.tasks[task.task_id].assigned_to == "agent_1"

    async def test_complete_task(self, coordinator):
        """Test task completion."""
        from cirkelline.ckc.mastermind import TaskResult

        session = await coordinator.create_session(objective="Complete task test")
        task = await coordinator.create_task(
            session_id=session.session_id,
            title="Complete me",
            description="Test"
        )

        result = TaskResult(
            task_id=task.task_id,
            success=True,
            output={"data": "test"}
        )

        await coordinator.complete_task(
            session_id=session.session_id,
            task_id=task.task_id,
            result=result
        )

        assert session.tasks[task.task_id].status.value == "completed"

    async def test_list_sessions(self, coordinator):
        """Test session listing."""
        await coordinator.create_session(objective="List test 1")
        await coordinator.create_session(objective="List test 2")

        sessions = coordinator.list_sessions()
        assert len(sessions) >= 2

    async def test_issue_directive(self, coordinator):
        """Test issuing directives."""
        from cirkelline.ckc.mastermind import DirectiveType

        session = await coordinator.create_session(objective="Directive test")

        directive = await coordinator.issue_directive(
            session_id=session.session_id,
            directive_type=DirectiveType.OBJECTIVE,
            source="super_admin",
            target="all",
            content={"instruction": "Do something"}
        )

        assert directive is not None
        assert directive.directive_id.startswith("dir_")
        assert len(session.super_admin_directives) == 1

    async def test_register_agent(self, coordinator):
        """Test agent registration."""
        from cirkelline.ckc.mastermind import ParticipantRole

        session = await coordinator.create_session(objective="Agent test")

        participation = await coordinator.register_agent(
            session_id=session.session_id,
            agent_id="test_agent",
            agent_name="Test Agent",
            role=ParticipantRole.SPECIALIST,
            capabilities=["analyze", "generate"]
        )

        assert participation is not None
        assert participation.agent_id == "test_agent"
        assert "test_agent" in session.active_agents

    async def test_generate_feedback_report(self, coordinator):
        """Test feedback report generation."""
        session = await coordinator.create_session(objective="Feedback test")
        await coordinator.create_task(session.session_id, "Task 1", "Desc")
        await coordinator.create_task(session.session_id, "Task 2", "Desc")

        report = await coordinator.generate_feedback_report(session.session_id)

        assert report is not None
        assert report.session_id == session.session_id
        assert report.pending_tasks == 2

    async def test_metrics(self, coordinator):
        """Test coordinator metrics."""
        await coordinator.create_session(objective="Metrics test")

        metrics = coordinator.get_metrics()
        assert metrics["total_sessions"] >= 1

    async def test_max_sessions_limit(self, coordinator):
        """Test max concurrent sessions limit."""
        # Create max sessions
        for i in range(5):
            await coordinator.create_session(objective=f"Session {i}")

        # Should fail
        with pytest.raises(ValueError, match="Max antal"):
            await coordinator.create_session(objective="Too many")


# =============================================================================
# SESSION MANAGEMENT TESTS
# =============================================================================

class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.fixture
    def manager(self):
        from cirkelline.ckc.mastermind import create_session_manager, InMemorySessionStore
        return create_session_manager(store=InMemorySessionStore())

    @pytest.fixture
    def sample_session(self):
        from cirkelline.ckc.mastermind import MastermindSession
        return MastermindSession(
            session_id="test_session_1",
            primary_objective="Test objective"
        )

    async def test_save_load_session(self, manager, sample_session):
        """Test save and load."""
        await manager.save_session(sample_session)
        loaded = await manager.load_session(sample_session.session_id)

        assert loaded is not None
        assert loaded.session_id == sample_session.session_id

    async def test_delete_session(self, manager, sample_session):
        """Test session deletion."""
        await manager.save_session(sample_session)
        result = await manager.delete_session(sample_session.session_id)

        assert result is True
        assert await manager.load_session(sample_session.session_id) is None

    async def test_create_checkpoint(self, manager, sample_session):
        """Test checkpoint creation."""
        checkpoint = await manager.create_checkpoint(
            sample_session,
            label="Test checkpoint"
        )

        assert checkpoint is not None
        assert checkpoint.checkpoint_id.startswith("cp_")
        assert checkpoint.label == "Test checkpoint"

    async def test_list_checkpoints(self, manager, sample_session):
        """Test checkpoint listing."""
        await manager.create_checkpoint(sample_session, label="CP 1")
        await manager.create_checkpoint(sample_session, label="CP 2")

        checkpoints = await manager.list_checkpoints(sample_session.session_id)
        assert len(checkpoints) >= 2

    async def test_clone_session(self, manager, sample_session):
        """Test session cloning."""
        await manager.save_session(sample_session)

        cloned = await manager.clone_session(
            sample_session,
            new_objective="Cloned objective"
        )

        assert cloned is not None
        assert cloned.session_id != sample_session.session_id
        assert cloned.primary_objective == "Cloned objective"
        assert "cloned" in cloned.tags

    async def test_session_statistics(self, manager, sample_session):
        """Test session statistics."""
        stats = await manager.get_session_statistics(sample_session)

        assert "session_id" in stats
        assert "total_tasks" in stats
        assert "success_rate_percent" in stats


# =============================================================================
# MESSAGING TESTS
# =============================================================================

class TestMessaging:
    """Tests for messaging system."""

    @pytest.fixture
    def message_bus(self):
        from cirkelline.ckc.mastermind import InMemoryMessageBus
        return InMemoryMessageBus()

    async def test_connect_disconnect(self, message_bus):
        """Test connect and disconnect."""
        assert await message_bus.connect() is True
        assert await message_bus.disconnect() is True

    async def test_publish_message(self, message_bus):
        """Test message publishing."""
        from cirkelline.ckc.mastermind import (
            MastermindMessage,
            MastermindMessageType,
            MessagePriority
        )

        await message_bus.connect()

        message = MastermindMessage(
            message_id="msg_test_1",
            session_id="session_1",
            message_type=MastermindMessageType.STATUS_SESSION_UPDATE,
            source="test",
            destination="all",
            payload={"status": "updated"}
        )

        result = await message_bus.publish(message)
        assert result is True

    async def test_subscribe_receive(self, message_bus):
        """Test subscribe and receive messages."""
        from cirkelline.ckc.mastermind import (
            MastermindMessage,
            MastermindMessageType
        )

        await message_bus.connect()

        received = []

        async def handler(msg):
            received.append(msg)

        handler_id = await message_bus.subscribe(
            message_types=[MastermindMessageType.STATUS_SESSION_UPDATE],
            handler=handler
        )

        assert handler_id is not None

        # Publish message
        message = MastermindMessage(
            message_id="msg_test_2",
            session_id="session_1",
            message_type=MastermindMessageType.STATUS_SESSION_UPDATE,
            source="test",
            destination="all",
            payload={}
        )

        await message_bus.publish(message)
        assert len(received) == 1

    async def test_unsubscribe(self, message_bus):
        """Test unsubscribe."""
        from cirkelline.ckc.mastermind import MastermindMessageType

        await message_bus.connect()

        handler_id = await message_bus.subscribe(
            message_types=[MastermindMessageType.STATUS_SESSION_UPDATE],
            handler=lambda msg: None
        )

        result = await message_bus.unsubscribe(handler_id)
        assert result is True

    async def test_message_builder(self):
        """Test message builder."""
        from cirkelline.ckc.mastermind import (
            MastermindMessageBuilder,
            MastermindMessageType,
            MessagePriority
        )

        message = MastermindMessageBuilder("session_1", "test") \
            .type(MastermindMessageType.STATUS_SESSION_UPDATE) \
            .to("dirigent") \
            .payload({"data": "test"}) \
            .priority(MessagePriority.HIGH) \
            .require_ack() \
            .build()

        assert message is not None
        assert message.session_id == "session_1"
        assert message.priority == MessagePriority.HIGH
        assert message.requires_ack is True

    async def test_convenience_functions(self):
        """Test convenience message creation functions."""
        from cirkelline.ckc.mastermind import (
            create_command_message,
            create_directive_message,
            create_status_message,
            create_result_message,
            MastermindMessageType
        )

        cmd = create_command_message(
            session_id="s1",
            command_type=MastermindMessageType.COMMAND_START,
            payload={}
        )
        assert cmd.source == "super_admin"

        directive = create_directive_message(
            session_id="s1",
            directive_type=MastermindMessageType.DIRECTIVE_ASSIGN,
            target_agent="agent_1",
            payload={}
        )
        assert directive.source == "dirigent"

        status = create_status_message(
            session_id="s1",
            agent_id="agent_1",
            status_type=MastermindMessageType.STATUS_TASK_STARTED,
            payload={}
        )
        assert status.destination == "all"

        result = create_result_message(
            session_id="s1",
            agent_id="agent_1",
            task_id="task_1",
            result={"data": "test"}
        )
        assert result.requires_ack is True


# =============================================================================
# ROLES TESTS
# =============================================================================

class TestRoles:
    """Tests for role system."""

    async def test_super_admin_interface(self):
        """Test Super Admin interface."""
        from cirkelline.ckc.mastermind import create_super_admin_interface

        super_admin = create_super_admin_interface()

        # Test start session command
        cmd = await super_admin.start_session(
            session_id="s1",
            objective="Test"
        )

        assert cmd is not None
        assert cmd.command_type == "start_session"
        assert cmd.status == "sent"

    async def test_super_admin_commands(self):
        """Test various Super Admin commands."""
        from cirkelline.ckc.mastermind import (
            create_super_admin_interface,
            MastermindPriority
        )

        super_admin = create_super_admin_interface()

        # Pause
        cmd = await super_admin.pause_session("s1")
        assert cmd.command_type == "pause_session"

        # Resume
        cmd = await super_admin.resume_session("s1")
        assert cmd.command_type == "resume_session"

        # Abort
        cmd = await super_admin.abort_session("s1", "Test reason")
        assert cmd.command_type == "abort_session"

        # Issue directive
        cmd = await super_admin.issue_directive("s1", "Do something", priority=MastermindPriority.HIGH)
        assert cmd.command_type == "issue_directive"

        # Prioritize agent
        cmd = await super_admin.prioritize_agent("s1", "agent_1", MastermindPriority.CRITICAL)
        assert cmd.command_type == "prioritize_agent"

    async def test_systems_dirigent(self):
        """Test Systems Dirigent."""
        from cirkelline.ckc.mastermind import (
            create_systems_dirigent,
            DirigentState,
            MastermindSession
        )

        dirigent = create_systems_dirigent()
        assert dirigent.state == DirigentState.AWAITING_DIRECTIVE

        # Receive directive
        session = MastermindSession(
            session_id="test_session",
            primary_objective="Test"
        )

        plan = await dirigent.receive_directive(session, "Create a report")

        assert plan is not None
        assert len(plan.phases) > 0
        assert dirigent.state == DirigentState.PLANNING

    async def test_mastermind_capable_agent(self):
        """Test MastermindCapableAgent mixin."""
        from cirkelline.ckc.mastermind import (
            MastermindCapableAgent,
            MastermindPriority,
            Directive,
            DirectiveType
        )

        class TestAgent(MastermindCapableAgent):
            def __init__(self):
                super().__init__()
                self.name = "Test Agent"

        agent = TestAgent()
        assert not agent.in_mastermind_mode

        # Enter mastermind mode
        agent.enter_mastermind_mode("session_1", MastermindPriority.HIGH)
        assert agent.in_mastermind_mode
        assert agent._mastermind_session == "session_1"

        # Receive adjustment
        directive = Directive(
            directive_id="d1",
            directive_type=DirectiveType.ADJUSTMENT,
            source="dirigent",
            target="agent_1",
            content={"priority": 4, "reporting_interval": 10}
        )

        agent.receive_adjustment(directive)
        assert agent._mastermind_priority == MastermindPriority.CRITICAL
        assert agent._reporting_interval == 10

        # Exit
        agent.exit_mastermind_mode()
        assert not agent.in_mastermind_mode


# =============================================================================
# FEEDBACK TESTS
# =============================================================================

class TestFeedback:
    """Tests for feedback system."""

    @pytest.fixture
    def aggregator(self):
        from cirkelline.ckc.mastermind import create_feedback_aggregator
        return create_feedback_aggregator()

    @pytest.fixture
    def sample_session(self):
        from cirkelline.ckc.mastermind import MastermindSession
        return MastermindSession(
            session_id="feedback_test",
            primary_objective="Test",
            budget_usd=100.0
        )

    async def test_process_result(self, aggregator, sample_session):
        """Test result processing."""
        from cirkelline.ckc.mastermind import TaskResult

        result = TaskResult(
            task_id="task_1",
            success=True,
            output={"data": "test"},
            confidence=0.95
        )

        report = await aggregator.process_result(sample_session, result)

        assert report is not None
        assert report.session_id == sample_session.session_id

    async def test_add_feedback(self, aggregator):
        """Test adding feedback."""
        from cirkelline.ckc.mastermind import FeedbackSeverity

        item = aggregator.add_feedback(
            session_id="s1",
            source="agent_1",
            category="quality",
            message="Task completed with high quality",
            severity=FeedbackSeverity.INFO
        )

        assert item is not None
        assert item.item_id.startswith("fb_")

    async def test_result_collector(self):
        """Test ResultCollector."""
        from cirkelline.ckc.mastermind import ResultCollector, TaskResult

        collector = ResultCollector()

        result = TaskResult(
            task_id="task_1",
            success=True,
            output="test",
            confidence=0.8
        )

        success = await collector.collect("s1", result)
        assert success is True

        results = collector.get_results("s1", min_confidence=0.5)
        assert len(results) == 1

    async def test_synthesis_engine(self):
        """Test SynthesisEngine."""
        from cirkelline.ckc.mastermind import SynthesisEngine, TaskResult

        engine = SynthesisEngine()

        results = [
            TaskResult(task_id="t1", success=True, output="r1", confidence=0.9),
            TaskResult(task_id="t2", success=True, output="r2", confidence=0.8),
            TaskResult(task_id="t3", success=False, output=None, error="fail", confidence=0.7)
        ]

        synthesis = await engine.synthesize(results)

        assert synthesis["total_results"] == 3
        assert synthesis["successful"] == 2
        assert synthesis["failed"] == 1

    async def test_decision_engine(self, sample_session):
        """Test DecisionEngine."""
        from cirkelline.ckc.mastermind import DecisionEngine

        engine = DecisionEngine()

        synthesis = {
            "total_results": 10,
            "successful": 9,
            "failed": 1,
            "avg_confidence": 0.85,
            "conflicts": []
        }

        passed, issues, recommendations = await engine.evaluate(sample_session, synthesis)

        assert passed is True
        assert len(issues) == 0

    async def test_decision_engine_with_issues(self, sample_session):
        """Test DecisionEngine with issues."""
        from cirkelline.ckc.mastermind import DecisionEngine

        engine = DecisionEngine()

        # Low success rate
        synthesis = {
            "total_results": 10,
            "successful": 5,
            "failed": 5,
            "avg_confidence": 0.6,
            "conflicts": [{"type": "test"}]
        }

        passed, issues, recommendations = await engine.evaluate(sample_session, synthesis)

        assert passed is False
        assert len(issues) > 0
        assert len(recommendations) > 0


# =============================================================================
# RESOURCE TESTS
# =============================================================================

class TestResources:
    """Tests for resource management."""

    @pytest.fixture
    def allocator(self):
        from cirkelline.ckc.mastermind import create_resource_allocator
        return create_resource_allocator()

    @pytest.fixture
    def sample_session(self):
        from cirkelline.ckc.mastermind import (
            MastermindSession,
            AgentParticipation,
            ParticipantRole
        )

        session = MastermindSession(
            session_id="resource_test",
            primary_objective="Test"
        )

        # Add some agents
        session.active_agents["agent_1"] = AgentParticipation(
            agent_id="agent_1",
            agent_name="Agent 1",
            role=ParticipantRole.SPECIALIST,
            capabilities=[]
        )
        session.active_agents["agent_2"] = AgentParticipation(
            agent_id="agent_2",
            agent_name="Agent 2",
            role=ParticipantRole.SPECIALIST,
            capabilities=[]
        )

        return session

    async def test_allocate_for_session(self, allocator, sample_session):
        """Test session resource allocation."""
        allocations = await allocator.allocate_for_session(sample_session)

        assert len(allocations) > 0
        assert "agent_1" in allocations
        assert "agent_2" in allocations

    async def test_reserve_api_capacity(self, allocator):
        """Test API capacity reservation."""
        reservation = await allocator.reserve_api_capacity(
            session_id="s1",
            api_name="openai",
            calls=100,
            cost_per_call=0.01,
            duration_minutes=30
        )

        assert reservation is not None
        assert reservation.calls_reserved == 100
        assert reservation.calls_remaining == 100

    async def test_use_api_call(self, allocator):
        """Test using API calls from reservation."""
        reservation = await allocator.reserve_api_capacity(
            session_id="s1",
            api_name="test_api",
            calls=10
        )

        success = await allocator.use_api_call(reservation.reservation_id, calls=3)
        assert success is True
        assert reservation.calls_remaining == 7

    async def test_budget_tracking(self, allocator):
        """Test budget tracking."""
        allocator.set_session_budget("s1", 100.0)

        # Consume
        success = allocator.consume_budget("s1", 25.0)
        assert success is True

        status = allocator.get_budget_status("s1")
        assert status["consumed"] == 25.0
        assert status["available"] == 75.0

    async def test_budget_reserve(self, allocator):
        """Test budget reservation."""
        allocator.set_session_budget("s1", 100.0)

        # Reserve
        success = allocator.reserve_budget("s1", 30.0)
        assert success is True

        status = allocator.get_budget_status("s1")
        assert status["reserved"] == 30.0
        assert status["available"] == 70.0

        # Release reservation
        allocator.release_budget_reservation("s1", 30.0)
        status = allocator.get_budget_status("s1")
        assert status["reserved"] == 0.0

    async def test_load_balancer(self):
        """Test LoadBalancer."""
        from cirkelline.ckc.mastermind import create_load_balancer

        balancer = create_load_balancer(max_load=3)

        # Get least loaded
        agents = ["a1", "a2", "a3"]
        selected = balancer.get_least_loaded_agent(agents)
        assert selected in agents

        # Assign tasks
        for _ in range(3):
            balancer.assign_task("a1")

        # a1 should be at max
        assert balancer.get_agent_load("a1") == 3

        # Next selection should not be a1
        selected = balancer.get_least_loaded_agent(["a1", "a2"])
        assert selected == "a2"

    async def test_pool_status(self, allocator):
        """Test resource pool status."""
        from cirkelline.ckc.mastermind import ResourceType

        status = allocator.get_pool_status()
        assert ResourceType.COMPUTE.value in status
        assert ResourceType.API_CALLS.value in status


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for MASTERMIND system."""

    async def test_full_session_workflow(self):
        """Test complete session workflow."""
        from cirkelline.ckc.mastermind import (
            create_mastermind_coordinator,
            create_session_manager,
            create_message_bus,
            create_feedback_aggregator,
            ParticipantRole,
            TaskResult,
            InMemorySessionStore
        )

        # Setup
        coordinator = create_mastermind_coordinator()
        manager = create_session_manager(store=InMemorySessionStore())
        message_bus = create_message_bus()
        feedback = create_feedback_aggregator()

        await message_bus.connect()

        # Create and start session
        session = await coordinator.create_session(
            objective="Generer markedsføringsmateriale",
            budget_usd=50.0
        )
        await coordinator.start_session(session.session_id)

        # Register agents
        await coordinator.register_agent(
            session.session_id,
            "content_agent",
            "Content Specialist",
            ParticipantRole.SPECIALIST,
            ["write", "edit"]
        )
        await coordinator.register_agent(
            session.session_id,
            "design_agent",
            "Design Specialist",
            ParticipantRole.SPECIALIST,
            ["design", "illustrate"]
        )

        # Create tasks
        task1 = await coordinator.create_task(
            session.session_id,
            "Skriv blogindlæg",
            "Skriv et engagerende blogindlæg"
        )
        task2 = await coordinator.create_task(
            session.session_id,
            "Design grafik",
            "Design tilhørende grafik"
        )

        # Assign tasks
        await coordinator.assign_task(session.session_id, task1.task_id, "content_agent")
        await coordinator.assign_task(session.session_id, task2.task_id, "design_agent")

        # Complete tasks
        result1 = TaskResult(
            task_id=task1.task_id,
            success=True,
            output={"content": "Blog post content..."},
            agent_id="content_agent"
        )
        await coordinator.complete_task(session.session_id, task1.task_id, result1)

        result2 = TaskResult(
            task_id=task2.task_id,
            success=True,
            output={"design": "graphic_url.png"},
            agent_id="design_agent"
        )
        await coordinator.complete_task(session.session_id, task2.task_id, result2)

        # Generate feedback report
        report = await coordinator.generate_feedback_report(session.session_id)
        assert report.completed_tasks == 2
        assert report.pending_tasks == 0

        # Complete session
        completed = await coordinator.complete_session(
            session.session_id,
            final_result={"blog": "content", "graphic": "url"}
        )

        assert completed.status.value == "completed"

        # Save session
        await manager.save_session(completed)

        # Load and verify
        loaded = await manager.load_session(session.session_id)
        assert loaded is not None

        await message_bus.disconnect()

    async def test_module_imports(self):
        """Test that all module imports work."""
        from cirkelline.ckc.mastermind import (
            # Coordinator
            MastermindCoordinator,
            MastermindSession,
            MastermindStatus,
            MastermindPriority,

            # Session
            SessionManager,
            SessionCheckpoint,

            # Messaging
            MastermindMessage,
            MastermindMessageType,
            InMemoryMessageBus,

            # Roles
            SuperAdminInterface,
            SystemsDirigent,
            MastermindCapableAgent,

            # Feedback
            FeedbackAggregator,
            ResultCollector,

            # Resources
            ResourceAllocator,
            LoadBalancer,

            # Factory functions
            create_mastermind_coordinator,
            create_session_manager,
            create_message_bus,
            create_super_admin_interface,
            create_systems_dirigent,
            create_feedback_aggregator,
            create_resource_allocator,
            create_load_balancer,
        )

        # All imports successful
        assert True


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
