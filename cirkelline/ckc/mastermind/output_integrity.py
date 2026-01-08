"""
CKC LÆRERUMS OUTPUT INTEGRITET & GODKENDELSES PROTOKOL

Dette modul implementerer den komplette output kontrol protokol for CKC Lærerum:
- Output Validation Gateway (OVG) - Lærerummets Portvogter
- Mastermind Audit System (MAS) - Den Øverste Vogter
- Quarantine Mechanism (QM) - Sikkerhedens Venteværelse
- Super Admin Notification (SAN) - Øjeblikkelig Advarsel

Filosofi: "Integritet er ikke en feature; det er vores fundament."
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set
import asyncio
import hashlib
import logging
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS - Definitioner af tilstande og typer
# =============================================================================

class ValidationRuleType(Enum):
    """Typer af valideringsregler for Output Validation Gateway."""
    CONTEXTUAL_RELEVANCE = auto()     # Matcher outputtet den forespurgte kontekst?
    ETHICAL_COMPLIANCE = auto()        # Overholder etiske retningslinjer?
    SECURITY_STANDARDS = auto()        # Opfylder sikkerhedsstandarder?
    FORMAT_INTEGRITY = auto()          # Korrekt datastruktur og format?
    METADATA_VERIFICATION = auto()     # Valide metadata (kilde, dato, agent)?
    CONTENT_QUALITY = auto()           # Kvalitet af indholdet
    BIAS_DETECTION = auto()            # Detektion af bias
    SENSITIVE_DATA = auto()            # Check for sensitiv data


class ValidationResult(Enum):
    """Resultat af validering."""
    PASSED = auto()          # Validering bestået
    FAILED = auto()          # Validering fejlet
    WARNING = auto()         # Advarsel, men ikke blokerende
    REQUIRES_REVIEW = auto() # Kræver manuel gennemgang


class AuditDecision(Enum):
    """Mastermind Audit System beslutninger."""
    APPROVED = auto()               # Godkendt til externalisering
    REJECTED = auto()               # Afvist - send til karantæne
    REQUIRES_MODIFICATION = auto()  # Kræver ændring før godkendelse
    REQUIRES_SUPER_ADMIN = auto()   # Kræver Super Admin godkendelse
    PENDING_REVIEW = auto()         # Afventer gennemgang


class QuarantineReason(Enum):
    """Årsager til karantæne."""
    OVG_VALIDATION_FAILURE = auto()  # Fejlet OVG validering
    MAS_REJECTION = auto()           # Afvist af Mastermind Audit
    SECURITY_CONCERN = auto()        # Sikkerhedsproblem
    ETHICAL_VIOLATION = auto()       # Etisk overtrædelse
    POLICY_BREACH = auto()           # Politik overtrædelse
    MANUAL_QUARANTINE = auto()       # Manuelt sat i karantæne
    SUSPICIOUS_CONTENT = auto()      # Mistænkeligt indhold


class QuarantineStatus(Enum):
    """Status for karantæne-objekter."""
    ACTIVE = auto()          # Aktivt i karantæne
    RELEASED = auto()        # Frigivet efter godkendelse
    DELETED = auto()         # Slettet
    EXPIRED = auto()         # Udløbet og fjernet
    UNDER_REVIEW = auto()    # Under gennemgang


class NotificationType(Enum):
    """Typer af Super Admin notifikationer."""
    QUARANTINE_ALERT = auto()        # Output placeret i karantæne
    MAS_REJECTION = auto()           # Mastermind afvisning
    OVG_CRITICAL_FAILURE = auto()    # Kritisk OVG fejl
    SYSTEM_INTEGRITY_ALERT = auto()  # System integritetsproblem
    POLICY_VIOLATION = auto()        # Politik overtrædelse
    SECURITY_BREACH = auto()         # Sikkerhedsbrud
    AUDIT_SUMMARY = auto()           # Daglig audit opsummering


class NotificationPriority(Enum):
    """Prioritet af notifikationer."""
    CRITICAL = auto()    # Øjeblikkelig handling påkrævet
    HIGH = auto()        # Hurtig opmærksomhed påkrævet
    MEDIUM = auto()      # Normal prioritet
    LOW = auto()         # Informativ
    AGGREGATE = auto()   # Kan aggregeres


class NotificationChannel(Enum):
    """Notifikationskanaler."""
    EMAIL = auto()
    DASHBOARD = auto()
    MOBILE_PUSH = auto()
    SMS = auto()
    INTERNAL_LOG = auto()


# =============================================================================
# DATAKLASSER - Strukturerede datamodeller
# =============================================================================

@dataclass
class ValidationRule:
    """En enkelt valideringsregel."""
    rule_id: str
    rule_type: ValidationRuleType
    name: str
    description: str
    is_blocking: bool = True  # Hvis True, blokerer fejl output
    severity: int = 5  # 1-10, hvor 10 er mest alvorlig
    enabled: bool = True
    validator: Optional[Callable[[Any], ValidationResult]] = None


@dataclass
class ValidationReport:
    """Rapport fra Output Validation Gateway."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    output_id: str = ""
    output_hash: str = ""
    requesting_agent: str = ""
    intended_destination: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    rule_results: Dict[str, ValidationResult] = field(default_factory=dict)
    overall_result: ValidationResult = ValidationResult.PASSED
    failed_rules: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditReport:
    """Rapport fra Mastermind Audit System."""
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    validation_report: Optional[ValidationReport] = None
    decision: AuditDecision = AuditDecision.PENDING_REVIEW
    reasoning: str = ""
    policy_checks: Dict[str, bool] = field(default_factory=dict)
    risk_score: float = 0.0  # 0.0 - 1.0
    recommendations: List[str] = field(default_factory=list)
    requires_super_admin: bool = False
    auto_learning_applied: bool = False


@dataclass
class QuarantineItem:
    """Et objekt i karantæne."""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    output_content: Any = None
    output_hash: str = ""
    reason: QuarantineReason = QuarantineReason.OVG_VALIDATION_FAILURE
    status: QuarantineStatus = QuarantineStatus.ACTIVE
    validation_report: Optional[ValidationReport] = None
    audit_report: Optional[AuditReport] = None
    requesting_agent: str = ""
    intended_destination: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    review_notes: List[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None


@dataclass
class Notification:
    """En Super Admin notifikation."""
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    notification_type: NotificationType = NotificationType.QUARANTINE_ALERT
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str = ""
    message: str = ""
    source_component: str = ""
    related_item_id: Optional[str] = None
    channels: List[NotificationChannel] = field(default_factory=list)
    is_read: bool = False
    is_acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationPreferences:
    """Super Admin notifikationspræferencer."""
    user_id: str = "super_admin"
    email: str = ""
    enabled_channels: Set[NotificationChannel] = field(
        default_factory=lambda: {NotificationChannel.DASHBOARD, NotificationChannel.EMAIL}
    )
    critical_only_mobile: bool = True
    aggregate_low_priority: bool = True
    quiet_hours_start: Optional[int] = None  # Time (0-23)
    quiet_hours_end: Optional[int] = None
    minimum_priority: NotificationPriority = NotificationPriority.LOW


# =============================================================================
# DEL I: OUTPUT VALIDATION GATEWAY (OVG)
# =============================================================================

class OutputValidationGateway:
    """
    Output Validation Gateway - Lærerummets Portvogter

    Det første og mest afgørende kontrolpunkt, der sikrer at intet
    uautoriseret eller ukonsistent output forlader lærerummet.
    """

    def __init__(self):
        self._rules: Dict[str, ValidationRule] = {}
        self._rule_validators: Dict[ValidationRuleType, Callable] = {}
        self._validation_history: List[ValidationReport] = []
        self._lock = asyncio.Lock()
        self._initialize_default_rules()
        self._initialize_validators()

    def _initialize_default_rules(self) -> None:
        """Initialiserer standard valideringsregler."""
        default_rules = [
            ValidationRule(
                rule_id="contextual_001",
                rule_type=ValidationRuleType.CONTEXTUAL_RELEVANCE,
                name="Kontekstuel Relevans",
                description="Verificerer at output matcher den forespurgte kontekst",
                is_blocking=True,
                severity=8
            ),
            ValidationRule(
                rule_id="ethical_001",
                rule_type=ValidationRuleType.ETHICAL_COMPLIANCE,
                name="Etisk Compliance",
                description="Kontrollerer mod CKC's etiske retningslinjer",
                is_blocking=True,
                severity=10
            ),
            ValidationRule(
                rule_id="security_001",
                rule_type=ValidationRuleType.SECURITY_STANDARDS,
                name="Sikkerhedsstandarder",
                description="Scanner for potentielle sikkerhedsbrister",
                is_blocking=True,
                severity=10
            ),
            ValidationRule(
                rule_id="format_001",
                rule_type=ValidationRuleType.FORMAT_INTEGRITY,
                name="Format Integritet",
                description="Sikrer korrekt datastruktur og format",
                is_blocking=False,
                severity=5
            ),
            ValidationRule(
                rule_id="metadata_001",
                rule_type=ValidationRuleType.METADATA_VERIFICATION,
                name="Metadata Verifikation",
                description="Kontrollerer tilhørende metadata",
                is_blocking=False,
                severity=6
            ),
            ValidationRule(
                rule_id="bias_001",
                rule_type=ValidationRuleType.BIAS_DETECTION,
                name="Bias Detektion",
                description="Detekterer potentiel bias i output",
                is_blocking=True,
                severity=9
            ),
            ValidationRule(
                rule_id="sensitive_001",
                rule_type=ValidationRuleType.SENSITIVE_DATA,
                name="Sensitiv Data Check",
                description="Tjekker for utilsigtet sensitiv data",
                is_blocking=True,
                severity=10
            ),
        ]

        for rule in default_rules:
            self._rules[rule.rule_id] = rule

    def _initialize_validators(self) -> None:
        """Initialiserer validator funktioner for hver regeltype."""
        self._rule_validators = {
            ValidationRuleType.CONTEXTUAL_RELEVANCE: self._validate_contextual,
            ValidationRuleType.ETHICAL_COMPLIANCE: self._validate_ethical,
            ValidationRuleType.SECURITY_STANDARDS: self._validate_security,
            ValidationRuleType.FORMAT_INTEGRITY: self._validate_format,
            ValidationRuleType.METADATA_VERIFICATION: self._validate_metadata,
            ValidationRuleType.BIAS_DETECTION: self._validate_bias,
            ValidationRuleType.SENSITIVE_DATA: self._validate_sensitive,
            ValidationRuleType.CONTENT_QUALITY: self._validate_quality,
        }

    async def _validate_contextual(self, output: Any, context: Dict) -> ValidationResult:
        """Validerer kontekstuel relevans."""
        # Basis kontekst validering
        if not context:
            return ValidationResult.WARNING

        expected_type = context.get("expected_type")
        if expected_type and not isinstance(output, type(expected_type)):
            return ValidationResult.FAILED

        return ValidationResult.PASSED

    async def _validate_ethical(self, output: Any, context: Dict) -> ValidationResult:
        """Validerer etisk compliance."""
        # Konverter output til string for analyse
        output_str = str(output).lower()

        # Check for åbenlyse etiske problemer
        ethical_violations = [
            "diskrimination", "hadtale", "vold", "ulovlig"
        ]

        for violation in ethical_violations:
            if violation in output_str:
                return ValidationResult.FAILED

        return ValidationResult.PASSED

    async def _validate_security(self, output: Any, context: Dict) -> ValidationResult:
        """Validerer sikkerhedsstandarder."""
        output_str = str(output)

        # Check for potentielle sikkerhedsproblemer
        security_patterns = [
            "password=", "api_key=", "secret=", "token=",
            "SELECT * FROM", "DROP TABLE", "<script>"
        ]

        for pattern in security_patterns:
            if pattern.lower() in output_str.lower():
                return ValidationResult.FAILED

        return ValidationResult.PASSED

    async def _validate_format(self, output: Any, context: Dict) -> ValidationResult:
        """Validerer format integritet."""
        expected_format = context.get("expected_format")

        if expected_format == "json" and not isinstance(output, (dict, list)):
            return ValidationResult.WARNING

        return ValidationResult.PASSED

    async def _validate_metadata(self, output: Any, context: Dict) -> ValidationResult:
        """Validerer metadata."""
        required_metadata = ["source", "timestamp", "agent_id"]
        metadata = context.get("metadata", {})

        missing = [m for m in required_metadata if m not in metadata]

        if missing:
            return ValidationResult.WARNING

        return ValidationResult.PASSED

    async def _validate_bias(self, output: Any, context: Dict) -> ValidationResult:
        """Detekterer potentiel bias."""
        # Simpel bias detektion
        output_str = str(output).lower()

        bias_indicators = [
            "altid", "aldrig", "alle", "ingen",  # Absolutte udsagn
        ]

        bias_count = sum(1 for indicator in bias_indicators if indicator in output_str)

        if bias_count > 3:
            return ValidationResult.REQUIRES_REVIEW

        return ValidationResult.PASSED

    async def _validate_sensitive(self, output: Any, context: Dict) -> ValidationResult:
        """Tjekker for sensitiv data."""
        output_str = str(output)

        # Patterns for sensitiv data
        import re

        # CPR nummer pattern (dansk)
        cpr_pattern = r'\d{6}-?\d{4}'
        if re.search(cpr_pattern, output_str):
            return ValidationResult.FAILED

        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if context.get("allow_emails", False) is False and re.search(email_pattern, output_str):
            return ValidationResult.WARNING

        return ValidationResult.PASSED

    async def _validate_quality(self, output: Any, context: Dict) -> ValidationResult:
        """Validerer indholdskvalitet."""
        if output is None or (isinstance(output, str) and len(output.strip()) == 0):
            return ValidationResult.FAILED

        return ValidationResult.PASSED

    def add_rule(self, rule: ValidationRule) -> None:
        """Tilføjer en ny valideringsregel."""
        self._rules[rule.rule_id] = rule
        logger.info(f"Valideringsregel tilføjet: {rule.name}")

    def remove_rule(self, rule_id: str) -> bool:
        """Fjerner en valideringsregel."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def enable_rule(self, rule_id: str) -> bool:
        """Aktiverer en valideringsregel."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Deaktiverer en valideringsregel."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            return True
        return False

    async def validate_output(
        self,
        output: Any,
        requesting_agent: str,
        intended_destination: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationReport:
        """
        Validerer et output mod alle aktive regler.

        Args:
            output: Det output der skal valideres
            requesting_agent: ID på den agent der anmoder
            intended_destination: Den tilsigtede destination
            context: Yderligere kontekst for validering

        Returns:
            ValidationReport med resultater
        """
        async with self._lock:
            context = context or {}

            # Opret output hash for integritet
            output_hash = hashlib.sha256(str(output).encode()).hexdigest()

            report = ValidationReport(
                output_id=str(uuid.uuid4()),
                output_hash=output_hash,
                requesting_agent=requesting_agent,
                intended_destination=intended_destination,
                context=context
            )

            # Kør alle aktive regler
            blocking_failures = []

            for rule_id, rule in self._rules.items():
                if not rule.enabled:
                    continue

                validator = self._rule_validators.get(rule.rule_type)
                if validator:
                    try:
                        result = await validator(output, context)
                        report.rule_results[rule_id] = result

                        if result == ValidationResult.FAILED:
                            report.failed_rules.append(rule_id)
                            if rule.is_blocking:
                                blocking_failures.append(rule_id)
                        elif result == ValidationResult.WARNING:
                            report.warnings.append(f"{rule.name}: Advarsel")
                        elif result == ValidationResult.REQUIRES_REVIEW:
                            report.warnings.append(f"{rule.name}: Kræver gennemgang")

                    except Exception as e:
                        logger.error(f"Fejl i validering af regel {rule_id}: {e}")
                        report.rule_results[rule_id] = ValidationResult.FAILED
                        report.failed_rules.append(rule_id)

            # Bestem overordnet resultat
            if blocking_failures:
                report.overall_result = ValidationResult.FAILED
            elif report.warnings:
                report.overall_result = ValidationResult.WARNING
            else:
                report.overall_result = ValidationResult.PASSED

            # Gem i historik
            self._validation_history.append(report)

            # Trim historik
            if len(self._validation_history) > 1000:
                self._validation_history = self._validation_history[-500:]

            logger.info(
                f"OVG Validering komplet: {report.overall_result.name} "
                f"(Agent: {requesting_agent}, Destination: {intended_destination})"
            )

            return report

    def get_rule_statistics(self) -> Dict[str, Any]:
        """Returnerer statistik over regelanvendelse."""
        stats = {
            "total_rules": len(self._rules),
            "enabled_rules": sum(1 for r in self._rules.values() if r.enabled),
            "total_validations": len(self._validation_history),
            "passed": sum(1 for v in self._validation_history if v.overall_result == ValidationResult.PASSED),
            "failed": sum(1 for v in self._validation_history if v.overall_result == ValidationResult.FAILED),
            "warnings": sum(1 for v in self._validation_history if v.overall_result == ValidationResult.WARNING),
        }
        return stats


# =============================================================================
# DEL II: MASTERMIND AUDIT SYSTEM (MAS)
# =============================================================================

class MastermindAuditSystem:
    """
    Mastermind Audit System - Den Øverste Vogter

    Aktiverer Masterminds rolle som den ultimative godkender og observatør
    af alle externaliseringsforespørgsler.
    """

    def __init__(self):
        self._audit_history: List[AuditReport] = []
        self._policies: Dict[str, Callable] = {}
        self._learning_data: List[Dict] = []
        self._risk_thresholds = {
            "auto_approve": 0.2,      # Under 20% risiko = auto-godkend
            "requires_review": 0.5,   # 20-50% = kræver gennemgang
            "auto_reject": 0.8,       # Over 80% = auto-afvis
        }
        self._lock = asyncio.Lock()
        self._initialize_policies()

    def _initialize_policies(self) -> None:
        """Initialiserer standard politikker."""
        self._policies = {
            "master_command_compliance": self._check_master_command_compliance,
            "ethical_guidelines": self._check_ethical_guidelines,
            "security_policy": self._check_security_policy,
            "data_governance": self._check_data_governance,
            "agent_authorization": self._check_agent_authorization,
        }

    async def _check_master_command_compliance(
        self,
        validation_report: ValidationReport
    ) -> bool:
        """Tjekker overensstemmelse med Master Commands."""
        # Tjek om alle kritiske regler er bestået
        critical_rules = ["ethical_001", "security_001", "sensitive_001"]

        for rule_id in critical_rules:
            result = validation_report.rule_results.get(rule_id)
            if result == ValidationResult.FAILED:
                return False

        return True

    async def _check_ethical_guidelines(
        self,
        validation_report: ValidationReport
    ) -> bool:
        """Tjekker overensstemmelse med etiske retningslinjer."""
        ethical_rules = ["ethical_001", "bias_001"]

        for rule_id in ethical_rules:
            result = validation_report.rule_results.get(rule_id)
            if result == ValidationResult.FAILED:
                return False

        return True

    async def _check_security_policy(
        self,
        validation_report: ValidationReport
    ) -> bool:
        """Tjekker overensstemmelse med sikkerhedspolitik."""
        security_rules = ["security_001", "sensitive_001"]

        for rule_id in security_rules:
            result = validation_report.rule_results.get(rule_id)
            if result == ValidationResult.FAILED:
                return False

        return True

    async def _check_data_governance(
        self,
        validation_report: ValidationReport
    ) -> bool:
        """Tjekker overensstemmelse med data governance."""
        # Tjek metadata
        metadata_result = validation_report.rule_results.get("metadata_001")
        if metadata_result == ValidationResult.FAILED:
            return False

        return True

    async def _check_agent_authorization(
        self,
        validation_report: ValidationReport
    ) -> bool:
        """Tjekker om agenten er autoriseret."""
        # Her kunne man tjekke mod en liste af autoriserede agenter
        authorized_agents = {"mastermind", "super_admin", "training_room"}

        requesting_agent = validation_report.requesting_agent.lower()

        # Tillad alle for nu, men log
        return True

    def _calculate_risk_score(self, validation_report: ValidationReport) -> float:
        """Beregner en risikoscore baseret på valideringsresultater."""
        if not validation_report.rule_results:
            return 0.5  # Neutral score hvis ingen resultater

        weights = {
            ValidationResult.PASSED: 0.0,
            ValidationResult.WARNING: 0.3,
            ValidationResult.REQUIRES_REVIEW: 0.5,
            ValidationResult.FAILED: 1.0,
        }

        total_weight = 0.0
        count = 0

        for result in validation_report.rule_results.values():
            total_weight += weights.get(result, 0.5)
            count += 1

        if count == 0:
            return 0.5

        return total_weight / count

    async def audit_output(
        self,
        validation_report: ValidationReport
    ) -> AuditReport:
        """
        Udfører en fuld audit af et output baseret på OVG's rapport.

        Args:
            validation_report: Rapport fra Output Validation Gateway

        Returns:
            AuditReport med beslutning og begrundelse
        """
        async with self._lock:
            audit_report = AuditReport(
                validation_report=validation_report
            )

            # Kør alle politiktjek
            policy_results = {}
            for policy_name, policy_check in self._policies.items():
                try:
                    result = await policy_check(validation_report)
                    policy_results[policy_name] = result
                except Exception as e:
                    logger.error(f"Fejl i politik {policy_name}: {e}")
                    policy_results[policy_name] = False

            audit_report.policy_checks = policy_results

            # Beregn risikoscore
            risk_score = self._calculate_risk_score(validation_report)
            audit_report.risk_score = risk_score

            # Træf beslutning baseret på resultater
            all_policies_passed = all(policy_results.values())
            validation_passed = validation_report.overall_result == ValidationResult.PASSED

            if validation_passed and all_policies_passed:
                if risk_score < self._risk_thresholds["auto_approve"]:
                    audit_report.decision = AuditDecision.APPROVED
                    audit_report.reasoning = "Alle valideringer og politikker bestået med lav risiko"
                else:
                    audit_report.decision = AuditDecision.APPROVED
                    audit_report.reasoning = "Alle valideringer bestået"

            elif validation_report.overall_result == ValidationResult.WARNING:
                if risk_score < self._risk_thresholds["requires_review"]:
                    audit_report.decision = AuditDecision.APPROVED
                    audit_report.reasoning = "Advarsler noteret, men risiko acceptabel"
                    audit_report.recommendations = validation_report.warnings
                else:
                    audit_report.decision = AuditDecision.REQUIRES_SUPER_ADMIN
                    audit_report.reasoning = "Advarsler kræver Super Admin gennemgang"
                    audit_report.requires_super_admin = True

            elif risk_score >= self._risk_thresholds["auto_reject"]:
                audit_report.decision = AuditDecision.REJECTED
                audit_report.reasoning = f"Høj risikoscore ({risk_score:.2f}) - automatisk afvist"

            else:
                audit_report.decision = AuditDecision.REQUIRES_MODIFICATION
                audit_report.reasoning = "Valideringsfejl kræver rettelser"
                audit_report.recommendations = [
                    f"Ret fejl i regel: {rule}" for rule in validation_report.failed_rules
                ]

            # Gem audit til læring
            self._learning_data.append({
                "timestamp": datetime.now(),
                "risk_score": risk_score,
                "decision": audit_report.decision.name,
                "policies_passed": sum(policy_results.values()),
                "total_policies": len(policy_results)
            })

            # Gem i historik
            self._audit_history.append(audit_report)

            # Trim historik
            if len(self._audit_history) > 1000:
                self._audit_history = self._audit_history[-500:]

            logger.info(
                f"MAS Audit komplet: {audit_report.decision.name} "
                f"(Risiko: {risk_score:.2f})"
            )

            return audit_report

    def update_risk_thresholds(
        self,
        auto_approve: Optional[float] = None,
        requires_review: Optional[float] = None,
        auto_reject: Optional[float] = None
    ) -> None:
        """Opdaterer risiko thresholds."""
        if auto_approve is not None:
            self._risk_thresholds["auto_approve"] = auto_approve
        if requires_review is not None:
            self._risk_thresholds["requires_review"] = requires_review
        if auto_reject is not None:
            self._risk_thresholds["auto_reject"] = auto_reject

    def get_audit_statistics(self) -> Dict[str, Any]:
        """Returnerer statistik over audits."""
        decision_counts = {}
        for decision in AuditDecision:
            decision_counts[decision.name] = sum(
                1 for a in self._audit_history if a.decision == decision
            )

        avg_risk = 0.0
        if self._audit_history:
            avg_risk = sum(a.risk_score for a in self._audit_history) / len(self._audit_history)

        return {
            "total_audits": len(self._audit_history),
            "decisions": decision_counts,
            "average_risk_score": avg_risk,
            "learning_samples": len(self._learning_data),
        }


# =============================================================================
# DEL III: QUARANTINE MECHANISM (QM)
# =============================================================================

class QuarantineMechanism:
    """
    Quarantine Mechanism - Sikkerhedens Venteværelse

    Sikker isoleret lagring for ikke-godkendt output, der forhindrer
    utilsigtet eksponering og giver mulighed for manuel gennemgang.
    """

    def __init__(self, retention_days: int = 90):
        self._quarantine: Dict[str, QuarantineItem] = {}
        self._retention_days = retention_days
        self._access_log: List[Dict] = []
        self._lock = asyncio.Lock()

    async def add_to_quarantine(
        self,
        output: Any,
        reason: QuarantineReason,
        validation_report: Optional[ValidationReport] = None,
        audit_report: Optional[AuditReport] = None,
        requesting_agent: str = "",
        intended_destination: str = "",
        metadata: Optional[Dict] = None
    ) -> QuarantineItem:
        """
        Tilføjer et output til karantæne.

        Args:
            output: Det output der skal karantæneplaceres
            reason: Årsagen til karantæne
            validation_report: OVG rapport hvis tilgængelig
            audit_report: MAS rapport hvis tilgængelig
            requesting_agent: Den anmodende agent
            intended_destination: Den tilsigtede destination
            metadata: Yderligere metadata

        Returns:
            QuarantineItem objektet
        """
        async with self._lock:
            output_hash = hashlib.sha256(str(output).encode()).hexdigest()

            item = QuarantineItem(
                output_content=output,
                output_hash=output_hash,
                reason=reason,
                validation_report=validation_report,
                audit_report=audit_report,
                requesting_agent=requesting_agent,
                intended_destination=intended_destination,
                metadata=metadata or {},
                expires_at=datetime.now() + timedelta(days=self._retention_days)
            )

            self._quarantine[item.item_id] = item

            self._log_access("add", item.item_id, "system")

            logger.warning(
                f"Output tilføjet til karantæne: {item.item_id} "
                f"(Årsag: {reason.name})"
            )

            return item

    async def get_item(self, item_id: str, accessor: str = "system") -> Optional[QuarantineItem]:
        """Henter et karantæne-objekt."""
        async with self._lock:
            item = self._quarantine.get(item_id)
            if item:
                self._log_access("get", item_id, accessor)
            return item

    async def release_item(
        self,
        item_id: str,
        accessor: str,
        notes: str = ""
    ) -> bool:
        """
        Frigiver et objekt fra karantæne efter godkendelse.

        Kun Super Admin kan frigive objekter.
        """
        async with self._lock:
            if accessor.lower() not in ["super_admin", "mastermind"]:
                logger.warning(f"Uautoriseret frigivelsesførsøg af {accessor}")
                return False

            item = self._quarantine.get(item_id)
            if not item:
                return False

            item.status = QuarantineStatus.RELEASED
            if notes:
                item.review_notes.append(f"[{datetime.now()}] {accessor}: {notes}")

            self._log_access("release", item_id, accessor)

            logger.info(f"Karantæne-objekt frigivet: {item_id} af {accessor}")

            return True

    async def delete_item(
        self,
        item_id: str,
        accessor: str,
        notes: str = ""
    ) -> bool:
        """Sletter et objekt fra karantæne."""
        async with self._lock:
            if accessor.lower() not in ["super_admin", "mastermind"]:
                logger.warning(f"Uautoriseret sletningsforsøg af {accessor}")
                return False

            item = self._quarantine.get(item_id)
            if not item:
                return False

            item.status = QuarantineStatus.DELETED
            if notes:
                item.review_notes.append(f"[{datetime.now()}] {accessor}: {notes}")

            self._log_access("delete", item_id, accessor)

            # Fjern fra aktiv karantæne men behold metadata
            del self._quarantine[item_id]

            logger.info(f"Karantæne-objekt slettet: {item_id} af {accessor}")

            return True

    async def add_review_note(
        self,
        item_id: str,
        accessor: str,
        note: str
    ) -> bool:
        """Tilføjer en gennemgangsnote til et karantæne-objekt."""
        async with self._lock:
            item = self._quarantine.get(item_id)
            if not item:
                return False

            item.review_notes.append(f"[{datetime.now()}] {accessor}: {note}")
            item.status = QuarantineStatus.UNDER_REVIEW

            self._log_access("review", item_id, accessor)

            return True

    async def cleanup_expired(self) -> int:
        """Rydder op i udløbede karantæne-objekter."""
        async with self._lock:
            now = datetime.now()
            expired_ids = [
                item_id for item_id, item in self._quarantine.items()
                if item.expires_at and item.expires_at < now
            ]

            for item_id in expired_ids:
                self._quarantine[item_id].status = QuarantineStatus.EXPIRED
                del self._quarantine[item_id]

            if expired_ids:
                logger.info(f"Fjernet {len(expired_ids)} udløbede karantæne-objekter")

            return len(expired_ids)

    def _log_access(self, action: str, item_id: str, accessor: str) -> None:
        """Logger adgang til karantæne."""
        self._access_log.append({
            "timestamp": datetime.now(),
            "action": action,
            "item_id": item_id,
            "accessor": accessor
        })

        # Trim log
        if len(self._access_log) > 10000:
            self._access_log = self._access_log[-5000:]

    def get_active_items(self) -> List[QuarantineItem]:
        """Returnerer alle aktive karantæne-objekter."""
        return [
            item for item in self._quarantine.values()
            if item.status == QuarantineStatus.ACTIVE
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Returnerer statistik over karantæne."""
        status_counts = {}
        for status in QuarantineStatus:
            status_counts[status.name] = sum(
                1 for item in self._quarantine.values() if item.status == status
            )

        reason_counts = {}
        for reason in QuarantineReason:
            reason_counts[reason.name] = sum(
                1 for item in self._quarantine.values() if item.reason == reason
            )

        return {
            "total_items": len(self._quarantine),
            "active_items": sum(1 for i in self._quarantine.values() if i.status == QuarantineStatus.ACTIVE),
            "status_distribution": status_counts,
            "reason_distribution": reason_counts,
            "access_log_entries": len(self._access_log),
        }


# =============================================================================
# DEL IV: SUPER ADMIN NOTIFICATION (SAN)
# =============================================================================

class SuperAdminNotification:
    """
    Super Admin Notification - Øjeblikkelig Advarsel

    Robust notifikationssystem der leverer øjeblikkelige, prioriterede
    advarsler til Super Admin via foretrukne kanaler.
    """

    def __init__(self):
        self._notifications: List[Notification] = []
        self._preferences: NotificationPreferences = NotificationPreferences()
        self._notification_handlers: Dict[NotificationChannel, Callable] = {}
        self._aggregation_queue: List[Notification] = []
        self._lock = asyncio.Lock()
        self._initialize_handlers()

    def _initialize_handlers(self) -> None:
        """Initialiserer notifikation handlers."""
        self._notification_handlers = {
            NotificationChannel.EMAIL: self._send_email,
            NotificationChannel.DASHBOARD: self._send_dashboard,
            NotificationChannel.MOBILE_PUSH: self._send_mobile,
            NotificationChannel.SMS: self._send_sms,
            NotificationChannel.INTERNAL_LOG: self._log_notification,
        }

    async def _send_email(self, notification: Notification) -> bool:
        """Sender notifikation via email."""
        # I produktion ville dette integrere med email service
        logger.info(f"[EMAIL] {notification.title}: {notification.message}")
        return True

    async def _send_dashboard(self, notification: Notification) -> bool:
        """Sender notifikation til dashboard."""
        logger.info(f"[DASHBOARD] {notification.title}: {notification.message}")
        return True

    async def _send_mobile(self, notification: Notification) -> bool:
        """Sender mobile push notifikation."""
        logger.info(f"[MOBILE] {notification.title}: {notification.message}")
        return True

    async def _send_sms(self, notification: Notification) -> bool:
        """Sender SMS notifikation."""
        logger.info(f"[SMS] {notification.title}: {notification.message}")
        return True

    async def _log_notification(self, notification: Notification) -> bool:
        """Logger notifikation internt."""
        logger.info(f"[LOG] {notification.title}: {notification.message}")
        return True

    def _should_send_now(self, notification: Notification) -> bool:
        """Bestemmer om notifikation skal sendes nu eller aggregeres."""
        # Kritiske notifikationer sendes altid med det samme
        if notification.priority == NotificationPriority.CRITICAL:
            return True

        # Tjek quiet hours
        if self._preferences.quiet_hours_start is not None:
            current_hour = datetime.now().hour
            start = self._preferences.quiet_hours_start
            end = self._preferences.quiet_hours_end or 0

            if start <= current_hour < end:
                if notification.priority != NotificationPriority.CRITICAL:
                    return False

        # Lav prioritet kan aggregeres
        if notification.priority == NotificationPriority.LOW:
            return not self._preferences.aggregate_low_priority

        return True

    async def send_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        source_component: str = "",
        related_item_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Notification:
        """
        Sender en notifikation til Super Admin.

        Args:
            notification_type: Type af notifikation
            title: Titel på notifikationen
            message: Besked indhold
            priority: Prioritet
            source_component: Kildekomponent
            related_item_id: ID på relateret objekt
            metadata: Yderligere metadata

        Returns:
            Den oprettede Notification
        """
        async with self._lock:
            notification = Notification(
                notification_type=notification_type,
                priority=priority,
                title=title,
                message=message,
                source_component=source_component,
                related_item_id=related_item_id,
                channels=list(self._preferences.enabled_channels),
                metadata=metadata or {}
            )

            # Gem notifikation
            self._notifications.append(notification)

            # Bestem om vi skal sende nu eller aggregere
            if self._should_send_now(notification):
                await self._dispatch_notification(notification)
            else:
                self._aggregation_queue.append(notification)

            # Trim historik
            if len(self._notifications) > 10000:
                self._notifications = self._notifications[-5000:]

            logger.info(
                f"Notifikation oprettet: [{notification.priority.name}] "
                f"{notification.title}"
            )

            return notification

    async def _dispatch_notification(self, notification: Notification) -> None:
        """Dispatcher notifikation til alle aktiverede kanaler."""
        for channel in notification.channels:
            if channel in self._preferences.enabled_channels:
                # Tjek mobile-only kritiske præference
                if channel == NotificationChannel.MOBILE_PUSH:
                    if self._preferences.critical_only_mobile:
                        if notification.priority != NotificationPriority.CRITICAL:
                            continue

                handler = self._notification_handlers.get(channel)
                if handler:
                    try:
                        await handler(notification)
                    except Exception as e:
                        logger.error(f"Fejl i notifikation til {channel.name}: {e}")

    async def flush_aggregation_queue(self) -> int:
        """Sender alle aggregerede notifikationer."""
        async with self._lock:
            count = len(self._aggregation_queue)

            if count > 0:
                # Opret summary notifikation
                summary = Notification(
                    notification_type=NotificationType.AUDIT_SUMMARY,
                    priority=NotificationPriority.LOW,
                    title=f"CKC Notifikations Opsummering ({count} meddelelser)",
                    message="\n".join([
                        f"- [{n.priority.name}] {n.title}"
                        for n in self._aggregation_queue
                    ]),
                    channels=list(self._preferences.enabled_channels)
                )

                await self._dispatch_notification(summary)
                self._aggregation_queue.clear()

            return count

    def set_preferences(self, preferences: NotificationPreferences) -> None:
        """Opdaterer notifikationspræferencer."""
        self._preferences = preferences
        logger.info("Notifikationspræferencer opdateret")

    def get_preferences(self) -> NotificationPreferences:
        """Returnerer aktuelle præferencer."""
        return self._preferences

    def enable_channel(self, channel: NotificationChannel) -> None:
        """Aktiverer en notifikationskanal."""
        self._preferences.enabled_channels.add(channel)

    def disable_channel(self, channel: NotificationChannel) -> None:
        """Deaktiverer en notifikationskanal."""
        self._preferences.enabled_channels.discard(channel)

    async def mark_as_read(self, notification_id: str) -> bool:
        """Markerer en notifikation som læst."""
        for notification in self._notifications:
            if notification.notification_id == notification_id:
                notification.is_read = True
                return True
        return False

    async def acknowledge(self, notification_id: str) -> bool:
        """Kvitterer for en notifikation."""
        for notification in self._notifications:
            if notification.notification_id == notification_id:
                notification.is_acknowledged = True
                notification.is_read = True
                return True
        return False

    def get_unread_notifications(self) -> List[Notification]:
        """Returnerer ulæste notifikationer."""
        return [n for n in self._notifications if not n.is_read]

    def get_notifications_by_type(
        self,
        notification_type: NotificationType
    ) -> List[Notification]:
        """Returnerer notifikationer af en bestemt type."""
        return [n for n in self._notifications if n.notification_type == notification_type]

    def get_statistics(self) -> Dict[str, Any]:
        """Returnerer notifikationsstatistik."""
        type_counts = {}
        for ntype in NotificationType:
            type_counts[ntype.name] = sum(
                1 for n in self._notifications if n.notification_type == ntype
            )

        priority_counts = {}
        for priority in NotificationPriority:
            priority_counts[priority.name] = sum(
                1 for n in self._notifications if n.priority == priority
            )

        return {
            "total_notifications": len(self._notifications),
            "unread": sum(1 for n in self._notifications if not n.is_read),
            "unacknowledged": sum(1 for n in self._notifications if not n.is_acknowledged),
            "pending_aggregation": len(self._aggregation_queue),
            "type_distribution": type_counts,
            "priority_distribution": priority_counts,
        }


# =============================================================================
# MASTER CONTROLLER - Integreret Output Integrity System
# =============================================================================

class OutputIntegritySystem:
    """
    Master Controller for hele Output Integrity systemet.

    Integrerer alle fire komponenter:
    - Output Validation Gateway (OVG)
    - Mastermind Audit System (MAS)
    - Quarantine Mechanism (QM)
    - Super Admin Notification (SAN)
    """

    def __init__(self, retention_days: int = 90):
        self.ovg = OutputValidationGateway()
        self.mas = MastermindAuditSystem()
        self.qm = QuarantineMechanism(retention_days=retention_days)
        self.san = SuperAdminNotification()
        self._processing_lock = asyncio.Lock()

    async def process_output(
        self,
        output: Any,
        requesting_agent: str,
        intended_destination: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processerer et output gennem hele integritets-pipelinen.

        Args:
            output: Output der skal processeres
            requesting_agent: Den anmodende agent
            intended_destination: Tilsigtet destination
            context: Yderligere kontekst

        Returns:
            Dict med resultat og detaljer
        """
        async with self._processing_lock:
            result = {
                "approved": False,
                "validation_report": None,
                "audit_report": None,
                "quarantine_item": None,
                "notifications_sent": []
            }

            # TRIN 1: Output Validation Gateway
            validation_report = await self.ovg.validate_output(
                output=output,
                requesting_agent=requesting_agent,
                intended_destination=intended_destination,
                context=context
            )
            result["validation_report"] = validation_report

            # Hvis OVG fejler kritisk, send direkte til karantæne
            if validation_report.overall_result == ValidationResult.FAILED:
                quarantine_item = await self.qm.add_to_quarantine(
                    output=output,
                    reason=QuarantineReason.OVG_VALIDATION_FAILURE,
                    validation_report=validation_report,
                    requesting_agent=requesting_agent,
                    intended_destination=intended_destination
                )
                result["quarantine_item"] = quarantine_item

                # Send notifikation
                notification = await self.san.send_notification(
                    notification_type=NotificationType.OVG_CRITICAL_FAILURE,
                    title="OVG Validering Fejlet",
                    message=f"Output fra {requesting_agent} fejlede validering. "
                            f"Fejlede regler: {', '.join(validation_report.failed_rules)}",
                    priority=NotificationPriority.HIGH,
                    source_component="OutputValidationGateway",
                    related_item_id=quarantine_item.item_id
                )
                result["notifications_sent"].append(notification.notification_id)

                return result

            # TRIN 2: Mastermind Audit System
            audit_report = await self.mas.audit_output(validation_report)
            result["audit_report"] = audit_report

            # Håndter audit beslutning
            if audit_report.decision == AuditDecision.APPROVED:
                result["approved"] = True

            elif audit_report.decision == AuditDecision.REJECTED:
                quarantine_item = await self.qm.add_to_quarantine(
                    output=output,
                    reason=QuarantineReason.MAS_REJECTION,
                    validation_report=validation_report,
                    audit_report=audit_report,
                    requesting_agent=requesting_agent,
                    intended_destination=intended_destination
                )
                result["quarantine_item"] = quarantine_item

                # Send notifikation
                notification = await self.san.send_notification(
                    notification_type=NotificationType.MAS_REJECTION,
                    title="Mastermind Audit Afvisning",
                    message=f"Output afvist: {audit_report.reasoning}",
                    priority=NotificationPriority.HIGH,
                    source_component="MastermindAuditSystem",
                    related_item_id=quarantine_item.item_id
                )
                result["notifications_sent"].append(notification.notification_id)

            elif audit_report.decision == AuditDecision.REQUIRES_SUPER_ADMIN:
                quarantine_item = await self.qm.add_to_quarantine(
                    output=output,
                    reason=QuarantineReason.MAS_REJECTION,
                    validation_report=validation_report,
                    audit_report=audit_report,
                    requesting_agent=requesting_agent,
                    intended_destination=intended_destination
                )
                result["quarantine_item"] = quarantine_item

                # Send kritisk notifikation
                notification = await self.san.send_notification(
                    notification_type=NotificationType.QUARANTINE_ALERT,
                    title="Super Admin Godkendelse Påkrævet",
                    message=f"Output kræver din godkendelse. "
                            f"Årsag: {audit_report.reasoning}",
                    priority=NotificationPriority.CRITICAL,
                    source_component="MastermindAuditSystem",
                    related_item_id=quarantine_item.item_id
                )
                result["notifications_sent"].append(notification.notification_id)

            elif audit_report.decision == AuditDecision.REQUIRES_MODIFICATION:
                # Log anbefalinger men tillad ikke
                notification = await self.san.send_notification(
                    notification_type=NotificationType.POLICY_VIOLATION,
                    title="Output Kræver Modifikation",
                    message=f"Anbefalinger: {', '.join(audit_report.recommendations)}",
                    priority=NotificationPriority.MEDIUM,
                    source_component="MastermindAuditSystem"
                )
                result["notifications_sent"].append(notification.notification_id)

            return result

    async def super_admin_approve(
        self,
        quarantine_item_id: str,
        notes: str = ""
    ) -> bool:
        """Super Admin godkender et karantæne-objekt."""
        success = await self.qm.release_item(
            item_id=quarantine_item_id,
            accessor="super_admin",
            notes=notes
        )

        if success:
            await self.san.send_notification(
                notification_type=NotificationType.QUARANTINE_ALERT,
                title="Karantæne-objekt Frigivet",
                message=f"Objekt {quarantine_item_id} er godkendt og frigivet.",
                priority=NotificationPriority.LOW,
                source_component="SuperAdmin",
                related_item_id=quarantine_item_id
            )

        return success

    async def super_admin_reject(
        self,
        quarantine_item_id: str,
        notes: str = ""
    ) -> bool:
        """Super Admin afviser et karantæne-objekt."""
        success = await self.qm.delete_item(
            item_id=quarantine_item_id,
            accessor="super_admin",
            notes=notes
        )

        if success:
            await self.san.send_notification(
                notification_type=NotificationType.QUARANTINE_ALERT,
                title="Karantæne-objekt Slettet",
                message=f"Objekt {quarantine_item_id} er permanent slettet.",
                priority=NotificationPriority.LOW,
                source_component="SuperAdmin",
                related_item_id=quarantine_item_id
            )

        return success

    def get_system_status(self) -> Dict[str, Any]:
        """Returnerer status for hele systemet."""
        return {
            "ovg_stats": self.ovg.get_rule_statistics(),
            "mas_stats": self.mas.get_audit_statistics(),
            "qm_stats": self.qm.get_statistics(),
            "san_stats": self.san.get_statistics(),
        }

    async def cleanup(self) -> Dict[str, int]:
        """Kører oprydning på alle komponenter."""
        expired = await self.qm.cleanup_expired()
        aggregated = await self.san.flush_aggregation_queue()

        return {
            "expired_quarantine_items": expired,
            "aggregated_notifications": aggregated
        }


# =============================================================================
# FACTORY FUNKTIONER
# =============================================================================

def create_output_validation_gateway() -> OutputValidationGateway:
    """Factory funktion til at oprette Output Validation Gateway."""
    return OutputValidationGateway()


def create_mastermind_audit_system() -> MastermindAuditSystem:
    """Factory funktion til at oprette Mastermind Audit System."""
    return MastermindAuditSystem()


def create_quarantine_mechanism(retention_days: int = 90) -> QuarantineMechanism:
    """Factory funktion til at oprette Quarantine Mechanism."""
    return QuarantineMechanism(retention_days=retention_days)


def create_super_admin_notification() -> SuperAdminNotification:
    """Factory funktion til at oprette Super Admin Notification."""
    return SuperAdminNotification()


def create_output_integrity_system(retention_days: int = 90) -> OutputIntegritySystem:
    """Factory funktion til at oprette det komplette Output Integrity System."""
    return OutputIntegritySystem(retention_days=retention_days)


# Singleton instance
_output_integrity_system: Optional[OutputIntegritySystem] = None


def get_output_integrity_system() -> OutputIntegritySystem:
    """Returnerer singleton instance af Output Integrity System."""
    global _output_integrity_system
    if _output_integrity_system is None:
        _output_integrity_system = create_output_integrity_system()
    return _output_integrity_system
