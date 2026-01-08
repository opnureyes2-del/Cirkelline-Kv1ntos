"""
CKC Dashboard - Visual Status System
=====================================

Visual overvågningssystem med:
- StatusDot (blå/grøn/gul/rød)
- Dashboard oversigt
- Akut notifikationsside
- Real-time status opdatering

Farvekoder:
    BLUE   - Alt er godt, stabilt, valideret
    GREEN  - Aktivt og funktionelt, i brug
    YELLOW - Advarsel, mindre problem
    RED    - Kritisk fejl, sikkerhedsproblem
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import asyncio
import uuid
from collections import defaultdict

from cirkelline.config import logger
from .learning_rooms import RoomStatus, get_room_manager


class StatusLevel(Enum):
    """Status niveau."""
    BLUE = "blue"      # Alt er godt
    GREEN = "green"    # Aktivt
    YELLOW = "yellow"  # Advarsel
    RED = "red"        # Kritisk


@dataclass
class StatusDot:
    """
    Visual status indikator.

    Repræsenterer status for et system/komponent med en farvet prik.
    """
    id: str
    name: str
    status: StatusLevel
    description: str = ""
    last_updated: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    pulse: bool = False  # True = animeret puls

    @property
    def color(self) -> str:
        """CSS farve for status."""
        colors = {
            StatusLevel.BLUE: "#3498db",
            StatusLevel.GREEN: "#2ecc71",
            StatusLevel.YELLOW: "#f1c40f",
            StatusLevel.RED: "#e74c3c"
        }
        return colors.get(self.status, "#95a5a6")

    @property
    def label(self) -> str:
        """Dansk label for status."""
        labels = {
            StatusLevel.BLUE: "Stabil",
            StatusLevel.GREEN: "Aktiv",
            StatusLevel.YELLOW: "Advarsel",
            StatusLevel.RED: "Kritisk"
        }
        return labels.get(self.status, "Ukendt")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "color": self.color,
            "label": self.label,
            "description": self.description,
            "last_updated": self.last_updated.isoformat(),
            "details": self.details,
            "pulse": self.pulse
        }

    def to_html(self) -> str:
        """Generer HTML for status dot."""
        pulse_class = "pulse" if self.pulse else ""
        return f'''
        <div class="status-dot-container">
            <div class="status-dot {pulse_class}" style="background-color: {self.color};"
                 title="{self.name}: {self.label}">
            </div>
            <span class="status-label">{self.name}</span>
        </div>
        '''


@dataclass
class AcuteNotification:
    """En akut notifikation der kræver opmærksomhed."""
    id: str
    message: str
    severity: str  # warning, critical, error
    source: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message": self.message,
            "severity": self.severity,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "details": self.details,
            "actions": self.actions
        }


class AcuteNotificationPage:
    """
    Akut Notifikationsside

    Viser alle kritiske og advarsels-status systemer.
    Kræver brugerens opmærksomhed og handling.
    """

    def __init__(self):
        self._notifications: Dict[str, AcuteNotification] = {}
        self._notification_history: List[str] = []  # notification IDs
        self._observers: List[Callable] = []

        logger.info("AcuteNotificationPage initialized")

    async def add_notification(
        self,
        message: str,
        severity: str,
        source: str,
        details: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, str]]] = None
    ) -> AcuteNotification:
        """Tilføj en akut notifikation."""
        notif_id = f"acute_{uuid.uuid4().hex[:8]}"

        notification = AcuteNotification(
            id=notif_id,
            message=message,
            severity=severity,
            source=source,
            timestamp=datetime.utcnow(),
            details=details or {},
            actions=actions or []
        )

        self._notifications[notif_id] = notification
        self._notification_history.append(notif_id)

        # Notify observers
        await self._notify_observers("new_notification", notification)

        logger.warning(f"Acute notification: [{severity}] {message} from {source}")
        return notification

    async def acknowledge_notification(
        self,
        notification_id: str,
        acknowledged_by: str
    ) -> bool:
        """Kvitter for en notifikation."""
        notification = self._notifications.get(notification_id)
        if not notification:
            return False

        notification.acknowledged = True
        notification.acknowledged_by = acknowledged_by
        notification.acknowledged_at = datetime.utcnow()

        logger.info(f"Notification {notification_id} acknowledged by {acknowledged_by}")
        return True

    async def get_active_notifications(self) -> List[AcuteNotification]:
        """Hent alle aktive (ikke-kvitterede) notifikationer."""
        return [
            n for n in self._notifications.values()
            if not n.acknowledged
        ]

    async def get_notifications_by_severity(
        self,
        severity: str
    ) -> List[AcuteNotification]:
        """Hent notifikationer efter alvorlighed."""
        return [
            n for n in self._notifications.values()
            if n.severity == severity and not n.acknowledged
        ]

    async def get_all_notifications(
        self,
        include_acknowledged: bool = False,
        limit: int = 100
    ) -> List[AcuteNotification]:
        """Hent alle notifikationer."""
        notifications = list(self._notifications.values())
        if not include_acknowledged:
            notifications = [n for n in notifications if not n.acknowledged]

        # Sort by timestamp, newest first
        notifications.sort(key=lambda n: n.timestamp, reverse=True)
        return notifications[:limit]

    def add_observer(self, callback: Callable) -> None:
        """Tilføj observer for notifikationer."""
        self._observers.append(callback)

    async def _notify_observers(
        self,
        event_type: str,
        data: Any
    ) -> None:
        """Notify alle observers."""
        for observer in self._observers:
            try:
                if asyncio.iscoroutinefunction(observer):
                    await observer(event_type, data)
                else:
                    observer(event_type, data)
            except Exception as e:
                logger.error(f"Observer notification failed: {e}")

    async def get_page_data(self) -> Dict[str, Any]:
        """Hent data til akut notifikationsside."""
        active = await self.get_active_notifications()
        critical = [n for n in active if n.severity == "critical"]
        warnings = [n for n in active if n.severity == "warning"]

        return {
            "title": "Akutte Notifikationer",
            "total_active": len(active),
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "notifications": {
                "critical": [n.to_dict() for n in critical],
                "warning": [n.to_dict() for n in warnings],
                "other": [
                    n.to_dict() for n in active
                    if n.severity not in ["critical", "warning"]
                ]
            },
            "requires_action": len(critical) > 0,
            "generated_at": datetime.utcnow().isoformat()
        }


class DashboardManager:
    """
    Central Dashboard Manager

    Koordinerer alle status dots og giver samlet overblik.
    """

    def __init__(self):
        self._status_dots: Dict[str, StatusDot] = {}
        self._acute_page = AcuteNotificationPage()
        self._update_callbacks: List[Callable] = []

        # System metrics
        self._metrics = {
            "uptime_start": datetime.utcnow(),
            "total_updates": 0,
            "alerts_triggered": 0
        }

        logger.info("DashboardManager initialized")

    async def register_component(
        self,
        component_id: str,
        name: str,
        initial_status: StatusLevel = StatusLevel.BLUE,
        description: str = ""
    ) -> StatusDot:
        """Registrer en komponent i dashboard."""
        dot = StatusDot(
            id=component_id,
            name=name,
            status=initial_status,
            description=description
        )
        self._status_dots[component_id] = dot

        logger.debug(f"Component registered: {name} ({component_id})")
        return dot

    async def set_component_status(
        self,
        component_id: str,
        status: StatusLevel,
        description: str = ""
    ) -> bool:
        """
        Sæt status for en komponent (opretter hvis den ikke findes).

        Bruges typisk af emergency stop og system events.

        Args:
            component_id: Unik komponent ID
            status: Nyt status niveau
            description: Beskrivelse af status ændring

        Returns:
            True hvis succesfuldt
        """
        if component_id not in self._status_dots:
            await self.register_component(
                component_id,
                component_id.replace("_", " ").title(),
                status,
                description
            )
            return True

        return await self.update_status(component_id, status, {"description": description})

    async def update_status(
        self,
        component_id: str,
        status: StatusLevel,
        details: Optional[Dict[str, Any]] = None,
        pulse: bool = False
    ) -> bool:
        """Opdater status for en komponent."""
        dot = self._status_dots.get(component_id)
        if not dot:
            return False

        old_status = dot.status
        dot.status = status
        dot.last_updated = datetime.utcnow()
        dot.pulse = pulse

        if details:
            dot.details.update(details)

        self._metrics["total_updates"] += 1

        # Check for status degradation
        if self._is_degradation(old_status, status):
            await self._handle_degradation(dot, old_status, status)

        # Notify callbacks
        await self._notify_updates(dot)

        return True

    def _is_degradation(
        self,
        old_status: StatusLevel,
        new_status: StatusLevel
    ) -> bool:
        """Check om status er forværret."""
        priority = {
            StatusLevel.BLUE: 0,
            StatusLevel.GREEN: 1,
            StatusLevel.YELLOW: 2,
            StatusLevel.RED: 3
        }
        return priority.get(new_status, 0) > priority.get(old_status, 0)

    async def _handle_degradation(
        self,
        dot: StatusDot,
        old_status: StatusLevel,
        new_status: StatusLevel
    ) -> None:
        """Håndter status forværring."""
        if new_status == StatusLevel.RED:
            severity = "critical"
        elif new_status == StatusLevel.YELLOW:
            severity = "warning"
        else:
            severity = "info"

        await self._acute_page.add_notification(
            message=f"{dot.name} status ændret fra {old_status.value} til {new_status.value}",
            severity=severity,
            source=dot.id,
            details={"old_status": old_status.value, "new_status": new_status.value}
        )

        self._metrics["alerts_triggered"] += 1

    async def get_status_dot(
        self,
        component_id: str
    ) -> Optional[StatusDot]:
        """Hent status dot for en komponent."""
        return self._status_dots.get(component_id)

    async def get_all_status_dots(self) -> List[StatusDot]:
        """Hent alle status dots."""
        return list(self._status_dots.values())

    async def get_status_overview(self) -> Dict[str, Any]:
        """Hent samlet status oversigt."""
        dots = list(self._status_dots.values())

        status_counts = defaultdict(int)
        for dot in dots:
            status_counts[dot.status.value] += 1

        critical_components = [d for d in dots if d.status == StatusLevel.RED]
        warning_components = [d for d in dots if d.status == StatusLevel.YELLOW]

        # Calculate overall status
        if critical_components:
            overall = StatusLevel.RED
        elif warning_components:
            overall = StatusLevel.YELLOW
        elif any(d.status == StatusLevel.GREEN for d in dots):
            overall = StatusLevel.GREEN
        else:
            overall = StatusLevel.BLUE

        return {
            "overall_status": overall.value,
            "total_components": len(dots),
            "status_counts": dict(status_counts),
            "critical_components": [d.to_dict() for d in critical_components],
            "warning_components": [d.to_dict() for d in warning_components],
            "uptime": str(datetime.utcnow() - self._metrics["uptime_start"]),
            "total_updates": self._metrics["total_updates"],
            "alerts_triggered": self._metrics["alerts_triggered"],
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Hent komplet dashboard data."""
        overview = await self.get_status_overview()
        acute_data = await self._acute_page.get_page_data()

        # Get learning room status from manager
        room_manager = get_room_manager()
        room_status = await room_manager.get_status_overview()

        return {
            "title": "CKC Dashboard",
            "overview": overview,
            "components": [d.to_dict() for d in self._status_dots.values()],
            "learning_rooms": room_status,
            "acute_notifications": acute_data,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def get_health_check(self) -> Dict[str, Any]:
        """Hent system health check."""
        dots = list(self._status_dots.values())

        healthy = all(d.status in [StatusLevel.BLUE, StatusLevel.GREEN] for d in dots)
        critical = any(d.status == StatusLevel.RED for d in dots)

        return {
            "healthy": healthy,
            "critical": critical,
            "components_checked": len(dots),
            "status": "healthy" if healthy else ("critical" if critical else "degraded"),
            "checked_at": datetime.utcnow().isoformat()
        }

    def add_update_callback(self, callback: Callable) -> None:
        """Tilføj callback for status opdateringer."""
        self._update_callbacks.append(callback)

    async def _notify_updates(self, dot: StatusDot) -> None:
        """Notify alle callbacks om opdatering."""
        for callback in self._update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(dot)
                else:
                    callback(dot)
            except Exception as e:
                logger.error(f"Update callback failed: {e}")

    @property
    def acute_notifications(self) -> AcuteNotificationPage:
        """Hent akut notifikationsside."""
        return self._acute_page

    async def generate_html_dashboard(self) -> str:
        """Generer HTML for dashboard."""
        data = await self.get_dashboard_data()
        overview = data["overview"]

        # Generate status dots HTML
        dots_html = ""
        for dot_data in data["components"]:
            status = dot_data["status"]
            color = dot_data["color"]
            pulse = "pulse" if dot_data.get("pulse") else ""
            dots_html += f'''
            <div class="status-item">
                <div class="status-dot {pulse}" style="background-color: {color}"></div>
                <span class="status-name">{dot_data["name"]}</span>
                <span class="status-label">{dot_data["label"]}</span>
            </div>
            '''

        # Generate acute notifications
        acute_html = ""
        if data["acute_notifications"]["total_active"] > 0:
            acute_html = f'''
            <div class="acute-section">
                <h3>Akutte Notifikationer ({data["acute_notifications"]["total_active"]})</h3>
                <div class="acute-list">
            '''
            for notif in data["acute_notifications"]["notifications"].get("critical", []):
                acute_html += f'''
                <div class="acute-item critical">
                    <span class="severity">KRITISK</span>
                    <span class="message">{notif["message"]}</span>
                    <span class="source">{notif["source"]}</span>
                </div>
                '''
            for notif in data["acute_notifications"]["notifications"].get("warning", []):
                acute_html += f'''
                <div class="acute-item warning">
                    <span class="severity">ADVARSEL</span>
                    <span class="message">{notif["message"]}</span>
                    <span class="source">{notif["source"]}</span>
                </div>
                '''
            acute_html += "</div></div>"

        return f'''
<!DOCTYPE html>
<html lang="da">
<head>
    <meta charset="UTF-8">
    <title>CKC Dashboard</title>
    <style>
        body {{ font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #3498db; }}
        .overall-status {{ font-size: 24px; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }}
        .overall-status.blue {{ background: linear-gradient(135deg, #3498db, #2980b9); }}
        .overall-status.green {{ background: linear-gradient(135deg, #2ecc71, #27ae60); }}
        .overall-status.yellow {{ background: linear-gradient(135deg, #f1c40f, #f39c12); color: #333; }}
        .overall-status.red {{ background: linear-gradient(135deg, #e74c3c, #c0392b); }}
        .status-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }}
        .status-item {{ background: #16213e; padding: 15px; border-radius: 8px; display: flex; align-items: center; gap: 10px; }}
        .status-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
        .status-dot.pulse {{ animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        .status-name {{ flex: 1; font-weight: 500; }}
        .status-label {{ font-size: 12px; opacity: 0.7; }}
        .acute-section {{ background: #2c1810; padding: 20px; border-radius: 10px; margin-top: 20px; border: 2px solid #e74c3c; }}
        .acute-item {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .acute-item.critical {{ background: #4a1a1a; }}
        .acute-item.warning {{ background: #4a3a1a; }}
        .severity {{ font-weight: bold; margin-right: 10px; }}
        .message {{ flex: 1; }}
        .source {{ font-size: 12px; opacity: 0.7; }}
        .metrics {{ display: flex; gap: 30px; justify-content: center; margin: 20px 0; }}
        .metric {{ text-align: center; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #3498db; }}
        .metric-label {{ font-size: 12px; opacity: 0.7; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>CKC Dashboard</h1>
            <p>Cirkelline Kreativ Koordinator - Status Oversigt</p>
        </div>

        <div class="overall-status {overview['overall_status']}">
            System Status: {overview['overall_status'].upper()}
        </div>

        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{overview['total_components']}</div>
                <div class="metric-label">Komponenter</div>
            </div>
            <div class="metric">
                <div class="metric-value">{overview['status_counts'].get('blue', 0) + overview['status_counts'].get('green', 0)}</div>
                <div class="metric-label">Sunde</div>
            </div>
            <div class="metric">
                <div class="metric-value">{overview['alerts_triggered']}</div>
                <div class="metric-label">Alerts</div>
            </div>
        </div>

        <h2>Komponent Status</h2>
        <div class="status-grid">
            {dots_html}
        </div>

        {acute_html}

        <p style="text-align: center; margin-top: 30px; opacity: 0.5;">
            Opdateret: {data['generated_at']}
        </p>
    </div>
</body>
</html>
'''


# ═══════════════════════════════════════════════════════════════
# SINGLETON & CONVENIENCE
# ═══════════════════════════════════════════════════════════════

_dashboard_manager: Optional[DashboardManager] = None


def get_dashboard_manager() -> DashboardManager:
    """Hent singleton DashboardManager."""
    global _dashboard_manager
    if _dashboard_manager is None:
        _dashboard_manager = DashboardManager()
    return _dashboard_manager


async def register_component(
    component_id: str,
    name: str,
    **kwargs
) -> StatusDot:
    """Convenience function til at registrere komponent."""
    return await get_dashboard_manager().register_component(component_id, name, **kwargs)


async def update_component_status(
    component_id: str,
    status: StatusLevel,
    **kwargs
) -> bool:
    """Convenience function til at opdatere status."""
    return await get_dashboard_manager().update_status(component_id, status, **kwargs)


async def get_dashboard_overview() -> Dict[str, Any]:
    """Convenience function til at hente oversigt."""
    return await get_dashboard_manager().get_status_overview()


logger.info("CKC Dashboard module loaded - Visual status system ready")
