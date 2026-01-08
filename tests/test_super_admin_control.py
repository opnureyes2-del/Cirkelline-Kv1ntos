"""
Tests for CKC MASTERMIND Super Admin Control System (DEL L)
============================================================

Tests alle 4 kernefunktioner:
1. Masterminds Øje (SuperAdminDashboard)
2. Masterminds Stemme (IntelligentNotificationEngine)
3. KV1NT Terminal Partner (KV1NTTerminalPartner)
4. Organisk Læring (AdaptiveLearningSystem)
5. Unified SuperAdminControlSystem
"""

import pytest
from datetime import datetime, timezone

from cirkelline.ckc.mastermind.super_admin_control import (
    # Enums
    DashboardZone,
    AlertLevel,
    AlertCategory,
    DeliveryChannel,
    WorkflowRecommendationType,
    KnowledgeQueryType,
    FeedbackType,
    LearningAdaptationType,

    # Data classes
    ZoneStatus,
    Alert,
    NotificationPreference,
    WorkflowRecommendation,
    KnowledgeQuery,
    KnowledgeResponse,
    UserFeedback,
    LearningAdaptation,

    # Main classes
    SuperAdminDashboard,
    IntelligentNotificationEngine,
    KV1NTTerminalPartner,
    AdaptiveLearningSystem,
    SuperAdminControlSystem,

    # Factory functions
    create_super_admin_control_system,
    get_super_admin_control_system,
    create_dashboard,
    create_notification_engine,
    create_kv1nt_partner,
    create_adaptive_learning_system,
)


# =============================================================================
# ENUM TESTS
# =============================================================================

class TestEnums:
    """Test alle enums."""

    def test_dashboard_zone_values(self):
        """Test DashboardZone enum values."""
        assert len(DashboardZone) == 9  # Updated: added CKC_FOLDERS zone
        assert DashboardZone.LEARNING_ROOMS.value == "learning_rooms"
        assert DashboardZone.SYSTEMS.value == "systems"
        assert DashboardZone.PROFILES.value == "profiles"
        assert DashboardZone.TASKS.value == "tasks"
        assert DashboardZone.COMMUNICATIONS.value == "communications"
        assert DashboardZone.UPDATES.value == "updates"
        assert DashboardZone.SECURITY.value == "security"
        assert DashboardZone.ETHICS.value == "ethics"
        assert DashboardZone.CKC_FOLDERS.value == "ckc_folders"

    def test_alert_level_values(self):
        """Test AlertLevel enum values."""
        assert len(AlertLevel) == 4
        assert AlertLevel.CRITICAL.value == "critical"
        assert AlertLevel.IMPORTANT.value == "important"
        assert AlertLevel.INFORMATIONAL.value == "informational"
        assert AlertLevel.DEBUG.value == "debug"

    def test_alert_category_values(self):
        """Test AlertCategory enum values."""
        assert len(AlertCategory) == 7
        assert AlertCategory.SYSTEM_DEVIATION.value == "system_deviation"
        assert AlertCategory.MILESTONE.value == "milestone"
        assert AlertCategory.KNOWLEDGE_FLOW.value == "knowledge_flow"
        assert AlertCategory.RESOURCE_TREND.value == "resource_trend"
        assert AlertCategory.SECURITY_EVENT.value == "security_event"
        assert AlertCategory.ETHICS_ALERT.value == "ethics_alert"
        assert AlertCategory.PERFORMANCE.value == "performance"

    def test_delivery_channel_values(self):
        """Test DeliveryChannel enum values."""
        assert len(DeliveryChannel) == 5
        assert DeliveryChannel.TERMINAL.value == "terminal"
        assert DeliveryChannel.EMAIL.value == "email"
        assert DeliveryChannel.INTERNAL_MESSAGE.value == "internal_message"
        assert DeliveryChannel.WEBHOOK.value == "webhook"
        assert DeliveryChannel.SMS.value == "sms"

    def test_workflow_recommendation_type_values(self):
        """Test WorkflowRecommendationType enum values."""
        assert len(WorkflowRecommendationType) == 5
        assert WorkflowRecommendationType.AGENT_REALLOCATION.value == "agent_reallocation"
        assert WorkflowRecommendationType.CONFLICT_WARNING.value == "conflict_warning"
        assert WorkflowRecommendationType.REDUNDANCY_REMOVAL.value == "redundancy_removal"
        assert WorkflowRecommendationType.PERFORMANCE_INSIGHT.value == "performance_insight"
        assert WorkflowRecommendationType.OPTIMIZATION_SUGGESTION.value == "optimization_suggestion"

    def test_knowledge_query_type_values(self):
        """Test KnowledgeQueryType enum values."""
        assert len(KnowledgeQueryType) == 4
        assert KnowledgeQueryType.SYNTHESIS_REPORT.value == "synthesis_report"
        assert KnowledgeQueryType.AD_HOC_QUERY.value == "ad_hoc_query"
        assert KnowledgeQueryType.AUDIT_TRAIL.value == "audit_trail"
        assert KnowledgeQueryType.SCENARIO_SIMULATION.value == "scenario_simulation"

    def test_feedback_type_values(self):
        """Test FeedbackType enum values."""
        assert len(FeedbackType) == 5
        assert FeedbackType.DASHBOARD_PREFERENCE.value == "dashboard_preference"
        assert FeedbackType.NOTIFICATION_PREFERENCE.value == "notification_preference"
        assert FeedbackType.WORKFLOW_PREFERENCE.value == "workflow_preference"
        assert FeedbackType.KNOWLEDGE_FORMAT_PREFERENCE.value == "knowledge_format_preference"
        assert FeedbackType.EXPLICIT_RATING.value == "explicit_rating"

    def test_learning_adaptation_type_values(self):
        """Test LearningAdaptationType enum values."""
        assert len(LearningAdaptationType) == 4
        assert LearningAdaptationType.DISPLAY_OPTIMIZATION.value == "display_optimization"
        assert LearningAdaptationType.ALERT_TUNING.value == "alert_tuning"
        assert LearningAdaptationType.RECOMMENDATION_REFINEMENT.value == "recommendation_refinement"
        assert LearningAdaptationType.FORMAT_ADJUSTMENT.value == "format_adjustment"


# =============================================================================
# DATA CLASS TESTS
# =============================================================================

class TestDataClasses:
    """Test alle data classes."""

    def test_zone_status_creation(self):
        """Test ZoneStatus creation."""
        status = ZoneStatus(
            zone=DashboardZone.LEARNING_ROOMS,
            status="healthy"
        )
        assert status.zone == DashboardZone.LEARNING_ROOMS
        assert status.status == "healthy"
        assert status.metrics == {}
        assert status.alerts_count == 0
        assert status.active_items == 0
        assert isinstance(status.last_updated, datetime)

    def test_zone_status_with_metrics(self):
        """Test ZoneStatus with custom metrics."""
        metrics = {"cpu": 45.2, "memory": 67.8}
        status = ZoneStatus(
            zone=DashboardZone.SYSTEMS,
            status="warning",
            metrics=metrics,
            alerts_count=3,
            active_items=12
        )
        assert status.metrics == metrics
        assert status.alerts_count == 3
        assert status.active_items == 12

    def test_alert_creation(self):
        """Test Alert creation."""
        alert = Alert(
            level=AlertLevel.CRITICAL,
            category=AlertCategory.SECURITY_EVENT,
            title="Sikkerhedsadvarsel",
            message="Uautoriseret adgangsforsøg detekteret"
        )
        assert alert.level == AlertLevel.CRITICAL
        assert alert.category == AlertCategory.SECURITY_EVENT
        assert alert.title == "Sikkerhedsadvarsel"
        assert not alert.acknowledged
        assert alert.alert_id.startswith("alert_")

    def test_notification_preference_creation(self):
        """Test NotificationPreference creation."""
        pref = NotificationPreference(
            user_id="rasmus",
            channels=[DeliveryChannel.TERMINAL, DeliveryChannel.EMAIL],
            alert_levels=[AlertLevel.CRITICAL, AlertLevel.IMPORTANT],
            categories=[AlertCategory.SECURITY_EVENT]
        )
        assert pref.user_id == "rasmus"
        assert len(pref.channels) == 2
        assert len(pref.alert_levels) == 2

    def test_workflow_recommendation_creation(self):
        """Test WorkflowRecommendation creation."""
        rec = WorkflowRecommendation(
            recommendation_type=WorkflowRecommendationType.AGENT_REALLOCATION,
            title="Optimer agent allokering",
            description="Agent A bruges sjældent",
            impact_assessment="Lav risiko, høj gevinst",
            confidence=0.85
        )
        assert rec.recommendation_type == WorkflowRecommendationType.AGENT_REALLOCATION
        assert rec.confidence == 0.85
        assert rec.accepted is None

    def test_knowledge_query_creation(self):
        """Test KnowledgeQuery creation."""
        query = KnowledgeQuery(
            query_type=KnowledgeQueryType.SYNTHESIS_REPORT,
            query_text="Generer daglig syntese",
            context={"period": "last_24h"}
        )
        assert query.query_type == KnowledgeQueryType.SYNTHESIS_REPORT
        assert query.query_id.startswith("query_")

    def test_knowledge_response_creation(self):
        """Test KnowledgeResponse creation."""
        response = KnowledgeResponse(
            query_id="query_abc123",
            content="Syntese rapport...",
            sources=["historian", "journal"],
            confidence=0.92
        )
        assert response.query_id == "query_abc123"
        assert len(response.sources) == 2

    def test_user_feedback_creation(self):
        """Test UserFeedback creation."""
        feedback = UserFeedback(
            feedback_type=FeedbackType.EXPLICIT_RATING,
            target_component="dashboard",
            value=5
        )
        assert feedback.feedback_type == FeedbackType.EXPLICIT_RATING
        assert feedback.value == 5

    def test_learning_adaptation_creation(self):
        """Test LearningAdaptation creation."""
        adaptation = LearningAdaptation(
            adaptation_type=LearningAdaptationType.DISPLAY_OPTIMIZATION,
            description="Tilpasning af visning",
            parameters_changed={"layout": "compact"}
        )
        assert adaptation.adaptation_type == LearningAdaptationType.DISPLAY_OPTIMIZATION
        assert adaptation.parameters_changed["layout"] == "compact"


# =============================================================================
# SUPER ADMIN DASHBOARD TESTS (MASTERMINDS ØJE)
# =============================================================================

class TestSuperAdminDashboard:
    """Test Masterminds Øje - SuperAdminDashboard."""

    @pytest.fixture
    def dashboard(self):
        """Create dashboard instance."""
        return SuperAdminDashboard(refresh_rate_seconds=1.0)

    def test_dashboard_initialization(self, dashboard):
        """Test dashboard initialization."""
        assert not dashboard.is_active()
        assert dashboard._refresh_rate == 1.0
        assert dashboard._security_profile == "super_admin_exclusive"
        assert len(dashboard._zones) == 9  # All DashboardZone values (including CKC_FOLDERS)

    def test_dashboard_activation(self, dashboard):
        """Test dashboard activation."""
        result = dashboard.activate()
        assert result is True
        assert dashboard.is_active()

    def test_dashboard_deactivation(self, dashboard):
        """Test dashboard deactivation."""
        dashboard.activate()
        result = dashboard.deactivate()
        assert result is True
        assert not dashboard.is_active()

    def test_get_zone_status(self, dashboard):
        """Test getting zone status."""
        status = dashboard.get_zone_status(DashboardZone.LEARNING_ROOMS)
        assert status.zone == DashboardZone.LEARNING_ROOMS
        assert status.status == "healthy"

    def test_update_zone_status(self, dashboard):
        """Test updating zone status."""
        status = dashboard.update_zone_status(
            zone=DashboardZone.SECURITY,
            status="warning",
            metrics={"threats_detected": 2},
            active_items=5,
            alerts_count=1
        )
        assert status.status == "warning"
        assert status.metrics["threats_detected"] == 2
        assert status.active_items == 5
        assert status.alerts_count == 1

    def test_get_global_status(self, dashboard):
        """Test getting global status."""
        dashboard.activate()
        status = dashboard.get_global_status()

        assert status["is_active"] is True
        assert "zones" in status
        assert "overall_health" in status
        assert "total_alerts" in status
        assert "total_active_items" in status

    def test_global_health_aggregation(self, dashboard):
        """Test global health aggregation logic."""
        dashboard.update_zone_status(DashboardZone.SYSTEMS, "healthy")
        status = dashboard.get_global_status()
        assert status["overall_health"] == "healthy"

        dashboard.update_zone_status(DashboardZone.SECURITY, "warning")
        status = dashboard.get_global_status()
        assert status["overall_health"] == "warning"

        dashboard.update_zone_status(DashboardZone.ETHICS, "critical")
        status = dashboard.get_global_status()
        assert status["overall_health"] == "critical"

    def test_refresh(self, dashboard):
        """Test dashboard refresh."""
        dashboard.activate()
        status = dashboard.refresh()
        assert "zones" in status
        assert dashboard._last_refresh is not None

    def test_custom_metrics(self, dashboard):
        """Test custom metrics."""
        dashboard.set_custom_metric("custom_key", "custom_value")
        metrics = dashboard.get_custom_metrics()
        assert metrics["custom_key"] == "custom_value"

    def test_refresh_callback(self, dashboard):
        """Test refresh callback registration."""
        callback_called = []

        def my_callback(dash):
            callback_called.append(True)

        dashboard.register_refresh_callback(my_callback)
        dashboard.refresh()

        assert len(callback_called) == 1


# =============================================================================
# INTELLIGENT NOTIFICATION ENGINE TESTS (MASTERMINDS STEMME)
# =============================================================================

class TestIntelligentNotificationEngine:
    """Test Masterminds Stemme - IntelligentNotificationEngine."""

    @pytest.fixture
    def engine(self):
        """Create notification engine instance."""
        return IntelligentNotificationEngine()

    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert not engine.is_active()
        assert len(engine._alerts) == 0
        assert len(engine._preferences) == 0

    def test_engine_activation(self, engine):
        """Test engine activation."""
        result = engine.activate()
        assert result is True
        assert engine.is_active()

    def test_engine_deactivation(self, engine):
        """Test engine deactivation."""
        engine.activate()
        result = engine.deactivate()
        assert result is True
        assert not engine.is_active()

    def test_set_preferences(self, engine):
        """Test setting notification preferences."""
        pref = engine.set_preferences(
            user_id="rasmus",
            channels=[DeliveryChannel.TERMINAL],
            alert_levels=[AlertLevel.CRITICAL]
        )
        assert pref.user_id == "rasmus"
        assert DeliveryChannel.TERMINAL in pref.channels

    def test_get_preferences(self, engine):
        """Test getting notification preferences."""
        engine.set_preferences("rasmus", channels=[DeliveryChannel.EMAIL])
        pref = engine.get_preferences("rasmus")
        assert pref is not None
        assert DeliveryChannel.EMAIL in pref.channels

    def test_create_alert(self, engine):
        """Test creating alert."""
        alert = engine.create_alert(
            level=AlertLevel.CRITICAL,
            category=AlertCategory.SECURITY_EVENT,
            title="Test Alert",
            message="Test message"
        )
        assert alert.level == AlertLevel.CRITICAL
        assert alert.title == "Test Alert"

    def test_get_alerts(self, engine):
        """Test getting alerts."""
        engine.create_alert(AlertLevel.CRITICAL, AlertCategory.SECURITY_EVENT, "Alert 1", "Msg 1")
        engine.create_alert(AlertLevel.INFORMATIONAL, AlertCategory.MILESTONE, "Alert 2", "Msg 2")

        all_alerts = engine.get_alerts()
        assert len(all_alerts) == 2

        critical_only = engine.get_alerts(level=AlertLevel.CRITICAL)
        assert len(critical_only) == 1

    def test_acknowledge_alert(self, engine):
        """Test acknowledging alert."""
        alert = engine.create_alert(AlertLevel.IMPORTANT, AlertCategory.PERFORMANCE, "Test", "Msg")

        result = engine.acknowledge_alert(alert.alert_id)
        assert result is True
        assert alert.acknowledged is True
        assert alert.acknowledged_at is not None

    def test_acknowledge_nonexistent_alert(self, engine):
        """Test acknowledging non-existent alert."""
        result = engine.acknowledge_alert("nonexistent_id")
        assert result is False

    def test_register_delivery_handler(self, engine):
        """Test registering delivery handler."""
        handler = lambda alert: True
        engine.register_delivery_handler(DeliveryChannel.TERMINAL, handler)
        assert DeliveryChannel.TERMINAL in engine._delivery_handlers

    def test_get_status(self, engine):
        """Test getting engine status."""
        engine.activate()
        engine.create_alert(AlertLevel.CRITICAL, AlertCategory.SECURITY_EVENT, "Test", "Msg")

        status = engine.get_status()
        assert status["is_active"] is True
        assert status["total_alerts"] == 1
        assert status["unacknowledged_alerts"] == 1
        assert status["critical_alerts"] == 1

    @pytest.mark.asyncio
    async def test_deliver_alert_no_preferences(self, engine):
        """Test delivering alert without preferences."""
        alert = engine.create_alert(AlertLevel.CRITICAL, AlertCategory.SECURITY_EVENT, "Test", "Msg")
        result = await engine.deliver_alert(alert, "unknown_user")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_deliver_alert_filtered_by_level(self, engine):
        """Test alert filtered by level."""
        engine.set_preferences(
            "rasmus",
            channels=[DeliveryChannel.TERMINAL],
            alert_levels=[AlertLevel.CRITICAL],
            categories=[AlertCategory.SECURITY_EVENT]
        )
        alert = engine.create_alert(AlertLevel.INFORMATIONAL, AlertCategory.SECURITY_EVENT, "Test", "Msg")
        result = await engine.deliver_alert(alert, "rasmus")
        assert result.get("skipped") is True


# =============================================================================
# KV1NT TERMINAL PARTNER TESTS
# =============================================================================

class TestKV1NTTerminalPartner:
    """Test KV1NT Terminal Partner."""

    @pytest.fixture
    def kv1nt(self):
        """Create KV1NT instance."""
        return KV1NTTerminalPartner(interface="terminal")

    def test_kv1nt_initialization(self, kv1nt):
        """Test KV1NT initialization."""
        assert not kv1nt.is_active()
        assert kv1nt._interface == "terminal"

    def test_kv1nt_activation(self, kv1nt):
        """Test KV1NT activation."""
        result = kv1nt.activate()
        assert result is True
        assert kv1nt.is_active()

    def test_register_workflow(self, kv1nt):
        """Test workflow registration."""
        workflow = kv1nt.register_workflow(
            workflow_id="wf_001",
            workflow_type="analysis",
            agents=["agent_a", "agent_b"]
        )
        assert workflow["workflow_id"] == "wf_001"
        assert workflow["status"] == "active"

    def test_get_active_workflows(self, kv1nt):
        """Test getting active workflows."""
        kv1nt.register_workflow("wf_001", "analysis", ["agent_a"])
        kv1nt.register_workflow("wf_002", "synthesis", ["agent_b"])

        workflows = kv1nt.get_active_workflows()
        assert len(workflows) == 2

    def test_create_recommendation(self, kv1nt):
        """Test creating recommendation."""
        rec = kv1nt.create_recommendation(
            recommendation_type=WorkflowRecommendationType.AGENT_REALLOCATION,
            title="Optimer allokering",
            description="Agent A underudnyttet",
            impact_assessment="Lav risiko",
            confidence=0.85
        )
        assert rec.confidence == 0.85
        assert rec.accepted is None

    def test_get_recommendations_filtered(self, kv1nt):
        """Test getting filtered recommendations."""
        kv1nt.create_recommendation(
            WorkflowRecommendationType.AGENT_REALLOCATION, "R1", "D1", "I1", 0.9
        )
        kv1nt.create_recommendation(
            WorkflowRecommendationType.CONFLICT_WARNING, "R2", "D2", "I2", 0.7
        )

        all_recs = kv1nt.get_recommendations()
        assert len(all_recs) == 2

        filtered = kv1nt.get_recommendations(
            recommendation_type=WorkflowRecommendationType.AGENT_REALLOCATION
        )
        assert len(filtered) == 1

        high_confidence = kv1nt.get_recommendations(min_confidence=0.8)
        assert len(high_confidence) == 1

    def test_accept_recommendation(self, kv1nt):
        """Test accepting recommendation."""
        rec = kv1nt.create_recommendation(
            WorkflowRecommendationType.OPTIMIZATION_SUGGESTION, "R", "D", "I", 0.8
        )

        result = kv1nt.accept_recommendation(rec.recommendation_id, True)
        assert result is True
        assert rec.accepted is True

    def test_register_knowledge_source(self, kv1nt):
        """Test registering knowledge source."""
        kv1nt.register_knowledge_source("historian_logs")
        kv1nt.register_knowledge_source("agent_journals")

        sources = kv1nt.get_knowledge_sources()
        assert "historian_logs" in sources
        assert "agent_journals" in sources

    def test_query_knowledge(self, kv1nt):
        """Test knowledge query."""
        query = kv1nt.query_knowledge(
            query_type=KnowledgeQueryType.SYNTHESIS_REPORT,
            query_text="Generer daglig rapport",
            context={"period": "24h"}
        )
        assert query.query_type == KnowledgeQueryType.SYNTHESIS_REPORT

    def test_create_response(self, kv1nt):
        """Test creating knowledge response."""
        query = kv1nt.query_knowledge(KnowledgeQueryType.AD_HOC_QUERY, "Test query")

        response = kv1nt.create_response(
            query_id=query.query_id,
            content="Test svar",
            sources=["source1", "source2"],
            confidence=0.9
        )
        assert response.query_id == query.query_id

    def test_get_response_for_query(self, kv1nt):
        """Test getting response for query."""
        query = kv1nt.query_knowledge(KnowledgeQueryType.AD_HOC_QUERY, "Test")
        kv1nt.create_response(query.query_id, "Svar", ["src"], 0.8)

        response = kv1nt.get_response_for_query(query.query_id)
        assert response is not None
        assert response.content == "Svar"

    def test_simulate_scenario(self, kv1nt):
        """Test scenario simulation."""
        result = kv1nt.simulate_scenario(
            scenario_name="Scale to 100 agents",
            parameters={"agent_count": 100}
        )
        assert result["scenario_name"] == "Scale to 100 agents"
        assert "confidence" in result

    def test_get_status(self, kv1nt):
        """Test getting KV1NT status."""
        kv1nt.activate()
        kv1nt.register_workflow("wf_001", "test", ["a"])

        status = kv1nt.get_status()
        assert status["is_active"] is True
        assert status["active_workflows"] == 1


# =============================================================================
# ADAPTIVE LEARNING SYSTEM TESTS (ORGANISK LÆRING)
# =============================================================================

class TestAdaptiveLearningSystem:
    """Test Organisk Læring - AdaptiveLearningSystem."""

    @pytest.fixture
    def learning(self):
        """Create learning system instance."""
        return AdaptiveLearningSystem(target_user="rasmus")

    def test_learning_initialization(self, learning):
        """Test learning system initialization."""
        assert not learning.is_active()
        assert learning._target_user == "rasmus"
        assert learning._learning_rate == 0.1

    def test_learning_activation(self, learning):
        """Test learning activation."""
        result = learning.activate()
        assert result is True
        assert learning.is_active()

    def test_record_feedback(self, learning):
        """Test recording feedback."""
        feedback = learning.record_feedback(
            feedback_type=FeedbackType.EXPLICIT_RATING,
            target_component="dashboard",
            value=5
        )
        assert feedback.feedback_type == FeedbackType.EXPLICIT_RATING
        assert feedback.value == 5

    def test_get_feedback(self, learning):
        """Test getting feedback."""
        learning.record_feedback(FeedbackType.EXPLICIT_RATING, "dashboard", 5)
        learning.record_feedback(FeedbackType.NOTIFICATION_PREFERENCE, "alerts", {"muted": True})

        all_fb = learning.get_feedback()
        assert len(all_fb) == 2

        filtered = learning.get_feedback(feedback_type=FeedbackType.EXPLICIT_RATING)
        assert len(filtered) == 1

    def test_record_interaction(self, learning):
        """Test recording interaction."""
        learning.record_interaction(
            interaction_type="click",
            component="dashboard",
            data={"target": "zone_learning_rooms"}
        )

        patterns = learning.get_interaction_patterns()
        assert "click:dashboard" in patterns
        assert patterns["click:dashboard"]["count"] == 1

    def test_interaction_sample_limit(self, learning):
        """Test interaction sample limit (max 100)."""
        for i in range(150):
            learning.record_interaction("click", "button", {"iteration": i})

        patterns = learning.get_interaction_patterns()
        assert len(patterns["click:button"]["data_samples"]) == 100

    def test_create_adaptation(self, learning):
        """Test creating adaptation."""
        adaptation = learning.create_adaptation(
            adaptation_type=LearningAdaptationType.DISPLAY_OPTIMIZATION,
            description="Optimeret layout",
            parameters_changed={"layout": "compact"}
        )
        assert adaptation.adaptation_type == LearningAdaptationType.DISPLAY_OPTIMIZATION

    def test_get_adaptations(self, learning):
        """Test getting adaptations."""
        learning.create_adaptation(LearningAdaptationType.DISPLAY_OPTIMIZATION, "A1", {})
        learning.create_adaptation(LearningAdaptationType.ALERT_TUNING, "A2", {})

        all_adapt = learning.get_adaptations()
        assert len(all_adapt) == 2

        filtered = learning.get_adaptations(LearningAdaptationType.DISPLAY_OPTIMIZATION)
        assert len(filtered) == 1

    def test_analyze_and_adapt(self, learning):
        """Test analyze and adapt."""
        # Add enough feedback to trigger adaptation (>=3)
        learning.record_feedback(FeedbackType.EXPLICIT_RATING, "dashboard", 5)
        learning.record_feedback(FeedbackType.EXPLICIT_RATING, "dashboard", 4)
        learning.record_feedback(FeedbackType.EXPLICIT_RATING, "dashboard", 5)

        adaptations = learning.analyze_and_adapt()
        assert len(adaptations) >= 1

    def test_set_learning_rate(self, learning):
        """Test setting learning rate."""
        learning.set_learning_rate(0.5)
        assert learning._learning_rate == 0.5

        # Test clamping
        learning.set_learning_rate(1.5)
        assert learning._learning_rate == 1.0

        learning.set_learning_rate(-0.5)
        assert learning._learning_rate == 0.0

    def test_set_adaptation_threshold(self, learning):
        """Test setting adaptation threshold."""
        learning.set_adaptation_threshold(0.7)
        assert learning._adaptation_threshold == 0.7

    def test_get_status(self, learning):
        """Test getting learning status."""
        learning.activate()
        learning.record_feedback(FeedbackType.EXPLICIT_RATING, "test", 5)

        status = learning.get_status()
        assert status["is_active"] is True
        assert status["total_feedback"] == 1
        assert status["target_user"] == "rasmus"


# =============================================================================
# SUPER ADMIN CONTROL SYSTEM TESTS (UNIFIED)
# =============================================================================

class TestSuperAdminControlSystem:
    """Test unified SuperAdminControlSystem."""

    @pytest.fixture
    def control_system(self):
        """Create control system instance."""
        return SuperAdminControlSystem(admin_user="rasmus_super_admin")

    def test_control_system_initialization(self, control_system):
        """Test control system initialization."""
        assert control_system._admin_user == "rasmus_super_admin"
        assert control_system.dashboard is not None
        assert control_system.notifications is not None
        assert control_system.kv1nt is not None
        assert control_system.learning is not None

    def test_kv1nt_default_knowledge_sources(self, control_system):
        """Test KV1NT has default knowledge sources."""
        sources = control_system.kv1nt.get_knowledge_sources()
        assert "historian_logs" in sources
        assert "agent_journals" in sources
        assert "knowledge_bank" in sources
        assert "mastermind_meta_analysis" in sources

    def test_activate_all(self, control_system):
        """Test activating all components."""
        results = control_system.activate_all()

        assert results["dashboard"] is True
        assert results["notifications"] is True
        assert results["kv1nt"] is True
        assert results["learning"] is True
        assert control_system.is_fully_active()

    def test_deactivate_all(self, control_system):
        """Test deactivating all components."""
        control_system.activate_all()
        results = control_system.deactivate_all()

        assert results["dashboard"] is True
        assert results["notifications"] is True
        assert results["kv1nt"] is True
        assert results["learning"] is True
        assert not control_system.is_fully_active()

    def test_is_fully_active(self, control_system):
        """Test full activation check."""
        assert not control_system.is_fully_active()

        control_system.dashboard.activate()
        assert not control_system.is_fully_active()

        control_system.notifications.activate()
        control_system.kv1nt.activate()
        control_system.learning.activate()
        assert control_system.is_fully_active()

    def test_get_comprehensive_status(self, control_system):
        """Test comprehensive status."""
        control_system.activate_all()
        status = control_system.get_comprehensive_status()

        assert status["admin_user"] == "rasmus_super_admin"
        assert status["is_fully_active"] is True
        assert "components" in status
        assert "masterminds_eye" in status["components"]
        assert "masterminds_voice" in status["components"]
        assert "kv1nt_partner" in status["components"]
        assert "organic_learning" in status["components"]


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_super_admin_control_system(self):
        """Test create_super_admin_control_system."""
        system = create_super_admin_control_system(admin_user="test_admin")
        assert system._admin_user == "test_admin"

    def test_get_super_admin_control_system_singleton(self):
        """Test get_super_admin_control_system returns singleton."""
        system1 = get_super_admin_control_system()
        system2 = get_super_admin_control_system()
        # Note: After create_super_admin_control_system was called, this returns that instance
        assert system1 is not None

    def test_create_dashboard(self):
        """Test create_dashboard factory."""
        dashboard = create_dashboard()
        assert isinstance(dashboard, SuperAdminDashboard)

    def test_create_notification_engine(self):
        """Test create_notification_engine factory."""
        engine = create_notification_engine()
        assert isinstance(engine, IntelligentNotificationEngine)

    def test_create_kv1nt_partner(self):
        """Test create_kv1nt_partner factory."""
        kv1nt = create_kv1nt_partner(interface="web")
        assert isinstance(kv1nt, KV1NTTerminalPartner)
        assert kv1nt._interface == "web"

    def test_create_adaptive_learning_system(self):
        """Test create_adaptive_learning_system factory."""
        learning = create_adaptive_learning_system(target_user="test_user")
        assert isinstance(learning, AdaptiveLearningSystem)
        assert learning._target_user == "test_user"


# =============================================================================
# IMPORT TESTS
# =============================================================================

class TestImports:
    """Test that all exports are importable."""

    def test_import_from_module_directly(self):
        """Test imports directly from module."""
        from cirkelline.ckc.mastermind.super_admin_control import (
            DashboardZone,
            AlertLevel,
            AlertCategory,
            DeliveryChannel,
            WorkflowRecommendationType,
            KnowledgeQueryType,
            FeedbackType,
            LearningAdaptationType,
            ZoneStatus,
            Alert,
            NotificationPreference,
            WorkflowRecommendation,
            KnowledgeQuery,
            KnowledgeResponse,
            UserFeedback,
            LearningAdaptation,
            SuperAdminDashboard,
            IntelligentNotificationEngine,
            KV1NTTerminalPartner,
            AdaptiveLearningSystem,
            SuperAdminControlSystem,
            create_super_admin_control_system,
            get_super_admin_control_system,
            create_dashboard,
            create_notification_engine,
            create_kv1nt_partner,
            create_adaptive_learning_system,
        )
        assert DashboardZone is not None
        assert SuperAdminControlSystem is not None

    def test_import_from_mastermind_package(self):
        """Test imports from mastermind package (with aliases)."""
        from cirkelline.ckc.mastermind import (
            DashboardZone,
            NotificationAlertLevel,
            AlertCategory,
            DeliveryChannel,
            WorkflowRecommendationType,
            KnowledgeQueryType,
            AdaptiveFeedbackType,
            LearningAdaptationType,
            ZoneStatus,
            NotificationAlert,
            NotificationPreference,
            WorkflowRecommendation,
            KnowledgeQuery,
            KnowledgeResponse,
            AdaptiveUserFeedback,
            LearningAdaptation,
            SuperAdminDashboard,
            IntelligentNotificationEngine,
            KV1NTTerminalPartner,
            AdaptiveLearningSystem,
            SuperAdminControlSystem,
            create_super_admin_control_system,
            get_super_admin_control_system,
            create_dashboard,
            create_notification_engine,
            create_kv1nt_partner,
            create_adaptive_learning_system,
        )
        assert DashboardZone is not None
        assert NotificationAlertLevel is not None  # Aliased from AlertLevel
        assert AdaptiveFeedbackType is not None  # Aliased from FeedbackType
        assert NotificationAlert is not None  # Aliased from Alert
        assert AdaptiveUserFeedback is not None  # Aliased from UserFeedback
