"""
DEL G: Etisk AI & Transparens Protokoller
==========================================

Modul for etisk AI-håndtering og transparens i MASTERMIND systemet.

Komponenter:
- BiasDetector: Opdagelse af bias i outputs
- TransparencyLogger: Fuld audit trail
- ExplainabilityEngine: Forklaring af beslutninger
- EthicsGuardrails: Sikkerhedsmekanismer
- ComplianceReporter: GDPR/AI Act compliance

Eksempel:
    from cirkelline.ckc.mastermind.ethics import (
        create_bias_detector,
        create_transparency_logger,
        create_explainability_engine,
        create_ethics_guardrails,
        create_compliance_reporter,
    )

    # Setup
    bias_detector = create_bias_detector()
    logger = create_transparency_logger()
    explainer = create_explainability_engine()
    guardrails = create_ethics_guardrails()
    compliance = create_compliance_reporter()

    # Check for bias
    result = await bias_detector.analyze("Some AI output text")

    # Log decision
    await logger.log_decision(decision_id, context, outcome)

    # Get explanation
    explanation = await explainer.explain_decision(decision_id)
"""

from __future__ import annotations

import uuid
import json
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, TypeVar
from collections import defaultdict


# =============================================================================
# ENUMS
# =============================================================================


class BiasType(Enum):
    """Typer af bias der kan detekteres."""
    GENDER = "gender"
    RACIAL = "racial"
    AGE = "age"
    CULTURAL = "cultural"
    SOCIOECONOMIC = "socioeconomic"
    LANGUAGE = "language"
    CONFIRMATION = "confirmation"
    SELECTION = "selection"
    UNKNOWN = "unknown"


class BiasLevel(Enum):
    """Niveau af detekteret bias."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionType(Enum):
    """Typer af beslutninger der logges."""
    TASK_ASSIGNMENT = "task_assignment"
    RESOURCE_ALLOCATION = "resource_allocation"
    CONTENT_GENERATION = "content_generation"
    USER_INTERACTION = "user_interaction"
    SYSTEM_CONFIGURATION = "system_configuration"
    AGENT_SELECTION = "agent_selection"
    PRIORITY_CHANGE = "priority_change"
    ACCESS_CONTROL = "access_control"


class ComplianceStandard(Enum):
    """Compliance standarder."""
    GDPR = "gdpr"
    AI_ACT = "ai_act"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


class GuardrailType(Enum):
    """Typer af etiske guardrails."""
    CONTENT_FILTER = "content_filter"
    FAIRNESS_CHECK = "fairness_check"
    PRIVACY_PROTECTION = "privacy_protection"
    HARM_PREVENTION = "harm_prevention"
    TRANSPARENCY_REQUIREMENT = "transparency_requirement"
    CONSENT_VERIFICATION = "consent_verification"


class ViolationSeverity(Enum):
    """Alvorlighed af etiske overtrædelser."""
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class BiasIndicator:
    """Indikator for detekteret bias."""
    indicator_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    bias_type: BiasType = BiasType.UNKNOWN
    confidence: float = 0.0  # 0.0 - 1.0
    evidence: str = ""
    source_text: str = ""
    suggested_mitigation: str = ""
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class BiasReport:
    """Rapport over bias-analyse."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    content_analyzed: str = ""
    overall_level: BiasLevel = BiasLevel.NONE
    indicators: List[BiasIndicator] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    analysis_duration_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def has_bias(self) -> bool:
        """Returnerer True hvis bias er detekteret."""
        return self.overall_level not in (BiasLevel.NONE, BiasLevel.LOW)

    @property
    def indicator_count(self) -> int:
        """Antal bias-indikatorer."""
        return len(self.indicators)


@dataclass
class DecisionLog:
    """Log-entry for en beslutning."""
    log_id: str = field(default_factory=lambda: str(uuid.uuid4())[:16])
    decision_id: str = ""
    decision_type: DecisionType = DecisionType.SYSTEM_CONFIGURATION
    actor: str = ""  # Who made the decision (agent_id, user_id, system)
    context: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    confidence: float = 0.0
    alternatives_considered: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    is_explainable: bool = True


@dataclass
class Explanation:
    """Forklaring af en beslutning."""
    explanation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    decision_id: str = ""
    summary: str = ""  # Non-technical summary
    detailed_reasoning: str = ""  # Technical details
    factors: List[Dict[str, Any]] = field(default_factory=list)  # Contributing factors
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    counterfactuals: List[str] = field(default_factory=list)  # "If X was different..."
    created_at: datetime = field(default_factory=datetime.now)
    language: str = "da"  # Danish default


@dataclass
class GuardrailViolation:
    """Overtrædelse af en guardrail."""
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    guardrail_type: GuardrailType = GuardrailType.CONTENT_FILTER
    severity: ViolationSeverity = ViolationSeverity.WARNING
    description: str = ""
    content_flagged: str = ""
    action_taken: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    blocked: bool = False


@dataclass
class ComplianceStatus:
    """Status for compliance med en standard."""
    standard: ComplianceStandard = ComplianceStandard.GDPR
    is_compliant: bool = True
    last_audit: datetime = field(default_factory=datetime.now)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    score: float = 100.0  # 0-100


@dataclass
class ComplianceReport:
    """Samlet compliance rapport."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    generated_at: datetime = field(default_factory=datetime.now)
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    statuses: List[ComplianceStatus] = field(default_factory=list)
    total_decisions_logged: int = 0
    violations_detected: int = 0
    bias_incidents: int = 0
    overall_score: float = 100.0

    @property
    def is_fully_compliant(self) -> bool:
        """Returnerer True hvis alle standarder er opfyldt."""
        return all(s.is_compliant for s in self.statuses)


# =============================================================================
# BIAS DETECTOR
# =============================================================================


class BiasDetector:
    """
    Detektor for bias i AI outputs.

    Analyserer tekst og identificerer potentielle bias-indikatorer.
    """

    def __init__(
        self,
        sensitivity: float = 0.5,
        enabled_types: Optional[Set[BiasType]] = None,
    ):
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        self.enabled_types = enabled_types or set(BiasType)
        self._lock = asyncio.Lock()

        # Simplified bias indicators (in production, use ML models)
        self._gender_indicators = {
            "han", "hun", "mand", "kvinde", "dreng", "pige",
            "he", "she", "man", "woman", "boy", "girl"
        }
        self._age_indicators = {
            "ung", "gammel", "ældre", "teenager", "pensionist",
            "young", "old", "elderly", "teenager", "senior"
        }

    async def analyze(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> BiasReport:
        """Analysér indhold for bias."""
        start_time = datetime.now()

        async with self._lock:
            indicators = []

            # Check for various bias types
            content_lower = content.lower()
            words = set(content_lower.split())

            # Gender bias check
            if BiasType.GENDER in self.enabled_types:
                gender_words = words.intersection(self._gender_indicators)
                if gender_words and self.sensitivity > 0.3:
                    indicators.append(BiasIndicator(
                        bias_type=BiasType.GENDER,
                        confidence=0.3 + (len(gender_words) * 0.1),
                        evidence=f"Kønsspecifikke ord fundet: {gender_words}",
                        source_text=content[:100],
                        suggested_mitigation="Overvej kønsneutrale alternativer"
                    ))

            # Age bias check
            if BiasType.AGE in self.enabled_types:
                age_words = words.intersection(self._age_indicators)
                if age_words and self.sensitivity > 0.4:
                    indicators.append(BiasIndicator(
                        bias_type=BiasType.AGE,
                        confidence=0.2 + (len(age_words) * 0.1),
                        evidence=f"Aldersspecifikke ord fundet: {age_words}",
                        source_text=content[:100],
                        suggested_mitigation="Overvej aldersneutrale formuleringer"
                    ))

            # Determine overall level
            if not indicators:
                overall_level = BiasLevel.NONE
            else:
                max_confidence = max(i.confidence for i in indicators)
                if max_confidence < 0.3:
                    overall_level = BiasLevel.LOW
                elif max_confidence < 0.5:
                    overall_level = BiasLevel.MEDIUM
                elif max_confidence < 0.7:
                    overall_level = BiasLevel.HIGH
                else:
                    overall_level = BiasLevel.CRITICAL

            # Generate recommendations
            recommendations = []
            if indicators:
                recommendations.append("Gennemgå markeret indhold for potentiel bias")
                if overall_level in (BiasLevel.HIGH, BiasLevel.CRITICAL):
                    recommendations.append("Overvej manuel gennemgang før publicering")

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return BiasReport(
                content_analyzed=content[:500],  # Truncate for storage
                overall_level=overall_level,
                indicators=indicators,
                recommendations=recommendations,
                analysis_duration_ms=duration_ms,
            )

    def set_sensitivity(self, sensitivity: float) -> None:
        """Sæt følsomhed for bias-detektion."""
        self.sensitivity = max(0.0, min(1.0, sensitivity))

    def enable_bias_type(self, bias_type: BiasType) -> None:
        """Aktivér detektion af specifik bias-type."""
        self.enabled_types.add(bias_type)

    def disable_bias_type(self, bias_type: BiasType) -> None:
        """Deaktivér detektion af specifik bias-type."""
        self.enabled_types.discard(bias_type)


# =============================================================================
# TRANSPARENCY LOGGER
# =============================================================================


class TransparencyLogger:
    """
    Logger for fuld transparens og audit trail.

    Logger alle beslutninger med fuld kontekst for efterfølgende
    analyse og forklaring.
    """

    def __init__(self, retention_days: int = 90):
        self.retention_days = retention_days
        self._logs: Dict[str, DecisionLog] = {}
        self._by_session: Dict[str, List[str]] = defaultdict(list)
        self._by_actor: Dict[str, List[str]] = defaultdict(list)
        self._by_type: Dict[DecisionType, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def log_decision(
        self,
        decision_id: str,
        decision_type: DecisionType,
        actor: str,
        context: Dict[str, Any],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        reasoning: str = "",
        confidence: float = 0.0,
        alternatives: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
    ) -> DecisionLog:
        """Log en beslutning med fuld kontekst."""
        async with self._lock:
            log = DecisionLog(
                decision_id=decision_id,
                decision_type=decision_type,
                actor=actor,
                context=context,
                input_data=input_data,
                output_data=output_data,
                reasoning=reasoning,
                confidence=confidence,
                alternatives_considered=alternatives or [],
                session_id=session_id,
            )

            self._logs[log.log_id] = log
            self._by_actor[actor].append(log.log_id)
            self._by_type[decision_type].append(log.log_id)

            if session_id:
                self._by_session[session_id].append(log.log_id)

            return log

    async def get_log(self, log_id: str) -> Optional[DecisionLog]:
        """Hent specifik log entry."""
        async with self._lock:
            return self._logs.get(log_id)

    async def get_logs_by_decision(self, decision_id: str) -> List[DecisionLog]:
        """Hent alle logs for en beslutning."""
        async with self._lock:
            return [
                log for log in self._logs.values()
                if log.decision_id == decision_id
            ]

    async def get_logs_by_session(self, session_id: str) -> List[DecisionLog]:
        """Hent alle logs for en session."""
        async with self._lock:
            log_ids = self._by_session.get(session_id, [])
            return [self._logs[lid] for lid in log_ids if lid in self._logs]

    async def get_logs_by_actor(self, actor: str) -> List[DecisionLog]:
        """Hent alle logs for en aktør."""
        async with self._lock:
            log_ids = self._by_actor.get(actor, [])
            return [self._logs[lid] for lid in log_ids if lid in self._logs]

    async def get_logs_by_type(self, decision_type: DecisionType) -> List[DecisionLog]:
        """Hent alle logs af en type."""
        async with self._lock:
            log_ids = self._by_type.get(decision_type, [])
            return [self._logs[lid] for lid in log_ids if lid in self._logs]

    async def get_audit_trail(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[DecisionLog]:
        """Hent audit trail for en tidsperiode."""
        async with self._lock:
            logs = list(self._logs.values())

            if start_time:
                logs = [l for l in logs if l.timestamp >= start_time]
            if end_time:
                logs = [l for l in logs if l.timestamp <= end_time]

            return sorted(logs, key=lambda l: l.timestamp)

    async def cleanup_old_logs(self) -> int:
        """Fjern logs ældre end retention period."""
        async with self._lock:
            cutoff = datetime.now() - timedelta(days=self.retention_days)
            old_ids = [
                lid for lid, log in self._logs.items()
                if log.timestamp < cutoff
            ]

            for lid in old_ids:
                del self._logs[lid]

            return len(old_ids)

    async def get_statistics(self) -> Dict[str, Any]:
        """Hent statistik over logget aktivitet."""
        async with self._lock:
            total = len(self._logs)
            by_type = {dt.value: len(ids) for dt, ids in self._by_type.items()}

            return {
                "total_logs": total,
                "by_decision_type": by_type,
                "unique_actors": len(self._by_actor),
                "unique_sessions": len(self._by_session),
            }


# =============================================================================
# EXPLAINABILITY ENGINE
# =============================================================================


class ExplainabilityEngine:
    """
    Engine til at generere forklaringer af AI-beslutninger.

    Opretter menneskevenlige forklaringer baseret på loggede
    beslutninger og deres kontekst.
    """

    def __init__(
        self,
        transparency_logger: TransparencyLogger,
        default_language: str = "da",
    ):
        self.logger = transparency_logger
        self.default_language = default_language
        self._explanations: Dict[str, Explanation] = {}
        self._lock = asyncio.Lock()

    async def explain_decision(
        self,
        decision_id: str,
        language: Optional[str] = None,
    ) -> Optional[Explanation]:
        """Generer forklaring for en beslutning."""
        logs = await self.logger.get_logs_by_decision(decision_id)

        if not logs:
            return None

        log = logs[0]  # Primary log
        lang = language or self.default_language

        async with self._lock:
            # Generate summary based on decision type
            summary = self._generate_summary(log, lang)
            detailed = self._generate_detailed_reasoning(log, lang)
            factors = self._extract_factors(log)
            counterfactuals = self._generate_counterfactuals(log, lang)

            explanation = Explanation(
                decision_id=decision_id,
                summary=summary,
                detailed_reasoning=detailed,
                factors=factors,
                confidence_breakdown={"overall": log.confidence},
                counterfactuals=counterfactuals,
                language=lang,
            )

            self._explanations[explanation.explanation_id] = explanation
            return explanation

    def _generate_summary(self, log: DecisionLog, lang: str) -> str:
        """Generer ikke-teknisk opsummering."""
        if lang == "da":
            type_names = {
                DecisionType.TASK_ASSIGNMENT: "opgavetildeling",
                DecisionType.RESOURCE_ALLOCATION: "ressourceallokering",
                DecisionType.CONTENT_GENERATION: "indholdsgenerering",
                DecisionType.USER_INTERACTION: "brugerinteraktion",
                DecisionType.SYSTEM_CONFIGURATION: "systemkonfiguration",
                DecisionType.AGENT_SELECTION: "agentvalg",
                DecisionType.PRIORITY_CHANGE: "prioritetsændring",
                DecisionType.ACCESS_CONTROL: "adgangskontrol",
            }
            type_name = type_names.get(log.decision_type, "beslutning")
            return f"Denne {type_name} blev foretaget af {log.actor} med {log.confidence*100:.0f}% sikkerhed."
        else:
            return f"This decision was made by {log.actor} with {log.confidence*100:.0f}% confidence."

    def _generate_detailed_reasoning(self, log: DecisionLog, lang: str) -> str:
        """Generer detaljeret teknisk forklaring."""
        if log.reasoning:
            return log.reasoning

        if lang == "da":
            return f"Beslutningen var baseret på konteksten: {json.dumps(log.context, ensure_ascii=False)}"
        else:
            return f"Decision was based on context: {json.dumps(log.context)}"

    def _extract_factors(self, log: DecisionLog) -> List[Dict[str, Any]]:
        """Udtræk bidragende faktorer."""
        factors = []

        for key, value in log.context.items():
            factors.append({
                "factor": key,
                "value": value,
                "impact": "contributing"
            })

        return factors

    def _generate_counterfactuals(self, log: DecisionLog, lang: str) -> List[str]:
        """Generer kontrafaktiske forklaringer."""
        counterfactuals = []

        for alt in log.alternatives_considered:
            if lang == "da":
                counterfactuals.append(
                    f"Hvis {alt.get('condition', 'betingelsen')} var anderledes, "
                    f"ville resultatet være {alt.get('outcome', 'anderledes')}"
                )
            else:
                counterfactuals.append(
                    f"If {alt.get('condition', 'condition')} was different, "
                    f"outcome would be {alt.get('outcome', 'different')}"
                )

        return counterfactuals

    async def get_explanation(self, explanation_id: str) -> Optional[Explanation]:
        """Hent eksisterende forklaring."""
        async with self._lock:
            return self._explanations.get(explanation_id)


# =============================================================================
# ETHICS GUARDRAILS
# =============================================================================


class EthicsGuardrails:
    """
    Sikkerhedsmekanismer for etisk AI-adfærd.

    Implementerer guardrails der sikrer at AI-systemet opererer
    indenfor etiske grænser.
    """

    def __init__(self):
        self._enabled_guardrails: Set[GuardrailType] = set(GuardrailType)
        self._violations: List[GuardrailViolation] = []
        self._blocked_patterns: Set[str] = set()
        self._lock = asyncio.Lock()

        # Default blocked patterns
        self._harmful_keywords = {
            "hack", "exploit", "attack", "steal", "illegal"
        }

    async def check_content(
        self,
        content: str,
        guardrail_type: Optional[GuardrailType] = None,
    ) -> Optional[GuardrailViolation]:
        """Tjek indhold mod guardrails."""
        async with self._lock:
            types_to_check = [guardrail_type] if guardrail_type else self._enabled_guardrails

            for gt in types_to_check:
                if gt not in self._enabled_guardrails:
                    continue

                violation = self._check_guardrail(content, gt)
                if violation:
                    self._violations.append(violation)
                    return violation

            return None

    def _check_guardrail(self, content: str, guardrail_type: GuardrailType) -> Optional[GuardrailViolation]:
        """Tjek specifik guardrail."""
        content_lower = content.lower()

        if guardrail_type == GuardrailType.CONTENT_FILTER:
            # Check for harmful content
            for keyword in self._harmful_keywords:
                if keyword in content_lower:
                    return GuardrailViolation(
                        guardrail_type=guardrail_type,
                        severity=ViolationSeverity.WARNING,
                        description=f"Potentielt skadeligt indhold detekteret",
                        content_flagged=content[:100],
                        action_taken="Indhold markeret for review",
                        blocked=False,
                    )

        elif guardrail_type == GuardrailType.PRIVACY_PROTECTION:
            # Simple PII detection (simplified)
            pii_patterns = ["@", "cpr", "personnummer"]
            for pattern in pii_patterns:
                if pattern in content_lower:
                    return GuardrailViolation(
                        guardrail_type=guardrail_type,
                        severity=ViolationSeverity.VIOLATION,
                        description="Potentiel personlig information detekteret",
                        content_flagged="[REDACTED]",
                        action_taken="Indhold blokeret",
                        blocked=True,
                    )

        return None

    async def enable_guardrail(self, guardrail_type: GuardrailType) -> None:
        """Aktivér guardrail."""
        async with self._lock:
            self._enabled_guardrails.add(guardrail_type)

    async def disable_guardrail(self, guardrail_type: GuardrailType) -> None:
        """Deaktivér guardrail."""
        async with self._lock:
            self._enabled_guardrails.discard(guardrail_type)

    async def add_blocked_pattern(self, pattern: str) -> None:
        """Tilføj blokeret mønster."""
        async with self._lock:
            self._blocked_patterns.add(pattern.lower())

    async def get_violations(
        self,
        since: Optional[datetime] = None,
    ) -> List[GuardrailViolation]:
        """Hent registrerede violations."""
        async with self._lock:
            if since:
                return [v for v in self._violations if v.timestamp >= since]
            return list(self._violations)

    async def get_statistics(self) -> Dict[str, Any]:
        """Hent statistik over guardrail aktivitet."""
        async with self._lock:
            by_type = defaultdict(int)
            by_severity = defaultdict(int)
            blocked_count = 0

            for v in self._violations:
                by_type[v.guardrail_type.value] += 1
                by_severity[v.severity.value] += 1
                if v.blocked:
                    blocked_count += 1

            return {
                "total_violations": len(self._violations),
                "blocked_count": blocked_count,
                "by_type": dict(by_type),
                "by_severity": dict(by_severity),
                "enabled_guardrails": [g.value for g in self._enabled_guardrails],
            }


# =============================================================================
# COMPLIANCE REPORTER
# =============================================================================


class ComplianceReporter:
    """
    Reporter for compliance med regulatoriske standarder.

    Genererer compliance-rapporter for GDPR, AI Act, osv.
    """

    def __init__(
        self,
        transparency_logger: TransparencyLogger,
        guardrails: EthicsGuardrails,
        bias_detector: BiasDetector,
    ):
        self.logger = transparency_logger
        self.guardrails = guardrails
        self.bias_detector = bias_detector
        self._reports: List[ComplianceReport] = []
        self._lock = asyncio.Lock()

    async def check_compliance(
        self,
        standard: ComplianceStandard,
    ) -> ComplianceStatus:
        """Tjek compliance med en specifik standard."""
        issues = []
        recommendations = []
        score = 100.0

        if standard == ComplianceStandard.GDPR:
            # Check for data protection compliance
            stats = await self.logger.get_statistics()
            guardrail_stats = await self.guardrails.get_statistics()

            if guardrail_stats["blocked_count"] > 0:
                score -= 10
                issues.append("Blokerede privacy-relaterede handlinger")

            if stats["total_logs"] == 0:
                score -= 20
                issues.append("Ingen beslutningslogning aktiveret")
                recommendations.append("Aktivér fuld beslutningslogning")

        elif standard == ComplianceStandard.AI_ACT:
            # Check for AI Act compliance
            guardrail_stats = await self.guardrails.get_statistics()

            if len(guardrail_stats["enabled_guardrails"]) < 3:
                score -= 30
                issues.append("For få guardrails aktiveret")
                recommendations.append("Aktivér alle relevante guardrails")

        return ComplianceStatus(
            standard=standard,
            is_compliant=score >= 70,
            issues=issues,
            recommendations=recommendations,
            score=score,
        )

    async def generate_report(
        self,
        standards: Optional[List[ComplianceStandard]] = None,
        period_days: int = 30,
    ) -> ComplianceReport:
        """Generer samlet compliance rapport."""
        standards = standards or list(ComplianceStandard)

        async with self._lock:
            statuses = []
            for standard in standards:
                status = await self.check_compliance(standard)
                statuses.append(status)

            # Get statistics
            logger_stats = await self.logger.get_statistics()
            guardrail_stats = await self.guardrails.get_statistics()

            # Calculate overall score
            if statuses:
                overall_score = sum(s.score for s in statuses) / len(statuses)
            else:
                overall_score = 100.0

            report = ComplianceReport(
                period_start=datetime.now() - timedelta(days=period_days),
                period_end=datetime.now(),
                statuses=statuses,
                total_decisions_logged=logger_stats["total_logs"],
                violations_detected=guardrail_stats["total_violations"],
                bias_incidents=0,  # Would come from bias detector
                overall_score=overall_score,
            )

            self._reports.append(report)
            return report

    async def get_reports(
        self,
        since: Optional[datetime] = None,
    ) -> List[ComplianceReport]:
        """Hent genererede rapporter."""
        async with self._lock:
            if since:
                return [r for r in self._reports if r.generated_at >= since]
            return list(self._reports)

    async def export_report(
        self,
        report: ComplianceReport,
        format: str = "json",
    ) -> str:
        """Eksporter rapport til format."""
        if format == "json":
            return json.dumps({
                "report_id": report.report_id,
                "generated_at": report.generated_at.isoformat(),
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                "overall_score": report.overall_score,
                "is_fully_compliant": report.is_fully_compliant,
                "total_decisions_logged": report.total_decisions_logged,
                "violations_detected": report.violations_detected,
                "statuses": [
                    {
                        "standard": s.standard.value,
                        "is_compliant": s.is_compliant,
                        "score": s.score,
                        "issues": s.issues,
                        "recommendations": s.recommendations,
                    }
                    for s in report.statuses
                ],
            }, indent=2, ensure_ascii=False)

        return str(report)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


_bias_detector_instance: Optional[BiasDetector] = None
_transparency_logger_instance: Optional[TransparencyLogger] = None
_explainability_engine_instance: Optional[ExplainabilityEngine] = None
_ethics_guardrails_instance: Optional[EthicsGuardrails] = None
_compliance_reporter_instance: Optional[ComplianceReporter] = None


def create_bias_detector(
    sensitivity: float = 0.5,
    enabled_types: Optional[Set[BiasType]] = None,
) -> BiasDetector:
    """Opret BiasDetector instans."""
    global _bias_detector_instance
    _bias_detector_instance = BiasDetector(
        sensitivity=sensitivity,
        enabled_types=enabled_types,
    )
    return _bias_detector_instance


def get_bias_detector() -> Optional[BiasDetector]:
    """Hent eksisterende BiasDetector instans."""
    return _bias_detector_instance


def create_transparency_logger(
    retention_days: int = 90,
) -> TransparencyLogger:
    """Opret TransparencyLogger instans."""
    global _transparency_logger_instance
    _transparency_logger_instance = TransparencyLogger(
        retention_days=retention_days,
    )
    return _transparency_logger_instance


def get_transparency_logger() -> Optional[TransparencyLogger]:
    """Hent eksisterende TransparencyLogger instans."""
    return _transparency_logger_instance


def create_explainability_engine(
    transparency_logger: Optional[TransparencyLogger] = None,
    default_language: str = "da",
) -> ExplainabilityEngine:
    """Opret ExplainabilityEngine instans."""
    global _explainability_engine_instance
    logger = transparency_logger or get_transparency_logger() or create_transparency_logger()
    _explainability_engine_instance = ExplainabilityEngine(
        transparency_logger=logger,
        default_language=default_language,
    )
    return _explainability_engine_instance


def get_explainability_engine() -> Optional[ExplainabilityEngine]:
    """Hent eksisterende ExplainabilityEngine instans."""
    return _explainability_engine_instance


def create_ethics_guardrails() -> EthicsGuardrails:
    """Opret EthicsGuardrails instans."""
    global _ethics_guardrails_instance
    _ethics_guardrails_instance = EthicsGuardrails()
    return _ethics_guardrails_instance


def get_ethics_guardrails() -> Optional[EthicsGuardrails]:
    """Hent eksisterende EthicsGuardrails instans."""
    return _ethics_guardrails_instance


def create_compliance_reporter(
    transparency_logger: Optional[TransparencyLogger] = None,
    guardrails: Optional[EthicsGuardrails] = None,
    bias_detector: Optional[BiasDetector] = None,
) -> ComplianceReporter:
    """Opret ComplianceReporter instans."""
    global _compliance_reporter_instance
    logger = transparency_logger or get_transparency_logger() or create_transparency_logger()
    guards = guardrails or get_ethics_guardrails() or create_ethics_guardrails()
    detector = bias_detector or get_bias_detector() or create_bias_detector()
    _compliance_reporter_instance = ComplianceReporter(
        transparency_logger=logger,
        guardrails=guards,
        bias_detector=detector,
    )
    return _compliance_reporter_instance


def get_compliance_reporter() -> Optional[ComplianceReporter]:
    """Hent eksisterende ComplianceReporter instans."""
    return _compliance_reporter_instance


# =============================================================================
# ALL EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "BiasType",
    "BiasLevel",
    "DecisionType",
    "ComplianceStandard",
    "GuardrailType",
    "ViolationSeverity",

    # Data classes
    "BiasIndicator",
    "BiasReport",
    "DecisionLog",
    "Explanation",
    "GuardrailViolation",
    "ComplianceStatus",
    "ComplianceReport",

    # Classes
    "BiasDetector",
    "TransparencyLogger",
    "ExplainabilityEngine",
    "EthicsGuardrails",
    "ComplianceReporter",

    # Factory functions
    "create_bias_detector",
    "get_bias_detector",
    "create_transparency_logger",
    "get_transparency_logger",
    "create_explainability_engine",
    "get_explainability_engine",
    "create_ethics_guardrails",
    "get_ethics_guardrails",
    "create_compliance_reporter",
    "get_compliance_reporter",
]
