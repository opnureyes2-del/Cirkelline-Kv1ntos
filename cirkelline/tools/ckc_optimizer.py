"""
CKC Bridge Optimizer
====================

Optimization and improvement unit for the CKC Bridge integration.
Monitors, analyzes, and suggests improvements for CKC-Cirkelline communication.

Features:
    - Performance monitoring for CKC tool calls
    - Latency tracking and optimization
    - Error pattern detection
    - Usage analytics
    - Improvement suggestions

Usage:
    from cirkelline.tools.ckc_optimizer import CKCOptimizer, get_ckc_optimizer

    optimizer = get_ckc_optimizer()
    stats = optimizer.get_performance_stats()
    suggestions = optimizer.get_improvement_suggestions()

Version: 1.0.0
Date: 2025-12-16
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ToolCallStatus(str, Enum):
    """Status of a tool call."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


@dataclass
class ToolCallMetrics:
    """Metrics for a single tool call."""
    tool_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: ToolCallStatus = ToolCallStatus.SUCCESS
    error_message: Optional[str] = None
    input_size: int = 0
    output_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolPerformanceStats:
    """Aggregated performance statistics for a tool."""
    tool_name: str
    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration_ms: float = 0
    avg_duration_ms: float = 0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0
    p95_duration_ms: float = 0
    error_rate: float = 0
    last_call: Optional[datetime] = None
    error_patterns: Dict[str, int] = field(default_factory=dict)


class CKCOptimizer:
    """
    CKC Bridge Optimizer Unit.

    Monitors and optimizes the CKC-Cirkelline bridge integration.
    Provides performance metrics, error detection, and improvement suggestions.
    """

    # Performance thresholds
    LATENCY_THRESHOLD_MS = 500  # Warning if tool takes longer
    ERROR_RATE_THRESHOLD = 0.05  # 5% error rate warning
    MIN_CALLS_FOR_ANALYSIS = 10  # Minimum calls before analysis

    def __init__(self):
        """Initialize the CKC Optimizer."""
        self._call_history: List[ToolCallMetrics] = []
        self._tool_stats: Dict[str, ToolPerformanceStats] = {}
        self._start_time = datetime.utcnow()
        self._improvement_cache: List[Dict[str, Any]] = []
        self._cache_timestamp: Optional[datetime] = None

        # Tool-specific optimization hints
        self._optimization_hints: Dict[str, List[str]] = {
            "get_ckc_status": [
                "Cache status for 30 seconds to reduce API calls",
                "Use async polling for real-time status updates",
            ],
            "list_ckc_capabilities": [
                "Cache capabilities - they rarely change",
                "Consider lazy loading for rarely-used capabilities",
            ],
            "create_ckc_task": [
                "Batch similar tasks when possible",
                "Use priority queuing for better resource allocation",
            ],
            "start_mastermind_session": [
                "Reuse existing sessions when objectives are similar",
                "Set appropriate budget limits to prevent runaway costs",
            ],
            "list_learning_rooms": [
                "Cache room list with TTL of 60 seconds",
                "Subscribe to room status changes via WebSocket",
            ],
        }

        logger.info("CKC Optimizer initialized")

    def track_call(
        self,
        tool_name: str,
        status: ToolCallStatus,
        duration_ms: float,
        error_message: Optional[str] = None,
        input_size: int = 0,
        output_size: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a CKC tool call for optimization analysis.

        Args:
            tool_name: Name of the tool called
            status: Status of the call
            duration_ms: Duration in milliseconds
            error_message: Error message if failed
            input_size: Size of input data
            output_size: Size of output data
            metadata: Additional metadata
        """
        now = datetime.utcnow()

        metrics = ToolCallMetrics(
            tool_name=tool_name,
            start_time=now - timedelta(milliseconds=duration_ms),
            end_time=now,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            input_size=input_size,
            output_size=output_size,
            metadata=metadata or {},
        )

        self._call_history.append(metrics)
        self._update_tool_stats(metrics)

        # Clear improvement cache when new data arrives
        self._cache_timestamp = None

        # Log performance warnings
        if duration_ms > self.LATENCY_THRESHOLD_MS:
            logger.warning(
                f"CKC tool '{tool_name}' took {duration_ms:.0f}ms "
                f"(threshold: {self.LATENCY_THRESHOLD_MS}ms)"
            )

        if status == ToolCallStatus.FAILURE:
            logger.warning(
                f"CKC tool '{tool_name}' failed: {error_message}"
            )

    def _update_tool_stats(self, metrics: ToolCallMetrics) -> None:
        """Update aggregated statistics for a tool."""
        tool_name = metrics.tool_name

        if tool_name not in self._tool_stats:
            self._tool_stats[tool_name] = ToolPerformanceStats(tool_name=tool_name)

        stats = self._tool_stats[tool_name]
        stats.call_count += 1
        stats.last_call = metrics.end_time

        if metrics.status == ToolCallStatus.SUCCESS:
            stats.success_count += 1
        else:
            stats.failure_count += 1
            if metrics.error_message:
                # Track error patterns
                error_key = metrics.error_message[:50]  # Truncate for grouping
                stats.error_patterns[error_key] = stats.error_patterns.get(error_key, 0) + 1

        if metrics.duration_ms:
            stats.total_duration_ms += metrics.duration_ms
            stats.avg_duration_ms = stats.total_duration_ms / stats.call_count
            stats.min_duration_ms = min(stats.min_duration_ms, metrics.duration_ms)
            stats.max_duration_ms = max(stats.max_duration_ms, metrics.duration_ms)

        # Update error rate
        stats.error_rate = stats.failure_count / stats.call_count if stats.call_count > 0 else 0

    def get_performance_stats(self) -> Dict[str, ToolPerformanceStats]:
        """
        Get performance statistics for all tracked tools.

        Returns:
            Dict mapping tool names to their performance stats.
        """
        return self._tool_stats.copy()

    def get_tool_stats(self, tool_name: str) -> Optional[ToolPerformanceStats]:
        """
        Get performance statistics for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Performance stats or None if not tracked.
        """
        return self._tool_stats.get(tool_name)

    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """
        Generate improvement suggestions based on tracked metrics.

        Returns:
            List of improvement suggestions with priority and details.
        """
        # Use cache if recent
        if (self._cache_timestamp and
            datetime.utcnow() - self._cache_timestamp < timedelta(minutes=5)):
            return self._improvement_cache

        suggestions = []

        for tool_name, stats in self._tool_stats.items():
            # Skip if not enough data
            if stats.call_count < self.MIN_CALLS_FOR_ANALYSIS:
                continue

            # High latency suggestion
            if stats.avg_duration_ms > self.LATENCY_THRESHOLD_MS:
                suggestions.append({
                    "priority": "high",
                    "tool": tool_name,
                    "issue": "high_latency",
                    "message": f"Average latency of {stats.avg_duration_ms:.0f}ms exceeds threshold",
                    "recommendation": "Consider implementing caching or async processing",
                    "metrics": {
                        "avg_ms": stats.avg_duration_ms,
                        "max_ms": stats.max_duration_ms,
                        "threshold_ms": self.LATENCY_THRESHOLD_MS,
                    }
                })

            # High error rate suggestion
            if stats.error_rate > self.ERROR_RATE_THRESHOLD:
                suggestions.append({
                    "priority": "critical",
                    "tool": tool_name,
                    "issue": "high_error_rate",
                    "message": f"Error rate of {stats.error_rate:.1%} exceeds threshold",
                    "recommendation": "Investigate error patterns and add retry logic",
                    "metrics": {
                        "error_rate": stats.error_rate,
                        "failure_count": stats.failure_count,
                        "threshold": self.ERROR_RATE_THRESHOLD,
                        "top_errors": dict(list(stats.error_patterns.items())[:3]),
                    }
                })

            # Tool-specific hints
            if tool_name in self._optimization_hints:
                for hint in self._optimization_hints[tool_name]:
                    suggestions.append({
                        "priority": "low",
                        "tool": tool_name,
                        "issue": "optimization_hint",
                        "message": hint,
                        "recommendation": hint,
                        "metrics": {},
                    })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 99))

        # Cache results
        self._improvement_cache = suggestions
        self._cache_timestamp = datetime.utcnow()

        return suggestions

    def get_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive health report for the CKC Bridge.

        Returns:
            Health report with overall status and detailed metrics.
        """
        total_calls = sum(s.call_count for s in self._tool_stats.values())
        total_failures = sum(s.failure_count for s in self._tool_stats.values())
        overall_error_rate = total_failures / total_calls if total_calls > 0 else 0

        # Determine overall health status
        if overall_error_rate > 0.1:  # 10%+ errors
            health_status = "critical"
        elif overall_error_rate > 0.05:  # 5%+ errors
            health_status = "degraded"
        elif overall_error_rate > 0.01:  # 1%+ errors
            health_status = "warning"
        else:
            health_status = "healthy"

        return {
            "status": health_status,
            "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds(),
            "total_calls": total_calls,
            "total_failures": total_failures,
            "overall_error_rate": overall_error_rate,
            "tools_tracked": len(self._tool_stats),
            "suggestions_count": len(self.get_improvement_suggestions()),
            "last_updated": datetime.utcnow().isoformat(),
            "per_tool_stats": {
                name: {
                    "calls": stats.call_count,
                    "avg_latency_ms": stats.avg_duration_ms,
                    "error_rate": stats.error_rate,
                    "last_call": stats.last_call.isoformat() if stats.last_call else None,
                }
                for name, stats in self._tool_stats.items()
            }
        }

    def reset_stats(self) -> None:
        """Reset all collected statistics."""
        self._call_history.clear()
        self._tool_stats.clear()
        self._improvement_cache.clear()
        self._cache_timestamp = None
        logger.info("CKC Optimizer stats reset")

    def create_wrapper(self, tool_name: str) -> Callable:
        """
        Create a decorator wrapper for tracking tool calls.

        Args:
            tool_name: Name of the tool to track

        Returns:
            Decorator function for wrapping tool calls.
        """
        optimizer = self

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                status = ToolCallStatus.SUCCESS
                error_msg = None
                result = None

                try:
                    result = await func(*args, **kwargs)
                except Exception as e:
                    status = ToolCallStatus.FAILURE
                    error_msg = str(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    optimizer.track_call(
                        tool_name=tool_name,
                        status=status,
                        duration_ms=duration_ms,
                        error_message=error_msg,
                    )

                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                status = ToolCallStatus.SUCCESS
                error_msg = None
                result = None

                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    status = ToolCallStatus.FAILURE
                    error_msg = str(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    optimizer.track_call(
                        tool_name=tool_name,
                        status=status,
                        duration_ms=duration_ms,
                        error_message=error_msg,
                    )

                return result

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


# Singleton instance
_ckc_optimizer: Optional[CKCOptimizer] = None


def get_ckc_optimizer() -> CKCOptimizer:
    """Get singleton CKC Optimizer instance."""
    global _ckc_optimizer
    if _ckc_optimizer is None:
        _ckc_optimizer = CKCOptimizer()
    return _ckc_optimizer


def track_ckc_call(tool_name: str) -> Callable:
    """
    Decorator for tracking CKC tool calls.

    Usage:
        @track_ckc_call("get_ckc_status")
        def get_ckc_status():
            ...
    """
    return get_ckc_optimizer().create_wrapper(tool_name)


logger.info("CKC Optimizer module loaded")
