"""
Usage Tracking
==============

FASE 6: API Marketplace

Tracking af API-brug for analytics og fakturering.

Features:
    - Request logging
    - Usage statistics
    - Cost calculation
    - Billing integration hooks
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import asyncio
import uuid


@dataclass
class UsageRecord:
    """
    En enkelt usage record.

    Attributes:
        id: Unik identifikator
        user_id: Bruger ID
        api_name: API der blev kaldt
        endpoint: Specifik endpoint
        method: HTTP metode
        status_code: Response status
        latency_ms: Response tid i ms
        request_size: Request størrelse i bytes
        response_size: Response størrelse i bytes
        timestamp: Tidspunkt for request
        metadata: Yderligere metadata
    """
    user_id: str
    api_name: str
    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_size: int = 0
    response_size: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Tjek om request var succesfuld."""
        return 200 <= self.status_code < 400

    @property
    def is_error(self) -> bool:
        """Tjek om request var en fejl."""
        return self.status_code >= 400


@dataclass
class UsageStats:
    """
    Aggregerede usage statistikker.

    Attributes:
        period_start: Start af periode
        period_end: Slut af periode
        total_requests: Totalt antal requests
        successful_requests: Antal succesfulde requests
        failed_requests: Antal fejlede requests
        total_latency_ms: Total latency
        avg_latency_ms: Gennemsnitlig latency
        by_api: Breakdown per API
        by_endpoint: Breakdown per endpoint
        by_status: Breakdown per status code
    """
    period_start: datetime
    period_end: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    total_request_size: int = 0
    total_response_size: int = 0
    by_api: Dict[str, int] = field(default_factory=dict)
    by_endpoint: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[int, int] = field(default_factory=dict)
    by_hour: Dict[int, int] = field(default_factory=dict)

    @property
    def avg_latency_ms(self) -> float:
        """Gennemsnitlig latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    @property
    def success_rate(self) -> float:
        """Success rate som procent."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """Error rate som procent."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "success_rate": round(self.success_rate, 2),
            "error_rate": round(self.error_rate, 2),
            "by_api": self.by_api,
            "by_endpoint": dict(list(self.by_endpoint.items())[:10]),  # Top 10
            "by_status": self.by_status,
            "by_hour": self.by_hour,
        }


class UsageTracker:
    """
    Tracker for API usage.

    Håndterer:
        - Logging af requests
        - Aggregering af statistik
        - Eksport til billing
        - Real-time metrics

    Eksempel:
        tracker = UsageTracker()

        # Log en request
        await tracker.log(UsageRecord(
            user_id="user123",
            api_name="web3-research",
            endpoint="/api/v1/search",
            method="GET",
            status_code=200,
            latency_ms=150.5
        ))

        # Hent statistik
        stats = await tracker.get_stats(user_id="user123")
    """

    def __init__(self, retention_days: int = 30):
        """
        Initialiser tracker.

        Args:
            retention_days: Antal dage at beholde data
        """
        self.retention_days = retention_days
        self._records: List[UsageRecord] = []
        self._by_user: Dict[str, List[UsageRecord]] = defaultdict(list)
        self._by_api: Dict[str, List[UsageRecord]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def log(self, record: UsageRecord) -> None:
        """
        Log en usage record.

        Args:
            record: Usage record
        """
        async with self._lock:
            self._records.append(record)
            self._by_user[record.user_id].append(record)
            self._by_api[record.api_name].append(record)

            # Cleanup gamle records periodisk
            if len(self._records) % 1000 == 0:
                await self._cleanup()

    async def get_stats(
        self,
        user_id: Optional[str] = None,
        api_name: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> UsageStats:
        """
        Hent aggregerede statistikker.

        Args:
            user_id: Filtrer på bruger
            api_name: Filtrer på API
            start: Start tidspunkt (default: 24 timer siden)
            end: Slut tidspunkt (default: nu)

        Returns:
            UsageStats
        """
        now = datetime.utcnow()
        start = start or (now - timedelta(days=1))
        end = end or now

        # Vælg records at aggregere
        if user_id:
            records = self._by_user.get(user_id, [])
        elif api_name:
            records = self._by_api.get(api_name, [])
        else:
            records = self._records

        # Filtrer på tidsperiode
        filtered = [
            r for r in records
            if start <= r.timestamp <= end
        ]

        # Aggreger
        stats = UsageStats(
            period_start=start,
            period_end=end
        )

        for record in filtered:
            stats.total_requests += 1
            stats.total_latency_ms += record.latency_ms
            stats.total_request_size += record.request_size
            stats.total_response_size += record.response_size

            if record.is_success:
                stats.successful_requests += 1
            else:
                stats.failed_requests += 1

            # By API
            api = record.api_name
            stats.by_api[api] = stats.by_api.get(api, 0) + 1

            # By endpoint
            endpoint = f"{record.method} {record.endpoint}"
            stats.by_endpoint[endpoint] = stats.by_endpoint.get(endpoint, 0) + 1

            # By status
            status = record.status_code
            stats.by_status[status] = stats.by_status.get(status, 0) + 1

            # By hour
            hour = record.timestamp.hour
            stats.by_hour[hour] = stats.by_hour.get(hour, 0) + 1

        return stats

    async def get_recent_records(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[UsageRecord]:
        """
        Hent seneste usage records.

        Args:
            user_id: Filtrer på bruger
            limit: Max antal records

        Returns:
            Liste af UsageRecords
        """
        if user_id:
            records = self._by_user.get(user_id, [])
        else:
            records = self._records

        # Returner nyeste først
        return sorted(
            records,
            key=lambda r: r.timestamp,
            reverse=True
        )[:limit]

    async def get_user_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Hent usage summary for en bruger.

        Args:
            user_id: Bruger ID
            days: Antal dage at inkludere

        Returns:
            Summary dict
        """
        now = datetime.utcnow()
        start = now - timedelta(days=days)

        stats = await self.get_stats(user_id=user_id, start=start, end=now)

        return {
            "user_id": user_id,
            "period_days": days,
            "total_requests": stats.total_requests,
            "avg_requests_per_day": stats.total_requests / days if days > 0 else 0,
            "success_rate": stats.success_rate,
            "avg_latency_ms": stats.avg_latency_ms,
            "top_apis": sorted(
                stats.by_api.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "top_endpoints": sorted(
                stats.by_endpoint.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }

    async def calculate_cost(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
        pricing: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Beregn estimeret kostnad for en periode.

        Args:
            user_id: Bruger ID
            start: Start tidspunkt
            end: Slut tidspunkt
            pricing: API -> pris per 1000 requests mapping

        Returns:
            Cost breakdown dict
        """
        pricing = pricing or {
            "default": 0.001,  # $0.001 per request default
        }

        records = [
            r for r in self._by_user.get(user_id, [])
            if start <= r.timestamp <= end
        ]

        costs_by_api: Dict[str, Dict[str, Any]] = {}
        total_cost = 0.0

        for record in records:
            api = record.api_name
            price_per_1k = pricing.get(api, pricing.get("default", 0.001))
            cost = price_per_1k / 1000  # Cost per request

            if api not in costs_by_api:
                costs_by_api[api] = {
                    "requests": 0,
                    "cost": 0.0,
                    "price_per_1k": price_per_1k
                }

            costs_by_api[api]["requests"] += 1
            costs_by_api[api]["cost"] += cost
            total_cost += cost

        return {
            "user_id": user_id,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "total_requests": len(records),
            "total_cost": round(total_cost, 4),
            "by_api": costs_by_api,
            "currency": "USD"
        }

    async def _cleanup(self) -> None:
        """Fjern gamle records."""
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)

        self._records = [r for r in self._records if r.timestamp >= cutoff]

        for user_id in list(self._by_user.keys()):
            self._by_user[user_id] = [
                r for r in self._by_user[user_id]
                if r.timestamp >= cutoff
            ]
            if not self._by_user[user_id]:
                del self._by_user[user_id]

        for api_name in list(self._by_api.keys()):
            self._by_api[api_name] = [
                r for r in self._by_api[api_name]
                if r.timestamp >= cutoff
            ]
            if not self._by_api[api_name]:
                del self._by_api[api_name]


# ============================================
# SINGLETON & CONVENIENCE
# ============================================

_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Hent singleton UsageTracker."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker


async def track_usage(
    user_id: str,
    api_name: str,
    endpoint: str,
    method: str,
    status_code: int,
    latency_ms: float,
    **kwargs
) -> UsageRecord:
    """
    Convenience function til at tracke usage.

    Args:
        user_id: Bruger ID
        api_name: API navn
        endpoint: Endpoint sti
        method: HTTP metode
        status_code: Response status
        latency_ms: Response tid
        **kwargs: Yderligere record attributter

    Returns:
        Den loggede UsageRecord
    """
    record = UsageRecord(
        user_id=user_id,
        api_name=api_name,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        latency_ms=latency_ms,
        **kwargs
    )

    await get_usage_tracker().log(record)
    return record


async def get_usage_stats(
    user_id: Optional[str] = None,
    api_name: Optional[str] = None,
    days: int = 1
) -> UsageStats:
    """Convenience function til at hente usage stats."""
    now = datetime.utcnow()
    start = now - timedelta(days=days)
    return await get_usage_tracker().get_stats(
        user_id=user_id,
        api_name=api_name,
        start=start,
        end=now
    )
