"""
Anomaly Detector
================
Proactive error detection and issue prediction.

Responsibilities:
- Monitor patterns for anomalies
- Detect potential issues before they occur
- Alert on unusual behavior
- Track error patterns
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import statistics

from cirkelline.headquarters.event_bus import (
    EventBus,
    Event,
    EventType,
    get_event_bus,
)
from cirkelline.headquarters.shared_memory import (
    SharedMemory,
    get_shared_memory,
)
from cirkelline.context.system_status import (
    SystemStatus,
    HealthStatus,
    get_system_status,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ANOMALY TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class AnomalyType(Enum):
    """Types of detected anomalies."""
    LATENCY_SPIKE = "latency_spike"
    ERROR_RATE_INCREASE = "error_rate_increase"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    AGENT_FAILURE = "agent_failure"
    MISSION_STALL = "mission_stall"
    PATTERN_DEVIATION = "pattern_deviation"
    SECURITY_ANOMALY = "security_anomaly"
    DATA_INCONSISTENCY = "data_inconsistency"


class AnomalySeverity(Enum):
    """Severity levels for anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """A detected anomaly."""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    expected_value: Optional[float] = None
    threshold: Optional[float] = None
    source: str = ""
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved: bool = False
    resolved_at: Optional[str] = None
    related_entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
            "threshold": self.threshold,
            "source": self.source,
            "detected_at": self.detected_at,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "related_entities": self.related_entities,
            "metadata": self.metadata,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# METRIC TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MetricWindow:
    """Rolling window of metric values."""
    name: str
    values: List[Tuple[datetime, float]] = field(default_factory=list)
    window_size: int = 100
    window_minutes: int = 60

    def add(self, value: float, timestamp: Optional[datetime] = None) -> None:
        """Add a value to the window."""
        ts = timestamp or datetime.utcnow()
        self.values.append((ts, value))

        # Trim by size
        if len(self.values) > self.window_size:
            self.values = self.values[-self.window_size:]

        # Trim by time
        cutoff = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        self.values = [(t, v) for t, v in self.values if t > cutoff]

    def get_values(self) -> List[float]:
        """Get all values."""
        return [v for _, v in self.values]

    def get_recent(self, minutes: int = 5) -> List[float]:
        """Get values from last N minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [v for t, v in self.values if t > cutoff]

    @property
    def mean(self) -> Optional[float]:
        """Get mean of values."""
        vals = self.get_values()
        return statistics.mean(vals) if vals else None

    @property
    def std_dev(self) -> Optional[float]:
        """Get standard deviation."""
        vals = self.get_values()
        return statistics.stdev(vals) if len(vals) >= 2 else None

    @property
    def latest(self) -> Optional[float]:
        """Get latest value."""
        return self.values[-1][1] if self.values else None


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTION RULES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DetectionRule:
    """Rule for anomaly detection."""
    rule_id: str
    name: str
    metric_name: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity

    # Threshold-based detection
    threshold_high: Optional[float] = None
    threshold_low: Optional[float] = None

    # Statistical detection
    std_dev_multiplier: Optional[float] = None  # z-score threshold

    # Rate of change detection
    change_rate_threshold: Optional[float] = None  # % change

    # Cooldown (avoid duplicate alerts)
    cooldown_minutes: int = 5

    enabled: bool = True


DEFAULT_DETECTION_RULES: List[DetectionRule] = [
    # Latency rules
    DetectionRule(
        rule_id="latency-high",
        name="High Latency",
        metric_name="response_latency_ms",
        anomaly_type=AnomalyType.LATENCY_SPIKE,
        severity=AnomalySeverity.MEDIUM,
        threshold_high=2000,  # 2 seconds
    ),
    DetectionRule(
        rule_id="latency-critical",
        name="Critical Latency",
        metric_name="response_latency_ms",
        anomaly_type=AnomalyType.LATENCY_SPIKE,
        severity=AnomalySeverity.CRITICAL,
        threshold_high=5000,  # 5 seconds
    ),
    DetectionRule(
        rule_id="latency-spike",
        name="Latency Spike",
        metric_name="response_latency_ms",
        anomaly_type=AnomalyType.LATENCY_SPIKE,
        severity=AnomalySeverity.HIGH,
        std_dev_multiplier=3.0,  # 3 standard deviations
    ),

    # Error rate rules
    DetectionRule(
        rule_id="error-rate-high",
        name="High Error Rate",
        metric_name="error_rate",
        anomaly_type=AnomalyType.ERROR_RATE_INCREASE,
        severity=AnomalySeverity.HIGH,
        threshold_high=0.10,  # 10% errors
    ),
    DetectionRule(
        rule_id="error-rate-spike",
        name="Error Rate Spike",
        metric_name="error_rate",
        anomaly_type=AnomalyType.ERROR_RATE_INCREASE,
        severity=AnomalySeverity.MEDIUM,
        change_rate_threshold=50.0,  # 50% increase
    ),

    # Resource rules
    DetectionRule(
        rule_id="memory-high",
        name="High Memory Usage",
        metric_name="memory_usage_percent",
        anomaly_type=AnomalyType.RESOURCE_EXHAUSTION,
        severity=AnomalySeverity.HIGH,
        threshold_high=90,  # 90%
    ),
    DetectionRule(
        rule_id="cpu-high",
        name="High CPU Usage",
        metric_name="cpu_usage_percent",
        anomaly_type=AnomalyType.RESOURCE_EXHAUSTION,
        severity=AnomalySeverity.MEDIUM,
        threshold_high=85,  # 85%
    ),

    # Mission rules
    DetectionRule(
        rule_id="mission-stall",
        name="Mission Stalled",
        metric_name="mission_duration_minutes",
        anomaly_type=AnomalyType.MISSION_STALL,
        severity=AnomalySeverity.HIGH,
        threshold_high=30,  # 30 minutes
    ),

    # Agent rules
    DetectionRule(
        rule_id="agent-failure-rate",
        name="Agent Failure Rate",
        metric_name="agent_failure_rate",
        anomaly_type=AnomalyType.AGENT_FAILURE,
        severity=AnomalySeverity.HIGH,
        threshold_high=0.20,  # 20% failures
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# ANOMALY DETECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class AnomalyDetector:
    """
    Proactive anomaly detection for system monitoring.

    Uses statistical analysis, threshold detection, and pattern
    matching to identify potential issues before they escalate.
    """

    # Detection check interval
    CHECK_INTERVAL = 30  # seconds

    def __init__(self):
        self._event_bus: Optional[EventBus] = None
        self._memory: Optional[SharedMemory] = None
        self._system_status: Optional[SystemStatus] = None
        self._running = False

        # Metric tracking
        self._metrics: Dict[str, MetricWindow] = {}

        # Detection rules
        self._rules: List[DetectionRule] = DEFAULT_DETECTION_RULES.copy()

        # Detected anomalies
        self._anomalies: Dict[str, Anomaly] = {}

        # Rule cooldowns
        self._cooldowns: Dict[str, datetime] = {}

    async def initialize(self) -> bool:
        """Initialize connections."""
        try:
            self._event_bus = get_event_bus()
            self._memory = get_shared_memory()
            self._system_status = get_system_status()

            # Subscribe to events
            self._event_bus.subscribe(EventType.SYSTEM_METRIC, self._handle_metric)
            self._event_bus.subscribe(EventType.MISSION_COMPLETED, self._handle_mission_completed)
            self._event_bus.subscribe(EventType.MISSION_FAILED, self._handle_mission_failed)
            self._event_bus.subscribe(EventType.AGENT_ERROR, self._handle_agent_error)

            logger.info("AnomalyDetector initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize AnomalyDetector: {e}")
            return False

    async def start(self) -> None:
        """Start the detection loop."""
        self._running = True
        logger.info("AnomalyDetector started")

        while self._running:
            try:
                await self._run_detection_cycle()
                await self._check_system_health()
                await self._cleanup_resolved()

                await asyncio.sleep(self.CHECK_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Detection loop error: {e}")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop detection."""
        self._running = False
        logger.info("AnomalyDetector stopped")

    # ═══════════════════════════════════════════════════════════════════════════
    # METRIC COLLECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def record_metric(
        self,
        name: str,
        value: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record a metric value."""
        if name not in self._metrics:
            self._metrics[name] = MetricWindow(name=name)
        self._metrics[name].add(value, timestamp)

    def get_metric(self, name: str) -> Optional[MetricWindow]:
        """Get metric window by name."""
        return self._metrics.get(name)

    # ═══════════════════════════════════════════════════════════════════════════
    # DETECTION ENGINE
    # ═══════════════════════════════════════════════════════════════════════════

    async def _run_detection_cycle(self) -> None:
        """Run detection on all rules."""
        for rule in self._rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.rule_id in self._cooldowns:
                if datetime.utcnow() < self._cooldowns[rule.rule_id]:
                    continue

            # Get metric data
            metric = self._metrics.get(rule.metric_name)
            if not metric or metric.latest is None:
                continue

            # Run detection
            anomaly = self._detect_anomaly(rule, metric)
            if anomaly:
                await self._report_anomaly(anomaly)

                # Set cooldown
                self._cooldowns[rule.rule_id] = (
                    datetime.utcnow() + timedelta(minutes=rule.cooldown_minutes)
                )

    def _detect_anomaly(
        self,
        rule: DetectionRule,
        metric: MetricWindow,
    ) -> Optional[Anomaly]:
        """Detect anomaly based on rule."""
        current = metric.latest

        # Threshold detection
        if rule.threshold_high is not None and current > rule.threshold_high:
            return self._create_anomaly(
                rule=rule,
                current=current,
                expected=rule.threshold_high,
                description=f"{rule.name}: {current:.2f} exceeds threshold {rule.threshold_high}",
            )

        if rule.threshold_low is not None and current < rule.threshold_low:
            return self._create_anomaly(
                rule=rule,
                current=current,
                expected=rule.threshold_low,
                description=f"{rule.name}: {current:.2f} below threshold {rule.threshold_low}",
            )

        # Statistical detection (z-score)
        if rule.std_dev_multiplier is not None:
            mean = metric.mean
            std_dev = metric.std_dev

            if mean is not None and std_dev is not None and std_dev > 0:
                z_score = abs(current - mean) / std_dev
                if z_score > rule.std_dev_multiplier:
                    return self._create_anomaly(
                        rule=rule,
                        current=current,
                        expected=mean,
                        description=f"{rule.name}: Value {current:.2f} is {z_score:.1f} standard deviations from mean {mean:.2f}",
                    )

        # Rate of change detection
        if rule.change_rate_threshold is not None:
            recent = metric.get_recent(minutes=5)
            older = metric.get_recent(minutes=15)

            if len(recent) >= 2 and len(older) >= 5:
                recent_avg = statistics.mean(recent)
                older_avg = statistics.mean(older[:-len(recent)])  # Exclude recent

                if older_avg > 0:
                    change_rate = ((recent_avg - older_avg) / older_avg) * 100
                    if abs(change_rate) > rule.change_rate_threshold:
                        return self._create_anomaly(
                            rule=rule,
                            current=current,
                            expected=older_avg,
                            description=f"{rule.name}: {change_rate:.1f}% change detected",
                        )

        return None

    def _create_anomaly(
        self,
        rule: DetectionRule,
        current: float,
        expected: float,
        description: str,
    ) -> Anomaly:
        """Create an anomaly from a rule match."""
        import uuid
        return Anomaly(
            anomaly_id=f"anomaly-{uuid.uuid4().hex[:8]}",
            anomaly_type=rule.anomaly_type,
            severity=rule.severity,
            title=rule.name,
            description=description,
            metric_name=rule.metric_name,
            current_value=current,
            expected_value=expected,
            threshold=rule.threshold_high or rule.threshold_low,
            source=rule.rule_id,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SYSTEM HEALTH CHECKS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _check_system_health(self) -> None:
        """Check overall system health for anomalies."""
        try:
            health = await self._system_status.check_all()
            overall = health.get("overall", "unknown")

            # Record as metric
            health_score = {
                "healthy": 1.0,
                "degraded": 0.5,
                "unhealthy": 0.0,
            }.get(overall, 0.0)

            self.record_metric("system_health_score", health_score)

            # Check individual services
            for service_name, service_health in health.get("services", {}).items():
                if service_health.get("status") == "unhealthy":
                    import uuid
                    anomaly = Anomaly(
                        anomaly_id=f"anomaly-svc-{uuid.uuid4().hex[:8]}",
                        anomaly_type=AnomalyType.AGENT_FAILURE,
                        severity=AnomalySeverity.HIGH,
                        title=f"Service Unhealthy: {service_name}",
                        description=f"Service {service_name} is not responding",
                        source="system_health_check",
                        related_entities=[service_name],
                    )
                    await self._report_anomaly(anomaly)

        except Exception as e:
            logger.debug(f"System health check error: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # ANOMALY MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def _report_anomaly(self, anomaly: Anomaly) -> None:
        """Report and store an anomaly."""
        self._anomalies[anomaly.anomaly_id] = anomaly

        # Publish event
        await self._event_bus.publish(Event(
            event_type=EventType.SYSTEM_ALERT,
            source="anomaly_detector",
            payload=anomaly.to_dict(),
            priority=self._severity_to_priority(anomaly.severity),
        ))

        logger.warning(f"Anomaly detected: [{anomaly.severity.value}] {anomaly.title}")

    def _severity_to_priority(self, severity: AnomalySeverity) -> int:
        """Convert severity to event priority."""
        return {
            AnomalySeverity.LOW: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.HIGH: 3,
            AnomalySeverity.CRITICAL: 4,
        }.get(severity, 1)

    def resolve_anomaly(self, anomaly_id: str) -> bool:
        """Mark an anomaly as resolved."""
        if anomaly_id in self._anomalies:
            self._anomalies[anomaly_id].resolved = True
            self._anomalies[anomaly_id].resolved_at = datetime.utcnow().isoformat()
            return True
        return False

    async def _cleanup_resolved(self) -> None:
        """Remove old resolved anomalies."""
        cutoff = datetime.utcnow() - timedelta(hours=1)

        for anomaly_id in list(self._anomalies.keys()):
            anomaly = self._anomalies[anomaly_id]
            if anomaly.resolved and anomaly.resolved_at:
                resolved_at = datetime.fromisoformat(anomaly.resolved_at)
                if resolved_at < cutoff:
                    del self._anomalies[anomaly_id]

    def get_active_anomalies(self) -> List[Anomaly]:
        """Get all unresolved anomalies."""
        return [a for a in self._anomalies.values() if not a.resolved]

    def get_anomalies_by_type(self, anomaly_type: AnomalyType) -> List[Anomaly]:
        """Get anomalies by type."""
        return [
            a for a in self._anomalies.values()
            if a.anomaly_type == anomaly_type and not a.resolved
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _handle_metric(self, event: Event) -> None:
        """Handle incoming metric events."""
        payload = event.payload
        name = payload.get("name")
        value = payload.get("value")

        if name and value is not None:
            self.record_metric(name, float(value))

    async def _handle_mission_completed(self, event: Event) -> None:
        """Handle mission completion for tracking."""
        # Track mission success
        self.record_metric("mission_success", 1.0)

    async def _handle_mission_failed(self, event: Event) -> None:
        """Handle mission failure."""
        # Track mission failure
        self.record_metric("mission_success", 0.0)

        # Potential anomaly if high failure rate
        metric = self._metrics.get("mission_success")
        if metric:
            recent = metric.get_recent(minutes=10)
            if len(recent) >= 5:
                failure_rate = 1 - statistics.mean(recent)
                if failure_rate > 0.3:  # 30% failure rate
                    import uuid
                    anomaly = Anomaly(
                        anomaly_id=f"anomaly-mission-{uuid.uuid4().hex[:8]}",
                        anomaly_type=AnomalyType.MISSION_STALL,
                        severity=AnomalySeverity.HIGH,
                        title="High Mission Failure Rate",
                        description=f"Mission failure rate is {failure_rate:.0%}",
                        current_value=failure_rate,
                        expected_value=0.1,
                        source="mission_tracking",
                    )
                    await self._report_anomaly(anomaly)

    async def _handle_agent_error(self, event: Event) -> None:
        """Handle agent errors."""
        agent_id = event.source
        error = event.payload.get("error", "Unknown")

        # Track agent errors
        self.record_metric(f"agent_error_{agent_id}", 1.0)

        # Could create anomaly for repeated errors
        metric = self._metrics.get(f"agent_error_{agent_id}")
        if metric:
            recent = metric.get_recent(minutes=5)
            if len(recent) >= 3:
                import uuid
                anomaly = Anomaly(
                    anomaly_id=f"anomaly-agent-{uuid.uuid4().hex[:8]}",
                    anomaly_type=AnomalyType.AGENT_FAILURE,
                    severity=AnomalySeverity.HIGH,
                    title=f"Repeated Agent Errors: {agent_id}",
                    description=f"Agent {agent_id} has {len(recent)} errors in 5 minutes",
                    source="agent_error_tracking",
                    related_entities=[agent_id],
                    metadata={"last_error": error},
                )
                await self._report_anomaly(anomaly)

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get detector statistics."""
        active = self.get_active_anomalies()

        by_type = defaultdict(int)
        by_severity = defaultdict(int)

        for a in active:
            by_type[a.anomaly_type.value] += 1
            by_severity[a.severity.value] += 1

        return {
            "total_anomalies": len(self._anomalies),
            "active_anomalies": len(active),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "metrics_tracked": len(self._metrics),
            "rules_active": sum(1 for r in self._rules if r.enabled),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_detector_instance: Optional[AnomalyDetector] = None


def get_detector() -> AnomalyDetector:
    """Get the singleton AnomalyDetector instance."""
    global _detector_instance

    if _detector_instance is None:
        _detector_instance = AnomalyDetector()

    return _detector_instance


async def init_detector() -> AnomalyDetector:
    """Initialize and return the detector."""
    detector = get_detector()
    await detector.initialize()
    return detector
