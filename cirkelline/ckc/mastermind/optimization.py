"""
DEL F: SYSTEMBRED OPTIMERING
============================

Optimeringsmodul for CKC MASTERMIND systemet.

Inkluderer:
- PerformanceMonitor: Overvåger system performance
- CacheManager: Intelligent caching strategi
- BatchProcessor: Batch-processering af opgaver
- CostOptimizer: Minimerer API og ressource omkostninger
- LatencyTracker: Sporer og optimerer latency

Eksempel:
    from cirkelline.ckc.mastermind.optimization import (
        create_performance_monitor,
        create_cache_manager,
        create_cost_optimizer,
    )

    monitor = await create_performance_monitor()
    cache = await create_cache_manager(max_size_mb=256)
    optimizer = await create_cost_optimizer(budget_usd=100.0)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar

logger = logging.getLogger(__name__)

# =============================================================================
# ENUMS
# =============================================================================


class MetricType(Enum):
    """Typer af performance metrics."""
    LATENCY = "latency"             # Responstid
    THROUGHPUT = "throughput"       # Gennemløb
    ERROR_RATE = "error_rate"       # Fejlrate
    CPU_USAGE = "cpu_usage"         # CPU forbrug
    MEMORY_USAGE = "memory_usage"   # Hukommelsesforbrug
    API_CALLS = "api_calls"         # API kald
    CACHE_HIT = "cache_hit"         # Cache hits
    CACHE_MISS = "cache_miss"       # Cache misses
    COST = "cost"                   # Omkostninger


class OptimizationStrategy(Enum):
    """Optimeringsstrategier."""
    MINIMIZE_LATENCY = "minimize_latency"
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_THROUGHPUT = "maximize_throughput"
    BALANCED = "balanced"


class CacheEvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"           # Least Recently Used
    LFU = "lfu"           # Least Frequently Used
    TTL = "ttl"           # Time To Live
    FIFO = "fifo"         # First In First Out


class AlertLevel(Enum):
    """Alert niveauer for performance problemer."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class PerformanceMetric:
    """En enkelt performance metric."""
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Snapshot af system performance."""
    snapshot_id: str
    timestamp: datetime
    metrics: Dict[MetricType, float]

    # Beregnede værdier
    avg_latency_ms: float = 0.0
    throughput_per_second: float = 0.0
    error_rate_percent: float = 0.0
    cache_hit_rate_percent: float = 0.0
    estimated_cost_usd: float = 0.0


@dataclass
class PerformanceAlert:
    """Alert for performance problemer."""
    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    message: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class CacheEntry:
    """En cache entry."""
    key: str
    value: Any
    size_bytes: int
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: Optional[int] = None

    @property
    def is_expired(self) -> bool:
        """Tjek om entry er udløbet."""
        if self.ttl_seconds is None:
            return False
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds


@dataclass
class CacheStats:
    """Statistik for cache performance."""
    total_entries: int = 0
    total_size_bytes: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Beregn hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


@dataclass
class BatchJob:
    """En batch job."""
    job_id: str
    items: List[Any]
    processor: str
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Job status."""
        if self.completed_at:
            return "completed"
        elif self.started_at:
            return "running"
        else:
            return "pending"


@dataclass
class CostEstimate:
    """Estimat af omkostninger."""
    estimate_id: str
    operation: str
    estimated_cost_usd: float
    actual_cost_usd: Optional[float] = None
    api_calls: int = 0
    tokens_used: int = 0
    compute_time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationRecommendation:
    """Anbefaling for optimering."""
    recommendation_id: str
    category: str
    title: str
    description: str
    estimated_savings_usd: float = 0.0
    estimated_latency_reduction_ms: float = 0.0
    priority: int = 5  # 1-10, higher = more important
    created_at: datetime = field(default_factory=datetime.now)


# =============================================================================
# PERFORMANCE MONITOR
# =============================================================================


class PerformanceMonitor:
    """
    Overvåger system performance og genererer alerts.

    Features:
    - Real-time metric collection
    - Alert generation baseret på thresholds
    - Historical data analyse
    - Performance snapshots
    """

    def __init__(
        self,
        window_size_seconds: int = 60,
        alert_cooldown_seconds: int = 300,
    ) -> None:
        self.window_size = window_size_seconds
        self.alert_cooldown = alert_cooldown_seconds

        self._metrics: Dict[MetricType, List[PerformanceMetric]] = defaultdict(list)
        self._alerts: List[PerformanceAlert] = []
        self._thresholds: Dict[MetricType, Dict[AlertLevel, float]] = {}
        self._last_alert_time: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

        # Default thresholds
        self._set_default_thresholds()

    def _set_default_thresholds(self) -> None:
        """Sæt default thresholds."""
        self._thresholds = {
            MetricType.LATENCY: {
                AlertLevel.WARNING: 500.0,    # ms
                AlertLevel.CRITICAL: 2000.0,
            },
            MetricType.ERROR_RATE: {
                AlertLevel.WARNING: 0.05,     # 5%
                AlertLevel.CRITICAL: 0.15,    # 15%
            },
            MetricType.CPU_USAGE: {
                AlertLevel.WARNING: 0.80,     # 80%
                AlertLevel.CRITICAL: 0.95,    # 95%
            },
            MetricType.MEMORY_USAGE: {
                AlertLevel.WARNING: 0.80,     # 80%
                AlertLevel.CRITICAL: 0.95,    # 95%
            },
        }

    async def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        source: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Registrer en metric."""
        async with self._lock:
            metric = PerformanceMetric(
                metric_type=metric_type,
                value=value,
                source=source,
                tags=tags or {},
            )
            self._metrics[metric_type].append(metric)

            # Cleanup gamle metrics
            self._cleanup_old_metrics(metric_type)

            # Check thresholds
            await self._check_thresholds(metric)

    def _cleanup_old_metrics(self, metric_type: MetricType) -> None:
        """Fjern gamle metrics udenfor window."""
        cutoff = datetime.now() - timedelta(seconds=self.window_size * 10)
        self._metrics[metric_type] = [
            m for m in self._metrics[metric_type]
            if m.timestamp > cutoff
        ]

    async def _check_thresholds(self, metric: PerformanceMetric) -> None:
        """Check om metric overstiger thresholds."""
        if metric.metric_type not in self._thresholds:
            return

        thresholds = self._thresholds[metric.metric_type]

        for level in [AlertLevel.CRITICAL, AlertLevel.WARNING]:
            if level not in thresholds:
                continue

            threshold = thresholds[level]
            if metric.value > threshold:
                await self._create_alert(metric, level, threshold)
                break

    async def _create_alert(
        self,
        metric: PerformanceMetric,
        level: AlertLevel,
        threshold: float,
    ) -> None:
        """Opret en alert."""
        alert_key = f"{metric.metric_type.value}_{level.value}"

        # Check cooldown
        if alert_key in self._last_alert_time:
            elapsed = (datetime.now() - self._last_alert_time[alert_key]).total_seconds()
            if elapsed < self.alert_cooldown:
                return

        alert = PerformanceAlert(
            alert_id=str(uuid.uuid4()),
            level=level,
            metric_type=metric.metric_type,
            message=f"{metric.metric_type.value} exceeded {level.value} threshold",
            current_value=metric.value,
            threshold=threshold,
        )

        self._alerts.append(alert)
        self._last_alert_time[alert_key] = datetime.now()

        logger.warning(
            f"Performance alert: {alert.message} "
            f"(value={metric.value:.2f}, threshold={threshold:.2f})"
        )

    async def get_current_metrics(self) -> Dict[MetricType, float]:
        """Hent gennemsnitlige metrics for current window."""
        async with self._lock:
            cutoff = datetime.now() - timedelta(seconds=self.window_size)
            result = {}

            for metric_type, metrics in self._metrics.items():
                recent = [m for m in metrics if m.timestamp > cutoff]
                if recent:
                    result[metric_type] = sum(m.value for m in recent) / len(recent)

            return result

    async def create_snapshot(self) -> PerformanceSnapshot:
        """Opret et performance snapshot."""
        metrics = await self.get_current_metrics()

        snapshot = PerformanceSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            metrics=metrics,
            avg_latency_ms=metrics.get(MetricType.LATENCY, 0.0),
            throughput_per_second=metrics.get(MetricType.THROUGHPUT, 0.0),
            error_rate_percent=metrics.get(MetricType.ERROR_RATE, 0.0) * 100,
            estimated_cost_usd=metrics.get(MetricType.COST, 0.0),
        )

        # Calculate cache hit rate
        hits = metrics.get(MetricType.CACHE_HIT, 0)
        misses = metrics.get(MetricType.CACHE_MISS, 0)
        total = hits + misses
        if total > 0:
            snapshot.cache_hit_rate_percent = (hits / total) * 100

        return snapshot

    async def get_active_alerts(self) -> List[PerformanceAlert]:
        """Hent aktive (uløste) alerts."""
        return [a for a in self._alerts if not a.resolved]

    async def resolve_alert(self, alert_id: str) -> bool:
        """Marker en alert som løst."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                return True
        return False

    def set_threshold(
        self,
        metric_type: MetricType,
        level: AlertLevel,
        value: float,
    ) -> None:
        """Sæt custom threshold."""
        if metric_type not in self._thresholds:
            self._thresholds[metric_type] = {}
        self._thresholds[metric_type][level] = value


# =============================================================================
# CACHE MANAGER
# =============================================================================

T = TypeVar('T')


class CacheManager(Generic[T]):
    """
    Intelligent cache manager med multiple eviction policies.

    Features:
    - LRU, LFU, TTL, FIFO eviction
    - Size-based eviction
    - Cache statistics
    - Automatic cleanup
    """

    def __init__(
        self,
        max_size_mb: float = 256,
        default_ttl_seconds: Optional[int] = 3600,
        eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU,
    ) -> None:
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.default_ttl = default_ttl_seconds
        self.eviction_policy = eviction_policy

        self._cache: Dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[T]:
        """Hent værdi fra cache."""
        async with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                return None

            # Update access info
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            self._stats.hits += 1

            return entry.value

    async def set(
        self,
        key: str,
        value: T,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Sæt værdi i cache."""
        async with self._lock:
            # Estimate size
            size = self._estimate_size(value)

            # Evict if needed
            while self._stats.total_size_bytes + size > self.max_size_bytes:
                if not self._evict_one():
                    break

            entry = CacheEntry(
                key=key,
                value=value,
                size_bytes=size,
                ttl_seconds=ttl_seconds or self.default_ttl,
            )

            # Update size tracking
            if key in self._cache:
                self._stats.total_size_bytes -= self._cache[key].size_bytes

            self._cache[key] = entry
            self._stats.total_size_bytes += size
            self._stats.total_entries = len(self._cache)

    async def delete(self, key: str) -> bool:
        """Slet entry fra cache."""
        async with self._lock:
            if key in self._cache:
                self._stats.total_size_bytes -= self._cache[key].size_bytes
                del self._cache[key]
                self._stats.total_entries = len(self._cache)
                return True
            return False

    async def clear(self) -> None:
        """Ryd hele cachen."""
        async with self._lock:
            self._cache.clear()
            self._stats = CacheStats()

    def _estimate_size(self, value: Any) -> int:
        """Estimér størrelse af værdi i bytes."""
        try:
            return len(json.dumps(value, default=str).encode('utf-8'))
        except (TypeError, ValueError):
            return 1024  # Default estimate

    def _evict_one(self) -> bool:
        """Evict én entry baseret på policy."""
        if not self._cache:
            return False

        key_to_evict: Optional[str] = None

        if self.eviction_policy == CacheEvictionPolicy.LRU:
            key_to_evict = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].last_accessed
            )
        elif self.eviction_policy == CacheEvictionPolicy.LFU:
            key_to_evict = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].access_count
            )
        elif self.eviction_policy == CacheEvictionPolicy.TTL:
            expired = [k for k, v in self._cache.items() if v.is_expired]
            if expired:
                key_to_evict = expired[0]
            else:
                key_to_evict = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].created_at
                )
        elif self.eviction_policy == CacheEvictionPolicy.FIFO:
            key_to_evict = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].created_at
            )

        if key_to_evict:
            self._stats.total_size_bytes -= self._cache[key_to_evict].size_bytes
            del self._cache[key_to_evict]
            self._stats.evictions += 1
            self._stats.total_entries = len(self._cache)
            return True

        return False

    async def get_stats(self) -> CacheStats:
        """Hent cache statistik."""
        async with self._lock:
            return CacheStats(
                total_entries=self._stats.total_entries,
                total_size_bytes=self._stats.total_size_bytes,
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
            )

    async def cleanup_expired(self) -> int:
        """Fjern alle expired entries."""
        async with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired]
            for key in expired_keys:
                self._stats.total_size_bytes -= self._cache[key].size_bytes
                del self._cache[key]
            self._stats.total_entries = len(self._cache)
            return len(expired_keys)


# =============================================================================
# BATCH PROCESSOR
# =============================================================================


class BatchProcessor:
    """
    Processor for batch-opgaver.

    Samler små opgaver til større batches for
    at reducere overhead og forbedre throughput.
    """

    def __init__(
        self,
        batch_size: int = 10,
        max_wait_seconds: float = 5.0,
    ) -> None:
        self.batch_size = batch_size
        self.max_wait = max_wait_seconds

        self._pending: Dict[str, List[Any]] = defaultdict(list)
        self._processors: Dict[str, Callable] = {}
        self._jobs: Dict[str, BatchJob] = {}
        self._lock = asyncio.Lock()

    def register_processor(
        self,
        name: str,
        processor: Callable[[List[Any]], List[Any]],
    ) -> None:
        """Registrer en batch processor."""
        self._processors[name] = processor

    async def add_item(
        self,
        processor_name: str,
        item: Any,
    ) -> str:
        """Tilføj item til batch kø."""
        async with self._lock:
            self._pending[processor_name].append(item)

            # Check if batch is ready
            if len(self._pending[processor_name]) >= self.batch_size:
                job_id = await self._create_job(processor_name)
                return job_id

            return ""

    async def _create_job(self, processor_name: str) -> str:
        """Opret et batch job."""
        items = self._pending[processor_name][:self.batch_size]
        self._pending[processor_name] = self._pending[processor_name][self.batch_size:]

        job = BatchJob(
            job_id=str(uuid.uuid4()),
            items=items,
            processor=processor_name,
        )

        self._jobs[job.job_id] = job
        return job.job_id

    async def process_job(self, job_id: str) -> BatchJob:
        """Process et batch job."""
        if job_id not in self._jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self._jobs[job_id]
        job.started_at = datetime.now()

        processor = self._processors.get(job.processor)
        if processor is None:
            job.errors.append(f"Processor {job.processor} not found")
            job.completed_at = datetime.now()
            return job

        try:
            if asyncio.iscoroutinefunction(processor):
                job.results = await processor(job.items)
            else:
                job.results = processor(job.items)
        except Exception as e:
            job.errors.append(str(e))

        job.completed_at = datetime.now()
        return job

    async def flush_all(self) -> List[str]:
        """Flush alle pending items til jobs."""
        async with self._lock:
            job_ids = []
            for processor_name in list(self._pending.keys()):
                while self._pending[processor_name]:
                    job_id = await self._create_job(processor_name)
                    job_ids.append(job_id)
            return job_ids

    async def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Hent job status."""
        return self._jobs.get(job_id)

    async def get_pending_count(self) -> Dict[str, int]:
        """Hent antal pending items per processor."""
        async with self._lock:
            return {k: len(v) for k, v in self._pending.items()}


# =============================================================================
# COST OPTIMIZER
# =============================================================================


class CostOptimizer:
    """
    Optimerer omkostninger for API kald og ressourcer.

    Features:
    - Budget tracking
    - Cost estimation
    - Optimization recommendations
    - Usage patterns analyse
    """

    def __init__(
        self,
        budget_usd: float = 100.0,
        budget_period_days: int = 30,
    ) -> None:
        self.budget_usd = budget_usd
        self.budget_period_days = budget_period_days

        self._estimates: List[CostEstimate] = []
        self._total_cost_usd: float = 0.0
        self._recommendations: List[OptimizationRecommendation] = []
        self._lock = asyncio.Lock()

        # Cost rates (example values)
        self._rates = {
            "api_call": 0.001,           # $0.001 per call
            "token_input": 0.000003,     # $0.000003 per token
            "token_output": 0.000015,    # $0.000015 per token
            "compute_second": 0.00001,   # $0.00001 per second
        }

    async def estimate_cost(
        self,
        operation: str,
        api_calls: int = 0,
        tokens_input: int = 0,
        tokens_output: int = 0,
        compute_seconds: float = 0.0,
    ) -> CostEstimate:
        """Estimér omkostning for en operation."""
        cost = (
            api_calls * self._rates["api_call"] +
            tokens_input * self._rates["token_input"] +
            tokens_output * self._rates["token_output"] +
            compute_seconds * self._rates["compute_second"]
        )

        estimate = CostEstimate(
            estimate_id=str(uuid.uuid4()),
            operation=operation,
            estimated_cost_usd=cost,
            api_calls=api_calls,
            tokens_used=tokens_input + tokens_output,
            compute_time_seconds=compute_seconds,
        )

        async with self._lock:
            self._estimates.append(estimate)

        return estimate

    async def record_actual_cost(
        self,
        estimate_id: str,
        actual_cost_usd: float,
    ) -> None:
        """Registrer faktisk omkostning."""
        async with self._lock:
            for estimate in self._estimates:
                if estimate.estimate_id == estimate_id:
                    estimate.actual_cost_usd = actual_cost_usd
                    self._total_cost_usd += actual_cost_usd
                    break

    async def get_budget_status(self) -> Dict[str, Any]:
        """Hent budget status."""
        async with self._lock:
            remaining = self.budget_usd - self._total_cost_usd
            usage_percent = (self._total_cost_usd / self.budget_usd) * 100 if self.budget_usd > 0 else 0

            return {
                "budget_usd": self.budget_usd,
                "spent_usd": self._total_cost_usd,
                "remaining_usd": remaining,
                "usage_percent": usage_percent,
                "budget_period_days": self.budget_period_days,
                "is_over_budget": remaining < 0,
            }

    async def generate_recommendations(self) -> List[OptimizationRecommendation]:
        """Generer optimeringsanbefalinger."""
        async with self._lock:
            recommendations = []

            # Analyze recent estimates
            recent = self._estimates[-100:]  # Last 100

            if not recent:
                return []

            # Check for high API usage
            total_api_calls = sum(e.api_calls for e in recent)
            if total_api_calls > 1000:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    category="api_usage",
                    title="Reducer API kald",
                    description="Overvej at implementere caching eller batching for at reducere antal API kald",
                    estimated_savings_usd=total_api_calls * self._rates["api_call"] * 0.3,
                    priority=7,
                ))

            # Check for high token usage
            total_tokens = sum(e.tokens_used for e in recent)
            if total_tokens > 100000:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    category="token_usage",
                    title="Optimer prompt længde",
                    description="Reducer prompt længde eller brug kortere context for at spare tokens",
                    estimated_savings_usd=total_tokens * self._rates["token_input"] * 0.2,
                    priority=6,
                ))

            # Budget warning (inline calculation to avoid deadlock)
            usage_percent = (self._total_cost_usd / self.budget_usd) * 100 if self.budget_usd > 0 else 0
            if usage_percent > 80:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    category="budget",
                    title="Budget advarsel",
                    description=f"Budget er {usage_percent:.1f}% brugt. Overvej at reducere forbrug.",
                    priority=9,
                ))

            self._recommendations = recommendations
            return recommendations

    async def get_cost_breakdown(self) -> Dict[str, float]:
        """Hent cost breakdown per operation type."""
        async with self._lock:
            breakdown: Dict[str, float] = defaultdict(float)

            for estimate in self._estimates:
                cost = estimate.actual_cost_usd or estimate.estimated_cost_usd
                breakdown[estimate.operation] += cost

            return dict(breakdown)

    def set_rate(self, rate_name: str, rate_value: float) -> None:
        """Sæt custom rate."""
        self._rates[rate_name] = rate_value


# =============================================================================
# LATENCY TRACKER
# =============================================================================


class LatencyTracker:
    """
    Sporer og analyserer latency for operationer.

    Features:
    - Operation timing
    - Percentile beregning
    - Trend analyse
    - Hotspot identifikation
    """

    def __init__(self, window_size: int = 1000) -> None:
        self.window_size = window_size
        self._timings: Dict[str, List[float]] = defaultdict(list)
        self._active_operations: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    def start_operation(self, operation_id: str) -> None:
        """Start timing af en operation."""
        self._active_operations[operation_id] = time.perf_counter()

    async def end_operation(
        self,
        operation_id: str,
        operation_type: str = "default",
    ) -> float:
        """Afslut timing og returner latency i ms."""
        if operation_id not in self._active_operations:
            return 0.0

        start_time = self._active_operations.pop(operation_id)
        latency_ms = (time.perf_counter() - start_time) * 1000

        async with self._lock:
            self._timings[operation_type].append(latency_ms)

            # Trim to window size
            if len(self._timings[operation_type]) > self.window_size:
                self._timings[operation_type] = self._timings[operation_type][-self.window_size:]

        return latency_ms

    async def get_percentiles(
        self,
        operation_type: str = "default",
    ) -> Dict[str, float]:
        """Hent latency percentiles."""
        async with self._lock:
            timings = self._timings.get(operation_type, [])

            if not timings:
                return {}

            sorted_timings = sorted(timings)
            n = len(sorted_timings)

            return {
                "p50": sorted_timings[int(n * 0.50)],
                "p75": sorted_timings[int(n * 0.75)],
                "p90": sorted_timings[int(n * 0.90)],
                "p95": sorted_timings[int(n * 0.95)],
                "p99": sorted_timings[min(int(n * 0.99), n - 1)],
                "avg": sum(sorted_timings) / n,
                "min": sorted_timings[0],
                "max": sorted_timings[-1],
            }

    async def get_hotspots(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Find de langsomste operation typer."""
        async with self._lock:
            hotspots = []

            for op_type, timings in self._timings.items():
                if timings:
                    avg = sum(timings) / len(timings)
                    hotspots.append({
                        "operation_type": op_type,
                        "avg_latency_ms": avg,
                        "sample_count": len(timings),
                    })

            hotspots.sort(key=lambda x: x["avg_latency_ms"], reverse=True)
            return hotspots[:top_n]

    async def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Hent statistik for alle operation typer."""
        async with self._lock:
            return {
                op_type: {
                    "count": len(timings),
                    "avg": sum(timings) / len(timings) if timings else 0,
                    "max": max(timings) if timings else 0,
                    "min": min(timings) if timings else 0,
                }
                for op_type, timings in self._timings.items()
            }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

# Singleton instances
_performance_monitor: Optional[PerformanceMonitor] = None
_cache_manager: Optional[CacheManager] = None
_batch_processor: Optional[BatchProcessor] = None
_cost_optimizer: Optional[CostOptimizer] = None
_latency_tracker: Optional[LatencyTracker] = None


async def create_performance_monitor(
    window_size_seconds: int = 60,
    alert_cooldown_seconds: int = 300,
) -> PerformanceMonitor:
    """Factory for PerformanceMonitor."""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor(
        window_size_seconds=window_size_seconds,
        alert_cooldown_seconds=alert_cooldown_seconds,
    )
    return _performance_monitor


def get_performance_monitor() -> Optional[PerformanceMonitor]:
    """Hent eksisterende PerformanceMonitor."""
    return _performance_monitor


async def create_cache_manager(
    max_size_mb: float = 256,
    default_ttl_seconds: Optional[int] = 3600,
    eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU,
) -> CacheManager:
    """Factory for CacheManager."""
    global _cache_manager
    _cache_manager = CacheManager(
        max_size_mb=max_size_mb,
        default_ttl_seconds=default_ttl_seconds,
        eviction_policy=eviction_policy,
    )
    return _cache_manager


def get_cache_manager() -> Optional[CacheManager]:
    """Hent eksisterende CacheManager."""
    return _cache_manager


async def create_batch_processor(
    batch_size: int = 10,
    max_wait_seconds: float = 5.0,
) -> BatchProcessor:
    """Factory for BatchProcessor."""
    global _batch_processor
    _batch_processor = BatchProcessor(
        batch_size=batch_size,
        max_wait_seconds=max_wait_seconds,
    )
    return _batch_processor


def get_batch_processor() -> Optional[BatchProcessor]:
    """Hent eksisterende BatchProcessor."""
    return _batch_processor


async def create_cost_optimizer(
    budget_usd: float = 100.0,
    budget_period_days: int = 30,
) -> CostOptimizer:
    """Factory for CostOptimizer."""
    global _cost_optimizer
    _cost_optimizer = CostOptimizer(
        budget_usd=budget_usd,
        budget_period_days=budget_period_days,
    )
    return _cost_optimizer


def get_cost_optimizer() -> Optional[CostOptimizer]:
    """Hent eksisterende CostOptimizer."""
    return _cost_optimizer


async def create_latency_tracker(window_size: int = 1000) -> LatencyTracker:
    """Factory for LatencyTracker."""
    global _latency_tracker
    _latency_tracker = LatencyTracker(window_size=window_size)
    return _latency_tracker


def get_latency_tracker() -> Optional[LatencyTracker]:
    """Hent eksisterende LatencyTracker."""
    return _latency_tracker


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "MetricType",
    "OptimizationStrategy",
    "CacheEvictionPolicy",
    "AlertLevel",

    # Data classes
    "PerformanceMetric",
    "PerformanceSnapshot",
    "PerformanceAlert",
    "CacheEntry",
    "CacheStats",
    "BatchJob",
    "CostEstimate",
    "OptimizationRecommendation",

    # Classes
    "PerformanceMonitor",
    "CacheManager",
    "BatchProcessor",
    "CostOptimizer",
    "LatencyTracker",

    # Factory functions
    "create_performance_monitor",
    "get_performance_monitor",
    "create_cache_manager",
    "get_cache_manager",
    "create_batch_processor",
    "get_batch_processor",
    "create_cost_optimizer",
    "get_cost_optimizer",
    "create_latency_tracker",
    "get_latency_tracker",
]
