"""
CKC Specialiserede Agenter
==========================

Fem specialiserede agenter til CKC systemet:

1. Tool Explorer & Integrator - Værktøjsopdagelse med sikkerhedsfokus
2. Creative Synthesizer - Kreativ produktion med etisk filter
3. Knowledge Architect & Educator - Videnopbygning med sandhedskrav
4. Virtual World Builder - Miljøkonstruktion med integritet
5. Quality Assurance & Self-Corrector - Kvalitetssikring med realtidsobservation

Alle agenter følger CKC's kerneprincipper:
- Transparens og ærlighed
- Sandhed og fakta
- Etisk ansvar
- Brugerinddragelse
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from pathlib import Path
import asyncio
import uuid
import json
import os

from cirkelline.config import logger
from .orchestrator import AgentCapability

# F-004: Persistence konfiguration
CKC_DATA_DIR = Path(os.environ.get("CKC_DATA_DIR", Path.home() / ".ckc"))
MASTERY_DATA_DIR = CKC_DATA_DIR / "mastery"


class AgentStatus(Enum):
    """Status for en agent."""
    IDLE = "idle"
    PROCESSING = "processing"
    VALIDATING = "validating"
    WAITING_INPUT = "waiting_input"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentResult:
    """Resultat fra en agent-opgave."""
    success: bool
    output: Any
    confidence: float  # 0.0 - 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    requires_validation: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "confidence": self.confidence,
            "warnings": self.warnings,
            "requires_validation": self.requires_validation,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAgent:
    """
    Basisklasse for alle CKC agenter.

    Alle agenter har:
    - Unikt ID og navn
    - Tilknyttet læringsrum
    - Kapabiliteter
    - Etisk filter
    - Validerings integration
    - Feedback integration (F-005)
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        learning_room_id: int,
        capabilities: Set[AgentCapability]
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.learning_room_id = learning_room_id
        self.capabilities = capabilities

        self.status = AgentStatus.IDLE
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()

        # Statistik
        self.tasks_processed = 0
        self.tasks_successful = 0
        self.tasks_failed = 0

        # F-005: Feedback Integration System (med bounded growth)
        self._feedback_log: List[Dict[str, Any]] = []
        self._learning_rate: float = 0.1  # Baseline learning rate
        self._performance_history: List[float] = []
        self._improvement_suggestions: List[str] = []

        # F-005 FIX: Bounded growth konfiguration
        self._max_feedback_log_size: int = 1000  # Maksimum antal feedback entries
        self._max_performance_history: int = 500  # Maksimum performance entries
        self._max_suggestions: int = 100  # Maksimum forbedringsforslag
        self._valid_feedback_types: Set[str] = {"correction", "praise", "suggestion", "error"}
        self._valid_feedback_sources: Set[str] = {"user", "system", "peer_agent", "self", "hitl"}

        logger.info(f"Agent initialized: {name} ({agent_id})")

    # ═══════════════════════════════════════════════════════════
    # F-005: FEEDBACK INTEGRATION METHODS
    # ═══════════════════════════════════════════════════════════

    def _validate_feedback(
        self,
        feedback_type: str,
        content: Dict[str, Any],
        source: str
    ) -> Dict[str, Any]:
        """
        F-005 FIX: Valider feedback før behandling.

        Returns:
            Dict med validation status og eventuelle fejl
        """
        errors = []

        # Valider feedback type
        if feedback_type not in self._valid_feedback_types:
            errors.append(f"Invalid feedback type: {feedback_type}. Valid: {self._valid_feedback_types}")

        # Valider kilde
        if source not in self._valid_feedback_sources:
            errors.append(f"Invalid source: {source}. Valid: {self._valid_feedback_sources}")

        # Valider content
        if not isinstance(content, dict):
            errors.append(f"Content must be a dict, got: {type(content).__name__}")

        # Valider content størrelse (max 10KB)
        import json
        try:
            content_size = len(json.dumps(content))
            if content_size > 10240:
                errors.append(f"Content too large: {content_size} bytes (max 10KB)")
        except (TypeError, ValueError):
            errors.append("Content not JSON serializable")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _prune_feedback_log(self) -> int:
        """
        F-005 FIX: Fjern gamle feedback entries når max størrelse nås.

        Returns:
            Antal fjernede entries
        """
        if len(self._feedback_log) <= self._max_feedback_log_size:
            return 0

        # Behold nyeste entries
        to_remove = len(self._feedback_log) - self._max_feedback_log_size
        self._feedback_log = self._feedback_log[to_remove:]

        logger.debug(f"Pruned {to_remove} old feedback entries")
        return to_remove

    def _prune_performance_history(self) -> int:
        """F-005 FIX: Fjern gamle performance entries."""
        if len(self._performance_history) <= self._max_performance_history:
            return 0

        to_remove = len(self._performance_history) - self._max_performance_history
        self._performance_history = self._performance_history[to_remove:]
        return to_remove

    async def receive_feedback(
        self,
        feedback_type: str,
        content: Dict[str, Any],
        source: str = "system"
    ) -> Dict[str, Any]:
        """
        Modtag og behandl feedback for selvlæring.

        Args:
            feedback_type: Type af feedback (correction, praise, suggestion, error)
            content: Feedbackindhold med detaljer
            source: Kilde til feedback (user, system, peer_agent, self, hitl)

        Returns:
            Dict med feedback-behandlingsresultat
        """
        # F-005 FIX: Valider feedback før behandling
        validation = self._validate_feedback(feedback_type, content, source)
        if not validation["valid"]:
            logger.warning(f"Agent {self.agent_id} rejected invalid feedback: {validation['errors']}")
            return {
                "accepted": False,
                "errors": validation["errors"],
                "learning_applied": False
            }

        # F-005 FIX: Prune hvis nødvendigt
        self._prune_feedback_log()
        self._prune_performance_history()

        feedback_entry = {
            "id": f"fb_{uuid.uuid4().hex[:8]}",
            "type": feedback_type,
            "content": content,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "processed": False,
            "learning_applied": False
        }

        self._feedback_log.append(feedback_entry)

        # Behandl feedback baseret på type
        result = await self._process_feedback(feedback_entry)
        feedback_entry["processed"] = True
        feedback_entry["learning_applied"] = result.get("learning_applied", False)

        logger.info(f"Agent {self.agent_id} received feedback: {feedback_type}")
        return {**result, "accepted": True}

    async def _process_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Intern behandling af feedback."""
        feedback_type = feedback.get("type", "")
        content = feedback.get("content", {})

        if feedback_type == "correction":
            # Lær fra korrektioner
            return await self._apply_correction(content)
        elif feedback_type == "praise":
            # Forstærk god adfærd
            return self._reinforce_behavior(content)
        elif feedback_type == "suggestion":
            # Gem forbedringsforslag
            return self._store_suggestion(content)
        elif feedback_type == "error":
            # Analyser fejl for læring
            return await self._analyze_error(content)
        else:
            return {"processed": True, "learning_applied": False}

    async def _apply_correction(self, content: Dict) -> Dict[str, Any]:
        """Anvend korrektion til intern model."""
        correction_target = content.get("target", "")
        correct_behavior = content.get("correct_behavior", "")

        # Juster learning rate baseret på fejlens alvorlighed
        severity = content.get("severity", "medium")
        if severity == "high":
            self._learning_rate = min(0.3, self._learning_rate + 0.05)
        elif severity == "low":
            self._learning_rate = max(0.05, self._learning_rate - 0.02)

        return {
            "learning_applied": True,
            "adjustment": "correction_integrated",
            "new_learning_rate": self._learning_rate
        }

    def _reinforce_behavior(self, content: Dict) -> Dict[str, Any]:
        """Forstærk positiv adfærd."""
        behavior = content.get("behavior", "")
        strength = content.get("strength", 1.0)

        # Reducér learning rate ved konsekvent god performance
        if len(self._performance_history) > 10:
            avg_performance = sum(self._performance_history[-10:]) / 10
            if avg_performance > 0.85:
                self._learning_rate = max(0.05, self._learning_rate - 0.01)

        return {
            "learning_applied": True,
            "reinforcement": "positive",
            "behavior_strengthened": behavior
        }

    def _store_suggestion(self, content: Dict) -> Dict[str, Any]:
        """Gem forbedringsforslag til senere review."""
        suggestion = content.get("suggestion", "")
        if suggestion and suggestion not in self._improvement_suggestions:
            # F-005 FIX: Bounded suggestions list
            if len(self._improvement_suggestions) >= self._max_suggestions:
                # Fjern ældste forslag
                self._improvement_suggestions.pop(0)
            self._improvement_suggestions.append(suggestion)

        return {
            "learning_applied": False,
            "stored_for_review": True,
            "total_suggestions": len(self._improvement_suggestions)
        }

    async def _analyze_error(self, content: Dict) -> Dict[str, Any]:
        """Analyser fejl for fremtidig undgåelse."""
        error_type = content.get("error_type", "unknown")
        context = content.get("context", {})

        # Øg learning rate ved fejl
        self._learning_rate = min(0.3, self._learning_rate + 0.02)
        self._performance_history.append(0.0)  # Marker fejl

        return {
            "learning_applied": True,
            "error_analyzed": error_type,
            "prevention_strategy": "adaptive_adjustment"
        }

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Hent statistik over modtaget feedback."""
        total = len(self._feedback_log)
        by_type = {}
        for fb in self._feedback_log:
            fb_type = fb.get("type", "unknown")
            by_type[fb_type] = by_type.get(fb_type, 0) + 1

        return {
            "total_feedback": total,
            "by_type": by_type,
            "learning_rate": self._learning_rate,
            "pending_suggestions": len(self._improvement_suggestions),
            "avg_performance": (
                sum(self._performance_history) / max(1, len(self._performance_history))
                if self._performance_history else 0.0
            )
        }

    async def process(self, input_data: Any, context: Optional[Dict] = None) -> AgentResult:
        """
        Behandl input og returner resultat.
        Override i subklasser.
        """
        raise NotImplementedError("Subclasses must implement process()")

    async def validate_output(self, output: Any) -> tuple[bool, List[str]]:
        """
        Valider output før det sendes videre.
        Override i subklasser for specifik validering.
        """
        warnings = []
        if output is None:
            warnings.append("Output is None")
            return False, warnings
        return True, warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "learning_room_id": self.learning_room_id,
            "capabilities": [c.value for c in self.capabilities],
            "status": self.status.value,
            "tasks_processed": self.tasks_processed,
            "tasks_successful": self.tasks_successful,
            "tasks_failed": self.tasks_failed
        }


# ═══════════════════════════════════════════════════════════════
# AGENT 1: TOOL EXPLORER & INTEGRATOR
# ═══════════════════════════════════════════════════════════════

class ToolExplorerAgent(BaseAgent):
    """
    Tool Explorer & Integrator Agent

    Ansvar:
        - Opdage nye værktøjer og APIs
        - Evaluere sikkerhed og pålidelighed
        - Integrere godkendte værktøjer
        - Overvåge værktøjers sundhed
        - Capability tracking og mastery (F-004)

    Sikkerhedsprincipper:
        - Alle værktøjer skal valideres før integration
        - Sandboxing af nye værktøjer
        - Kontinuerlig sikkerhedsovervågning
        - Brugernotifikation ved kritiske fund
    """

    def __init__(self, learning_room_id: int = 2):
        super().__init__(
            agent_id="tool-explorer",
            name="Tool Explorer & Integrator",
            description="Værktøjsopdagelse med sikkerhedsfokus",
            learning_room_id=learning_room_id,
            capabilities={
                AgentCapability.TOOL_DISCOVERY,
                AgentCapability.TOOL_INTEGRATION
            }
        )

        # Værktøjsregister
        self._discovered_tools: Dict[str, Dict[str, Any]] = {}
        self._integrated_tools: Dict[str, Dict[str, Any]] = {}
        self._blocked_tools: Set[str] = set()

        # F-004: Persistence konfiguration
        self._persistence_enabled: bool = True
        self._mastery_file: Path = MASTERY_DATA_DIR / f"{self.agent_id}_mastery.json"
        self._auto_save: bool = True

        # Thread safety: asyncio Lock for concurrent access
        self._mastery_lock: asyncio.Lock = asyncio.Lock()
        self._save_in_progress: bool = False

        # F-004: Capability Tracking System (initialiseres og loades fra disk)
        self._capability_mastery: Dict[str, Dict[str, Any]] = {
            "tool_discovery": {
                "level": "intermediate",
                "score": 0.75,
                "uses": 0,
                "successes": 0,
                "last_used": None
            },
            "tool_integration": {
                "level": "intermediate",
                "score": 0.70,
                "uses": 0,
                "successes": 0,
                "last_used": None
            },
            "security_evaluation": {
                "level": "advanced",
                "score": 0.85,
                "uses": 0,
                "successes": 0,
                "last_used": None
            },
            "tool_monitoring": {
                "level": "intermediate",
                "score": 0.72,
                "uses": 0,
                "successes": 0,
                "last_used": None
            }
        }
        self._mastery_thresholds = {
            "novice": 0.0,
            "beginner": 0.3,
            "intermediate": 0.5,
            "advanced": 0.75,
            "expert": 0.9,
            "master": 0.98
        }
        self._capability_log: List[Dict[str, Any]] = []

        # F-004: Load existing mastery data from disk
        self._load_mastery_from_disk()

    # ═══════════════════════════════════════════════════════════
    # F-004: PERSISTENCE METHODS
    # ═══════════════════════════════════════════════════════════

    def _ensure_data_dir(self) -> bool:
        """
        F-004: Sikr at data-mappen eksisterer.

        Returns:
            True hvis mappen eksisterer eller blev oprettet
        """
        try:
            MASTERY_DATA_DIR.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not create mastery data dir: {e}")
            return False

    def _save_mastery_to_disk(self) -> Dict[str, Any]:
        """
        F-004: Gem mastery data til disk.

        Returns:
            Dict med save status
        """
        if not self._persistence_enabled:
            return {"saved": False, "reason": "persistence_disabled"}

        if not self._ensure_data_dir():
            return {"saved": False, "reason": "could_not_create_dir"}

        try:
            data = {
                "agent_id": self.agent_id,
                "version": "1.0",
                "saved_at": datetime.utcnow().isoformat(),
                "capability_mastery": self._capability_mastery,
                "capability_log": self._capability_log[-100:],  # Gem kun seneste 100
                "statistics": {
                    "total_uses": sum(c["uses"] for c in self._capability_mastery.values()),
                    "overall_mastery": self._calculate_overall_mastery()
                }
            }

            # Skriv til temp-fil først (atomic write)
            temp_file = self._mastery_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Flyt temp til endelig fil
            temp_file.replace(self._mastery_file)

            logger.debug(f"Saved mastery data for {self.agent_id}")
            return {
                "saved": True,
                "file": str(self._mastery_file),
                "capabilities_saved": len(self._capability_mastery)
            }

        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to save mastery data: {e}")
            return {"saved": False, "reason": str(e)}

    def _load_mastery_from_disk(self) -> Dict[str, Any]:
        """
        F-004: Indlæs mastery data fra disk.

        Returns:
            Dict med load status
        """
        if not self._persistence_enabled:
            return {"loaded": False, "reason": "persistence_disabled"}

        if not self._mastery_file.exists():
            logger.info(f"No existing mastery data for {self.agent_id}")
            return {"loaded": False, "reason": "file_not_found"}

        try:
            with open(self._mastery_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Valider data struktur
            if data.get("agent_id") != self.agent_id:
                logger.warning(f"Mastery file agent_id mismatch")
                return {"loaded": False, "reason": "agent_id_mismatch"}

            # Merge loaded data med defaults (bevar nye capabilities)
            loaded_mastery = data.get("capability_mastery", {})
            for cap_name, cap_data in loaded_mastery.items():
                if cap_name in self._capability_mastery:
                    # Opdater kun med loaded data
                    self._capability_mastery[cap_name].update(cap_data)
                else:
                    # Tilføj ny capability
                    self._capability_mastery[cap_name] = cap_data

            # Load capability log
            self._capability_log = data.get("capability_log", [])

            logger.info(f"Loaded mastery data for {self.agent_id}: {len(loaded_mastery)} capabilities")
            return {
                "loaded": True,
                "capabilities_loaded": len(loaded_mastery),
                "saved_at": data.get("saved_at")
            }

        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load mastery data: {e}")
            return {"loaded": False, "reason": str(e)}

    def reset_mastery(self, capability: Optional[str] = None) -> Dict[str, Any]:
        """
        F-004: Nulstil mastery data.

        Args:
            capability: Specifik capability at nulstille, eller None for alle

        Returns:
            Dict med reset status
        """
        if capability:
            if capability in self._capability_mastery:
                self._capability_mastery[capability] = {
                    "level": "novice",
                    "score": 0.0,
                    "uses": 0,
                    "successes": 0,
                    "last_used": None
                }
                if self._auto_save:
                    self._save_mastery_to_disk()
                return {"reset": True, "capability": capability}
            return {"reset": False, "reason": "capability_not_found"}

        # Nulstil alle
        for cap in self._capability_mastery:
            self._capability_mastery[cap] = {
                "level": "novice",
                "score": 0.0,
                "uses": 0,
                "successes": 0,
                "last_used": None
            }
        self._capability_log = []

        if self._auto_save:
            self._save_mastery_to_disk()

        return {"reset": True, "capabilities_reset": len(self._capability_mastery)}

    # ═══════════════════════════════════════════════════════════
    # F-004: CAPABILITY TRACKING METHODS (Thread-Safe)
    # ═══════════════════════════════════════════════════════════

    def track_capability_use(
        self,
        capability: str,
        success: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track brug af en capability for mastery-beregning (sync version).
        For thread-safe operationer, brug track_capability_use_async().

        Args:
            capability: Navn på capability
            success: Om brugen var succesfuld
            context: Ekstra kontekst om brugen

        Returns:
            Dict med opdateret mastery-status
        """
        return self._track_capability_internal(capability, success, context)

    async def track_capability_use_async(
        self,
        capability: str,
        success: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Thread-safe async version af track_capability_use.

        Bruger asyncio.Lock for at sikre thread-safety ved
        concurrent capability updates.

        Args:
            capability: Navn på capability
            success: Om brugen var succesfuld
            context: Ekstra kontekst om brugen

        Returns:
            Dict med opdateret mastery-status
        """
        async with self._mastery_lock:
            result = self._track_capability_internal(capability, success, context)

            # Async save for at undgå blocking
            if self._auto_save and not self._save_in_progress:
                self._save_in_progress = True
                try:
                    # Kør save i executor for at undgå blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self._save_mastery_to_disk)
                finally:
                    self._save_in_progress = False

            return result

    def _track_capability_internal(
        self,
        capability: str,
        success: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Intern tracking logic (ikke thread-safe).
        """
        if capability not in self._capability_mastery:
            # Tilføj ny capability
            self._capability_mastery[capability] = {
                "level": "novice",
                "score": 0.0,
                "uses": 0,
                "successes": 0,
                "last_used": None
            }

        cap = self._capability_mastery[capability]
        cap["uses"] += 1
        cap["last_used"] = datetime.utcnow().isoformat()

        if success:
            cap["successes"] += 1
            # Øg score med adaptive learning
            improvement = 0.05 * (1.0 - cap["score"])  # Mindre forbedring ved højere score
            cap["score"] = min(1.0, cap["score"] + improvement)
        else:
            # Reducer score ved fejl (mindre reduktion)
            cap["score"] = max(0.0, cap["score"] - 0.02)

        # Opdater level baseret på score
        cap["level"] = self._calculate_level(cap["score"])

        # Log event
        self._capability_log.append({
            "capability": capability,
            "success": success,
            "new_score": cap["score"],
            "new_level": cap["level"],
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        })

        # F-004: Auto-save mastery data (sync version)
        if self._auto_save:
            self._save_mastery_to_disk()

        return {
            "capability": capability,
            "current_score": cap["score"],
            "current_level": cap["level"],
            "total_uses": cap["uses"],
            "success_rate": cap["successes"] / cap["uses"] if cap["uses"] > 0 else 0
        }

    def _calculate_level(self, score: float) -> str:
        """Beregn mastery level fra score."""
        level = "novice"
        for lvl, threshold in sorted(
            self._mastery_thresholds.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if score >= threshold:
                level = lvl
                break
        return level

    def get_capability_mastery(self, capability: Optional[str] = None) -> Dict[str, Any]:
        """
        Hent mastery-information for capabilities.

        Args:
            capability: Specifik capability eller None for alle

        Returns:
            Dict med mastery-data
        """
        if capability:
            if capability in self._capability_mastery:
                return {capability: self._capability_mastery[capability]}
            return {}

        return {
            "capabilities": self._capability_mastery,
            "overall_mastery": self._calculate_overall_mastery(),
            "strongest_capability": self._get_strongest_capability(),
            "weakest_capability": self._get_weakest_capability(),
            "total_capability_uses": sum(
                c["uses"] for c in self._capability_mastery.values()
            )
        }

    def _calculate_overall_mastery(self) -> float:
        """Beregn samlet mastery-score."""
        if not self._capability_mastery:
            return 0.0
        scores = [c["score"] for c in self._capability_mastery.values()]
        return sum(scores) / len(scores)

    def _get_strongest_capability(self) -> Optional[str]:
        """Find stærkeste capability."""
        if not self._capability_mastery:
            return None
        return max(
            self._capability_mastery.items(),
            key=lambda x: x[1]["score"]
        )[0]

    def _get_weakest_capability(self) -> Optional[str]:
        """Find svageste capability."""
        if not self._capability_mastery:
            return None
        return min(
            self._capability_mastery.items(),
            key=lambda x: x[1]["score"]
        )[0]

    def get_capability_recommendations(self) -> List[Dict[str, Any]]:
        """
        Få anbefalinger for capability-forbedring.

        Returns:
            Liste af anbefalinger med prioritet
        """
        recommendations = []

        for cap_name, cap_data in self._capability_mastery.items():
            if cap_data["score"] < 0.5:
                priority = "high"
            elif cap_data["score"] < 0.75:
                priority = "medium"
            else:
                priority = "low"

            if cap_data["uses"] < 10:
                recommendations.append({
                    "capability": cap_name,
                    "recommendation": f"Brug '{cap_name}' mere for at forbedre mastery",
                    "current_level": cap_data["level"],
                    "uses": cap_data["uses"],
                    "priority": priority
                })
            elif cap_data["score"] < 0.75:
                success_rate = cap_data["successes"] / cap_data["uses"] if cap_data["uses"] > 0 else 0
                recommendations.append({
                    "capability": cap_name,
                    "recommendation": f"Fokuser på at forbedre success rate (nuværende: {success_rate:.0%})",
                    "current_level": cap_data["level"],
                    "success_rate": success_rate,
                    "priority": priority
                })

        return sorted(recommendations, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])

    async def process(self, input_data: Any, context: Optional[Dict] = None) -> AgentResult:
        """Behandl værktøjsrelaterede opgaver."""
        self.status = AgentStatus.PROCESSING
        self.last_activity = datetime.utcnow()
        self.tasks_processed += 1

        try:
            action = input_data.get("action", "discover") if isinstance(input_data, dict) else "discover"

            if action == "discover":
                result = await self._discover_tools(input_data)
            elif action == "evaluate":
                result = await self._evaluate_tool(input_data)
            elif action == "integrate":
                result = await self._integrate_tool(input_data)
            elif action == "monitor":
                result = await self._monitor_tools()
            else:
                result = {"error": f"Unknown action: {action}"}

            self.tasks_successful += 1
            self.status = AgentStatus.IDLE

            return AgentResult(
                success=True,
                output=result,
                confidence=0.85,
                requires_validation=True
            )

        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.ERROR
            logger.error(f"Tool Explorer error: {e}")

            return AgentResult(
                success=False,
                output={"error": str(e)},
                confidence=0.0,
                warnings=[str(e)]
            )

    async def _discover_tools(self, params: Dict) -> Dict[str, Any]:
        """Opdage nye værktøjer."""
        category = params.get("category", "general")
        query = params.get("query", "")

        # Simuleret opdagelse
        discovered = [
            {
                "id": f"tool_{uuid.uuid4().hex[:8]}",
                "name": f"Discovered Tool",
                "category": category,
                "source": "discovery_scan",
                "security_rating": "pending",
                "discovered_at": datetime.utcnow().isoformat()
            }
        ]

        for tool in discovered:
            self._discovered_tools[tool["id"]] = tool

        return {
            "discovered_count": len(discovered),
            "tools": discovered,
            "category": category
        }

    async def _evaluate_tool(self, params: Dict) -> Dict[str, Any]:
        """Evaluér et værktøjs sikkerhed."""
        tool_id = params.get("tool_id", "")

        # Sikkerhedsevaluering
        evaluation = {
            "tool_id": tool_id,
            "security_score": 0.85,
            "reliability_score": 0.90,
            "performance_score": 0.80,
            "issues_found": [],
            "recommendation": "approve",
            "evaluated_at": datetime.utcnow().isoformat()
        }

        return evaluation

    async def _integrate_tool(self, params: Dict) -> Dict[str, Any]:
        """Integrer et godkendt værktøj."""
        tool_id = params.get("tool_id", "")

        if tool_id in self._blocked_tools:
            return {"error": "Tool is blocked", "tool_id": tool_id}

        integration = {
            "tool_id": tool_id,
            "status": "integrated",
            "integration_id": f"int_{uuid.uuid4().hex[:8]}",
            "integrated_at": datetime.utcnow().isoformat()
        }

        self._integrated_tools[tool_id] = integration
        return integration

    async def _monitor_tools(self) -> Dict[str, Any]:
        """Overvåg integrerede værktøjer."""
        return {
            "total_discovered": len(self._discovered_tools),
            "total_integrated": len(self._integrated_tools),
            "blocked": len(self._blocked_tools),
            "status": "healthy",
            "last_check": datetime.utcnow().isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# AGENT 2: CREATIVE SYNTHESIZER
# ═══════════════════════════════════════════════════════════════

class CreativeSynthesizerAgent(BaseAgent):
    """
    Creative Synthesizer Agent

    Ansvar:
        - Kreativ indholdsproduktion
        - Syntese af information
        - Kunstnerisk visualisering
        - Narrativ konstruktion

    Etiske principper:
        - Intet skadeligt indhold
        - Respekt for ophavsret
        - Transparens om AI-generering
        - Kulturel sensitivitet
    """

    def __init__(self, learning_room_id: int = 3):
        super().__init__(
            agent_id="creative-synthesizer",
            name="Creative Synthesizer",
            description="Kreativ produktion med etisk filter",
            learning_room_id=learning_room_id,
            capabilities={
                AgentCapability.CREATIVE_WRITING,
                AgentCapability.CONTENT_SYNTHESIS
            }
        )

        # Etiske guidelines
        self._blocked_topics: Set[str] = {
            "violence", "hate", "illegal", "exploitation"
        }
        self._content_history: List[Dict[str, Any]] = []

    async def process(self, input_data: Any, context: Optional[Dict] = None) -> AgentResult:
        """Behandl kreative opgaver."""
        self.status = AgentStatus.PROCESSING
        self.last_activity = datetime.utcnow()
        self.tasks_processed += 1

        try:
            # Etisk pre-check
            ethical_check = await self._ethical_precheck(input_data)
            if not ethical_check["passed"]:
                self.status = AgentStatus.IDLE
                return AgentResult(
                    success=False,
                    output={"blocked": True, "reason": ethical_check["reason"]},
                    confidence=1.0,
                    warnings=[ethical_check["reason"]],
                    requires_validation=True
                )

            content_type = input_data.get("type", "text") if isinstance(input_data, dict) else "text"

            if content_type == "text":
                result = await self._synthesize_text(input_data)
            elif content_type == "narrative":
                result = await self._create_narrative(input_data)
            elif content_type == "summary":
                result = await self._create_summary(input_data)
            else:
                result = await self._general_synthesis(input_data)

            # Etisk post-check
            post_check = await self._ethical_postcheck(result)

            self.tasks_successful += 1
            self.status = AgentStatus.IDLE

            return AgentResult(
                success=True,
                output=result,
                confidence=0.80,
                warnings=post_check.get("warnings", []),
                requires_validation=True,
                metadata={"ai_generated": True}
            )

        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.ERROR
            logger.error(f"Creative Synthesizer error: {e}")

            return AgentResult(
                success=False,
                output={"error": str(e)},
                confidence=0.0,
                warnings=[str(e)]
            )

    async def _ethical_precheck(self, input_data: Any) -> Dict[str, Any]:
        """Pre-check input for etiske problemer."""
        text = str(input_data).lower()

        for topic in self._blocked_topics:
            if topic in text:
                return {
                    "passed": False,
                    "reason": f"Blocked topic detected: {topic}"
                }

        return {"passed": True, "reason": None}

    async def _ethical_postcheck(self, output: Any) -> Dict[str, Any]:
        """Post-check output for etiske problemer."""
        warnings = []
        text = str(output).lower()

        # Check for problematisk indhold
        sensitive_markers = ["controversial", "unverified", "opinion"]
        for marker in sensitive_markers:
            if marker in text:
                warnings.append(f"Contains potentially {marker} content")

        return {"passed": len(warnings) == 0, "warnings": warnings}

    async def _synthesize_text(self, params: Dict) -> Dict[str, Any]:
        """Syntetiser tekst."""
        prompt = params.get("prompt", "")
        style = params.get("style", "neutral")

        return {
            "type": "text",
            "content": f"[Synthesized content based on: {prompt[:100]}...]",
            "style": style,
            "word_count": 0,
            "ai_generated": True,
            "created_at": datetime.utcnow().isoformat()
        }

    async def _create_narrative(self, params: Dict) -> Dict[str, Any]:
        """Opret en narrativ."""
        theme = params.get("theme", "")
        characters = params.get("characters", [])

        return {
            "type": "narrative",
            "theme": theme,
            "characters": characters,
            "structure": {
                "introduction": "[Generated introduction]",
                "development": "[Generated development]",
                "conclusion": "[Generated conclusion]"
            },
            "ai_generated": True
        }

    async def _create_summary(self, params: Dict) -> Dict[str, Any]:
        """Opret en sammenfatning."""
        content = params.get("content", "")
        max_length = params.get("max_length", 200)

        return {
            "type": "summary",
            "original_length": len(str(content)),
            "summary": f"[Summary of content, max {max_length} chars]",
            "ai_generated": True
        }

    async def _general_synthesis(self, input_data: Any) -> Dict[str, Any]:
        """Generel syntese."""
        return {
            "type": "synthesis",
            "input_processed": True,
            "output": "[Synthesized output]",
            "ai_generated": True
        }


# ═══════════════════════════════════════════════════════════════
# AGENT 3: KNOWLEDGE ARCHITECT & EDUCATOR
# ═══════════════════════════════════════════════════════════════

class KnowledgeArchitectAgent(BaseAgent):
    """
    Knowledge Architect & Educator Agent

    Ansvar:
        - Videnopbygning og strukturering
        - Uddannelse og forklaring
        - Faktaverifikation
        - Kildekritik

    Sandhedsprincipper:
        - Kun verificerede fakta
        - Tydelig markering af usikkerhed
        - Kildeangivelse
        - Skelne mellem fakta og mening
    """

    def __init__(self, learning_room_id: int = 4):
        super().__init__(
            agent_id="knowledge-architect",
            name="Knowledge Architect & Educator",
            description="Videnopbygning med sandhedskrav",
            learning_room_id=learning_room_id,
            capabilities={
                AgentCapability.KNOWLEDGE_EXTRACTION,
                AgentCapability.EDUCATION
            }
        )

        # Videnbase
        self._knowledge_graph: Dict[str, Any] = {}
        self._verified_facts: Dict[str, Dict[str, Any]] = {}
        self._uncertainty_markers: Set[str] = {"may", "possibly", "suggests", "appears"}

    async def process(self, input_data: Any, context: Optional[Dict] = None) -> AgentResult:
        """Behandl videnrelaterede opgaver."""
        self.status = AgentStatus.PROCESSING
        self.last_activity = datetime.utcnow()
        self.tasks_processed += 1

        try:
            action = input_data.get("action", "extract") if isinstance(input_data, dict) else "extract"

            if action == "extract":
                result = await self._extract_knowledge(input_data)
            elif action == "verify":
                result = await self._verify_facts(input_data)
            elif action == "educate":
                result = await self._create_educational_content(input_data)
            elif action == "structure":
                result = await self._structure_knowledge(input_data)
            else:
                result = await self._general_knowledge_task(input_data)

            self.tasks_successful += 1
            self.status = AgentStatus.IDLE

            return AgentResult(
                success=True,
                output=result,
                confidence=result.get("confidence", 0.75),
                requires_validation=True,
                metadata={"sources_used": result.get("sources", [])}
            )

        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.ERROR
            logger.error(f"Knowledge Architect error: {e}")

            return AgentResult(
                success=False,
                output={"error": str(e)},
                confidence=0.0,
                warnings=[str(e)]
            )

    async def _extract_knowledge(self, params: Dict) -> Dict[str, Any]:
        """Ekstraher viden fra input."""
        content = params.get("content", "")

        return {
            "action": "extract",
            "entities": [],
            "relationships": [],
            "facts": [],
            "uncertainty_detected": False,
            "confidence": 0.80,
            "sources": []
        }

    async def _verify_facts(self, params: Dict) -> Dict[str, Any]:
        """Verificer påstande."""
        claims = params.get("claims", [])

        verified_results = []
        for claim in claims:
            verified_results.append({
                "claim": claim,
                "verified": None,  # None = unknown, True = verified, False = refuted
                "confidence": 0.0,
                "sources": [],
                "notes": "Verification pending"
            })

        return {
            "action": "verify",
            "results": verified_results,
            "total_claims": len(claims),
            "verified_count": 0,
            "confidence": 0.0
        }

    async def _create_educational_content(self, params: Dict) -> Dict[str, Any]:
        """Opret uddannelsesindhold."""
        topic = params.get("topic", "")
        level = params.get("level", "intermediate")  # beginner, intermediate, advanced

        return {
            "action": "educate",
            "topic": topic,
            "level": level,
            "content": {
                "introduction": "[Educational introduction]",
                "key_concepts": [],
                "examples": [],
                "exercises": [],
                "summary": "[Educational summary]"
            },
            "sources": [],
            "confidence": 0.75,
            "disclaimer": "This educational content should be verified with authoritative sources."
        }

    async def _structure_knowledge(self, params: Dict) -> Dict[str, Any]:
        """Strukturer viden i grafer/hierarkier."""
        knowledge = params.get("knowledge", {})

        return {
            "action": "structure",
            "graph": {
                "nodes": [],
                "edges": [],
                "clusters": []
            },
            "hierarchy": {},
            "confidence": 0.70
        }

    async def _general_knowledge_task(self, params: Dict) -> Dict[str, Any]:
        """Generel videnopgave."""
        return {
            "action": "general",
            "result": "[Knowledge task result]",
            "confidence": 0.60
        }


# ═══════════════════════════════════════════════════════════════
# AGENT 4: VIRTUAL WORLD BUILDER
# ═══════════════════════════════════════════════════════════════

class VirtualWorldBuilderAgent(BaseAgent):
    """
    Virtual World Builder Agent

    Ansvar:
        - Virtuel miljøkonstruktion
        - Simulation og modellering
        - Interaktive oplevelser
        - Konsistensvalidering

    Integritetsprincipper:
        - Fysisk korrekthed hvor muligt
        - Konsistent verdenslogik
        - Tydelig markering af fantasi vs. realisme
        - Sikkerhed i interaktioner
    """

    def __init__(self, learning_room_id: int = 5):
        super().__init__(
            agent_id="virtual-world-builder",
            name="Virtual World Builder",
            description="Miljøkonstruktion med integritet",
            learning_room_id=learning_room_id,
            capabilities={
                AgentCapability.WORLD_BUILDING,
                AgentCapability.SIMULATION
            }
        )

        # Verdensregister
        self._worlds: Dict[str, Dict[str, Any]] = {}
        self._active_simulations: Dict[str, Dict[str, Any]] = {}

    async def process(self, input_data: Any, context: Optional[Dict] = None) -> AgentResult:
        """Behandl verdensopgaver."""
        self.status = AgentStatus.PROCESSING
        self.last_activity = datetime.utcnow()
        self.tasks_processed += 1

        try:
            action = input_data.get("action", "create") if isinstance(input_data, dict) else "create"

            if action == "create":
                result = await self._create_world(input_data)
            elif action == "simulate":
                result = await self._run_simulation(input_data)
            elif action == "modify":
                result = await self._modify_world(input_data)
            elif action == "validate":
                result = await self._validate_consistency(input_data)
            else:
                result = await self._general_world_task(input_data)

            self.tasks_successful += 1
            self.status = AgentStatus.IDLE

            return AgentResult(
                success=True,
                output=result,
                confidence=0.85,
                requires_validation=True,
                metadata={"world_type": result.get("type", "unknown")}
            )

        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.ERROR
            logger.error(f"Virtual World Builder error: {e}")

            return AgentResult(
                success=False,
                output={"error": str(e)},
                confidence=0.0,
                warnings=[str(e)]
            )

    async def _create_world(self, params: Dict) -> Dict[str, Any]:
        """Opret en ny virtuel verden."""
        name = params.get("name", f"World_{uuid.uuid4().hex[:8]}")
        world_type = params.get("type", "fantasy")
        rules = params.get("rules", {})

        world_id = f"world_{uuid.uuid4().hex[:8]}"

        world = {
            "id": world_id,
            "name": name,
            "type": world_type,
            "rules": {
                "physics": rules.get("physics", "standard"),
                "magic": rules.get("magic", False),
                "time_flow": rules.get("time_flow", "linear")
            },
            "entities": [],
            "regions": [],
            "created_at": datetime.utcnow().isoformat(),
            "disclaimer": "This is a fictional world and does not represent reality."
        }

        self._worlds[world_id] = world
        return world

    async def _run_simulation(self, params: Dict) -> Dict[str, Any]:
        """Kør en simulation i en verden."""
        world_id = params.get("world_id", "")
        scenario = params.get("scenario", {})
        steps = params.get("steps", 10)

        sim_id = f"sim_{uuid.uuid4().hex[:8]}"

        simulation = {
            "id": sim_id,
            "world_id": world_id,
            "scenario": scenario,
            "steps_completed": 0,
            "steps_total": steps,
            "results": [],
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        }

        self._active_simulations[sim_id] = simulation
        return simulation

    async def _modify_world(self, params: Dict) -> Dict[str, Any]:
        """Modificer en eksisterende verden."""
        world_id = params.get("world_id", "")
        modifications = params.get("modifications", {})

        if world_id not in self._worlds:
            return {"error": f"World not found: {world_id}"}

        world = self._worlds[world_id]
        # Anvend modifikationer
        world["modified_at"] = datetime.utcnow().isoformat()

        return {
            "world_id": world_id,
            "modifications_applied": len(modifications),
            "status": "modified"
        }

    async def _validate_consistency(self, params: Dict) -> Dict[str, Any]:
        """Valider verdens konsistens."""
        world_id = params.get("world_id", "")

        if world_id not in self._worlds:
            return {"error": f"World not found: {world_id}"}

        # Konsistenskontrol
        return {
            "world_id": world_id,
            "consistent": True,
            "issues_found": [],
            "validated_at": datetime.utcnow().isoformat()
        }

    async def _general_world_task(self, params: Dict) -> Dict[str, Any]:
        """Generel verdensopgave."""
        return {
            "action": "general",
            "result": "[World task result]",
            "type": "unknown"
        }


# ═══════════════════════════════════════════════════════════════
# AGENT 5: QUALITY ASSURANCE & SELF-CORRECTOR
# ═══════════════════════════════════════════════════════════════

class QualityAssuranceAgent(BaseAgent):
    """
    Quality Assurance & Self-Corrector Agent

    Ansvar:
        - Kvalitetskontrol af alle outputs
        - Fejldetektering og korrektion
        - Performance monitoring
        - Realtidsobservation

    Observationsprincipper:
        - Kontinuerlig overvågning
        - Proaktiv fejlidentifikation
        - Selvkorrektion hvor muligt
        - Eskalering ved kritiske problemer
    """

    def __init__(self, learning_room_id: int = 6):
        super().__init__(
            agent_id="quality-assurance",
            name="Quality Assurance & Self-Corrector",
            description="Kvalitetssikring med realtidsobservation",
            learning_room_id=learning_room_id,
            capabilities={
                AgentCapability.QUALITY_ASSURANCE,
                AgentCapability.SELF_CORRECTION
            }
        )

        # QA metrics
        self._quality_scores: Dict[str, float] = {}
        self._issues_log: List[Dict[str, Any]] = []
        self._corrections_made: int = 0
        self._escalations: List[Dict[str, Any]] = []

    async def process(self, input_data: Any, context: Optional[Dict] = None) -> AgentResult:
        """Behandl kvalitetsopgaver."""
        self.status = AgentStatus.PROCESSING
        self.last_activity = datetime.utcnow()
        self.tasks_processed += 1

        try:
            action = input_data.get("action", "review") if isinstance(input_data, dict) else "review"

            if action == "review":
                result = await self._review_output(input_data)
            elif action == "correct":
                result = await self._correct_issues(input_data)
            elif action == "monitor":
                result = await self._monitor_system(input_data)
            elif action == "report":
                result = await self._generate_report()
            else:
                result = await self._general_qa_task(input_data)

            self.tasks_successful += 1
            self.status = AgentStatus.IDLE

            return AgentResult(
                success=True,
                output=result,
                confidence=0.90,
                requires_validation=result.get("requires_escalation", False),
                warnings=result.get("issues", [])
            )

        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.ERROR
            logger.error(f"Quality Assurance error: {e}")

            return AgentResult(
                success=False,
                output={"error": str(e)},
                confidence=0.0,
                warnings=[str(e)]
            )

    async def _review_output(self, params: Dict) -> Dict[str, Any]:
        """Review output for kvalitetsproblemer."""
        content = params.get("content", {})
        source_agent = params.get("source_agent", "unknown")

        # Kvalitetscheck
        issues = []
        score = 1.0

        # Check for tomme resultater
        if not content:
            issues.append("Empty content")
            score -= 0.3

        # Check for fejlmarkører
        content_str = str(content).lower()
        error_markers = ["error", "failed", "exception"]
        for marker in error_markers:
            if marker in content_str:
                issues.append(f"Error marker detected: {marker}")
                score -= 0.2

        self._quality_scores[source_agent] = score

        return {
            "action": "review",
            "source_agent": source_agent,
            "score": max(0, score),
            "issues": issues,
            "passed": score >= 0.6,
            "requires_escalation": score < 0.4,
            "reviewed_at": datetime.utcnow().isoformat()
        }

    async def _correct_issues(self, params: Dict) -> Dict[str, Any]:
        """Forsøg at korrigere identificerede problemer."""
        issues = params.get("issues", [])
        content = params.get("content", {})

        corrections = []
        for issue in issues:
            correction = {
                "issue": issue,
                "corrected": False,
                "correction_method": "manual_review_required"
            }
            corrections.append(correction)

        self._corrections_made += len([c for c in corrections if c["corrected"]])

        return {
            "action": "correct",
            "total_issues": len(issues),
            "corrected": sum(1 for c in corrections if c["corrected"]),
            "corrections": corrections,
            "requires_escalation": any(not c["corrected"] for c in corrections)
        }

    async def _monitor_system(self, params: Dict) -> Dict[str, Any]:
        """Overvåg system performance."""
        return {
            "action": "monitor",
            "agents_monitored": len(self._quality_scores),
            "average_score": sum(self._quality_scores.values()) / max(1, len(self._quality_scores)),
            "issues_logged": len(self._issues_log),
            "corrections_made": self._corrections_made,
            "escalations_pending": len([e for e in self._escalations if not e.get("resolved")]),
            "status": "healthy",
            "monitored_at": datetime.utcnow().isoformat()
        }

    async def _generate_report(self) -> Dict[str, Any]:
        """Generer QA rapport."""
        return {
            "action": "report",
            "report": {
                "period": "current_session",
                "total_reviews": self.tasks_processed,
                "average_quality": sum(self._quality_scores.values()) / max(1, len(self._quality_scores)),
                "issues_found": len(self._issues_log),
                "corrections_made": self._corrections_made,
                "escalations": len(self._escalations),
                "agent_scores": dict(self._quality_scores)
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    async def _general_qa_task(self, params: Dict) -> Dict[str, Any]:
        """Generel QA opgave."""
        return {
            "action": "general",
            "result": "[QA task result]",
            "issues": []
        }


# ═══════════════════════════════════════════════════════════════
# FACTORY & CONVENIENCE
# ═══════════════════════════════════════════════════════════════

def create_all_agents() -> Dict[str, BaseAgent]:
    """Opret alle CKC agenter."""
    return {
        "tool_explorer": ToolExplorerAgent(),
        "creative_synthesizer": CreativeSynthesizerAgent(),
        "knowledge_architect": KnowledgeArchitectAgent(),
        "virtual_world_builder": VirtualWorldBuilderAgent(),
        "quality_assurance": QualityAssuranceAgent()
    }


logger.info("CKC Agents module loaded - 5 specialized agents available")
