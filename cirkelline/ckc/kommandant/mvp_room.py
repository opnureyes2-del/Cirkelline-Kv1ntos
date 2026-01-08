"""
CKC MVP Learning Room
=====================

Det første lærerum til validering af Kommandant-funktionalitet.

Features:
    - Document Specialist integration
    - Simpel opgaveudførelse
    - End-to-end test flow
    - Erfaringsbaseret læring

Usage:
    from cirkelline.ckc.kommandant.mvp_room import (
        create_mvp_room,
        get_mvp_room,
        test_mvp_workflow,
    )

    # Setup the MVP room
    room, kommandant = await create_mvp_room()

    # Test the workflow
    result = await test_mvp_workflow(room, kommandant)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from ..learning_rooms import (
    LearningRoom,
    LearningRoomManager,
    LearningEvent,
    RoomStatus,
    get_room_manager,
    create_learning_room,
    get_learning_room,
)

from .core import (
    Kommandant,
    create_kommandant,
    get_kommandant,
    TaskPriority,
    KommandantStatus,
)

from .delegation import (
    SpecialistSelector,
    TaskPlanner,
    DelegationEngine,
    get_delegation_engine,
)

logger = logging.getLogger(__name__)


# ========== MVP Room Configuration ==========

MVP_ROOM_NAME = "Document Analysis MVP"
MVP_ROOM_DESCRIPTION = """
Første MVP lærerum til validering af Kommandant-arkitekturen.

Fokus:
    - Dokumentanalyse
    - OCR-behandling
    - Opsummering
    - Gem til Notion

Specialister:
    - Document Specialist (primær)
"""

MVP_KOMMANDANT_NAME = "Analyse Kommandant"
MVP_KOMMANDANT_DESCRIPTION = """
Kommandant for Document Analysis MVP lærerummet.

Ansvar:
    - Modtage dokumentanalyse-opgaver
    - Delegere til Document Specialist
    - Aggregere resultater
    - Lære fra erfaringer
"""


# ========== Document Specialist Stub ==========

@dataclass
class DocumentSpecialist:
    """
    Document Specialist stub for MVP.

    I fuld implementering vil dette integrere med:
    - Docling for PDF-behandling
    - Tesseract for OCR
    - LLM for opsummering
    """

    specialist_id: str = field(default_factory=lambda: f"doc_specialist_{uuid.uuid4().hex[:8]}")
    name: str = "Document Specialist"
    status: str = "idle"
    processed_count: int = 0
    capabilities: List[str] = field(default_factory=lambda: [
        "document_analysis",
        "document_summary",
        "ocr",
        "pdf_processing"
    ])

    async def process_document(
        self,
        content: str,
        task_type: str = "analyze"
    ) -> Dict[str, Any]:
        """
        Process a document.

        Args:
            content: Document content or path
            task_type: Type of processing (analyze, summarize, ocr)

        Returns:
            Processing result
        """
        self.status = "processing"
        start_time = datetime.now(timezone.utc)

        # Simulate processing
        await asyncio.sleep(0.5)

        self.processed_count += 1

        result = {
            "specialist_id": self.specialist_id,
            "task_type": task_type,
            "success": True,
            "output": {
                "type": "document_analysis",
                "summary": f"Dokumentet indeholder {len(content)} tegn. "
                           f"Analyseret af {self.name}.",
                "key_points": [
                    "Punkt 1: Dokumentets hovedemne identificeret",
                    "Punkt 2: Nøglebegreber ekstraheret",
                    "Punkt 3: Strukturanalyse gennemført"
                ],
                "confidence": 0.87,
                "processing_time_ms": 500
            },
            "metadata": {
                "content_length": len(content),
                "task_type": task_type,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
        }

        self.status = "idle"
        return result

    async def summarize(self, content: str, max_length: int = 500) -> Dict[str, Any]:
        """Create a summary of the content."""
        return await self.process_document(content, task_type="summarize")

    async def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text from image (OCR)."""
        return await self.process_document(f"[Image: {image_path}]", task_type="ocr")

    def get_status(self) -> Dict[str, Any]:
        """Get specialist status."""
        return {
            "specialist_id": self.specialist_id,
            "name": self.name,
            "status": self.status,
            "processed_count": self.processed_count,
            "capabilities": self.capabilities
        }


# ========== MVP Room Factory ==========

_mvp_room: Optional[LearningRoom] = None
_mvp_kommandant: Optional[Kommandant] = None
_document_specialist: Optional[DocumentSpecialist] = None


async def create_mvp_room(owner: str = "system") -> tuple:
    """
    Create the MVP learning room with Kommandant.

    Args:
        owner: Owner of the room

    Returns:
        Tuple of (LearningRoom, Kommandant)
    """
    global _mvp_room, _mvp_kommandant, _document_specialist

    # Create learning room
    _mvp_room = await create_learning_room(
        name=MVP_ROOM_NAME,
        owner=owner,
        description=MVP_ROOM_DESCRIPTION
    )

    # Create Kommandant for this room
    _mvp_kommandant = await create_kommandant(
        room_id=_mvp_room.room_id,
        name=MVP_KOMMANDANT_NAME,
        description=MVP_KOMMANDANT_DESCRIPTION,
        auto_start=True
    )

    # Create Document Specialist
    _document_specialist = DocumentSpecialist()

    # Register specialist with delegation engine
    engine = get_delegation_engine()
    engine.selector.register_specialist(
        specialist_id=_document_specialist.specialist_id,
        specialist_type="document-specialist",
        capabilities=_document_specialist.capabilities,
        max_load=10
    )

    # Add room event
    event = LearningEvent(
        id=f"evt_{uuid.uuid4().hex[:8]}",
        event_type="room_setup",
        content={
            "room_name": MVP_ROOM_NAME,
            "kommandant_id": _mvp_kommandant.kommandant_id,
            "specialist_id": _document_specialist.specialist_id
        },
        source="mvp_room_factory",
        timestamp=datetime.now(timezone.utc)
    )
    _mvp_room.add_event(event)

    logger.info(f"MVP Room created: {_mvp_room.full_name} with Kommandant {_mvp_kommandant.name}")

    return _mvp_room, _mvp_kommandant


async def get_mvp_room() -> Optional[LearningRoom]:
    """Get the MVP room if it exists."""
    return _mvp_room


async def get_mvp_kommandant() -> Optional[Kommandant]:
    """Get the MVP Kommandant if it exists."""
    return _mvp_kommandant


async def get_document_specialist() -> Optional[DocumentSpecialist]:
    """Get the Document Specialist if it exists."""
    return _document_specialist


# ========== Rejsekommando (Journey Command) ==========

@dataclass
class JourneyStep:
    """A step in a journey command."""
    step_id: str
    name: str
    status: str = "pending"
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class JourneyCommand:
    """
    En 'Rejsekommando' - en komplet arbejdsgang fra start til slut.

    Denne MVP implementerer:
        1. Modtag dokument
        2. Analysér via Document Specialist
        3. Opsummer indhold
        4. (Simuler) Gem til Notion
        5. Rapportér resultat

    Usage:
        journey = JourneyCommand("Analysér rapport")
        journey.add_document("Min rapport tekst...")
        result = await journey.execute(kommandant)
    """

    name: str
    journey_id: str = field(default_factory=lambda: f"journey_{uuid.uuid4().hex[:12]}")
    status: str = "created"
    steps: List[JourneyStep] = field(default_factory=list)
    document_content: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None

    def add_document(self, content: str) -> None:
        """Add document content for processing."""
        self.document_content = content

    def _create_default_steps(self) -> None:
        """Create default journey steps."""
        self.steps = [
            JourneyStep(
                step_id=f"step_1_{uuid.uuid4().hex[:6]}",
                name="Modtag dokument"
            ),
            JourneyStep(
                step_id=f"step_2_{uuid.uuid4().hex[:6]}",
                name="Analysér dokument"
            ),
            JourneyStep(
                step_id=f"step_3_{uuid.uuid4().hex[:6]}",
                name="Opsummer indhold"
            ),
            JourneyStep(
                step_id=f"step_4_{uuid.uuid4().hex[:6]}",
                name="Gem til Notion (simuleret)"
            ),
            JourneyStep(
                step_id=f"step_5_{uuid.uuid4().hex[:6]}",
                name="Rapportér resultat"
            )
        ]

    async def execute(self, kommandant: Kommandant) -> Dict[str, Any]:
        """
        Execute the journey command.

        Args:
            kommandant: The Kommandant to use for execution

        Returns:
            Journey execution result
        """
        self.status = "executing"
        self._create_default_steps()
        results = {}

        try:
            # Step 1: Receive document
            await self._execute_step(0, {"content": self.document_content[:100]})

            # Step 2: Analyze via Kommandant
            task_result = await kommandant.receive_task(
                task_id=f"task_{self.journey_id}",
                context_id=f"ctx_{self.journey_id}",
                prompt=f"Analysér dette dokument: {self.document_content[:200]}...",
                priority=TaskPriority.NORMAL,
                metadata={"journey_id": self.journey_id}
            )

            exec_result = await kommandant.execute_task(task_result["task_id"])
            await self._execute_step(1, exec_result)
            results["analysis"] = exec_result

            # Step 3: Summarize
            summary_result = {
                "summary": f"Opsummering af dokument ({len(self.document_content)} tegn)",
                "key_findings": exec_result.get("result", {})
            }
            await self._execute_step(2, summary_result)
            results["summary"] = summary_result

            # Step 4: Save to Notion (simulated)
            notion_result = {
                "notion_page_id": f"notion_{uuid.uuid4().hex[:12]}",
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "simulated": True
            }
            await self._execute_step(3, notion_result)
            results["notion"] = notion_result

            # Step 5: Report
            report = {
                "journey_id": self.journey_id,
                "name": self.name,
                "steps_completed": len([s for s in self.steps if s.status == "completed"]),
                "total_steps": len(self.steps),
                "success": True
            }
            await self._execute_step(4, report)

            self.status = "completed"
            self.completed_at = datetime.now(timezone.utc)
            self.result = {
                "success": True,
                "journey_id": self.journey_id,
                "steps": [self._step_to_dict(s) for s in self.steps],
                "results": results,
                "duration_seconds": (self.completed_at - self.created_at).total_seconds()
            }

            logger.info(f"Journey {self.journey_id} completed successfully")
            return self.result

        except Exception as e:
            self.status = "failed"
            self.completed_at = datetime.now(timezone.utc)
            self.result = {
                "success": False,
                "journey_id": self.journey_id,
                "error": str(e),
                "steps": [self._step_to_dict(s) for s in self.steps]
            }
            logger.error(f"Journey {self.journey_id} failed: {e}")
            return self.result

    async def _execute_step(self, step_index: int, data: Dict[str, Any]) -> None:
        """Execute a journey step."""
        step = self.steps[step_index]
        step.status = "running"
        step.started_at = datetime.now(timezone.utc)
        step.input_data = data

        # Simulate step execution
        await asyncio.sleep(0.2)

        step.status = "completed"
        step.completed_at = datetime.now(timezone.utc)
        step.output_data = data

    def _step_to_dict(self, step: JourneyStep) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_id": step.step_id,
            "name": step.name,
            "status": step.status,
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert journey to dictionary."""
        return {
            "journey_id": self.journey_id,
            "name": self.name,
            "status": self.status,
            "steps": [self._step_to_dict(s) for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result
        }


# ========== MVP Workflow Test ==========

async def test_mvp_workflow(
    room: Optional[LearningRoom] = None,
    kommandant: Optional[Kommandant] = None
) -> Dict[str, Any]:
    """
    Test the complete MVP workflow.

    This tests:
        1. Room and Kommandant setup
        2. Task reception and execution
        3. Delegation to specialists
        4. Result aggregation
        5. Learning from experience
        6. Journey command execution

    Returns:
        Test results dictionary
    """
    results = {
        "tests": [],
        "passed": 0,
        "failed": 0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Setup if not provided
    if not room or not kommandant:
        room, kommandant = await create_mvp_room()

    # Test 1: Room exists
    test1 = {
        "name": "Room Created",
        "passed": room is not None,
        "details": room.to_dict() if room else "No room"
    }
    results["tests"].append(test1)

    # Test 2: Kommandant active
    test2 = {
        "name": "Kommandant Active",
        "passed": kommandant.status != KommandantStatus.ERROR,
        "details": kommandant.get_status()
    }
    results["tests"].append(test2)

    # Test 3: Simple task execution
    try:
        task_result = await kommandant.receive_task(
            task_id=f"test_task_{uuid.uuid4().hex[:8]}",
            context_id="test_ctx",
            prompt="Analysér dette test dokument for mig",
            priority=TaskPriority.NORMAL
        )

        exec_result = await kommandant.execute_task(task_result["task_id"])

        test3 = {
            "name": "Task Execution",
            "passed": exec_result.get("success", False) or exec_result.get("outcome") == "success",
            "details": exec_result
        }
    except Exception as e:
        test3 = {
            "name": "Task Execution",
            "passed": False,
            "details": str(e)
        }
    results["tests"].append(test3)

    # Test 4: Journey command
    try:
        journey = JourneyCommand(name="Test Rejsekommando")
        journey.add_document("Dette er et test dokument med noget indhold der skal analyseres.")

        journey_result = await journey.execute(kommandant)

        test4 = {
            "name": "Journey Command",
            "passed": journey_result.get("success", False),
            "details": {
                "journey_id": journey_result.get("journey_id"),
                "steps_completed": journey_result.get("steps", []),
                "duration": journey_result.get("duration_seconds")
            }
        }
    except Exception as e:
        test4 = {
            "name": "Journey Command",
            "passed": False,
            "details": str(e)
        }
    results["tests"].append(test4)

    # Test 5: Learning recorded
    test5 = {
        "name": "Experience Recorded",
        "passed": len(kommandant._experiences) > 0,
        "details": {
            "experiences_count": len(kommandant._experiences),
            "latest": kommandant._experiences[-1].to_dict() if kommandant._experiences else None
        }
    }
    results["tests"].append(test5)

    # Test 6: Audit log
    audit_entries = kommandant.get_audit_log(limit=10)
    test6 = {
        "name": "Audit Logging",
        "passed": len(audit_entries) > 0,
        "details": {
            "entries_count": len(audit_entries),
            "sample": audit_entries[0] if audit_entries else None
        }
    }
    results["tests"].append(test6)

    # Calculate totals
    results["passed"] = sum(1 for t in results["tests"] if t["passed"])
    results["failed"] = sum(1 for t in results["tests"] if not t["passed"])
    results["success"] = results["failed"] == 0

    logger.info(f"MVP Workflow Test: {results['passed']}/{len(results['tests'])} passed")

    return results


# ========== Convenience Functions ==========

async def run_simple_journey(
    document_content: str,
    journey_name: str = "Dokument Analyse"
) -> Dict[str, Any]:
    """
    Run a simple journey with default setup.

    Args:
        document_content: The document to analyze
        journey_name: Name for the journey

    Returns:
        Journey result
    """
    # Ensure room exists
    room, kommandant = await create_mvp_room()

    # Create and execute journey
    journey = JourneyCommand(name=journey_name)
    journey.add_document(document_content)

    return await journey.execute(kommandant)


logger.info("CKC MVP Room module loaded")
