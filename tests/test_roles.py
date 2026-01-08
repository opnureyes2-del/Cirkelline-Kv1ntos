"""
Tests for CKC MASTERMIND Roles & Direction (cirkelline.ckc.mastermind.roles)
============================================================================

Tests covering:
- Enums: DirigentState
- Data Classes: SuperAdminCommand, DirigentPlan
- SuperAdminInterface
- SystemsDirigent
- MastermindCapableAgent mixin
- Factory functions
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from cirkelline.ckc.mastermind.roles import (
    # Enums
    DirigentState,
    # Data Classes
    SuperAdminCommand,
    DirigentPlan,
    # Classes
    SuperAdminInterface,
    SystemsDirigent,
    MastermindCapableAgent,
    # Factory functions
    create_super_admin_interface,
    create_systems_dirigent,
)
from cirkelline.ckc.mastermind.coordinator import (
    MastermindSession,
    MastermindStatus,
    MastermindPriority,
    MastermindTask,
    TaskStatus,
    Directive,
    DirectiveType,
)
from cirkelline.ckc.mastermind.messaging import InMemoryMessageBus


# =============================================================================
# TESTS FOR ENUMS
# =============================================================================

class TestDirigentStateEnum:
    """Tests for DirigentState enum."""

    def test_awaiting_directive(self):
        """Test AWAITING_DIRECTIVE state."""
        assert DirigentState.AWAITING_DIRECTIVE.value == "awaiting_directive"

    def test_planning(self):
        """Test PLANNING state."""
        assert DirigentState.PLANNING.value == "planning"

    def test_delegating(self):
        """Test DELEGATING state."""
        assert DirigentState.DELEGATING.value == "delegating"

    def test_monitoring(self):
        """Test MONITORING state."""
        assert DirigentState.MONITORING.value == "monitoring"

    def test_synthesizing(self):
        """Test SYNTHESIZING state."""
        assert DirigentState.SYNTHESIZING.value == "synthesizing"

    def test_reporting(self):
        """Test REPORTING state."""
        assert DirigentState.REPORTING.value == "reporting"


# =============================================================================
# TESTS FOR DATA CLASSES
# =============================================================================

class TestSuperAdminCommand:
    """Tests for SuperAdminCommand dataclass."""

    def test_command_creation_minimal(self):
        """Test creating command with minimal parameters."""
        cmd = SuperAdminCommand(
            command_id="cmd_001",
            command_type="start_session",
            parameters={"session_id": "s001"}
        )
        assert cmd.command_id == "cmd_001"
        assert cmd.command_type == "start_session"
        assert cmd.status == "pending"  # default
        assert cmd.executed_at is None

    def test_command_creation_full(self):
        """Test creating command with all parameters."""
        now = datetime.now()
        cmd = SuperAdminCommand(
            command_id="cmd_002",
            command_type="pause_session",
            parameters={"session_id": "s002"},
            issued_at=now,
            executed_at=now,
            status="executed",
            result={"success": True}
        )
        assert cmd.executed_at == now
        assert cmd.status == "executed"
        assert cmd.result["success"] is True


class TestDirigentPlan:
    """Tests for DirigentPlan dataclass."""

    def test_plan_creation_minimal(self):
        """Test creating plan with minimal parameters."""
        plan = DirigentPlan(
            plan_id="plan_001",
            session_id="s001",
            objective="Test objective"
        )
        assert plan.plan_id == "plan_001"
        assert plan.status == "draft"  # default
        assert plan.current_phase == 0  # default
        assert plan.phases == []  # default

    def test_plan_creation_with_phases(self):
        """Test creating plan with phases."""
        phases = [
            {"phase_id": "p1", "name": "Phase 1"},
            {"phase_id": "p2", "name": "Phase 2"}
        ]
        plan = DirigentPlan(
            plan_id="plan_002",
            session_id="s002",
            objective="Multi-phase objective",
            phases=phases,
            status="ready"
        )
        assert len(plan.phases) == 2
        assert plan.status == "ready"

    def test_plan_to_execution_plan(self):
        """Test converting DirigentPlan to ExecutionPlan."""
        plan = DirigentPlan(
            plan_id="plan_003",
            session_id="s003",
            objective="Conversion test",
            phases=[{"phase_id": "p1"}],
            current_phase=1
        )
        exec_plan = plan.to_execution_plan()

        assert exec_plan.plan_id == "plan_003"
        assert exec_plan.objective == "Conversion test"
        assert exec_plan.current_phase == 1


# =============================================================================
# TESTS FOR SUPER ADMIN INTERFACE
# =============================================================================

class TestSuperAdminInterface:
    """Tests for SuperAdminInterface."""

    @pytest.fixture
    def interface(self):
        """Create a fresh interface for each test."""
        return SuperAdminInterface()

    @pytest_asyncio.fixture
    async def interface_with_bus(self):
        """Create interface with message bus."""
        bus = InMemoryMessageBus()
        await bus.connect()
        return SuperAdminInterface(message_bus=bus)

    @pytest.mark.asyncio
    async def test_start_session(self, interface):
        """Test starting a session."""
        cmd = await interface.start_session(
            session_id="s001",
            objective="Test session",
            priority=MastermindPriority.HIGH
        )

        assert cmd.command_type == "start_session"
        assert cmd.parameters["session_id"] == "s001"
        assert cmd.parameters["objective"] == "Test session"
        assert len(interface._command_history) == 1

    @pytest.mark.asyncio
    async def test_start_session_with_bus(self, interface_with_bus):
        """Test starting a session with message bus."""
        cmd = await interface_with_bus.start_session(
            session_id="s002",
            objective="With bus"
        )

        assert cmd.status == "sent"

    @pytest.mark.asyncio
    async def test_pause_session(self, interface):
        """Test pausing a session."""
        cmd = await interface.pause_session(session_id="s001")

        assert cmd.command_type == "pause_session"
        assert cmd.parameters["session_id"] == "s001"

    @pytest.mark.asyncio
    async def test_resume_session(self, interface):
        """Test resuming a session."""
        cmd = await interface.resume_session(session_id="s001")

        assert cmd.command_type == "resume_session"

    @pytest.mark.asyncio
    async def test_abort_session(self, interface):
        """Test aborting a session."""
        cmd = await interface.abort_session(
            session_id="s001",
            reason="Testing abort"
        )

        assert cmd.command_type == "abort_session"
        assert cmd.parameters["reason"] == "Testing abort"

    @pytest.mark.asyncio
    async def test_issue_directive(self, interface):
        """Test issuing a directive."""
        cmd = await interface.issue_directive(
            session_id="s001",
            directive_text="Focus on analysis",
            target="all",
            priority=MastermindPriority.HIGH
        )

        assert cmd.command_type == "issue_directive"
        assert cmd.parameters["directive"] == "Focus on analysis"

    @pytest.mark.asyncio
    async def test_adjust_parameters(self, interface):
        """Test adjusting parameters."""
        cmd = await interface.adjust_parameters(
            session_id="s001",
            parameters={"timeout": 300, "max_retries": 3}
        )

        assert cmd.command_type == "adjust_parameters"
        assert cmd.parameters["timeout"] == 300

    @pytest.mark.asyncio
    async def test_prioritize_agent(self, interface):
        """Test prioritizing an agent."""
        cmd = await interface.prioritize_agent(
            session_id="s001",
            agent_id="agent_001",
            priority=MastermindPriority.CRITICAL
        )

        assert cmd.command_type == "prioritize_agent"
        assert cmd.parameters["agent_id"] == "agent_001"

    @pytest.mark.asyncio
    async def test_approve_request(self, interface):
        """Test approving a HITL request."""
        cmd = await interface.approve_request(
            session_id="s001",
            request_id="req_001",
            comments="Approved"
        )

        assert cmd.command_type == "approve_request"
        assert cmd.status == "executed"

    @pytest.mark.asyncio
    async def test_reject_request(self, interface):
        """Test rejecting a HITL request."""
        cmd = await interface.reject_request(
            session_id="s001",
            request_id="req_002",
            reason="Insufficient data"
        )

        assert cmd.command_type == "reject_request"
        assert cmd.parameters["reason"] == "Insufficient data"

    @pytest.mark.asyncio
    async def test_get_command_history(self, interface):
        """Test getting command history."""
        await interface.start_session("s001", "Session 1")
        await interface.start_session("s002", "Session 2")
        await interface.pause_session("s001")

        # All commands
        history = interface.get_command_history()
        assert len(history) == 3

        # Filtered by session
        history_s001 = interface.get_command_history(session_id="s001")
        assert len(history_s001) == 2

    @pytest.mark.asyncio
    async def test_get_command_history_with_limit(self, interface):
        """Test command history with limit."""
        for i in range(10):
            await interface.start_session(f"s{i}", f"Session {i}")

        history = interface.get_command_history(limit=5)
        assert len(history) == 5


# =============================================================================
# TESTS FOR SYSTEMS DIRIGENT
# =============================================================================

class TestSystemsDirigent:
    """Tests for SystemsDirigent."""

    @pytest.fixture
    def dirigent(self):
        """Create a fresh dirigent for each test."""
        return SystemsDirigent()

    @pytest.fixture
    def session(self):
        """Create a test session."""
        return MastermindSession(
            session_id="test_session",
            primary_objective="Test objective"
        )

    def test_initial_state(self, dirigent):
        """Test initial state is AWAITING_DIRECTIVE."""
        assert dirigent.state == DirigentState.AWAITING_DIRECTIVE

    @pytest.mark.asyncio
    async def test_transition_to(self, dirigent):
        """Test state transition."""
        await dirigent.transition_to(DirigentState.PLANNING)

        assert dirigent.state == DirigentState.PLANNING
        assert len(dirigent._state_history) == 1
        assert dirigent._state_history[0]["from"] == "awaiting_directive"
        assert dirigent._state_history[0]["to"] == "planning"

    @pytest.mark.asyncio
    async def test_receive_directive(self, dirigent, session):
        """Test receiving a directive and creating a plan."""
        plan = await dirigent.receive_directive(
            session=session,
            directive="Analyze the data and provide insights"
        )

        assert plan.session_id == "test_session"
        assert plan.objective == "Analyze the data and provide insights"
        assert len(plan.phases) == 3  # Default 3 phases
        assert plan.status == "ready"
        assert dirigent._current_plan is plan

    @pytest.mark.asyncio
    async def test_delegate_tasks(self, dirigent, session):
        """Test delegating tasks to agents."""
        tasks = [
            MastermindTask(
                task_id="t1",
                title="Task 1",
                description="First task"
            ),
            MastermindTask(
                task_id="t2",
                title="Task 2",
                description="Second task"
            )
        ]
        agents = ["agent_001", "agent_002", "agent_003"]

        delegations = await dirigent.delegate_tasks(session, tasks, agents)

        assert len(delegations) == 2
        assert "t1" in delegations
        assert "t2" in delegations
        assert dirigent.state == DirigentState.MONITORING

    @pytest.mark.asyncio
    async def test_collect_result(self, dirigent):
        """Test collecting result from agent."""
        dirigent._active_delegations["t1"] = "agent_001"

        await dirigent.collect_result(
            task_id="t1",
            agent_id="agent_001",
            result={"analysis": "complete"}
        )

        assert len(dirigent._collected_results) == 1
        assert dirigent._collected_results[0]["task_id"] == "t1"
        assert "t1" not in dirigent._active_delegations

    @pytest.mark.asyncio
    async def test_synthesize_results(self, dirigent):
        """Test synthesizing collected results."""
        dirigent._collected_results = [
            {"task_id": "t1", "result": "Result 1"},
            {"task_id": "t2", "result": "Result 2"}
        ]

        synthesis = await dirigent.synthesize_results()

        assert synthesis["total_results"] == 2
        assert "synthesis_id" in synthesis
        assert dirigent.state == DirigentState.SYNTHESIZING

    @pytest.mark.asyncio
    async def test_report_to_super_admin(self, dirigent, session):
        """Test reporting to super admin."""
        dirigent._collected_results = [{"task_id": "t1"}]

        report = await dirigent.report_to_super_admin(
            session=session,
            report_type="progress"
        )

        assert report["session_id"] == "test_session"
        assert report["report_type"] == "progress"
        assert report["collected_results"] == 1
        assert dirigent.state == DirigentState.AWAITING_DIRECTIVE

    @pytest.mark.asyncio
    async def test_reallocate_resources(self, dirigent, session):
        """Test resource reallocation."""
        result = await dirigent.reallocate_resources(
            session=session,
            reason="Performance bottleneck"
        )

        assert result is True

    def test_get_state_history(self, dirigent):
        """Test getting state history."""
        history = dirigent.get_state_history()
        assert isinstance(history, list)


# =============================================================================
# TESTS FOR MASTERMIND CAPABLE AGENT
# =============================================================================

class TestMastermindCapableAgent:
    """Tests for MastermindCapableAgent mixin."""

    @pytest.fixture
    def agent(self):
        """Create a test agent."""
        return MastermindCapableAgent()

    def test_initial_state(self, agent):
        """Test initial state is not in mastermind mode."""
        assert agent.in_mastermind_mode is False
        assert agent._mastermind_session is None

    def test_enter_mastermind_mode(self, agent):
        """Test entering mastermind mode."""
        agent.enter_mastermind_mode(
            session_id="s001",
            priority=MastermindPriority.HIGH,
            reporting_interval=10
        )

        assert agent.in_mastermind_mode is True
        assert agent._mastermind_session == "s001"
        assert agent._mastermind_priority == MastermindPriority.HIGH
        assert agent._reporting_interval == 10

    def test_exit_mastermind_mode(self, agent):
        """Test exiting mastermind mode."""
        agent.enter_mastermind_mode("s001")
        agent.exit_mastermind_mode()

        assert agent.in_mastermind_mode is False
        assert agent._mastermind_session is None
        assert agent._mastermind_priority == MastermindPriority.NORMAL

    @pytest.mark.asyncio
    async def test_report_progress_not_in_mode(self, agent):
        """Test reporting progress when not in mastermind mode."""
        result = await agent.report_progress(progress=0.5)
        assert result is False

    @pytest.mark.asyncio
    async def test_report_progress_in_mode(self, agent):
        """Test reporting progress in mastermind mode."""
        agent.enter_mastermind_mode("s001")
        result = await agent.report_progress(
            progress=0.75,
            partial_result={"data": "partial"}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_report_progress_with_bus(self, agent):
        """Test reporting progress with message bus."""
        bus = InMemoryMessageBus()
        await bus.connect()

        agent.enter_mastermind_mode("s001")
        result = await agent.report_progress(
            progress=0.5,
            message_bus=bus
        )

        assert result is True
        assert len(bus._message_history) == 1

    def test_receive_adjustment(self, agent):
        """Test receiving adjustment from dirigent."""
        agent.enter_mastermind_mode("s001")

        adjustment = Directive(
            directive_id="dir_001",
            directive_type=DirectiveType.PRIORITIZATION,
            source="super_admin",
            target="agent_001",
            content={"priority": 4, "reporting_interval": 15}
        )

        result = agent.receive_adjustment(adjustment)

        assert result is True
        assert agent._mastermind_priority == MastermindPriority(4)
        assert agent._reporting_interval == 15
        assert len(agent._adjustment_history) == 1

    def test_get_adjustment_history(self, agent):
        """Test getting adjustment history."""
        agent.enter_mastermind_mode("s001")

        adj1 = Directive(
            directive_id="dir_001",
            directive_type=DirectiveType.PRIORITIZATION,
            source="super_admin",
            target="agent_001",
            content={"priority": 3}
        )
        adj2 = Directive(
            directive_id="dir_002",
            directive_type=DirectiveType.FEEDBACK,
            source="super_admin",
            target="agent_001",
            content={"feedback": "good"}
        )

        agent.receive_adjustment(adj1)
        agent.receive_adjustment(adj2)

        history = agent.get_adjustment_history()
        assert len(history) == 2
        assert history[0]["directive_id"] == "dir_001"


# =============================================================================
# TESTS FOR FACTORY FUNCTIONS
# =============================================================================

class TestRolesFactoryFunctions:
    """Tests for roles factory functions."""

    def test_create_super_admin_interface(self):
        """Test creating super admin interface."""
        interface = create_super_admin_interface()

        assert isinstance(interface, SuperAdminInterface)
        assert interface.message_bus is None

    def test_create_super_admin_interface_with_bus(self):
        """Test creating super admin interface with message bus."""
        bus = InMemoryMessageBus()
        interface = create_super_admin_interface(message_bus=bus)

        assert interface.message_bus is bus

    def test_create_systems_dirigent(self):
        """Test creating systems dirigent."""
        dirigent = create_systems_dirigent()

        assert isinstance(dirigent, SystemsDirigent)
        assert dirigent.state == DirigentState.AWAITING_DIRECTIVE

    def test_create_systems_dirigent_with_bus(self):
        """Test creating systems dirigent with message bus."""
        bus = InMemoryMessageBus()
        dirigent = create_systems_dirigent(message_bus=bus)

        assert dirigent.message_bus is bus


# =============================================================================
# TESTS FOR MODULE IMPORTS
# =============================================================================

class TestRolesModuleImports:
    """Tests for roles module imports."""

    def test_all_exports_importable(self):
        """Test that all expected exports are available."""
        from cirkelline.ckc.mastermind import roles

        # Enums
        assert hasattr(roles, 'DirigentState')

        # Data classes
        assert hasattr(roles, 'SuperAdminCommand')
        assert hasattr(roles, 'DirigentPlan')

        # Classes
        assert hasattr(roles, 'SuperAdminInterface')
        assert hasattr(roles, 'SystemsDirigent')
        assert hasattr(roles, 'MastermindCapableAgent')

        # Factory functions
        assert hasattr(roles, 'create_super_admin_interface')
        assert hasattr(roles, 'create_systems_dirigent')
