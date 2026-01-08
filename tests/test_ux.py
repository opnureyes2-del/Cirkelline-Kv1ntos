"""
Tests for DEL H: Brugercentrisk Udvikling & UX
==============================================

Tests for:
- UserFeedbackCollector
- AdaptiveUI
- AccessibilityChecker
- OnboardingWizard
- PreferenceManager
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from cirkelline.ckc.mastermind.ux import (
    # Enums
    FeedbackType,
    FeedbackSentiment,
    UITheme,
    AccessibilityLevel,
    OnboardingStep,
    PreferenceCategory,
    # Data classes
    UserFeedback,
    FeedbackAnalysis,
    UIAdaptation,
    AccessibilityIssue,
    AccessibilityReport,
    OnboardingProgress,
    UserPreference,
    PreferenceProfile,
    # Classes
    UserFeedbackCollector,
    AdaptiveUI,
    AccessibilityChecker,
    OnboardingWizard,
    PreferenceManager,
    # Factory functions
    create_feedback_collector,
    get_feedback_collector,
    create_adaptive_ui,
    get_adaptive_ui,
    create_accessibility_checker,
    get_accessibility_checker,
    create_onboarding_wizard,
    get_onboarding_wizard,
    create_preference_manager,
    get_preference_manager,
)


# =============================================================================
# TEST ENUMS
# =============================================================================

class TestUXEnums:
    """Tests for UX enums."""

    def test_feedback_type_values(self):
        """Test FeedbackType enum values."""
        assert FeedbackType.BUG_REPORT.value == "bug_report"
        assert FeedbackType.FEATURE_REQUEST.value == "feature_request"
        assert FeedbackType.USABILITY_ISSUE.value == "usability_issue"
        assert len(FeedbackType) == 7

    def test_feedback_sentiment_values(self):
        """Test FeedbackSentiment enum values."""
        assert FeedbackSentiment.POSITIVE.value == "positive"
        assert FeedbackSentiment.NEGATIVE.value == "negative"
        assert FeedbackSentiment.NEUTRAL.value == "neutral"
        assert FeedbackSentiment.MIXED.value == "mixed"

    def test_ui_theme_values(self):
        """Test UITheme enum values."""
        assert UITheme.LIGHT.value == "light"
        assert UITheme.DARK.value == "dark"
        assert UITheme.SYSTEM.value == "system"
        assert UITheme.HIGH_CONTRAST.value == "high_contrast"

    def test_accessibility_level_values(self):
        """Test AccessibilityLevel enum values."""
        assert AccessibilityLevel.A.value == "A"
        assert AccessibilityLevel.AA.value == "AA"
        assert AccessibilityLevel.AAA.value == "AAA"

    def test_onboarding_step_values(self):
        """Test OnboardingStep enum values."""
        assert OnboardingStep.WELCOME.value == "welcome"
        assert OnboardingStep.COMPLETION.value == "completion"
        assert len(OnboardingStep) == 6

    def test_preference_category_values(self):
        """Test PreferenceCategory enum values."""
        assert PreferenceCategory.APPEARANCE.value == "appearance"
        assert PreferenceCategory.NOTIFICATIONS.value == "notifications"
        assert len(PreferenceCategory) == 6


# =============================================================================
# TEST DATA CLASSES
# =============================================================================

class TestUXDataClasses:
    """Tests for UX data classes."""

    def test_user_feedback_creation(self):
        """Test UserFeedback creation."""
        feedback = UserFeedback(
            feedback_id="fb_123",
            user_id="user_456",
            feedback_type=FeedbackType.BUG_REPORT,
            content="Der er en fejl i login",
            sentiment=FeedbackSentiment.NEGATIVE,
            rating=2
        )

        assert feedback.feedback_id == "fb_123"
        assert feedback.user_id == "user_456"
        assert feedback.feedback_type == FeedbackType.BUG_REPORT
        assert feedback.rating == 2
        assert not feedback.resolved

    def test_user_feedback_rating_validation(self):
        """Test UserFeedback rating validation."""
        with pytest.raises(ValueError):
            UserFeedback(
                feedback_id="fb_123",
                user_id="user_456",
                feedback_type=FeedbackType.GENERAL_FEEDBACK,
                content="Test",
                sentiment=FeedbackSentiment.NEUTRAL,
                rating=6  # Invalid - over 5
            )

    def test_accessibility_report_properties(self):
        """Test AccessibilityReport properties."""
        issue = AccessibilityIssue(
            issue_id="a11y_123",
            component="button",
            wcag_criterion="1.4.3",
            level=AccessibilityLevel.AA,
            description="Lav kontrast",
            impact="Svært at læse",
            recommendation="Øg kontrast"
        )

        report = AccessibilityReport(
            report_id="report_123",
            checked_at=datetime.now(timezone.utc),
            total_components=10,
            issues=[issue],
            compliance_level=AccessibilityLevel.A,
            score=80.0
        )

        assert not report.is_compliant
        assert report.issues_by_level["AA"] == 1
        assert report.issues_by_level["A"] == 0

    def test_onboarding_progress_properties(self):
        """Test OnboardingProgress properties."""
        progress = OnboardingProgress(
            user_id="user_123",
            current_step=OnboardingStep.TUTORIAL,
            completed_steps=[OnboardingStep.WELCOME, OnboardingStep.PROFILE_SETUP]
        )

        assert not progress.is_completed
        assert progress.progress_percent == pytest.approx(33.33, rel=0.1)

    def test_preference_profile_creation(self):
        """Test PreferenceProfile creation."""
        profile = PreferenceProfile(
            user_id="user_123",
            preferences={},
            theme=UITheme.DARK,
            language="en"
        )

        assert profile.user_id == "user_123"
        assert profile.theme == UITheme.DARK
        assert profile.language == "en"


# =============================================================================
# TEST USER FEEDBACK COLLECTOR
# =============================================================================

class TestUserFeedbackCollector:
    """Tests for UserFeedbackCollector class."""

    @pytest_asyncio.fixture
    async def collector(self):
        """Create feedback collector fixture."""
        return create_feedback_collector()

    @pytest.mark.asyncio
    async def test_submit_feedback(self, collector):
        """Test submitting feedback."""
        feedback = await collector.submit_feedback(
            user_id="user_123",
            feedback_type=FeedbackType.FEATURE_REQUEST,
            content="Jeg vil gerne have dark mode",
            rating=4
        )

        assert feedback.feedback_id.startswith("fb_")
        assert feedback.user_id == "user_123"
        assert feedback.rating == 4

    @pytest.mark.asyncio
    async def test_sentiment_analysis_positive(self, collector):
        """Test positive sentiment analysis."""
        feedback = await collector.submit_feedback(
            user_id="user_123",
            feedback_type=FeedbackType.PRAISE,
            content="Fantastisk produkt! Jeg elsker det!"
        )

        assert feedback.sentiment == FeedbackSentiment.POSITIVE

    @pytest.mark.asyncio
    async def test_sentiment_analysis_negative(self, collector):
        """Test negative sentiment analysis."""
        feedback = await collector.submit_feedback(
            user_id="user_123",
            feedback_type=FeedbackType.COMPLAINT,
            content="Der er en fejl og problemet er irriterende"
        )

        assert feedback.sentiment == FeedbackSentiment.NEGATIVE

    @pytest.mark.asyncio
    async def test_get_user_feedback(self, collector):
        """Test getting user feedback."""
        await collector.submit_feedback("user_123", FeedbackType.BUG_REPORT, "Bug 1")
        await collector.submit_feedback("user_123", FeedbackType.BUG_REPORT, "Bug 2")
        await collector.submit_feedback("user_456", FeedbackType.BUG_REPORT, "Bug 3")

        user_feedback = await collector.get_user_feedback("user_123")
        assert len(user_feedback) == 2

    @pytest.mark.asyncio
    async def test_resolve_feedback(self, collector):
        """Test resolving feedback."""
        feedback = await collector.submit_feedback(
            user_id="user_123",
            feedback_type=FeedbackType.BUG_REPORT,
            content="Login fejl"
        )

        resolved = await collector.resolve_feedback(
            feedback.feedback_id,
            "Fikset i version 2.0"
        )

        assert resolved.resolved
        assert resolved.resolution_notes == "Fikset i version 2.0"

    @pytest.mark.asyncio
    async def test_analyze_feedback(self, collector):
        """Test feedback analysis."""
        await collector.submit_feedback("user_1", FeedbackType.BUG_REPORT, "Bug", rating=2)
        await collector.submit_feedback("user_2", FeedbackType.PRAISE, "Fantastisk!", rating=5)
        await collector.submit_feedback("user_3", FeedbackType.FEATURE_REQUEST, "Feature", rating=4)

        analysis = await collector.analyze_feedback()

        assert analysis.total_count == 3
        assert analysis.average_rating == pytest.approx(3.67, rel=0.1)


# =============================================================================
# TEST ADAPTIVE UI
# =============================================================================

class TestAdaptiveUI:
    """Tests for AdaptiveUI class."""

    @pytest_asyncio.fixture
    async def adaptive_ui(self):
        """Create adaptive UI fixture."""
        return create_adaptive_ui()

    @pytest.mark.asyncio
    async def test_track_behavior(self, adaptive_ui):
        """Test tracking user behavior."""
        await adaptive_ui.track_behavior(
            user_id="user_123",
            action="click",
            component="dashboard_button"
        )

        summary = await adaptive_ui.get_behavior_summary("user_123")
        assert summary["total_actions"] == 1

    @pytest.mark.asyncio
    async def test_suggest_adaptations_frequent_use(self, adaptive_ui):
        """Test suggesting adaptations for frequent use."""
        # Simuler hyppig brug
        for _ in range(15):
            await adaptive_ui.track_behavior("user_123", "click", "search_bar")

        adaptations = await adaptive_ui.suggest_adaptations("user_123")
        assert len(adaptations) > 0
        assert any(a.component == "search_bar" for a in adaptations)

    @pytest.mark.asyncio
    async def test_apply_adaptation(self, adaptive_ui):
        """Test applying adaptation."""
        adaptation = UIAdaptation(
            adaptation_id="adapt_123",
            user_id="user_123",
            component="sidebar",
            changes={"collapsed": True},
            reason="Brugerønske"
        )

        result = await adaptive_ui.apply_adaptation("user_123", adaptation)
        assert result is True

        user_adaptations = await adaptive_ui.get_user_adaptations("user_123")
        assert len(user_adaptations) == 1

    @pytest.mark.asyncio
    async def test_revert_adaptation(self, adaptive_ui):
        """Test reverting adaptation."""
        adaptation = UIAdaptation(
            adaptation_id="adapt_123",
            user_id="user_123",
            component="sidebar",
            changes={"collapsed": True},
            reason="Test"
        )

        await adaptive_ui.apply_adaptation("user_123", adaptation)
        result = await adaptive_ui.revert_adaptation("user_123", "adapt_123")

        assert result is True
        active = await adaptive_ui.get_user_adaptations("user_123")
        assert len(active) == 0


# =============================================================================
# TEST ACCESSIBILITY CHECKER
# =============================================================================

class TestAccessibilityChecker:
    """Tests for AccessibilityChecker class."""

    @pytest_asyncio.fixture
    async def checker(self):
        """Create accessibility checker fixture."""
        return create_accessibility_checker(AccessibilityLevel.AA)

    @pytest.mark.asyncio
    async def test_check_missing_alt_text(self, checker):
        """Test checking for missing alt text."""
        component = {
            "name": "hero_image",
            "images": [{"src": "hero.jpg"}]  # Missing alt
        }

        issues = await checker.check_component("hero_image", component)
        assert len(issues) > 0
        assert any(i.wcag_criterion == "1.1.1" for i in issues)

    @pytest.mark.asyncio
    async def test_check_low_contrast(self, checker):
        """Test checking for low contrast."""
        component = {
            "name": "text_block",
            "contrast_ratio": 3.0  # Below 4.5
        }

        issues = await checker.check_component("text_block", component)
        assert len(issues) > 0
        assert any(i.wcag_criterion == "1.4.3" for i in issues)

    @pytest.mark.asyncio
    async def test_check_keyboard_accessibility(self, checker):
        """Test checking keyboard accessibility."""
        component = {
            "name": "custom_dropdown",
            "interactive": True,
            "keyboard_accessible": False
        }

        issues = await checker.check_component("custom_dropdown", component)
        assert len(issues) > 0
        assert any(i.wcag_criterion == "2.1.1" for i in issues)

    @pytest.mark.asyncio
    async def test_generate_report(self, checker):
        """Test generating accessibility report."""
        components = [
            {"name": "header", "images": [{"src": "logo.png", "alt": "Logo"}]},
            {"name": "content", "contrast_ratio": 5.0},
            {"name": "footer", "interactive": True, "keyboard_accessible": True}
        ]

        report = await checker.generate_report(components)

        assert report.total_components == 3
        assert report.score >= 0

    @pytest.mark.asyncio
    async def test_get_rule_info(self, checker):
        """Test getting WCAG rule info."""
        rule = checker.get_rule_info("1.4.3")

        assert rule is not None
        assert rule["name"] == "Contrast (Minimum)"
        assert rule["level"] == AccessibilityLevel.AA


# =============================================================================
# TEST ONBOARDING WIZARD
# =============================================================================

class TestOnboardingWizard:
    """Tests for OnboardingWizard class."""

    @pytest_asyncio.fixture
    async def wizard(self):
        """Create onboarding wizard fixture."""
        return create_onboarding_wizard()

    @pytest.mark.asyncio
    async def test_start_onboarding(self, wizard):
        """Test starting onboarding."""
        progress = await wizard.start_onboarding("user_123")

        assert progress.user_id == "user_123"
        assert progress.current_step == OnboardingStep.WELCOME
        assert len(progress.completed_steps) == 0

    @pytest.mark.asyncio
    async def test_complete_step(self, wizard):
        """Test completing an onboarding step."""
        await wizard.start_onboarding("user_123")
        progress = await wizard.complete_step("user_123", OnboardingStep.WELCOME)

        assert OnboardingStep.WELCOME in progress.completed_steps
        assert progress.current_step == OnboardingStep.PROFILE_SETUP

    @pytest.mark.asyncio
    async def test_skip_step(self, wizard):
        """Test skipping an onboarding step."""
        await wizard.start_onboarding("user_123")
        progress = await wizard.skip_step("user_123", OnboardingStep.WELCOME)

        assert OnboardingStep.WELCOME in progress.skipped_steps
        assert progress.current_step == OnboardingStep.PROFILE_SETUP

    @pytest.mark.asyncio
    async def test_complete_full_onboarding(self, wizard):
        """Test completing full onboarding."""
        await wizard.start_onboarding("user_123")

        for step in OnboardingStep:
            if step != OnboardingStep.COMPLETION:
                await wizard.complete_step("user_123", step)

        progress = await wizard.get_progress("user_123")
        assert progress.is_completed
        assert progress.completed_at is not None

    @pytest.mark.asyncio
    async def test_get_step_content(self, wizard):
        """Test getting step content."""
        content = await wizard.get_step_content(OnboardingStep.WELCOME)

        assert "title" in content
        assert "description" in content
        assert content["title"] == "Velkommen til MASTERMIND"

    @pytest.mark.asyncio
    async def test_get_statistics(self, wizard):
        """Test getting onboarding statistics."""
        await wizard.start_onboarding("user_1")
        await wizard.start_onboarding("user_2")
        await wizard.complete_step("user_1", OnboardingStep.WELCOME)

        stats = await wizard.get_statistics()

        assert stats["total_users"] == 2
        assert stats["completed_users"] == 0


# =============================================================================
# TEST PREFERENCE MANAGER
# =============================================================================

class TestPreferenceManager:
    """Tests for PreferenceManager class."""

    @pytest_asyncio.fixture
    async def manager(self):
        """Create preference manager fixture."""
        return create_preference_manager()

    @pytest.mark.asyncio
    async def test_create_profile(self, manager):
        """Test creating preference profile."""
        profile = await manager.create_profile("user_123")

        assert profile.user_id == "user_123"
        assert profile.theme == UITheme.SYSTEM
        assert profile.language == "da"

    @pytest.mark.asyncio
    async def test_create_profile_with_initial_preferences(self, manager):
        """Test creating profile with initial preferences."""
        profile = await manager.create_profile(
            "user_123",
            initial_preferences={"compact_mode": True}
        )

        compact = await manager.get_preference("user_123", "compact_mode")
        assert compact is True

    @pytest.mark.asyncio
    async def test_set_preference(self, manager):
        """Test setting a preference."""
        await manager.create_profile("user_123")
        pref = await manager.set_preference("user_123", "auto_save", False)

        assert pref.value is False
        assert not pref.is_default

    @pytest.mark.asyncio
    async def test_set_theme(self, manager):
        """Test setting UI theme."""
        await manager.create_profile("user_123")
        result = await manager.set_theme("user_123", UITheme.DARK)

        assert result is True
        profile = await manager.get_profile("user_123")
        assert profile.theme == UITheme.DARK

    @pytest.mark.asyncio
    async def test_set_language(self, manager):
        """Test setting language."""
        await manager.create_profile("user_123")
        result = await manager.set_language("user_123", "en")

        assert result is True
        profile = await manager.get_profile("user_123")
        assert profile.language == "en"

    @pytest.mark.asyncio
    async def test_export_preferences(self, manager):
        """Test exporting preferences."""
        await manager.create_profile("user_123")
        await manager.set_theme("user_123", UITheme.DARK)

        exported = await manager.export_preferences("user_123")

        assert exported["user_id"] == "user_123"
        assert exported["theme"] == "dark"
        assert "preferences" in exported

    @pytest.mark.asyncio
    async def test_import_preferences(self, manager):
        """Test importing preferences."""
        data = {
            "theme": "dark",
            "language": "en",
            "preferences": {"compact_mode": True}
        }

        profile = await manager.import_preferences("user_123", data)

        assert profile.theme == UITheme.DARK
        assert profile.language == "en"

    @pytest.mark.asyncio
    async def test_reset_to_defaults(self, manager):
        """Test resetting to defaults."""
        await manager.create_profile("user_123")
        await manager.set_theme("user_123", UITheme.DARK)
        await manager.set_language("user_123", "en")

        profile = await manager.reset_to_defaults("user_123")

        assert profile.theme == UITheme.SYSTEM
        assert profile.language == "da"


# =============================================================================
# TEST FACTORY FUNCTIONS
# =============================================================================

class TestUXFactoryFunctions:
    """Tests for UX factory functions."""

    def test_create_feedback_collector(self):
        """Test creating feedback collector."""
        collector = create_feedback_collector()
        assert isinstance(collector, UserFeedbackCollector)

    def test_create_adaptive_ui(self):
        """Test creating adaptive UI."""
        ui = create_adaptive_ui()
        assert isinstance(ui, AdaptiveUI)

    def test_create_accessibility_checker(self):
        """Test creating accessibility checker."""
        checker = create_accessibility_checker(AccessibilityLevel.AAA)
        assert isinstance(checker, AccessibilityChecker)

    def test_create_onboarding_wizard(self):
        """Test creating onboarding wizard."""
        wizard = create_onboarding_wizard()
        assert isinstance(wizard, OnboardingWizard)

    def test_create_preference_manager(self):
        """Test creating preference manager."""
        manager = create_preference_manager()
        assert isinstance(manager, PreferenceManager)


# =============================================================================
# TEST MODULE IMPORTS
# =============================================================================

class TestUXModuleImports:
    """Tests for UX module imports."""

    def test_import_all_enums(self):
        """Test importing all enums from mastermind."""
        from cirkelline.ckc.mastermind import (
            FeedbackType,
            FeedbackSentiment,
            UITheme,
            AccessibilityLevel,
            OnboardingStep,
            PreferenceCategory,
        )
        assert FeedbackType is not None
        assert UITheme is not None

    def test_import_all_dataclasses(self):
        """Test importing all dataclasses from mastermind."""
        from cirkelline.ckc.mastermind import (
            UserFeedback,
            FeedbackAnalysis,
            UIAdaptation,
            AccessibilityIssue,
            AccessibilityReport,
            OnboardingProgress,
            UserPreference,
            PreferenceProfile,
        )
        assert UserFeedback is not None
        assert PreferenceProfile is not None

    def test_import_all_classes(self):
        """Test importing all classes from mastermind."""
        from cirkelline.ckc.mastermind import (
            UserFeedbackCollector,
            AdaptiveUI,
            AccessibilityChecker,
            OnboardingWizard,
            PreferenceManager,
        )
        assert UserFeedbackCollector is not None
        assert PreferenceManager is not None

    def test_all_exports(self):
        """Test all exports are in __all__."""
        from cirkelline.ckc.mastermind import __all__

        expected = [
            "FeedbackType", "FeedbackSentiment", "UITheme",
            "AccessibilityLevel", "OnboardingStep", "PreferenceCategory",
            "UserFeedback", "FeedbackAnalysis", "UIAdaptation",
            "AccessibilityIssue", "AccessibilityReport", "OnboardingProgress",
            "UserPreference", "PreferenceProfile",
            "UserFeedbackCollector", "AdaptiveUI", "AccessibilityChecker",
            "OnboardingWizard", "PreferenceManager",
        ]

        for item in expected:
            assert item in __all__, f"{item} should be in __all__"
