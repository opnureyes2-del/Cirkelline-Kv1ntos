"""
Monitor Agent
=============
System health monitoring and metrics aggregation.

Responsibilities:
- Monitor all services health (DB, Redis, APIs)
- Aggregate metrics from agents
- Send alerts via EventBus
- Report to admin dashboard
- Track SLA compliance
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

from cirkelline.headquarters.event_bus import (
    EventBus,
    Event,
    EventType,
    get_event_bus,
)
from cirkelline.headquarters.shared_memory import (
    SharedMemory,
    AgentState,
    get_shared_memory,
)
from cirkelline.context.system_status import (
    SystemStatus,
    HealthStatus,
    ServiceHealth,
    get_system_status,
)
from cirkelline.context.agent_protocol import (
    AgentDescriptor,
    AgentCapability,
    get_capability_registry,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS & ALERTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MetricPoint:
    """A single metric measurement."""
    name: str
    value: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class Alert:
    """System alert."""
    alert_id: str
    severity: str  # info, warning, error, critical
    title: str
    message: str
    source: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved: bool = False
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MONITOR AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class MonitorAgent:
    """
    Monitors system health and aggregates metrics.

    Runs periodic health checks, collects metrics from agents,
    and sends alerts when thresholds are breached.
    """

    AGENT_ID = "hq:monitor"
    AGENT_NAME = "System Monitor"

    # Health check interval in seconds
    CHECK_INTERVAL = 30

    # Alert thresholds
    THRESHOLDS = {
        "latency_ms": {"warning": 500, "critical": 2000},
        "error_rate": {"warning": 0.05, "critical": 0.10},
        "agent_offline_minutes": {"warning": 2, "critical": 5},
    }

    def __init__(self):
        self._event_bus: Optional[EventBus] = None
        self._memory: Optional[SharedMemory] = None
        self._system_status: Optional[SystemStatus] = None
        self._running = False

        # Metrics storage (in-memory, rolling window)
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._alerts: Dict[str, Alert] = {}

        # Last check timestamps
        self._last_health_check: Optional[datetime] = None
        self._last_metrics_report: Optional[datetime] = None

    async def initialize(self) -> bool:
        """Initialize connections."""
        try:
            self._event_bus = get_event_bus()
            self._memory = get_shared_memory()
            self._system_status = get_system_status()

            # Register self
            registry = get_capability_registry()
            registry.register(AgentDescriptor(
                agent_id=self.AGENT_ID,
                name=self.AGENT_NAME,
                role="System health monitoring",
                capabilities=[],
                max_concurrent_tasks=1,
            ))

            # Subscribe to events
            self._event_bus.subscribe(EventType.AGENT_HEARTBEAT, self._handle_heartbeat)
            self._event_bus.subscribe(EventType.AGENT_ERROR, self._handle_agent_error)
            self._event_bus.subscribe(EventType.SYSTEM_METRIC, self._handle_metric)

            logger.info(f"MonitorAgent initialized: {self.AGENT_ID}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MonitorAgent: {e}")
            return False

    async def start(self) -> None:
        """Start the monitoring loop."""
        self._running = True
        logger.info("MonitorAgent started")

        while self._running:
            try:
                await self._run_health_checks()
                await self._check_agent_health()
                await self._process_alerts()
                await self._cleanup_old_metrics()

                await asyncio.sleep(self.CHECK_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        logger.info("MonitorAgent stopped")

    # ═══════════════════════════════════════════════════════════════════════════
    # HEALTH CHECKS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _run_health_checks(self) -> None:
        """Run all system health checks."""
        self._last_health_check = datetime.utcnow()

        # Check all services
        health = await self._system_status.check_all()

        # Record metrics
        for service_name, service_health in health.get("services", {}).items():
            self._record_metric(
                name=f"service.{service_name}.status",
                value=1.0 if service_health.get("status") == "healthy" else 0.0,
                tags={"service": service_name},
            )

            if service_health.get("latency_ms"):
                self._record_metric(
                    name=f"service.{service_name}.latency",
                    value=float(service_health["latency_ms"]),
                    unit="ms",
                    tags={"service": service_name},
                )

        # Check for unhealthy services
        overall = health.get("overall", "unknown")
        if overall == "unhealthy":
            await self._create_alert(
                severity="critical",
                title="System Health Critical",
                message=f"Overall system status: {overall}",
                source="health_check",
            )
        elif overall == "degraded":
            await self._create_alert(
                severity="warning",
                title="System Health Degraded",
                message=f"Some services are degraded",
                source="health_check",
            )

        # Publish health event
        await self._event_bus.publish(Event(
            event_type=EventType.SYSTEM_HEALTH,
            source=self.AGENT_ID,
            payload=health,
        ))

    async def _check_agent_health(self) -> None:
        """Check health of all registered agents."""
        registry = get_capability_registry()
        active_agents = await self._memory.get_active_agents(timeout_seconds=120)

        active_ids = {a.agent_id for a in active_agents}

        for agent in registry.get_all_agents():
            if agent.agent_id.startswith("hq:"):
                continue  # Skip HQ agents

            if agent.agent_id not in active_ids:
                # Agent hasn't sent heartbeat
                await self._create_alert(
                    severity="warning",
                    title=f"Agent Offline: {agent.name}",
                    message=f"Agent {agent.agent_id} has not sent heartbeat",
                    source="agent_health",
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # METRICS
    # ═══════════════════════════════════════════════════════════════════════════

    def _record_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a metric point."""
        point = MetricPoint(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {},
        )
        self._metrics[name].append(point)

        # Keep only last 1000 points per metric
        if len(self._metrics[name]) > 1000:
            self._metrics[name] = self._metrics[name][-1000:]

    def get_metric_stats(
        self,
        name: str,
        window_minutes: int = 5,
    ) -> Dict[str, float]:
        """Get statistics for a metric over a time window."""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        points = [
            p for p in self._metrics.get(name, [])
            if datetime.fromisoformat(p.timestamp) > cutoff
        ]

        if not points:
            return {}

        values = [p.value for p in points]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
        }

    async def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than 1 hour."""
        cutoff = datetime.utcnow() - timedelta(hours=1)

        for name in list(self._metrics.keys()):
            self._metrics[name] = [
                p for p in self._metrics[name]
                if datetime.fromisoformat(p.timestamp) > cutoff
            ]

    # ═══════════════════════════════════════════════════════════════════════════
    # ALERTS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _create_alert(
        self,
        severity: str,
        title: str,
        message: str,
        source: str,
    ) -> Alert:
        """Create and publish an alert."""
        import uuid
        alert_id = f"alert-{uuid.uuid4().hex[:8]}"

        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            message=message,
            source=source,
        )

        self._alerts[alert_id] = alert

        # Publish alert event
        await self._event_bus.publish(Event(
            event_type=EventType.SYSTEM_ALERT,
            source=self.AGENT_ID,
            payload=alert.to_dict(),
            priority=3 if severity == "critical" else 2,
        ))

        logger.warning(f"Alert created: [{severity}] {title}")
        return alert

    async def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        if alert_id in self._alerts:
            self._alerts[alert_id].resolved = True
            self._alerts[alert_id].resolved_at = datetime.utcnow().isoformat()
            return True
        return False

    async def _process_alerts(self) -> None:
        """Process and auto-resolve stale alerts."""
        now = datetime.utcnow()

        for alert_id, alert in list(self._alerts.items()):
            if alert.resolved:
                # Remove resolved alerts after 1 hour
                resolved_at = datetime.fromisoformat(alert.resolved_at)
                if now - resolved_at > timedelta(hours=1):
                    del self._alerts[alert_id]

    def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts."""
        return [a for a in self._alerts.values() if not a.resolved]

    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _handle_heartbeat(self, event: Event) -> None:
        """Handle agent heartbeat events."""
        agent_id = event.source
        self._record_metric(
            name="agent.heartbeat",
            value=1.0,
            tags={"agent_id": agent_id},
        )

    async def _handle_agent_error(self, event: Event) -> None:
        """Handle agent error events."""
        agent_id = event.source
        error = event.payload.get("error", "Unknown error")

        await self._create_alert(
            severity="error",
            title=f"Agent Error: {agent_id}",
            message=error,
            source=agent_id,
        )

    async def _handle_metric(self, event: Event) -> None:
        """Handle incoming metric events."""
        payload = event.payload
        self._record_metric(
            name=payload.get("name", "unknown"),
            value=float(payload.get("value", 0)),
            unit=payload.get("unit", ""),
            tags=payload.get("tags", {}),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # REPORTING
    # ═══════════════════════════════════════════════════════════════════════════

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for admin dashboard."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "alerts": {
                "total": len(self._alerts),
                "active": len(self.get_active_alerts()),
                "by_severity": {
                    "critical": len([a for a in self._alerts.values() if a.severity == "critical" and not a.resolved]),
                    "error": len([a for a in self._alerts.values() if a.severity == "error" and not a.resolved]),
                    "warning": len([a for a in self._alerts.values() if a.severity == "warning" and not a.resolved]),
                },
            },
            "metrics_summary": {
                name: self.get_metric_stats(name)
                for name in list(self._metrics.keys())[:20]  # Top 20 metrics
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_monitor_instance: Optional[MonitorAgent] = None


def get_monitor() -> MonitorAgent:
    """Get the singleton MonitorAgent instance."""
    global _monitor_instance

    if _monitor_instance is None:
        _monitor_instance = MonitorAgent()

    return _monitor_instance


async def init_monitor() -> MonitorAgent:
    """Initialize and start the monitor."""
    monitor = get_monitor()
    await monitor.initialize()
    return monitor
