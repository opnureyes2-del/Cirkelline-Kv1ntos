"""
CIRKELLINE MASTERMIND - DEL Y: AutonomyController
==================================================

Styring af autonomi-niveauer (0-4) for MASTERMIND systemet.
Håndterer grader af selvstændighed, godkendelsesflows og sikkerhedsbarrierer.

Autonomi Niveauer:
- Niveau 0: Fuld manuel kontrol - alt kræver godkendelse
- Niveau 1: Foreslår - systemet foreslår, menneske godkender
- Niveau 2: Notificerer - handler og notificerer bagefter
- Niveau 3: Autonomt med log - handler selvstændigt, logger alt
- Niveau 4: Fuld autonomi - handler uden begrænsninger

Forfatter: Cirkelline Team
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class AutonomyLevel(IntEnum):
    """
    Autonomi-niveauer for systemet.

    Bruger IntEnum for nem sammenligning (FULL > SUPERVISED osv.)
    """

    MANUAL = 0           # Fuld manuel kontrol
    SUGGESTED = 1        # Foreslår, venter på godkendelse
    NOTIFIED = 2         # Handler, notificerer bagefter
    SUPERVISED = 3       # Autonomt med logging
    FULL = 4             # Fuld autonomi


class ActionCategory(Enum):
    """Kategorier af handlinger med forskellige risiko-niveauer."""

    INFORMATIONAL = "informational"    # Læsning, forespørgsler
    ANALYTICAL = "analytical"          # Analyse, beregninger
    COMMUNICATION = "communication"    # Beskeder, notifikationer
    OPERATIONAL = "operational"        # Daglige operationer
    ADMINISTRATIVE = "administrative"  # Admin-opgaver
    FINANCIAL = "financial"           # Økonomi-relateret
    SECURITY = "security"             # Sikkerheds-handlinger
    CRITICAL = "critical"             # Kritiske system-handlinger


class ApprovalStatus(Enum):
    """Status for en godkendelsesanmodning."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class EscalationLevel(Enum):
    """Eskalerings-niveauer for handlinger der kræver godkendelse."""

    NONE = "none"              # Ingen eskalering
    INFORM = "inform"          # Informer supervisor
    REVIEW = "review"          # Kræver review
    APPROVAL = "approval"      # Kræver godkendelse
    MULTI_APPROVAL = "multi_approval"  # Kræver flere godkendelser
    EXECUTIVE = "executive"    # Kræver højeste niveau godkendelse


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ActionPolicy:
    """Politik for en specifik handlingskategori."""

    category: ActionCategory
    min_autonomy_level: AutonomyLevel
    default_escalation: EscalationLevel
    requires_logging: bool = True
    requires_notification: bool = False
    max_frequency: Optional[int] = None  # Max antal per time
    cooldown_seconds: int = 0
    allowed_agents: Optional[Set[str]] = None
    blocked_agents: Optional[Set[str]] = None


@dataclass
class ApprovalRequest:
    """En anmodning om godkendelse."""

    request_id: str
    action_category: ActionCategory
    action_name: str
    description: str
    requested_by: str
    requested_at: datetime
    current_level: AutonomyLevel
    required_level: AutonomyLevel
    escalation: EscalationLevel

    # Kontekst
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Status
    status: ApprovalStatus = ApprovalStatus.PENDING
    expires_at: Optional[datetime] = None
    auto_approve_at: Optional[datetime] = None

    # Resultat
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


@dataclass
class AutonomyOverride:
    """Midlertidig override af autonomi-niveau."""

    override_id: str
    scope: str  # 'global', 'category', 'agent', 'action'
    target: Optional[str] = None  # Specifikt mål (category/agent/action navn)
    override_level: Optional[AutonomyLevel] = None
    escalation_override: Optional[EscalationLevel] = None

    # Tidsramme
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    created_by: str = "system"
    reason: str = ""

    # Status
    active: bool = True


@dataclass
class ActionRecord:
    """Log af en udført handling."""

    record_id: str
    action_name: str
    category: ActionCategory
    autonomy_level: AutonomyLevel
    executed_at: datetime
    executed_by: str

    # Godkendelse
    required_approval: bool = False
    approval_request_id: Optional[str] = None
    auto_approved: bool = False

    # Resultat
    success: bool = False
    error: Optional[str] = None
    result_summary: Optional[str] = None

    # Metadata
    context: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None


@dataclass
class AutonomyStats:
    """Statistik for AutonomyController."""

    current_level: AutonomyLevel
    effective_level: AutonomyLevel  # Med overrides

    total_actions: int = 0
    actions_by_category: Dict[str, int] = field(default_factory=dict)
    actions_by_level: Dict[int, int] = field(default_factory=dict)

    pending_approvals: int = 0
    approved_today: int = 0
    rejected_today: int = 0
    auto_approved_today: int = 0

    active_overrides: int = 0
    escalations_triggered: int = 0

    last_action_at: Optional[datetime] = None
    last_escalation_at: Optional[datetime] = None


# ============================================================================
# AUTONOMY CONTROLLER KLASSE
# ============================================================================

class AutonomyController:
    """
    Styrer autonomi-niveauer for MASTERMIND systemet.

    Ansvar:
    - Definere og håndhæve autonomi-niveauer
    - Håndtere godkendelsesflows
    - Administrere midlertidige overrides
    - Logge alle handlinger
    - Eskalere når nødvendigt
    """

    def __init__(
        self,
        default_level: AutonomyLevel = AutonomyLevel.SUPERVISED,
        approval_timeout_minutes: int = 30,
        auto_approve_low_risk: bool = True,
        log_all_actions: bool = True,
    ):
        """
        Initialisér AutonomyController.

        Args:
            default_level: Standard autonomi-niveau
            approval_timeout_minutes: Timeout for godkendelser
            auto_approve_low_risk: Auto-godkend lav-risiko handlinger
            log_all_actions: Log alle handlinger
        """
        self._default_level = default_level
        self._current_level = default_level
        self._approval_timeout = timedelta(minutes=approval_timeout_minutes)
        self._auto_approve_low_risk = auto_approve_low_risk
        self._log_all = log_all_actions

        # Policies
        self._policies: Dict[ActionCategory, ActionPolicy] = {}
        self._setup_default_policies()

        # Data storage
        self._approval_requests: Dict[str, ApprovalRequest] = {}
        self._overrides: Dict[str, AutonomyOverride] = {}
        self._action_records: List[ActionRecord] = []

        # Rate limiting
        self._action_counts: Dict[ActionCategory, List[datetime]] = {
            cat: [] for cat in ActionCategory
        }

        # Callbacks
        self._approval_callbacks: List[Callable[[ApprovalRequest], None]] = []
        self._action_callbacks: List[Callable[[ActionRecord], None]] = []
        self._escalation_callbacks: List[Callable[[str, EscalationLevel], None]] = []

        logger.info(f"AutonomyController initialiseret med niveau {default_level.name}")

    def _setup_default_policies(self):
        """Konfigurér standard policies for handlingskategorier."""
        self._policies = {
            # Lav risiko - kan køre næsten autonomt
            ActionCategory.INFORMATIONAL: ActionPolicy(
                category=ActionCategory.INFORMATIONAL,
                min_autonomy_level=AutonomyLevel.MANUAL,
                default_escalation=EscalationLevel.NONE,
                requires_logging=True,
                requires_notification=False,
            ),
            ActionCategory.ANALYTICAL: ActionPolicy(
                category=ActionCategory.ANALYTICAL,
                min_autonomy_level=AutonomyLevel.SUGGESTED,
                default_escalation=EscalationLevel.NONE,
                requires_logging=True,
            ),

            # Medium risiko - notification anbefales
            ActionCategory.COMMUNICATION: ActionPolicy(
                category=ActionCategory.COMMUNICATION,
                min_autonomy_level=AutonomyLevel.NOTIFIED,
                default_escalation=EscalationLevel.INFORM,
                requires_notification=True,
                max_frequency=100,  # Max 100 per time
            ),
            ActionCategory.OPERATIONAL: ActionPolicy(
                category=ActionCategory.OPERATIONAL,
                min_autonomy_level=AutonomyLevel.NOTIFIED,
                default_escalation=EscalationLevel.REVIEW,
                requires_logging=True,
                requires_notification=True,
            ),

            # Høj risiko - kræver typisk godkendelse
            ActionCategory.ADMINISTRATIVE: ActionPolicy(
                category=ActionCategory.ADMINISTRATIVE,
                min_autonomy_level=AutonomyLevel.SUPERVISED,
                default_escalation=EscalationLevel.APPROVAL,
                requires_logging=True,
                requires_notification=True,
                max_frequency=50,
                cooldown_seconds=60,
            ),
            ActionCategory.FINANCIAL: ActionPolicy(
                category=ActionCategory.FINANCIAL,
                min_autonomy_level=AutonomyLevel.FULL,
                default_escalation=EscalationLevel.APPROVAL,
                requires_logging=True,
                requires_notification=True,
                max_frequency=20,
                cooldown_seconds=300,
            ),

            # Kritisk risiko - altid eskalering
            ActionCategory.SECURITY: ActionPolicy(
                category=ActionCategory.SECURITY,
                min_autonomy_level=AutonomyLevel.FULL,
                default_escalation=EscalationLevel.MULTI_APPROVAL,
                requires_logging=True,
                requires_notification=True,
                max_frequency=10,
                cooldown_seconds=600,
            ),
            ActionCategory.CRITICAL: ActionPolicy(
                category=ActionCategory.CRITICAL,
                min_autonomy_level=AutonomyLevel.FULL,
                default_escalation=EscalationLevel.EXECUTIVE,
                requires_logging=True,
                requires_notification=True,
                max_frequency=5,
                cooldown_seconds=3600,
            ),
        }

    # ========================================================================
    # NIVEAU STYRING
    # ========================================================================

    @property
    def current_level(self) -> AutonomyLevel:
        """Hent nuværende autonomi-niveau."""
        return self._current_level

    @property
    def effective_level(self) -> AutonomyLevel:
        """Hent effektivt niveau med globale overrides."""
        for override in self._overrides.values():
            if override.active and override.scope == "global":
                if override.expires_at and datetime.now() > override.expires_at:
                    override.active = False
                    continue
                if override.override_level is not None:
                    return override.override_level
        return self._current_level

    async def set_level(
        self,
        level: AutonomyLevel,
        reason: str = "",
        requested_by: str = "system",
    ) -> bool:
        """
        Sæt nyt autonomi-niveau.

        Args:
            level: Nyt niveau
            reason: Årsag til ændring
            requested_by: Hvem der anmoder

        Returns:
            True hvis niveau blev ændret
        """
        old_level = self._current_level

        # Log niveau-ændring
        logger.info(
            f"Autonomi-niveau ændret: {old_level.name} -> {level.name} "
            f"af {requested_by}: {reason}"
        )

        self._current_level = level

        # Notificér om ændring
        if level < old_level:
            # Nedgradering - potentielt vigtig
            await self._trigger_escalation(
                f"Autonomi nedgraderet fra {old_level.name} til {level.name}",
                EscalationLevel.INFORM,
            )

        return True

    async def increase_level(
        self,
        reason: str = "",
        requested_by: str = "system",
    ) -> bool:
        """Øg autonomi-niveau med ét trin."""
        if self._current_level < AutonomyLevel.FULL:
            new_level = AutonomyLevel(self._current_level + 1)
            return await self.set_level(new_level, reason, requested_by)
        return False

    async def decrease_level(
        self,
        reason: str = "",
        requested_by: str = "system",
    ) -> bool:
        """Sænk autonomi-niveau med ét trin."""
        if self._current_level > AutonomyLevel.MANUAL:
            new_level = AutonomyLevel(self._current_level - 1)
            return await self.set_level(new_level, reason, requested_by)
        return False

    async def emergency_lockdown(
        self,
        reason: str,
        requested_by: str = "system",
        duration_minutes: Optional[int] = None,
    ) -> str:
        """
        Nødbremse - sæt til MANUAL niveau.

        Args:
            reason: Årsag til lockdown
            requested_by: Hvem der anmoder
            duration_minutes: Varighed (None = permanent)

        Returns:
            Override ID
        """
        logger.warning(f"EMERGENCY LOCKDOWN aktiveret af {requested_by}: {reason}")

        override = AutonomyOverride(
            override_id=f"lockdown_{uuid4().hex[:8]}",
            scope="global",
            override_level=AutonomyLevel.MANUAL,
            created_by=requested_by,
            reason=reason,
        )

        if duration_minutes:
            override.expires_at = datetime.now() + timedelta(minutes=duration_minutes)

        self._overrides[override.override_id] = override

        await self._trigger_escalation(
            f"EMERGENCY LOCKDOWN: {reason}",
            EscalationLevel.EXECUTIVE,
        )

        return override.override_id

    async def lift_lockdown(
        self,
        override_id: str,
        requested_by: str = "system",
    ) -> bool:
        """Ophæv en lockdown."""
        override = self._overrides.get(override_id)
        if override and override.active:
            override.active = False
            logger.info(f"Lockdown {override_id} ophævet af {requested_by}")
            return True
        return False

    # ========================================================================
    # HANDLING VALIDERING
    # ========================================================================

    async def can_execute(
        self,
        action_name: str,
        category: ActionCategory,
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[str], Optional[EscalationLevel]]:
        """
        Check om en handling kan udføres.

        Args:
            action_name: Navn på handling
            category: Handlingskategori
            agent_id: ID på agent der vil udføre
            context: Yderligere kontekst

        Returns:
            Tuple af (kan_udføres, årsag, eskalerings_niveau)
        """
        policy = self._policies.get(category)
        if not policy:
            return False, "Ingen policy for kategori", EscalationLevel.APPROVAL

        effective = self._get_effective_level(category, agent_id, action_name)

        # Check niveau
        if effective < policy.min_autonomy_level:
            return (
                False,
                f"Kræver niveau {policy.min_autonomy_level.name}, har {effective.name}",
                policy.default_escalation,
            )

        # Check agent-restriktioner
        if agent_id:
            if policy.blocked_agents and agent_id in policy.blocked_agents:
                return False, f"Agent {agent_id} er blokeret", EscalationLevel.APPROVAL
            if policy.allowed_agents and agent_id not in policy.allowed_agents:
                return False, f"Agent {agent_id} er ikke tilladt", EscalationLevel.APPROVAL

        # Check rate limiting
        if policy.max_frequency:
            if not self._check_rate_limit(category, policy.max_frequency):
                return (
                    False,
                    f"Rate limit overskredet for {category.value}",
                    EscalationLevel.REVIEW,
                )

        # Check cooldown
        if policy.cooldown_seconds > 0:
            if not self._check_cooldown(category, policy.cooldown_seconds):
                return (
                    False,
                    f"Cooldown aktiv for {category.value}",
                    EscalationLevel.NONE,
                )

        # Check overrides
        category_override = self._get_category_override(category)
        if category_override and category_override.escalation_override:
            return True, None, category_override.escalation_override

        return True, None, policy.default_escalation

    def _get_effective_level(
        self,
        category: ActionCategory,
        agent_id: Optional[str],
        action_name: str,
    ) -> AutonomyLevel:
        """Beregn effektivt autonomi-niveau for specifik handling."""
        # Start med global effektiv
        level = self.effective_level

        # Check kategori-override
        cat_override = self._get_category_override(category)
        if cat_override and cat_override.override_level is not None:
            level = min(level, cat_override.override_level)

        # Check agent-override
        if agent_id:
            agent_override = self._get_agent_override(agent_id)
            if agent_override and agent_override.override_level is not None:
                level = min(level, agent_override.override_level)

        # Check action-override
        action_override = self._get_action_override(action_name)
        if action_override and action_override.override_level is not None:
            level = min(level, action_override.override_level)

        return level

    def _get_category_override(self, category: ActionCategory) -> Optional[AutonomyOverride]:
        """Hent aktiv override for kategori."""
        for override in self._overrides.values():
            if (
                override.active
                and override.scope == "category"
                and override.target == category.value
            ):
                if override.expires_at and datetime.now() > override.expires_at:
                    override.active = False
                    continue
                return override
        return None

    def _get_agent_override(self, agent_id: str) -> Optional[AutonomyOverride]:
        """Hent aktiv override for agent."""
        for override in self._overrides.values():
            if (
                override.active
                and override.scope == "agent"
                and override.target == agent_id
            ):
                if override.expires_at and datetime.now() > override.expires_at:
                    override.active = False
                    continue
                return override
        return None

    def _get_action_override(self, action_name: str) -> Optional[AutonomyOverride]:
        """Hent aktiv override for handling."""
        for override in self._overrides.values():
            if (
                override.active
                and override.scope == "action"
                and override.target == action_name
            ):
                if override.expires_at and datetime.now() > override.expires_at:
                    override.active = False
                    continue
                return override
        return None

    def _check_rate_limit(
        self,
        category: ActionCategory,
        max_frequency: int,
    ) -> bool:
        """Check om rate limit er overholdt."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Fjern gamle entries
        self._action_counts[category] = [
            ts for ts in self._action_counts[category]
            if ts > hour_ago
        ]

        return len(self._action_counts[category]) < max_frequency

    def _check_cooldown(
        self,
        category: ActionCategory,
        cooldown_seconds: int,
    ) -> bool:
        """Check om cooldown er overstået."""
        if not self._action_counts[category]:
            return True

        last_action = max(self._action_counts[category])
        cooldown_end = last_action + timedelta(seconds=cooldown_seconds)
        return datetime.now() > cooldown_end

    # ========================================================================
    # GODKENDELSE
    # ========================================================================

    async def request_approval(
        self,
        action_name: str,
        category: ActionCategory,
        description: str,
        requested_by: str,
        context: Optional[Dict[str, Any]] = None,
        auto_approve_timeout: Optional[int] = None,
    ) -> ApprovalRequest:
        """
        Anmod om godkendelse til en handling.

        Args:
            action_name: Navn på handling
            category: Handlingskategori
            description: Beskrivelse af handling
            requested_by: Hvem der anmoder
            context: Yderligere kontekst
            auto_approve_timeout: Auto-godkend efter X sekunder

        Returns:
            ApprovalRequest objekt
        """
        policy = self._policies.get(category)
        escalation = policy.default_escalation if policy else EscalationLevel.APPROVAL

        request = ApprovalRequest(
            request_id=f"apr_{uuid4().hex[:12]}",
            action_category=category,
            action_name=action_name,
            description=description,
            requested_by=requested_by,
            requested_at=datetime.now(),
            current_level=self.effective_level,
            required_level=policy.min_autonomy_level if policy else AutonomyLevel.FULL,
            escalation=escalation,
            context=context or {},
            expires_at=datetime.now() + self._approval_timeout,
        )

        # Auto-approve for lav-risiko
        if self._auto_approve_low_risk and category in [
            ActionCategory.INFORMATIONAL,
            ActionCategory.ANALYTICAL,
        ]:
            request.status = ApprovalStatus.AUTO_APPROVED
            request.approved_at = datetime.now()
        elif auto_approve_timeout:
            request.auto_approve_at = datetime.now() + timedelta(seconds=auto_approve_timeout)

        self._approval_requests[request.request_id] = request

        # Notificér
        for callback in self._approval_callbacks:
            try:
                callback(request)
            except Exception as e:
                logger.error(f"Approval callback fejl: {e}")

        logger.info(
            f"Godkendelsesanmodning oprettet: {request.request_id} "
            f"for {action_name} ({category.value})"
        )

        return request

    async def approve(
        self,
        request_id: str,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Godkend en anmodning."""
        request = self._approval_requests.get(request_id)
        if not request or request.status != ApprovalStatus.PENDING:
            return False

        if request.expires_at and datetime.now() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            return False

        request.status = ApprovalStatus.APPROVED
        request.approved_by = approved_by
        request.approved_at = datetime.now()

        logger.info(f"Godkendelse {request_id} godkendt af {approved_by}")
        return True

    async def reject(
        self,
        request_id: str,
        rejected_by: str,
        reason: str,
    ) -> bool:
        """Afvis en anmodning."""
        request = self._approval_requests.get(request_id)
        if not request or request.status != ApprovalStatus.PENDING:
            return False

        request.status = ApprovalStatus.REJECTED
        request.approved_by = rejected_by
        request.approved_at = datetime.now()
        request.rejection_reason = reason

        logger.info(f"Godkendelse {request_id} afvist af {rejected_by}: {reason}")
        return True

    async def get_pending_approvals(
        self,
        category: Optional[ActionCategory] = None,
    ) -> List[ApprovalRequest]:
        """Hent ventende godkendelser."""
        pending = []
        for request in self._approval_requests.values():
            if request.status != ApprovalStatus.PENDING:
                continue

            # Check expiration
            if request.expires_at and datetime.now() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                continue

            # Check auto-approve
            if request.auto_approve_at and datetime.now() > request.auto_approve_at:
                request.status = ApprovalStatus.AUTO_APPROVED
                request.approved_at = datetime.now()
                continue

            if category and request.action_category != category:
                continue

            pending.append(request)

        return sorted(pending, key=lambda r: r.requested_at)

    async def is_approved(self, request_id: str) -> Tuple[bool, Optional[str]]:
        """Check om en anmodning er godkendt."""
        request = self._approval_requests.get(request_id)
        if not request:
            return False, "Anmodning ikke fundet"

        if request.status == ApprovalStatus.APPROVED:
            return True, None
        elif request.status == ApprovalStatus.AUTO_APPROVED:
            return True, "Auto-godkendt"
        elif request.status == ApprovalStatus.REJECTED:
            return False, request.rejection_reason
        elif request.status == ApprovalStatus.EXPIRED:
            return False, "Udløbet"
        else:
            return False, "Afventer godkendelse"

    # ========================================================================
    # HANDLING UDFØRELSE
    # ========================================================================

    async def execute_with_control(
        self,
        action_name: str,
        category: ActionCategory,
        executor: Callable[[], Any],
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        auto_request_approval: bool = True,
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Udfør en handling med autonomi-kontrol.

        Args:
            action_name: Navn på handling
            category: Kategori
            executor: Funktion der udfører handlingen
            agent_id: Agent ID
            context: Kontekst
            description: Beskrivelse til godkendelse
            auto_request_approval: Auto-anmod om godkendelse hvis nødvendigt

        Returns:
            Tuple af (success, result, error_message)
        """
        start_time = datetime.now()

        # Check om handling kan udføres
        can_exec, reason, escalation = await self.can_execute(
            action_name, category, agent_id, context
        )

        record = ActionRecord(
            record_id=f"act_{uuid4().hex[:12]}",
            action_name=action_name,
            category=category,
            autonomy_level=self.effective_level,
            executed_at=start_time,
            executed_by=agent_id or "system",
            context=context or {},
        )

        if not can_exec:
            if auto_request_approval and escalation != EscalationLevel.NONE:
                # Anmod om godkendelse
                request = await self.request_approval(
                    action_name=action_name,
                    category=category,
                    description=description or f"{action_name}: {reason}",
                    requested_by=agent_id or "system",
                    context=context,
                )
                record.required_approval = True
                record.approval_request_id = request.request_id

                # Vent på godkendelse for visse niveauer
                if escalation in [EscalationLevel.INFORM, EscalationLevel.REVIEW]:
                    # Fortsæt men log
                    logger.info(f"Handling {action_name} fortsætter trods {escalation.value}")
                else:
                    # Afvent godkendelse
                    record.success = False
                    record.error = f"Afventer godkendelse: {request.request_id}"
                    self._log_action(record)
                    return False, None, f"Kræver godkendelse: {request.request_id}"
            else:
                record.success = False
                record.error = reason
                self._log_action(record)
                return False, None, reason

        # Udfør handling
        try:
            if asyncio.iscoroutinefunction(executor):
                result = await executor()
            else:
                result = await asyncio.to_thread(executor)

            record.success = True
            record.result_summary = str(result)[:200] if result else None

            # Opdater rate limiting
            self._action_counts[category].append(datetime.now())

            end_time = datetime.now()
            record.duration_ms = (end_time - start_time).total_seconds() * 1000

            self._log_action(record)
            return True, result, None

        except Exception as e:
            record.success = False
            record.error = str(e)
            end_time = datetime.now()
            record.duration_ms = (end_time - start_time).total_seconds() * 1000

            self._log_action(record)
            logger.error(f"Handling {action_name} fejlede: {e}")
            return False, None, str(e)

    def _log_action(self, record: ActionRecord):
        """Log en handling."""
        self._action_records.append(record)

        # Trim gammel historik
        if len(self._action_records) > 10000:
            self._action_records = self._action_records[-5000:]

        # Notificér callbacks
        for callback in self._action_callbacks:
            try:
                callback(record)
            except Exception as e:
                logger.error(f"Action callback fejl: {e}")

    # ========================================================================
    # OVERRIDES
    # ========================================================================

    async def create_override(
        self,
        scope: str,
        target: Optional[str] = None,
        override_level: Optional[AutonomyLevel] = None,
        escalation_override: Optional[EscalationLevel] = None,
        duration_minutes: Optional[int] = None,
        reason: str = "",
        created_by: str = "system",
    ) -> AutonomyOverride:
        """
        Opret en midlertidig override.

        Args:
            scope: 'global', 'category', 'agent', eller 'action'
            target: Specifikt mål (navn på kategori/agent/action)
            override_level: Nyt autonomi-niveau
            escalation_override: Nyt eskalerings-niveau
            duration_minutes: Varighed
            reason: Årsag
            created_by: Oprettet af

        Returns:
            AutonomyOverride objekt
        """
        override = AutonomyOverride(
            override_id=f"ovr_{uuid4().hex[:8]}",
            scope=scope,
            target=target,
            override_level=override_level,
            escalation_override=escalation_override,
            created_by=created_by,
            reason=reason,
        )

        if duration_minutes:
            override.expires_at = datetime.now() + timedelta(minutes=duration_minutes)

        self._overrides[override.override_id] = override

        logger.info(
            f"Override oprettet: {override.override_id} "
            f"({scope}/{target}) af {created_by}"
        )

        return override

    async def remove_override(self, override_id: str) -> bool:
        """Fjern en override."""
        override = self._overrides.get(override_id)
        if override:
            override.active = False
            logger.info(f"Override {override_id} deaktiveret")
            return True
        return False

    async def get_active_overrides(self) -> List[AutonomyOverride]:
        """Hent alle aktive overrides."""
        active = []
        for override in self._overrides.values():
            if not override.active:
                continue
            if override.expires_at and datetime.now() > override.expires_at:
                override.active = False
                continue
            active.append(override)
        return active

    # ========================================================================
    # ESKALERING
    # ========================================================================

    async def _trigger_escalation(
        self,
        message: str,
        level: EscalationLevel,
    ):
        """Trigger en eskalering."""
        logger.warning(f"Eskalering [{level.value}]: {message}")

        for callback in self._escalation_callbacks:
            try:
                callback(message, level)
            except Exception as e:
                logger.error(f"Escalation callback fejl: {e}")

    # ========================================================================
    # CALLBACKS
    # ========================================================================

    def on_approval_request(self, callback: Callable[[ApprovalRequest], None]):
        """Registrér callback for nye godkendelsesanmodninger."""
        self._approval_callbacks.append(callback)

    def on_action(self, callback: Callable[[ActionRecord], None]):
        """Registrér callback for udførte handlinger."""
        self._action_callbacks.append(callback)

    def on_escalation(self, callback: Callable[[str, EscalationLevel], None]):
        """Registrér callback for eskaleringer."""
        self._escalation_callbacks.append(callback)

    # ========================================================================
    # STATISTIK
    # ========================================================================

    async def get_stats(self) -> AutonomyStats:
        """Hent statistik."""
        today = datetime.now().date()

        # Tæl actions
        actions_by_cat = {}
        actions_by_level = {}
        for record in self._action_records:
            cat = record.category.value
            actions_by_cat[cat] = actions_by_cat.get(cat, 0) + 1

            level = record.autonomy_level.value
            actions_by_level[level] = actions_by_level.get(level, 0) + 1

        # Tæl approvals
        approved_today = 0
        rejected_today = 0
        auto_approved_today = 0
        pending = 0

        for request in self._approval_requests.values():
            if request.status == ApprovalStatus.PENDING:
                pending += 1
            elif request.approved_at and request.approved_at.date() == today:
                if request.status == ApprovalStatus.APPROVED:
                    approved_today += 1
                elif request.status == ApprovalStatus.AUTO_APPROVED:
                    auto_approved_today += 1
                elif request.status == ApprovalStatus.REJECTED:
                    rejected_today += 1

        active_overrides = len(await self.get_active_overrides())

        last_action = None
        if self._action_records:
            last_action = max(r.executed_at for r in self._action_records)

        return AutonomyStats(
            current_level=self._current_level,
            effective_level=self.effective_level,
            total_actions=len(self._action_records),
            actions_by_category=actions_by_cat,
            actions_by_level=actions_by_level,
            pending_approvals=pending,
            approved_today=approved_today,
            rejected_today=rejected_today,
            auto_approved_today=auto_approved_today,
            active_overrides=active_overrides,
            last_action_at=last_action,
        )

    async def get_action_history(
        self,
        category: Optional[ActionCategory] = None,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[ActionRecord]:
        """Hent handling-historik."""
        records = []
        for record in reversed(self._action_records):
            if category and record.category != category:
                continue
            if since and record.executed_at < since:
                continue
            records.append(record)
            if len(records) >= limit:
                break
        return records


# ============================================================================
# FACTORY FUNKTIONER
# ============================================================================

_autonomy_controller_instance: Optional[AutonomyController] = None


def create_autonomy_controller(**kwargs) -> AutonomyController:
    """
    Opret ny AutonomyController instans.

    Args:
        **kwargs: Parametre til AutonomyController

    Returns:
        Ny AutonomyController instans
    """
    global _autonomy_controller_instance
    _autonomy_controller_instance = AutonomyController(**kwargs)
    return _autonomy_controller_instance


def get_autonomy_controller() -> Optional[AutonomyController]:
    """Hent global AutonomyController instans."""
    return _autonomy_controller_instance


def set_autonomy_controller(instance: AutonomyController):
    """Sæt global AutonomyController instans."""
    global _autonomy_controller_instance
    _autonomy_controller_instance = instance


# ============================================================================
# CONVENIENCE FUNKTIONER
# ============================================================================

async def check_autonomy(
    action_name: str,
    category: ActionCategory,
    agent_id: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Convenience: Check om handling er tilladt.

    Returns:
        Tuple af (tilladt, årsag)
    """
    controller = get_autonomy_controller()
    if not controller:
        return True, None  # Ingen controller = alt tilladt

    can_exec, reason, _ = await controller.can_execute(
        action_name, category, agent_id
    )
    return can_exec, reason


async def execute_controlled(
    action_name: str,
    category: ActionCategory,
    executor: Callable,
    agent_id: Optional[str] = None,
) -> Tuple[bool, Any, Optional[str]]:
    """
    Convenience: Udfør handling med kontrol.

    Returns:
        Tuple af (success, result, error)
    """
    controller = get_autonomy_controller()
    if not controller:
        # Ingen controller - kør direkte
        try:
            if asyncio.iscoroutinefunction(executor):
                result = await executor()
            else:
                result = executor()
            return True, result, None
        except Exception as e:
            return False, None, str(e)

    return await controller.execute_with_control(
        action_name, category, executor, agent_id
    )


def requires_approval(
    category: ActionCategory = ActionCategory.OPERATIONAL,
    description: Optional[str] = None,
):
    """
    Decorator til at kræve godkendelse for en funktion.

    Usage:
        @requires_approval(ActionCategory.ADMINISTRATIVE)
        async def delete_user(user_id: str):
            ...
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            controller = get_autonomy_controller()
            if controller:
                success, result, error = await controller.execute_with_control(
                    action_name=func.__name__,
                    category=category,
                    executor=lambda: func(*args, **kwargs),
                    description=description,
                )
                if not success:
                    raise PermissionError(error or "Handling ikke tilladt")
                return result
            else:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# MASTERMIND INTEGRATION
# ============================================================================

async def create_mastermind_autonomy(
    default_level: AutonomyLevel = AutonomyLevel.SUPERVISED,
) -> AutonomyController:
    """
    Opret og konfigurér AutonomyController til MASTERMIND.

    Args:
        default_level: Standard autonomi-niveau

    Returns:
        Konfigureret AutonomyController
    """
    controller = create_autonomy_controller(
        default_level=default_level,
        approval_timeout_minutes=60,
        auto_approve_low_risk=True,
        log_all_actions=True,
    )

    # Registrér standard callbacks
    def log_escalation(msg: str, level: EscalationLevel):
        logger.warning(f"MASTERMIND Eskalering [{level.value}]: {msg}")

    controller.on_escalation(log_escalation)

    return controller
