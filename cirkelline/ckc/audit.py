#!/usr/bin/env python3
"""
CKC FASE III - Systemaudit & Perfektionering
=============================================

Dybdegående audit af alle CKC komponenter med fokus på:
- Kompromisløs komplethed
- Fejlfri præcision
- Robusthed og sikkerhed
- Læringscontinuum

Kør audit med:
    python3 cirkelline/ckc/audit.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cirkelline.ckc.learning_rooms import (
    get_room_manager,
    initialize_default_rooms,
    RoomStatus,
    LearningRoom,
)
from cirkelline.ckc.orchestrator import (
    get_orchestrator,
    TaskPriority,
    TaskStatus,
    AgentCapability,
)
from cirkelline.ckc.agents import create_all_agents
from cirkelline.ckc.kommandanter import (
    get_historiker,
    get_bibliotekar,
    HistoricalEventType,
    KnowledgeCategory,
)
from cirkelline.ckc.dashboard import get_dashboard_manager, StatusLevel
from cirkelline.ckc.security import get_sanitizer, InputType, ThreatLevel
from cirkelline.ckc.advanced_protocols import (
    get_security_manager,
    get_ilcp_manager,
    get_terminal,
    SecurityLevel,
    MessageType,
    MessagePriority,
    AuthorizationLevel,
)


class AuditStatus(Enum):
    """Status for et audit punkt."""
    PASSED = "FULDT VERIFICERET"
    WARNING = "KRÆVER JUSTERING"
    FAILED = "KRITISK FEJL"
    PENDING = "UNDER TEST"


@dataclass
class AuditResult:
    """Resultat af en audit test."""
    component: str
    test_name: str
    status: AuditStatus
    details: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "test_name": self.test_name,
            "status": self.status.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "recommendations": self.recommendations,
            "metrics": self.metrics
        }


class Colors:
    """ANSI farver."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def print_header(title: str) -> None:
    print(f"\n{Colors.CYAN}{'═' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'═' * 80}{Colors.RESET}")


def print_section(title: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {title}{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}")


def print_result(result: AuditResult) -> None:
    """Print audit resultat."""
    status_colors = {
        AuditStatus.PASSED: Colors.GREEN,
        AuditStatus.WARNING: Colors.YELLOW,
        AuditStatus.FAILED: Colors.RED,
        AuditStatus.PENDING: Colors.BLUE,
    }
    color = status_colors.get(result.status, Colors.RESET)
    status_icon = {
        AuditStatus.PASSED: "✓",
        AuditStatus.WARNING: "⚠",
        AuditStatus.FAILED: "✗",
        AuditStatus.PENDING: "○",
    }

    print(f"  {color}{status_icon[result.status]} {result.test_name}: {result.status.value}{Colors.RESET}")
    if result.details:
        print(f"    {Colors.DIM}{result.details}{Colors.RESET}")
    if result.recommendations:
        for rec in result.recommendations:
            print(f"    {Colors.YELLOW}→ {rec}{Colors.RESET}")


class CKCAudit:
    """
    CKC System Audit Framework.

    Udfører dybdegående audit af alle CKC komponenter.
    """

    def __init__(self):
        self.results: List[AuditResult] = []
        self.started_at = datetime.now(timezone.utc)

        # Initialize managers
        self.room_manager = get_room_manager()
        self.orchestrator = get_orchestrator()
        self.dashboard = get_dashboard_manager()
        self.security_manager = get_security_manager()
        self.ilcp_manager = get_ilcp_manager()
        self.super_admin = get_terminal()
        self.historiker = get_historiker()
        self.bibliotekar = get_bibliotekar()
        self.sanitizer = get_sanitizer()
        self.agents = create_all_agents()

        self.initialized = False

    async def initialize(self) -> None:
        """Initialiser systemet til audit."""
        print(f"{Colors.CYAN}Initialiserer CKC til audit...{Colors.RESET}")

        # Initialiser læringsrum
        await initialize_default_rooms(owner="audit_system")

        # Registrer rum i security manager og ILCP
        rooms = await self.room_manager.list_rooms()
        for room in rooms:
            await self.security_manager.register_room(room.room_id)
            await self.ilcp_manager.register_room_capabilities(
                room.room_id,
                {"general", room.name.lower().replace(" ", "_")}
            )

        # Registrer agenter
        room_id = 2
        for agent_id, agent in self.agents.items():
            await self.orchestrator.register_agent(
                agent_id=agent.agent_id,
                name=agent.name,
                description=agent.description,
                capabilities=agent.capabilities,
                learning_room_id=room_id
            )
            room_id += 1

        self.initialized = True
        print(f"{Colors.GREEN}✓ System initialiseret til audit{Colors.RESET}")

    def add_result(self, result: AuditResult) -> None:
        """Tilføj et audit resultat."""
        self.results.append(result)
        print_result(result)

    # ═══════════════════════════════════════════════════════════════
    # FASE III.1: SYSTEMISK KOMPLETTHEDS- & FUNKTIONALITETSAUDIT
    # ═══════════════════════════════════════════════════════════════

    async def audit_phase_1(self) -> Dict[str, Any]:
        """Kør Fase III.1 audit."""
        print_header("FASE III.1: SYSTEMISK KOMPLETTHEDS- & FUNKTIONALITETSAUDIT")

        phase_results = {
            "orchestrator": await self.audit_1_1_orchestrator(),
            "learning_rooms": await self.audit_1_2_learning_rooms(),
            "agents": await self.audit_1_3_agents(),
            "kommandanter": await self.audit_1_4_kommandanter(),
            "security_protocols": await self.audit_1_5_security_protocols(),
            "dashboard": await self.audit_1_6_dashboard(),
        }

        return phase_results

    async def audit_1_1_orchestrator(self) -> Dict[str, Any]:
        """1.1 CKC Orchestrator Audit."""
        print_section("1.1 CKC ORCHESTRATOR - HJERTE OG HJERNE")

        results = {}

        # Test 1: Orchestrator aktiv
        try:
            status = await self.orchestrator.get_status()
            if status["status"] == "operational":
                self.add_result(AuditResult(
                    component="Orchestrator",
                    test_name="Orchestrator Aktivitet",
                    status=AuditStatus.PASSED,
                    details=f"Orchestrator er operativ med {status['agents']['total']} agenter",
                    metrics=status
                ))
                results["active"] = True
            else:
                self.add_result(AuditResult(
                    component="Orchestrator",
                    test_name="Orchestrator Aktivitet",
                    status=AuditStatus.FAILED,
                    details="Orchestrator er ikke operativ"
                ))
                results["active"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Orchestrator",
                test_name="Orchestrator Aktivitet",
                status=AuditStatus.FAILED,
                details=f"Fejl ved test: {e}"
            ))
            results["active"] = False

        # Test 2: Task Decomposition
        try:
            task = await self.orchestrator.create_task(
                description="Test task for audit - verificer task decomposition",
                priority=TaskPriority.MEDIUM,
                source="audit",
                requires_validation=True
            )

            subtasks = await self.orchestrator.decompose_task(
                task,
                ["Subtask 1: Analyse", "Subtask 2: Implementering", "Subtask 3: Validering"]
            )

            if len(subtasks) == 3 and all(st.parent_task_id == task.id for st in subtasks):
                self.add_result(AuditResult(
                    component="Orchestrator",
                    test_name="Task Decomposition",
                    status=AuditStatus.PASSED,
                    details=f"Task dekomponeret til {len(subtasks)} subtasks korrekt",
                    metrics={"task_id": task.id, "subtask_count": len(subtasks)}
                ))
                results["decomposition"] = True
            else:
                self.add_result(AuditResult(
                    component="Orchestrator",
                    test_name="Task Decomposition",
                    status=AuditStatus.WARNING,
                    details="Task decomposition delvist funktionel",
                    recommendations=["Verificer parent-child relationer"]
                ))
                results["decomposition"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Orchestrator",
                test_name="Task Decomposition",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["decomposition"] = False

        # Test 3: Validation Flow
        try:
            flow = await self.orchestrator.create_validation_flow(
                content={"test": "audit_data"},
                source_room_id=1,
                source_room_name="Audit Room",
                content_type="test_data"
            )

            if flow.current_stage == "learning_room" and flow.id:
                self.add_result(AuditResult(
                    component="Orchestrator",
                    test_name="Validation Flow Oprettelse",
                    status=AuditStatus.PASSED,
                    details=f"ValidationFlow oprettet: {flow.id}",
                    metrics={"flow_id": flow.id, "stage": flow.current_stage}
                ))
                results["validation_flow"] = True
            else:
                self.add_result(AuditResult(
                    component="Orchestrator",
                    test_name="Validation Flow Oprettelse",
                    status=AuditStatus.WARNING,
                    details="ValidationFlow oprettet men med uventet tilstand"
                ))
                results["validation_flow"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Orchestrator",
                test_name="Validation Flow Oprettelse",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["validation_flow"] = False

        # Test 4: Agent Routing
        try:
            agents = await self.orchestrator.list_agents()
            if len(agents) >= 5:
                self.add_result(AuditResult(
                    component="Orchestrator",
                    test_name="Agent Registrering",
                    status=AuditStatus.PASSED,
                    details=f"{len(agents)} agenter registreret og tilgængelige",
                    metrics={"agent_count": len(agents)}
                ))
                results["agent_routing"] = True
            else:
                self.add_result(AuditResult(
                    component="Orchestrator",
                    test_name="Agent Registrering",
                    status=AuditStatus.WARNING,
                    details=f"Kun {len(agents)} agenter registreret (forventet: 5+)",
                    recommendations=["Registrer manglende agenter"]
                ))
                results["agent_routing"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Orchestrator",
                test_name="Agent Registrering",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["agent_routing"] = False

        return results

    async def audit_1_2_learning_rooms(self) -> Dict[str, Any]:
        """1.2 Læringsrum Audit."""
        print_section("1.2 LÆRINGSRUM - ISOLERING OG LÆRINGSENHEDER")

        results = {}

        # Test 1: Alle rum oprettet
        rooms = await self.room_manager.list_rooms()
        if len(rooms) >= 10:
            self.add_result(AuditResult(
                component="LearningRooms",
                test_name="Rum Oprettelse",
                status=AuditStatus.PASSED,
                details=f"{len(rooms)} læringsrum oprettet",
                metrics={"room_count": len(rooms)}
            ))
            results["rooms_created"] = True
        else:
            self.add_result(AuditResult(
                component="LearningRooms",
                test_name="Rum Oprettelse",
                status=AuditStatus.WARNING,
                details=f"Kun {len(rooms)} rum oprettet (forventet: 10)"
            ))
            results["rooms_created"] = False

        # Test 2: Room Status
        status_counts = {"blue": 0, "green": 0, "yellow": 0, "red": 0}
        for room in rooms:
            status_counts[room.status.value] += 1

        healthy_count = status_counts["blue"] + status_counts["green"]
        if healthy_count == len(rooms):
            self.add_result(AuditResult(
                component="LearningRooms",
                test_name="Room Status Health",
                status=AuditStatus.PASSED,
                details=f"Alle {len(rooms)} rum er sunde (blå/grøn)",
                metrics=status_counts
            ))
            results["all_healthy"] = True
        elif status_counts["red"] > 0:
            self.add_result(AuditResult(
                component="LearningRooms",
                test_name="Room Status Health",
                status=AuditStatus.FAILED,
                details=f"{status_counts['red']} rum har kritisk status",
                recommendations=["Undersøg røde rum øjeblikkeligt"]
            ))
            results["all_healthy"] = False
        else:
            self.add_result(AuditResult(
                component="LearningRooms",
                test_name="Room Status Health",
                status=AuditStatus.WARNING,
                details=f"{status_counts['yellow']} rum har advarsler",
                metrics=status_counts
            ))
            results["all_healthy"] = False

        # Test 3: Room Isolation
        for room in rooms[:3]:  # Test de første 3 rum
            if room.integrity_verified:
                self.add_result(AuditResult(
                    component="LearningRooms",
                    test_name=f"Rum #{room.room_id} Integritet",
                    status=AuditStatus.PASSED,
                    details=f"{room.name} har verificeret integritet"
                ))

        results["integrity_verified"] = all(r.integrity_verified for r in rooms)

        # Test 4: Validation Flow i rum
        room = rooms[0] if rooms else None
        if room:
            flow = room.start_validation({"test": "data"}, "audit")
            if flow.id and flow.state.value == "in_learning_room":
                self.add_result(AuditResult(
                    component="LearningRooms",
                    test_name="Room Validation Flow",
                    status=AuditStatus.PASSED,
                    details=f"Validation flow fungerer i rum #{room.room_id}"
                ))
                results["validation_in_room"] = True
            else:
                results["validation_in_room"] = False

        return results

    async def audit_1_3_agents(self) -> Dict[str, Any]:
        """1.3 Specialiserede Agenter Audit."""
        print_section("1.3 SPECIALISEREDE AGENTER - EKSPERTISE OG INTEGRITET")

        results = {}
        expected_agents = [
            ("tool_explorer", "Tool Explorer & Integrator"),
            ("creative_synthesizer", "Creative Synthesizer"),
            ("knowledge_architect", "Knowledge Architect & Educator"),
            ("virtual_world_builder", "Virtual World Builder"),
            ("quality_assurance", "Quality Assurance & Self-Corrector"),
        ]

        for agent_key, expected_name in expected_agents:
            agent = self.agents.get(agent_key)
            if agent:
                # Test agent process
                try:
                    test_result = await agent.process(
                        {"action": "monitor" if agent_key == "tool_explorer" else "review"},
                        context={"audit": True}
                    )

                    if test_result.success:
                        self.add_result(AuditResult(
                            component="Agents",
                            test_name=f"{expected_name} Funktionalitet",
                            status=AuditStatus.PASSED,
                            details=f"Agent fungerer med confidence: {test_result.confidence:.2f}",
                            metrics={"confidence": test_result.confidence}
                        ))
                        results[agent_key] = True
                    else:
                        self.add_result(AuditResult(
                            component="Agents",
                            test_name=f"{expected_name} Funktionalitet",
                            status=AuditStatus.WARNING,
                            details="Agent svarede men med fejl"
                        ))
                        results[agent_key] = False
                except Exception as e:
                    self.add_result(AuditResult(
                        component="Agents",
                        test_name=f"{expected_name} Funktionalitet",
                        status=AuditStatus.FAILED,
                        details=f"Fejl: {e}"
                    ))
                    results[agent_key] = False
            else:
                self.add_result(AuditResult(
                    component="Agents",
                    test_name=f"{expected_name} Eksistens",
                    status=AuditStatus.FAILED,
                    details=f"Agent '{agent_key}' ikke fundet"
                ))
                results[agent_key] = False

        return results

    async def audit_1_4_kommandanter(self) -> Dict[str, Any]:
        """1.4 Kommandanter Audit."""
        print_section("1.4 KOMMANDANTER - HISTORISK OG VIDENSFORVALTNING")

        results = {}

        # Test Historiker
        try:
            await self.historiker.record_event(
                HistoricalEventType.SYSTEM_START,
                "Audit test event",
                "audit_system",
                importance=3
            )
            stats = await self.historiker.get_statistics()

            if stats["total_events"] > 0:
                self.add_result(AuditResult(
                    component="Kommandanter",
                    test_name="Historiker-Kommandant",
                    status=AuditStatus.PASSED,
                    details=f"Aktiv med {stats['total_events']} events logget",
                    metrics=stats
                ))
                results["historiker"] = True
            else:
                results["historiker"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Kommandanter",
                test_name="Historiker-Kommandant",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["historiker"] = False

        # Test Bibliotekar
        try:
            entry = await self.bibliotekar.add_entry(
                title="Audit Test Entry",
                content={"type": "test", "data": "audit verification"},
                category=KnowledgeCategory.OPERATIONAL,
                created_by="audit_system",
                tags={"audit", "test"}
            )
            stats = await self.bibliotekar.get_statistics()

            if stats["total_entries"] > 0:
                self.add_result(AuditResult(
                    component="Kommandanter",
                    test_name="Bibliotekar-Kommandant",
                    status=AuditStatus.PASSED,
                    details=f"Aktiv med {stats['total_entries']} entries",
                    metrics=stats
                ))
                results["bibliotekar"] = True
            else:
                results["bibliotekar"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Kommandanter",
                test_name="Bibliotekar-Kommandant",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["bibliotekar"] = False

        return results

    async def audit_1_5_security_protocols(self) -> Dict[str, Any]:
        """1.5 Sikkerhedsmoduler og Avancerede Protokoller."""
        print_section("1.5 SIKKERHEDSMODULER OG AVANCEREDE PROTOKOLLER")

        results = {}

        # Test 5.1: DynamicSecurityManager
        try:
            room_security = await self.security_manager.get_room_security(1)
            if room_security:
                self.add_result(AuditResult(
                    component="Security",
                    test_name="5.1 DynamicSecurityManager",
                    status=AuditStatus.PASSED,
                    details=f"Aktiv - rum 1 niveau: {room_security['state']['current_level']}",
                    metrics=room_security
                ))
                results["dynamic_security"] = True
            else:
                results["dynamic_security"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Security",
                test_name="5.1 DynamicSecurityManager",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["dynamic_security"] = False

        # Test Fail-Safe
        try:
            # Registrer fejlfri operation først
            await self.security_manager.record_operation(1, success=True)
            # Simuler fejl
            await self.security_manager.record_operation(1, success=False)
            # Check rollback
            security_after = await self.security_manager.get_room_security(1)
            if security_after and security_after["state"]["current_level"] == "high":
                self.add_result(AuditResult(
                    component="Security",
                    test_name="5.1 Fail-Safe Rollback",
                    status=AuditStatus.PASSED,
                    details="Sikkerhed rullet tilbage til HIGH ved fejl"
                ))
                results["fail_safe"] = True
            else:
                results["fail_safe"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Security",
                test_name="5.1 Fail-Safe Rollback",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["fail_safe"] = False

        # Test 5.2: ILCP
        try:
            msg = await self.ilcp_manager.send_message(
                sender_room_id=1,
                recipient_room_id=2,
                message_type=MessageType.STATUS_UPDATE,
                content={"audit": "test"},
                priority=MessagePriority.NORMAL
            )
            stats = await self.ilcp_manager.get_communication_stats()

            if msg.id and stats["total_messages"] > 0:
                self.add_result(AuditResult(
                    component="Security",
                    test_name="5.2 ILCP Kommunikation",
                    status=AuditStatus.PASSED,
                    details=f"Aktiv - {stats['total_messages']} beskeder sendt",
                    metrics=stats
                ))
                results["ilcp"] = True
            else:
                results["ilcp"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Security",
                test_name="5.2 ILCP Kommunikation",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["ilcp"] = False

        # Test 5.3: EIAP
        try:
            term_status = await self.super_admin.get_terminal_status()
            if term_status["status"] == "operational":
                self.add_result(AuditResult(
                    component="Security",
                    test_name="5.3 EIAP/Super-Admin Terminal",
                    status=AuditStatus.PASSED,
                    details="Terminal operativ",
                    metrics=term_status
                ))
                results["eiap"] = True
            else:
                results["eiap"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Security",
                test_name="5.3 EIAP/Super-Admin Terminal",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["eiap"] = False

        # Test HITL Flow
        try:
            hitl_req = await self.super_admin.request_hitl_approval(
                action_type="audit_test",
                description="Test HITL flow under audit",
                requested_by="audit_system",
                target_resource="test_resource",
                risk_level="low"
            )
            pending = await self.super_admin.get_pending_hitl_requests()

            if hitl_req.id and len(pending) > 0:
                self.add_result(AuditResult(
                    component="Security",
                    test_name="5.3 HITL Flow",
                    status=AuditStatus.PASSED,
                    details=f"HITL request oprettet: {hitl_req.id}"
                ))
                results["hitl"] = True

                # Clean up - approve test request
                await self.super_admin.approve_hitl_request(hitl_req.id, "audit_system")
            else:
                results["hitl"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Security",
                test_name="5.3 HITL Flow",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["hitl"] = False

        # Test Input Sanitizer
        try:
            sanitize_result = await self.sanitizer.sanitize(
                "Normal test input for audit",
                InputType.TEXT
            )
            if sanitize_result.is_safe:
                self.add_result(AuditResult(
                    component="Security",
                    test_name="Input Sanitizer",
                    status=AuditStatus.PASSED,
                    details=f"Fungerer - threat level: {sanitize_result.threat_level.value}"
                ))
                results["sanitizer"] = True
            else:
                results["sanitizer"] = False
        except Exception as e:
            self.add_result(AuditResult(
                component="Security",
                test_name="Input Sanitizer",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["sanitizer"] = False

        return results

    async def audit_1_6_dashboard(self) -> Dict[str, Any]:
        """1.6 Dashboard Audit."""
        print_section("1.6 CKC DASHBOARD - VISUEL STATUS")

        results = {}

        try:
            # Registrer test komponenter
            await self.dashboard.register_component(
                "audit_test",
                "Audit Test Component",
                StatusLevel.BLUE
            )

            overview = await self.dashboard.get_status_overview()

            if overview["total_components"] > 0:
                self.add_result(AuditResult(
                    component="Dashboard",
                    test_name="Dashboard Overview",
                    status=AuditStatus.PASSED,
                    details=f"{overview['total_components']} komponenter registreret",
                    metrics=overview
                ))
                results["overview"] = True
            else:
                results["overview"] = False

            # Test status update
            await self.dashboard.update_status("audit_test", StatusLevel.GREEN)
            dot = await self.dashboard.get_status_dot("audit_test")
            if dot and dot.status == StatusLevel.GREEN:
                self.add_result(AuditResult(
                    component="Dashboard",
                    test_name="Status Update",
                    status=AuditStatus.PASSED,
                    details="Status opdatering fungerer"
                ))
                results["status_update"] = True
            else:
                results["status_update"] = False

            # Test Acute Notifications
            await self.dashboard.acute_notifications.add_notification(
                message="Audit test notification",
                severity="warning",
                source="audit_system"
            )
            acute_data = await self.dashboard.acute_notifications.get_page_data()
            if acute_data["total_active"] > 0:
                self.add_result(AuditResult(
                    component="Dashboard",
                    test_name="Acute Notifications",
                    status=AuditStatus.PASSED,
                    details=f"{acute_data['total_active']} aktive notifikationer"
                ))
                results["acute"] = True
            else:
                results["acute"] = False

        except Exception as e:
            self.add_result(AuditResult(
                component="Dashboard",
                test_name="Dashboard",
                status=AuditStatus.FAILED,
                details=f"Fejl: {e}"
            ))
            results["overview"] = False

        return results

    # ═══════════════════════════════════════════════════════════════
    # REPORT GENERATION
    # ═══════════════════════════════════════════════════════════════

    def generate_report(self) -> Dict[str, Any]:
        """Generer samlet audit rapport."""
        passed = sum(1 for r in self.results if r.status == AuditStatus.PASSED)
        warnings = sum(1 for r in self.results if r.status == AuditStatus.WARNING)
        failed = sum(1 for r in self.results if r.status == AuditStatus.FAILED)

        overall_status = "FEJLFRI DRIFT" if failed == 0 and warnings == 0 else \
                         "KRÆVER OPMÆRKSOMHED" if failed == 0 else "KRITISKE FEJL"

        return {
            "audit_id": f"audit_{self.started_at.strftime('%Y%m%d_%H%M%S')}",
            "started_at": self.started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": (datetime.now(timezone.utc) - self.started_at).total_seconds(),
            "overall_status": overall_status,
            "summary": {
                "total_tests": len(self.results),
                "passed": passed,
                "warnings": warnings,
                "failed": failed,
                "pass_rate": f"{(passed / len(self.results) * 100):.1f}%" if self.results else "0%"
            },
            "results": [r.to_dict() for r in self.results],
            "recommendations": [
                rec for r in self.results
                for rec in r.recommendations
            ]
        }

    def print_summary(self) -> None:
        """Print audit summary."""
        report = self.generate_report()

        print_header("AUDIT RAPPORT - SAMMENFATNING")

        # Overall status
        status_color = Colors.GREEN if report["overall_status"] == "FEJLFRI DRIFT" else \
                       Colors.YELLOW if report["overall_status"] == "KRÆVER OPMÆRKSOMHED" else Colors.RED

        print(f"\n  {Colors.BOLD}Overall Status: {status_color}{report['overall_status']}{Colors.RESET}")
        print(f"\n  {Colors.DIM}Audit ID: {report['audit_id']}{Colors.RESET}")
        print(f"  {Colors.DIM}Varighed: {report['duration_seconds']:.2f} sekunder{Colors.RESET}")

        # Summary
        print_section("RESULTATER")
        print(f"  Total Tests: {report['summary']['total_tests']}")
        print(f"  {Colors.GREEN}Passed: {report['summary']['passed']}{Colors.RESET}")
        print(f"  {Colors.YELLOW}Warnings: {report['summary']['warnings']}{Colors.RESET}")
        print(f"  {Colors.RED}Failed: {report['summary']['failed']}{Colors.RESET}")
        print(f"  Pass Rate: {report['summary']['pass_rate']}")

        # Recommendations
        if report["recommendations"]:
            print_section("ANBEFALINGER")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")

        print(f"\n{Colors.CYAN}{'═' * 80}{Colors.RESET}\n")


async def run_full_audit() -> Dict[str, Any]:
    """Kør komplet system audit."""
    print(f"""
{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   {Colors.BOLD}CKC FASE III - DYBDEGÅENDE SYSTEMAUDIT{Colors.RESET}{Colors.CYAN}                               ║
║   {Colors.DIM}Kompromisløs Komplethed & Fejlfri Præcision{Colors.RESET}{Colors.CYAN}                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}""")

    audit = CKCAudit()
    await audit.initialize()

    # Run Phase III.1
    await audit.audit_phase_1()

    # Generate and print report
    audit.print_summary()
    report = audit.generate_report()

    return report


def main():
    """Main entry point."""
    asyncio.run(run_full_audit())


if __name__ == "__main__":
    main()
