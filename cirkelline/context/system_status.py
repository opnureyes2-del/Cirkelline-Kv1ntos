"""
System Status
=============
Monitors health of system services and CI/CD pipelines.

Services monitored:
- Database (PostgreSQL)
- Redis
- Vector DB
- External APIs
- CI/CD pipelines

Provides health checks and status aggregation.
"""

import os
import logging
import asyncio
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH STATUS
# ═══════════════════════════════════════════════════════════════════════════════

class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health status of a single service."""
    name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    latency_ms: Optional[int] = None
    last_check: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check,
            "message": self.message,
            "metadata": self.metadata,
        }


@dataclass
class CICDStatus:
    """CI/CD pipeline status."""
    pipeline: str
    status: str = "unknown"
    last_run: Optional[str] = None
    last_success: Optional[str] = None
    current_job: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline": self.pipeline,
            "status": self.status,
            "last_run": self.last_run,
            "last_success": self.last_success,
            "current_job": self.current_job,
            "url": self.url,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM STATUS
# ═══════════════════════════════════════════════════════════════════════════════

class SystemStatus:
    """
    Monitors and reports system health status.

    Usage:
        status = get_system_status()
        health = await status.check_all()
        print(health["overall"])  # "healthy" or "degraded"
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        redis_url: Optional[str] = None,
    ):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._services: Dict[str, ServiceHealth] = {}
        self._cicd: Dict[str, CICDStatus] = {}

    async def check_database(self) -> ServiceHealth:
        """Check PostgreSQL database health."""
        import time
        health = ServiceHealth(name="database")

        if not self.database_url:
            health.status = HealthStatus.UNKNOWN
            health.message = "No database URL configured"
            return health

        try:
            start = time.time()

            from sqlalchemy import create_engine, text

            engine = create_engine(self.database_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            latency = int((time.time() - start) * 1000)

            health.status = HealthStatus.HEALTHY
            health.latency_ms = latency
            health.message = f"Connected ({latency}ms)"

        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.message = str(e)

        health.last_check = datetime.utcnow().isoformat()
        self._services["database"] = health
        return health

    async def check_redis(self) -> ServiceHealth:
        """Check Redis health."""
        import time
        health = ServiceHealth(name="redis")

        try:
            import redis.asyncio as aioredis

            start = time.time()

            client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await client.ping()
            await client.close()

            latency = int((time.time() - start) * 1000)

            health.status = HealthStatus.HEALTHY
            health.latency_ms = latency
            health.message = f"Connected ({latency}ms)"

        except ImportError:
            health.status = HealthStatus.UNKNOWN
            health.message = "redis.asyncio not installed"

        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.message = str(e)

        health.last_check = datetime.utcnow().isoformat()
        self._services["redis"] = health
        return health

    async def check_vector_db(self) -> ServiceHealth:
        """Check vector database (pgvector) health."""
        import time
        health = ServiceHealth(name="vector_db")

        if not self.database_url:
            health.status = HealthStatus.UNKNOWN
            health.message = "No database URL configured"
            return health

        try:
            start = time.time()

            from sqlalchemy import create_engine, text

            engine = create_engine(self.database_url)
            with engine.connect() as conn:
                # Check pgvector extension
                result = conn.execute(text("""
                    SELECT extname FROM pg_extension WHERE extname = 'vector'
                """))
                row = result.fetchone()

                if row:
                    latency = int((time.time() - start) * 1000)
                    health.status = HealthStatus.HEALTHY
                    health.latency_ms = latency
                    health.message = f"pgvector extension active ({latency}ms)"
                else:
                    health.status = HealthStatus.DEGRADED
                    health.message = "pgvector extension not found"

        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.message = str(e)

        health.last_check = datetime.utcnow().isoformat()
        self._services["vector_db"] = health
        return health

    async def check_external_api(
        self,
        name: str,
        url: str,
        timeout: float = 5.0,
    ) -> ServiceHealth:
        """Check external API health."""
        import time
        import httpx

        health = ServiceHealth(name=name)

        try:
            start = time.time()

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                latency = int((time.time() - start) * 1000)

                if response.status_code < 400:
                    health.status = HealthStatus.HEALTHY
                    health.latency_ms = latency
                    health.message = f"HTTP {response.status_code} ({latency}ms)"
                else:
                    health.status = HealthStatus.DEGRADED
                    health.latency_ms = latency
                    health.message = f"HTTP {response.status_code}"

        except httpx.TimeoutException:
            health.status = HealthStatus.DEGRADED
            health.message = "Request timeout"

        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.message = str(e)

        health.last_check = datetime.utcnow().isoformat()
        self._services[name] = health
        return health

    async def check_cicd_github_actions(
        self,
        owner: str,
        repo: str,
        token: Optional[str] = None,
    ) -> CICDStatus:
        """Check GitHub Actions workflow status."""
        status = CICDStatus(pipeline=f"github:{owner}/{repo}")

        try:
            import httpx

            headers = {"Accept": "application/vnd.github.v3+json"}
            if token:
                headers["Authorization"] = f"token {token}"

            url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params={"per_page": 1})

                if response.status_code == 200:
                    data = response.json()
                    runs = data.get("workflow_runs", [])

                    if runs:
                        latest = runs[0]
                        status.status = latest.get("conclusion") or latest.get("status")
                        status.last_run = latest.get("created_at")
                        status.current_job = latest.get("name")
                        status.url = latest.get("html_url")

                        if latest.get("conclusion") == "success":
                            status.last_success = latest.get("created_at")

        except Exception as e:
            status.status = f"error: {e}"

        self._cicd[status.pipeline] = status
        return status

    async def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks and return aggregated status.

        Returns:
            {
                "overall": "healthy" | "degraded" | "unhealthy",
                "timestamp": "...",
                "services": {...},
                "cicd": {...},
            }
        """
        # Run service checks in parallel
        await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_vector_db(),
            return_exceptions=True,
        )

        # Determine overall status
        unhealthy_count = sum(
            1 for s in self._services.values()
            if s.status == HealthStatus.UNHEALTHY
        )
        degraded_count = sum(
            1 for s in self._services.values()
            if s.status == HealthStatus.DEGRADED
        )

        if unhealthy_count > 0:
            overall = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return {
            "overall": overall.value,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                name: service.to_dict()
                for name, service in self._services.items()
            },
            "cicd": {
                name: cicd.to_dict()
                for name, cicd in self._cicd.items()
            },
        }

    def get_service_status(self, name: str) -> Optional[ServiceHealth]:
        """Get cached status for a specific service."""
        return self._services.get(name)

    def get_all_services(self) -> Dict[str, ServiceHealth]:
        """Get all cached service statuses."""
        return dict(self._services)


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_system_status_instance: Optional[SystemStatus] = None


def get_system_status(
    database_url: Optional[str] = None,
    redis_url: Optional[str] = None,
) -> SystemStatus:
    """Get the singleton SystemStatus instance."""
    global _system_status_instance

    if _system_status_instance is None:
        _system_status_instance = SystemStatus(
            database_url=database_url,
            redis_url=redis_url,
        )

    return _system_status_instance
