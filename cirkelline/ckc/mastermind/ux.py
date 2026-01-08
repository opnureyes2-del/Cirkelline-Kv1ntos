"""
DEL H: Brugercentrisk Udvikling & UX
=====================================

Komponenter til brugercentreret design og brugeroplevelse i MASTERMIND.

Komponenter:
- UserFeedbackCollector: Indsamling og analyse af brugerfeedback
- AdaptiveUI: Adaptiv UI baseret på brugeradfærd
- AccessibilityChecker: Tjek for tilgængelighed (WCAG)
- OnboardingWizard: Guidet onboarding for nye brugere
- PreferenceManager: Håndtering af brugerpræferencer
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4
import asyncio


# =============================================================================
# ENUMS
# =============================================================================

class FeedbackType(Enum):
    """Typer af brugerfeedback."""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    USABILITY_ISSUE = "usability_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    GENERAL_FEEDBACK = "general_feedback"
    PRAISE = "praise"
    COMPLAINT = "complaint"


class FeedbackSentiment(Enum):
    """Sentiment i feedback."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class UITheme(Enum):
    """UI temaer."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"
    HIGH_CONTRAST = "high_contrast"


class AccessibilityLevel(Enum):
    """WCAG tilgængelighedsniveauer."""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class OnboardingStep(Enum):
    """Trin i onboarding processen."""
    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    PREFERENCES = "preferences"
    TUTORIAL = "tutorial"
    FIRST_TASK = "first_task"
    COMPLETION = "completion"


class PreferenceCategory(Enum):
    """Kategorier af præferencer."""
    APPEARANCE = "appearance"
    NOTIFICATIONS = "notifications"
    PRIVACY = "privacy"
    LANGUAGE = "language"
    ACCESSIBILITY = "accessibility"
    WORKFLOW = "workflow"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class UserFeedback:
    """En brugerfeedback entry."""
    feedback_id: str
    user_id: str
    feedback_type: FeedbackType
    content: str
    sentiment: FeedbackSentiment
    context: Dict[str, Any] = field(default_factory=dict)
    rating: Optional[int] = None  # 1-5
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolution_notes: Optional[str] = None

    def __post_init__(self):
        if self.rating is not None and not 1 <= self.rating <= 5:
            raise ValueError("Rating skal være mellem 1 og 5")


@dataclass
class FeedbackAnalysis:
    """Analyse af feedback."""
    total_count: int
    sentiment_distribution: Dict[str, int]
    type_distribution: Dict[str, int]
    average_rating: Optional[float]
    top_issues: List[str]
    trends: List[str]
    period_start: datetime
    period_end: datetime


@dataclass
class UIAdaptation:
    """En UI tilpasning."""
    adaptation_id: str
    user_id: str
    component: str
    changes: Dict[str, Any]
    reason: str
    applied_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reverted: bool = False


@dataclass
class AccessibilityIssue:
    """Et tilgængelighedsproblem."""
    issue_id: str
    component: str
    wcag_criterion: str
    level: AccessibilityLevel
    description: str
    impact: str
    recommendation: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AccessibilityReport:
    """Rapport over tilgængelighed."""
    report_id: str
    checked_at: datetime
    total_components: int
    issues: List[AccessibilityIssue]
    compliance_level: AccessibilityLevel
    score: float  # 0-100

    @property
    def is_compliant(self) -> bool:
        """Er siden compliant på det angivne niveau?"""
        return len(self.issues) == 0

    @property
    def issues_by_level(self) -> Dict[str, int]:
        """Antal issues per niveau."""
        result = {"A": 0, "AA": 0, "AAA": 0}
        for issue in self.issues:
            result[issue.level.value] += 1
        return result


@dataclass
class OnboardingProgress:
    """Onboarding fremskridt for en bruger."""
    user_id: str
    current_step: OnboardingStep
    completed_steps: List[OnboardingStep] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    skipped_steps: List[OnboardingStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_completed(self) -> bool:
        """Er onboarding færdig?"""
        return self.current_step == OnboardingStep.COMPLETION

    @property
    def progress_percent(self) -> float:
        """Procentvis fremskridt."""
        total_steps = len(OnboardingStep)
        completed = len(self.completed_steps)
        return (completed / total_steps) * 100


@dataclass
class UserPreference:
    """En brugerpræference."""
    preference_id: str
    user_id: str
    category: PreferenceCategory
    key: str
    value: Any
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_default: bool = False


@dataclass
class PreferenceProfile:
    """Komplet præferenceprofil for en bruger."""
    user_id: str
    preferences: Dict[str, UserPreference]
    theme: UITheme = UITheme.SYSTEM
    language: str = "da"
    accessibility_needs: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# USER FEEDBACK COLLECTOR
# =============================================================================

class UserFeedbackCollector:
    """Indsamler og analyserer brugerfeedback."""

    def __init__(self):
        self._feedback: Dict[str, UserFeedback] = {}
        self._lock = asyncio.Lock()
        self._listeners: List[Callable] = []

    async def submit_feedback(
        self,
        user_id: str,
        feedback_type: FeedbackType,
        content: str,
        rating: Optional[int] = None,
        context: Optional[Dict] = None
    ) -> UserFeedback:
        """Indsend ny feedback."""
        async with self._lock:
            feedback_id = f"fb_{uuid4().hex[:12]}"

            # Analyser sentiment
            sentiment = self._analyze_sentiment(content)

            feedback = UserFeedback(
                feedback_id=feedback_id,
                user_id=user_id,
                feedback_type=feedback_type,
                content=content,
                sentiment=sentiment,
                context=context or {},
                rating=rating
            )

            self._feedback[feedback_id] = feedback

            # Notificer listeners
            for listener in self._listeners:
                try:
                    await listener(feedback)
                except Exception:
                    pass

            return feedback

    def _analyze_sentiment(self, content: str) -> FeedbackSentiment:
        """Analyser sentiment i tekst."""
        content_lower = content.lower()

        positive_words = ["fantastisk", "godt", "elsker", "perfekt", "flot", "tak", "great", "love", "excellent"]
        negative_words = ["dårlig", "fejl", "problem", "irriterende", "langsom", "bug", "error", "broken"]

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)

        if positive_count > 0 and negative_count > 0:
            return FeedbackSentiment.MIXED
        elif positive_count > negative_count:
            return FeedbackSentiment.POSITIVE
        elif negative_count > positive_count:
            return FeedbackSentiment.NEGATIVE
        else:
            return FeedbackSentiment.NEUTRAL

    async def get_feedback(self, feedback_id: str) -> Optional[UserFeedback]:
        """Hent specifik feedback."""
        return self._feedback.get(feedback_id)

    async def get_user_feedback(self, user_id: str) -> List[UserFeedback]:
        """Hent al feedback fra en bruger."""
        return [f for f in self._feedback.values() if f.user_id == user_id]

    async def resolve_feedback(
        self,
        feedback_id: str,
        resolution_notes: str
    ) -> Optional[UserFeedback]:
        """Marker feedback som løst."""
        async with self._lock:
            if feedback_id in self._feedback:
                self._feedback[feedback_id].resolved = True
                self._feedback[feedback_id].resolution_notes = resolution_notes
                return self._feedback[feedback_id]
            return None

    async def analyze_feedback(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> FeedbackAnalysis:
        """Analyser feedback over en periode."""
        now = datetime.now(timezone.utc)
        start = start_date or datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        end = end_date or now

        # Filtrer feedback
        filtered = [
            f for f in self._feedback.values()
            if start <= f.timestamp <= end
        ]

        # Beregn statistikker
        sentiment_dist = {s.value: 0 for s in FeedbackSentiment}
        type_dist = {t.value: 0 for t in FeedbackType}
        ratings = []

        for f in filtered:
            sentiment_dist[f.sentiment.value] += 1
            type_dist[f.feedback_type.value] += 1
            if f.rating:
                ratings.append(f.rating)

        avg_rating = sum(ratings) / len(ratings) if ratings else None

        # Find top issues
        top_issues = []
        if type_dist[FeedbackType.BUG_REPORT.value] > 0:
            top_issues.append("Bug reports kræver opmærksomhed")
        if type_dist[FeedbackType.USABILITY_ISSUE.value] > 0:
            top_issues.append("Usability problemer rapporteret")

        return FeedbackAnalysis(
            total_count=len(filtered),
            sentiment_distribution=sentiment_dist,
            type_distribution=type_dist,
            average_rating=avg_rating,
            top_issues=top_issues,
            trends=["Stigende brug af feature requests"] if type_dist[FeedbackType.FEATURE_REQUEST.value] > 2 else [],
            period_start=start,
            period_end=end
        )

    def add_listener(self, callback: Callable) -> None:
        """Tilføj listener for ny feedback."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable) -> None:
        """Fjern listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)


# =============================================================================
# ADAPTIVE UI
# =============================================================================

class AdaptiveUI:
    """Adapterer UI baseret på brugeradfærd."""

    def __init__(self):
        self._adaptations: Dict[str, List[UIAdaptation]] = {}
        self._user_behavior: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()

    async def track_behavior(
        self,
        user_id: str,
        action: str,
        component: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Spor brugeradfærd."""
        async with self._lock:
            if user_id not in self._user_behavior:
                self._user_behavior[user_id] = {
                    "actions": [],
                    "components_used": {},
                    "session_count": 0
                }

            behavior = self._user_behavior[user_id]
            behavior["actions"].append({
                "action": action,
                "component": component,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {}
            })

            # Opdater komponent-brug
            if component not in behavior["components_used"]:
                behavior["components_used"][component] = 0
            behavior["components_used"][component] += 1

    async def suggest_adaptations(self, user_id: str) -> List[UIAdaptation]:
        """Foreslå UI tilpasninger baseret på adfærd."""
        adaptations = []

        if user_id not in self._user_behavior:
            return adaptations

        behavior = self._user_behavior[user_id]
        components = behavior.get("components_used", {})

        # Foreslå at fremhæve hyppigt brugte komponenter
        for component, usage_count in components.items():
            if usage_count > 10:
                adaptation = UIAdaptation(
                    adaptation_id=f"adapt_{uuid4().hex[:8]}",
                    user_id=user_id,
                    component=component,
                    changes={"visibility": "prominent", "shortcut": True},
                    reason=f"Komponenten bruges ofte ({usage_count} gange)"
                )
                adaptations.append(adaptation)

        return adaptations

    async def apply_adaptation(
        self,
        user_id: str,
        adaptation: UIAdaptation
    ) -> bool:
        """Anvend en UI tilpasning."""
        async with self._lock:
            if user_id not in self._adaptations:
                self._adaptations[user_id] = []

            self._adaptations[user_id].append(adaptation)
            return True

    async def get_user_adaptations(self, user_id: str) -> List[UIAdaptation]:
        """Hent aktive tilpasninger for en bruger."""
        return [a for a in self._adaptations.get(user_id, []) if not a.reverted]

    async def revert_adaptation(
        self,
        user_id: str,
        adaptation_id: str
    ) -> bool:
        """Fortryd en tilpasning."""
        async with self._lock:
            if user_id in self._adaptations:
                for adaptation in self._adaptations[user_id]:
                    if adaptation.adaptation_id == adaptation_id:
                        adaptation.reverted = True
                        return True
            return False

    async def get_behavior_summary(self, user_id: str) -> Dict[str, Any]:
        """Få opsummering af brugeradfærd."""
        if user_id not in self._user_behavior:
            return {"error": "Ingen data for bruger"}

        behavior = self._user_behavior[user_id]
        return {
            "total_actions": len(behavior.get("actions", [])),
            "most_used_components": sorted(
                behavior.get("components_used", {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "session_count": behavior.get("session_count", 0)
        }


# =============================================================================
# ACCESSIBILITY CHECKER
# =============================================================================

class AccessibilityChecker:
    """Tjekker for tilgængelighedsproblemer (WCAG)."""

    def __init__(self, target_level: AccessibilityLevel = AccessibilityLevel.AA):
        self._target_level = target_level
        self._issues: List[AccessibilityIssue] = []
        self._rules = self._init_rules()

    def _init_rules(self) -> Dict[str, Dict]:
        """Initialiser WCAG regler."""
        return {
            "1.1.1": {
                "name": "Non-text Content",
                "level": AccessibilityLevel.A,
                "description": "Alle ikke-tekstuelle elementer skal have tekstalternativ"
            },
            "1.4.3": {
                "name": "Contrast (Minimum)",
                "level": AccessibilityLevel.AA,
                "description": "Tekst skal have mindst 4.5:1 kontrast"
            },
            "1.4.6": {
                "name": "Contrast (Enhanced)",
                "level": AccessibilityLevel.AAA,
                "description": "Tekst skal have mindst 7:1 kontrast"
            },
            "2.1.1": {
                "name": "Keyboard",
                "level": AccessibilityLevel.A,
                "description": "Al funktionalitet skal kunne betjenes med tastatur"
            },
            "2.4.4": {
                "name": "Link Purpose",
                "level": AccessibilityLevel.A,
                "description": "Linktekster skal beskrive formålet"
            },
            "3.1.1": {
                "name": "Language of Page",
                "level": AccessibilityLevel.A,
                "description": "Sidens sprog skal være angivet"
            }
        }

    async def check_component(
        self,
        component_name: str,
        component_data: Dict[str, Any]
    ) -> List[AccessibilityIssue]:
        """Tjek et komponent for tilgængelighedsproblemer."""
        issues = []

        # Tjek for alt-tekst
        if "images" in component_data:
            for img in component_data["images"]:
                if not img.get("alt"):
                    issues.append(AccessibilityIssue(
                        issue_id=f"a11y_{uuid4().hex[:8]}",
                        component=component_name,
                        wcag_criterion="1.1.1",
                        level=AccessibilityLevel.A,
                        description=f"Billede mangler alt-tekst: {img.get('src', 'unknown')}",
                        impact="Skærmlæsere kan ikke beskrive billedet",
                        recommendation="Tilføj beskrivende alt-attribut"
                    ))

        # Tjek for kontrast
        if "contrast_ratio" in component_data:
            ratio = component_data["contrast_ratio"]
            if ratio < 4.5:
                issues.append(AccessibilityIssue(
                    issue_id=f"a11y_{uuid4().hex[:8]}",
                    component=component_name,
                    wcag_criterion="1.4.3",
                    level=AccessibilityLevel.AA,
                    description=f"Utilstrækkelig kontrast: {ratio}:1",
                    impact="Tekst kan være svær at læse for brugere med synsnedsættelse",
                    recommendation="Øg kontrasten til mindst 4.5:1"
                ))

        # Tjek for keyboard accessibility
        if component_data.get("interactive") and not component_data.get("keyboard_accessible"):
            issues.append(AccessibilityIssue(
                issue_id=f"a11y_{uuid4().hex[:8]}",
                component=component_name,
                wcag_criterion="2.1.1",
                level=AccessibilityLevel.A,
                description="Interaktivt element er ikke tastatur-tilgængeligt",
                impact="Brugere uden mus kan ikke interagere med elementet",
                recommendation="Tilføj keyboard event handlers og fokusindikatorer"
            ))

        self._issues.extend(issues)
        return issues

    async def generate_report(
        self,
        components: List[Dict[str, Any]]
    ) -> AccessibilityReport:
        """Generer tilgængelighedsrapport."""
        all_issues = []

        for component in components:
            issues = await self.check_component(
                component.get("name", "unknown"),
                component
            )
            all_issues.extend(issues)

        # Beregn compliance niveau
        has_a_issues = any(i.level == AccessibilityLevel.A for i in all_issues)
        has_aa_issues = any(i.level == AccessibilityLevel.AA for i in all_issues)

        if has_a_issues:
            compliance = AccessibilityLevel.A  # Ikke compliant med A
        elif has_aa_issues:
            compliance = AccessibilityLevel.A  # Compliant med A, ikke AA
        else:
            compliance = self._target_level

        # Beregn score
        max_issues = len(components) * 5  # Antag max 5 issues per komponent
        score = max(0, 100 - (len(all_issues) / max(max_issues, 1)) * 100)

        return AccessibilityReport(
            report_id=f"a11y_report_{uuid4().hex[:8]}",
            checked_at=datetime.now(timezone.utc),
            total_components=len(components),
            issues=all_issues,
            compliance_level=compliance,
            score=round(score, 1)
        )

    def get_rule_info(self, criterion: str) -> Optional[Dict]:
        """Hent information om en WCAG regel."""
        return self._rules.get(criterion)

    def set_target_level(self, level: AccessibilityLevel) -> None:
        """Sæt mål-niveau for compliance."""
        self._target_level = level


# =============================================================================
# ONBOARDING WIZARD
# =============================================================================

class OnboardingWizard:
    """Guidet onboarding for nye brugere."""

    def __init__(self):
        self._progress: Dict[str, OnboardingProgress] = {}
        self._step_content: Dict[OnboardingStep, Dict] = self._init_steps()
        self._lock = asyncio.Lock()

    def _init_steps(self) -> Dict[OnboardingStep, Dict]:
        """Initialiser step indhold."""
        return {
            OnboardingStep.WELCOME: {
                "title": "Velkommen til MASTERMIND",
                "description": "Lær hvordan du bruger systemet effektivt",
                "duration_minutes": 2
            },
            OnboardingStep.PROFILE_SETUP: {
                "title": "Opsæt din profil",
                "description": "Tilføj dine oplysninger og præferencer",
                "duration_minutes": 3,
                "required_fields": ["name", "role"]
            },
            OnboardingStep.PREFERENCES: {
                "title": "Tilpas dine indstillinger",
                "description": "Vælg tema, notifikationer og mere",
                "duration_minutes": 2
            },
            OnboardingStep.TUTORIAL: {
                "title": "Interaktiv tutorial",
                "description": "Lær de vigtigste funktioner",
                "duration_minutes": 5
            },
            OnboardingStep.FIRST_TASK: {
                "title": "Din første opgave",
                "description": "Prøv at oprette din første opgave",
                "duration_minutes": 3
            },
            OnboardingStep.COMPLETION: {
                "title": "Du er klar!",
                "description": "Onboarding er færdig - god fornøjelse!",
                "duration_minutes": 1
            }
        }

    async def start_onboarding(self, user_id: str) -> OnboardingProgress:
        """Start onboarding for en ny bruger."""
        async with self._lock:
            progress = OnboardingProgress(
                user_id=user_id,
                current_step=OnboardingStep.WELCOME
            )
            self._progress[user_id] = progress
            return progress

    async def get_progress(self, user_id: str) -> Optional[OnboardingProgress]:
        """Hent onboarding fremskridt."""
        return self._progress.get(user_id)

    async def complete_step(
        self,
        user_id: str,
        step: OnboardingStep,
        metadata: Optional[Dict] = None
    ) -> Optional[OnboardingProgress]:
        """Marker et step som færdigt."""
        async with self._lock:
            if user_id not in self._progress:
                return None

            progress = self._progress[user_id]

            if step not in progress.completed_steps:
                progress.completed_steps.append(step)

            if metadata:
                progress.metadata.update(metadata)

            # Find næste step
            steps = list(OnboardingStep)
            current_idx = steps.index(step)

            if current_idx < len(steps) - 1:
                next_step = steps[current_idx + 1]
                progress.current_step = next_step
                # Hvis næste step er COMPLETION, marker som færdig
                if next_step == OnboardingStep.COMPLETION:
                    progress.completed_at = datetime.now(timezone.utc)
            else:
                progress.current_step = OnboardingStep.COMPLETION
                progress.completed_at = datetime.now(timezone.utc)

            return progress

    async def skip_step(
        self,
        user_id: str,
        step: OnboardingStep
    ) -> Optional[OnboardingProgress]:
        """Spring et step over."""
        async with self._lock:
            if user_id not in self._progress:
                return None

            progress = self._progress[user_id]

            if step not in progress.skipped_steps:
                progress.skipped_steps.append(step)

            # Find næste step
            steps = list(OnboardingStep)
            current_idx = steps.index(step)

            if current_idx < len(steps) - 1:
                progress.current_step = steps[current_idx + 1]

            return progress

    async def get_step_content(self, step: OnboardingStep) -> Dict:
        """Hent indhold for et step."""
        return self._step_content.get(step, {})

    async def reset_onboarding(self, user_id: str) -> OnboardingProgress:
        """Nulstil onboarding for en bruger."""
        return await self.start_onboarding(user_id)

    async def get_statistics(self) -> Dict[str, Any]:
        """Hent statistik over onboarding."""
        total = len(self._progress)
        completed = sum(1 for p in self._progress.values() if p.is_completed)

        step_completion = {step.value: 0 for step in OnboardingStep}
        for progress in self._progress.values():
            for step in progress.completed_steps:
                step_completion[step.value] += 1

        return {
            "total_users": total,
            "completed_users": completed,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "step_completion_rates": {
                step: (count / total * 100) if total > 0 else 0
                for step, count in step_completion.items()
            },
            "average_completion_time_minutes": 15  # Placeholder
        }


# =============================================================================
# PREFERENCE MANAGER
# =============================================================================

class PreferenceManager:
    """Håndterer brugerpræferencer."""

    def __init__(self):
        self._profiles: Dict[str, PreferenceProfile] = {}
        self._defaults: Dict[str, Any] = {
            "theme": UITheme.SYSTEM,
            "language": "da",
            "notifications_enabled": True,
            "email_notifications": True,
            "sound_enabled": True,
            "auto_save": True,
            "compact_mode": False
        }
        self._lock = asyncio.Lock()

    async def create_profile(
        self,
        user_id: str,
        initial_preferences: Optional[Dict] = None
    ) -> PreferenceProfile:
        """Opret præferenceprofil for bruger."""
        async with self._lock:
            preferences = {}

            # Anvend defaults
            for key, value in self._defaults.items():
                category = self._categorize_preference(key)
                pref = UserPreference(
                    preference_id=f"pref_{uuid4().hex[:8]}",
                    user_id=user_id,
                    category=category,
                    key=key,
                    value=value,
                    is_default=True
                )
                preferences[key] = pref

            # Anvend initiale præferencer
            if initial_preferences:
                for key, value in initial_preferences.items():
                    category = self._categorize_preference(key)
                    pref = UserPreference(
                        preference_id=f"pref_{uuid4().hex[:8]}",
                        user_id=user_id,
                        category=category,
                        key=key,
                        value=value,
                        is_default=False
                    )
                    preferences[key] = pref

            profile = PreferenceProfile(
                user_id=user_id,
                preferences=preferences
            )

            self._profiles[user_id] = profile
            return profile

    def _categorize_preference(self, key: str) -> PreferenceCategory:
        """Kategoriser en præference baseret på nøgle."""
        if "theme" in key or "color" in key or "font" in key:
            return PreferenceCategory.APPEARANCE
        elif "notification" in key or "alert" in key:
            return PreferenceCategory.NOTIFICATIONS
        elif "privacy" in key or "data" in key:
            return PreferenceCategory.PRIVACY
        elif "language" in key or "locale" in key:
            return PreferenceCategory.LANGUAGE
        elif "accessibility" in key or "contrast" in key:
            return PreferenceCategory.ACCESSIBILITY
        else:
            return PreferenceCategory.WORKFLOW

    async def get_profile(self, user_id: str) -> Optional[PreferenceProfile]:
        """Hent præferenceprofil."""
        return self._profiles.get(user_id)

    async def get_preference(
        self,
        user_id: str,
        key: str
    ) -> Optional[Any]:
        """Hent en specifik præference."""
        profile = self._profiles.get(user_id)
        if profile and key in profile.preferences:
            return profile.preferences[key].value
        return self._defaults.get(key)

    def _set_preference_internal(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> Optional[UserPreference]:
        """Intern metode til at sætte præference (kræver at lock allerede er holdt)."""
        if user_id not in self._profiles:
            return None

        profile = self._profiles[user_id]
        category = self._categorize_preference(key)

        pref = UserPreference(
            preference_id=f"pref_{uuid4().hex[:8]}",
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            is_default=False
        )

        profile.preferences[key] = pref
        profile.last_updated = datetime.now(timezone.utc)

        return pref

    async def set_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> Optional[UserPreference]:
        """Sæt en præference."""
        async with self._lock:
            if user_id not in self._profiles:
                await self.create_profile(user_id)

            return self._set_preference_internal(user_id, key, value)

    async def set_theme(self, user_id: str, theme: UITheme) -> bool:
        """Sæt UI tema."""
        async with self._lock:
            if user_id not in self._profiles:
                await self.create_profile(user_id)

            self._profiles[user_id].theme = theme
            self._set_preference_internal(user_id, "theme", theme.value)
            return True

    async def set_language(self, user_id: str, language: str) -> bool:
        """Sæt sprog."""
        async with self._lock:
            if user_id not in self._profiles:
                await self.create_profile(user_id)

            self._profiles[user_id].language = language
            self._set_preference_internal(user_id, "language", language)
            return True

    async def reset_to_defaults(self, user_id: str) -> PreferenceProfile:
        """Nulstil alle præferencer til defaults."""
        return await self.create_profile(user_id)

    async def export_preferences(self, user_id: str) -> Dict[str, Any]:
        """Eksporter alle præferencer."""
        profile = self._profiles.get(user_id)
        if not profile:
            return {}

        return {
            "user_id": user_id,
            "theme": profile.theme.value,
            "language": profile.language,
            "preferences": {
                key: pref.value
                for key, pref in profile.preferences.items()
            },
            "exported_at": datetime.now(timezone.utc).isoformat()
        }

    async def import_preferences(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> PreferenceProfile:
        """Importer præferencer."""
        preferences = data.get("preferences", {})
        profile = await self.create_profile(user_id, preferences)

        if "theme" in data:
            profile.theme = UITheme(data["theme"])
        if "language" in data:
            profile.language = data["language"]

        return profile


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

# Singleton instances
_feedback_collector: Optional[UserFeedbackCollector] = None
_adaptive_ui: Optional[AdaptiveUI] = None
_accessibility_checker: Optional[AccessibilityChecker] = None
_onboarding_wizard: Optional[OnboardingWizard] = None
_preference_manager: Optional[PreferenceManager] = None


def create_feedback_collector() -> UserFeedbackCollector:
    """Opret ny UserFeedbackCollector instans."""
    return UserFeedbackCollector()


def get_feedback_collector() -> UserFeedbackCollector:
    """Hent eller opret singleton UserFeedbackCollector."""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = create_feedback_collector()
    return _feedback_collector


def create_adaptive_ui() -> AdaptiveUI:
    """Opret ny AdaptiveUI instans."""
    return AdaptiveUI()


def get_adaptive_ui() -> AdaptiveUI:
    """Hent eller opret singleton AdaptiveUI."""
    global _adaptive_ui
    if _adaptive_ui is None:
        _adaptive_ui = create_adaptive_ui()
    return _adaptive_ui


def create_accessibility_checker(
    target_level: AccessibilityLevel = AccessibilityLevel.AA
) -> AccessibilityChecker:
    """Opret ny AccessibilityChecker instans."""
    return AccessibilityChecker(target_level=target_level)


def get_accessibility_checker() -> AccessibilityChecker:
    """Hent eller opret singleton AccessibilityChecker."""
    global _accessibility_checker
    if _accessibility_checker is None:
        _accessibility_checker = create_accessibility_checker()
    return _accessibility_checker


def create_onboarding_wizard() -> OnboardingWizard:
    """Opret ny OnboardingWizard instans."""
    return OnboardingWizard()


def get_onboarding_wizard() -> OnboardingWizard:
    """Hent eller opret singleton OnboardingWizard."""
    global _onboarding_wizard
    if _onboarding_wizard is None:
        _onboarding_wizard = create_onboarding_wizard()
    return _onboarding_wizard


def create_preference_manager() -> PreferenceManager:
    """Opret ny PreferenceManager instans."""
    return PreferenceManager()


def get_preference_manager() -> PreferenceManager:
    """Hent eller opret singleton PreferenceManager."""
    global _preference_manager
    if _preference_manager is None:
        _preference_manager = create_preference_manager()
    return _preference_manager
