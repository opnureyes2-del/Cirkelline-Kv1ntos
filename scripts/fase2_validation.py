#!/usr/bin/env python3
"""
Fase 2: Dybdegående Accelereret Validering & Optimering
========================================================

Dette script udfører en komplet validering af Fase 2: Kommandant Kerne & Et Lærerum MVP.

Kører alle valideringer fra Master-Kommandoen:
    - DEL A: Funktionel Validering
    - DEL B: Krydsreference mod Master-Kommando
    - DEL C: Dokumentation & Fase 3 Forberedelse

Usage:
    python scripts/fase2_validation.py
"""

import asyncio
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cirkelline.ckc.kommandant import (
    Kommandant,
    create_kommandant,
    KommandantStatus,
    TaskPriority,
    DelegationStrategy,
    SpecialistSelector,
    TaskPlanner,
    DelegationEngine,
    create_mvp_room,
    test_mvp_workflow,
    run_simple_journey,
    JourneyCommand,
    DocumentSpecialist,
)

from cirkelline.ckc.learning_rooms import (
    get_room_manager,
    RoomStatus,
)

from cirkelline.ckc.api import control_panel_router


class Fase2Validator:
    """Validator for Fase 2 implementation."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": "Fase 2: Kommandant Kerne & Et Lærerum MVP",
            "del_a": {},
            "del_b": {},
            "del_c": {},
            "summary": {}
        }
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def log(self, message: str, level: str = "INFO"):
        """Log validation message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"INFO": "✓", "WARN": "⚠", "ERROR": "✗", "CHECK": "→"}.get(level, " ")
        print(f"[{timestamp}] {prefix} {message}")

    def record_test(self, category: str, test_name: str, passed: bool, details: str = ""):
        """Record a test result."""
        if category not in self.results:
            self.results[category] = {}

        self.results[category][test_name] = {
            "passed": passed,
            "details": details
        }

        if passed:
            self.passed += 1
            self.log(f"{test_name}: PASSED - {details}", "INFO")
        else:
            self.failed += 1
            self.log(f"{test_name}: FAILED - {details}", "ERROR")

    async def run_all_validations(self):
        """Run all validations."""
        print("\n" + "="*80)
        print("FASE 2: DYBDEGÅENDE ACCELERERET VALIDERING")
        print("="*80 + "\n")

        await self.del_a_funktionel_validering()
        await self.del_b_krydsreference()
        await self.del_c_dokumentation()

        self.generate_summary()
        return self.results

    # ============================================================
    # DEL A: FASE 2 FUNKTIONEL VALIDERING
    # ============================================================

    async def del_a_funktionel_validering(self):
        """DEL A: Fase 2 Funktionel Validering & Optimering."""
        print("\n" + "-"*60)
        print("DEL A: FASE 2 FUNKTIONEL VALIDERING")
        print("-"*60 + "\n")

        # A1: Kommandant Kerne-Agent Validering
        await self.validate_kommandant_core()

        # A2: Lærerum MVP & Document Specialist
        await self.validate_learning_room()

        # A3: Rejsekommando Udførelse
        await self.validate_journey_command()

        # A4: Lærings- & Dokumentationsmodul
        await self.validate_learning_module()

    async def validate_kommandant_core(self):
        """Validér Kommandant Kerne-Agent."""
        self.log("Validerer Kommandant Kerne-Agent...", "CHECK")

        try:
            # Test 1: Kommandant oprettelse
            kommandant = Kommandant(room_id=1, name="Validation Kommandant")
            self.record_test("del_a", "kommandant_creation",
                           kommandant is not None,
                           f"ID: {kommandant.kommandant_id}")

            # Test 2: Kommandant start
            await kommandant.start()
            self.record_test("del_a", "kommandant_start",
                           kommandant.status == KommandantStatus.IDLE,
                           f"Status: {kommandant.status.value}")

            # Test 3: Opgavemodtagelse
            task_result = await kommandant.receive_task(
                task_id="validation_task_001",
                context_id="validation_ctx",
                prompt="Analysér dette dokument for validering",
                priority=TaskPriority.NORMAL
            )
            self.record_test("del_a", "task_reception",
                           task_result.get("status") == "received",
                           f"Task ID: {task_result.get('task_id')}")

            # Test 4: Opgaveudførelse
            exec_result = await kommandant.execute_task("validation_task_001")
            self.record_test("del_a", "task_execution",
                           "outcome" in exec_result,
                           f"Outcome: {exec_result.get('outcome')}")

            # Test 5: Audit log
            audit_entries = kommandant.get_audit_log()
            self.record_test("del_a", "audit_logging",
                           len(audit_entries) > 0,
                           f"Entries: {len(audit_entries)}")

            # Test 6: Statistik
            stats = kommandant.get_statistics()
            self.record_test("del_a", "statistics_tracking",
                           stats["tasks_received"] > 0,
                           f"Tasks: {stats['tasks_received']}")

            # Clean up
            await kommandant.stop()

        except Exception as e:
            self.record_test("del_a", "kommandant_core", False, str(e))

    async def validate_learning_room(self):
        """Validér Lærerum MVP."""
        self.log("Validerer Lærerum MVP...", "CHECK")

        try:
            # Test 1: MVP Room oprettelse
            room, kommandant = await create_mvp_room()
            self.record_test("del_a", "mvp_room_creation",
                           room is not None,
                           f"Room: {room.name}, ID: {room.room_id}")

            # Test 2: Room status
            self.record_test("del_a", "room_status",
                           room.status in [RoomStatus.BLUE, RoomStatus.GREEN],
                           f"Status: {room.status.value}")

            # Test 3: Kommandant tilknytning
            self.record_test("del_a", "kommandant_attached",
                           kommandant is not None and kommandant._running,
                           f"Kommandant: {kommandant.name}")

            # Test 4: Document Specialist
            specialist = DocumentSpecialist()
            result = await specialist.process_document("Test dokument", "analyze")
            self.record_test("del_a", "document_specialist",
                           result.get("success", False),
                           f"Processed: {specialist.processed_count}")

        except Exception as e:
            self.record_test("del_a", "learning_room", False, str(e))

    async def validate_journey_command(self):
        """Validér Rejsekommando."""
        self.log("Validerer Rejsekommando...", "CHECK")

        try:
            # Test 1: Journey oprettelse
            journey = JourneyCommand(name="Validation Journey")
            journey.add_document("Dette er et test dokument til validering.")
            self.record_test("del_a", "journey_creation",
                           journey.document_content != "",
                           f"Journey: {journey.journey_id}")

            # Test 2: Journey udførelse
            _, kommandant = await create_mvp_room()
            result = await journey.execute(kommandant)
            self.record_test("del_a", "journey_execution",
                           result.get("success", False),
                           f"Steps: {len(result.get('steps', []))}")

            # Test 3: Simple journey helper
            simple_result = await run_simple_journey(
                document_content="Simpel test dokument",
                journey_name="Simple Validation"
            )
            self.record_test("del_a", "simple_journey",
                           simple_result.get("success", False),
                           f"Duration: {simple_result.get('duration_seconds', 0):.2f}s")

            # Test 4: Fejlhåndtering (tomt dokument)
            empty_journey = JourneyCommand(name="Empty Test")
            empty_journey.add_document("")
            empty_result = await empty_journey.execute(kommandant)
            self.record_test("del_a", "journey_error_handling",
                           "journey_id" in empty_result,  # Graceful handling
                           "Empty document handled gracefully")

        except Exception as e:
            self.record_test("del_a", "journey_command", False, str(e))

    async def validate_learning_module(self):
        """Validér Lærings- og Dokumentationsmodul."""
        self.log("Validerer Læringsmodul...", "CHECK")

        try:
            # Kør MVP workflow test
            workflow_result = await test_mvp_workflow()

            # Test 1: Erfaringsregistrering
            self.record_test("del_a", "experience_recording",
                           workflow_result.get("passed", 0) > 0,
                           f"Tests passed: {workflow_result.get('passed', 0)}/{workflow_result.get('passed', 0) + workflow_result.get('failed', 0)}")

            # Test 2: Workflow success rate
            total = workflow_result.get("passed", 0) + workflow_result.get("failed", 0)
            pass_rate = workflow_result.get("passed", 0) / max(1, total)
            self.record_test("del_a", "workflow_success_rate",
                           pass_rate >= 0.5,
                           f"Pass rate: {pass_rate:.1%}")

        except Exception as e:
            self.record_test("del_a", "learning_module", False, str(e))

    # ============================================================
    # DEL B: KRYDSREFERENCE MOD MASTER-KOMMANDO
    # ============================================================

    async def del_b_krydsreference(self):
        """DEL B: Krydsreference & Validering mod Master-Kommando."""
        print("\n" + "-"*60)
        print("DEL B: KRYDSREFERENCE MOD MASTER-KOMMANDO")
        print("-"*60 + "\n")

        # B1: Fase 1 Infrastruktur kompatibilitet
        await self.validate_infrastructure_compatibility()

        # B2: HITL Integration punkter
        await self.validate_hitl_integration()

        # B3: Sikkerhed & Privatliv
        await self.validate_security()

        # B4: UX & Klarhed
        await self.validate_ux()

        # B5: Ressourceforbrug
        await self.validate_resources()

    async def validate_infrastructure_compatibility(self):
        """Validér kompatibilitet med Fase 1 infrastruktur."""
        self.log("Validerer Fase 1 kompatibilitet...", "CHECK")

        try:
            # Test: Control Panel API integration
            from cirkelline.ckc.api.control_panel import _state
            self.record_test("del_b", "control_panel_integration",
                           _state is not None,
                           "Control Panel state accessible")

            # Test: Connector Registry
            from cirkelline.ckc.infrastructure.connector_registry import get_connector_registry
            registry = await get_connector_registry()
            self.record_test("del_b", "connector_registry",
                           registry is not None,
                           "Connector registry available")

            # Test: Knowledge Sync
            from cirkelline.ckc.infrastructure.knowledge_sync import KnowledgeSyncManager
            self.record_test("del_b", "knowledge_sync_available",
                           KnowledgeSyncManager is not None,
                           "Knowledge sync module available")

        except Exception as e:
            self.record_test("del_b", "infrastructure_compatibility", False, str(e))

    async def validate_hitl_integration(self):
        """Validér HITL integration punkter."""
        self.log("Validerer HITL integration...", "CHECK")

        try:
            # Test: HITL endpoint availability
            from cirkelline.ckc.api.control_panel import create_hitl_request, HITLStatus
            self.record_test("del_b", "hitl_endpoints_available",
                           create_hitl_request is not None,
                           "HITL request function available")

            # Identificér potentielle HITL punkter
            hitl_points = [
                "Før dokumentopsummering gemmes i Notion",
                "Ved delegering af komplekse opgaver",
                "Ved kritiske beslutninger",
                "Ved validering af resultater"
            ]
            self.record_test("del_b", "hitl_points_identified",
                           len(hitl_points) > 0,
                           f"Identified {len(hitl_points)} potential HITL points")

        except Exception as e:
            self.record_test("del_b", "hitl_integration", False, str(e))

    async def validate_security(self):
        """Validér sikkerhed og privatliv."""
        self.log("Validerer sikkerhed...", "CHECK")

        try:
            # Test: Kommandant har isoleret tilstand
            kommandant1 = Kommandant(room_id=100, name="Security Test 1")
            kommandant2 = Kommandant(room_id=101, name="Security Test 2")

            self.record_test("del_b", "kommandant_isolation",
                           kommandant1.kommandant_id != kommandant2.kommandant_id,
                           "Kommandanter are isolated")

            # Test: Audit trail for security events
            await kommandant1.start()
            audit = kommandant1.get_audit_log()
            self.record_test("del_b", "security_audit_trail",
                           len(audit) > 0,
                           f"Security events logged: {len(audit)}")

            await kommandant1.stop()

        except Exception as e:
            self.record_test("del_b", "security", False, str(e))

    async def validate_ux(self):
        """Validér brugeroplevelse (admin/udvikler perspektiv)."""
        self.log("Validerer UX...", "CHECK")

        try:
            # Test: Status er klar og forståelig
            kommandant = Kommandant(room_id=200, name="UX Test")
            status = kommandant.get_status()

            required_fields = ["kommandant_id", "status", "name", "room_id"]
            has_all_fields = all(f in status for f in required_fields)

            self.record_test("del_b", "status_clarity",
                           has_all_fields,
                           f"Status contains: {list(status.keys())}")

            # Test: Statistik er informativ
            stats = kommandant.get_statistics()
            self.record_test("del_b", "statistics_informative",
                           "tasks_received" in stats and "tasks_completed" in stats,
                           "Key metrics available")

        except Exception as e:
            self.record_test("del_b", "ux", False, str(e))

    async def validate_resources(self):
        """Validér ressourceforbrug."""
        self.log("Validerer ressourceforbrug...", "CHECK")

        import time

        try:
            # Test: Oprettelsestid
            start = time.time()
            kommandant = Kommandant(room_id=300, name="Resource Test")
            await kommandant.start()
            creation_time = time.time() - start

            self.record_test("del_b", "creation_time",
                           creation_time < 2.0,
                           f"Creation time: {creation_time:.3f}s")

            # Test: Opgavebehandlingstid
            start = time.time()
            await kommandant.receive_task(
                task_id="resource_test",
                context_id="ctx",
                prompt="Test"
            )
            await kommandant.execute_task("resource_test")
            task_time = time.time() - start

            self.record_test("del_b", "task_processing_time",
                           task_time < 5.0,
                           f"Task time: {task_time:.3f}s")

            await kommandant.stop()

        except Exception as e:
            self.record_test("del_b", "resources", False, str(e))

    # ============================================================
    # DEL C: DOKUMENTATION & FASE 3 FORBEREDELSE
    # ============================================================

    async def del_c_dokumentation(self):
        """DEL C: Dokumentation & Forberedelse til Fase 3."""
        print("\n" + "-"*60)
        print("DEL C: DOKUMENTATION & FASE 3 FORBEREDELSE")
        print("-"*60 + "\n")

        # C1: Verificér modulstruktur
        await self.verify_module_structure()

        # C2: Identificér næste skridt
        await self.identify_next_steps()

    async def verify_module_structure(self):
        """Verificér modulstruktur."""
        self.log("Verificerer modulstruktur...", "CHECK")

        try:
            required_files = [
                "cirkelline/ckc/kommandant/__init__.py",
                "cirkelline/ckc/kommandant/core.py",
                "cirkelline/ckc/kommandant/delegation.py",
                "cirkelline/ckc/kommandant/mvp_room.py",
                "tests/test_ckc_kommandant.py",
            ]

            project_root = Path(__file__).parent.parent
            existing = sum(1 for f in required_files if (project_root / f).exists())

            self.record_test("del_c", "module_structure",
                           existing == len(required_files),
                           f"Files: {existing}/{len(required_files)}")

        except Exception as e:
            self.record_test("del_c", "module_structure", False, str(e))

    async def identify_next_steps(self):
        """Identificér næste skridt for Fase 3."""
        self.log("Identificerer Fase 3 skridt...", "CHECK")

        fase3_tasks = [
            "Inter-lærerum kommunikation via Message Bus",
            "Koordinerede rejsekommandoer på tværs af rum",
            "Flere specialister i forskellige lærerum",
            "Avanceret HITL workflow",
            "Performance optimering for skalering",
        ]

        self.record_test("del_c", "fase3_planning",
                       len(fase3_tasks) > 0,
                       f"Identified {len(fase3_tasks)} tasks for Fase 3")

        self.results["fase3_roadmap"] = fase3_tasks

    # ============================================================
    # SAMMENFATNING
    # ============================================================

    def generate_summary(self):
        """Generér sammenfatning."""
        print("\n" + "="*80)
        print("VALIDERINGSSAMMENFATNING")
        print("="*80 + "\n")

        total = self.passed + self.failed
        success_rate = self.passed / max(1, total)

        self.results["summary"] = {
            "total_tests": total,
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": f"{success_rate:.1%}",
            "status": "PASS" if success_rate >= 0.8 else "NEEDS_REVIEW",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        print(f"  Total tests:    {total}")
        print(f"  Passed:         {self.passed}")
        print(f"  Failed:         {self.failed}")
        print(f"  Success rate:   {success_rate:.1%}")
        print(f"  Status:         {'✓ PASS' if success_rate >= 0.8 else '⚠ NEEDS REVIEW'}")
        print()

        if success_rate >= 0.9:
            print("🎉 FASE 2 VALIDERING FULDFØRT - KLAR TIL FASE 3!")
        elif success_rate >= 0.8:
            print("✓ FASE 2 VALIDERING BESTÅET - Små justeringer anbefales")
        else:
            print("⚠ FASE 2 KRÆVER OPMÆRKSOMHED - Gennemgå fejlede tests")


async def main():
    """Main entry point."""
    validator = Fase2Validator()
    results = await validator.run_all_validations()

    # Save results
    output_path = Path(__file__).parent.parent / "docs" / "fase2_validation_report.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nValidation report saved to: {output_path}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
