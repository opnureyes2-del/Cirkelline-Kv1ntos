"""
CKC Kommandant Core Agent
=========================

Den centrale Kommandant-agent der orkestrerer opgaver inden for et lærerum.

Ansvar:
    - Modtage og parse opgaver fra brugere/system
    - Analysere opgaver og beslutte delegering
    - Koordinere med specialister via Message Bus
    - Rapportere status til Control Panel
    - Persistere erfaringer og læring
    - Audit trail for alle handlinger

Integration:
    - Message Bus (RabbitMQ/Redis) til specialist-kommunikation
    - Control Panel API til opgavestyring
    - Knowledge Sync til erfaringspersistering
    - Learning Room til validering

Usage:
    kommandant = Kommandant(room_id=1, name="Analyse Kommandant")
    await kommandant.start()
    result = await kommandant.execute_task(task_context)
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


# ========== Enums & Types ==========

class KommandantStatus(Enum):
    """Status for Kommandanten."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    ANALYZING = "analyzing"
    DELEGATING = "delegating"
    MONITORING = "monitoring"
    LEARNING = "learning"
    ERROR = "error"
    STOPPED = "stopped"


class TaskPriority(Enum):
    """Opgaveprioriteter."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class DelegationStrategy(Enum):
    """Strategier for opgavedelegering."""
    SINGLE_SPECIALIST = "single_specialist"
    PARALLEL_SPECIALISTS = "parallel_specialists"
    SEQUENTIAL_PIPELINE = "sequential_pipeline"
    COLLABORATIVE = "collaborative"


class TaskOutcome(Enum):
    """Mulige udfald af en opgave."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    REQUIRES_HUMAN = "requires_human"


# ========== Data Classes ==========

@dataclass
class TaskAnalysis:
    """Analyse af en opgave."""
    task_id: str
    complexity: float  # 0.0 - 1.0
    required_capabilities: List[str]
    recommended_specialists: List[str]
    delegation_strategy: DelegationStrategy
    estimated_duration_seconds: int
    confidence: float
    analysis_notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "complexity": self.complexity,
            "required_capabilities": self.required_capabilities,
            "recommended_specialists": self.recommended_specialists,
            "delegation_strategy": self.delegation_strategy.value,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "confidence": self.confidence,
            "analysis_notes": self.analysis_notes,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class DelegationRecord:
    """Record af en delegering til specialist."""
    delegation_id: str
    task_id: str
    specialist_id: str
    specialist_type: str
    delegated_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "pending"
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "task_id": self.task_id,
            "specialist_id": self.specialist_id,
            "specialist_type": self.specialist_type,
            "delegated_at": self.delegated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "error": self.error
        }


@dataclass
class Experience:
    """En erfaring fra en afsluttet opgave."""
    experience_id: str
    task_id: str
    task_type: str
    outcome: TaskOutcome
    duration_seconds: float
    specialists_used: List[str]
    delegation_strategy: DelegationStrategy
    success_factors: List[str]
    failure_factors: List[str]
    lessons_learned: List[str]
    confidence_delta: float  # Change in confidence for similar tasks
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "task_id": self.task_id,
            "task_type": self.task_type,
            "outcome": self.outcome.value,
            "duration_seconds": self.duration_seconds,
            "specialists_used": self.specialists_used,
            "delegation_strategy": self.delegation_strategy.value,
            "success_factors": self.success_factors,
            "failure_factors": self.failure_factors,
            "lessons_learned": self.lessons_learned,
            "confidence_delta": self.confidence_delta,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class AuditEntry:
    """Audit trail entry."""
    entry_id: str
    timestamp: datetime
    action: str
    actor: str
    target: str
    details: Dict[str, Any]
    outcome: str
    severity: str = "info"  # info, warning, error, critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "actor": self.actor,
            "target": self.target,
            "details": self.details,
            "outcome": self.outcome,
            "severity": self.severity
        }


# ========== Capability Mapping ==========

CAPABILITY_TO_SPECIALIST = {
    "document_analysis": "document-specialist",
    "document_summary": "document-specialist",
    "ocr": "document-specialist",
    "pdf_processing": "document-specialist",
    "tool_discovery": "tool-explorer",
    "tool_integration": "tool-explorer",
    "creative_writing": "creative-synthesizer",
    "content_synthesis": "creative-synthesizer",
    "knowledge_extraction": "knowledge-architect",
    "education": "knowledge-architect",
    "world_building": "virtual-world-builder",
    "simulation": "virtual-world-builder",
    "quality_assurance": "quality-assurance",
    "self_correction": "quality-assurance",
    "research": "research-specialist",
    "web_search": "research-specialist",
}

SPECIALIST_CAPABILITIES = {
    "document-specialist": ["document_analysis", "document_summary", "ocr", "pdf_processing"],
    "tool-explorer": ["tool_discovery", "tool_integration"],
    "creative-synthesizer": ["creative_writing", "content_synthesis"],
    "knowledge-architect": ["knowledge_extraction", "education"],
    "virtual-world-builder": ["world_building", "simulation"],
    "quality-assurance": ["quality_assurance", "self_correction"],
    "research-specialist": ["research", "web_search"],
}


# ========== Kommandant Core ==========

class Kommandant:
    """
    Central Kommandant Agent for et lærerum.

    Hovedansvar:
        1. Modtage opgaver og analysere dem
        2. Beslutte delegation strategi
        3. Koordinere med specialister
        4. Overvåge opgaveudførelse
        5. Lære fra erfaringer
        6. Rapportere til Control Panel
    """

    def __init__(
        self,
        room_id: int,
        name: str,
        description: str = "",
        auto_learn: bool = True
    ):
        self.kommandant_id = f"kommandant_{room_id}_{uuid.uuid4().hex[:8]}"
        self.room_id = room_id
        self.name = name
        self.description = description
        self.auto_learn = auto_learn

        # Status
        self.status = KommandantStatus.INITIALIZING
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)

        # Statistics
        self.tasks_received = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_delegations = 0
        self.successful_delegations = 0

        # Internal storage
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._delegations: Dict[str, DelegationRecord] = {}
        self._experiences: List[Experience] = []
        self._audit_log: List[AuditEntry] = []

        # Confidence scores per task type (learned over time)
        self._task_type_confidence: Dict[str, float] = {}

        # Available specialists (discovered from registry)
        self._available_specialists: Dict[str, Dict[str, Any]] = {}

        # Message handlers
        self._message_handlers: Dict[str, Callable] = {}

        # Event bus reference
        self._event_bus = None
        self._event_subscription = None

        # Running state
        self._running = False
        self._task_queue: asyncio.Queue = asyncio.Queue()

        logger.info(f"Kommandant created: {self.name} (Room {room_id})")

    # ========== Lifecycle Methods ==========

    async def start(self) -> bool:
        """Start Kommandanten og forbind til infrastruktur."""
        if self._running:
            logger.warning(f"Kommandant {self.name} already running")
            return True

        try:
            self._audit("start", "kommandant", "system", {}, "initiated")

            # Initialize infrastructure connections
            await self._connect_event_bus()
            await self._discover_specialists()
            await self._register_with_control_panel()

            self._running = True
            self.status = KommandantStatus.IDLE
            self.last_activity = datetime.now(timezone.utc)

            self._audit("start", "kommandant", "system", {
                "specialists_available": len(self._available_specialists)
            }, "success")

            logger.info(f"Kommandant {self.name} started successfully")
            return True

        except Exception as e:
            self.status = KommandantStatus.ERROR
            self._audit("start", "kommandant", "system", {"error": str(e)}, "failure", "error")
            logger.error(f"Failed to start Kommandant {self.name}: {e}")
            return False

    async def stop(self) -> None:
        """Stop Kommandanten og frigør ressourcer."""
        if not self._running:
            return

        self._audit("stop", "kommandant", "system", {}, "initiated")

        self._running = False

        # Disconnect from event bus
        if self._event_bus and self._event_subscription:
            try:
                await self._event_bus.unsubscribe(self._event_subscription)
            except Exception as e:
                logger.warning(f"Error unsubscribing from event bus: {e}")

        # Update control panel
        await self._update_control_panel_status("stopped")

        self.status = KommandantStatus.STOPPED
        self._audit("stop", "kommandant", "system", {}, "success")
        logger.info(f"Kommandant {self.name} stopped")

    # ========== Task Processing ==========

    async def receive_task(
        self,
        task_id: str,
        context_id: str,
        prompt: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Modtag en ny opgave til behandling.

        Args:
            task_id: Unik ID for opgaven
            context_id: Kontekst ID
            prompt: Opgavebeskrivelse
            priority: Opgaveprioritet
            metadata: Ekstra metadata

        Returns:
            Dict med modtagelsesbekræftelse
        """
        self.tasks_received += 1
        self.last_activity = datetime.now(timezone.utc)

        self._audit("receive_task", "task", task_id, {
            "prompt_preview": prompt[:100],
            "priority": priority.value
        }, "received")

        # Store task
        task_data = {
            "task_id": task_id,
            "context_id": context_id,
            "prompt": prompt,
            "priority": priority,
            "metadata": metadata or {},
            "received_at": datetime.now(timezone.utc),
            "status": "received"
        }
        self._active_tasks[task_id] = task_data

        # Update Control Panel
        await self._create_task_in_control_panel(task_id, context_id, prompt, metadata)

        return {
            "task_id": task_id,
            "status": "received",
            "kommandant_id": self.kommandant_id,
            "received_at": task_data["received_at"].isoformat()
        }

    async def execute_task(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Udfør en modtaget opgave.

        Args:
            task_id: ID på opgaven der skal udføres

        Returns:
            Dict med opgaveresultat
        """
        if task_id not in self._active_tasks:
            return {"error": f"Task {task_id} not found", "success": False}

        task_data = self._active_tasks[task_id]
        start_time = datetime.now(timezone.utc)

        self._audit("execute_task", "task", task_id, {}, "started")

        try:
            # 1. Analyze task
            self.status = KommandantStatus.ANALYZING
            analysis = await self._analyze_task(task_data)
            task_data["analysis"] = analysis
            task_data["status"] = "analyzed"

            await self._update_task_in_control_panel(task_id, "running", progress=0.2)

            # 2. Delegate to specialists
            self.status = KommandantStatus.DELEGATING
            delegation_results = await self._delegate_task(task_id, analysis)
            task_data["delegations"] = delegation_results
            task_data["status"] = "delegated"

            await self._update_task_in_control_panel(task_id, "running", progress=0.5)

            # 3. Monitor and collect results
            self.status = KommandantStatus.MONITORING
            execution_results = await self._monitor_delegations(task_id, delegation_results)
            task_data["execution_results"] = execution_results

            await self._update_task_in_control_panel(task_id, "running", progress=0.8)

            # 4. Aggregate results
            final_result = self._aggregate_results(execution_results, analysis)
            task_data["final_result"] = final_result
            task_data["status"] = "completed"

            # 5. Learn from experience
            if self.auto_learn:
                self.status = KommandantStatus.LEARNING
                experience = await self._learn_from_task(task_id, task_data, final_result)
                task_data["experience"] = experience

            # Update statistics
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            if final_result.get("success", False):
                self.tasks_completed += 1
                outcome = TaskOutcome.SUCCESS
            else:
                self.tasks_failed += 1
                outcome = TaskOutcome.FAILURE if final_result.get("error") else TaskOutcome.PARTIAL_SUCCESS

            self.status = KommandantStatus.IDLE
            await self._update_task_in_control_panel(task_id, "completed", progress=1.0)

            self._audit("execute_task", "task", task_id, {
                "outcome": outcome.value,
                "duration_seconds": duration
            }, "completed")

            return {
                "task_id": task_id,
                "success": final_result.get("success", False),
                "result": final_result.get("output"),
                "outcome": outcome.value,
                "duration_seconds": duration,
                "specialists_used": list(set(d["specialist_id"] for d in delegation_results)),
                "confidence": final_result.get("confidence", 0.0)
            }

        except Exception as e:
            self.tasks_failed += 1
            self.status = KommandantStatus.ERROR
            task_data["status"] = "failed"
            task_data["error"] = str(e)

            await self._update_task_in_control_panel(task_id, "failed")

            self._audit("execute_task", "task", task_id, {
                "error": str(e)
            }, "failed", "error")

            logger.error(f"Task {task_id} execution failed: {e}")

            return {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "outcome": TaskOutcome.FAILURE.value
            }

    # ========== Task Analysis ==========

    async def _analyze_task(self, task_data: Dict[str, Any]) -> TaskAnalysis:
        """Analyser opgaven for at bestemme delegering."""
        task_id = task_data["task_id"]
        prompt = task_data["prompt"].lower()

        # Identify required capabilities based on prompt keywords
        required_capabilities = []
        complexity = 0.5  # Base complexity

        # Document-related
        if any(kw in prompt for kw in ["dokument", "document", "pdf", "analyse", "summary", "opsummer"]):
            required_capabilities.append("document_analysis")
            if "opsummer" in prompt or "summary" in prompt:
                required_capabilities.append("document_summary")

        # Research-related
        if any(kw in prompt for kw in ["søg", "search", "find", "research", "undersøg"]):
            required_capabilities.append("research")
            complexity += 0.1

        # Creative-related
        if any(kw in prompt for kw in ["skriv", "write", "create", "opret", "kreativ"]):
            required_capabilities.append("creative_writing")
            complexity += 0.1

        # Knowledge-related
        if any(kw in prompt for kw in ["lær", "learn", "forklar", "explain", "viden"]):
            required_capabilities.append("knowledge_extraction")

        # Default to document analysis if no clear match
        if not required_capabilities:
            required_capabilities.append("document_analysis")

        # Map to specialists
        recommended_specialists = []
        for cap in required_capabilities:
            specialist = CAPABILITY_TO_SPECIALIST.get(cap)
            if specialist and specialist not in recommended_specialists:
                recommended_specialists.append(specialist)

        # Determine delegation strategy
        if len(recommended_specialists) == 1:
            strategy = DelegationStrategy.SINGLE_SPECIALIST
        elif len(recommended_specialists) <= 2:
            strategy = DelegationStrategy.SEQUENTIAL_PIPELINE
            complexity += 0.1
        else:
            strategy = DelegationStrategy.PARALLEL_SPECIALISTS
            complexity += 0.2

        # Estimate duration
        base_duration = 10  # seconds
        estimated_duration = int(base_duration * (1 + complexity) * len(recommended_specialists))

        # Calculate confidence based on past experiences
        task_type = "_".join(sorted(required_capabilities))
        confidence = self._task_type_confidence.get(task_type, 0.7)

        analysis = TaskAnalysis(
            task_id=task_id,
            complexity=min(1.0, complexity),
            required_capabilities=required_capabilities,
            recommended_specialists=recommended_specialists,
            delegation_strategy=strategy,
            estimated_duration_seconds=estimated_duration,
            confidence=confidence,
            analysis_notes=f"Identified {len(required_capabilities)} capabilities"
        )

        self._audit("analyze_task", "task", task_id, analysis.to_dict(), "completed")

        return analysis

    # ========== Delegation ==========

    async def _delegate_task(
        self,
        task_id: str,
        analysis: TaskAnalysis
    ) -> List[Dict[str, Any]]:
        """Delegér opgave til specialister baseret på analyse."""
        task_data = self._active_tasks[task_id]
        delegation_results = []

        for specialist_id in analysis.recommended_specialists:
            delegation_id = f"del_{uuid.uuid4().hex[:12]}"

            record = DelegationRecord(
                delegation_id=delegation_id,
                task_id=task_id,
                specialist_id=specialist_id,
                specialist_type=specialist_id,
                delegated_at=datetime.now(timezone.utc),
                input_data={
                    "prompt": task_data["prompt"],
                    "context_id": task_data["context_id"],
                    "metadata": task_data["metadata"]
                }
            )

            self._delegations[delegation_id] = record
            self.total_delegations += 1

            # Send to specialist via event bus
            await self._send_to_specialist(specialist_id, record)

            self._audit("delegate_task", "delegation", delegation_id, {
                "specialist_id": specialist_id,
                "task_id": task_id
            }, "sent")

            delegation_results.append({
                "delegation_id": delegation_id,
                "specialist_id": specialist_id,
                "status": "sent"
            })

        return delegation_results

    async def _send_to_specialist(
        self,
        specialist_id: str,
        record: DelegationRecord
    ) -> bool:
        """Send opgave til specialist via Message Bus."""
        try:
            if self._event_bus:
                from ..infrastructure import CKCMessage, MessagePriority

                message = CKCMessage(
                    message_type="task_delegation",
                    source=self.kommandant_id,
                    destination=specialist_id,
                    payload={
                        "delegation_id": record.delegation_id,
                        "task_id": record.task_id,
                        "input": record.input_data
                    },
                    priority=MessagePriority.NORMAL
                )

                await self._event_bus.publish(
                    exchange="specialist_tasks",
                    routing_key=specialist_id,
                    message=message
                )
                return True

            # Fallback: Direct execution (for MVP)
            await self._execute_specialist_task_directly(specialist_id, record)
            return True

        except Exception as e:
            logger.error(f"Failed to send to specialist {specialist_id}: {e}")
            record.status = "send_failed"
            record.error = str(e)
            return False

    async def _execute_specialist_task_directly(
        self,
        specialist_id: str,
        record: DelegationRecord
    ) -> None:
        """Direct execution of specialist task (for MVP without full Message Bus)."""
        # This simulates what would happen when a specialist receives and processes a task
        record.status = "processing"

        # Simulate specialist work
        await asyncio.sleep(0.5)  # Simulated processing time

        # Generate result based on specialist type
        result = {
            "specialist_id": specialist_id,
            "delegation_id": record.delegation_id,
            "success": True,
            "output": {
                "type": specialist_id,
                "summary": f"Processed by {specialist_id}",
                "content": f"Result for: {record.input_data.get('prompt', '')[:50]}..."
            },
            "confidence": 0.85,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }

        record.status = "completed"
        record.output_data = result
        record.completed_at = datetime.now(timezone.utc)
        self.successful_delegations += 1

    # ========== Monitoring ==========

    async def _monitor_delegations(
        self,
        task_id: str,
        delegations: List[Dict[str, Any]],
        timeout_seconds: int = 60
    ) -> List[Dict[str, Any]]:
        """Overvåg delegeringer og saml resultater."""
        results = []

        for deleg in delegations:
            delegation_id = deleg["delegation_id"]
            record = self._delegations.get(delegation_id)

            if not record:
                continue

            # Wait for completion (with timeout)
            start_wait = datetime.now(timezone.utc)
            while record.status not in ["completed", "failed", "send_failed"]:
                if (datetime.now(timezone.utc) - start_wait).total_seconds() > timeout_seconds:
                    record.status = "timeout"
                    record.error = "Delegation timed out"
                    break
                await asyncio.sleep(0.1)

            results.append({
                "delegation_id": delegation_id,
                "specialist_id": record.specialist_id,
                "status": record.status,
                "output": record.output_data,
                "error": record.error
            })

            self._audit("monitor_delegation", "delegation", delegation_id, {
                "status": record.status
            }, record.status)

        return results

    # ========== Result Aggregation ==========

    def _aggregate_results(
        self,
        execution_results: List[Dict[str, Any]],
        analysis: TaskAnalysis
    ) -> Dict[str, Any]:
        """Aggregér resultater fra alle specialister."""
        successful = [r for r in execution_results if r["status"] == "completed"]
        failed = [r for r in execution_results if r["status"] in ["failed", "timeout", "send_failed"]]

        if not successful:
            return {
                "success": False,
                "output": None,
                "error": "All delegations failed",
                "confidence": 0.0,
                "failed_specialists": [r["specialist_id"] for r in failed]
            }

        # Combine outputs
        combined_output = {}
        total_confidence = 0.0

        for result in successful:
            output = result.get("output", {})
            specialist = result["specialist_id"]

            if isinstance(output, dict):
                combined_output[specialist] = output.get("output", output)
                total_confidence += output.get("confidence", 0.7)
            else:
                combined_output[specialist] = output
                total_confidence += 0.7

        avg_confidence = total_confidence / len(successful) if successful else 0.0

        # Determine overall success
        success = len(successful) >= len(execution_results) / 2

        return {
            "success": success,
            "output": combined_output,
            "confidence": avg_confidence,
            "successful_specialists": [r["specialist_id"] for r in successful],
            "failed_specialists": [r["specialist_id"] for r in failed],
            "aggregation_method": analysis.delegation_strategy.value
        }

    # ========== Learning ==========

    async def _learn_from_task(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Experience:
        """Lær fra opgavens udførelse."""
        analysis = task_data.get("analysis")
        if not analysis:
            analysis = TaskAnalysis(
                task_id=task_id,
                complexity=0.5,
                required_capabilities=[],
                recommended_specialists=[],
                delegation_strategy=DelegationStrategy.SINGLE_SPECIALIST,
                estimated_duration_seconds=10,
                confidence=0.5
            )

        # Calculate duration
        received_at = task_data.get("received_at", datetime.now(timezone.utc))
        if isinstance(received_at, str):
            received_at = datetime.fromisoformat(received_at)
        duration = (datetime.now(timezone.utc) - received_at).total_seconds()

        # Determine outcome
        if result.get("success"):
            outcome = TaskOutcome.SUCCESS
        elif result.get("error"):
            outcome = TaskOutcome.FAILURE
        else:
            outcome = TaskOutcome.PARTIAL_SUCCESS

        # Extract learning factors
        success_factors = []
        failure_factors = []
        lessons = []

        if outcome == TaskOutcome.SUCCESS:
            success_factors.append(f"Strategy {analysis.delegation_strategy.value} worked well")
            for specialist in result.get("successful_specialists", []):
                success_factors.append(f"Specialist {specialist} performed well")

            # Update task type confidence positively
            confidence_delta = 0.05

        elif outcome == TaskOutcome.FAILURE:
            for specialist in result.get("failed_specialists", []):
                failure_factors.append(f"Specialist {specialist} failed")

            if result.get("error"):
                failure_factors.append(f"Error: {result['error'][:50]}")

            lessons.append("Consider alternative specialists for this task type")
            confidence_delta = -0.05

        else:
            confidence_delta = 0.0
            lessons.append("Partial success - review delegation strategy")

        # Update confidence for task type
        task_type = "_".join(sorted(analysis.required_capabilities))
        current_confidence = self._task_type_confidence.get(task_type, 0.7)
        self._task_type_confidence[task_type] = max(0.1, min(0.95, current_confidence + confidence_delta))

        experience = Experience(
            experience_id=f"exp_{uuid.uuid4().hex[:12]}",
            task_id=task_id,
            task_type=task_type,
            outcome=outcome,
            duration_seconds=duration,
            specialists_used=result.get("successful_specialists", []) + result.get("failed_specialists", []),
            delegation_strategy=analysis.delegation_strategy,
            success_factors=success_factors,
            failure_factors=failure_factors,
            lessons_learned=lessons,
            confidence_delta=confidence_delta
        )

        self._experiences.append(experience)

        # Persist to Knowledge Bank
        await self._persist_experience(experience)

        self._audit("learn_from_task", "experience", experience.experience_id, {
            "outcome": outcome.value,
            "confidence_delta": confidence_delta
        }, "recorded")

        return experience

    async def _persist_experience(self, experience: Experience) -> bool:
        """Persist erfaring til Knowledge Bank."""
        try:
            from ..infrastructure import create_entry

            await create_entry(
                title=f"Experience: {experience.task_type}",
                content=experience.to_dict(),
                category="experience",
                tags=["kommandant", experience.outcome.value, experience.task_type],
                metadata={
                    "kommandant_id": self.kommandant_id,
                    "room_id": self.room_id
                },
                target="local"
            )
            return True

        except Exception as e:
            logger.warning(f"Failed to persist experience: {e}")
            return False

    # ========== Infrastructure Integration ==========

    async def _connect_event_bus(self) -> None:
        """Connect to CKC Event Bus."""
        try:
            from ..infrastructure import get_event_bus

            self._event_bus = await get_event_bus()

            # Subscribe to responses
            if self._event_bus:
                self._event_subscription = await self._event_bus.subscribe(
                    exchange="kommandant_responses",
                    routing_key=self.kommandant_id,
                    callback=self._handle_specialist_response
                )

            logger.info(f"Kommandant {self.name} connected to Event Bus")

        except Exception as e:
            logger.warning(f"Could not connect to Event Bus: {e}")

    async def _handle_specialist_response(self, message: Dict[str, Any]) -> None:
        """Handle response from a specialist."""
        delegation_id = message.get("delegation_id")
        if delegation_id in self._delegations:
            record = self._delegations[delegation_id]
            record.status = "completed" if message.get("success") else "failed"
            record.output_data = message
            record.completed_at = datetime.now(timezone.utc)

            if message.get("success"):
                self.successful_delegations += 1

    async def _discover_specialists(self) -> None:
        """Discover available specialists from connector registry."""
        try:
            from ..infrastructure import get_connector_registry

            registry = await get_connector_registry()
            connectors = registry.list_connectors()

            for conn in connectors:
                if "specialist" in conn.get("tags", []):
                    self._available_specialists[conn["id"]] = conn

            logger.info(f"Discovered {len(self._available_specialists)} specialists")

        except Exception as e:
            logger.warning(f"Could not discover specialists: {e}")

    async def _register_with_control_panel(self) -> None:
        """Register with Control Panel."""
        try:
            from ..api.control_panel import _state

            # Add as agent
            from ..api.control_panel import AgentSummary, AgentStatus

            agent_summary = AgentSummary(
                agent_id=self.kommandant_id,
                name=self.name,
                role="Kommandant",
                status=AgentStatus.IDLE,
                tasks_completed=self.tasks_completed,
                uptime_seconds=0.0,
                last_active=datetime.now(timezone.utc)
            )

            _state._agents[self.kommandant_id] = agent_summary

            logger.info(f"Kommandant {self.name} registered with Control Panel")

        except Exception as e:
            logger.warning(f"Could not register with Control Panel: {e}")

    async def _create_task_in_control_panel(
        self,
        task_id: str,
        context_id: str,
        prompt: str,
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Create task entry in Control Panel."""
        try:
            from ..api.control_panel import create_task

            await create_task(
                task_id=task_id,
                context_id=context_id,
                prompt=prompt,
                metadata=metadata or {}
            )

        except Exception as e:
            logger.warning(f"Could not create task in Control Panel: {e}")

    async def _update_task_in_control_panel(
        self,
        task_id: str,
        status: str,
        progress: float = 0.0
    ) -> None:
        """Update task status in Control Panel."""
        try:
            from ..api.control_panel import update_task_status, TaskStatus

            status_map = {
                "running": TaskStatus.RUNNING,
                "completed": TaskStatus.COMPLETED,
                "failed": TaskStatus.FAILED
            }

            await update_task_status(
                task_id=task_id,
                status=status_map.get(status, TaskStatus.RUNNING),
                current_agent=self.kommandant_id,
                progress=progress
            )

        except Exception as e:
            logger.warning(f"Could not update task in Control Panel: {e}")

    async def _update_control_panel_status(self, status: str) -> None:
        """Update Kommandant status in Control Panel."""
        try:
            from ..api.control_panel import _state, AgentStatus

            if self.kommandant_id in _state._agents:
                agent = _state._agents[self.kommandant_id]
                status_map = {
                    "stopped": AgentStatus.OFFLINE,
                    "idle": AgentStatus.IDLE,
                    "busy": AgentStatus.BUSY,
                    "error": AgentStatus.ERROR
                }
                agent.status = status_map.get(status, AgentStatus.IDLE)

        except Exception as e:
            logger.warning(f"Could not update Control Panel status: {e}")

    # ========== Audit ==========

    def _audit(
        self,
        action: str,
        target_type: str,
        target_id: str,
        details: Dict[str, Any],
        outcome: str,
        severity: str = "info"
    ) -> None:
        """Record an audit entry."""
        entry = AuditEntry(
            entry_id=f"audit_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc),
            action=action,
            actor=self.kommandant_id,
            target=f"{target_type}:{target_id}",
            details=details,
            outcome=outcome,
            severity=severity
        )

        self._audit_log.append(entry)

        # Keep only last 1000 entries
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]

        if severity in ["error", "critical"]:
            logger.warning(f"Audit [{severity}]: {action} on {target_type}:{target_id} - {outcome}")

    # ========== Status & Statistics ==========

    def get_status(self) -> Dict[str, Any]:
        """Get current Kommandant status."""
        return {
            "kommandant_id": self.kommandant_id,
            "room_id": self.room_id,
            "name": self.name,
            "status": self.status.value,
            "running": self._running,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "statistics": self.get_statistics(),
            "available_specialists": list(self._available_specialists.keys()),
            "active_tasks": len(self._active_tasks)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get Kommandant statistics."""
        return {
            "tasks_received": self.tasks_received,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_delegations": self.total_delegations,
            "successful_delegations": self.successful_delegations,
            "delegation_success_rate": (
                self.successful_delegations / max(1, self.total_delegations)
            ),
            "experiences_recorded": len(self._experiences),
            "task_type_confidences": dict(self._task_type_confidence)
        }

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return [entry.to_dict() for entry in self._audit_log[-limit:]]

    def get_experiences(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent experiences."""
        return [exp.to_dict() for exp in self._experiences[-limit:]]


# ========== Factory ==========

_kommandanter: Dict[int, Kommandant] = {}


async def create_kommandant(
    room_id: int,
    name: str,
    description: str = "",
    auto_start: bool = True
) -> Kommandant:
    """
    Create a new Kommandant for a learning room.

    Args:
        room_id: Learning room ID
        name: Kommandant name
        description: Description
        auto_start: Start immediately

    Returns:
        Created Kommandant
    """
    kommandant = Kommandant(
        room_id=room_id,
        name=name,
        description=description
    )

    if auto_start:
        await kommandant.start()

    _kommandanter[room_id] = kommandant

    logger.info(f"Kommandant created for room {room_id}: {name}")
    return kommandant


async def get_kommandant(room_id: int) -> Optional[Kommandant]:
    """Get Kommandant for a learning room."""
    return _kommandanter.get(room_id)


def list_kommandanter() -> List[Dict[str, Any]]:
    """List all Kommandanter."""
    return [k.get_status() for k in _kommandanter.values()]


logger.info("CKC Kommandant Core module loaded")
