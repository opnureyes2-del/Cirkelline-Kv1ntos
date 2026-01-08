"""
CKC Tools for Cirkelline Integration
=====================================

Provides tools for Cirkelline to interact with the CKC (Cirkelline Knowledge Center)
ecosystem, including:
- Mastermind collaborative sessions
- Learning Rooms
- CKC Orchestrator task management
- Super Admin capabilities

Usage:
    from cirkelline.tools.ckc_tools import CKCTools

    ckc_tools = CKCTools()
    # Add to Cirkelline team tools

Version: 1.1.0 (with Optimizer integration)
Date: 2025-12-16
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from cirkelline.config import logger

# Import CKC Optimizer for performance tracking
try:
    from cirkelline.tools.ckc_optimizer import (
        get_ckc_optimizer,
        ToolCallStatus,
    )
    CKC_OPTIMIZER_AVAILABLE = True
except ImportError:
    CKC_OPTIMIZER_AVAILABLE = False
    logger.info("CKC Optimizer not available - tracking disabled")

# Import CKC components
try:
    from cirkelline.ckc.orchestrator import (
        get_orchestrator,
        get_orchestrator_status,
        create_task,
        CKCOrchestrator,
        TaskPriority,
    )
    CKC_ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CKC Orchestrator not available: {e}")
    CKC_ORCHESTRATOR_AVAILABLE = False

try:
    from cirkelline.ckc.learning_rooms import (
        LearningRoom,
        RoomStatus,
        ValidationState,
    )
    CKC_LEARNING_ROOMS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CKC Learning Rooms not available: {e}")
    CKC_LEARNING_ROOMS_AVAILABLE = False

try:
    from cirkelline.ckc.mastermind import (
        get_mastermind_coordinator,
        create_mastermind_coordinator,
        MastermindCoordinator,
        MastermindStatus,
        MastermindPriority,
    )
    CKC_MASTERMIND_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CKC Mastermind not available: {e}")
    CKC_MASTERMIND_AVAILABLE = False


class CKCTools:
    """
    CKC Integration Tools for Cirkelline.

    Provides agent-callable tools for interacting with the CKC ecosystem.
    All methods are designed to be used as AGNO tools.

    Features:
        - get_ckc_status: Get overall CKC system status
        - list_ckc_capabilities: List available CKC capabilities
        - create_ckc_task: Create a task in CKC orchestrator
        - start_mastermind_session: Start collaborative Mastermind session
        - list_learning_rooms: List available learning rooms
        - get_room_status: Get status of a specific room
    """

    def __init__(self):
        """Initialize CKC Tools."""
        self._orchestrator: Optional[CKCOrchestrator] = None
        self._mastermind: Optional[MastermindCoordinator] = None
        self._optimizer = get_ckc_optimizer() if CKC_OPTIMIZER_AVAILABLE else None

        # Check availability
        self.orchestrator_available = CKC_ORCHESTRATOR_AVAILABLE
        self.mastermind_available = CKC_MASTERMIND_AVAILABLE
        self.learning_rooms_available = CKC_LEARNING_ROOMS_AVAILABLE

        logger.info(f"CKC Tools initialized - Orchestrator: {self.orchestrator_available}, "
                   f"Mastermind: {self.mastermind_available}, "
                   f"Learning Rooms: {self.learning_rooms_available}, "
                   f"Optimizer: {CKC_OPTIMIZER_AVAILABLE}")

    def _track_call(
        self,
        tool_name: str,
        status: str,
        duration_ms: float,
        error_message: Optional[str] = None
    ) -> None:
        """Track a tool call with the optimizer."""
        if self._optimizer:
            call_status = ToolCallStatus.SUCCESS if status == "success" else ToolCallStatus.FAILURE
            self._optimizer.track_call(
                tool_name=tool_name,
                status=call_status,
                duration_ms=duration_ms,
                error_message=error_message
            )

    def get_optimizer_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics from the CKC Optimizer.

        Returns:
            Dict containing optimizer health report and suggestions.
        """
        if not self._optimizer:
            return {"error": "Optimizer not available", "available": False}

        return {
            "health_report": self._optimizer.get_health_report(),
            "suggestions": self._optimizer.get_improvement_suggestions(),
            "available": True
        }

    @property
    def orchestrator(self) -> Optional[CKCOrchestrator]:
        """Get CKC Orchestrator singleton."""
        if not self.orchestrator_available:
            return None
        if self._orchestrator is None:
            self._orchestrator = get_orchestrator()
        return self._orchestrator

    @property
    def mastermind(self) -> Optional[MastermindCoordinator]:
        """Get Mastermind Coordinator singleton."""
        if not self.mastermind_available:
            return None
        if self._mastermind is None:
            self._mastermind = get_mastermind_coordinator()
        return self._mastermind

    def get_ckc_status(self) -> Dict[str, Any]:
        """
        Get the overall status of the CKC system.

        Returns:
            Dict containing:
            - orchestrator_status: CKC Orchestrator status
            - mastermind_status: Mastermind coordinator status
            - learning_rooms_status: Learning rooms availability
            - capabilities: List of available capabilities
            - timestamp: Current timestamp

        Example:
            status = ckc_tools.get_ckc_status()
            print(status['orchestrator_status'])
        """
        start_time = time.time()
        error_msg = None

        try:
            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "ckc_available": True,
                "components": {
                    "orchestrator": {
                        "available": self.orchestrator_available,
                        "status": "unknown"
                    },
                    "mastermind": {
                        "available": self.mastermind_available,
                        "status": "unknown"
                    },
                    "learning_rooms": {
                        "available": self.learning_rooms_available,
                        "status": "unknown"
                    }
                },
                "capabilities": self.list_ckc_capabilities()
            }

            # Get orchestrator status if available
            if self.orchestrator_available and self.orchestrator:
                try:
                    status["components"]["orchestrator"]["status"] = "ready"
                    status["components"]["orchestrator"]["details"] = {
                        "agents_registered": len(getattr(self.orchestrator, '_agents', {})),
                        "active_tasks": len(getattr(self.orchestrator, '_tasks', {})),
                    }
                except Exception as e:
                    status["components"]["orchestrator"]["status"] = f"error: {e}"

            # Get mastermind status if available
            if self.mastermind_available and self.mastermind:
                try:
                    status["components"]["mastermind"]["status"] = "ready"
                except Exception as e:
                    status["components"]["mastermind"]["status"] = f"error: {e}"

            # Get learning rooms status if available
            if self.learning_rooms_available:
                status["components"]["learning_rooms"]["status"] = "ready"

            # Track successful call
            duration_ms = (time.time() - start_time) * 1000
            self._track_call("get_ckc_status", "success", duration_ms)

            return status

        except Exception as e:
            error_msg = str(e)
            duration_ms = (time.time() - start_time) * 1000
            self._track_call("get_ckc_status", "failure", duration_ms, error_msg)
            raise

    def list_ckc_capabilities(self) -> List[str]:
        """
        List all available CKC capabilities.

        Returns:
            List of capability names that are currently available.

        Example:
            caps = ckc_tools.list_ckc_capabilities()
            # ['task_management', 'mastermind_sessions', 'learning_rooms', ...]
        """
        capabilities = []

        if self.orchestrator_available:
            capabilities.extend([
                "task_management",      # Create and manage tasks
                "agent_coordination",   # Coordinate multiple agents
                "validation_flows",     # Input validation and verification
                "work_loop_sequencer",  # Complex workflow orchestration
            ])

        if self.mastermind_available:
            capabilities.extend([
                "mastermind_sessions",      # Collaborative AI sessions
                "super_admin_control",      # Super admin capabilities
                "systems_dirigent",         # System orchestration
                "feedback_aggregation",     # Feedback collection and analysis
                "resource_allocation",      # Resource management
                "training_room",            # Agent training
                "self_optimization",        # Self-improvement scheduling
                "ethics_guardrails",        # Ethical AI controls
                "output_integrity",         # Output validation
                "learning_loop",            # Continuous learning
                "autonomy_control",         # Autonomy level management
                "insight_synthesis",        # Insight aggregation
                "decision_engine",          # Structured decision making
                "ritual_execution",         # Routine/ritual execution
                "think_aloud_streaming",    # Real-time thought streaming
                "collective_awareness",     # Shared memory/awareness
            ])

        if self.learning_rooms_available:
            capabilities.extend([
                "learning_rooms",           # Isolated learning environments
                "room_status_tracking",     # Visual status (blue/green/yellow/red)
                "validation_flow_items",    # Validation pipeline
                "integrity_verification",   # Data integrity checks
            ])

        return capabilities

    async def create_ckc_task(
        self,
        description: str,
        priority: str = "medium",
        context: Optional[Dict[str, Any]] = None,
        assigned_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a task in the CKC Orchestrator.

        Args:
            description: Task description
            priority: Task priority ('low', 'medium', 'high', 'critical')
            context: Optional context dictionary
            assigned_agent: Optional agent to assign the task to

        Returns:
            Dict containing task_id and creation status

        Example:
            result = await ckc_tools.create_ckc_task(
                description="Analyze user feedback patterns",
                priority="high",
                context={"user_id": "123"}
            )
        """
        if not self.orchestrator_available:
            return {
                "success": False,
                "error": "CKC Orchestrator is not available",
                "task_id": None
            }

        try:
            # Map string priority to enum
            priority_map = {
                "low": TaskPriority.LOW,
                "medium": TaskPriority.MEDIUM,
                "high": TaskPriority.HIGH,
                "critical": TaskPriority.CRITICAL,
            }
            task_priority = priority_map.get(priority.lower(), TaskPriority.MEDIUM)

            # Create task
            task = await create_task(
                description=description,
                priority=task_priority,
                context=context or {},
            )

            return {
                "success": True,
                "task_id": task.task_id if hasattr(task, 'task_id') else str(task),
                "description": description,
                "priority": priority,
                "status": "created",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to create CKC task: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": None
            }

    async def start_mastermind_session(
        self,
        objective: str,
        participants: Optional[List[str]] = None,
        budget_usd: float = 10.0,
        priority: str = "medium",
    ) -> Dict[str, Any]:
        """
        Start a Mastermind collaborative session.

        Mastermind sessions allow multiple AI agents to collaborate on complex tasks
        under the direction of the Systems Dirigent.

        Args:
            objective: The main objective/goal for the session
            participants: Optional list of agent IDs to include
            budget_usd: Budget limit for API calls (default: $10)
            priority: Session priority ('low', 'medium', 'high', 'critical')

        Returns:
            Dict containing session_id and session status

        Example:
            result = await ckc_tools.start_mastermind_session(
                objective="Create comprehensive marketing strategy",
                participants=["research-agent", "creative-agent"],
                budget_usd=25.0
            )
        """
        if not self.mastermind_available:
            return {
                "success": False,
                "error": "CKC Mastermind is not available",
                "session_id": None
            }

        try:
            coordinator = self.mastermind or create_mastermind_coordinator()

            # Map priority
            priority_map = {
                "low": MastermindPriority.LOW,
                "medium": MastermindPriority.MEDIUM,
                "high": MastermindPriority.HIGH,
                "critical": MastermindPriority.CRITICAL,
            }
            session_priority = priority_map.get(priority.lower(), MastermindPriority.MEDIUM)

            # Create session
            session = await coordinator.create_session(
                objective=objective,
                budget_usd=budget_usd,
                priority=session_priority,
            )

            # Start session
            await coordinator.start_session(session.session_id)

            return {
                "success": True,
                "session_id": session.session_id,
                "objective": objective,
                "status": "started",
                "budget_usd": budget_usd,
                "participants": participants or [],
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to start Mastermind session: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": None
            }

    def list_learning_rooms(self) -> List[Dict[str, Any]]:
        """
        List available CKC Learning Rooms.

        Learning Rooms are isolated environments where AI agents can learn
        and evolve with visual status tracking (blue/green/yellow/red).

        Returns:
            List of learning room summaries

        Example:
            rooms = ckc_tools.list_learning_rooms()
            for room in rooms:
                print(f"Room {room['room_id']}: {room['name']} - {room['status']}")
        """
        start_time = time.time()

        if not self.learning_rooms_available:
            duration_ms = (time.time() - start_time) * 1000
            self._track_call("list_learning_rooms", "success", duration_ms)
            return [{
                "error": "Learning Rooms not available",
                "available": False
            }]

        # Default rooms that CKC provides
        default_rooms = [
            {
                "room_id": 1,
                "name": "Research Room",
                "description": "For research tasks and knowledge synthesis",
                "status": "blue",
                "status_meaning": "Stable and validated",
                "owner": "system",
                "type": "research"
            },
            {
                "room_id": 2,
                "name": "Creative Room",
                "description": "For creative tasks and content generation",
                "status": "green",
                "status_meaning": "Active and functional",
                "owner": "system",
                "type": "creative"
            },
            {
                "room_id": 3,
                "name": "Analysis Room",
                "description": "For data analysis and pattern recognition",
                "status": "blue",
                "status_meaning": "Stable and validated",
                "owner": "system",
                "type": "analysis"
            },
            {
                "room_id": 4,
                "name": "Training Room",
                "description": "For agent training and optimization",
                "status": "green",
                "status_meaning": "Active and functional",
                "owner": "system",
                "type": "training"
            },
            {
                "room_id": 5,
                "name": "MVP Room",
                "description": "For rapid prototyping and MVP development",
                "status": "green",
                "status_meaning": "Active and functional",
                "owner": "system",
                "type": "mvp"
            },
        ]

        # Track successful call
        duration_ms = (time.time() - start_time) * 1000
        self._track_call("list_learning_rooms", "success", duration_ms)

        return default_rooms

    def get_ckc_help(self) -> str:
        """
        Get help text explaining CKC capabilities.

        Returns:
            Formatted help text describing CKC features.
        """
        help_text = """
CKC (Cirkelline Knowledge Center) Capabilities
===============================================

CKC is an advanced AI orchestration system with the following features:

ORCHESTRATOR
- Task Management: Create, track, and manage AI tasks
- Agent Coordination: Coordinate multiple specialized agents
- Validation Flows: Ensure data integrity and validation
- Work Loop Sequencer: Execute complex multi-step workflows

MASTERMIND
- Collaborative Sessions: Multiple AI agents working together
- Super Admin Control: Administrative oversight and control
- Systems Dirigent: Central orchestration of all systems
- Feedback Aggregation: Collect and analyze feedback
- Resource Allocation: Manage computational resources
- Ethics Guardrails: Ensure ethical AI behavior
- Output Integrity: Validate all AI outputs

LEARNING ROOMS
- Isolated Environments: Separate learning spaces for different tasks
- Visual Status: Blue (stable), Green (active), Yellow (warning), Red (critical)
- Validation Pipeline: Data validation before reaching rooms
- Integrity Verification: Ensure data authenticity

COMMANDS
- "enter mastermind" - Start a Mastermind collaborative session
- "ckc status" - Get CKC system status
- "list rooms" - List available learning rooms
- "create task [description]" - Create a new CKC task

For detailed help on specific features, ask about them directly.
"""
        return help_text.strip()


# Tool functions for AGNO integration
def create_ckc_tools() -> CKCTools:
    """Factory function to create CKC Tools instance."""
    return CKCTools()


# Singleton instance
_ckc_tools: Optional[CKCTools] = None


def get_ckc_tools() -> CKCTools:
    """Get singleton CKC Tools instance."""
    global _ckc_tools
    if _ckc_tools is None:
        _ckc_tools = create_ckc_tools()
    return _ckc_tools


logger.info("CKC Tools module loaded")
