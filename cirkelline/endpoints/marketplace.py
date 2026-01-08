"""
API Marketplace Endpoints
=========================

FASE 6: API Marketplace

FastAPI endpoints for API Marketplace funktionalitet.

Endpoints:
    GET  /api/marketplace/apis          - List alle API'er
    GET  /api/marketplace/apis/{name}   - Hent specifik API
    POST /api/marketplace/apis          - Registrer ny API
    GET  /api/marketplace/quota         - Hent bruger quota
    GET  /api/marketplace/usage         - Hent usage statistik
    GET  /api/marketplace/usage/summary - Hent usage summary
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, Field

from cirkelline.marketplace import (
    APIRegistry,
    APIDefinition,
    APIVersion,
    APIStatus,
    register_api,
    get_api,
    list_apis,
    QuotaManager,
    QuotaTier,
    get_user_quota,
    check_quota,
    UsageTracker,
    track_usage,
    get_usage_stats,
)
from cirkelline.marketplace.registry import get_registry, HTTPMethod, APIEndpoint
from cirkelline.marketplace.quota import get_quota_manager, increment_quota
from cirkelline.marketplace.usage import get_usage_tracker

from cirkelline.config import logger


# Pydantic models for request/response
class APIEndpointCreate(BaseModel):
    """Endpoint creation schema."""
    path: str
    method: str = "GET"
    description: str
    parameters: List[dict] = Field(default_factory=list)
    request_body: Optional[dict] = None
    response: Optional[dict] = None
    rate_limit: Optional[int] = None
    requires_auth: bool = True
    tags: List[str] = Field(default_factory=list)


class APICreate(BaseModel):
    """API creation schema."""
    name: str
    display_name: str
    description: str
    category: str
    version: str = "1.0.0"
    endpoints: List[APIEndpointCreate] = Field(default_factory=list)
    rate_limit: int = 100
    tags: List[str] = Field(default_factory=list)


class QuotaResponse(BaseModel):
    """Quota response schema."""
    user_id: str
    tier: str
    requests_today: int
    requests_this_minute: int
    remaining_today: int
    remaining_this_minute: int
    is_rate_limited: bool
    is_quota_exceeded: bool
    limits: dict
    reset_at: Optional[str]


class UsageStatsResponse(BaseModel):
    """Usage statistics response."""
    period_start: str
    period_end: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    success_rate: float
    error_rate: float
    by_api: dict
    by_status: dict


# Create router
router = APIRouter(prefix="/api/marketplace", tags=["Marketplace"])


# ============================================
# API REGISTRY ENDPOINTS
# ============================================

@router.get("/apis")
async def list_marketplace_apis(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    List alle tilgængelige API'er i marketplace.

    Returns:
        Liste af API definitioner
    """
    try:
        apis = list_apis(category)

        return {
            "success": True,
            "apis": [
                {
                    "id": api.id,
                    "name": api.name,
                    "display_name": api.display_name,
                    "description": api.description,
                    "category": api.category,
                    "tags": api.tags,
                    "rate_limit": api.default_rate_limit,
                    "latest_version": api.get_latest_version().version if api.get_latest_version() else None,
                    "status": api.get_latest_version().status.value if api.get_latest_version() else "unknown"
                }
                for api in apis
            ],
            "total": len(apis),
            "categories": get_registry().get_categories()
        }

    except Exception as e:
        logger.error(f"Marketplace list APIs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/apis/{name}")
async def get_marketplace_api(
    request: Request,
    name: str
):
    """
    Hent specifik API definition.

    Args:
        name: API navn

    Returns:
        Komplet API definition med alle versioner
    """
    api = get_api(name)
    if not api:
        raise HTTPException(status_code=404, detail=f"API '{name}' not found")

    latest = api.get_latest_version()

    return {
        "success": True,
        "api": {
            "id": api.id,
            "name": api.name,
            "display_name": api.display_name,
            "description": api.description,
            "category": api.category,
            "tags": api.tags,
            "base_path": api.base_path,
            "default_rate_limit": api.default_rate_limit,
            "documentation_url": api.documentation_url,
            "support_email": api.support_email,
            "created_at": api.created_at.isoformat(),
            "updated_at": api.updated_at.isoformat(),
            "versions": [
                {
                    "version": v.version,
                    "status": v.status.value,
                    "released_at": v.released_at.isoformat() if v.released_at else None,
                    "endpoints_count": len(v.endpoints),
                    "breaking_changes": v.breaking_changes
                }
                for v in api.versions
            ],
            "latest_version": {
                "version": latest.version,
                "status": latest.status.value,
                "endpoints": [
                    {
                        "path": ep.path,
                        "method": ep.method.value,
                        "description": ep.description,
                        "requires_auth": ep.requires_auth,
                        "rate_limit": ep.rate_limit,
                        "tags": ep.tags
                    }
                    for ep in latest.endpoints
                ]
            } if latest else None
        }
    }


@router.get("/apis/{name}/openapi")
async def get_api_openapi_spec(
    request: Request,
    name: str
):
    """
    Hent OpenAPI specification for en API.

    Args:
        name: API navn

    Returns:
        OpenAPI 3.0 specification
    """
    spec = get_registry().to_openapi(name)
    if not spec:
        raise HTTPException(status_code=404, detail=f"API '{name}' not found")

    return spec


@router.post("/apis")
async def create_marketplace_api(
    request: Request,
    api_data: APICreate
):
    """
    Registrer en ny API i marketplace.

    Kræver admin rettigheder.
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Check if API already exists
    if get_api(api_data.name):
        raise HTTPException(status_code=409, detail=f"API '{api_data.name}' already exists")

    try:
        # Convert endpoints
        endpoints = [
            {
                "path": ep.path,
                "method": ep.method,
                "description": ep.description,
                "parameters": ep.parameters,
                "request_body": ep.request_body,
                "response": ep.response,
                "rate_limit": ep.rate_limit,
                "requires_auth": ep.requires_auth,
                "tags": ep.tags
            }
            for ep in api_data.endpoints
        ]

        api = register_api(
            name=api_data.name,
            display_name=api_data.display_name,
            description=api_data.description,
            category=api_data.category,
            version=api_data.version,
            endpoints=endpoints,
            rate_limit=api_data.rate_limit,
            tags=api_data.tags,
            owner=user_id
        )

        logger.info(f"API '{api_data.name}' registered by user {user_id}")

        return {
            "success": True,
            "message": f"API '{api_data.name}' registered successfully",
            "api_id": api.id
        }

    except Exception as e:
        logger.error(f"API registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# QUOTA ENDPOINTS
# ============================================

@router.get("/quota")
async def get_current_quota(request: Request):
    """
    Hent aktuel quota for authenticated user.

    Returns:
        QuotaResponse med brugerens quota status
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        quota = await get_user_quota(user_id)
        return {
            "success": True,
            "quota": quota.to_dict()
        }

    except Exception as e:
        logger.error(f"Get quota error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quota/check")
async def check_quota_status(
    request: Request,
    api_name: Optional[str] = Query(None)
):
    """
    Tjek om bruger kan lave en request.

    Args:
        api_name: Optional API-specifik check

    Returns:
        Boolean og eventuel ventetid
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        can_request = await check_quota(user_id, api_name)
        manager = get_quota_manager()
        wait_time = await manager.get_wait_time(user_id)

        return {
            "success": True,
            "can_request": can_request,
            "wait_time_seconds": wait_time
        }

    except Exception as e:
        logger.error(f"Check quota error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# USAGE ENDPOINTS
# ============================================

@router.get("/usage")
async def get_usage_statistics(
    request: Request,
    days: int = Query(1, ge=1, le=90, description="Number of days"),
    api_name: Optional[str] = Query(None)
):
    """
    Hent usage statistikker.

    Args:
        days: Antal dage at inkludere
        api_name: Optional API filter

    Returns:
        UsageStatsResponse
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        stats = await get_usage_stats(
            user_id=user_id,
            api_name=api_name,
            days=days
        )

        return {
            "success": True,
            "stats": stats.to_dict()
        }

    except Exception as e:
        logger.error(f"Get usage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/summary")
async def get_usage_summary(
    request: Request,
    days: int = Query(30, ge=1, le=365)
):
    """
    Hent usage summary for bruger.

    Args:
        days: Antal dage at inkludere

    Returns:
        Summary med top APIs og endpoints
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        tracker = get_usage_tracker()
        summary = await tracker.get_user_summary(user_id, days)

        return {
            "success": True,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Get usage summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/cost")
async def get_estimated_cost(
    request: Request,
    days: int = Query(30, ge=1, le=365)
):
    """
    Hent estimeret kostnad for en periode.

    Args:
        days: Antal dage

    Returns:
        Cost breakdown
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        tracker = get_usage_tracker()
        now = datetime.utcnow()
        start = now - timedelta(days=days)

        cost = await tracker.calculate_cost(user_id, start, now)

        return {
            "success": True,
            "cost": cost
        }

    except Exception as e:
        logger.error(f"Get cost error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# HEALTH & CATEGORIES
# ============================================

@router.get("/health")
async def marketplace_health():
    """
    Marketplace sundhedstjek.
    """
    registry = get_registry()

    return {
        "status": "healthy",
        "registered_apis": len(registry.list_all()),
        "categories": registry.get_categories(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/categories")
async def list_categories():
    """
    List alle API kategorier.
    """
    registry = get_registry()
    categories = registry.get_categories()

    return {
        "success": True,
        "categories": [
            {
                "name": cat,
                "api_count": len(registry.list_by_category(cat))
            }
            for cat in categories
        ]
    }


logger.info("✅ Marketplace endpoints configured")
