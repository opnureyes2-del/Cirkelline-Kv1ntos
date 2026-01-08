"""
CKC MASTERMIND Roles & Direction
=================================

Roller i MASTERMIND systemet:
- Super Admin (Rasmus): Overordnet direktion og kontrol
- Systems Dirigent (Claude): Orkestrering og syntese
- Kommandanter: Domænespecifikke ledere
- Specialister: Udførende agenter
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .coordinator import (
    MastermindSession,
    MastermindStatus,
    MastermindPriority,
    MastermindTask,
    TaskStatus,
    Directive,
    DirectiveType,
    ExecutionPlan,
    ParticipantRole,
)
from .messaging import (
    MastermindMessage,
    MastermindMessageType,
    MessagePriority,
    MastermindMessageBus,
    create_command_message,
    create_directive_message,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DIRIGENT STATE MACHINE
# =============================================================================

class DirigentState(Enum):
    """Tilstande for Systems Dirigent."""
    AWAITING_DIRECTIVE = "awaiting_directive"
    PLANNING = "planning"
    DELEGATING = "delegating"
    MONITORING = "monitoring"
    SYNTHESIZING = "synthesizing"
    REPORTING = "reporting"


# =============================================================================
# SUPER ADMIN INTERFACE
# =============================================================================

@dataclass
class SuperAdminCommand:
    """En kommando fra Super Admin."""
    command_id: str
    command_type: str
    parameters: Dict[str, Any]
    issued_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Any] = None


class SuperAdminInterface:
    """
    Interface for Super Admin (Rasmus) til at styre MASTERMIND.

    Kommandoer:
    - start_session: Start ny MASTERMIND session
    - pause_session: Pause aktiv session
    - resume_session: Genoptag pauset session
    - abort_session: Afbryd session
    - issue_directive: Send direktiv til session
    - adjust_parameters: Juster session parametre
    - prioritize_agent: Prioriter specifik agent
    - approve_request: Godkend HITL request
    - reject_request: Afvis HITL request
    """

    def __init__(
        self,
        message_bus: Optional[MastermindMessageBus] = None
    ):
        self.message_bus = message_bus
        self._command_history: List[SuperAdminCommand] = []

    async def start_session(
        self,
        session_id: str,
        objective: str,
        priority: MastermindPriority = MastermindPriority.NORMAL
    ) -> SuperAdminCommand:
        """Start en MASTERMIND session."""
        command = SuperAdminCommand(
            command_id=f"cmd_{secrets.token_hex(6)}",
            command_type="start_session",
            parameters={
                "session_id": session_id,
                "objective": objective,
                "priority": priority.value
            }
        )

        if self.message_bus:
            message = create_command_message(
                session_id=session_id,
                command_type=MastermindMessageType.COMMAND_START,
                payload=command.parameters
            )
            await self.message_bus.publish(message)

        command.status = "sent"
        command.executed_at = datetime.now()
        self._command_history.append(command)

        logger.info(f"Super Admin: Start session {session_id}")
        return command

    async def pause_session(self, session_id: str) -> SuperAdminCommand:
        """Pause en session."""
        command = SuperAdminCommand(
            command_id=f"cmd_{secrets.token_hex(6)}",
            command_type="pause_session",
            parameters={"session_id": session_id}
        )

        if self.message_bus:
            message = create_command_message(
                session_id=session_id,
                command_type=MastermindMessageType.COMMAND_PAUSE,
                payload={},
                priority=MessagePriority.HIGH
            )
            await self.message_bus.publish(message)

        command.status = "sent"
        self._command_history.append(command)

        logger.info(f"Super Admin: Pause session {session_id}")
        return command

    async def resume_session(self, session_id: str) -> SuperAdminCommand:
        """Genoptag en session."""
        command = SuperAdminCommand(
            command_id=f"cmd_{secrets.token_hex(6)}",
            command_type="resume_session",
            parameters={"session_id": session_id}
        )

        if self.message_bus:
            message = create_command_message(
                session_id=session_id,
                command_type=MastermindMessageType.COMMAND_RESUME,
                payload={}
            )
            await self.message_bus.publish(message)

        command.status = "sent"
        self._command_history.append(command)

        logger.info(f"Super Admin: Resume session {session_id}")
        return command

    async def abort_session(
        self,
        session_id: str,
        reason: str = ""
    ) -> SuperAdminCommand:
        """Afbryd en session."""
        command = SuperAdminCommand(
            command_id=f"cmd_{secrets.token_hex(6)}",
            command_type="abort_session",
            parameters={"session_id": session_id, "reason": reason}
        )

        if self.message_bus:
            message = create_command_message(
                session_id=session_id,
                command_type=MastermindMessageType.COMMAND_ABORT,
                payload={"reason": reason},
                priority=MessagePriority.CRITICAL
            )
            await self.message_bus.publish(message)

        command.status = "sent"
        self._command_history.append(command)

        logger.warning(f"Super Admin: Abort session {session_id} - {reason}")
        return command

    async def issue_directive(
        self,
        session_id: str,
        directive_text: str,
        target: str = "all",
        priority: MastermindPriority = MastermindPriority.NORMAL
    ) -> SuperAdminCommand:
        """Send et direktiv til sessionen."""
        command = SuperAdminCommand(
            command_id=f"cmd_{secrets.token_hex(6)}",
            command_type="issue_directive",
            parameters={
                "session_id": session_id,
                "directive": directive_text,
                "target": target,
                "priority": priority.value
            }
        )

        if self.message_bus:
            message = create_command_message(
                session_id=session_id,
                command_type=MastermindMessageType.COMMAND_ADJUST,
                payload={
                    "directive": directive_text,
                    "target": target
                }
            )
            await self.message_bus.publish(message)

        command.status = "sent"
        self._command_history.append(command)

        logger.info(f"Super Admin: Directive issued to {target} in session {session_id}")
        return command

    async def adjust_parameters(
        self,
        session_id: str,
        parameters: Dict[str, Any]
    ) -> SuperAdminCommand:
        """Juster session parametre."""
        command = SuperAdminCommand(
            command_id=f"cmd_{secrets.token_hex(6)}",
            command_type="adjust_parameters",
            parameters={"session_id": session_id, **parameters}
        )

        if self.message_bus:
            message = create_command_message(
                session_id=session_id,
                command_type=MastermindMessageType.COMMAND_ADJUST,
                payload={"adjustments": parameters}
            )
            await self.message_bus.publish(message)

        command.status = "sent"
        self._command_history.append(command)

        logger.info(f"Super Admin: Parameters adjusted for session {session_id}")
        return command

    async def prioritize_agent(
        self,
        session_id: str,
        agent_id: str,
        priority: MastermindPriority
    ) -> SuperAdminCommand:
        """Prioriter en specifik agent."""
        command = SuperAdminCommand(
            command_id=f"cmd_{secrets.token_hex(6)}",
            command_type="prioritize_agent",
            parameters={
                "session_id": session_id,
                "agent_id": agent_id,
                "priority": priority.value
            }
        )

        if self.message_bus:
            message = create_command_message(
                session_id=session_id,
                command_type=MastermindMessageType.COMMAND_ADJUST,
                payload={
                    "action": "prioritize_agent",
                    "agent_id": agent_id,
                    "priority": priority.value
                }
            )
            await self.message_bus.publish(message)

        command.status = "sent"
        self._command_history.append(command)

        logger.info(f"Super Admin: Agent {agent_id} prioritized to {priority.value}")
        return command

    async def approve_request(
        self,
        session_id: str,
        request_id: str,
        comments: str = ""
    ) -> SuperAdminCommand:
        """Godkend en HITL request."""
        command = SuperAdminCommand(
            command_id=f"cmd_{secrets.token_hex(6)}",
            command_type="approve_request",
            parameters={
                "session_id": session_id,
                "request_id": request_id,
                "comments": comments
            }
        )

        command.status = "executed"
        self._command_history.append(command)

        logger.info(f"Super Admin: Request {request_id} approved")
        return command

    async def reject_request(
        self,
        session_id: str,
        request_id: str,
        reason: str = ""
    ) -> SuperAdminCommand:
        """Afvis en HITL request."""
        command = SuperAdminCommand(
            command_id=f"cmd_{secrets.token_hex(6)}",
            command_type="reject_request",
            parameters={
                "session_id": session_id,
                "request_id": request_id,
                "reason": reason
            }
        )

        command.status = "executed"
        self._command_history.append(command)

        logger.info(f"Super Admin: Request {request_id} rejected - {reason}")
        return command

    def get_command_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SuperAdminCommand]:
        """Hent kommando historik."""
        commands = self._command_history

        if session_id:
            commands = [
                c for c in commands
                if c.parameters.get("session_id") == session_id
            ]

        return commands[-limit:]


# =============================================================================
# SYSTEMS DIRIGENT
# =============================================================================

@dataclass
class DirigentPlan:
    """En plan oprettet af Dirigent."""
    plan_id: str
    session_id: str
    objective: str
    phases: List[Dict[str, Any]] = field(default_factory=list)
    current_phase: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "draft"

    def to_execution_plan(self) -> ExecutionPlan:
        """Konverter til ExecutionPlan."""
        return ExecutionPlan(
            plan_id=self.plan_id,
            objective=self.objective,
            phases=self.phases,
            current_phase=self.current_phase,
            created_at=self.created_at
        )


class SystemsDirigent:
    """
    Systems Dirigent (Claude) - Orkestrator for MASTERMIND.

    Ansvar:
    1. Oversættelse: Konvertér Super Admin direktiver til konkrete agent-opgaver
    2. Orkestrering: Koordinér parallel og sekventiel udførelse
    3. Syntese: Sammenfat delresultater til sammenhængende output
    4. Rapportering: Hold Super Admin informeret i realtid
    5. Optimering: Identificér flaskehalse og foreslå justeringer

    State Machine:
    AWAITING_DIRECTIVE → PLANNING → DELEGATING → MONITORING → SYNTHESIZING → REPORTING
    """

    def __init__(
        self,
        message_bus: Optional[MastermindMessageBus] = None
    ):
        self.message_bus = message_bus
        self._state = DirigentState.AWAITING_DIRECTIVE
        self._current_plan: Optional[DirigentPlan] = None
        self._active_delegations: Dict[str, str] = {}  # task_id -> agent_id
        self._collected_results: List[Dict[str, Any]] = []
        self._state_history: List[Dict[str, Any]] = []

    @property
    def state(self) -> DirigentState:
        """Aktuel tilstand."""
        return self._state

    async def transition_to(self, new_state: DirigentState) -> None:
        """Skift tilstand."""
        old_state = self._state
        self._state = new_state

        self._state_history.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"Dirigent: {old_state.value} → {new_state.value}")

    async def receive_directive(
        self,
        session: MastermindSession,
        directive: str
    ) -> DirigentPlan:
        """
        Modtag direktiv fra Super Admin og opret plan.

        Args:
            session: MASTERMIND session
            directive: Direktivtekst

        Returns:
            DirigentPlan
        """
        await self.transition_to(DirigentState.PLANNING)

        # Analyze directive and create plan
        plan = DirigentPlan(
            plan_id=f"plan_{secrets.token_hex(6)}",
            session_id=session.session_id,
            objective=directive
        )

        # Break down into phases (simplified)
        plan.phases = await self._create_phases(directive, session)
        plan.status = "ready"

        self._current_plan = plan

        logger.info(f"Dirigent: Plan oprettet med {len(plan.phases)} faser")
        return plan

    async def _create_phases(
        self,
        directive: str,
        session: MastermindSession
    ) -> List[Dict[str, Any]]:
        """
        Opret faser baseret på direktiv.

        I en fuld implementation ville dette bruge AI til at
        analysere direktivet og oprette passende faser.
        """
        # Simplified phase creation
        phases = [
            {
                "phase_id": "phase_1",
                "name": "Analyse",
                "description": "Analysér opgaven og identificér delkomponenter",
                "tasks": [],
                "status": "pending"
            },
            {
                "phase_id": "phase_2",
                "name": "Udførelse",
                "description": "Udfør de identificerede delkomponenter",
                "tasks": [],
                "status": "pending"
            },
            {
                "phase_id": "phase_3",
                "name": "Syntese",
                "description": "Sammenfat resultater",
                "tasks": [],
                "status": "pending"
            }
        ]

        return phases

    async def delegate_tasks(
        self,
        session: MastermindSession,
        tasks: List[MastermindTask],
        available_agents: List[str]
    ) -> Dict[str, str]:
        """
        Delegér opgaver til tilgængelige agenter.

        Args:
            session: MASTERMIND session
            tasks: Opgaver at delegere
            available_agents: Tilgængelige agent IDs

        Returns:
            Dict mapping task_id -> agent_id
        """
        await self.transition_to(DirigentState.DELEGATING)

        delegations = {}

        for task in tasks:
            if not available_agents:
                break

            # Simple round-robin delegation
            agent_id = available_agents.pop(0)
            delegations[task.task_id] = agent_id

            # Send directive to agent
            if self.message_bus:
                message = create_directive_message(
                    session_id=session.session_id,
                    directive_type=MastermindMessageType.DIRECTIVE_ASSIGN,
                    target_agent=agent_id,
                    payload={
                        "task_id": task.task_id,
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority.value
                    }
                )
                await self.message_bus.publish(message)

            self._active_delegations[task.task_id] = agent_id

        await self.transition_to(DirigentState.MONITORING)

        logger.info(f"Dirigent: {len(delegations)} opgaver delegeret")
        return delegations

    async def collect_result(
        self,
        task_id: str,
        agent_id: str,
        result: Any
    ) -> None:
        """Indsaml resultat fra agent."""
        self._collected_results.append({
            "task_id": task_id,
            "agent_id": agent_id,
            "result": result,
            "collected_at": datetime.now().isoformat()
        })

        # Remove from active delegations
        if task_id in self._active_delegations:
            del self._active_delegations[task_id]

        logger.debug(f"Dirigent: Resultat indsamlet fra {agent_id} for {task_id}")

    async def synthesize_results(self) -> Dict[str, Any]:
        """
        Syntesér indsamlede resultater.

        Returns:
            Syntetiseret resultat
        """
        await self.transition_to(DirigentState.SYNTHESIZING)

        # In a full implementation, this would use AI to synthesize results
        synthesis = {
            "synthesis_id": f"syn_{secrets.token_hex(6)}",
            "total_results": len(self._collected_results),
            "results": self._collected_results,
            "summary": f"Syntetiseret {len(self._collected_results)} resultater",
            "synthesized_at": datetime.now().isoformat()
        }

        logger.info(f"Dirigent: Resultater syntetiseret")
        return synthesis

    async def report_to_super_admin(
        self,
        session: MastermindSession,
        report_type: str = "progress"
    ) -> Dict[str, Any]:
        """
        Rapportér til Super Admin.

        Args:
            session: MASTERMIND session
            report_type: Type af rapport ("progress", "completion", "issue")

        Returns:
            Rapport data
        """
        await self.transition_to(DirigentState.REPORTING)

        report = {
            "report_id": f"rep_{secrets.token_hex(6)}",
            "session_id": session.session_id,
            "report_type": report_type,
            "current_state": self._state.value,
            "active_delegations": len(self._active_delegations),
            "collected_results": len(self._collected_results),
            "plan_phase": self._current_plan.current_phase if self._current_plan else 0,
            "timestamp": datetime.now().isoformat()
        }

        if self.message_bus:
            message = MastermindMessage(
                message_id=f"msg_{secrets.token_hex(8)}",
                session_id=session.session_id,
                message_type=MastermindMessageType.FEEDBACK_REPORT,
                source="dirigent",
                destination="super_admin",
                payload=report,
                priority=MessagePriority.NORMAL
            )
            await self.message_bus.publish(message)

        await self.transition_to(DirigentState.AWAITING_DIRECTIVE)

        logger.info(f"Dirigent: Rapport sendt til Super Admin")
        return report

    async def reallocate_resources(
        self,
        session: MastermindSession,
        reason: str
    ) -> bool:
        """
        Omallokér ressourcer baseret på aktuel status.

        Args:
            session: MASTERMIND session
            reason: Årsag til omallokering

        Returns:
            True hvis succesfuldt
        """
        if self.message_bus:
            message = create_directive_message(
                session_id=session.session_id,
                directive_type=MastermindMessageType.DIRECTIVE_REALLOCATE,
                target_agent="all",
                payload={"reason": reason}
            )
            await self.message_bus.publish(message)

        logger.info(f"Dirigent: Ressourcer omallokeret - {reason}")
        return True

    def get_state_history(self) -> List[Dict[str, Any]]:
        """Hent state historik."""
        return self._state_history.copy()


# =============================================================================
# MASTERMIND-CAPABLE AGENT MIXIN
# =============================================================================

class MastermindCapableAgent:
    """
    Mixin til agenter der kan deltage i MASTERMIND sessions.

    Tilføjer:
    - enter_mastermind_mode()
    - exit_mastermind_mode()
    - report_progress()
    - receive_adjustment()
    """

    def __init__(self):
        self._mastermind_session: Optional[str] = None
        self._reporting_interval = 5  # sekunder
        self._auto_share_partial = True
        self._mastermind_priority = MastermindPriority.NORMAL
        self._adjustment_history: List[Dict[str, Any]] = []

    @property
    def in_mastermind_mode(self) -> bool:
        """Er agenten i MASTERMIND mode."""
        return self._mastermind_session is not None

    def enter_mastermind_mode(
        self,
        session_id: str,
        priority: MastermindPriority = MastermindPriority.NORMAL,
        reporting_interval: int = 5
    ) -> None:
        """
        Skift til MASTERMIND mode.

        Args:
            session_id: MASTERMIND session ID
            priority: Prioritet
            reporting_interval: Interval for progress rapportering
        """
        self._mastermind_session = session_id
        self._mastermind_priority = priority
        self._reporting_interval = reporting_interval
        self._auto_share_partial = True

        logger.info(f"Agent entered MASTERMIND mode for session {session_id}")

    def exit_mastermind_mode(self) -> None:
        """Afslut MASTERMIND mode."""
        session_id = self._mastermind_session
        self._mastermind_session = None
        self._mastermind_priority = MastermindPriority.NORMAL
        self._auto_share_partial = False

        logger.info(f"Agent exited MASTERMIND mode (was session {session_id})")

    async def report_progress(
        self,
        progress: float,
        partial_result: Optional[Any] = None,
        message_bus: Optional[MastermindMessageBus] = None
    ) -> bool:
        """
        Rapportér fremskridt til Mastermindrummet.

        Args:
            progress: Fremskridt (0.0-1.0)
            partial_result: Eventuelt delresultat
            message_bus: Message bus

        Returns:
            True hvis sendt succesfuldt
        """
        if not self._mastermind_session:
            return False

        payload = {
            "progress": progress,
            "partial_result": partial_result,
            "timestamp": datetime.now().isoformat()
        }

        if message_bus:
            message = MastermindMessage(
                message_id=f"msg_{secrets.token_hex(8)}",
                session_id=self._mastermind_session,
                message_type=MastermindMessageType.STATUS_TASK_PROGRESS,
                source="agent",  # Would be actual agent_id
                destination="dirigent",
                payload=payload
            )
            await message_bus.publish(message)

        return True

    def receive_adjustment(
        self,
        adjustment: Directive
    ) -> bool:
        """
        Modtag og anvend justering fra Dirigent.

        Args:
            adjustment: Direktiv med justering

        Returns:
            True hvis anvendt succesfuldt
        """
        self._adjustment_history.append({
            "directive_id": adjustment.directive_id,
            "content": adjustment.content,
            "received_at": datetime.now().isoformat()
        })

        # Apply adjustments
        if "priority" in adjustment.content:
            self._mastermind_priority = MastermindPriority(adjustment.content["priority"])

        if "reporting_interval" in adjustment.content:
            self._reporting_interval = adjustment.content["reporting_interval"]

        logger.info(f"Agent received adjustment: {adjustment.directive_id}")
        return True

    def get_adjustment_history(self) -> List[Dict[str, Any]]:
        """Hent justering historik."""
        return self._adjustment_history.copy()


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_super_admin_interface(
    message_bus: Optional[MastermindMessageBus] = None
) -> SuperAdminInterface:
    """Opret Super Admin interface."""
    return SuperAdminInterface(message_bus=message_bus)


def create_systems_dirigent(
    message_bus: Optional[MastermindMessageBus] = None
) -> SystemsDirigent:
    """Opret Systems Dirigent."""
    return SystemsDirigent(message_bus=message_bus)
