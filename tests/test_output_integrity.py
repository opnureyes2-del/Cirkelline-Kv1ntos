"""
CKC Output Integrity Protocol Tests
====================================

Komplet test suite for Output Integrity modulet:
- Output Validation Gateway (OVG)
- Mastermind Audit System (MAS)
- Quarantine Mechanism (QM)
- Super Admin Notification (SAN)
- OutputIntegritySystem (Master Controller)
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from cirkelline.ckc.mastermind.output_integrity import (
    # Enums
    ValidationRuleType,
    ValidationResult,
    AuditDecision,
    QuarantineReason,
    QuarantineStatus,
    NotificationType,
    NotificationPriority,
    NotificationChannel,

    # Data classes
    ValidationRule,
    ValidationReport,
    AuditReport,
    QuarantineItem,
    Notification,
    NotificationPreferences,

    # Classes
    OutputValidationGateway,
    MastermindAuditSystem,
    QuarantineMechanism,
    SuperAdminNotification,
    OutputIntegritySystem,

    # Factory functions
    create_output_validation_gateway,
    create_mastermind_audit_system,
    create_quarantine_mechanism,
    create_super_admin_notification,
    create_output_integrity_system,
    get_output_integrity_system,
)


# =============================================================================
# TEST ENUMS
# =============================================================================

class TestValidationEnums:
    """Tests for validation-related enums."""

    def test_validation_rule_type_values(self):
        """Test all ValidationRuleType enum values exist."""
        assert ValidationRuleType.CONTEXTUAL_RELEVANCE
        assert ValidationRuleType.ETHICAL_COMPLIANCE
        assert ValidationRuleType.SECURITY_STANDARDS
        assert ValidationRuleType.FORMAT_INTEGRITY
        assert ValidationRuleType.METADATA_VERIFICATION
        assert ValidationRuleType.CONTENT_QUALITY
        assert ValidationRuleType.BIAS_DETECTION
        assert ValidationRuleType.SENSITIVE_DATA

    def test_validation_result_values(self):
        """Test all ValidationResult enum values exist."""
        assert ValidationResult.PASSED
        assert ValidationResult.FAILED
        assert ValidationResult.WARNING
        assert ValidationResult.REQUIRES_REVIEW

    def test_audit_decision_values(self):
        """Test all AuditDecision enum values exist."""
        assert AuditDecision.APPROVED
        assert AuditDecision.REJECTED
        assert AuditDecision.REQUIRES_MODIFICATION
        assert AuditDecision.REQUIRES_SUPER_ADMIN
        assert AuditDecision.PENDING_REVIEW

    def test_quarantine_reason_values(self):
        """Test all QuarantineReason enum values exist."""
        assert QuarantineReason.OVG_VALIDATION_FAILURE
        assert QuarantineReason.MAS_REJECTION
        assert QuarantineReason.SECURITY_CONCERN
        assert QuarantineReason.ETHICAL_VIOLATION
        assert QuarantineReason.POLICY_BREACH
        assert QuarantineReason.MANUAL_QUARANTINE
        assert QuarantineReason.SUSPICIOUS_CONTENT

    def test_quarantine_status_values(self):
        """Test all QuarantineStatus enum values exist."""
        assert QuarantineStatus.ACTIVE
        assert QuarantineStatus.RELEASED
        assert QuarantineStatus.DELETED
        assert QuarantineStatus.EXPIRED
        assert QuarantineStatus.UNDER_REVIEW

    def test_notification_type_values(self):
        """Test all NotificationType enum values exist."""
        assert NotificationType.QUARANTINE_ALERT
        assert NotificationType.MAS_REJECTION
        assert NotificationType.OVG_CRITICAL_FAILURE
        assert NotificationType.SYSTEM_INTEGRITY_ALERT
        assert NotificationType.POLICY_VIOLATION
        assert NotificationType.SECURITY_BREACH
        assert NotificationType.AUDIT_SUMMARY

    def test_notification_priority_values(self):
        """Test all NotificationPriority enum values exist."""
        assert NotificationPriority.CRITICAL
        assert NotificationPriority.HIGH
        assert NotificationPriority.MEDIUM
        assert NotificationPriority.LOW
        assert NotificationPriority.AGGREGATE

    def test_notification_channel_values(self):
        """Test all NotificationChannel enum values exist."""
        assert NotificationChannel.EMAIL
        assert NotificationChannel.DASHBOARD
        assert NotificationChannel.MOBILE_PUSH
        assert NotificationChannel.SMS
        assert NotificationChannel.INTERNAL_LOG


# =============================================================================
# TEST DATA CLASSES
# =============================================================================

class TestDataClasses:
    """Tests for data classes."""

    def test_validation_rule_creation(self):
        """Test ValidationRule dataclass creation."""
        rule = ValidationRule(
            rule_id="test_001",
            rule_type=ValidationRuleType.SECURITY_STANDARDS,
            name="Test Rule",
            description="A test rule",
            is_blocking=True,
            severity=8
        )
        assert rule.rule_id == "test_001"
        assert rule.rule_type == ValidationRuleType.SECURITY_STANDARDS
        assert rule.is_blocking is True
        assert rule.severity == 8
        assert rule.enabled is True  # Default

    def test_validation_report_creation(self):
        """Test ValidationReport dataclass creation."""
        report = ValidationReport(
            output_id="out_123",
            requesting_agent="test_agent",
            intended_destination="external_api"
        )
        assert report.output_id == "out_123"
        assert report.requesting_agent == "test_agent"
        assert report.overall_result == ValidationResult.PASSED  # Default
        assert isinstance(report.rule_results, dict)
        assert isinstance(report.failed_rules, list)

    def test_audit_report_creation(self):
        """Test AuditReport dataclass creation."""
        report = AuditReport()
        assert report.audit_id is not None
        assert report.decision == AuditDecision.PENDING_REVIEW
        assert report.risk_score == 0.0
        assert isinstance(report.policy_checks, dict)

    def test_quarantine_item_creation(self):
        """Test QuarantineItem dataclass creation."""
        item = QuarantineItem(
            output_content={"test": "data"},
            reason=QuarantineReason.SECURITY_CONCERN,
            requesting_agent="agent_1"
        )
        assert item.item_id is not None
        assert item.output_content == {"test": "data"}
        assert item.reason == QuarantineReason.SECURITY_CONCERN
        assert item.status == QuarantineStatus.ACTIVE

    def test_notification_creation(self):
        """Test Notification dataclass creation."""
        notification = Notification(
            notification_type=NotificationType.QUARANTINE_ALERT,
            priority=NotificationPriority.HIGH,
            title="Test Alert",
            message="Test message"
        )
        assert notification.notification_id is not None
        assert notification.priority == NotificationPriority.HIGH
        assert notification.is_read is False
        assert notification.is_acknowledged is False

    def test_notification_preferences_defaults(self):
        """Test NotificationPreferences default values."""
        prefs = NotificationPreferences()
        assert prefs.user_id == "super_admin"
        assert NotificationChannel.DASHBOARD in prefs.enabled_channels
        assert NotificationChannel.EMAIL in prefs.enabled_channels
        assert prefs.critical_only_mobile is True


# =============================================================================
# TEST OUTPUT VALIDATION GATEWAY (OVG)
# =============================================================================

class TestOutputValidationGateway:
    """Tests for Output Validation Gateway."""

    @pytest.fixture
    def ovg(self):
        """Create fresh OVG instance."""
        return OutputValidationGateway()

    def test_ovg_initialization(self, ovg):
        """Test OVG initializes with default rules."""
        assert len(ovg._rules) >= 7
        assert "ethical_001" in ovg._rules
        assert "security_001" in ovg._rules
        assert "bias_001" in ovg._rules

    def test_add_custom_rule(self, ovg):
        """Test adding a custom validation rule."""
        rule = ValidationRule(
            rule_id="custom_001",
            rule_type=ValidationRuleType.CONTENT_QUALITY,
            name="Custom Quality Check",
            description="Custom quality validation"
        )
        ovg.add_rule(rule)
        assert "custom_001" in ovg._rules

    def test_remove_rule(self, ovg):
        """Test removing a validation rule."""
        result = ovg.remove_rule("format_001")
        assert result is True
        assert "format_001" not in ovg._rules

    def test_remove_nonexistent_rule(self, ovg):
        """Test removing a non-existent rule returns False."""
        result = ovg.remove_rule("nonexistent_999")
        assert result is False

    def test_enable_disable_rule(self, ovg):
        """Test enabling and disabling rules."""
        ovg.disable_rule("format_001")
        assert ovg._rules["format_001"].enabled is False

        ovg.enable_rule("format_001")
        assert ovg._rules["format_001"].enabled is True

    @pytest.mark.asyncio
    async def test_validate_clean_output(self, ovg):
        """Test validation of clean, safe output."""
        report = await ovg.validate_output(
            output="This is a valid, safe output.",
            requesting_agent="test_agent",
            intended_destination="user_interface",
            context={"metadata": {"source": "test", "timestamp": "now", "agent_id": "a1"}}
        )
        # PASSED or WARNING are both acceptable (warnings from optional checks)
        assert report.overall_result in [ValidationResult.PASSED, ValidationResult.WARNING]
        assert len(report.failed_rules) == 0

    @pytest.mark.asyncio
    async def test_validate_security_violation(self, ovg):
        """Test validation catches security violations."""
        report = await ovg.validate_output(
            output="password=secret123 api_key=abc",
            requesting_agent="test_agent",
            intended_destination="external"
        )
        assert report.overall_result == ValidationResult.FAILED
        assert "security_001" in report.failed_rules

    @pytest.mark.asyncio
    async def test_validate_sensitive_data_cpr(self, ovg):
        """Test validation catches Danish CPR numbers."""
        report = await ovg.validate_output(
            output="Brugerens CPR er 010190-1234",
            requesting_agent="test_agent",
            intended_destination="external"
        )
        assert report.overall_result == ValidationResult.FAILED
        assert "sensitive_001" in report.failed_rules

    @pytest.mark.asyncio
    async def test_validate_with_context(self, ovg):
        """Test validation with context information."""
        report = await ovg.validate_output(
            output={"key": "value"},
            requesting_agent="test_agent",
            intended_destination="api",
            context={
                "expected_format": "json",
                "metadata": {"source": "test", "timestamp": "now", "agent_id": "a1"}
            }
        )
        assert report.overall_result == ValidationResult.PASSED

    def test_get_rule_statistics(self, ovg):
        """Test getting rule statistics."""
        stats = ovg.get_rule_statistics()
        assert "total_rules" in stats
        assert "enabled_rules" in stats
        assert "total_validations" in stats
        assert stats["total_rules"] >= 7


# =============================================================================
# TEST MASTERMIND AUDIT SYSTEM (MAS)
# =============================================================================

class TestMastermindAuditSystem:
    """Tests for Mastermind Audit System."""

    @pytest.fixture
    def mas(self):
        """Create fresh MAS instance."""
        return MastermindAuditSystem()

    def test_mas_initialization(self, mas):
        """Test MAS initializes with policies."""
        assert len(mas._policies) >= 5
        assert "master_command_compliance" in mas._policies
        assert "ethical_guidelines" in mas._policies
        assert "security_policy" in mas._policies

    def test_risk_thresholds(self, mas):
        """Test default risk thresholds."""
        assert mas._risk_thresholds["auto_approve"] == 0.2
        assert mas._risk_thresholds["requires_review"] == 0.5
        assert mas._risk_thresholds["auto_reject"] == 0.8

    def test_update_risk_thresholds(self, mas):
        """Test updating risk thresholds."""
        mas.update_risk_thresholds(auto_approve=0.3, auto_reject=0.9)
        assert mas._risk_thresholds["auto_approve"] == 0.3
        assert mas._risk_thresholds["auto_reject"] == 0.9

    @pytest.mark.asyncio
    async def test_audit_passed_validation(self, mas):
        """Test auditing a passed validation report."""
        validation_report = ValidationReport(
            output_id="out_123",
            requesting_agent="test_agent",
            intended_destination="user",
            overall_result=ValidationResult.PASSED,
            rule_results={
                "ethical_001": ValidationResult.PASSED,
                "security_001": ValidationResult.PASSED,
                "sensitive_001": ValidationResult.PASSED,
            }
        )

        audit_report = await mas.audit_output(validation_report)
        assert audit_report.decision == AuditDecision.APPROVED
        assert audit_report.risk_score < 0.5

    @pytest.mark.asyncio
    async def test_audit_failed_validation(self, mas):
        """Test auditing a failed validation report."""
        validation_report = ValidationReport(
            output_id="out_456",
            requesting_agent="test_agent",
            intended_destination="external",
            overall_result=ValidationResult.FAILED,
            failed_rules=["security_001", "sensitive_001"],
            rule_results={
                "ethical_001": ValidationResult.PASSED,
                "security_001": ValidationResult.FAILED,
                "sensitive_001": ValidationResult.FAILED,
            }
        )

        audit_report = await mas.audit_output(validation_report)
        assert audit_report.decision in [AuditDecision.REJECTED, AuditDecision.REQUIRES_MODIFICATION]
        assert audit_report.risk_score > 0.3

    @pytest.mark.asyncio
    async def test_audit_warning_validation(self, mas):
        """Test auditing a warning validation report."""
        validation_report = ValidationReport(
            output_id="out_789",
            requesting_agent="test_agent",
            intended_destination="user",
            overall_result=ValidationResult.WARNING,
            warnings=["Minor issue detected"],
            rule_results={
                "ethical_001": ValidationResult.PASSED,
                "format_001": ValidationResult.WARNING,
            }
        )

        audit_report = await mas.audit_output(validation_report)
        # With low risk score, warnings should still be approved
        assert audit_report.decision in [AuditDecision.APPROVED, AuditDecision.REQUIRES_SUPER_ADMIN]

    def test_get_audit_statistics(self, mas):
        """Test getting audit statistics."""
        stats = mas.get_audit_statistics()
        assert "total_audits" in stats
        assert "decisions" in stats
        assert "average_risk_score" in stats
        assert "learning_samples" in stats


# =============================================================================
# TEST QUARANTINE MECHANISM (QM)
# =============================================================================

class TestQuarantineMechanism:
    """Tests for Quarantine Mechanism."""

    @pytest.fixture
    def qm(self):
        """Create fresh QM instance."""
        return QuarantineMechanism(retention_days=90)

    @pytest.mark.asyncio
    async def test_add_to_quarantine(self, qm):
        """Test adding item to quarantine."""
        item = await qm.add_to_quarantine(
            output={"sensitive": "data"},
            reason=QuarantineReason.SECURITY_CONCERN,
            requesting_agent="test_agent",
            intended_destination="external"
        )

        assert item.item_id is not None
        assert item.status == QuarantineStatus.ACTIVE
        assert item.reason == QuarantineReason.SECURITY_CONCERN
        assert item.expires_at is not None

    @pytest.mark.asyncio
    async def test_get_item(self, qm):
        """Test retrieving quarantine item."""
        item = await qm.add_to_quarantine(
            output="test content",
            reason=QuarantineReason.OVG_VALIDATION_FAILURE
        )

        retrieved = await qm.get_item(item.item_id)
        assert retrieved is not None
        assert retrieved.item_id == item.item_id

    @pytest.mark.asyncio
    async def test_release_item_authorized(self, qm):
        """Test releasing item with authorized accessor."""
        item = await qm.add_to_quarantine(
            output="test content",
            reason=QuarantineReason.MANUAL_QUARANTINE
        )

        result = await qm.release_item(
            item_id=item.item_id,
            accessor="super_admin",
            notes="Reviewed and approved"
        )

        assert result is True
        released_item = await qm.get_item(item.item_id)
        assert released_item.status == QuarantineStatus.RELEASED

    @pytest.mark.asyncio
    async def test_release_item_unauthorized(self, qm):
        """Test releasing item fails with unauthorized accessor."""
        item = await qm.add_to_quarantine(
            output="test content",
            reason=QuarantineReason.MANUAL_QUARANTINE
        )

        result = await qm.release_item(
            item_id=item.item_id,
            accessor="random_agent",
            notes="Attempting unauthorized release"
        )

        assert result is False
        still_quarantined = await qm.get_item(item.item_id)
        assert still_quarantined.status == QuarantineStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_delete_item(self, qm):
        """Test deleting quarantine item."""
        item = await qm.add_to_quarantine(
            output="test content",
            reason=QuarantineReason.SUSPICIOUS_CONTENT
        )

        result = await qm.delete_item(
            item_id=item.item_id,
            accessor="super_admin",
            notes="Permanently deleted"
        )

        assert result is True
        deleted = await qm.get_item(item.item_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_add_review_note(self, qm):
        """Test adding review notes to quarantine item."""
        item = await qm.add_to_quarantine(
            output="test content",
            reason=QuarantineReason.ETHICAL_VIOLATION
        )

        result = await qm.add_review_note(
            item_id=item.item_id,
            accessor="reviewer",
            note="Initial review - needs more analysis"
        )

        assert result is True
        reviewed = await qm.get_item(item.item_id)
        assert reviewed.status == QuarantineStatus.UNDER_REVIEW
        assert len(reviewed.review_notes) == 1

    def test_get_active_items(self, qm):
        """Test getting list of active quarantine items."""
        active = qm.get_active_items()
        assert isinstance(active, list)

    def test_get_statistics(self, qm):
        """Test getting quarantine statistics."""
        stats = qm.get_statistics()
        assert "total_items" in stats
        assert "active_items" in stats
        assert "status_distribution" in stats
        assert "reason_distribution" in stats


# =============================================================================
# TEST SUPER ADMIN NOTIFICATION (SAN)
# =============================================================================

class TestSuperAdminNotification:
    """Tests for Super Admin Notification system."""

    @pytest.fixture
    def san(self):
        """Create fresh SAN instance."""
        return SuperAdminNotification()

    def test_san_initialization(self, san):
        """Test SAN initializes with default handlers."""
        assert len(san._notification_handlers) >= 5
        assert NotificationChannel.EMAIL in san._notification_handlers
        assert NotificationChannel.DASHBOARD in san._notification_handlers

    @pytest.mark.asyncio
    async def test_send_notification(self, san):
        """Test sending a notification."""
        notification = await san.send_notification(
            notification_type=NotificationType.QUARANTINE_ALERT,
            title="Test Alert",
            message="This is a test notification",
            priority=NotificationPriority.HIGH
        )

        assert notification.notification_id is not None
        assert notification.title == "Test Alert"
        assert notification.priority == NotificationPriority.HIGH

    @pytest.mark.asyncio
    async def test_send_critical_notification(self, san):
        """Test sending critical notification."""
        notification = await san.send_notification(
            notification_type=NotificationType.SECURITY_BREACH,
            title="Security Alert",
            message="Critical security issue detected",
            priority=NotificationPriority.CRITICAL
        )

        assert notification.priority == NotificationPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_mark_as_read(self, san):
        """Test marking notification as read."""
        notification = await san.send_notification(
            notification_type=NotificationType.AUDIT_SUMMARY,
            title="Daily Summary",
            message="Summary content",
            priority=NotificationPriority.LOW
        )

        result = await san.mark_as_read(notification.notification_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_acknowledge_notification(self, san):
        """Test acknowledging notification."""
        notification = await san.send_notification(
            notification_type=NotificationType.POLICY_VIOLATION,
            title="Policy Alert",
            message="Policy violation detected",
            priority=NotificationPriority.MEDIUM
        )

        result = await san.acknowledge(notification.notification_id)
        assert result is True

    def test_get_unread_notifications(self, san):
        """Test getting unread notifications."""
        unread = san.get_unread_notifications()
        assert isinstance(unread, list)

    def test_set_preferences(self, san):
        """Test setting notification preferences."""
        new_prefs = NotificationPreferences(
            user_id="admin",
            email="admin@test.com",
            enabled_channels={NotificationChannel.EMAIL, NotificationChannel.SMS},
            quiet_hours_start=22,
            quiet_hours_end=7
        )

        san.set_preferences(new_prefs)
        current = san.get_preferences()
        assert current.email == "admin@test.com"
        assert NotificationChannel.SMS in current.enabled_channels

    def test_enable_disable_channel(self, san):
        """Test enabling and disabling notification channels."""
        san.disable_channel(NotificationChannel.MOBILE_PUSH)
        assert NotificationChannel.MOBILE_PUSH not in san._preferences.enabled_channels

        san.enable_channel(NotificationChannel.MOBILE_PUSH)
        assert NotificationChannel.MOBILE_PUSH in san._preferences.enabled_channels

    def test_get_statistics(self, san):
        """Test getting notification statistics."""
        stats = san.get_statistics()
        assert "total_notifications" in stats
        assert "unread" in stats
        assert "pending_aggregation" in stats
        assert "type_distribution" in stats
        assert "priority_distribution" in stats


# =============================================================================
# TEST OUTPUT INTEGRITY SYSTEM (MASTER CONTROLLER)
# =============================================================================

class TestOutputIntegritySystem:
    """Tests for the integrated Output Integrity System."""

    @pytest.fixture
    def ois(self):
        """Create fresh OIS instance."""
        return OutputIntegritySystem(retention_days=30)

    def test_ois_initialization(self, ois):
        """Test OIS initializes all components."""
        assert ois.ovg is not None
        assert ois.mas is not None
        assert ois.qm is not None
        assert ois.san is not None

    @pytest.mark.asyncio
    async def test_process_safe_output(self, ois):
        """Test processing safe, valid output."""
        result = await ois.process_output(
            output="This is a safe, normal output message.",
            requesting_agent="test_agent",
            intended_destination="user_interface"
        )

        assert result["approved"] is True
        assert result["validation_report"] is not None
        assert result["audit_report"] is not None
        assert result["quarantine_item"] is None

    @pytest.mark.asyncio
    async def test_process_unsafe_output(self, ois):
        """Test processing unsafe output with security issues."""
        result = await ois.process_output(
            output="password=secret123 DROP TABLE users;",
            requesting_agent="test_agent",
            intended_destination="external_api"
        )

        assert result["approved"] is False
        assert result["quarantine_item"] is not None
        assert len(result["notifications_sent"]) > 0

    @pytest.mark.asyncio
    async def test_process_sensitive_data_output(self, ois):
        """Test processing output with sensitive personal data."""
        result = await ois.process_output(
            output="CPR nummer: 010190-1234, password=abc",
            requesting_agent="data_agent",
            intended_destination="report"
        )

        assert result["approved"] is False
        assert result["quarantine_item"] is not None

    @pytest.mark.asyncio
    async def test_super_admin_approve(self, ois):
        """Test Super Admin approval of quarantined item."""
        # First quarantine something
        result = await ois.process_output(
            output="api_key=test123",
            requesting_agent="test_agent",
            intended_destination="external"
        )

        if result["quarantine_item"]:
            item_id = result["quarantine_item"].item_id
            approved = await ois.super_admin_approve(item_id, "Manually reviewed and approved")
            assert approved is True

    @pytest.mark.asyncio
    async def test_super_admin_reject(self, ois):
        """Test Super Admin rejection of quarantined item."""
        # First quarantine something
        result = await ois.process_output(
            output="token=secret_token",
            requesting_agent="test_agent",
            intended_destination="external"
        )

        if result["quarantine_item"]:
            item_id = result["quarantine_item"].item_id
            rejected = await ois.super_admin_reject(item_id, "Confirmed as malicious")
            assert rejected is True

    def test_get_system_status(self, ois):
        """Test getting full system status."""
        status = ois.get_system_status()
        assert "ovg_stats" in status
        assert "mas_stats" in status
        assert "qm_stats" in status
        assert "san_stats" in status

    @pytest.mark.asyncio
    async def test_cleanup(self, ois):
        """Test system cleanup."""
        cleanup_result = await ois.cleanup()
        assert "expired_quarantine_items" in cleanup_result
        assert "aggregated_notifications" in cleanup_result


# =============================================================================
# TEST FACTORY FUNCTIONS
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_output_validation_gateway(self):
        """Test OVG factory function."""
        ovg = create_output_validation_gateway()
        assert isinstance(ovg, OutputValidationGateway)

    def test_create_mastermind_audit_system(self):
        """Test MAS factory function."""
        mas = create_mastermind_audit_system()
        assert isinstance(mas, MastermindAuditSystem)

    def test_create_quarantine_mechanism(self):
        """Test QM factory function."""
        qm = create_quarantine_mechanism(retention_days=60)
        assert isinstance(qm, QuarantineMechanism)
        assert qm._retention_days == 60

    def test_create_super_admin_notification(self):
        """Test SAN factory function."""
        san = create_super_admin_notification()
        assert isinstance(san, SuperAdminNotification)

    def test_create_output_integrity_system(self):
        """Test OIS factory function."""
        ois = create_output_integrity_system(retention_days=45)
        assert isinstance(ois, OutputIntegritySystem)

    def test_get_output_integrity_system_singleton(self):
        """Test singleton instance of OIS."""
        ois1 = get_output_integrity_system()
        ois2 = get_output_integrity_system()
        assert ois1 is ois2


# =============================================================================
# TEST IMPORTS
# =============================================================================

class TestImports:
    """Tests for module imports."""

    def test_import_from_mastermind_package(self):
        """Test importing from mastermind package."""
        from cirkelline.ckc.mastermind import (
            ValidationRuleType,
            ValidationResult,
            AuditDecision,
            QuarantineReason,
            QuarantineStatus,
            OutputNotificationType,
            OutputNotificationPriority,
            NotificationChannel,
            ValidationRule,
            ValidationReport,
            AuditReport,
            QuarantineItem,
            OutputNotification,
            OutputNotificationPreferences,
            OutputValidationGateway,
            MastermindAuditSystem,
            QuarantineMechanism,
            SuperAdminNotification,
            OutputIntegritySystem,
            create_output_validation_gateway,
            create_mastermind_audit_system,
            create_quarantine_mechanism,
            create_super_admin_notification,
            create_output_integrity_system,
            get_output_integrity_system,
        )
        assert ValidationRuleType is not None
        assert OutputIntegritySystem is not None

    def test_all_exports_in_package(self):
        """Test all exports are listed in __all__."""
        from cirkelline.ckc import mastermind

        expected_exports = [
            "ValidationRuleType",
            "ValidationResult",
            "AuditDecision",
            "QuarantineReason",
            "QuarantineStatus",
            "OutputNotificationType",
            "OutputNotificationPriority",
            "NotificationChannel",
            "OutputValidationGateway",
            "MastermindAuditSystem",
            "QuarantineMechanism",
            "SuperAdminNotification",
            "OutputIntegritySystem",
        ]

        for export in expected_exports:
            assert export in mastermind.__all__, f"{export} not in __all__"


# =============================================================================
# TEST CONCURRENT OPERATIONS
# =============================================================================

class TestConcurrentOperations:
    """Tests for concurrent operations and thread safety."""

    @pytest.mark.asyncio
    async def test_concurrent_validations(self):
        """Test multiple concurrent validations."""
        ovg = OutputValidationGateway()

        async def validate_one(i):
            return await ovg.validate_output(
                output=f"Output number {i}",
                requesting_agent=f"agent_{i}",
                intended_destination="user"
            )

        tasks = [validate_one(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for report in results:
            # PASSED or WARNING are acceptable (no failures)
            assert report.overall_result in [ValidationResult.PASSED, ValidationResult.WARNING]
            assert len(report.failed_rules) == 0

    @pytest.mark.asyncio
    async def test_concurrent_quarantine_operations(self):
        """Test multiple concurrent quarantine operations."""
        qm = QuarantineMechanism()

        async def quarantine_one(i):
            return await qm.add_to_quarantine(
                output=f"Content {i}",
                reason=QuarantineReason.MANUAL_QUARANTINE,
                requesting_agent=f"agent_{i}"
            )

        tasks = [quarantine_one(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for item in results:
            assert item.status == QuarantineStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_concurrent_notifications(self):
        """Test multiple concurrent notifications."""
        san = SuperAdminNotification()

        async def send_one(i):
            return await san.send_notification(
                notification_type=NotificationType.AUDIT_SUMMARY,
                title=f"Notification {i}",
                message=f"Message {i}",
                priority=NotificationPriority.LOW
            )

        tasks = [send_one(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for notification in results:
            assert notification.notification_id is not None


# =============================================================================
# TEST EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_validate_empty_output(self):
        """Test validation of empty output."""
        ovg = OutputValidationGateway()
        report = await ovg.validate_output(
            output="",
            requesting_agent="test",
            intended_destination="user"
        )
        # Empty output may trigger quality check
        assert report is not None

    @pytest.mark.asyncio
    async def test_validate_none_output(self):
        """Test validation of None output."""
        ovg = OutputValidationGateway()
        report = await ovg.validate_output(
            output=None,
            requesting_agent="test",
            intended_destination="user"
        )
        assert report is not None

    @pytest.mark.asyncio
    async def test_quarantine_nonexistent_item(self):
        """Test operations on non-existent quarantine item."""
        qm = QuarantineMechanism()
        item = await qm.get_item("nonexistent_id")
        assert item is None

        result = await qm.release_item("nonexistent_id", "super_admin")
        assert result is False

    @pytest.mark.asyncio
    async def test_notification_mark_nonexistent(self):
        """Test marking non-existent notification."""
        san = SuperAdminNotification()
        result = await san.mark_as_read("nonexistent_notification")
        assert result is False

    @pytest.mark.asyncio
    async def test_large_output_validation(self):
        """Test validation of large output."""
        ovg = OutputValidationGateway()
        large_output = "x" * 100000  # 100KB of text
        report = await ovg.validate_output(
            output=large_output,
            requesting_agent="test",
            intended_destination="user",
            context={"metadata": {"source": "test", "timestamp": "now", "agent_id": "a1"}}
        )
        # PASSED or WARNING are acceptable (no blocking failures)
        assert report.overall_result in [ValidationResult.PASSED, ValidationResult.WARNING]
        assert len(report.failed_rules) == 0
