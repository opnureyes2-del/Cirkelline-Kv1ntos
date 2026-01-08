"""
Tests for DEL G: Etisk AI & Transparens Protokoller
====================================================

Tests for the ethics module (bias detection, transparency, explainability, guardrails, compliance).
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta


# =============================================================================
# TEST ENUMS
# =============================================================================


class TestEthicsEnums:
    """Tests for ethics enums."""

    def test_bias_type_values(self):
        """Test BiasType enum values."""
        from cirkelline.ckc.mastermind.ethics import BiasType

        assert BiasType.GENDER.value == "gender"
        assert BiasType.RACIAL.value == "racial"
        assert BiasType.AGE.value == "age"
        assert BiasType.CULTURAL.value == "cultural"
        assert BiasType.SOCIOECONOMIC.value == "socioeconomic"
        assert BiasType.LANGUAGE.value == "language"
        assert BiasType.CONFIRMATION.value == "confirmation"
        assert BiasType.SELECTION.value == "selection"
        assert BiasType.UNKNOWN.value == "unknown"

    def test_bias_level_values(self):
        """Test BiasLevel enum values."""
        from cirkelline.ckc.mastermind.ethics import BiasLevel

        assert BiasLevel.NONE.value == "none"
        assert BiasLevel.LOW.value == "low"
        assert BiasLevel.MEDIUM.value == "medium"
        assert BiasLevel.HIGH.value == "high"
        assert BiasLevel.CRITICAL.value == "critical"

    def test_decision_type_values(self):
        """Test DecisionType enum values."""
        from cirkelline.ckc.mastermind.ethics import DecisionType

        assert DecisionType.TASK_ASSIGNMENT.value == "task_assignment"
        assert DecisionType.RESOURCE_ALLOCATION.value == "resource_allocation"
        assert DecisionType.CONTENT_GENERATION.value == "content_generation"
        assert DecisionType.USER_INTERACTION.value == "user_interaction"

    def test_compliance_standard_values(self):
        """Test ComplianceStandard enum values."""
        from cirkelline.ckc.mastermind.ethics import ComplianceStandard

        assert ComplianceStandard.GDPR.value == "gdpr"
        assert ComplianceStandard.AI_ACT.value == "ai_act"
        assert ComplianceStandard.CCPA.value == "ccpa"
        assert ComplianceStandard.HIPAA.value == "hipaa"

    def test_guardrail_type_values(self):
        """Test GuardrailType enum values."""
        from cirkelline.ckc.mastermind.ethics import GuardrailType

        assert GuardrailType.CONTENT_FILTER.value == "content_filter"
        assert GuardrailType.FAIRNESS_CHECK.value == "fairness_check"
        assert GuardrailType.PRIVACY_PROTECTION.value == "privacy_protection"
        assert GuardrailType.HARM_PREVENTION.value == "harm_prevention"

    def test_violation_severity_values(self):
        """Test ViolationSeverity enum values."""
        from cirkelline.ckc.mastermind.ethics import ViolationSeverity

        assert ViolationSeverity.INFO.value == "info"
        assert ViolationSeverity.WARNING.value == "warning"
        assert ViolationSeverity.VIOLATION.value == "violation"
        assert ViolationSeverity.CRITICAL.value == "critical"
        assert ViolationSeverity.EMERGENCY.value == "emergency"


# =============================================================================
# TEST DATA CLASSES
# =============================================================================


class TestEthicsDataClasses:
    """Tests for ethics data classes."""

    def test_bias_indicator_creation(self):
        """Test BiasIndicator dataclass."""
        from cirkelline.ckc.mastermind.ethics import BiasIndicator, BiasType

        indicator = BiasIndicator(
            bias_type=BiasType.GENDER,
            confidence=0.7,
            evidence="Gender-specific language detected",
            source_text="He is a good programmer",
        )

        assert indicator.bias_type == BiasType.GENDER
        assert indicator.confidence == 0.7
        assert indicator.indicator_id is not None

    def test_bias_report_properties(self):
        """Test BiasReport properties."""
        from cirkelline.ckc.mastermind.ethics import BiasReport, BiasLevel, BiasIndicator

        report = BiasReport(
            overall_level=BiasLevel.MEDIUM,
            indicators=[BiasIndicator(), BiasIndicator()],
        )

        assert report.has_bias is True
        assert report.indicator_count == 2

        report_none = BiasReport(overall_level=BiasLevel.NONE)
        assert report_none.has_bias is False

    def test_decision_log_creation(self):
        """Test DecisionLog dataclass."""
        from cirkelline.ckc.mastermind.ethics import DecisionLog, DecisionType

        log = DecisionLog(
            decision_id="dec_123",
            decision_type=DecisionType.TASK_ASSIGNMENT,
            actor="agent_001",
            context={"task": "analyze"},
            input_data={"text": "sample"},
            output_data={"result": "done"},
            reasoning="Best agent available",
            confidence=0.85,
        )

        assert log.decision_id == "dec_123"
        assert log.actor == "agent_001"
        assert log.confidence == 0.85
        assert log.is_explainable is True

    def test_explanation_creation(self):
        """Test Explanation dataclass."""
        from cirkelline.ckc.mastermind.ethics import Explanation

        explanation = Explanation(
            decision_id="dec_123",
            summary="Opgaven blev tildelt baseret på tilgængelighed",
            detailed_reasoning="Agent var den eneste tilgængelige",
            factors=[{"factor": "availability", "value": True}],
            counterfactuals=["Hvis andre agenter var tilgængelige..."],
        )

        assert explanation.decision_id == "dec_123"
        assert explanation.language == "da"
        assert len(explanation.factors) == 1

    def test_guardrail_violation_creation(self):
        """Test GuardrailViolation dataclass."""
        from cirkelline.ckc.mastermind.ethics import (
            GuardrailViolation,
            GuardrailType,
            ViolationSeverity,
        )

        violation = GuardrailViolation(
            guardrail_type=GuardrailType.CONTENT_FILTER,
            severity=ViolationSeverity.WARNING,
            description="Harmful content detected",
            content_flagged="Some content",
            action_taken="Flagged for review",
            blocked=False,
        )

        assert violation.guardrail_type == GuardrailType.CONTENT_FILTER
        assert violation.blocked is False

    def test_compliance_report_properties(self):
        """Test ComplianceReport properties."""
        from cirkelline.ckc.mastermind.ethics import (
            ComplianceReport,
            ComplianceStatus,
            ComplianceStandard,
        )

        report = ComplianceReport(
            statuses=[
                ComplianceStatus(standard=ComplianceStandard.GDPR, is_compliant=True),
                ComplianceStatus(standard=ComplianceStandard.AI_ACT, is_compliant=True),
            ],
            total_decisions_logged=100,
            violations_detected=5,
            overall_score=95.0,
        )

        assert report.is_fully_compliant is True
        assert report.total_decisions_logged == 100

        report_non_compliant = ComplianceReport(
            statuses=[
                ComplianceStatus(standard=ComplianceStandard.GDPR, is_compliant=False),
            ],
        )
        assert report_non_compliant.is_fully_compliant is False


# =============================================================================
# TEST BIAS DETECTOR
# =============================================================================


class TestBiasDetector:
    """Tests for BiasDetector."""

    @pytest_asyncio.fixture
    async def detector(self):
        """Create test bias detector."""
        from cirkelline.ckc.mastermind.ethics import BiasDetector
        return BiasDetector(sensitivity=0.5)

    @pytest.mark.asyncio
    async def test_analyze_neutral_content(self, detector):
        """Test analysis of neutral content."""
        report = await detector.analyze("This is a neutral statement about technology.")

        assert report.overall_level.value == "none"
        assert len(report.indicators) == 0

    @pytest.mark.asyncio
    async def test_analyze_gender_bias(self, detector):
        """Test detection of gender bias."""
        from cirkelline.ckc.mastermind.ethics import BiasType

        report = await detector.analyze("He is always better at programming than she is.")

        # Should detect gender indicators
        assert any(i.bias_type == BiasType.GENDER for i in report.indicators)

    @pytest.mark.asyncio
    async def test_analyze_age_bias(self, detector):
        """Test detection of age bias."""
        from cirkelline.ckc.mastermind.ethics import BiasType

        detector.set_sensitivity(0.5)
        report = await detector.analyze("Young people are better at technology than elderly.")

        # Should detect age indicators
        assert any(i.bias_type == BiasType.AGE for i in report.indicators)

    @pytest.mark.asyncio
    async def test_set_sensitivity(self, detector):
        """Test sensitivity adjustment."""
        detector.set_sensitivity(0.9)
        assert detector.sensitivity == 0.9

        detector.set_sensitivity(1.5)  # Should clamp to 1.0
        assert detector.sensitivity == 1.0

        detector.set_sensitivity(-0.5)  # Should clamp to 0.0
        assert detector.sensitivity == 0.0

    @pytest.mark.asyncio
    async def test_enable_disable_bias_type(self, detector):
        """Test enabling/disabling bias types."""
        from cirkelline.ckc.mastermind.ethics import BiasType

        detector.disable_bias_type(BiasType.GENDER)
        assert BiasType.GENDER not in detector.enabled_types

        detector.enable_bias_type(BiasType.GENDER)
        assert BiasType.GENDER in detector.enabled_types


# =============================================================================
# TEST TRANSPARENCY LOGGER
# =============================================================================


class TestTransparencyLogger:
    """Tests for TransparencyLogger."""

    @pytest_asyncio.fixture
    async def logger(self):
        """Create test transparency logger."""
        from cirkelline.ckc.mastermind.ethics import TransparencyLogger
        return TransparencyLogger(retention_days=30)

    @pytest.mark.asyncio
    async def test_log_decision(self, logger):
        """Test logging a decision."""
        from cirkelline.ckc.mastermind.ethics import DecisionType

        log = await logger.log_decision(
            decision_id="dec_001",
            decision_type=DecisionType.TASK_ASSIGNMENT,
            actor="agent_001",
            context={"session_id": "sess_001"},
            input_data={"task": "analyze"},
            output_data={"status": "assigned"},
            reasoning="Best available agent",
            confidence=0.9,
            session_id="sess_001",
        )

        assert log.decision_id == "dec_001"
        assert log.actor == "agent_001"
        assert log.confidence == 0.9

    @pytest.mark.asyncio
    async def test_get_logs_by_decision(self, logger):
        """Test retrieving logs by decision ID."""
        from cirkelline.ckc.mastermind.ethics import DecisionType

        await logger.log_decision(
            decision_id="dec_002",
            decision_type=DecisionType.RESOURCE_ALLOCATION,
            actor="system",
            context={},
            input_data={},
            output_data={},
        )

        logs = await logger.get_logs_by_decision("dec_002")
        assert len(logs) == 1
        assert logs[0].decision_id == "dec_002"

    @pytest.mark.asyncio
    async def test_get_logs_by_session(self, logger):
        """Test retrieving logs by session."""
        from cirkelline.ckc.mastermind.ethics import DecisionType

        await logger.log_decision(
            decision_id="dec_003",
            decision_type=DecisionType.CONTENT_GENERATION,
            actor="agent_002",
            context={},
            input_data={},
            output_data={},
            session_id="sess_002",
        )

        logs = await logger.get_logs_by_session("sess_002")
        assert len(logs) == 1

    @pytest.mark.asyncio
    async def test_get_logs_by_actor(self, logger):
        """Test retrieving logs by actor."""
        from cirkelline.ckc.mastermind.ethics import DecisionType

        await logger.log_decision(
            decision_id="dec_004",
            decision_type=DecisionType.USER_INTERACTION,
            actor="agent_003",
            context={},
            input_data={},
            output_data={},
        )

        logs = await logger.get_logs_by_actor("agent_003")
        assert len(logs) == 1

    @pytest.mark.asyncio
    async def test_get_statistics(self, logger):
        """Test getting statistics."""
        from cirkelline.ckc.mastermind.ethics import DecisionType

        await logger.log_decision(
            decision_id="dec_005",
            decision_type=DecisionType.TASK_ASSIGNMENT,
            actor="agent_004",
            context={},
            input_data={},
            output_data={},
        )

        stats = await logger.get_statistics()
        assert stats["total_logs"] >= 1
        assert "by_decision_type" in stats


# =============================================================================
# TEST EXPLAINABILITY ENGINE
# =============================================================================


class TestExplainabilityEngine:
    """Tests for ExplainabilityEngine."""

    @pytest_asyncio.fixture
    async def engine(self):
        """Create test explainability engine."""
        from cirkelline.ckc.mastermind.ethics import (
            ExplainabilityEngine,
            TransparencyLogger,
        )
        logger = TransparencyLogger()
        return ExplainabilityEngine(transparency_logger=logger)

    @pytest.mark.asyncio
    async def test_explain_decision(self, engine):
        """Test generating explanation for a decision."""
        from cirkelline.ckc.mastermind.ethics import DecisionType

        # First log a decision
        await engine.logger.log_decision(
            decision_id="dec_explain_001",
            decision_type=DecisionType.AGENT_SELECTION,
            actor="system",
            context={"reason": "availability"},
            input_data={"agents": ["a1", "a2"]},
            output_data={"selected": "a1"},
            reasoning="Agent a1 had lowest load",
            confidence=0.85,
            alternatives=[
                {"condition": "a2 availability", "outcome": "a2 selected"}
            ],
        )

        explanation = await engine.explain_decision("dec_explain_001")

        assert explanation is not None
        assert explanation.decision_id == "dec_explain_001"
        assert explanation.summary is not None
        assert explanation.language == "da"

    @pytest.mark.asyncio
    async def test_explain_nonexistent_decision(self, engine):
        """Test explaining a decision that doesn't exist."""
        explanation = await engine.explain_decision("nonexistent_id")
        assert explanation is None

    @pytest.mark.asyncio
    async def test_explain_with_language(self, engine):
        """Test explanation with specific language."""
        from cirkelline.ckc.mastermind.ethics import DecisionType

        await engine.logger.log_decision(
            decision_id="dec_lang_001",
            decision_type=DecisionType.TASK_ASSIGNMENT,
            actor="system",
            context={},
            input_data={},
            output_data={},
            confidence=0.7,
        )

        explanation_en = await engine.explain_decision("dec_lang_001", language="en")
        assert explanation_en is not None
        assert explanation_en.language == "en"


# =============================================================================
# TEST ETHICS GUARDRAILS
# =============================================================================


class TestEthicsGuardrails:
    """Tests for EthicsGuardrails."""

    @pytest_asyncio.fixture
    async def guardrails(self):
        """Create test guardrails."""
        from cirkelline.ckc.mastermind.ethics import EthicsGuardrails
        return EthicsGuardrails()

    @pytest.mark.asyncio
    async def test_check_safe_content(self, guardrails):
        """Test checking safe content."""
        violation = await guardrails.check_content("This is a normal, safe message.")
        assert violation is None

    @pytest.mark.asyncio
    async def test_detect_harmful_content(self, guardrails):
        """Test detection of harmful content."""
        from cirkelline.ckc.mastermind.ethics import GuardrailType

        violation = await guardrails.check_content(
            "Let me hack into the system",
            guardrail_type=GuardrailType.CONTENT_FILTER,
        )

        assert violation is not None
        assert violation.guardrail_type == GuardrailType.CONTENT_FILTER

    @pytest.mark.asyncio
    async def test_detect_pii(self, guardrails):
        """Test detection of PII."""
        from cirkelline.ckc.mastermind.ethics import GuardrailType

        violation = await guardrails.check_content(
            "My CPR number is 123456-7890",
            guardrail_type=GuardrailType.PRIVACY_PROTECTION,
        )

        assert violation is not None
        assert violation.blocked is True

    @pytest.mark.asyncio
    async def test_enable_disable_guardrail(self, guardrails):
        """Test enabling/disabling guardrails."""
        from cirkelline.ckc.mastermind.ethics import GuardrailType

        await guardrails.disable_guardrail(GuardrailType.CONTENT_FILTER)

        # Content filter should now be disabled
        violation = await guardrails.check_content(
            "hack exploit attack",
            guardrail_type=GuardrailType.CONTENT_FILTER,
        )
        assert violation is None

        await guardrails.enable_guardrail(GuardrailType.CONTENT_FILTER)

    @pytest.mark.asyncio
    async def test_get_violations(self, guardrails):
        """Test getting violations."""
        # Generate a violation
        await guardrails.check_content("hack the system")

        violations = await guardrails.get_violations()
        assert len(violations) >= 1

    @pytest.mark.asyncio
    async def test_get_statistics(self, guardrails):
        """Test getting statistics."""
        await guardrails.check_content("exploit vulnerability")

        stats = await guardrails.get_statistics()
        assert "total_violations" in stats
        assert "by_type" in stats


# =============================================================================
# TEST COMPLIANCE REPORTER
# =============================================================================


class TestComplianceReporter:
    """Tests for ComplianceReporter."""

    @pytest_asyncio.fixture
    async def reporter(self):
        """Create test compliance reporter."""
        from cirkelline.ckc.mastermind.ethics import (
            ComplianceReporter,
            TransparencyLogger,
            EthicsGuardrails,
            BiasDetector,
        )
        logger = TransparencyLogger()
        guardrails = EthicsGuardrails()
        detector = BiasDetector()
        return ComplianceReporter(
            transparency_logger=logger,
            guardrails=guardrails,
            bias_detector=detector,
        )

    @pytest.mark.asyncio
    async def test_check_gdpr_compliance(self, reporter):
        """Test GDPR compliance check."""
        from cirkelline.ckc.mastermind.ethics import ComplianceStandard

        status = await reporter.check_compliance(ComplianceStandard.GDPR)

        assert status.standard == ComplianceStandard.GDPR
        assert isinstance(status.score, float)

    @pytest.mark.asyncio
    async def test_check_ai_act_compliance(self, reporter):
        """Test AI Act compliance check."""
        from cirkelline.ckc.mastermind.ethics import ComplianceStandard

        status = await reporter.check_compliance(ComplianceStandard.AI_ACT)

        assert status.standard == ComplianceStandard.AI_ACT

    @pytest.mark.asyncio
    async def test_generate_report(self, reporter):
        """Test report generation."""
        report = await reporter.generate_report(period_days=30)

        assert report.report_id is not None
        assert report.period_end >= report.period_start
        assert len(report.statuses) > 0

    @pytest.mark.asyncio
    async def test_export_report_json(self, reporter):
        """Test exporting report to JSON."""
        report = await reporter.generate_report()
        json_output = await reporter.export_report(report, format="json")

        assert isinstance(json_output, str)
        assert "report_id" in json_output
        assert "overall_score" in json_output


# =============================================================================
# TEST FACTORY FUNCTIONS
# =============================================================================


class TestEthicsFactoryFunctions:
    """Tests for factory functions."""

    def test_create_bias_detector(self):
        """Test creating bias detector."""
        from cirkelline.ckc.mastermind.ethics import create_bias_detector, get_bias_detector

        detector = create_bias_detector(sensitivity=0.7)
        assert detector is not None
        assert detector.sensitivity == 0.7

        retrieved = get_bias_detector()
        assert retrieved is detector

    def test_create_transparency_logger(self):
        """Test creating transparency logger."""
        from cirkelline.ckc.mastermind.ethics import (
            create_transparency_logger,
            get_transparency_logger,
        )

        logger = create_transparency_logger(retention_days=60)
        assert logger is not None
        assert logger.retention_days == 60

        retrieved = get_transparency_logger()
        assert retrieved is logger

    def test_create_explainability_engine(self):
        """Test creating explainability engine."""
        from cirkelline.ckc.mastermind.ethics import (
            create_explainability_engine,
            get_explainability_engine,
        )

        engine = create_explainability_engine()
        assert engine is not None

        retrieved = get_explainability_engine()
        assert retrieved is engine

    def test_create_ethics_guardrails(self):
        """Test creating ethics guardrails."""
        from cirkelline.ckc.mastermind.ethics import (
            create_ethics_guardrails,
            get_ethics_guardrails,
        )

        guardrails = create_ethics_guardrails()
        assert guardrails is not None

        retrieved = get_ethics_guardrails()
        assert retrieved is guardrails

    def test_create_compliance_reporter(self):
        """Test creating compliance reporter."""
        from cirkelline.ckc.mastermind.ethics import (
            create_compliance_reporter,
            get_compliance_reporter,
        )

        reporter = create_compliance_reporter()
        assert reporter is not None

        retrieved = get_compliance_reporter()
        assert retrieved is reporter


# =============================================================================
# TEST MODULE IMPORTS
# =============================================================================


class TestEthicsModuleImports:
    """Tests for module imports."""

    def test_import_all_enums(self):
        """Test importing all enums."""
        from cirkelline.ckc.mastermind.ethics import (
            BiasType,
            BiasLevel,
            DecisionType,
            ComplianceStandard,
            GuardrailType,
            ViolationSeverity,
        )

        assert BiasType is not None
        assert BiasLevel is not None
        assert DecisionType is not None
        assert ComplianceStandard is not None
        assert GuardrailType is not None
        assert ViolationSeverity is not None

    def test_import_all_dataclasses(self):
        """Test importing all dataclasses."""
        from cirkelline.ckc.mastermind.ethics import (
            BiasIndicator,
            BiasReport,
            DecisionLog,
            Explanation,
            GuardrailViolation,
            ComplianceStatus,
            ComplianceReport,
        )

        assert BiasIndicator is not None
        assert BiasReport is not None
        assert DecisionLog is not None
        assert Explanation is not None
        assert GuardrailViolation is not None
        assert ComplianceStatus is not None
        assert ComplianceReport is not None

    def test_import_all_classes(self):
        """Test importing all main classes."""
        from cirkelline.ckc.mastermind.ethics import (
            BiasDetector,
            TransparencyLogger,
            ExplainabilityEngine,
            EthicsGuardrails,
            ComplianceReporter,
        )

        assert BiasDetector is not None
        assert TransparencyLogger is not None
        assert ExplainabilityEngine is not None
        assert EthicsGuardrails is not None
        assert ComplianceReporter is not None

    def test_all_exports(self):
        """Test that __all__ exports are complete."""
        from cirkelline.ckc.mastermind import ethics

        # Check that key items are in __all__
        expected = [
            "BiasType", "BiasLevel", "BiasDetector",
            "TransparencyLogger", "ExplainabilityEngine",
            "EthicsGuardrails", "ComplianceReporter",
        ]

        for item in expected:
            assert item in ethics.__all__
