"""
CKC MASTERMIND Super Admin Kontrol & Bevidsthedssystem
======================================================

Dette modul implementerer de 4 kernefunktioner for Super Admin kontrol:

1. Masterminds Øje (SuperAdminDashboard)
   - Globalt realtids overblik over hele økosystemet

2. Masterminds Stemme (IntelligentNotificationEngine)
   - Proaktive, intelligente advarsler

3. KV1NT Terminal Partner (KV1NTTerminalPartner)
   - Strategisk sparring og workflow-dirigering

4. Organisk Læring (AdaptiveLearningSystem)
   - System der konstant tilpasser sig brugerens behov

Kerneprincipper:
- "Absolut bevidsthed for Super Admin"
- "Proaktiv intelligens"
- "Organisk tilpasning"
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

# CKC Folder Switcher import (v1.3.5)
from ..folder_switcher import CKCFolderSwitcher, get_folder_switcher

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class DashboardZone(Enum):
    """Zoner i Super Admin Dashboard."""
    LEARNING_ROOMS = "learning_rooms"
    SYSTEMS = "systems"
    PROFILES = "profiles"
    TASKS = "tasks"
    COMMUNICATIONS = "communications"
    UPDATES = "updates"
    SECURITY = "security"
    ETHICS = "ethics"
    CKC_FOLDERS = "ckc_folders"  # v1.3.5: Folder context zone for Super Admin


class AlertLevel(Enum):
    """Advarsels-niveauer."""
    CRITICAL = "critical"
    IMPORTANT = "important"
    INFORMATIONAL = "informational"
    DEBUG = "debug"


class AlertCategory(Enum):
    """Kategori af advarsler."""
    SYSTEM_DEVIATION = "system_deviation"
    MILESTONE = "milestone"
    KNOWLEDGE_FLOW = "knowledge_flow"
    RESOURCE_TREND = "resource_trend"
    SECURITY_EVENT = "security_event"
    ETHICS_ALERT = "ethics_alert"
    PERFORMANCE = "performance"


class DeliveryChannel(Enum):
    """Leveringskanaler for notifikationer."""
    TERMINAL = "terminal"
    EMAIL = "email"
    INTERNAL_MESSAGE = "internal_message"
    WEBHOOK = "webhook"
    SMS = "sms"


class WorkflowRecommendationType(Enum):
    """Typer af workflow-anbefalinger."""
    AGENT_REALLOCATION = "agent_reallocation"
    CONFLICT_WARNING = "conflict_warning"
    REDUNDANCY_REMOVAL = "redundancy_removal"
    PERFORMANCE_INSIGHT = "performance_insight"
    OPTIMIZATION_SUGGESTION = "optimization_suggestion"


class KnowledgeQueryType(Enum):
    """Typer af videns-forespørgsler."""
    SYNTHESIS_REPORT = "synthesis_report"
    AD_HOC_QUERY = "ad_hoc_query"
    AUDIT_TRAIL = "audit_trail"
    SCENARIO_SIMULATION = "scenario_simulation"


class FeedbackType(Enum):
    """Typer af bruger-feedback."""
    DASHBOARD_PREFERENCE = "dashboard_preference"
    NOTIFICATION_PREFERENCE = "notification_preference"
    WORKFLOW_PREFERENCE = "workflow_preference"
    KNOWLEDGE_FORMAT_PREFERENCE = "knowledge_format_preference"
    EXPLICIT_RATING = "explicit_rating"


class LearningAdaptationType(Enum):
    """Typer af adaptiv læring."""
    DISPLAY_OPTIMIZATION = "display_optimization"
    ALERT_TUNING = "alert_tuning"
    RECOMMENDATION_REFINEMENT = "recommendation_refinement"
    FORMAT_ADJUSTMENT = "format_adjustment"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ZoneStatus:
    """Status for en dashboard-zone."""
    zone: DashboardZone
    status: str  # "healthy", "warning", "critical"
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    alerts_count: int = 0
    active_items: int = 0


@dataclass
class Alert:
    """En intelligent advarsel."""
    alert_id: str = field(default_factory=lambda: f"alert_{secrets.token_hex(6)}")
    level: AlertLevel = AlertLevel.INFORMATIONAL
    category: AlertCategory = AlertCategory.SYSTEM_DEVIATION
    title: str = ""
    message: str = ""
    source_zone: Optional[DashboardZone] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationPreference:
    """Notifikationspræferencer for en bruger."""
    user_id: str = ""
    channels: List[DeliveryChannel] = field(default_factory=list)
    alert_levels: List[AlertLevel] = field(default_factory=list)
    categories: List[AlertCategory] = field(default_factory=list)
    quiet_hours_start: Optional[int] = None  # Hour (0-23)
    quiet_hours_end: Optional[int] = None
    aggregation_interval_minutes: int = 5


@dataclass
class WorkflowRecommendation:
    """En workflow-anbefaling fra KV1NT."""
    recommendation_id: str = field(default_factory=lambda: f"rec_{secrets.token_hex(6)}")
    recommendation_type: WorkflowRecommendationType = WorkflowRecommendationType.OPTIMIZATION_SUGGESTION
    title: str = ""
    description: str = ""
    impact_assessment: str = ""
    confidence: float = 0.0
    affected_workflows: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accepted: Optional[bool] = None
    implemented: bool = False


@dataclass
class KnowledgeQuery:
    """En videns-forespørgsel til KV1NT."""
    query_id: str = field(default_factory=lambda: f"query_{secrets.token_hex(6)}")
    query_type: KnowledgeQueryType = KnowledgeQueryType.AD_HOC_QUERY
    query_text: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class KnowledgeResponse:
    """Svar på en videns-forespørgsel."""
    response_id: str = field(default_factory=lambda: f"resp_{secrets.token_hex(6)}")
    query_id: str = ""
    content: str = ""
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.0
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    format: str = "text"  # "text", "json", "markdown", "structured"


@dataclass
class UserFeedback:
    """Feedback fra brugeren."""
    feedback_id: str = field(default_factory=lambda: f"fb_{secrets.token_hex(6)}")
    feedback_type: FeedbackType = FeedbackType.EXPLICIT_RATING
    target_component: str = ""
    value: Any = None
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LearningAdaptation:
    """En adaptiv tilpasning baseret på læring."""
    adaptation_id: str = field(default_factory=lambda: f"adapt_{secrets.token_hex(6)}")
    adaptation_type: LearningAdaptationType = LearningAdaptationType.DISPLAY_OPTIMIZATION
    description: str = ""
    parameters_changed: Dict[str, Any] = field(default_factory=dict)
    applied_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    effectiveness_score: float = 0.0


# =============================================================================
# 1. MASTERMINDS ØJE - SUPER ADMIN DASHBOARD
# =============================================================================

class SuperAdminDashboard:
    """
    Masterminds Øje - Globalt realtids status dashboard.

    Viser øjeblikkelig status for:
    - Alle lærerum
    - Alle systemer/platforme
    - Alle profiler
    - Alle opgaver
    - Alle kommunikationer
    - Systemopdateringer
    """

    def __init__(
        self,
        refresh_rate_seconds: float = 1.0,
        security_profile: str = "super_admin_exclusive"
    ):
        self._refresh_rate = refresh_rate_seconds
        self._security_profile = security_profile
        self._zones: Dict[DashboardZone, ZoneStatus] = {}
        self._is_active = False
        self._last_refresh: Optional[datetime] = None
        self._refresh_callbacks: List[Callable] = []
        self._custom_metrics: Dict[str, Any] = {}

        # Initialize all zones
        for zone in DashboardZone:
            self._zones[zone] = ZoneStatus(
                zone=zone,
                status="healthy",
                metrics={},
                active_items=0
            )

        logger.info(f"SuperAdminDashboard initialiseret (refresh={refresh_rate_seconds}s)")

    def activate(self) -> bool:
        """Aktiver dashboard."""
        self._is_active = True
        self._last_refresh = datetime.now(timezone.utc)
        logger.info("SuperAdminDashboard aktiveret")
        return True

    def deactivate(self) -> bool:
        """Deaktiver dashboard."""
        self._is_active = False
        logger.info("SuperAdminDashboard deaktiveret")
        return True

    def is_active(self) -> bool:
        """Check om dashboard er aktivt."""
        return self._is_active

    def get_zone_status(self, zone: DashboardZone) -> ZoneStatus:
        """Hent status for en specifik zone."""
        return self._zones.get(zone, ZoneStatus(zone=zone, status="unknown"))

    def update_zone_status(
        self,
        zone: DashboardZone,
        status: str,
        metrics: Optional[Dict[str, Any]] = None,
        active_items: Optional[int] = None,
        alerts_count: Optional[int] = None
    ) -> ZoneStatus:
        """Opdater status for en zone."""
        zone_status = self._zones.get(zone, ZoneStatus(zone=zone, status="unknown"))
        zone_status.status = status
        zone_status.last_updated = datetime.now(timezone.utc)

        if metrics is not None:
            zone_status.metrics.update(metrics)
        if active_items is not None:
            zone_status.active_items = active_items
        if alerts_count is not None:
            zone_status.alerts_count = alerts_count

        self._zones[zone] = zone_status
        return zone_status

    def get_global_status(self) -> Dict[str, Any]:
        """Hent global status for hele økosystemet."""
        zone_statuses = {}
        total_alerts = 0
        total_active = 0
        overall_health = "healthy"

        for zone, status in self._zones.items():
            zone_statuses[zone.value] = {
                "status": status.status,
                "metrics": status.metrics,
                "active_items": status.active_items,
                "alerts_count": status.alerts_count,
                "last_updated": status.last_updated.isoformat()
            }
            total_alerts += status.alerts_count
            total_active += status.active_items

            if status.status == "critical":
                overall_health = "critical"
            elif status.status == "warning" and overall_health != "critical":
                overall_health = "warning"

        return {
            "is_active": self._is_active,
            "overall_health": overall_health,
            "total_alerts": total_alerts,
            "total_active_items": total_active,
            "zones": zone_statuses,
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "refresh_rate_seconds": self._refresh_rate,
            "security_profile": self._security_profile
        }

    def refresh(self) -> Dict[str, Any]:
        """Opfrisk dashboard data."""
        self._last_refresh = datetime.now(timezone.utc)

        # Execute refresh callbacks
        for callback in self._refresh_callbacks:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Refresh callback fejl: {e}")

        return self.get_global_status()

    def register_refresh_callback(self, callback: Callable) -> None:
        """Registrer en callback der køres ved refresh."""
        self._refresh_callbacks.append(callback)

    def set_custom_metric(self, key: str, value: Any) -> None:
        """Sæt en custom metric."""
        self._custom_metrics[key] = value

    def get_custom_metrics(self) -> Dict[str, Any]:
        """Hent custom metrics."""
        return self._custom_metrics.copy()


# =============================================================================
# 2. MASTERMINDS STEMME - INTELLIGENT NOTIFIKATIONSMOTOR
# =============================================================================

class IntelligentNotificationEngine:
    """
    Masterminds Stemme - Intelligent notifikations- og advarselsmotor.

    Sender proaktive advarsler om:
    - Kritiske systemafvigelser
    - Afgørende milepæle
    - Nye videnstrømme
    - Ressourceforbrugstendenser
    - Sikkerhedsrelaterede hændelser
    """

    def __init__(self):
        self._alerts: List[Alert] = []
        self._preferences: Dict[str, NotificationPreference] = {}
        self._delivery_handlers: Dict[DeliveryChannel, Callable] = {}
        self._alert_history: List[Alert] = []
        self._is_active = False
        self._pending_aggregation: Dict[str, List[Alert]] = {}

        logger.info("IntelligentNotificationEngine initialiseret")

    def activate(self) -> bool:
        """Aktiver notifikationsmotoren."""
        self._is_active = True
        logger.info("IntelligentNotificationEngine aktiveret")
        return True

    def deactivate(self) -> bool:
        """Deaktiver notifikationsmotoren."""
        self._is_active = False
        logger.info("IntelligentNotificationEngine deaktiveret")
        return True

    def is_active(self) -> bool:
        """Check om motoren er aktiv."""
        return self._is_active

    def set_preferences(
        self,
        user_id: str,
        channels: Optional[List[DeliveryChannel]] = None,
        alert_levels: Optional[List[AlertLevel]] = None,
        categories: Optional[List[AlertCategory]] = None
    ) -> NotificationPreference:
        """Sæt notifikationspræferencer for en bruger."""
        pref = self._preferences.get(user_id, NotificationPreference(user_id=user_id))

        if channels is not None:
            pref.channels = channels
        if alert_levels is not None:
            pref.alert_levels = alert_levels
        if categories is not None:
            pref.categories = categories

        self._preferences[user_id] = pref
        return pref

    def get_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """Hent præferencer for en bruger."""
        return self._preferences.get(user_id)

    def create_alert(
        self,
        level: AlertLevel,
        category: AlertCategory,
        title: str,
        message: str,
        source_zone: Optional[DashboardZone] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Opret en ny advarsel."""
        alert = Alert(
            level=level,
            category=category,
            title=title,
            message=message,
            source_zone=source_zone,
            metadata=metadata or {}
        )
        self._alerts.append(alert)
        logger.info(f"Alert oprettet: [{level.value}] {title}")
        return alert

    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        category: Optional[AlertCategory] = None,
        unacknowledged_only: bool = False
    ) -> List[Alert]:
        """Hent advarsler med optional filtrering."""
        alerts = self._alerts

        if level:
            alerts = [a for a in alerts if a.level == level]
        if category:
            alerts = [a for a in alerts if a.category == category]
        if unacknowledged_only:
            alerts = [a for a in alerts if not a.acknowledged]

        return sorted(alerts, key=lambda x: x.created_at, reverse=True)

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Kvitter en advarsel."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.now(timezone.utc)
                logger.info(f"Alert kvitteret: {alert_id}")
                return True
        return False

    def register_delivery_handler(
        self,
        channel: DeliveryChannel,
        handler: Callable[[Alert], bool]
    ) -> None:
        """Registrer en delivery handler for en kanal."""
        self._delivery_handlers[channel] = handler

    async def deliver_alert(self, alert: Alert, user_id: str) -> Dict[str, bool]:
        """Lever en advarsel via foretrukne kanaler."""
        results = {}
        pref = self._preferences.get(user_id)

        if not pref:
            return {"error": "No preferences set"}

        # Check if alert matches preferences
        if alert.level not in pref.alert_levels:
            return {"skipped": True, "reason": "level_filtered"}
        if alert.category not in pref.categories:
            return {"skipped": True, "reason": "category_filtered"}

        # Deliver via each channel
        for channel in pref.channels:
            handler = self._delivery_handlers.get(channel)
            if handler:
                try:
                    results[channel.value] = handler(alert)
                except Exception as e:
                    results[channel.value] = False
                    logger.error(f"Delivery fejl for {channel.value}: {e}")

        return results

    def get_status(self) -> Dict[str, Any]:
        """Hent status for notifikationsmotoren."""
        return {
            "is_active": self._is_active,
            "total_alerts": len(self._alerts),
            "unacknowledged_alerts": len([a for a in self._alerts if not a.acknowledged]),
            "critical_alerts": len([a for a in self._alerts if a.level == AlertLevel.CRITICAL and not a.acknowledged]),
            "registered_channels": [c.value for c in self._delivery_handlers.keys()],
            "users_with_preferences": len(self._preferences)
        }


# =============================================================================
# 3. KV1NT TERMINAL PARTNER
# =============================================================================

class KV1NTTerminalPartner:
    """
    KV1NT som Terminal Partner - Strategisk sparring og workflow-dirigering.

    Tilbyder:
    - Workflow dirigent & optimeringsstøtte
    - Kontekstuel videnlevering & beslutningsgrundlag
    - "What-if" scenarier og forudsigelser
    """

    def __init__(self, interface: str = "terminal"):
        self._interface = interface
        self._is_active = False
        self._recommendations: List[WorkflowRecommendation] = []
        self._queries: List[KnowledgeQuery] = []
        self._responses: List[KnowledgeResponse] = []
        self._knowledge_sources: Set[str] = set()
        self._active_workflows: Dict[str, Dict[str, Any]] = {}

        logger.info(f"KV1NTTerminalPartner initialiseret (interface={interface})")

    def activate(self) -> bool:
        """Aktiver KV1NT terminal partner."""
        self._is_active = True
        logger.info("KV1NTTerminalPartner aktiveret")
        return True

    def deactivate(self) -> bool:
        """Deaktiver KV1NT terminal partner."""
        self._is_active = False
        logger.info("KV1NTTerminalPartner deaktiveret")
        return True

    def is_active(self) -> bool:
        """Check om KV1NT er aktiv."""
        return self._is_active

    # -------------------------------------------------------------------------
    # WORKFLOW DIRIGERING
    # -------------------------------------------------------------------------

    def register_workflow(
        self,
        workflow_id: str,
        workflow_type: str,
        agents: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Registrer et workflow for overvågning."""
        self._active_workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "agents": agents,
            "metadata": metadata or {},
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        }
        return self._active_workflows[workflow_id]

    def get_active_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Hent alle aktive workflows."""
        return self._active_workflows.copy()

    def create_recommendation(
        self,
        recommendation_type: WorkflowRecommendationType,
        title: str,
        description: str,
        impact_assessment: str,
        confidence: float,
        affected_workflows: Optional[List[str]] = None
    ) -> WorkflowRecommendation:
        """Opret en workflow-anbefaling."""
        rec = WorkflowRecommendation(
            recommendation_type=recommendation_type,
            title=title,
            description=description,
            impact_assessment=impact_assessment,
            confidence=confidence,
            affected_workflows=affected_workflows or []
        )
        self._recommendations.append(rec)
        logger.info(f"Recommendation oprettet: {title}")
        return rec

    def get_recommendations(
        self,
        recommendation_type: Optional[WorkflowRecommendationType] = None,
        min_confidence: float = 0.0
    ) -> List[WorkflowRecommendation]:
        """Hent anbefalinger med optional filtrering."""
        recs = self._recommendations

        if recommendation_type:
            recs = [r for r in recs if r.recommendation_type == recommendation_type]
        recs = [r for r in recs if r.confidence >= min_confidence]

        return sorted(recs, key=lambda x: x.confidence, reverse=True)

    def accept_recommendation(self, recommendation_id: str, accepted: bool) -> bool:
        """Accepter eller afvis en anbefaling."""
        for rec in self._recommendations:
            if rec.recommendation_id == recommendation_id:
                rec.accepted = accepted
                logger.info(f"Recommendation {recommendation_id}: {'accepteret' if accepted else 'afvist'}")
                return True
        return False

    # -------------------------------------------------------------------------
    # KONTEKSTUEL VIDENLEVERING
    # -------------------------------------------------------------------------

    def register_knowledge_source(self, source_name: str) -> None:
        """Registrer en videnskilde."""
        self._knowledge_sources.add(source_name)

    def get_knowledge_sources(self) -> Set[str]:
        """Hent registrerede videnkilder."""
        return self._knowledge_sources.copy()

    def query_knowledge(
        self,
        query_type: KnowledgeQueryType,
        query_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> KnowledgeQuery:
        """Opret en videns-forespørgsel."""
        query = KnowledgeQuery(
            query_type=query_type,
            query_text=query_text,
            context=context or {}
        )
        self._queries.append(query)
        logger.info(f"Knowledge query oprettet: {query_type.value}")
        return query

    def create_response(
        self,
        query_id: str,
        content: str,
        sources: List[str],
        confidence: float,
        format: str = "text"
    ) -> KnowledgeResponse:
        """Opret et svar på en videns-forespørgsel."""
        response = KnowledgeResponse(
            query_id=query_id,
            content=content,
            sources=sources,
            confidence=confidence,
            format=format
        )
        self._responses.append(response)
        return response

    def get_response_for_query(self, query_id: str) -> Optional[KnowledgeResponse]:
        """Hent svar for en specifik forespørgsel."""
        for resp in self._responses:
            if resp.query_id == query_id:
                return resp
        return None

    # -------------------------------------------------------------------------
    # SCENARIO SIMULATION
    # -------------------------------------------------------------------------

    def simulate_scenario(
        self,
        scenario_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simuler et what-if scenarie."""
        # Create scenario simulation query
        query = self.query_knowledge(
            query_type=KnowledgeQueryType.SCENARIO_SIMULATION,
            query_text=f"Simulate: {scenario_name}",
            context={"parameters": parameters}
        )

        # Generate simulation result (simplified)
        simulation_result = {
            "scenario_id": f"scenario_{secrets.token_hex(6)}",
            "scenario_name": scenario_name,
            "parameters": parameters,
            "query_id": query.query_id,
            "predicted_outcomes": [],
            "confidence": 0.75,
            "simulated_at": datetime.now(timezone.utc).isoformat()
        }

        return simulation_result

    def get_status(self) -> Dict[str, Any]:
        """Hent status for KV1NT."""
        return {
            "is_active": self._is_active,
            "interface": self._interface,
            "active_workflows": len(self._active_workflows),
            "total_recommendations": len(self._recommendations),
            "pending_recommendations": len([r for r in self._recommendations if r.accepted is None]),
            "knowledge_sources": list(self._knowledge_sources),
            "total_queries": len(self._queries),
            "total_responses": len(self._responses)
        }


# =============================================================================
# 4. ORGANISK LÆRING - ADAPTIV FEEDBACK SYSTEM
# =============================================================================

class AdaptiveLearningSystem:
    """
    Organisk Læring - System der konstant tilpasser sig brugerens behov.

    Håndterer:
    - Super Admin feedback loop
    - Adaptiv forbedring af alle komponenter
    - Personalisering baseret på interaktionsmønstre
    """

    def __init__(self, target_user: str = "super_admin"):
        self._target_user = target_user
        self._is_active = False
        self._feedback: List[UserFeedback] = []
        self._adaptations: List[LearningAdaptation] = []
        self._interaction_patterns: Dict[str, Any] = {}
        self._learning_rate: float = 0.1
        self._adaptation_threshold: float = 0.5

        logger.info(f"AdaptiveLearningSystem initialiseret for {target_user}")

    def activate(self) -> bool:
        """Aktiver læringssystemet."""
        self._is_active = True
        logger.info("AdaptiveLearningSystem aktiveret")
        return True

    def deactivate(self) -> bool:
        """Deaktiver læringssystemet."""
        self._is_active = False
        logger.info("AdaptiveLearningSystem deaktiveret")
        return True

    def is_active(self) -> bool:
        """Check om systemet er aktivt."""
        return self._is_active

    def record_feedback(
        self,
        feedback_type: FeedbackType,
        target_component: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """Registrer bruger-feedback."""
        feedback = UserFeedback(
            feedback_type=feedback_type,
            target_component=target_component,
            value=value,
            context=context or {}
        )
        self._feedback.append(feedback)
        logger.info(f"Feedback registreret: {feedback_type.value} for {target_component}")
        return feedback

    def get_feedback(
        self,
        feedback_type: Optional[FeedbackType] = None,
        target_component: Optional[str] = None
    ) -> List[UserFeedback]:
        """Hent feedback med optional filtrering."""
        feedback = self._feedback

        if feedback_type:
            feedback = [f for f in feedback if f.feedback_type == feedback_type]
        if target_component:
            feedback = [f for f in feedback if f.target_component == target_component]

        return feedback

    def record_interaction(
        self,
        interaction_type: str,
        component: str,
        data: Dict[str, Any]
    ) -> None:
        """Registrer en interaktion for mønster-analyse."""
        key = f"{interaction_type}:{component}"
        if key not in self._interaction_patterns:
            self._interaction_patterns[key] = {
                "count": 0,
                "last_interaction": None,
                "data_samples": []
            }

        self._interaction_patterns[key]["count"] += 1
        self._interaction_patterns[key]["last_interaction"] = datetime.now(timezone.utc).isoformat()
        self._interaction_patterns[key]["data_samples"].append(data)

        # Keep only last 100 samples
        if len(self._interaction_patterns[key]["data_samples"]) > 100:
            self._interaction_patterns[key]["data_samples"] = \
                self._interaction_patterns[key]["data_samples"][-100:]

    def get_interaction_patterns(self) -> Dict[str, Any]:
        """Hent interaktionsmønstre."""
        return self._interaction_patterns.copy()

    def create_adaptation(
        self,
        adaptation_type: LearningAdaptationType,
        description: str,
        parameters_changed: Dict[str, Any]
    ) -> LearningAdaptation:
        """Opret en adaptiv tilpasning."""
        adaptation = LearningAdaptation(
            adaptation_type=adaptation_type,
            description=description,
            parameters_changed=parameters_changed
        )
        self._adaptations.append(adaptation)
        logger.info(f"Adaptation oprettet: {adaptation_type.value}")
        return adaptation

    def get_adaptations(
        self,
        adaptation_type: Optional[LearningAdaptationType] = None
    ) -> List[LearningAdaptation]:
        """Hent tilpasninger med optional filtrering."""
        adaptations = self._adaptations

        if adaptation_type:
            adaptations = [a for a in adaptations if a.adaptation_type == adaptation_type]

        return adaptations

    def analyze_and_adapt(self) -> List[LearningAdaptation]:
        """Analyser feedback og interaktioner, generer adaptationer."""
        new_adaptations = []

        # Analyze feedback patterns
        feedback_by_type = {}
        for fb in self._feedback:
            key = fb.feedback_type.value
            if key not in feedback_by_type:
                feedback_by_type[key] = []
            feedback_by_type[key].append(fb)

        # Generate adaptations based on patterns
        for fb_type, feedbacks in feedback_by_type.items():
            if len(feedbacks) >= 3:  # Need at least 3 feedbacks to identify pattern
                # Simplified pattern detection
                adaptation = self.create_adaptation(
                    adaptation_type=LearningAdaptationType.DISPLAY_OPTIMIZATION,
                    description=f"Adaptation based on {len(feedbacks)} {fb_type} feedbacks",
                    parameters_changed={"feedback_count": len(feedbacks)}
                )
                new_adaptations.append(adaptation)

        return new_adaptations

    def set_learning_rate(self, rate: float) -> None:
        """Sæt læringsrate (0.0 - 1.0)."""
        self._learning_rate = max(0.0, min(1.0, rate))

    def set_adaptation_threshold(self, threshold: float) -> None:
        """Sæt tærskel for adaptationer (0.0 - 1.0)."""
        self._adaptation_threshold = max(0.0, min(1.0, threshold))

    def get_status(self) -> Dict[str, Any]:
        """Hent status for læringssystemet."""
        return {
            "is_active": self._is_active,
            "target_user": self._target_user,
            "total_feedback": len(self._feedback),
            "total_adaptations": len(self._adaptations),
            "interaction_patterns_count": len(self._interaction_patterns),
            "learning_rate": self._learning_rate,
            "adaptation_threshold": self._adaptation_threshold
        }


# =============================================================================
# UNIFIED SUPER ADMIN CONTROL SYSTEM
# =============================================================================

class SuperAdminControlSystem:
    """
    Unified Super Admin Kontrol System.

    Kombinerer alle 4 komponenter:
    1. Masterminds Øje (Dashboard)
    2. Masterminds Stemme (Notifikationer)
    3. KV1NT Terminal Partner
    4. Organisk Læring
    """

    def __init__(self, admin_user: str = "rasmus_super_admin"):
        self._admin_user = admin_user
        self._is_active = False

        # Initialize all components
        self.dashboard = SuperAdminDashboard()
        self.notifications = IntelligentNotificationEngine()
        self.kv1nt = KV1NTTerminalPartner()
        self.learning = AdaptiveLearningSystem(target_user=admin_user)

        # CKC Folder Switcher (v1.3.5)
        self.folder_switcher = get_folder_switcher(admin_user)

        # Register default knowledge sources for KV1NT
        self.kv1nt.register_knowledge_source("historian_logs")
        self.kv1nt.register_knowledge_source("agent_journals")
        self.kv1nt.register_knowledge_source("knowledge_bank")
        self.kv1nt.register_knowledge_source("mastermind_meta_analysis")

        logger.info(f"SuperAdminControlSystem initialiseret for {admin_user}")

    def activate_all(self) -> Dict[str, bool]:
        """Aktiver alle komponenter."""
        results = {
            "dashboard": self.dashboard.activate(),
            "notifications": self.notifications.activate(),
            "kv1nt": self.kv1nt.activate(),
            "learning": self.learning.activate()
        }
        self._is_active = all(results.values())
        logger.info(f"SuperAdminControlSystem fuldt aktiveret: {self._is_active}")
        return results

    def deactivate_all(self) -> Dict[str, bool]:
        """Deaktiver alle komponenter."""
        results = {
            "dashboard": self.dashboard.deactivate(),
            "notifications": self.notifications.deactivate(),
            "kv1nt": self.kv1nt.deactivate(),
            "learning": self.learning.deactivate()
        }
        self._is_active = False
        return results

    def is_fully_active(self) -> bool:
        """Check om alle komponenter er aktive."""
        return (
            self.dashboard.is_active() and
            self.notifications.is_active() and
            self.kv1nt.is_active() and
            self.learning.is_active()
        )

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Hent komplet status for hele kontrolsystemet."""
        return {
            "admin_user": self._admin_user,
            "is_fully_active": self.is_fully_active(),
            "components": {
                "masterminds_eye": self.dashboard.get_global_status(),
                "masterminds_voice": self.notifications.get_status(),
                "kv1nt_partner": self.kv1nt.get_status(),
                "organic_learning": self.learning.get_status(),
                "folder_context": self.folder_switcher.get_status()  # v1.3.5
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # =========================================================================
    # CKC FOLDER SWITCHER METHODS (v1.3.5)
    # =========================================================================

    async def initialize_folder_switcher(self) -> None:
        """Initialiser folder switcher asynkront."""
        await self.folder_switcher.initialize()
        logger.info("CKC Folder Switcher initialiseret")

    async def switch_ckc_folder(
        self,
        folder_id: str,
        method: str = "api"
    ) -> Dict[str, Any]:
        """
        Skift CKC folder kontekst.

        Args:
            folder_id: ID på folder der skal skiftes til
            method: Switch metode (dropdown, sidebar, terminal, api)

        Returns:
            Event dictionary med resultat
        """
        event = await self.folder_switcher.switch_folder(folder_id, method)

        # Opdater dashboard zone hvis success
        if event.success:
            folders = await self.folder_switcher.list_folders()
            self.dashboard.update_zone_status(
                zone=DashboardZone.CKC_FOLDERS,
                status="active",
                metrics={
                    "current_folder": folder_id,
                    "total_folders": len(folders)
                },
                active_items=1
            )

        return event.to_dict()

    async def get_ckc_folder_context(self) -> Dict[str, Any]:
        """
        Hent nuværende CKC folder kontekst.

        Returns:
            Folder kontekst dictionary
        """
        context = await self.folder_switcher.get_current_context()
        return context.to_dict()

    async def list_ckc_folders(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List alle CKC folders.

        Args:
            category: Optional kategori filter

        Returns:
            Liste af folder dictionaries
        """
        from ..folder_context import FolderCategory

        category_enum = None
        if category:
            try:
                category_enum = FolderCategory(category)
            except ValueError:
                pass

        folders = await self.folder_switcher.list_folders(category_enum)
        return [f.to_dict() for f in folders]

    async def add_custom_ckc_folder(
        self,
        path: str,
        name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Tilføj en custom CKC folder.

        Args:
            path: Absolut sti til folder
            name: Visningsnavn

        Returns:
            Folder info eller None
        """
        folder = await self.folder_switcher.add_custom_folder(path, name)
        return folder.to_dict() if folder else None

    async def remove_custom_ckc_folder(self, folder_id: str) -> bool:
        """
        Fjern en custom CKC folder.

        Args:
            folder_id: Folder ID (skal starte med 'custom-')

        Returns:
            True hvis fjernet
        """
        return await self.folder_switcher.remove_custom_folder(folder_id)

    async def toggle_ckc_folder_favorite(self, folder_id: str) -> bool:
        """
        Toggle favorite status for en CKC folder.

        Args:
            folder_id: Folder ID

        Returns:
            True hvis tilføjet til favorites, False hvis fjernet
        """
        return await self.folder_switcher.toggle_favorite(folder_id)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_control_system_instance: Optional[SuperAdminControlSystem] = None


def create_super_admin_control_system(
    admin_user: str = "rasmus_super_admin"
) -> SuperAdminControlSystem:
    """Opret et nyt Super Admin Control System."""
    global _control_system_instance
    _control_system_instance = SuperAdminControlSystem(admin_user=admin_user)
    return _control_system_instance


def get_super_admin_control_system() -> SuperAdminControlSystem:
    """Hent det globale Super Admin Control System."""
    global _control_system_instance
    if _control_system_instance is None:
        _control_system_instance = SuperAdminControlSystem()
    return _control_system_instance


def create_dashboard() -> SuperAdminDashboard:
    """Opret et nyt Super Admin Dashboard."""
    return SuperAdminDashboard()


def create_notification_engine() -> IntelligentNotificationEngine:
    """Opret en ny Intelligent Notification Engine."""
    return IntelligentNotificationEngine()


def create_kv1nt_partner(interface: str = "terminal") -> KV1NTTerminalPartner:
    """Opret en ny KV1NT Terminal Partner."""
    return KV1NTTerminalPartner(interface=interface)


def create_adaptive_learning_system(
    target_user: str = "super_admin"
) -> AdaptiveLearningSystem:
    """Opret et nyt Adaptivt Læringssystem."""
    return AdaptiveLearningSystem(target_user=target_user)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "DashboardZone",
    "AlertLevel",
    "AlertCategory",
    "DeliveryChannel",
    "WorkflowRecommendationType",
    "KnowledgeQueryType",
    "FeedbackType",
    "LearningAdaptationType",

    # Data classes
    "ZoneStatus",
    "Alert",
    "NotificationPreference",
    "WorkflowRecommendation",
    "KnowledgeQuery",
    "KnowledgeResponse",
    "UserFeedback",
    "LearningAdaptation",

    # Main classes
    "SuperAdminDashboard",
    "IntelligentNotificationEngine",
    "KV1NTTerminalPartner",
    "AdaptiveLearningSystem",
    "SuperAdminControlSystem",

    # Factory functions
    "create_super_admin_control_system",
    "get_super_admin_control_system",
    "create_dashboard",
    "create_notification_engine",
    "create_kv1nt_partner",
    "create_adaptive_learning_system",
]
