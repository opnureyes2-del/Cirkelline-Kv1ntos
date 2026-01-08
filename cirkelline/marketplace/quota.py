"""
Quota Management
================

FASE 6: API Marketplace

Håndtering af bruger-kvoter og rate limiting.

Features:
    - Tier-baserede kvoter
    - Rate limiting per endpoint
    - Burst allowance
    - Quota reset scheduling
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from enum import Enum
import asyncio


class QuotaTier(Enum):
    """
    Abonnements-tiers med forskellige kvote-grænser.

    Værdier svarer til requests per dag.
    """
    FREE = "free"           # 100 requests/dag
    STARTER = "starter"     # 1,000 requests/dag
    PROFESSIONAL = "pro"    # 10,000 requests/dag
    ENTERPRISE = "enterprise"  # 100,000+ requests/dag
    UNLIMITED = "unlimited"  # Ingen grænse


@dataclass
class TierLimits:
    """Limits for et specifikt tier."""
    requests_per_day: int
    requests_per_minute: int
    burst_allowance: int  # Extra requests tilladt i burst
    concurrent_requests: int
    max_request_size_kb: int
    features: Dict[str, bool] = field(default_factory=dict)


# Default tier configurations
TIER_CONFIGS: Dict[QuotaTier, TierLimits] = {
    QuotaTier.FREE: TierLimits(
        requests_per_day=100,
        requests_per_minute=10,
        burst_allowance=5,
        concurrent_requests=2,
        max_request_size_kb=100,
        features={
            "basic_search": True,
            "advanced_search": False,
            "export": False,
            "webhooks": False,
        }
    ),
    QuotaTier.STARTER: TierLimits(
        requests_per_day=1000,
        requests_per_minute=30,
        burst_allowance=10,
        concurrent_requests=5,
        max_request_size_kb=500,
        features={
            "basic_search": True,
            "advanced_search": True,
            "export": True,
            "webhooks": False,
        }
    ),
    QuotaTier.PROFESSIONAL: TierLimits(
        requests_per_day=10000,
        requests_per_minute=100,
        burst_allowance=50,
        concurrent_requests=20,
        max_request_size_kb=2000,
        features={
            "basic_search": True,
            "advanced_search": True,
            "export": True,
            "webhooks": True,
        }
    ),
    QuotaTier.ENTERPRISE: TierLimits(
        requests_per_day=100000,
        requests_per_minute=500,
        burst_allowance=200,
        concurrent_requests=100,
        max_request_size_kb=10000,
        features={
            "basic_search": True,
            "advanced_search": True,
            "export": True,
            "webhooks": True,
            "dedicated_support": True,
            "sla": True,
        }
    ),
    QuotaTier.UNLIMITED: TierLimits(
        requests_per_day=-1,  # -1 = unlimited
        requests_per_minute=-1,
        burst_allowance=-1,
        concurrent_requests=-1,
        max_request_size_kb=-1,
        features={
            "basic_search": True,
            "advanced_search": True,
            "export": True,
            "webhooks": True,
            "dedicated_support": True,
            "sla": True,
            "custom_features": True,
        }
    ),
}


@dataclass
class UserQuota:
    """
    En brugers quota-status.

    Attributes:
        user_id: Bruger ID
        tier: Abonnements-tier
        requests_today: Requests brugt i dag
        requests_this_minute: Requests brugt dette minut
        last_request_at: Tidspunkt for sidste request
        reset_at: Tidspunkt for næste daglige reset
    """
    user_id: str
    tier: QuotaTier
    requests_today: int = 0
    requests_this_minute: int = 0
    last_request_at: Optional[datetime] = None
    reset_at: Optional[datetime] = None
    minute_reset_at: Optional[datetime] = None
    overage_count: int = 0  # Antal gange kvoten er overskredet
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if self.reset_at is None:
            # Sæt reset til midnat næste dag
            now = datetime.utcnow()
            self.reset_at = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        if self.minute_reset_at is None:
            now = datetime.utcnow()
            self.minute_reset_at = now + timedelta(minutes=1)

    @property
    def limits(self) -> TierLimits:
        """Hent tier limits."""
        return TIER_CONFIGS.get(self.tier, TIER_CONFIGS[QuotaTier.FREE])

    @property
    def remaining_today(self) -> int:
        """Antal remaining requests i dag."""
        if self.limits.requests_per_day < 0:
            return -1  # Unlimited
        return max(0, self.limits.requests_per_day - self.requests_today)

    @property
    def remaining_this_minute(self) -> int:
        """Antal remaining requests dette minut."""
        if self.limits.requests_per_minute < 0:
            return -1  # Unlimited
        return max(0, self.limits.requests_per_minute - self.requests_this_minute)

    @property
    def is_rate_limited(self) -> bool:
        """Tjek om brugeren er rate limited."""
        if self.limits.requests_per_minute < 0:
            return False
        return self.requests_this_minute >= self.limits.requests_per_minute

    @property
    def is_quota_exceeded(self) -> bool:
        """Tjek om daglig kvote er overskredet."""
        if self.limits.requests_per_day < 0:
            return False
        return self.requests_today >= self.limits.requests_per_day

    def can_make_request(self) -> bool:
        """Tjek om brugeren kan lave endnu en request."""
        return not self.is_rate_limited and not self.is_quota_exceeded

    def has_feature(self, feature: str) -> bool:
        """Tjek om brugeren har adgang til en feature."""
        return self.limits.features.get(feature, False)

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "user_id": self.user_id,
            "tier": self.tier.value,
            "requests_today": self.requests_today,
            "requests_this_minute": self.requests_this_minute,
            "remaining_today": self.remaining_today,
            "remaining_this_minute": self.remaining_this_minute,
            "is_rate_limited": self.is_rate_limited,
            "is_quota_exceeded": self.is_quota_exceeded,
            "limits": {
                "requests_per_day": self.limits.requests_per_day,
                "requests_per_minute": self.limits.requests_per_minute,
            },
            "reset_at": self.reset_at.isoformat() if self.reset_at else None,
        }


class QuotaManager:
    """
    Manager for bruger-kvoter.

    Håndterer:
        - Oprettelse og opdatering af kvoter
        - Rate limiting
        - Quota enforcement
        - Reset scheduling

    Eksempel:
        manager = QuotaManager()

        # Tjek om request er tilladt
        if await manager.can_request(user_id):
            await manager.increment(user_id)
            # Process request
        else:
            # Return 429 Too Many Requests
    """

    def __init__(self):
        self._quotas: Dict[str, UserQuota] = {}
        self._lock = asyncio.Lock()

    async def get_quota(self, user_id: str) -> UserQuota:
        """
        Hent eller opret quota for en bruger.

        Args:
            user_id: Bruger ID

        Returns:
            UserQuota
        """
        async with self._lock:
            if user_id not in self._quotas:
                # Opret default quota (FREE tier)
                self._quotas[user_id] = UserQuota(
                    user_id=user_id,
                    tier=QuotaTier.FREE
                )
            return self._quotas[user_id]

    async def set_tier(self, user_id: str, tier: QuotaTier) -> UserQuota:
        """
        Sæt tier for en bruger.

        Args:
            user_id: Bruger ID
            tier: Nyt tier

        Returns:
            Opdateret UserQuota
        """
        quota = await self.get_quota(user_id)
        quota.tier = tier
        return quota

    async def can_request(
        self,
        user_id: str,
        api_name: Optional[str] = None
    ) -> bool:
        """
        Tjek om en bruger kan lave en request.

        Args:
            user_id: Bruger ID
            api_name: Optional API-specifik tjek

        Returns:
            True hvis request er tilladt
        """
        quota = await self.get_quota(user_id)

        # Tjek for reset
        await self._check_reset(quota)

        return quota.can_make_request()

    async def increment(
        self,
        user_id: str,
        count: int = 1
    ) -> UserQuota:
        """
        Inkrementer request count.

        Args:
            user_id: Bruger ID
            count: Antal requests at tælle

        Returns:
            Opdateret UserQuota
        """
        quota = await self.get_quota(user_id)

        async with self._lock:
            # Tjek for reset først
            await self._check_reset(quota)

            quota.requests_today += count
            quota.requests_this_minute += count
            quota.last_request_at = datetime.utcnow()

            # Track overage
            if quota.is_quota_exceeded:
                quota.overage_count += 1

        return quota

    async def _check_reset(self, quota: UserQuota) -> None:
        """Tjek og udfør reset hvis nødvendigt."""
        now = datetime.utcnow()

        # Daglig reset
        if quota.reset_at and now >= quota.reset_at:
            quota.requests_today = 0
            quota.reset_at = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        # Minut reset
        if quota.minute_reset_at and now >= quota.minute_reset_at:
            quota.requests_this_minute = 0
            quota.minute_reset_at = now + timedelta(minutes=1)

    async def get_wait_time(self, user_id: str) -> Optional[int]:
        """
        Få antal sekunder at vente før næste request.

        Args:
            user_id: Bruger ID

        Returns:
            Sekunder at vente, eller None hvis ingen ventetid
        """
        quota = await self.get_quota(user_id)

        if quota.can_make_request():
            return None

        now = datetime.utcnow()

        # Hvis rate limited, vent til minut reset
        if quota.is_rate_limited and quota.minute_reset_at:
            delta = quota.minute_reset_at - now
            return max(0, int(delta.total_seconds()))

        # Hvis daglig kvote er brugt, vent til midnat
        if quota.is_quota_exceeded and quota.reset_at:
            delta = quota.reset_at - now
            return max(0, int(delta.total_seconds()))

        return None

    async def check_feature(
        self,
        user_id: str,
        feature: str
    ) -> bool:
        """
        Tjek om bruger har adgang til en feature.

        Args:
            user_id: Bruger ID
            feature: Feature navn

        Returns:
            True hvis adgang er tilladt
        """
        quota = await self.get_quota(user_id)
        return quota.has_feature(feature)


# ============================================
# SINGLETON & CONVENIENCE
# ============================================

_manager: Optional[QuotaManager] = None


def get_quota_manager() -> QuotaManager:
    """Hent singleton QuotaManager."""
    global _manager
    if _manager is None:
        _manager = QuotaManager()
    return _manager


async def get_user_quota(user_id: str) -> UserQuota:
    """Convenience function til at hente bruger quota."""
    return await get_quota_manager().get_quota(user_id)


async def check_quota(
    user_id: str,
    api_name: Optional[str] = None
) -> bool:
    """Convenience function til at tjekke quota."""
    return await get_quota_manager().can_request(user_id, api_name)


async def increment_quota(user_id: str, count: int = 1) -> UserQuota:
    """Convenience function til at inkrementere quota."""
    return await get_quota_manager().increment(user_id, count)
