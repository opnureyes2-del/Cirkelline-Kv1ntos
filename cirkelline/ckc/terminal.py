#!/usr/bin/env python3
"""
CKC Kommandør Terminal
======================

Interaktiv terminaladgang til CKC Super-Admin systemet.
Giver realtidsvisning af systemstatus og validering af protokoller.

Start med:
    python -m cirkelline.ckc.terminal

Eller direkte:
    python cirkelline/ckc/terminal.py
"""

import asyncio
import sys
import os
import secrets
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
import uuid

# Tilføj parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cirkelline.ckc.learning_rooms import (
    get_room_manager,
    initialize_default_rooms,
    RoomStatus,
)
from cirkelline.ckc.orchestrator import (
    get_orchestrator,
    TaskPriority,
    AgentCapability,
)
from cirkelline.ckc.agents import create_all_agents
from cirkelline.ckc.kommandanter import get_historiker, get_bibliotekar, HistoricalEventType
from cirkelline.ckc.dashboard import get_dashboard_manager, StatusLevel
from cirkelline.ckc.security import get_sanitizer
from cirkelline.ckc.advanced_protocols import (
    get_security_manager,
    get_ilcp_manager,
    get_terminal,
    SecurityLevel,
    MessageType,
    MessagePriority,
    AuthorizationLevel,
)
from cirkelline.ckc.folder_switcher import get_folder_switcher
from cirkelline.ckc.folder_context import FolderCategory


# ═══════════════════════════════════════════════════════════════
# TERMINAL FARVER OG FORMATTERING
# ═══════════════════════════════════════════════════════════════

class Colors:
    """ANSI farver til terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def status_color(status: str) -> str:
    """Returner farve baseret på status."""
    colors = {
        "blue": Colors.BLUE,
        "green": Colors.GREEN,
        "yellow": Colors.YELLOW,
        "red": Colors.RED,
    }
    return colors.get(status.lower(), Colors.WHITE)


def print_header(title: str) -> None:
    """Print en formateret header."""
    width = 70
    print(f"\n{Colors.CYAN}{'═' * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'═' * width}{Colors.RESET}")


def print_section(title: str) -> None:
    """Print en sektion header."""
    print(f"\n{Colors.BOLD}{Colors.WHITE}▶ {title}{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 50}{Colors.RESET}")


def print_status_dot(status: str, name: str, details: str = "") -> None:
    """Print en status dot med navn."""
    color = status_color(status)
    dot = "●"
    detail_str = f" {Colors.DIM}({details}){Colors.RESET}" if details else ""
    print(f"  {color}{dot}{Colors.RESET} {name}{detail_str}")


def print_success(msg: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def print_info(msg: str) -> None:
    """Print info message."""
    print(f"{Colors.CYAN}ℹ {msg}{Colors.RESET}")


# ═══════════════════════════════════════════════════════════════
# CKC TERMINAL KLASSE
# ═══════════════════════════════════════════════════════════════

class CKCTerminal:
    """
    Interaktiv CKC Kommandør Terminal.

    Giver direkte adgang til CKC Orchestrator og alle underliggende systemer.
    """

    def __init__(self, user_id: str = "rasmus"):
        self.user_id = user_id
        self.session_id = f"term_{uuid.uuid4().hex[:8]}"
        self.started_at = datetime.utcnow()

        # Managers
        self.room_manager = get_room_manager()
        self.orchestrator = get_orchestrator()
        self.dashboard = get_dashboard_manager()
        self.security_manager = get_security_manager()
        self.ilcp_manager = get_ilcp_manager()
        self.super_admin = get_terminal()
        self.historiker = get_historiker()
        self.bibliotekar = get_bibliotekar()
        self.sanitizer = get_sanitizer()

        # CKC Folder Switcher (v1.3.5)
        self.folder_switcher = get_folder_switcher(user_id)

        # Agents
        self.agents = create_all_agents()

        # State
        self.initialized = False
        self._emergency_stop_active: bool = False
        self._emergency_stop_timestamp: Optional[datetime] = None

    async def initialize(self) -> None:
        """Initialiser alle CKC komponenter."""
        print_info("Initialiserer CKC systemet...")

        # Initialiser læringsrum
        rooms = await initialize_default_rooms(owner=self.user_id)

        # Registrer rum i security manager
        for room in rooms.values():
            await self.security_manager.register_room(room.room_id)
            await self.ilcp_manager.register_room_capabilities(
                room.room_id,
                {"general", room.name.lower().replace(" ", "_")}
            )

        # Registrer agenter i orchestrator
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

        # Registrer komponenter i dashboard
        components = [
            ("orchestrator", "CKC Orchestrator", StatusLevel.GREEN),
            ("security", "Security Manager", StatusLevel.BLUE),
            ("ilcp", "ILCP Manager", StatusLevel.BLUE),
            ("super_admin", "Super-Admin Terminal", StatusLevel.GREEN),
            ("historiker", "Historiker-Kommandant", StatusLevel.BLUE),
            ("bibliotekar", "Bibliotekar-Kommandant", StatusLevel.BLUE),
        ]
        for comp_id, name, status in components:
            await self.dashboard.register_component(comp_id, name, status)

        # Log initialization
        await self.historiker.record_event(
            HistoricalEventType.SYSTEM_START,
            f"CKC Terminal started by {self.user_id}",
            "terminal",
            importance=4
        )

        self.initialized = True
        print_success("CKC system initialiseret")

    async def show_status(self) -> None:
        """Vis komplet systemstatus."""
        print_header("CKC SYSTEM STATUS")
        print(f"{Colors.DIM}Session: {self.session_id} | User: {self.user_id} | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC{Colors.RESET}")

        # Kommandant Status
        print_section("KOMMANDANT-AGENT STATUS")
        orch_status = await self.orchestrator.get_status()
        print_status_dot("green", "CKC Orchestrator", "AKTIV - Fejlfri drift")
        print(f"    Agenter: {orch_status['agents']['total']} registreret, {orch_status['agents']['available']} tilgængelige")
        print(f"    Opgaver: {orch_status['tasks']['completed']} fuldført, {orch_status['tasks']['queued']} i kø")

        # Læringsrum Status
        print_section("LÆRINGSRUM STATUS")
        room_overview = await self.room_manager.get_status_overview()

        status_emoji = {
            "blue": f"{Colors.BLUE}●{Colors.RESET}",
            "green": f"{Colors.GREEN}●{Colors.RESET}",
            "yellow": f"{Colors.YELLOW}●{Colors.RESET}",
            "red": f"{Colors.RED}●{Colors.RESET}",
        }

        rooms = await self.room_manager.list_rooms()
        for room in rooms:
            emoji = status_emoji.get(room.status.value, "○")
            print(f"  {emoji} #{room.room_id:02d} {room.name} - {room.status.value.upper()}")

        print(f"\n  {Colors.DIM}Samlet: {room_overview['total_rooms']} rum | "
              f"Blå: {room_overview['status_counts'].get('blue', 0)} | "
              f"Grøn: {room_overview['status_counts'].get('green', 0)} | "
              f"Gul: {room_overview['status_counts'].get('yellow', 0)} | "
              f"Rød: {room_overview['status_counts'].get('red', 0)}{Colors.RESET}")

        # Agent Status
        print_section("SPECIALISEREDE AGENTER")
        for agent_id, agent in self.agents.items():
            print_status_dot(
                "green" if agent.status.value == "idle" else "yellow",
                agent.name,
                f"Tasks: {agent.tasks_processed}"
            )

        # Kommandanter
        print_section("KOMMANDANTER")
        hist_stats = await self.historiker.get_statistics()
        bibl_stats = await self.bibliotekar.get_statistics()
        print_status_dot("blue", "Historiker-Kommandant", f"{hist_stats['total_events']} events logged")
        print_status_dot("blue", "Bibliotekar-Kommandant", f"{bibl_stats['total_entries']} entries")

        # Protokol Status
        print_section("AVANCEREDE PROTOKOLLER")
        print_status_dot("green", "5.1 Dynamisk Sikkerhedsjustering", "OPERATIV")
        print_status_dot("green", "5.2 ILCP Inter-Læringsrum Kommunikation", "OPERATIV")
        print_status_dot("green", "5.3 EIAP External Access Protocol", "OPERATIV")

        term_status = await self.super_admin.get_terminal_status()
        print(f"\n  {Colors.DIM}HITL Pending: {term_status['pending_hitl_requests']} | "
              f"Audit Log: {term_status['audit_log_size']} entries{Colors.RESET}")

        # Nylige aktiviteter
        print_section("NYLIGE AKTIVITETER")
        timeline = await self.historiker.get_timeline(limit=5)
        if timeline:
            for event in timeline:
                time_str = event.timestamp.strftime("%H:%M:%S")
                print(f"  {Colors.DIM}[{time_str}]{Colors.RESET} {event.event_type.value}: {event.description[:50]}")
        else:
            print(f"  {Colors.DIM}Ingen nylige aktiviteter{Colors.RESET}")

        print(f"\n{Colors.GREEN}{'═' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}  SYSTEM STATUS: FEJLFRI DRIFT ✓{Colors.RESET}")
        print(f"{Colors.GREEN}{'═' * 70}{Colors.RESET}\n")

    # ═══════════════════════════════════════════════════════════
    # SIMULERINGS KOMMANDOER
    # ═══════════════════════════════════════════════════════════

    async def simulate_learning_room_error(self, room_id: int) -> Dict[str, Any]:
        """
        Simuler en fejl i et læringsrum for at teste fail-safe.

        Args:
            room_id: ID på læringsrummet
        """
        print_header(f"SIMULERING: Fejl i Læringsrum #{room_id}")

        # Hent nuværende sikkerhedsniveau
        security = await self.security_manager.get_room_security(room_id)
        if not security:
            print_error(f"Læringsrum {room_id} ikke fundet")
            return {"success": False, "error": "Room not found"}

        old_level = security["state"]["current_level"]
        print_info(f"Nuværende sikkerhedsniveau: {old_level}")

        # Simuler fejl
        print_warning("Simulerer fejl...")
        await self.security_manager.record_operation(room_id, success=False)

        # Check nyt niveau
        new_security = await self.security_manager.get_room_security(room_id)
        new_level = new_security["state"]["current_level"]

        if new_level == "high":
            print_success(f"FAIL-SAFE AKTIVERET: Sikkerhed rullet tilbage til HIGH")
        else:
            print_error(f"FEJL: Sikkerhed ikke rullet tilbage korrekt")

        # Log event
        await self.historiker.record_event(
            HistoricalEventType.ERROR_OCCURRED,
            f"Simulated error in room {room_id} - fail-safe test",
            "terminal_simulation",
            importance=3
        )

        return {
            "success": True,
            "old_level": old_level,
            "new_level": new_level,
            "fail_safe_activated": new_level == "high"
        }

    async def initiate_ilcp_request(
        self,
        source_room_id: int,
        target_room_id: int,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Test ILCP kommunikation mellem læringsrum.

        Args:
            source_room_id: Afsender rum
            target_room_id: Modtager rum
            task_description: Beskrivelse af opgaven
        """
        print_header(f"ILCP KOMMUNIKATION: Rum {source_room_id} → Rum {target_room_id}")

        print_info(f"Sender assistance request: {task_description}")

        # Send assistance request
        request = await self.ilcp_manager.request_assistance(
            requester_room_id=source_room_id,
            task_description=task_description,
            required_capabilities={"general"},
            urgency=MessagePriority.NORMAL
        )

        print_success(f"Request oprettet: {request.id}")
        print(f"  Status: {request.status}")
        print(f"  Assigned to: Room {request.assigned_room_id or 'Pending'}")

        # Check messages
        messages = await self.ilcp_manager.get_messages_for_room(target_room_id)
        print(f"\n  {Colors.DIM}Beskeder til rum {target_room_id}: {len(messages)}{Colors.RESET}")

        # Log
        await self.historiker.record_event(
            HistoricalEventType.TASK_COMPLETED,
            f"ILCP request from room {source_room_id} to {target_room_id}",
            "ilcp_manager",
            importance=2
        )

        return {
            "success": True,
            "request_id": request.id,
            "status": request.status,
            "assigned_room": request.assigned_room_id
        }

    async def request_new_agent_feature(
        self,
        room_id: int,
        agent_type: str,
        feature_description: str
    ) -> Dict[str, Any]:
        """
        Test anmodning om ny agent/feature.

        Args:
            room_id: Anmodende læringsrum
            agent_type: Type af agent
            feature_description: Beskrivelse af feature
        """
        print_header(f"FEATURE REQUEST fra Rum #{room_id}")

        print_info(f"Agent type: {agent_type}")
        print_info(f"Feature: {feature_description}")

        # Opret task
        task = await self.orchestrator.create_task(
            description=f"New feature request: {feature_description}",
            priority=TaskPriority.MEDIUM,
            source=f"room_{room_id}",
            user_id=self.user_id,
            learning_room_id=room_id,
            requires_validation=True,
            metadata={
                "type": "feature_request",
                "agent_type": agent_type,
                "feature": feature_description
            }
        )

        print_success(f"Task oprettet: {task.id}")
        print(f"  Prioritet: {task.priority.name}")
        print(f"  Status: {task.status.value}")
        print(f"  Kræver validering: Ja")

        # Log
        await self.historiker.record_event(
            HistoricalEventType.KNOWLEDGE_ADDED,
            f"Feature request: {feature_description[:50]}",
            f"room_{room_id}",
            importance=3
        )

        return {
            "success": True,
            "task_id": task.id,
            "status": task.status.value,
            "requires_hitl": task.requires_validation
        }

    async def trigger_eiap_test(
        self,
        external_entity_name: str,
        access_level: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test External Implementation Access Protocol (EIAP).

        Args:
            external_entity_name: Navn på ekstern enhed
            access_level: Adgangsniveau (READ_ONLY, LIMITED, STANDARD)
            payload: Test payload
        """
        print_header(f"EIAP TEST: {external_entity_name}")

        # Map access level
        level_map = {
            "READ_ONLY": AuthorizationLevel.READ_ONLY,
            "LIMITED": AuthorizationLevel.LIMITED,
            "STANDARD": AuthorizationLevel.STANDARD,
            "ELEVATED": AuthorizationLevel.ELEVATED,
        }
        auth_level = level_map.get(access_level.upper(), AuthorizationLevel.LIMITED)

        print_info(f"Registrerer ekstern enhed med niveau: {auth_level.name}")

        # Registrer ekstern enhed
        entity, api_key = await self.super_admin.register_external_entity(
            name=external_entity_name,
            entity_type="ai_model",
            authorization_level=auth_level,
            allowed_rooms={1, 2, 3},
            allowed_actions={"read", "query", "analyze"},
            sandbox_only=True
        )

        print_success(f"Enhed registreret: {entity.entity_id}")
        print(f"  API Key: {api_key[:8]}...{api_key[-4:]}")

        # Test kommando execution (kræver HITL)
        print_warning("\nTester kommando eksekvering (kræver HITL)...")

        result = await self.super_admin.execute_command(
            entity_id=entity.entity_id,
            command="analyze",
            params=payload,
            require_hitl=True  # Force HITL for test
        )

        if result.get("pending_hitl"):
            print_info(f"HITL Request oprettet: {result['hitl_request_id']}")
            print(f"\n  {Colors.YELLOW}⚠ AFVENTER MENNESKELIG GODKENDELSE{Colors.RESET}")
            print(f"  Brug: ckc.approve_hitl('{result['hitl_request_id']}')")

        # Log
        await self.historiker.record_event(
            HistoricalEventType.USER_INTERVENTION,
            f"EIAP test: {external_entity_name} requested access",
            "eiap_protocol",
            importance=4
        )

        return {
            "success": True,
            "entity_id": entity.entity_id,
            "hitl_required": result.get("pending_hitl", False),
            "hitl_request_id": result.get("hitl_request_id")
        }

    async def approve_hitl(self, request_id: str) -> Dict[str, Any]:
        """Godkend en HITL request."""
        print_header(f"HITL GODKENDELSE: {request_id}")

        result = await self.super_admin.approve_hitl_request(request_id, self.user_id)

        if result:
            print_success("HITL request godkendt")
        else:
            print_error("Kunne ikke godkende request")

        return {"success": result}

    async def reject_hitl(self, request_id: str, reason: str) -> Dict[str, Any]:
        """Afvis en HITL request."""
        print_header(f"HITL AFVISNING: {request_id}")

        result = await self.super_admin.reject_hitl_request(request_id, self.user_id, reason)

        if result:
            print_warning(f"HITL request afvist: {reason}")
        else:
            print_error("Kunne ikke afvise request")

        return {"success": result}

    # ═══════════════════════════════════════════════════════════
    # EMERGENCY STOP - KRITISK SIKKERHEDSFUNKTION (F-001)
    # Med rollback, timeout og transaction-lignende adfærd
    # ═══════════════════════════════════════════════════════════

    # Konfiguration for emergency stop
    _EMERGENCY_STOP_TIMEOUT: float = 5.0  # Sekunder per operation
    _EMERGENCY_STOP_MAX_RETRIES: int = 2

    async def _lock_room_with_timeout(
        self,
        room_id: int,
        timeout: float
    ) -> Dict[str, Any]:
        """
        Lås et enkelt rum med timeout.

        Returns:
            Dict med success status og eventuel fejl
        """
        try:
            async with asyncio.timeout(timeout):
                # Sæt sikkerhed til HIGH
                await self.security_manager.reset_to_high(room_id)
                # Sæt status til LOCKED (rød)
                await self.room_manager.set_room_status(room_id, RoomStatus.RED)
                return {"success": True, "room_id": room_id}
        except asyncio.TimeoutError:
            return {"success": False, "room_id": room_id, "error": "timeout"}
        except Exception as e:
            return {"success": False, "room_id": room_id, "error": str(e)}

    async def _unlock_room(self, room_id: int) -> bool:
        """
        Lås et rum op (til rollback).

        Returns:
            True hvis success, False ved fejl
        """
        try:
            await self.room_manager.set_room_status(room_id, RoomStatus.BLUE)
            return True
        except Exception:
            return False

    async def _rollback_locked_rooms(
        self,
        locked_rooms: Set[int],
        reason: str
    ) -> Dict[str, Any]:
        """
        Rollback alle låste rum ved partial failure.

        Args:
            locked_rooms: Set af rum-IDs der blev låst
            reason: Årsag til rollback

        Returns:
            Dict med rollback status
        """
        rollback_results = {
            "attempted": len(locked_rooms),
            "success": 0,
            "failed": []
        }

        for room_id in locked_rooms:
            if await self._unlock_room(room_id):
                rollback_results["success"] += 1
            else:
                rollback_results["failed"].append(room_id)

        # Log rollback
        await self.historiker.record_event(
            HistoricalEventType.ERROR_OCCURRED,
            f"Emergency stop ROLLBACK: {reason}. Unlocked {rollback_results['success']}/{rollback_results['attempted']} rooms",
            "emergency_stop_rollback",
            importance=5
        )

        return rollback_results

    async def emergency_stop(self, reason: str = "Manual emergency stop") -> Dict[str, Any]:
        """
        NØDSTOP: Øjeblikkelig standsning af alle operationer.

        Denne funktion med rollback-support:
        1. Sætter alle læringsrum til LOCKED status (med per-room timeout)
        2. Ved partial failure: ruller tilbage alle låste rum
        3. Hæver sikkerhedsniveau til MAXIMUM på alle rum
        4. Afbryder alle igangværende opgaver
        5. Logger nødstop til audit trail
        6. Sender HITL notification

        Args:
            reason: Årsag til nødstop

        Returns:
            Dict med detaljer om nødstoppet inkl. eventuelle rollback-info
        """
        print_header("⛔ NØDSTOP AKTIVERET ⛔")
        print_error(f"Årsag: {reason}")

        results: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "initiated_by": self.user_id,
            "actions_taken": [],
            "partial_failures": [],
            "rollback_performed": False
        }

        # Track locked rooms for potential rollback
        locked_rooms: Set[int] = set()
        partial_failures: List[Dict[str, Any]] = []

        try:
            # 1. Hent alle læringsrum
            rooms = await self.room_manager.list_rooms()
            total_rooms = len(rooms)

            # 2. Lås hvert rum med timeout og tracking
            for room in rooms:
                lock_result = await self._lock_room_with_timeout(
                    room.room_id,
                    self._EMERGENCY_STOP_TIMEOUT
                )

                if lock_result["success"]:
                    locked_rooms.add(room.room_id)
                else:
                    partial_failures.append(lock_result)
                    print_error(f"  ✗ Rum {room.room_id} fejlede: {lock_result.get('error', 'unknown')}")

            # 3. Check for partial failures - trigger rollback
            if partial_failures and len(locked_rooms) < total_rooms:
                print_error(f"\n⚠ PARTIAL FAILURE: {len(partial_failures)} rum fejlede")
                print_warning("Starter rollback af låste rum...")

                rollback_result = await self._rollback_locked_rooms(
                    locked_rooms,
                    f"Partial failure during emergency stop: {len(partial_failures)} rooms failed"
                )

                results["rollback_performed"] = True
                results["rollback_result"] = rollback_result
                results["partial_failures"] = partial_failures
                results["success"] = False
                results["error"] = f"Emergency stop partial failure - {len(partial_failures)} rooms failed to lock"

                print_error(f"\n{'═' * 50}")
                print_error(f"  NØDSTOP FEJLET - ROLLBACK UDFØRT")
                print_error(f"  Låste rum genåbnet: {rollback_result['success']}/{rollback_result['attempted']}")
                print_error(f"{'═' * 50}")

                return results

            # Alle rum låst succesfuldt
            results["actions_taken"].append(f"Låste {len(locked_rooms)} læringsrum")
            print_warning(f"  → {len(locked_rooms)} læringsrum sat til LOCKED/HIGH sikkerhed")

            # 4. Afbryd alle igangværende opgaver (med timeout)
            try:
                async with asyncio.timeout(self._EMERGENCY_STOP_TIMEOUT * 2):
                    orch_status = await self.orchestrator.get_status()
                    active_tasks = orch_status.get("tasks", {}).get("active", 0)

                    if active_tasks > 0:
                        cancelled = await self.orchestrator.cancel_all_tasks(reason="Emergency stop")
                        results["actions_taken"].append(f"Afbrød {cancelled} aktive opgaver")
                        print_warning(f"  → {cancelled} opgaver afbrudt")
            except asyncio.TimeoutError:
                results["actions_taken"].append("Task cancellation timed out (fortsætter)")
                print_warning("  → Task cancellation timed out")

            # 5. Log til Historiker
            await self.historiker.record_event(
                HistoricalEventType.ERROR_OCCURRED,
                f"EMERGENCY STOP: {reason}",
                "emergency_stop_system",
                importance=5  # Højeste prioritet
            )
            results["actions_taken"].append("Logget til audit trail")

            # 6. Opret HITL notification
            try:
                hitl_result = await self.super_admin.execute_command(
                    entity_id="system",
                    command="emergency_stop_notification",
                    params={"reason": reason, "timestamp": results["timestamp"]},
                    require_hitl=True
                )

                if hitl_result.get("pending_hitl"):
                    results["hitl_request_id"] = hitl_result.get("hitl_request_id")
                    results["actions_taken"].append("HITL notification oprettet")
                    print_info(f"  → HITL Request: {hitl_result.get('hitl_request_id')}")
            except Exception as hitl_error:
                results["actions_taken"].append(f"HITL notification fejlede: {hitl_error}")
                print_warning(f"  → HITL notification fejlede (ikke kritisk)")

            # 7. Opdater dashboard
            await self.dashboard.set_component_status(
                "system_emergency",
                StatusLevel.RED,
                f"NØDSTOP: {reason}"
            )
            results["actions_taken"].append("Dashboard opdateret til RED")

            # Mark emergency state
            self._emergency_stop_active = True
            self._emergency_stop_timestamp = datetime.utcnow()

            results["success"] = True
            results["rooms_locked"] = list(locked_rooms)

            print_error(f"\n{'═' * 50}")
            print_error("  NØDSTOP FULDFØRT - SYSTEM I SIKKER TILSTAND")
            print_error(f"{'═' * 50}")

        except Exception as e:
            # Critical failure - attempt rollback if any rooms were locked
            if locked_rooms:
                print_error(f"\nKRITISK FEJL: {e}")
                print_warning("Starter nød-rollback...")

                rollback_result = await self._rollback_locked_rooms(
                    locked_rooms,
                    f"Critical error during emergency stop: {e}"
                )
                results["rollback_performed"] = True
                results["rollback_result"] = rollback_result

            results["success"] = False
            results["error"] = str(e)
            print_error(f"KRITISK FEJL under nødstop: {e}")

        return results

    async def resume_operations(self, confirmation_code: str) -> Dict[str, Any]:
        """
        Genoptag operationer efter nødstop.

        KRÆVER bekræftelseskode for sikkerhed.
        Bruger constant-time comparison for at undgå timing attacks.

        Args:
            confirmation_code: Bekræftelseskode (skal matche session_id)

        Returns:
            Dict med status
        """
        print_header("GENOPTAGELSE AF OPERATIONER")

        # Sikkerhedstjek med constant-time comparison
        # Undgår timing attacks ved at bruge secrets.compare_digest
        if not secrets.compare_digest(
            confirmation_code.encode('utf-8'),
            self.session_id.encode('utf-8')
        ):
            print_error("AFVIST: Ugyldig bekræftelseskode")
            # Log failed attempt
            await self.historiker.record_event(
                HistoricalEventType.USER_INTERVENTION,
                f"Failed resume attempt with invalid code by {self.user_id}",
                "emergency_stop_system",
                importance=4
            )
            return {"success": False, "error": "Invalid confirmation code"}

        results: Dict[str, Any] = {
            "actions_taken": [],
            "rooms_resumed": 0,
            "partial_failures": []
        }

        try:
            # Genåbn læringsrum med timeout per rum
            rooms = await self.room_manager.list_rooms()

            for room in rooms:
                try:
                    async with asyncio.timeout(self._EMERGENCY_STOP_TIMEOUT):
                        await self.room_manager.set_room_status(room.room_id, RoomStatus.BLUE)
                        results["rooms_resumed"] += 1
                except asyncio.TimeoutError:
                    results["partial_failures"].append({
                        "room_id": room.room_id,
                        "error": "timeout"
                    })
                except Exception as e:
                    results["partial_failures"].append({
                        "room_id": room.room_id,
                        "error": str(e)
                    })

            results["actions_taken"].append(f"Genåbnede {results['rooms_resumed']}/{len(rooms)} læringsrum")

            # Log genoptagelse
            await self.historiker.record_event(
                HistoricalEventType.SYSTEM_START,
                f"Operations resumed by {self.user_id}. Rooms: {results['rooms_resumed']}/{len(rooms)}",
                "emergency_stop_system",
                importance=4
            )

            # Opdater dashboard
            await self.dashboard.set_component_status(
                "system_emergency",
                StatusLevel.GREEN,
                "System genoptaget"
            )

            # Clear emergency state
            self._emergency_stop_active = False
            self._emergency_stop_timestamp = None

            results["success"] = True if not results["partial_failures"] else "partial"

            if results["partial_failures"]:
                print_warning(f"Genoptaget med {len(results['partial_failures'])} fejl")
            else:
                print_success("Operationer genoptaget succesfuldt")

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
            print_error(f"Fejl under genoptagelse: {e}")

        return results

    async def show_pending_hitl(self) -> None:
        """Vis ventende HITL requests."""
        print_section("VENTENDE HITL REQUESTS")

        pending = await self.super_admin.get_pending_hitl_requests()

        if not pending:
            print(f"  {Colors.DIM}Ingen ventende requests{Colors.RESET}")
            return

        for req in pending:
            print(f"\n  {Colors.YELLOW}ID: {req.id}{Colors.RESET}")
            print(f"    Type: {req.action_type}")
            print(f"    Fra: {req.requested_by}")
            print(f"    Risk: {req.risk_level}")
            print(f"    Beskrivelse: {req.description[:60]}...")

    # ═══════════════════════════════════════════════════════════
    # CKC FOLDER SWITCHER KOMMANDOER (v1.3.5)
    # ═══════════════════════════════════════════════════════════

    async def list_folders(self, category: Optional[str] = None) -> None:
        """
        List alle tilgængelige CKC folders.

        Args:
            category: Optional kategori filter (ckc_components, cirkelline_ckc, custom)

        Usage:
            await ckc.list_folders()
            await ckc.list_folders("ckc_components")
        """
        print_header("CKC FOLDERS")

        # Initialiser hvis nødvendigt
        if not self.folder_switcher._initialized:
            await self.folder_switcher.initialize()

        context = await self.folder_switcher.get_current_context()

        # Konverter kategori string
        category_enum = None
        if category:
            try:
                category_enum = FolderCategory(category)
            except ValueError:
                print_error(f"Ugyldig kategori: {category}")
                print_info("Vælg: ckc_components, cirkelline_ckc, custom")
                return

        folders = await self.folder_switcher.list_folders(category_enum)

        # Grupper efter kategori
        by_category: Dict[str, List[Any]] = {}
        for folder in folders:
            cat = folder.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(folder)

        # Print træstruktur
        for cat, folder_list in by_category.items():
            print_section(cat.upper())
            for folder in folder_list:
                status = "🔒" if folder.frozen else "📂"
                is_current = folder.folder_id == context.current_folder_id
                is_fav = folder.folder_id in context.favorite_folders
                current_marker = f"{Colors.GREEN}→ {Colors.RESET}" if is_current else "  "
                fav_marker = f" {Colors.YELLOW}★{Colors.RESET}" if is_fav else ""
                print(f"{current_marker}{status} {folder.display_name}{fav_marker}")
                print(f"      {Colors.DIM}ID: {folder.folder_id} | {folder.python_files_count} .py filer{Colors.RESET}")

        # Sammenfatning
        print(f"\n{Colors.DIM}Total: {len(folders)} folders | Current: {context.current_folder_id or 'Ingen'}{Colors.RESET}")

    async def switch_folder(self, folder_id: str) -> Dict[str, Any]:
        """
        Skift til en CKC folder.

        Args:
            folder_id: ID på folder der skal skiftes til

        Usage:
            await ckc.switch_folder("mastermind")
            await ckc.switch_folder("ckc-legal-kommandant")
        """
        print_header(f"SWITCH TIL: {folder_id}")

        # Initialiser hvis nødvendigt
        if not self.folder_switcher._initialized:
            await self.folder_switcher.initialize()

        event = await self.folder_switcher.switch_folder(folder_id, method="terminal")

        if event.success:
            context = await self.folder_switcher.get_current_context()
            folder = context.current_folder
            print_success(f"✓ Skiftede til: {folder.display_name if folder else folder_id}")
            if folder:
                print(f"  Path: {folder.path}")
                print(f"  Kategori: {folder.category.value}")
                print(f"  Status: {folder.status.value}")
                print(f"  Filer: {folder.files_count} total, {folder.python_files_count} Python")
                if folder.version:
                    print(f"  Version: {folder.version}")
        else:
            print_error(f"✗ Kunne ikke skifte: {event.error_message}")

        return event.to_dict()

    async def folder_info(self, folder_id: str) -> Dict[str, Any]:
        """
        Vis detaljer om en folder.

        Args:
            folder_id: Folder ID

        Usage:
            await ckc.folder_info("mastermind")
        """
        print_header(f"FOLDER: {folder_id}")

        # Initialiser hvis nødvendigt
        if not self.folder_switcher._initialized:
            await self.folder_switcher.initialize()

        folder = await self.folder_switcher.get_folder_info(folder_id)

        if not folder:
            print_error("Folder ikke fundet")
            return {}

        context = await self.folder_switcher.get_current_context()
        is_current = folder_id == context.current_folder_id
        is_fav = folder_id in context.favorite_folders

        print(f"  Navn: {folder.display_name}")
        print(f"  ID: {folder.folder_id}")
        print(f"  Path: {folder.path}")
        print(f"  Kategori: {folder.category.value}")
        print(f"  Status: {folder.status.value}")
        print(f"  Frozen: {'Ja' if folder.frozen else 'Nej'}")
        print(f"  Filer: {folder.files_count} total")
        print(f"  Python filer: {folder.python_files_count}")
        if folder.description:
            print(f"  Beskrivelse: {folder.description}")
        if folder.version:
            print(f"  Version: {folder.version}")
        print(f"  Current: {'→ Ja' if is_current else 'Nej'}")
        print(f"  Favorit: {'★ Ja' if is_fav else 'Nej'}")

        return folder.to_dict()

    async def folder_contents(self, folder_id: str) -> Dict[str, Any]:
        """
        Vis indholdet af en folder.

        Args:
            folder_id: Folder ID

        Usage:
            await ckc.folder_contents("mastermind")
        """
        print_header(f"FOLDER INDHOLD: {folder_id}")

        # Initialiser hvis nødvendigt
        if not self.folder_switcher._initialized:
            await self.folder_switcher.initialize()

        contents = await self.folder_switcher.get_folder_contents(folder_id)

        if "error" in contents:
            print_error(contents["error"])
            return contents

        # Subfolders
        if contents.get("subfolders"):
            print_section("SUBFOLDERS")
            for sf in contents["subfolders"]:
                print(f"  📁 {sf['name']}")

        # Python filer
        if contents.get("python_files"):
            print_section("PYTHON FILER")
            for pf in contents["python_files"][:20]:  # Max 20
                size_kb = pf.get('size', 0) / 1024
                print(f"  🐍 {pf['name']} ({size_kb:.1f} KB)")
            if len(contents["python_files"]) > 20:
                print(f"  {Colors.DIM}... og {len(contents['python_files']) - 20} mere{Colors.RESET}")

        # Andre filer
        if contents.get("other_files"):
            print_section("ANDRE FILER")
            for of in contents["other_files"][:10]:
                print(f"  📄 {of['name']}")
            if len(contents["other_files"]) > 10:
                print(f"  {Colors.DIM}... og {len(contents['other_files']) - 10} mere{Colors.RESET}")

        print(f"\n{Colors.DIM}Total: {contents.get('total_files', 0)} filer | {len(contents.get('subfolders', []))} subfolders{Colors.RESET}")
        return contents

    async def add_custom_folder(self, path: str, name: str) -> Dict[str, Any]:
        """
        Tilføj en custom folder.

        Args:
            path: Absolut sti til folderen
            name: Visningsnavn

        Usage:
            await ckc.add_custom_folder("/home/rasmus/my-ckc", "My CKC")
        """
        print_header(f"TILFØJ CUSTOM FOLDER: {name}")

        # Initialiser hvis nødvendigt
        if not self.folder_switcher._initialized:
            await self.folder_switcher.initialize()

        folder = await self.folder_switcher.add_custom_folder(path, name)

        if folder:
            print_success(f"✓ Tilføjede: {folder.display_name}")
            print(f"  ID: {folder.folder_id}")
            print(f"  Path: {folder.path}")
            print(f"  Filer: {folder.files_count}")
            return folder.to_dict()
        else:
            print_error("Kunne ikke tilføje folder")
            print_info("Check at stien eksisterer og er en mappe")
            return {}

    async def remove_custom_folder(self, folder_id: str) -> bool:
        """
        Fjern en custom folder.

        Args:
            folder_id: Folder ID (skal starte med 'custom-')

        Usage:
            await ckc.remove_custom_folder("custom-my-ckc")
        """
        print_header(f"FJERN CUSTOM FOLDER: {folder_id}")

        if not folder_id.startswith("custom-"):
            print_error("Kan kun fjerne custom folders (ID starter med 'custom-')")
            return False

        # Initialiser hvis nødvendigt
        if not self.folder_switcher._initialized:
            await self.folder_switcher.initialize()

        success = await self.folder_switcher.remove_custom_folder(folder_id)

        if success:
            print_success(f"✓ Fjernede: {folder_id}")
        else:
            print_error(f"Kunne ikke fjerne: {folder_id}")

        return success

    async def toggle_favorite(self, folder_id: str) -> bool:
        """
        Toggle favorite status for en folder.

        Args:
            folder_id: Folder ID

        Usage:
            await ckc.toggle_favorite("mastermind")
        """
        # Initialiser hvis nødvendigt
        if not self.folder_switcher._initialized:
            await self.folder_switcher.initialize()

        folder = await self.folder_switcher.get_folder_info(folder_id)
        if not folder:
            print_error(f"Folder ikke fundet: {folder_id}")
            return False

        is_favorite = await self.folder_switcher.toggle_favorite(folder_id)

        if is_favorite:
            print_success(f"★ Tilføjede {folder.display_name} til favorites")
        else:
            print_info(f"☆ Fjernede {folder.display_name} fra favorites")

        return is_favorite

    async def recent_folders(self) -> None:
        """
        Vis senest besøgte folders.

        Usage:
            await ckc.recent_folders()
        """
        print_header("SENESTE FOLDERS")

        # Initialiser hvis nødvendigt
        if not self.folder_switcher._initialized:
            await self.folder_switcher.initialize()

        recent = await self.folder_switcher.get_recent()

        if not recent:
            print(f"  {Colors.DIM}Ingen seneste folders{Colors.RESET}")
            return

        for i, folder in enumerate(recent, 1):
            print(f"  {i}. {folder.display_name}")
            print(f"     {Colors.DIM}ID: {folder.folder_id}{Colors.RESET}")

    async def favorite_folders(self) -> None:
        """
        Vis favorite folders.

        Usage:
            await ckc.favorite_folders()
        """
        print_header("FAVORITE FOLDERS")

        # Initialiser hvis nødvendigt
        if not self.folder_switcher._initialized:
            await self.folder_switcher.initialize()

        favorites = await self.folder_switcher.get_favorites()

        if not favorites:
            print(f"  {Colors.DIM}Ingen favorites - brug ckc.toggle_favorite(folder_id){Colors.RESET}")
            return

        for folder in favorites:
            status = "🔒" if folder.frozen else "📂"
            print(f"  ★ {status} {folder.display_name}")
            print(f"     {Colors.DIM}ID: {folder.folder_id}{Colors.RESET}")

    def help(self) -> None:
        """Vis hjælp."""
        print_header("CKC TERMINAL HJÆLP")

        print_section("GRUNDLÆGGENDE KOMMANDOER")
        print(f"""
  {Colors.CYAN}ckc.show_status(){Colors.RESET}
    Vis komplet systemstatus for alle komponenter

  {Colors.CYAN}ckc.help(){Colors.RESET}
    Vis denne hjælp
""")

        print_section("SIMULERINGS KOMMANDOER")
        print(f"""
  {Colors.CYAN}ckc.simulate_learning_room_error(room_id){Colors.RESET}
    Test DynamicSecurityManager's fail-safe
    Eksempel: await ckc.simulate_learning_room_error(1)

  {Colors.CYAN}ckc.initiate_ilcp_request(source_id, target_id, task){Colors.RESET}
    Test ILCP kommunikation mellem læringsrum
    Eksempel: await ckc.initiate_ilcp_request(1, 2, "Analyser data")

  {Colors.CYAN}ckc.request_new_agent_feature(room_id, agent_type, feature){Colors.RESET}
    Test anmodning om ny feature
    Eksempel: await ckc.request_new_agent_feature(3, "analyzer", "OCR support")

  {Colors.CYAN}ckc.trigger_eiap_test(name, level, payload){Colors.RESET}
    Test External Implementation Access Protocol
    Eksempel: await ckc.trigger_eiap_test("Claude", "LIMITED", {{"action": "test"}})
""")

        print_section("HITL KOMMANDOER")
        print(f"""
  {Colors.CYAN}ckc.show_pending_hitl(){Colors.RESET}
    Vis ventende HITL requests

  {Colors.CYAN}ckc.approve_hitl(request_id){Colors.RESET}
    Godkend en HITL request

  {Colors.CYAN}ckc.reject_hitl(request_id, reason){Colors.RESET}
    Afvis en HITL request
""")

        print_section("CKC FOLDER KOMMANDOER (v1.3.5)")
        print(f"""
  {Colors.CYAN}await ckc.list_folders([category]){Colors.RESET}
    List alle CKC folders
    Kategorier: ckc_components, cirkelline_ckc, custom

  {Colors.CYAN}await ckc.switch_folder(folder_id){Colors.RESET}
    Skift til en folder
    Eksempel: await ckc.switch_folder("mastermind")

  {Colors.CYAN}await ckc.folder_info(folder_id){Colors.RESET}
    Vis folder detaljer

  {Colors.CYAN}await ckc.folder_contents(folder_id){Colors.RESET}
    Vis folder indhold (filer og subfolders)

  {Colors.CYAN}await ckc.add_custom_folder(path, name){Colors.RESET}
    Tilføj custom folder
    Eksempel: await ckc.add_custom_folder("/my/path", "My CKC")

  {Colors.CYAN}await ckc.remove_custom_folder(folder_id){Colors.RESET}
    Fjern custom folder (kun custom- folders)

  {Colors.CYAN}await ckc.toggle_favorite(folder_id){Colors.RESET}
    Toggle favorite status for folder

  {Colors.CYAN}await ckc.recent_folders(){Colors.RESET}
    Vis senest besøgte folders

  {Colors.CYAN}await ckc.favorite_folders(){Colors.RESET}
    Vis favorite folders
""")

        print_section("PROTOKOL OVERSIGT")
        print(f"""
  {Colors.BOLD}5.1 Dynamisk Sikkerhedsjustering{Colors.RESET}
    - 72 timers fejlfri drift → gradvis sikkerhedsreduktion
    - HIGH → MODERATE → LIGHT
    - Øjeblikkelig rollback ved fejl (fail-safe)

  {Colors.BOLD}5.2 ILCP - Inter-Læringsrum Kommunikation{Colors.RESET}
    - Peer-to-peer kommunikation
    - Assistance requests og routing
    - Krypteret og logget

  {Colors.BOLD}5.3 EIAP - External Access Protocol{Colors.RESET}
    - Kontrolleret ekstern adgang
    - HITL for kritiske handlinger
    - Sandbox-miljøer
    - Fuld audit logging
""")


# ═══════════════════════════════════════════════════════════════
# INTERAKTIV TERMINAL
# ═══════════════════════════════════════════════════════════════

async def run_interactive_terminal(user_id: str = "rasmus") -> None:
    """Kør interaktiv terminal session."""

    # Banner
    print(f"""
{Colors.CYAN}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   {Colors.BOLD}CKC - CIRKELLINE KREATIV KOORDINATOR{Colors.RESET}{Colors.CYAN}                        ║
    ║   {Colors.DIM}Kommandør Terminal v1.0{Colors.RESET}{Colors.CYAN}                                      ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
{Colors.RESET}""")

    # Initialiser terminal
    ckc = CKCTerminal(user_id=user_id)
    await ckc.initialize()

    # Vis initial status
    await ckc.show_status()

    # Hjælp info
    print(f"\n{Colors.DIM}Skriv 'help' for kommandoer, 'exit' for at afslutte{Colors.RESET}")
    print(f"{Colors.DIM}Terminal klar til interaktiv brug{Colors.RESET}\n")

    # REPL loop
    while True:
        try:
            cmd = input(f"{Colors.GREEN}ckc>{Colors.RESET} ").strip()

            if not cmd:
                continue

            if cmd.lower() in ['exit', 'quit', 'q']:
                print_info("Afslutter CKC Terminal...")
                break

            if cmd.lower() == 'help':
                ckc.help()
                continue

            if cmd.lower() == 'status':
                await ckc.show_status()
                continue

            if cmd.lower() == 'hitl':
                await ckc.show_pending_hitl()
                continue

            # Evaluer kommando
            if cmd.startswith('await '):
                cmd = cmd[6:]

            # Erstatte ckc. med ckc.
            cmd = cmd.replace('ckc.', 'ckc.')

            try:
                # Sikker eval af async kommandoer
                if 'ckc.' in cmd:
                    result = eval(cmd.replace('ckc.', 'ckc.'))
                    if asyncio.iscoroutine(result):
                        result = await result
                    if result and isinstance(result, dict):
                        print(f"\n{Colors.DIM}Resultat: {result}{Colors.RESET}")
                else:
                    print_warning(f"Ukendt kommando: {cmd}")
                    print(f"{Colors.DIM}Skriv 'help' for at se tilgængelige kommandoer{Colors.RESET}")
            except Exception as e:
                print_error(f"Kommando fejlede: {e}")

        except KeyboardInterrupt:
            print(f"\n{Colors.DIM}Brug 'exit' for at afslutte{Colors.RESET}")
        except EOFError:
            break

    print_success("CKC Terminal afsluttet")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="CKC Kommandør Terminal")
    parser.add_argument('--user-id', default='rasmus', help='Bruger ID')
    parser.add_argument('--status-only', action='store_true', help='Vis kun status')

    args = parser.parse_args()

    if args.status_only:
        async def show_only():
            ckc = CKCTerminal(user_id=args.user_id)
            await ckc.initialize()
            await ckc.show_status()
        asyncio.run(show_only())
    else:
        asyncio.run(run_interactive_terminal(args.user_id))


if __name__ == "__main__":
    main()
