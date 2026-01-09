"""
Gateway Authentication Module for kv1ntos
==========================================
Provides FastAPI dependencies for CKC Gateway authentication.

This module uses the GatewayClient SDK to validate tokens against
the central CKC Gateway (lib-admin on port 7779).

INTEGRATION: P2-INT-2 Fælles Authentication Integration
DATE: 2026-01-09

Usage:
    from cirkelline.shared.gateway_auth import (
        gateway_auth,          # FastAPI dependency for protected routes
        optional_gateway_auth, # Optional auth (returns None if not authenticated)
        require_tier,          # Require minimum tier
        require_feature,       # Require specific feature
    )

    @app.get("/protected")
    async def protected_route(user = Depends(gateway_auth)):
        return {"email": user.user_email}

    @app.get("/vip-only")
    async def vip_route(user = Depends(require_tier("vip"))):
        return {"message": "Welcome VIP!"}
"""

import os
from typing import Optional
from fastapi import HTTPException, Header, status

from cirkelline.config import logger
from cirkelline.shared.gateway_client import (
    GatewayClient,
    TokenValidationResult,
    GatewayAuthDependency,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:7779")
GATEWAY_PLATFORM_CODE = os.getenv("GATEWAY_PLATFORM_CODE", "kv1ntos")
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY", "")

# Create singleton GatewayClient instance
_gateway_client: Optional[GatewayClient] = None


def get_gateway_client() -> GatewayClient:
    """
    Get or create the singleton GatewayClient.

    Returns:
        GatewayClient instance configured for kv1ntos
    """
    global _gateway_client

    if _gateway_client is None:
        _gateway_client = GatewayClient(
            gateway_url=GATEWAY_URL,
            platform_code=GATEWAY_PLATFORM_CODE,
            api_key=GATEWAY_API_KEY,
            timeout=10.0
        )
        logger.info(f"✅ GatewayClient initialized: {GATEWAY_URL}")

    return _gateway_client


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================

async def gateway_auth(
    authorization: str = Header(None, alias="Authorization")
) -> TokenValidationResult:
    """
    FastAPI dependency for gateway token authentication.

    Validates Bearer token against the CKC Gateway.
    Raises HTTPException 401 if invalid.

    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenValidationResult = Depends(gateway_auth)):
            return {"email": user.user_email, "tier": user.tier}

    Args:
        authorization: Authorization header value (Bearer token)

    Returns:
        TokenValidationResult with user info if valid

    Raises:
        HTTPException 401: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token from Bearer scheme
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    client = get_gateway_client()
    result = await client.validate_token(token)

    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error or "Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check platform access
    if result.platforms and GATEWAY_PLATFORM_CODE not in result.platforms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to {GATEWAY_PLATFORM_CODE} not permitted"
        )

    logger.debug(f"✅ Gateway auth: {result.user_email} ({result.tier})")
    return result


async def optional_gateway_auth(
    authorization: str = Header(None, alias="Authorization")
) -> Optional[TokenValidationResult]:
    """
    FastAPI dependency for optional gateway authentication.

    Returns None if no token provided, validates if token present.

    Usage:
        @app.get("/public")
        async def public_route(user: Optional[TokenValidationResult] = Depends(optional_gateway_auth)):
            if user:
                return {"message": f"Hello {user.user_email}!"}
            return {"message": "Hello guest!"}

    Args:
        authorization: Authorization header value (Bearer token)

    Returns:
        TokenValidationResult if authenticated, None otherwise
    """
    if not authorization:
        return None

    try:
        return await gateway_auth(authorization)
    except HTTPException:
        return None


def require_tier(min_tier: str):
    """
    Create a FastAPI dependency that requires a minimum tier.

    Usage:
        @app.get("/vip-feature")
        async def vip_feature(user = Depends(require_tier("vip"))):
            return {"message": "Welcome VIP!"}

    Args:
        min_tier: Minimum tier required (incognito, new_user, company, vip, enterprise)

    Returns:
        FastAPI dependency function
    """
    async def dependency(
        authorization: str = Header(None, alias="Authorization")
    ) -> TokenValidationResult:
        result = await gateway_auth(authorization)

        if not GatewayClient.is_tier_or_higher(result, min_tier):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_tier} tier or higher",
                headers={"X-Upgrade-Required": "true"}
            )

        return result

    return dependency


def require_feature(feature: str):
    """
    Create a FastAPI dependency that requires a specific feature.

    Usage:
        @app.get("/ocr-feature")
        async def ocr_feature(user = Depends(require_feature("document_ocr"))):
            return {"message": "OCR enabled!"}

    Args:
        feature: Feature code required (e.g., "document_ocr", "deep_research")

    Returns:
        FastAPI dependency function
    """
    async def dependency(
        authorization: str = Header(None, alias="Authorization")
    ) -> TokenValidationResult:
        result = await gateway_auth(authorization)

        if not GatewayClient.has_feature(result, feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature not available: {feature}",
                headers={"X-Feature-Required": feature}
            )

        return result

    return dependency


def require_platform(platform: str):
    """
    Create a FastAPI dependency that requires access to a specific platform.

    Usage:
        @app.get("/cosmic-bridge")
        async def cosmic_bridge(user = Depends(require_platform("cosmic_library"))):
            return {"message": "Cosmic Library access!"}

    Args:
        platform: Platform code required (e.g., "cosmic_library", "consulting")

    Returns:
        FastAPI dependency function
    """
    async def dependency(
        authorization: str = Header(None, alias="Authorization")
    ) -> TokenValidationResult:
        result = await gateway_auth(authorization)

        if not GatewayClient.has_platform_access(result, platform):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Platform not accessible: {platform}",
                headers={"X-Platform-Required": platform}
            )

        return result

    return dependency


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def validate_token_direct(token: str) -> TokenValidationResult:
    """
    Validate a token directly without FastAPI context.

    Useful for non-FastAPI contexts like WebSocket handlers,
    background tasks, or CLI tools.

    Args:
        token: JWT token string (without "Bearer " prefix)

    Returns:
        TokenValidationResult with validation details
    """
    client = get_gateway_client()
    return await client.validate_token(token)


async def exchange_token(token: str, target_platform: str) -> Optional[str]:
    """
    Exchange a token for another platform.

    Used for cross-platform navigation (SSO).

    Args:
        token: Current JWT token
        target_platform: Platform code to get token for

    Returns:
        Exchange token string if successful, None otherwise
    """
    client = get_gateway_client()
    result = await client.exchange_token(token, target_platform)

    if result.success:
        return result.exchange_token

    logger.warning(f"Token exchange failed: {result.error}")
    return None


async def get_user_info(token: str) -> dict:
    """
    Get user info from token.

    Args:
        token: JWT token

    Returns:
        Dict with user info
    """
    client = get_gateway_client()
    return await client.get_user_info(token)


# =============================================================================
# INITIALIZATION
# =============================================================================

def is_gateway_configured() -> bool:
    """Check if gateway authentication is properly configured."""
    return bool(GATEWAY_URL and GATEWAY_API_KEY)


logger.info(f"✅ Gateway auth module loaded (gateway={'configured' if is_gateway_configured() else 'NOT configured'})")
