"""
CKC MASTERMIND - Query Optimizer (DEL AE)
=========================================

Database query optimization system for MASTERMIND operations.
Provides query analysis, caching, batching, and performance monitoring.

Features:
- Query plan analysis and suggestions
- Automatic query batching
- N+1 query detection
- Slow query logging
- Query result caching integration
- Index usage tracking
- Connection pooling coordination
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar
import asyncio
import hashlib
import logging
import time
import functools
import re

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# ENUMS
# =============================================================================

class QueryType(Enum):
    """Types of database queries."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    AGGREGATE = "aggregate"
    JOIN = "join"
    TRANSACTION = "transaction"
    DDL = "ddl"
    UNKNOWN = "unknown"


class OptimizationLevel(Enum):
    """Query optimization levels."""
    NONE = 0       # No optimization
    BASIC = 1      # Basic caching
    STANDARD = 2   # Caching + batching
    AGGRESSIVE = 3 # Full optimization
    AUTO = 4       # Adaptive optimization


class QueryPriority(Enum):
    """Priority levels for query execution."""
    CRITICAL = 0   # Execute immediately
    HIGH = 1       # High priority
    NORMAL = 2     # Normal priority
    LOW = 3        # Low priority, can be batched
    BACKGROUND = 4 # Execute when idle


class IndexStatus(Enum):
    """Status of index usage."""
    USED = "used"
    UNUSED = "unused"
    MISSING = "missing"
    RECOMMENDED = "recommended"


class QueryHealth(Enum):
    """Health status of query patterns."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QueryOptimizerConfig:
    """Configuration for query optimizer."""
    enabled: bool = True
    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    slow_query_threshold_ms: float = 100.0
    very_slow_query_threshold_ms: float = 1000.0
    max_query_history: int = 1000
    batch_window_ms: int = 10
    max_batch_size: int = 50
    enable_query_cache: bool = True
    cache_ttl_seconds: int = 60
    enable_n_plus_one_detection: bool = True
    n_plus_one_threshold: int = 5
    enable_index_suggestions: bool = True
    enable_auto_explain: bool = False
    log_all_queries: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryInfo:
    """Information about a database query."""
    query_id: str
    query_type: QueryType
    query_text: str
    parameters: Dict[str, Any]
    timestamp: datetime
    duration_ms: float
    rows_affected: int = 0
    rows_returned: int = 0
    was_cached: bool = False
    was_batched: bool = False
    caller: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_fingerprint(self) -> str:
        """Get query fingerprint (normalized for caching)."""
        # Remove parameter values, keep structure
        normalized = re.sub(r"'[^']*'", "'?'", self.query_text)
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def is_slow(self, threshold_ms: float = 100.0) -> bool:
        """Check if query is slow."""
        return self.duration_ms >= threshold_ms


@dataclass
class QueryPlan:
    """Execution plan for a query."""
    query_fingerprint: str
    plan_type: str
    estimated_cost: float
    actual_time_ms: float
    rows_scanned: int
    rows_returned: int
    indexes_used: List[str]
    indexes_missing: List[str]
    suggestions: List[str]
    raw_plan: Optional[Dict[str, Any]] = None


@dataclass
class BatchedQuery:
    """A query waiting in the batch queue."""
    query_id: str
    query_text: str
    parameters: Dict[str, Any]
    priority: QueryPriority
    callback: Optional[Callable[[Any], None]]
    created_at: datetime
    timeout_ms: float = 5000.0


@dataclass
class NPlusOnePattern:
    """Detected N+1 query pattern."""
    pattern_id: str
    base_query: str
    child_query: str
    occurrence_count: int
    total_time_ms: float
    first_detected: datetime
    last_detected: datetime
    suggested_fix: str


@dataclass
class QueryMetrics:
    """Metrics for query performance."""
    total_queries: int = 0
    cached_queries: int = 0
    batched_queries: int = 0
    slow_queries: int = 0
    very_slow_queries: int = 0
    n_plus_one_detected: int = 0
    avg_query_time_ms: float = 0.0
    p50_query_time_ms: float = 0.0
    p95_query_time_ms: float = 0.0
    p99_query_time_ms: float = 0.0
    queries_by_type: Dict[str, int] = field(default_factory=dict)
    cache_hit_rate: float = 0.0


@dataclass
class IndexRecommendation:
    """Recommendation for a new index."""
    table_name: str
    columns: List[str]
    index_type: str
    reason: str
    estimated_improvement: float
    query_patterns: List[str]
    priority: int = 5


# =============================================================================
# QUERY ANALYZER
# =============================================================================

class QueryAnalyzer:
    """Analyzes queries for optimization opportunities."""

    def __init__(self):
        self._query_patterns: Dict[str, List[QueryInfo]] = {}
        self._n_plus_one_candidates: Dict[str, List[str]] = {}

    def analyze_query(self, query_info: QueryInfo) -> Dict[str, Any]:
        """Analyze a query for optimization opportunities."""
        fingerprint = query_info.get_fingerprint()
        analysis = {
            "fingerprint": fingerprint,
            "query_type": query_info.query_type.value,
            "is_slow": query_info.is_slow(),
            "suggestions": [],
            "warnings": []
        }

        # Track pattern
        if fingerprint not in self._query_patterns:
            self._query_patterns[fingerprint] = []
        self._query_patterns[fingerprint].append(query_info)

        # Check for common issues
        query_lower = query_info.query_text.lower()

        # SELECT * detection
        if "select *" in query_lower:
            analysis["suggestions"].append(
                "Consider selecting specific columns instead of SELECT *"
            )

        # Missing WHERE clause
        if query_info.query_type == QueryType.SELECT and "where" not in query_lower:
            analysis["warnings"].append(
                "SELECT without WHERE clause may return too many rows"
            )

        # LIKE with leading wildcard
        if "like '%" in query_lower:
            analysis["suggestions"].append(
                "LIKE with leading wildcard cannot use indexes efficiently"
            )

        # ORDER BY without LIMIT
        if "order by" in query_lower and "limit" not in query_lower:
            analysis["suggestions"].append(
                "Consider adding LIMIT to ORDER BY queries"
            )

        # DISTINCT detection
        if "distinct" in query_lower:
            analysis["suggestions"].append(
                "DISTINCT may indicate a need for better data modeling"
            )

        return analysis

    def detect_n_plus_one(
        self,
        query_info: QueryInfo,
        threshold: int = 5
    ) -> Optional[NPlusOnePattern]:
        """Detect N+1 query patterns."""
        fingerprint = query_info.get_fingerprint()
        caller = query_info.caller

        if caller not in self._n_plus_one_candidates:
            self._n_plus_one_candidates[caller] = []

        self._n_plus_one_candidates[caller].append(fingerprint)

        # Check if same query repeated from same caller
        recent = self._n_plus_one_candidates[caller][-threshold*2:]
        if len(recent) >= threshold:
            counts = {}
            for fp in recent:
                counts[fp] = counts.get(fp, 0) + 1

            for fp, count in counts.items():
                if count >= threshold:
                    return NPlusOnePattern(
                        pattern_id=f"n1_{fingerprint}",
                        base_query=caller,
                        child_query=query_info.query_text[:100],
                        occurrence_count=count,
                        total_time_ms=query_info.duration_ms * count,
                        first_detected=datetime.utcnow(),
                        last_detected=datetime.utcnow(),
                        suggested_fix="Consider using JOIN or batch fetching"
                    )

        return None

    def get_index_recommendations(
        self,
        query_info: QueryInfo
    ) -> List[IndexRecommendation]:
        """Get index recommendations for a query."""
        recommendations = []
        query_lower = query_info.query_text.lower()

        # Extract table name (simple heuristic)
        table_match = re.search(r'from\s+(\w+)', query_lower)
        if not table_match:
            return recommendations

        table_name = table_match.group(1)

        # Extract WHERE columns
        where_match = re.search(r'where\s+(.+?)(?:order|group|limit|$)', query_lower)
        if where_match:
            where_clause = where_match.group(1)
            # Extract column names from conditions
            columns = re.findall(r'(\w+)\s*[=<>!]', where_clause)
            if columns and query_info.is_slow():
                recommendations.append(IndexRecommendation(
                    table_name=table_name,
                    columns=columns[:3],  # Max 3 columns
                    index_type="btree",
                    reason=f"Query took {query_info.duration_ms:.1f}ms",
                    estimated_improvement=0.5,
                    query_patterns=[query_info.get_fingerprint()]
                ))

        # Extract ORDER BY columns
        order_match = re.search(r'order by\s+(\w+)', query_lower)
        if order_match and query_info.is_slow():
            order_col = order_match.group(1)
            recommendations.append(IndexRecommendation(
                table_name=table_name,
                columns=[order_col],
                index_type="btree",
                reason="Sort optimization",
                estimated_improvement=0.3,
                query_patterns=[query_info.get_fingerprint()]
            ))

        return recommendations


# =============================================================================
# QUERY BATCHER
# =============================================================================

class QueryBatcher:
    """Batches similar queries for efficient execution."""

    def __init__(self, config: QueryOptimizerConfig):
        self.config = config
        self._pending_queries: Dict[str, List[BatchedQuery]] = {}
        self._batch_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the batcher."""
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        """Stop the batcher."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush remaining
        await self._flush_all()

    async def add_query(
        self,
        query_text: str,
        parameters: Dict[str, Any],
        priority: QueryPriority = QueryPriority.LOW,
        callback: Optional[Callable] = None
    ) -> str:
        """Add a query to the batch queue."""
        import uuid
        query_id = f"batch_{uuid.uuid4().hex[:8]}"

        # Create fingerprint for grouping
        fingerprint = hashlib.md5(query_text.encode()).hexdigest()[:12]

        batched = BatchedQuery(
            query_id=query_id,
            query_text=query_text,
            parameters=parameters,
            priority=priority,
            callback=callback,
            created_at=datetime.utcnow()
        )

        async with self._batch_lock:
            if fingerprint not in self._pending_queries:
                self._pending_queries[fingerprint] = []
            self._pending_queries[fingerprint].append(batched)

            # Check if batch should be flushed
            if len(self._pending_queries[fingerprint]) >= self.config.max_batch_size:
                await self._flush_batch(fingerprint)

        return query_id

    async def _flush_loop(self) -> None:
        """Periodically flush batches."""
        while self._running:
            try:
                await asyncio.sleep(self.config.batch_window_ms / 1000)
                await self._flush_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch flush error: {e}")

    async def _flush_all(self) -> None:
        """Flush all pending batches."""
        async with self._batch_lock:
            fingerprints = list(self._pending_queries.keys())

        for fp in fingerprints:
            await self._flush_batch(fp)

    async def _flush_batch(self, fingerprint: str) -> None:
        """Flush a specific batch."""
        async with self._batch_lock:
            if fingerprint not in self._pending_queries:
                return

            batch = self._pending_queries.pop(fingerprint)

        if not batch:
            return

        # Execute batch (simplified - real implementation would combine queries)
        logger.debug(f"Flushing batch of {len(batch)} queries ({fingerprint})")

        for query in batch:
            if query.callback:
                try:
                    query.callback(None)  # Would pass actual result
                except Exception as e:
                    logger.error(f"Batch callback error: {e}")


# =============================================================================
# MAIN CLASS: QueryOptimizer
# =============================================================================

class QueryOptimizer:
    """
    Central query optimization system for MASTERMIND.

    Provides:
    - Query analysis and suggestions
    - Automatic batching for similar queries
    - N+1 detection and alerting
    - Slow query logging
    - Index recommendations
    """

    def __init__(self, config: Optional[QueryOptimizerConfig] = None):
        self.config = config or QueryOptimizerConfig()

        # Components
        self._analyzer = QueryAnalyzer()
        self._batcher = QueryBatcher(self.config)

        # Storage
        self._query_history: List[QueryInfo] = []
        self._slow_queries: List[QueryInfo] = []
        self._n_plus_one_patterns: Dict[str, NPlusOnePattern] = {}
        self._index_recommendations: List[IndexRecommendation] = []

        # Metrics
        self._metrics = QueryMetrics()
        self._query_times: List[float] = []

        # State
        self._running = False
        self._start_time = datetime.utcnow()

        logger.info("QueryOptimizer initialized")

    async def start(self) -> None:
        """Start the optimizer."""
        self._running = True
        self._start_time = datetime.utcnow()

        if self.config.optimization_level.value >= OptimizationLevel.STANDARD.value:
            await self._batcher.start()

        logger.info("QueryOptimizer started")

    async def stop(self) -> None:
        """Stop the optimizer."""
        self._running = False
        await self._batcher.stop()
        logger.info("QueryOptimizer stopped")

    # ========== Query Tracking ==========

    def track_query(
        self,
        query_text: str,
        parameters: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        rows_affected: int = 0,
        rows_returned: int = 0,
        was_cached: bool = False,
        caller: str = ""
    ) -> QueryInfo:
        """
        Track a query execution.

        Call this after executing any database query.
        """
        import uuid

        # Determine query type
        query_type = self._detect_query_type(query_text)

        query_info = QueryInfo(
            query_id=f"q_{uuid.uuid4().hex[:8]}",
            query_type=query_type,
            query_text=query_text,
            parameters=parameters or {},
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            rows_returned=rows_returned,
            was_cached=was_cached,
            caller=caller
        )

        # Store in history
        self._query_history.append(query_info)
        self._trim_history()

        # Track timing
        self._query_times.append(duration_ms)
        if len(self._query_times) > 1000:
            self._query_times = self._query_times[-1000:]

        # Update metrics
        self._update_metrics(query_info)

        # Analyze if enabled
        if self.config.enabled:
            self._analyze_query(query_info)

        # Log if configured
        if self.config.log_all_queries:
            logger.debug(
                f"Query: {query_type.value} | {duration_ms:.1f}ms | "
                f"{rows_returned} rows | {query_text[:50]}..."
            )

        return query_info

    def _detect_query_type(self, query_text: str) -> QueryType:
        """Detect the type of query."""
        query_upper = query_text.strip().upper()

        if query_upper.startswith("SELECT"):
            if "COUNT(" in query_upper or "SUM(" in query_upper:
                return QueryType.AGGREGATE
            if "JOIN" in query_upper:
                return QueryType.JOIN
            return QueryType.SELECT
        elif query_upper.startswith("INSERT"):
            return QueryType.INSERT
        elif query_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        elif query_upper.startswith("DELETE"):
            return QueryType.DELETE
        elif query_upper.startswith(("CREATE", "ALTER", "DROP")):
            return QueryType.DDL
        elif query_upper.startswith(("BEGIN", "COMMIT", "ROLLBACK")):
            return QueryType.TRANSACTION

        return QueryType.UNKNOWN

    def _analyze_query(self, query_info: QueryInfo) -> None:
        """Analyze a query for optimization opportunities."""
        # Run analyzer
        analysis = self._analyzer.analyze_query(query_info)

        # Check for slow queries
        if query_info.is_slow(self.config.slow_query_threshold_ms):
            self._slow_queries.append(query_info)
            self._metrics.slow_queries += 1

            if query_info.is_slow(self.config.very_slow_query_threshold_ms):
                self._metrics.very_slow_queries += 1
                logger.warning(
                    f"Very slow query ({query_info.duration_ms:.1f}ms): "
                    f"{query_info.query_text[:100]}..."
                )

        # N+1 detection
        if self.config.enable_n_plus_one_detection:
            n_plus_one = self._analyzer.detect_n_plus_one(
                query_info,
                self.config.n_plus_one_threshold
            )
            if n_plus_one:
                self._n_plus_one_patterns[n_plus_one.pattern_id] = n_plus_one
                self._metrics.n_plus_one_detected += 1
                logger.warning(
                    f"N+1 pattern detected: {n_plus_one.child_query[:50]}... "
                    f"({n_plus_one.occurrence_count} occurrences)"
                )

        # Index recommendations
        if self.config.enable_index_suggestions:
            recommendations = self._analyzer.get_index_recommendations(query_info)
            for rec in recommendations:
                self._index_recommendations.append(rec)

    def _update_metrics(self, query_info: QueryInfo) -> None:
        """Update query metrics."""
        self._metrics.total_queries += 1

        if query_info.was_cached:
            self._metrics.cached_queries += 1

        if query_info.was_batched:
            self._metrics.batched_queries += 1

        # Type counting
        type_key = query_info.query_type.value
        self._metrics.queries_by_type[type_key] = \
            self._metrics.queries_by_type.get(type_key, 0) + 1

        # Timing metrics
        if self._query_times:
            times = sorted(self._query_times)
            n = len(times)
            self._metrics.avg_query_time_ms = sum(times) / n
            self._metrics.p50_query_time_ms = times[int(n * 0.5)]
            self._metrics.p95_query_time_ms = times[int(n * 0.95)] if n > 20 else times[-1]
            self._metrics.p99_query_time_ms = times[int(n * 0.99)] if n > 100 else times[-1]

        # Cache hit rate
        if self._metrics.total_queries > 0:
            self._metrics.cache_hit_rate = \
                self._metrics.cached_queries / self._metrics.total_queries

    def _trim_history(self) -> None:
        """Trim query history to max size."""
        while len(self._query_history) > self.config.max_query_history:
            self._query_history.pop(0)

        while len(self._slow_queries) > self.config.max_query_history // 10:
            self._slow_queries.pop(0)

    # ========== Query Execution Helpers ==========

    def query_decorator(
        self,
        caller: str = ""
    ) -> Callable:
        """
        Decorator to automatically track query execution.

        Usage:
            @optimizer.query_decorator("user_service")
            async def get_users():
                return await db.execute("SELECT * FROM users")
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = await func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000

                # Extract query from args if possible
                query_text = str(args[0]) if args else "unknown"

                self.track_query(
                    query_text=query_text,
                    duration_ms=duration,
                    caller=caller or func.__name__
                )

                return result
            return wrapper
        return decorator

    async def execute_batched(
        self,
        query_text: str,
        parameters: Optional[Dict[str, Any]] = None,
        priority: QueryPriority = QueryPriority.LOW
    ) -> str:
        """
        Add a query to the batch queue.

        Returns query ID for tracking.
        """
        return await self._batcher.add_query(
            query_text=query_text,
            parameters=parameters or {},
            priority=priority
        )

    # ========== Analysis & Reporting ==========

    def get_slow_queries(
        self,
        limit: int = 20,
        min_duration_ms: Optional[float] = None
    ) -> List[QueryInfo]:
        """Get list of slow queries."""
        queries = self._slow_queries
        if min_duration_ms:
            queries = [q for q in queries if q.duration_ms >= min_duration_ms]
        return sorted(queries, key=lambda q: -q.duration_ms)[:limit]

    def get_n_plus_one_patterns(self) -> List[NPlusOnePattern]:
        """Get detected N+1 patterns."""
        return list(self._n_plus_one_patterns.values())

    def get_index_recommendations(
        self,
        min_priority: int = 0
    ) -> List[IndexRecommendation]:
        """Get index recommendations."""
        recs = [r for r in self._index_recommendations if r.priority >= min_priority]
        return sorted(recs, key=lambda r: -r.priority)

    def get_query_distribution(self) -> Dict[str, int]:
        """Get distribution of query types."""
        return dict(self._metrics.queries_by_type)

    def get_health(self) -> QueryHealth:
        """Get overall query health status."""
        if self._metrics.total_queries == 0:
            return QueryHealth.UNKNOWN

        slow_rate = self._metrics.slow_queries / self._metrics.total_queries
        n_plus_one_rate = self._metrics.n_plus_one_detected / self._metrics.total_queries

        if slow_rate > 0.2 or n_plus_one_rate > 0.1:
            return QueryHealth.CRITICAL
        elif slow_rate > 0.1 or n_plus_one_rate > 0.05:
            return QueryHealth.WARNING
        else:
            return QueryHealth.HEALTHY

    def get_metrics(self) -> QueryMetrics:
        """Get query metrics."""
        return self._metrics

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return {
            "total_queries": self._metrics.total_queries,
            "cached_queries": self._metrics.cached_queries,
            "batched_queries": self._metrics.batched_queries,
            "slow_queries": self._metrics.slow_queries,
            "very_slow_queries": self._metrics.very_slow_queries,
            "n_plus_one_detected": self._metrics.n_plus_one_detected,
            "timing": {
                "avg_ms": self._metrics.avg_query_time_ms,
                "p50_ms": self._metrics.p50_query_time_ms,
                "p95_ms": self._metrics.p95_query_time_ms,
                "p99_ms": self._metrics.p99_query_time_ms
            },
            "cache_hit_rate": self._metrics.cache_hit_rate,
            "queries_by_type": self._metrics.queries_by_type,
            "health": self.get_health().value,
            "index_recommendations": len(self._index_recommendations),
            "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds()
        }

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics = QueryMetrics()
        self._query_times = []
        self._slow_queries = []
        self._n_plus_one_patterns = {}
        logger.info("QueryOptimizer metrics reset")


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_query_optimizer: Optional[QueryOptimizer] = None


def create_query_optimizer(
    config: Optional[QueryOptimizerConfig] = None
) -> QueryOptimizer:
    """Create a new query optimizer."""
    return QueryOptimizer(config)


def get_query_optimizer() -> Optional[QueryOptimizer]:
    """Get the global query optimizer."""
    return _query_optimizer


def set_query_optimizer(optimizer: QueryOptimizer) -> None:
    """Set the global query optimizer."""
    global _query_optimizer
    _query_optimizer = optimizer


def track_query(
    query_text: str,
    duration_ms: float,
    **kwargs
) -> Optional[QueryInfo]:
    """Convenience function to track a query."""
    optimizer = get_query_optimizer()
    if optimizer:
        return optimizer.track_query(query_text, duration_ms=duration_ms, **kwargs)
    return None


def get_slow_queries(limit: int = 20) -> List[QueryInfo]:
    """Convenience function to get slow queries."""
    optimizer = get_query_optimizer()
    if optimizer:
        return optimizer.get_slow_queries(limit)
    return []


async def create_mastermind_query_optimizer() -> QueryOptimizer:
    """
    Create and configure query optimizer for MASTERMIND.
    """
    config = QueryOptimizerConfig(
        enabled=True,
        optimization_level=OptimizationLevel.STANDARD,
        slow_query_threshold_ms=100.0,
        very_slow_query_threshold_ms=500.0,
        enable_n_plus_one_detection=True,
        enable_index_suggestions=True
    )

    optimizer = create_query_optimizer(config)
    set_query_optimizer(optimizer)
    await optimizer.start()

    logger.info("MASTERMIND query optimizer created and started")
    return optimizer


__all__ = [
    # Enums
    "QueryType",
    "OptimizationLevel",
    "QueryPriority",
    "IndexStatus",
    "QueryHealth",

    # Data classes
    "QueryOptimizerConfig",
    "QueryInfo",
    "QueryPlan",
    "BatchedQuery",
    "NPlusOnePattern",
    "QueryMetrics",
    "IndexRecommendation",

    # Classes
    "QueryAnalyzer",
    "QueryBatcher",
    "QueryOptimizer",

    # Factory functions
    "create_query_optimizer",
    "get_query_optimizer",
    "set_query_optimizer",
    "track_query",
    "get_slow_queries",
    "create_mastermind_query_optimizer",
]
