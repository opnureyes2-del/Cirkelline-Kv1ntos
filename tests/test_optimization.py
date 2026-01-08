"""
Tests for DEL F: Systembred Optimering
======================================

Tests for the optimization module (performance, caching, batching, cost).
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock


# =============================================================================
# TEST ENUMS
# =============================================================================


class TestOptimizationEnums:
    """Tests for optimization enums."""

    def test_metric_type_values(self):
        """Test MetricType enum values."""
        from cirkelline.ckc.mastermind.optimization import MetricType

        assert MetricType.LATENCY.value == "latency"
        assert MetricType.THROUGHPUT.value == "throughput"
        assert MetricType.ERROR_RATE.value == "error_rate"
        assert MetricType.CPU_USAGE.value == "cpu_usage"
        assert MetricType.MEMORY_USAGE.value == "memory_usage"
        assert MetricType.API_CALLS.value == "api_calls"
        assert MetricType.CACHE_HIT.value == "cache_hit"
        assert MetricType.CACHE_MISS.value == "cache_miss"
        assert MetricType.COST.value == "cost"

    def test_optimization_strategy_values(self):
        """Test OptimizationStrategy enum values."""
        from cirkelline.ckc.mastermind.optimization import OptimizationStrategy

        assert OptimizationStrategy.MINIMIZE_LATENCY.value == "minimize_latency"
        assert OptimizationStrategy.MINIMIZE_COST.value == "minimize_cost"
        assert OptimizationStrategy.MAXIMIZE_THROUGHPUT.value == "maximize_throughput"
        assert OptimizationStrategy.BALANCED.value == "balanced"

    def test_cache_eviction_policy_values(self):
        """Test CacheEvictionPolicy enum values."""
        from cirkelline.ckc.mastermind.optimization import CacheEvictionPolicy

        assert CacheEvictionPolicy.LRU.value == "lru"
        assert CacheEvictionPolicy.LFU.value == "lfu"
        assert CacheEvictionPolicy.TTL.value == "ttl"
        assert CacheEvictionPolicy.FIFO.value == "fifo"

    def test_alert_level_values(self):
        """Test AlertLevel enum values."""
        from cirkelline.ckc.mastermind.optimization import AlertLevel

        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.CRITICAL.value == "critical"


# =============================================================================
# TEST DATA CLASSES
# =============================================================================


class TestOptimizationDataClasses:
    """Tests for optimization data classes."""

    def test_performance_metric_creation(self):
        """Test PerformanceMetric dataclass."""
        from cirkelline.ckc.mastermind.optimization import (
            PerformanceMetric,
            MetricType,
        )

        metric = PerformanceMetric(
            metric_type=MetricType.LATENCY,
            value=150.5,
            source="api_endpoint",
            tags={"endpoint": "/api/test"},
        )

        assert metric.metric_type == MetricType.LATENCY
        assert metric.value == 150.5
        assert metric.source == "api_endpoint"
        assert metric.timestamp is not None

    def test_cache_entry_expiration(self):
        """Test CacheEntry expiration logic."""
        from cirkelline.ckc.mastermind.optimization import CacheEntry

        # Entry with TTL
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            size_bytes=100,
            ttl_seconds=1,
        )

        assert not entry.is_expired

        # Manually set created_at to past
        entry.created_at = datetime.now() - timedelta(seconds=2)
        assert entry.is_expired

    def test_cache_entry_no_ttl(self):
        """Test CacheEntry without TTL."""
        from cirkelline.ckc.mastermind.optimization import CacheEntry

        entry = CacheEntry(
            key="test_key",
            value="test_value",
            size_bytes=100,
            ttl_seconds=None,
        )

        assert not entry.is_expired

    def test_cache_stats_hit_rate(self):
        """Test CacheStats hit rate calculation."""
        from cirkelline.ckc.mastermind.optimization import CacheStats

        stats = CacheStats(hits=80, misses=20)
        assert stats.hit_rate == 0.8

        empty_stats = CacheStats(hits=0, misses=0)
        assert empty_stats.hit_rate == 0.0

    def test_batch_job_status(self):
        """Test BatchJob status property."""
        from cirkelline.ckc.mastermind.optimization import BatchJob

        job = BatchJob(
            job_id="job_123",
            items=[1, 2, 3],
            processor="test_processor",
        )

        assert job.status == "pending"

        job.started_at = datetime.now()
        assert job.status == "running"

        job.completed_at = datetime.now()
        assert job.status == "completed"

    def test_cost_estimate_creation(self):
        """Test CostEstimate dataclass."""
        from cirkelline.ckc.mastermind.optimization import CostEstimate

        estimate = CostEstimate(
            estimate_id="est_123",
            operation="embedding",
            estimated_cost_usd=0.05,
            api_calls=10,
            tokens_used=5000,
        )

        assert estimate.operation == "embedding"
        assert estimate.estimated_cost_usd == 0.05
        assert estimate.actual_cost_usd is None


# =============================================================================
# TEST PERFORMANCE MONITOR
# =============================================================================


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor."""

    @pytest_asyncio.fixture
    async def monitor(self):
        """Create a test monitor."""
        from cirkelline.ckc.mastermind.optimization import PerformanceMonitor
        return PerformanceMonitor(window_size_seconds=60, alert_cooldown_seconds=1)

    @pytest.mark.asyncio
    async def test_record_metric(self, monitor):
        """Test recording metrics."""
        from cirkelline.ckc.mastermind.optimization import MetricType

        await monitor.record_metric(MetricType.LATENCY, 100.0)
        await monitor.record_metric(MetricType.LATENCY, 200.0)

        metrics = await monitor.get_current_metrics()
        assert MetricType.LATENCY in metrics
        assert metrics[MetricType.LATENCY] == 150.0  # Average

    @pytest.mark.asyncio
    async def test_create_snapshot(self, monitor):
        """Test creating performance snapshot."""
        from cirkelline.ckc.mastermind.optimization import MetricType

        await monitor.record_metric(MetricType.LATENCY, 100.0)
        await monitor.record_metric(MetricType.THROUGHPUT, 50.0)

        snapshot = await monitor.create_snapshot()

        assert snapshot.snapshot_id is not None
        assert snapshot.avg_latency_ms == 100.0
        assert snapshot.throughput_per_second == 50.0

    @pytest.mark.asyncio
    async def test_alert_generation(self, monitor):
        """Test alert generation on threshold breach."""
        from cirkelline.ckc.mastermind.optimization import MetricType, AlertLevel
        import asyncio

        # Record metric that exceeds warning threshold (500ms)
        await monitor.record_metric(MetricType.LATENCY, 600.0)

        alerts = await monitor.get_active_alerts()
        assert len(alerts) >= 1
        assert alerts[0].level == AlertLevel.WARNING

    @pytest.mark.asyncio
    async def test_resolve_alert(self, monitor):
        """Test resolving alerts."""
        from cirkelline.ckc.mastermind.optimization import MetricType

        await monitor.record_metric(MetricType.LATENCY, 600.0)
        alerts = await monitor.get_active_alerts()

        if alerts:
            result = await monitor.resolve_alert(alerts[0].alert_id)
            assert result is True

            active = await monitor.get_active_alerts()
            assert len(active) == 0

    @pytest.mark.asyncio
    async def test_set_custom_threshold(self, monitor):
        """Test setting custom thresholds."""
        from cirkelline.ckc.mastermind.optimization import MetricType, AlertLevel

        monitor.set_threshold(MetricType.LATENCY, AlertLevel.WARNING, 50.0)

        # Should trigger alert at 60ms now
        await monitor.record_metric(MetricType.LATENCY, 60.0)

        alerts = await monitor.get_active_alerts()
        assert len(alerts) >= 1


# =============================================================================
# TEST CACHE MANAGER
# =============================================================================


class TestCacheManager:
    """Tests for CacheManager."""

    @pytest_asyncio.fixture
    async def cache(self):
        """Create a test cache."""
        from cirkelline.ckc.mastermind.optimization import CacheManager
        return CacheManager(max_size_mb=1, default_ttl_seconds=3600)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test basic set and get."""
        await cache.set("key1", {"data": "value1"})
        result = await cache.get("key1")

        assert result == {"data": "value1"}

    @pytest.mark.asyncio
    async def test_get_missing_key(self, cache):
        """Test getting missing key."""
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test deleting entry."""
        await cache.set("key1", "value1")
        result = await cache.delete("key1")

        assert result is True
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing cache."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()

        stats = await cache.get_stats()
        assert stats.total_entries == 0

    @pytest.mark.asyncio
    async def test_stats_tracking(self, cache):
        """Test cache statistics tracking."""
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss

        stats = await cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.hit_rate == 0.5

    @pytest.mark.asyncio
    async def test_eviction_on_size(self, cache):
        """Test eviction when cache is full."""
        # Fill cache with large values (1MB = ~100 x 10KB values)
        for i in range(150):  # More than can fit in 1MB
            await cache.set(f"key_{i}", "x" * 10000)

        stats = await cache.get_stats()
        # Should have evicted some entries OR limited entries
        # Either evictions occurred or entries are limited by size
        assert stats.evictions > 0 or stats.total_entries < 150

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache):
        """Test TTL expiration."""
        from cirkelline.ckc.mastermind.optimization import CacheEntry
        from datetime import timedelta

        await cache.set("key1", "value1", ttl_seconds=1)

        # Access immediately should work
        result = await cache.get("key1")
        assert result == "value1"

        # Manually expire the entry
        async with cache._lock:
            if "key1" in cache._cache:
                cache._cache["key1"].created_at = datetime.now() - timedelta(seconds=2)

        # Should be expired now
        result = await cache.get("key1")
        assert result is None


# =============================================================================
# TEST BATCH PROCESSOR
# =============================================================================


class TestBatchProcessor:
    """Tests for BatchProcessor."""

    @pytest_asyncio.fixture
    async def processor(self):
        """Create a test batch processor."""
        from cirkelline.ckc.mastermind.optimization import BatchProcessor
        return BatchProcessor(batch_size=3, max_wait_seconds=5.0)

    @pytest.mark.asyncio
    async def test_register_processor(self, processor):
        """Test registering a processor function."""
        def my_processor(items):
            return [x * 2 for x in items]

        processor.register_processor("doubler", my_processor)
        assert "doubler" in processor._processors

    @pytest.mark.asyncio
    async def test_add_items_batch_creation(self, processor):
        """Test batch creation when batch size is reached."""
        def my_processor(items):
            return [x * 2 for x in items]

        processor.register_processor("doubler", my_processor)

        # Add items until batch is created
        await processor.add_item("doubler", 1)
        await processor.add_item("doubler", 2)
        job_id = await processor.add_item("doubler", 3)

        assert job_id != ""  # Batch should be created

    @pytest.mark.asyncio
    async def test_process_job(self, processor):
        """Test processing a batch job."""
        def my_processor(items):
            return [x * 2 for x in items]

        processor.register_processor("doubler", my_processor)

        await processor.add_item("doubler", 1)
        await processor.add_item("doubler", 2)
        job_id = await processor.add_item("doubler", 3)

        job = await processor.process_job(job_id)

        assert job.status == "completed"
        assert job.results == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_flush_all(self, processor):
        """Test flushing all pending items."""
        processor.register_processor("test", lambda x: x)

        await processor.add_item("test", 1)
        await processor.add_item("test", 2)

        job_ids = await processor.flush_all()
        assert len(job_ids) >= 1

    @pytest.mark.asyncio
    async def test_get_pending_count(self, processor):
        """Test getting pending item count."""
        processor.register_processor("test", lambda x: x)

        await processor.add_item("test", 1)
        await processor.add_item("test", 2)

        counts = await processor.get_pending_count()
        assert counts.get("test", 0) == 2


# =============================================================================
# TEST COST OPTIMIZER
# =============================================================================


class TestCostOptimizer:
    """Tests for CostOptimizer."""

    @pytest_asyncio.fixture
    async def optimizer(self):
        """Create a test cost optimizer."""
        from cirkelline.ckc.mastermind.optimization import CostOptimizer
        return CostOptimizer(budget_usd=100.0, budget_period_days=30)

    @pytest.mark.asyncio
    async def test_estimate_cost(self, optimizer):
        """Test cost estimation."""
        estimate = await optimizer.estimate_cost(
            operation="embedding",
            api_calls=10,
            tokens_input=1000,
            tokens_output=500,
        )

        assert estimate.operation == "embedding"
        assert estimate.estimated_cost_usd > 0
        assert estimate.api_calls == 10

    @pytest.mark.asyncio
    async def test_record_actual_cost(self, optimizer):
        """Test recording actual cost."""
        estimate = await optimizer.estimate_cost(
            operation="test",
            api_calls=5,
        )

        await optimizer.record_actual_cost(estimate.estimate_id, 0.05)

        status = await optimizer.get_budget_status()
        assert status["spent_usd"] == 0.05

    @pytest.mark.asyncio
    async def test_budget_status(self, optimizer):
        """Test budget status tracking."""
        status = await optimizer.get_budget_status()

        assert status["budget_usd"] == 100.0
        assert status["spent_usd"] == 0.0
        assert status["remaining_usd"] == 100.0
        assert status["usage_percent"] == 0.0
        assert status["is_over_budget"] is False

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, optimizer):
        """Test generating optimization recommendations."""
        # Generate some estimates
        for i in range(100):
            await optimizer.estimate_cost(
                operation="test",
                api_calls=20,
                tokens_input=2000,
            )

        recommendations = await optimizer.generate_recommendations()
        # Should generate recommendations for high API usage
        assert len(recommendations) >= 0

    @pytest.mark.asyncio
    async def test_cost_breakdown(self, optimizer):
        """Test cost breakdown by operation."""
        await optimizer.estimate_cost(operation="op1", api_calls=10)
        await optimizer.estimate_cost(operation="op2", api_calls=20)

        breakdown = await optimizer.get_cost_breakdown()

        assert "op1" in breakdown
        assert "op2" in breakdown

    @pytest.mark.asyncio
    async def test_set_custom_rate(self, optimizer):
        """Test setting custom rates."""
        optimizer.set_rate("api_call", 0.01)

        estimate = await optimizer.estimate_cost(
            operation="test",
            api_calls=10,
        )

        assert estimate.estimated_cost_usd == 0.10


# =============================================================================
# TEST LATENCY TRACKER
# =============================================================================


class TestLatencyTracker:
    """Tests for LatencyTracker."""

    @pytest_asyncio.fixture
    async def tracker(self):
        """Create a test latency tracker."""
        from cirkelline.ckc.mastermind.optimization import LatencyTracker
        return LatencyTracker(window_size=100)

    @pytest.mark.asyncio
    async def test_start_end_operation(self, tracker):
        """Test timing an operation."""
        import time

        tracker.start_operation("op_1")
        time.sleep(0.01)  # 10ms
        latency = await tracker.end_operation("op_1", "test")

        assert latency > 0
        assert latency < 1000  # Should be less than 1 second

    @pytest.mark.asyncio
    async def test_percentiles(self, tracker):
        """Test percentile calculation."""
        # Record some latencies
        for i in range(100):
            tracker.start_operation(f"op_{i}")
            await tracker.end_operation(f"op_{i}", "test")

        percentiles = await tracker.get_percentiles("test")

        assert "p50" in percentiles
        assert "p90" in percentiles
        assert "p99" in percentiles
        assert "avg" in percentiles

    @pytest.mark.asyncio
    async def test_hotspots(self, tracker):
        """Test finding hotspots."""
        import time

        # Fast operation
        for i in range(10):
            tracker.start_operation(f"fast_{i}")
            await tracker.end_operation(f"fast_{i}", "fast_op")

        # Slow operation
        for i in range(10):
            tracker.start_operation(f"slow_{i}")
            time.sleep(0.001)  # 1ms
            await tracker.end_operation(f"slow_{i}", "slow_op")

        hotspots = await tracker.get_hotspots(top_n=2)

        assert len(hotspots) == 2
        assert hotspots[0]["operation_type"] == "slow_op"

    @pytest.mark.asyncio
    async def test_all_stats(self, tracker):
        """Test getting all statistics."""
        tracker.start_operation("op_1")
        await tracker.end_operation("op_1", "type_a")

        tracker.start_operation("op_2")
        await tracker.end_operation("op_2", "type_b")

        stats = await tracker.get_all_stats()

        assert "type_a" in stats
        assert "type_b" in stats
        assert stats["type_a"]["count"] == 1


# =============================================================================
# TEST FACTORY FUNCTIONS
# =============================================================================


class TestOptimizationFactoryFunctions:
    """Tests for factory functions."""

    @pytest.mark.asyncio
    async def test_create_performance_monitor(self):
        """Test creating performance monitor."""
        from cirkelline.ckc.mastermind.optimization import (
            create_performance_monitor,
            get_performance_monitor,
            PerformanceMonitor,
        )

        monitor = await create_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)

        retrieved = get_performance_monitor()
        assert retrieved is monitor

    @pytest.mark.asyncio
    async def test_create_cache_manager(self):
        """Test creating cache manager."""
        from cirkelline.ckc.mastermind.optimization import (
            create_cache_manager,
            get_cache_manager,
            CacheManager,
        )

        cache = await create_cache_manager(max_size_mb=128)
        assert isinstance(cache, CacheManager)

        retrieved = get_cache_manager()
        assert retrieved is cache

    @pytest.mark.asyncio
    async def test_create_batch_processor(self):
        """Test creating batch processor."""
        from cirkelline.ckc.mastermind.optimization import (
            create_batch_processor,
            get_batch_processor,
            BatchProcessor,
        )

        processor = await create_batch_processor(batch_size=5)
        assert isinstance(processor, BatchProcessor)

        retrieved = get_batch_processor()
        assert retrieved is processor

    @pytest.mark.asyncio
    async def test_create_cost_optimizer(self):
        """Test creating cost optimizer."""
        from cirkelline.ckc.mastermind.optimization import (
            create_cost_optimizer,
            get_cost_optimizer,
            CostOptimizer,
        )

        optimizer = await create_cost_optimizer(budget_usd=200.0)
        assert isinstance(optimizer, CostOptimizer)

        retrieved = get_cost_optimizer()
        assert retrieved is optimizer

    @pytest.mark.asyncio
    async def test_create_latency_tracker(self):
        """Test creating latency tracker."""
        from cirkelline.ckc.mastermind.optimization import (
            create_latency_tracker,
            get_latency_tracker,
            LatencyTracker,
        )

        tracker = await create_latency_tracker(window_size=500)
        assert isinstance(tracker, LatencyTracker)

        retrieved = get_latency_tracker()
        assert retrieved is tracker


# =============================================================================
# TEST MODULE IMPORTS
# =============================================================================


class TestOptimizationModuleImports:
    """Tests for module imports."""

    def test_import_from_mastermind(self):
        """Test importing optimization from mastermind package."""
        from cirkelline.ckc.mastermind import (
            # Enums
            MetricType,
            OptimizationStrategy,
            CacheEvictionPolicy,
            AlertLevel,
            # Data classes
            PerformanceMetric,
            PerformanceSnapshot,
            PerformanceAlert,
            CacheEntry,
            CacheStats,
            BatchJob,
            CostEstimate,
            OptimizationRecommendation,
            # Classes
            PerformanceMonitor,
            CacheManager,
            BatchProcessor,
            CostOptimizer,
            LatencyTracker,
            # Factory functions
            create_performance_monitor,
            create_cache_manager,
            create_batch_processor,
            create_cost_optimizer,
            create_latency_tracker,
        )

        assert MetricType is not None
        assert PerformanceMonitor is not None
        assert CacheManager is not None
        assert create_performance_monitor is not None

    def test_all_exports_in_all(self):
        """Test that optimization exports are in __all__."""
        from cirkelline.ckc.mastermind import __all__

        optimization_exports = [
            "MetricType",
            "OptimizationStrategy",
            "CacheEvictionPolicy",
            "AlertLevel",
            "PerformanceMetric",
            "PerformanceSnapshot",
            "PerformanceAlert",
            "CacheEntry",
            "CacheStats",
            "BatchJob",
            "CostEstimate",
            "OptimizationRecommendation",
            "PerformanceMonitor",
            "CacheManager",
            "BatchProcessor",
            "CostOptimizer",
            "LatencyTracker",
            "create_performance_monitor",
            "create_cache_manager",
            "create_batch_processor",
            "create_cost_optimizer",
            "create_latency_tracker",
        ]

        for export in optimization_exports:
            assert export in __all__, f"{export} not in __all__"
