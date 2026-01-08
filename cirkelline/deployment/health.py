"""
Health Checker
==============
Readiness and liveness probes for deployment.

Responsibilities:
- Check system component health
- Provide Kubernetes-compatible endpoints
- Track health history
- Support custom health checks
"""

import logging
import asyncio
import time
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class HealthStatus(Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class HealthCheck:
    """A health check definition."""
    name: str
    check_func: Callable[[], Awaitable[HealthResult]]
    critical: bool = True  # If false, failure doesn't affect overall health
    timeout_seconds: float = 5.0
    enabled: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
# BUILT-IN CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

async def check_memory() -> HealthResult:
    """Check memory usage."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        used_percent = memory.percent

        if used_percent > 90:
            status = HealthStatus.UNHEALTHY
            message = f"Memory critically high: {used_percent}%"
        elif used_percent > 80:
            status = HealthStatus.DEGRADED
            message = f"Memory high: {used_percent}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory OK: {used_percent}%"

        return HealthResult(
            name="memory",
            status=status,
            message=message,
            details={
                "used_percent": used_percent,
                "available_mb": memory.available / (1024 * 1024),
            },
        )
    except ImportError:
        return HealthResult(
            name="memory",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed",
        )
    except Exception as e:
        return HealthResult(
            name="memory",
            status=HealthStatus.UNKNOWN,
            message=str(e),
        )


async def check_disk() -> HealthResult:
    """Check disk usage."""
    try:
        import psutil
        disk = psutil.disk_usage('/')
        used_percent = disk.percent

        if used_percent > 95:
            status = HealthStatus.UNHEALTHY
            message = f"Disk critically full: {used_percent}%"
        elif used_percent > 85:
            status = HealthStatus.DEGRADED
            message = f"Disk high: {used_percent}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk OK: {used_percent}%"

        return HealthResult(
            name="disk",
            status=status,
            message=message,
            details={
                "used_percent": used_percent,
                "free_gb": disk.free / (1024 * 1024 * 1024),
            },
        )
    except ImportError:
        return HealthResult(
            name="disk",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed",
        )
    except Exception as e:
        return HealthResult(
            name="disk",
            status=HealthStatus.UNKNOWN,
            message=str(e),
        )


async def check_cpu() -> HealthResult:
    """Check CPU usage."""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)

        if cpu_percent > 95:
            status = HealthStatus.DEGRADED
            message = f"CPU very high: {cpu_percent}%"
        elif cpu_percent > 80:
            status = HealthStatus.HEALTHY
            message = f"CPU high: {cpu_percent}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"CPU OK: {cpu_percent}%"

        return HealthResult(
            name="cpu",
            status=status,
            message=message,
            details={"percent": cpu_percent},
        )
    except ImportError:
        return HealthResult(
            name="cpu",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed",
        )
    except Exception as e:
        return HealthResult(
            name="cpu",
            status=HealthStatus.UNKNOWN,
            message=str(e),
        )


async def check_self() -> HealthResult:
    """Basic self-check."""
    return HealthResult(
        name="self",
        status=HealthStatus.HEALTHY,
        message="Application running",
        details={
            "python_version": __import__('sys').version,
            "pid": __import__('os').getpid(),
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class HealthChecker:
    """
    System health monitoring.

    Provides liveness and readiness probes compatible
    with Kubernetes and other orchestrators.
    """

    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._last_results: Dict[str, HealthResult] = {}
        self._history: List[Dict[str, Any]] = []
        self._max_history = 100

        # Register built-in checks
        self._register_builtin_checks()

    def _register_builtin_checks(self) -> None:
        """Register default health checks."""
        self.register(HealthCheck(
            name="self",
            check_func=check_self,
            critical=True,
        ))
        self.register(HealthCheck(
            name="memory",
            check_func=check_memory,
            critical=False,
        ))
        self.register(HealthCheck(
            name="disk",
            check_func=check_disk,
            critical=False,
        ))
        self.register(HealthCheck(
            name="cpu",
            check_func=check_cpu,
            critical=False,
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # REGISTRATION
    # ═══════════════════════════════════════════════════════════════════════════

    def register(self, check: HealthCheck) -> None:
        """Register a health check."""
        self._checks[check.name] = check
        logger.debug(f"Registered health check: {check.name}")

    def unregister(self, name: str) -> bool:
        """Unregister a health check."""
        if name in self._checks:
            del self._checks[name]
            return True
        return False

    def enable(self, name: str) -> bool:
        """Enable a health check."""
        if name in self._checks:
            self._checks[name].enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a health check."""
        if name in self._checks:
            self._checks[name].enabled = False
            return True
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECKING
    # ═══════════════════════════════════════════════════════════════════════════

    async def check(self, name: str) -> HealthResult:
        """
        Run a single health check.

        Args:
            name: Name of the health check

        Returns:
            HealthResult
        """
        if name not in self._checks:
            return HealthResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Unknown health check: {name}",
            )

        check = self._checks[name]
        if not check.enabled:
            return HealthResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="Health check disabled",
            )

        start_time = time.time()

        try:
            result = await asyncio.wait_for(
                check.check_func(),
                timeout=check.timeout_seconds,
            )
            result.latency_ms = (time.time() - start_time) * 1000
        except asyncio.TimeoutError:
            result = HealthResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {check.timeout_seconds}s",
                latency_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            result = HealthResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000,
            )

        self._last_results[name] = result
        return result

    async def check_all(self) -> Dict[str, HealthResult]:
        """Run all enabled health checks."""
        tasks = []
        for name, check in self._checks.items():
            if check.enabled:
                tasks.append(self.check(name))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to results
        all_results = {}
        for result in results:
            if isinstance(result, HealthResult):
                all_results[result.name] = result
            elif isinstance(result, Exception):
                all_results["error"] = HealthResult(
                    name="error",
                    status=HealthStatus.UNHEALTHY,
                    message=str(result),
                )

        # Add to history
        self._add_to_history(all_results)

        return all_results

    def _add_to_history(self, results: Dict[str, HealthResult]) -> None:
        """Add results to history."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall": self._calculate_overall(results).value,
            "checks": {k: v.status.value for k, v in results.items()},
        }
        self._history.append(entry)

        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def _calculate_overall(self, results: Dict[str, HealthResult]) -> HealthStatus:
        """Calculate overall health status."""
        critical_unhealthy = False
        any_degraded = False

        for name, result in results.items():
            check = self._checks.get(name)
            if check and check.critical:
                if result.status == HealthStatus.UNHEALTHY:
                    critical_unhealthy = True
            if result.status == HealthStatus.DEGRADED:
                any_degraded = True

        if critical_unhealthy:
            return HealthStatus.UNHEALTHY
        elif any_degraded:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    # ═══════════════════════════════════════════════════════════════════════════
    # PROBES
    # ═══════════════════════════════════════════════════════════════════════════

    async def liveness(self) -> Dict[str, Any]:
        """
        Liveness probe for Kubernetes.

        Returns healthy if the application is running.
        Used to determine if pod should be restarted.
        """
        result = await self.check("self")
        return {
            "status": result.status.value,
            "message": result.message,
            "timestamp": result.timestamp,
        }

    async def readiness(self) -> Dict[str, Any]:
        """
        Readiness probe for Kubernetes.

        Returns healthy if the application is ready to serve traffic.
        """
        results = await self.check_all()
        overall = self._calculate_overall(results)

        return {
            "status": overall.value,
            "checks": {k: v.to_dict() for k, v in results.items()},
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def startup(self) -> Dict[str, Any]:
        """
        Startup probe for Kubernetes.

        Returns healthy when initial startup is complete.
        """
        # For now, same as liveness
        return await self.liveness()

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get health checker statistics."""
        return {
            "registered_checks": len(self._checks),
            "enabled_checks": sum(1 for c in self._checks.values() if c.enabled),
            "critical_checks": sum(1 for c in self._checks.values() if c.critical),
            "last_results": {k: v.to_dict() for k, v in self._last_results.items()},
            "history_entries": len(self._history),
        }

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent health history."""
        return self._history[-limit:]


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_health_instance: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the singleton HealthChecker instance."""
    global _health_instance

    if _health_instance is None:
        _health_instance = HealthChecker()

    return _health_instance


async def init_health_checker() -> HealthChecker:
    """Initialize and return the health checker."""
    return get_health_checker()
