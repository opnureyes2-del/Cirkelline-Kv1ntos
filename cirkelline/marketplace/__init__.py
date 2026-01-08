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

from .registry import (
    APIRegistry,
    APIDefinition,
    APIVersion,
    APIStatus,
    register_api,
    get_api,
    list_apis,
)

from .quota import (
    QuotaManager,
    UserQuota,
    QuotaTier,
    get_user_quota,
    check_quota,
)

from .usage import (
    UsageTracker,
    UsageRecord,
    track_usage,
    get_usage_stats,
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
