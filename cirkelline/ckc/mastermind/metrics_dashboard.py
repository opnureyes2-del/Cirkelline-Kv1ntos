"""
=============================================================================
                        MASTERMIND METRICS DASHBOARD
                              (DEL AH)
=============================================================================

Aggregerer og visualiserer metrics fra alle MASTERMIND komponenter.
Giver real-time monitoring, alerting og dashboard data export.

Metrics Kilder:
    - CacheMetrics: Hit rates, evictions, memory usage
    - QueryMetrics: Query latency, cache hits, optimization stats
    - EventMetrics: Event throughput, delivery rates, failures
    - PoolMetrics: Connection usage, availability, health

Features:
    - Unified metrics aggregation
    - Real-time streaming via SSE
    - Threshold-based alerting
    - Time-series data collection
    - Dashboard JSON export
    - Prometheus-compatible output

Forfatter: Cirkelline Team
Version: 1.0.0
=============================================================================
"""

from __future__ import annotations

import asyncio
import json
import logging
import statistics
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class MetricType(Enum):
    """Type of metric being collected."""

    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Statistical summary
    RATE = "rate"  # Rate of change per second


class MetricSource(Enum):
    """Source system for the metric."""

    CACHE = "cache"
    QUERY = "query"
    EVENTS = "events"
    CONNECTIONS = "connections"
    SYSTEM = "system"
    CUSTOM = "custom"


class AlertSeverity(Enum):
    """Severity level for alerts."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertState(Enum):
    """Current state of an alert."""

    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"


class DashboardLayout(Enum):
    """Dashboard layout presets."""

    OVERVIEW = "overview"
    PERFORMANCE = "performance"
    HEALTH = "health"
    CUSTOM = "custom"


class TimeRange(Enum):
    """Predefined time ranges for queries."""

    LAST_MINUTE = "1m"
    LAST_5_MINUTES = "5m"
    LAST_15_MINUTES = "15m"
    LAST_HOUR = "1h"
    LAST_6_HOURS = "6h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class MetricsDashboardConfig:
    """Configuration for the metrics dashboard."""

    # Collection settings
    collection_interval: float = 5.0
    retention_period: timedelta = timedelta(hours=24)
    max_datapoints: int = 10000
    aggregate_older_than: timedelta = timedelta(minutes=5)

    # Alert settings
    alert_check_interval: float = 10.0
    alert_cooldown: timedelta = timedelta(minutes=5)
    max_active_alerts: int = 100

    # Streaming settings
    stream_buffer_size: int = 100
    stream_interval: float = 1.0

    # Export settings
    prometheus_enabled: bool = True
    json_export_enabled: bool = True

    # Dashboard settings
    default_layout: DashboardLayout = DashboardLayout.OVERVIEW
    auto_refresh_interval: float = 5.0


@dataclass
class MetricDatapoint:
    """A single datapoint for a metric."""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    source: MetricSource = MetricSource.CUSTOM

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "labels": self.labels,
            "source": self.source.value,
        }


@dataclass
class MetricDefinition:
    """Definition of a metric."""

    name: str
    metric_type: MetricType
    description: str
    unit: str = ""
    source: MetricSource = MetricSource.CUSTOM
    labels: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "description": self.description,
            "unit": self.unit,
            "source": self.source.value,
            "labels": self.labels,
        }


@dataclass
class MetricSeries:
    """Time series of metric datapoints."""

    definition: MetricDefinition
    datapoints: deque = field(default_factory=lambda: deque(maxlen=10000))
    last_value: Optional[float] = None
    last_updated: Optional[datetime] = None

    def add(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Add a datapoint to the series."""
        now = datetime.now()
        self.datapoints.append(
            MetricDatapoint(
                timestamp=now,
                value=value,
                labels=labels or {},
                source=self.definition.source,
            )
        )
        self.last_value = value
        self.last_updated = now

    def get_values(
        self, since: Optional[datetime] = None, limit: Optional[int] = None
    ) -> List[MetricDatapoint]:
        """Get datapoints, optionally filtered by time."""
        result = list(self.datapoints)
        if since:
            result = [dp for dp in result if dp.timestamp >= since]
        if limit:
            result = result[-limit:]
        return result

    def get_statistics(self, since: Optional[datetime] = None) -> Dict[str, float]:
        """Calculate statistics for the series."""
        values = [dp.value for dp in self.get_values(since)]
        if not values:
            return {"count": 0, "mean": 0, "min": 0, "max": 0, "stddev": 0}

        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0,
        }


@dataclass
class AlertRule:
    """Definition of an alert rule."""

    id: str
    name: str
    metric_name: str
    condition: str  # e.g., "> 90", "< 10", "== 0"
    threshold: float
    severity: AlertSeverity
    duration: timedelta = field(default_factory=lambda: timedelta(minutes=1))
    description: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "metric_name": self.metric_name,
            "condition": self.condition,
            "threshold": self.threshold,
            "severity": self.severity.value,
            "duration_seconds": self.duration.total_seconds(),
            "description": self.description,
            "labels": self.labels,
            "enabled": self.enabled,
        }


@dataclass
class Alert:
    """An active or resolved alert."""

    id: str
    rule: AlertRule
    state: AlertState
    started_at: datetime
    resolved_at: Optional[datetime] = None
    value: float = 0.0
    message: str = ""
    annotations: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule.id,
            "rule_name": self.rule.name,
            "state": self.state.value,
            "severity": self.rule.severity.value,
            "started_at": self.started_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "value": self.value,
            "message": self.message,
            "annotations": self.annotations,
        }


@dataclass
class DashboardPanel:
    """Definition of a dashboard panel."""

    id: str
    title: str
    metric_names: List[str]
    panel_type: str = "timeseries"  # timeseries, gauge, stat, table
    position: Tuple[int, int] = (0, 0)  # (row, col)
    size: Tuple[int, int] = (1, 1)  # (width, height)
    options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "metrics": self.metric_names,
            "type": self.panel_type,
            "position": {"row": self.position[0], "col": self.position[1]},
            "size": {"width": self.size[0], "height": self.size[1]},
            "options": self.options,
        }


@dataclass
class Dashboard:
    """Complete dashboard configuration."""

    id: str
    name: str
    layout: DashboardLayout
    panels: List[DashboardPanel] = field(default_factory=list)
    refresh_interval: float = 5.0
    time_range: TimeRange = TimeRange.LAST_HOUR
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "layout": self.layout.value,
            "panels": [p.to_dict() for p in self.panels],
            "refresh_interval": self.refresh_interval,
            "time_range": self.time_range.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SystemHealth:
    """Overall system health status."""

    status: str  # healthy, degraded, unhealthy
    score: float  # 0-100
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_check: datetime = field(default_factory=datetime.now)
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "score": self.score,
            "components": self.components,
            "last_check": self.last_check.isoformat(),
            "issues": self.issues,
        }


# =============================================================================
# METRICS COLLECTOR
# =============================================================================


class MetricsCollector:
    """
    Collects and aggregates metrics from various sources.
    """

    def __init__(self, config: Optional[MetricsDashboardConfig] = None):
        self.config = config or MetricsDashboardConfig()
        self._series: Dict[str, MetricSeries] = {}
        self._definitions: Dict[str, MetricDefinition] = {}
        self._collectors: Dict[str, Callable[[], Dict[str, float]]] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None

        # Register default metrics
        self._register_default_metrics()

    def _register_default_metrics(self) -> None:
        """Register default system metrics."""
        defaults = [
            MetricDefinition(
                name="system_uptime_seconds",
                metric_type=MetricType.COUNTER,
                description="System uptime in seconds",
                unit="seconds",
                source=MetricSource.SYSTEM,
            ),
            MetricDefinition(
                name="collection_duration_ms",
                metric_type=MetricType.GAUGE,
                description="Time to collect metrics",
                unit="milliseconds",
                source=MetricSource.SYSTEM,
            ),
            MetricDefinition(
                name="active_alerts_count",
                metric_type=MetricType.GAUGE,
                description="Number of active alerts",
                source=MetricSource.SYSTEM,
            ),
        ]
        for definition in defaults:
            self.register_metric(definition)

    def register_metric(self, definition: MetricDefinition) -> None:
        """Register a new metric definition."""
        self._definitions[definition.name] = definition
        if definition.name not in self._series:
            self._series[definition.name] = MetricSeries(definition=definition)

    def register_collector(
        self, name: str, collector: Callable[[], Dict[str, float]]
    ) -> None:
        """Register a metrics collector function."""
        self._collectors[name] = collector

    def record(
        self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric value."""
        if metric_name in self._series:
            self._series[metric_name].add(value, labels)
        else:
            logger.warning(f"Unknown metric: {metric_name}")

    async def collect_all(self) -> Dict[str, float]:
        """Collect metrics from all registered collectors."""
        start = time.time()
        results: Dict[str, float] = {}

        for name, collector in self._collectors.items():
            try:
                if asyncio.iscoroutinefunction(collector):
                    metrics = await collector()
                else:
                    metrics = collector()
                results.update(metrics)

                for metric_name, value in metrics.items():
                    self.record(metric_name, value)
            except Exception as e:
                logger.error(f"Error collecting metrics from {name}: {e}")

        duration = (time.time() - start) * 1000
        self.record("collection_duration_ms", duration)
        return results

    async def start(self) -> None:
        """Start background collection."""
        if self._running:
            return

        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("MetricsCollector started")

    async def stop(self) -> None:
        """Stop background collection."""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("MetricsCollector stopped")

    async def _collection_loop(self) -> None:
        """Background collection loop."""
        while self._running:
            try:
                await self.collect_all()
                await asyncio.sleep(self.config.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Collection loop error: {e}")
                await asyncio.sleep(1)

    def get_metric(self, name: str) -> Optional[MetricSeries]:
        """Get a metric series by name."""
        return self._series.get(name)

    def get_all_metrics(self) -> Dict[str, MetricSeries]:
        """Get all metric series."""
        return self._series.copy()

    def get_definitions(self) -> List[MetricDefinition]:
        """Get all metric definitions."""
        return list(self._definitions.values())


# =============================================================================
# ALERT MANAGER
# =============================================================================


class AlertManager:
    """
    Manages alert rules and active alerts.
    """

    def __init__(
        self, collector: MetricsCollector, config: Optional[MetricsDashboardConfig] = None
    ):
        self.config = config or MetricsDashboardConfig()
        self._collector = collector
        self._rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: deque = deque(maxlen=1000)
        self._pending_since: Dict[str, datetime] = {}
        self._running = False
        self._check_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[Alert], None]] = []

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self._rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> None:
        """Remove an alert rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            # Resolve any active alerts for this rule
            for alert_id, alert in list(self._active_alerts.items()):
                if alert.rule.id == rule_id:
                    self._resolve_alert(alert_id)

    def register_callback(self, callback: Callable[[Alert], None]) -> None:
        """Register callback for alert state changes."""
        self._callbacks.append(callback)

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate an alert condition."""
        if condition == ">":
            return value > threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<":
            return value < threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        return False

    async def check_alerts(self) -> List[Alert]:
        """Check all alert rules and update states."""
        new_alerts: List[Alert] = []
        now = datetime.now()

        for rule_id, rule in self._rules.items():
            if not rule.enabled:
                continue

            series = self._collector.get_metric(rule.metric_name)
            if not series or series.last_value is None:
                continue

            value = series.last_value
            is_firing = self._evaluate_condition(value, rule.condition, rule.threshold)

            if is_firing:
                if rule_id not in self._pending_since:
                    self._pending_since[rule_id] = now

                pending_duration = now - self._pending_since[rule_id]

                if pending_duration >= rule.duration:
                    if rule_id not in self._active_alerts:
                        alert = Alert(
                            id=str(uuid.uuid4()),
                            rule=rule,
                            state=AlertState.FIRING,
                            started_at=self._pending_since[rule_id],
                            value=value,
                            message=f"{rule.name}: {value} {rule.condition} {rule.threshold}",
                        )
                        self._active_alerts[rule_id] = alert
                        self._alert_history.append(alert)
                        new_alerts.append(alert)
                        self._notify_callbacks(alert)
                        logger.warning(f"Alert firing: {alert.message}")
            else:
                # Condition no longer met
                if rule_id in self._pending_since:
                    del self._pending_since[rule_id]

                if rule_id in self._active_alerts:
                    self._resolve_alert(rule_id)

        return new_alerts

    def _resolve_alert(self, rule_id: str) -> None:
        """Resolve an active alert."""
        if rule_id in self._active_alerts:
            alert = self._active_alerts[rule_id]
            alert.state = AlertState.RESOLVED
            alert.resolved_at = datetime.now()
            self._notify_callbacks(alert)
            del self._active_alerts[rule_id]
            logger.info(f"Alert resolved: {alert.rule.name}")

    def _notify_callbacks(self, alert: Alert) -> None:
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    async def start(self) -> None:
        """Start background alert checking."""
        if self._running:
            return

        self._running = True
        self._check_task = asyncio.create_task(self._check_loop())
        logger.info("AlertManager started")

    async def stop(self) -> None:
        """Stop background alert checking."""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("AlertManager stopped")

    async def _check_loop(self) -> None:
        """Background alert check loop."""
        while self._running:
            try:
                await self.check_alerts()
                await asyncio.sleep(self.config.alert_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert check loop error: {e}")
                await asyncio.sleep(1)

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self._active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        return list(self._alert_history)[-limit:]

    def get_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        return list(self._rules.values())


# =============================================================================
# METRICS STREAMER
# =============================================================================


class MetricsStreamer:
    """
    Streams metrics in real-time via SSE.
    """

    def __init__(
        self, collector: MetricsCollector, config: Optional[MetricsDashboardConfig] = None
    ):
        self.config = config or MetricsDashboardConfig()
        self._collector = collector
        self._subscribers: Dict[str, asyncio.Queue] = {}
        self._running = False
        self._stream_task: Optional[asyncio.Task] = None

    async def subscribe(self, subscriber_id: Optional[str] = None) -> AsyncIterator[str]:
        """Subscribe to metrics stream."""
        sub_id = subscriber_id or str(uuid.uuid4())
        queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.stream_buffer_size)
        self._subscribers[sub_id] = queue

        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
        finally:
            del self._subscribers[sub_id]

    async def broadcast(self, data: Dict[str, Any]) -> None:
        """Broadcast data to all subscribers."""
        for queue in self._subscribers.values():
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                # Drop oldest message
                try:
                    queue.get_nowait()
                    queue.put_nowait(data)
                except asyncio.QueueEmpty:
                    pass

    async def start(self) -> None:
        """Start streaming metrics."""
        if self._running:
            return

        self._running = True
        self._stream_task = asyncio.create_task(self._stream_loop())
        logger.info("MetricsStreamer started")

    async def stop(self) -> None:
        """Stop streaming metrics."""
        self._running = False
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        logger.info("MetricsStreamer stopped")

    async def _stream_loop(self) -> None:
        """Background streaming loop."""
        while self._running:
            try:
                # Gather current metrics
                metrics_data = {}
                for name, series in self._collector.get_all_metrics().items():
                    if series.last_value is not None:
                        metrics_data[name] = {
                            "value": series.last_value,
                            "timestamp": series.last_updated.isoformat()
                            if series.last_updated
                            else None,
                        }

                await self.broadcast(
                    {
                        "type": "metrics",
                        "timestamp": datetime.now().isoformat(),
                        "data": metrics_data,
                    }
                )

                await asyncio.sleep(self.config.stream_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stream loop error: {e}")
                await asyncio.sleep(1)

    @property
    def subscriber_count(self) -> int:
        """Get number of active subscribers."""
        return len(self._subscribers)


# =============================================================================
# DASHBOARD MANAGER
# =============================================================================


class DashboardManager:
    """
    Manages dashboards and generates dashboard data.
    """

    def __init__(
        self,
        collector: MetricsCollector,
        alert_manager: AlertManager,
        config: Optional[MetricsDashboardConfig] = None,
    ):
        self.config = config or MetricsDashboardConfig()
        self._collector = collector
        self._alert_manager = alert_manager
        self._dashboards: Dict[str, Dashboard] = {}
        self._start_time = datetime.now()

        # Create default dashboards
        self._create_default_dashboards()

    def _create_default_dashboards(self) -> None:
        """Create default dashboard layouts."""
        # Overview dashboard
        overview = Dashboard(
            id="default-overview",
            name="System Overview",
            layout=DashboardLayout.OVERVIEW,
            panels=[
                DashboardPanel(
                    id="health-score",
                    title="Health Score",
                    metric_names=["health_score"],
                    panel_type="gauge",
                    position=(0, 0),
                    size=(2, 1),
                ),
                DashboardPanel(
                    id="active-alerts",
                    title="Active Alerts",
                    metric_names=["active_alerts_count"],
                    panel_type="stat",
                    position=(0, 2),
                    size=(1, 1),
                ),
                DashboardPanel(
                    id="cache-hit-rate",
                    title="Cache Hit Rate",
                    metric_names=["cache_hit_rate"],
                    panel_type="timeseries",
                    position=(1, 0),
                    size=(2, 1),
                ),
                DashboardPanel(
                    id="query-latency",
                    title="Query Latency",
                    metric_names=["query_latency_ms"],
                    panel_type="timeseries",
                    position=(1, 2),
                    size=(2, 1),
                ),
            ],
        )
        self._dashboards[overview.id] = overview

        # Performance dashboard
        performance = Dashboard(
            id="default-performance",
            name="Performance Metrics",
            layout=DashboardLayout.PERFORMANCE,
            panels=[
                DashboardPanel(
                    id="response-times",
                    title="Response Times",
                    metric_names=["query_latency_ms", "cache_latency_ms"],
                    panel_type="timeseries",
                    position=(0, 0),
                    size=(4, 2),
                ),
                DashboardPanel(
                    id="throughput",
                    title="Throughput",
                    metric_names=["events_per_second", "queries_per_second"],
                    panel_type="timeseries",
                    position=(2, 0),
                    size=(4, 2),
                ),
            ],
        )
        self._dashboards[performance.id] = performance

    def create_dashboard(self, dashboard: Dashboard) -> None:
        """Create a new dashboard."""
        dashboard.created_at = datetime.now()
        dashboard.updated_at = datetime.now()
        self._dashboards[dashboard.id] = dashboard

    def update_dashboard(self, dashboard: Dashboard) -> None:
        """Update an existing dashboard."""
        dashboard.updated_at = datetime.now()
        self._dashboards[dashboard.id] = dashboard

    def delete_dashboard(self, dashboard_id: str) -> None:
        """Delete a dashboard."""
        if dashboard_id in self._dashboards:
            del self._dashboards[dashboard_id]

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get a dashboard by ID."""
        return self._dashboards.get(dashboard_id)

    def get_all_dashboards(self) -> List[Dashboard]:
        """Get all dashboards."""
        return list(self._dashboards.values())

    def get_dashboard_data(
        self, dashboard_id: str, time_range: Optional[TimeRange] = None
    ) -> Dict[str, Any]:
        """Get dashboard data with current metric values."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return {"error": "Dashboard not found"}

        time_range = time_range or dashboard.time_range
        since = self._get_since_time(time_range)

        panel_data = []
        for panel in dashboard.panels:
            metrics_data = {}
            for metric_name in panel.metric_names:
                series = self._collector.get_metric(metric_name)
                if series:
                    datapoints = series.get_values(since=since)
                    metrics_data[metric_name] = {
                        "values": [dp.to_dict() for dp in datapoints],
                        "current": series.last_value,
                        "stats": series.get_statistics(since),
                    }
            panel_data.append({"panel": panel.to_dict(), "data": metrics_data})

        return {
            "dashboard": dashboard.to_dict(),
            "panels": panel_data,
            "time_range": time_range.value,
            "generated_at": datetime.now().isoformat(),
        }

    def _get_since_time(self, time_range: TimeRange) -> datetime:
        """Convert time range to datetime."""
        now = datetime.now()
        mapping = {
            TimeRange.LAST_MINUTE: timedelta(minutes=1),
            TimeRange.LAST_5_MINUTES: timedelta(minutes=5),
            TimeRange.LAST_15_MINUTES: timedelta(minutes=15),
            TimeRange.LAST_HOUR: timedelta(hours=1),
            TimeRange.LAST_6_HOURS: timedelta(hours=6),
            TimeRange.LAST_24_HOURS: timedelta(hours=24),
            TimeRange.LAST_7_DAYS: timedelta(days=7),
        }
        return now - mapping.get(time_range, timedelta(hours=1))

    def get_system_health(self) -> SystemHealth:
        """Calculate overall system health."""
        issues: List[str] = []
        component_scores: Dict[str, float] = {}

        # Check cache health
        cache_hit_rate = self._get_metric_value("cache_hit_rate", default=0.5)
        component_scores["cache"] = min(cache_hit_rate * 100, 100)
        if cache_hit_rate < 0.5:
            issues.append("Low cache hit rate")

        # Check connection pool health
        pool_available = self._get_metric_value("pool_available_connections", default=10)
        pool_total = self._get_metric_value("pool_total_connections", default=10)
        pool_ratio = pool_available / max(pool_total, 1)
        component_scores["connections"] = pool_ratio * 100
        if pool_ratio < 0.2:
            issues.append("Low available connections")

        # Check query performance
        query_latency = self._get_metric_value("query_latency_ms", default=50)
        query_score = max(0, 100 - (query_latency / 10))
        component_scores["queries"] = query_score
        if query_latency > 500:
            issues.append("High query latency")

        # Check event delivery
        event_errors = self._get_metric_value("event_delivery_errors", default=0)
        event_score = max(0, 100 - (event_errors * 10))
        component_scores["events"] = event_score
        if event_errors > 5:
            issues.append("Event delivery errors")

        # Check active alerts
        alert_count = len(self._alert_manager.get_active_alerts())
        if alert_count > 0:
            issues.append(f"{alert_count} active alert(s)")

        # Calculate overall score
        overall_score = statistics.mean(component_scores.values()) if component_scores else 100
        overall_score = max(0, overall_score - (alert_count * 5))

        # Determine status
        if overall_score >= 80 and alert_count == 0:
            status = "healthy"
        elif overall_score >= 50:
            status = "degraded"
        else:
            status = "unhealthy"

        return SystemHealth(
            status=status,
            score=round(overall_score, 2),
            components={
                name: {"score": round(score, 2), "status": self._score_to_status(score)}
                for name, score in component_scores.items()
            },
            last_check=datetime.now(),
            issues=issues,
        )

    def _get_metric_value(self, name: str, default: float = 0.0) -> float:
        """Get current value of a metric."""
        series = self._collector.get_metric(name)
        return series.last_value if series and series.last_value is not None else default

    def _score_to_status(self, score: float) -> str:
        """Convert score to status string."""
        if score >= 80:
            return "healthy"
        elif score >= 50:
            return "degraded"
        return "unhealthy"


# =============================================================================
# PROMETHEUS EXPORTER
# =============================================================================


class PrometheusExporter:
    """
    Exports metrics in Prometheus format.
    """

    def __init__(self, collector: MetricsCollector):
        self._collector = collector

    def export(self) -> str:
        """Export all metrics in Prometheus format."""
        lines: List[str] = []

        for definition in self._collector.get_definitions():
            series = self._collector.get_metric(definition.name)
            if not series or series.last_value is None:
                continue

            # Add HELP and TYPE comments
            lines.append(f"# HELP {definition.name} {definition.description}")
            lines.append(f"# TYPE {definition.name} {self._prometheus_type(definition.metric_type)}")

            # Add metric line
            label_str = ""
            if series.datapoints:
                latest = series.datapoints[-1]
                if latest.labels:
                    label_parts = [f'{k}="{v}"' for k, v in latest.labels.items()]
                    label_str = "{" + ",".join(label_parts) + "}"

            lines.append(f"{definition.name}{label_str} {series.last_value}")
            lines.append("")

        return "\n".join(lines)

    def _prometheus_type(self, metric_type: MetricType) -> str:
        """Convert metric type to Prometheus type."""
        mapping = {
            MetricType.COUNTER: "counter",
            MetricType.GAUGE: "gauge",
            MetricType.HISTOGRAM: "histogram",
            MetricType.SUMMARY: "summary",
            MetricType.RATE: "gauge",
        }
        return mapping.get(metric_type, "gauge")


# =============================================================================
# METRICS DASHBOARD (MAIN CLASS)
# =============================================================================


class MetricsDashboard:
    """
    Main class for the MASTERMIND metrics dashboard.

    Provides unified interface for:
    - Metrics collection and aggregation
    - Alert management
    - Real-time streaming
    - Dashboard generation
    - Prometheus export

    Usage:
        dashboard = MetricsDashboard()
        await dashboard.start()

        # Register custom metrics
        dashboard.register_metric(MetricDefinition(...))

        # Record values
        dashboard.record("my_metric", 42.0)

        # Get dashboard data
        data = dashboard.get_dashboard_data("default-overview")

        # Stream metrics
        async for event in dashboard.stream():
            print(event)

        await dashboard.stop()
    """

    def __init__(self, config: Optional[MetricsDashboardConfig] = None):
        self.config = config or MetricsDashboardConfig()
        self._collector = MetricsCollector(self.config)
        self._alert_manager = AlertManager(self._collector, self.config)
        self._streamer = MetricsStreamer(self._collector, self.config)
        self._dashboard_manager = DashboardManager(
            self._collector, self._alert_manager, self.config
        )
        self._prometheus = PrometheusExporter(self._collector)
        self._running = False

        # Register default alert rules
        self._register_default_alerts()

    def _register_default_alerts(self) -> None:
        """Register default alert rules."""
        default_rules = [
            AlertRule(
                id="high-cache-miss",
                name="High Cache Miss Rate",
                metric_name="cache_hit_rate",
                condition="<",
                threshold=0.5,
                severity=AlertSeverity.WARNING,
                description="Cache hit rate below 50%",
            ),
            AlertRule(
                id="low-connections",
                name="Low Available Connections",
                metric_name="pool_available_ratio",
                condition="<",
                threshold=0.1,
                severity=AlertSeverity.ERROR,
                description="Less than 10% connections available",
            ),
            AlertRule(
                id="high-latency",
                name="High Query Latency",
                metric_name="query_latency_ms",
                condition=">",
                threshold=1000,
                severity=AlertSeverity.WARNING,
                description="Query latency exceeds 1 second",
            ),
            AlertRule(
                id="event-failures",
                name="Event Delivery Failures",
                metric_name="event_delivery_errors",
                condition=">",
                threshold=10,
                severity=AlertSeverity.ERROR,
                description="More than 10 event delivery failures",
            ),
        ]

        for rule in default_rules:
            self._alert_manager.add_rule(rule)

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    async def start(self) -> None:
        """Start the metrics dashboard."""
        if self._running:
            return

        await self._collector.start()
        await self._alert_manager.start()
        await self._streamer.start()
        self._running = True
        logger.info("MetricsDashboard started")

    async def stop(self) -> None:
        """Stop the metrics dashboard."""
        if not self._running:
            return

        await self._streamer.stop()
        await self._alert_manager.stop()
        await self._collector.stop()
        self._running = False
        logger.info("MetricsDashboard stopped")

    @property
    def is_running(self) -> bool:
        """Check if dashboard is running."""
        return self._running

    # -------------------------------------------------------------------------
    # Metrics API
    # -------------------------------------------------------------------------

    def register_metric(self, definition: MetricDefinition) -> None:
        """Register a new metric."""
        self._collector.register_metric(definition)

    def register_collector(
        self, name: str, collector: Callable[[], Dict[str, float]]
    ) -> None:
        """Register a metrics collector function."""
        self._collector.register_collector(name, collector)

    def record(
        self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric value."""
        self._collector.record(metric_name, value, labels)

    def get_metric(self, name: str) -> Optional[MetricSeries]:
        """Get a metric series by name."""
        return self._collector.get_metric(name)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values."""
        result = {}
        for name, series in self._collector.get_all_metrics().items():
            result[name] = {
                "current": series.last_value,
                "updated": series.last_updated.isoformat() if series.last_updated else None,
                "stats": series.get_statistics(),
            }
        return result

    # -------------------------------------------------------------------------
    # Alerts API
    # -------------------------------------------------------------------------

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self._alert_manager.add_rule(rule)

    def remove_alert_rule(self, rule_id: str) -> None:
        """Remove an alert rule."""
        self._alert_manager.remove_rule(rule_id)

    def get_active_alerts(self) -> List[Alert]:
        """Get active alerts."""
        return self._alert_manager.get_active_alerts()

    def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        return self._alert_manager.get_rules()

    def register_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Register callback for alert state changes."""
        self._alert_manager.register_callback(callback)

    # -------------------------------------------------------------------------
    # Streaming API
    # -------------------------------------------------------------------------

    async def stream(self, subscriber_id: Optional[str] = None) -> AsyncIterator[str]:
        """Subscribe to metrics stream."""
        async for event in self._streamer.subscribe(subscriber_id):
            yield event

    @property
    def subscriber_count(self) -> int:
        """Get number of active stream subscribers."""
        return self._streamer.subscriber_count

    # -------------------------------------------------------------------------
    # Dashboard API
    # -------------------------------------------------------------------------

    def create_dashboard(self, dashboard: Dashboard) -> None:
        """Create a new dashboard."""
        self._dashboard_manager.create_dashboard(dashboard)

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get a dashboard by ID."""
        return self._dashboard_manager.get_dashboard(dashboard_id)

    def get_dashboard_data(
        self, dashboard_id: str, time_range: Optional[TimeRange] = None
    ) -> Dict[str, Any]:
        """Get dashboard data with current metric values."""
        return self._dashboard_manager.get_dashboard_data(dashboard_id, time_range)

    def get_all_dashboards(self) -> List[Dashboard]:
        """Get all dashboards."""
        return self._dashboard_manager.get_all_dashboards()

    def get_system_health(self) -> SystemHealth:
        """Get overall system health."""
        return self._dashboard_manager.get_system_health()

    # -------------------------------------------------------------------------
    # Export API
    # -------------------------------------------------------------------------

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        return self._prometheus.export()

    def export_json(self) -> Dict[str, Any]:
        """Export full dashboard state as JSON."""
        return {
            "metrics": self.get_all_metrics(),
            "alerts": {
                "active": [a.to_dict() for a in self.get_active_alerts()],
                "rules": [r.to_dict() for r in self.get_alert_rules()],
            },
            "health": self.get_system_health().to_dict(),
            "dashboards": [d.to_dict() for d in self.get_all_dashboards()],
            "config": {
                "collection_interval": self.config.collection_interval,
                "alert_check_interval": self.config.alert_check_interval,
                "stream_interval": self.config.stream_interval,
            },
            "status": {
                "running": self._running,
                "subscribers": self.subscriber_count,
            },
            "exported_at": datetime.now().isoformat(),
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_dashboard_instance: Optional[MetricsDashboard] = None


def create_metrics_dashboard(
    config: Optional[MetricsDashboardConfig] = None,
) -> MetricsDashboard:
    """Create a new MetricsDashboard instance."""
    return MetricsDashboard(config)


def get_metrics_dashboard() -> Optional[MetricsDashboard]:
    """Get the global MetricsDashboard instance."""
    return _dashboard_instance


def set_metrics_dashboard(dashboard: MetricsDashboard) -> None:
    """Set the global MetricsDashboard instance."""
    global _dashboard_instance
    _dashboard_instance = dashboard


async def create_mastermind_metrics_dashboard() -> MetricsDashboard:
    """
    Create and configure a MetricsDashboard for MASTERMIND.

    Returns:
        Configured and started MetricsDashboard instance.
    """
    config = MetricsDashboardConfig(
        collection_interval=5.0,
        retention_period=timedelta(hours=24),
        alert_check_interval=10.0,
        stream_interval=1.0,
        prometheus_enabled=True,
    )

    dashboard = MetricsDashboard(config)

    # Register MASTERMIND-specific metrics
    mastermind_metrics = [
        MetricDefinition(
            name="cache_hit_rate",
            metric_type=MetricType.GAUGE,
            description="Cache hit rate ratio",
            unit="ratio",
            source=MetricSource.CACHE,
        ),
        MetricDefinition(
            name="cache_memory_bytes",
            metric_type=MetricType.GAUGE,
            description="Cache memory usage",
            unit="bytes",
            source=MetricSource.CACHE,
        ),
        MetricDefinition(
            name="query_latency_ms",
            metric_type=MetricType.GAUGE,
            description="Query latency",
            unit="milliseconds",
            source=MetricSource.QUERY,
        ),
        MetricDefinition(
            name="queries_per_second",
            metric_type=MetricType.RATE,
            description="Query throughput",
            unit="qps",
            source=MetricSource.QUERY,
        ),
        MetricDefinition(
            name="pool_available_connections",
            metric_type=MetricType.GAUGE,
            description="Available connections",
            source=MetricSource.CONNECTIONS,
        ),
        MetricDefinition(
            name="pool_total_connections",
            metric_type=MetricType.GAUGE,
            description="Total connections",
            source=MetricSource.CONNECTIONS,
        ),
        MetricDefinition(
            name="pool_available_ratio",
            metric_type=MetricType.GAUGE,
            description="Connection availability ratio",
            unit="ratio",
            source=MetricSource.CONNECTIONS,
        ),
        MetricDefinition(
            name="events_per_second",
            metric_type=MetricType.RATE,
            description="Event throughput",
            unit="eps",
            source=MetricSource.EVENTS,
        ),
        MetricDefinition(
            name="event_delivery_errors",
            metric_type=MetricType.COUNTER,
            description="Event delivery failures",
            source=MetricSource.EVENTS,
        ),
        MetricDefinition(
            name="health_score",
            metric_type=MetricType.GAUGE,
            description="Overall health score",
            unit="percent",
            source=MetricSource.SYSTEM,
        ),
    ]

    for metric in mastermind_metrics:
        dashboard.register_metric(metric)

    await dashboard.start()
    set_metrics_dashboard(dashboard)

    logger.info("MASTERMIND MetricsDashboard created and started")
    return dashboard


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "MetricType",
    "MetricSource",
    "AlertSeverity",
    "AlertState",
    "DashboardLayout",
    "TimeRange",
    # Config
    "MetricsDashboardConfig",
    # Data classes
    "MetricDatapoint",
    "MetricDefinition",
    "MetricSeries",
    "AlertRule",
    "Alert",
    "DashboardPanel",
    "Dashboard",
    "SystemHealth",
    # Components
    "MetricsCollector",
    "AlertManager",
    "MetricsStreamer",
    "DashboardManager",
    "PrometheusExporter",
    # Main class
    "MetricsDashboard",
    # Factory functions
    "create_metrics_dashboard",
    "get_metrics_dashboard",
    "set_metrics_dashboard",
    "create_mastermind_metrics_dashboard",
]
