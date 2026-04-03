"""
Cirkelline API Marketplace
==========================

FASE 6: Track B - API Marketplace

API Marketplace systemet gør det muligt at:
    - Registrere og versionere API'er
    - Håndtere rate limiting og kvoter
    - Tracke brug og fakturering
    - Generere developer dokumentation

Komponenter:
    - APIRegistry: Central registrering af tilgængelige API'er
    - QuotaManager: Håndtering af bruger-kvoter
    - UsageTracker: Tracking af API-kald
    - DocGenerator: Auto-generering af dokumentation

Eksempel:
    from cirkelline.marketplace import (
        APIRegistry,
        register_api,
        get_api_quota
    )

    # Registrer en ny API
    register_api(
        name="web3-research",
        version="1.0",
        endpoint="/api/v1/web3/research",
        rate_limit=100
    )
"""

from .quota import (
    QuotaManager,
    QuotaTier,
    UserQuota,
    check_quota,
    get_user_quota,
)
from .registry import (
    APIDefinition,
    APIRegistry,
    APIStatus,
    APIVersion,
    get_api,
    list_apis,
    register_api,
)
from .usage import (
    UsageRecord,
    UsageTracker,
    get_usage_stats,
    track_usage,
)

__all__ = [
    # Registry
    "APIRegistry",
    "APIDefinition",
    "APIVersion",
    "APIStatus",
    "register_api",
    "get_api",
    "list_apis",
    # Quota
    "QuotaManager",
    "UserQuota",
    "QuotaTier",
    "get_user_quota",
    "check_quota",
    # Usage
    "UsageTracker",
    "UsageRecord",
    "track_usage",
    "get_usage_stats",
]

__version__ = "1.0.0"
