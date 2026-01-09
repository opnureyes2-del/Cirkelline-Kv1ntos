"""
CKC Gateway Authentication Middleware
=====================================
Middleware for validating tokens against the central CKC Gateway.

INTEGRATION: P2-INT-2 Fælles Authentication Integration
DATE: 2026-01-09

This middleware:
1. Extracts Bearer token from Authorization header
2. Validates token against CKC Gateway (lib-admin on port 7779)
3. Sets user context in request.state for downstream use
4. Falls back to local JWT validation if gateway unavailable

Execution Order (add BEFORE RBACGatewayMiddleware):
1. SessionsDateFilterMiddleware
2. AuditTrailMiddleware
3. GatewayAuthMiddleware  <-- NEW
4. RBACGatewayMiddleware
5. AnonymousUserMiddleware
6. SessionLoggingMiddleware
7. JWTMiddleware (from AGNO - optional fallback)
"""

import os
from typing import Optional
from starlette.requests import Request as StarletteRequest
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from cirkelline.config import logger

# Import gateway auth utilities
from cirkelline.shared.gateway_auth import (
    get_gateway_client,
    is_gateway_configured,
)
from cirkelline.shared.gateway_client import TokenValidationResult


# =============================================================================
# CONFIGURATION
# =============================================================================

# Enable/disable gateway auth (can be toggled via env)
GATEWAY_AUTH_ENABLED = os.getenv("GATEWAY_AUTH_ENABLED", "true").lower() == "true"

# Fallback to local JWT if gateway fails
FALLBACK_TO_LOCAL_JWT = os.getenv("FALLBACK_TO_LOCAL_JWT", "true").lower() == "true"

# Endpoints that bypass gateway auth (public endpoints)
PUBLIC_ENDPOINTS = [
    "/health",
    "/config",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
    "/api/auth/login",
    "/api/auth/signup",
    "/api/auth/google",
    "/api/auth/google/callback",
    "/api/status",
]


# =============================================================================
# GATEWAY AUTH MIDDLEWARE
# =============================================================================

class GatewayAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates tokens against CKC Gateway.

    Sets the following in request.state:
        - user_id: User's unique identifier
        - user_email: User's email address
        - user_type: Type of user (customer, admin, creator)
        - tier_slug: User's subscription tier (incognito, new_user, company, vip, enterprise)
        - tier_level: Numeric tier level (1-5)
        - is_admin: Boolean indicating admin status
        - platforms: List of accessible platforms
        - features: List of enabled features
        - session_id: Gateway session ID
        - gateway_validated: True if validated via gateway

    Integration:
        Add this middleware BEFORE RBACGatewayMiddleware in my_os.py:

        app.add_middleware(GatewayAuthMiddleware)

    Note:
        This middleware does NOT block unauthorized requests.
        It just sets the user context. Use gateway_auth dependency
        or RBACGatewayMiddleware for actual enforcement.
    """

    async def dispatch(self, request: StarletteRequest, call_next):
        """Process request and validate token with gateway."""

        # Skip for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip for public endpoints
        path = request.url.path
        for public_path in PUBLIC_ENDPOINTS:
            if path.startswith(public_path):
                return await call_next(request)

        # Initialize request.state.dependencies if needed
        if not hasattr(request.state, 'dependencies'):
            request.state.dependencies = {}

        # Check if gateway auth is enabled
        if not GATEWAY_AUTH_ENABLED:
            logger.debug("Gateway auth disabled - skipping")
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            # No token - set anonymous defaults
            self._set_anonymous_context(request)
            return await call_next(request)

        # Extract token
        token = auth_header[7:]  # Remove "Bearer " prefix

        # Validate with gateway
        try:
            if is_gateway_configured():
                result = await self._validate_with_gateway(token)

                if result and result.valid:
                    self._set_user_context(request, result)
                    return await call_next(request)
                else:
                    # Gateway validation failed
                    logger.warning(f"Gateway validation failed: {result.error if result else 'No result'}")

                    if FALLBACK_TO_LOCAL_JWT:
                        # Try local JWT validation
                        local_result = await self._validate_local_jwt(token)
                        if local_result:
                            self._set_local_context(request, local_result)
                            return await call_next(request)

                    # Both failed - set anonymous
                    self._set_anonymous_context(request)

            else:
                # Gateway not configured - fallback to local JWT
                logger.debug("Gateway not configured - using local JWT")
                local_result = await self._validate_local_jwt(token)
                if local_result:
                    self._set_local_context(request, local_result)
                else:
                    self._set_anonymous_context(request)

        except Exception as e:
            logger.error(f"Gateway auth error: {e}")
            self._set_anonymous_context(request)

        return await call_next(request)

    async def _validate_with_gateway(self, token: str) -> Optional[TokenValidationResult]:
        """Validate token with CKC Gateway."""
        try:
            client = get_gateway_client()
            result = await client.validate_token(token)
            return result
        except Exception as e:
            logger.error(f"Gateway validation error: {e}")
            return None

    async def _validate_local_jwt(self, token: str) -> Optional[dict]:
        """Validate token locally (fallback)."""
        try:
            import jwt as pyjwt

            secret_key = os.getenv("JWT_SECRET_KEY")
            if not secret_key:
                return None

            payload = pyjwt.decode(
                token,
                secret_key,
                algorithms=["HS256"]
            )
            return payload

        except Exception as e:
            logger.debug(f"Local JWT validation failed: {e}")
            return None

    def _set_user_context(self, request: StarletteRequest, result: TokenValidationResult):
        """Set user context from gateway validation result."""
        # Map tier to tier_level
        tier_levels = {
            "incognito": 0,
            "new_user": 1,
            "company": 2,
            "vip": 3,
            "enterprise": 4,
            "creator": 5,
        }

        tier = result.tier or "new_user"
        tier_level = tier_levels.get(tier, 1)

        # Set in request.state
        request.state.user_id = result.user_email  # Use email as user_id for compatibility
        request.state.user_email = result.user_email
        request.state.user_type = result.user_type or "customer"
        request.state.tier_slug = tier
        request.state.tier_level = tier_level
        request.state.is_admin = result.user_type in ["admin", "creator"]
        request.state.platforms = result.platforms or []
        request.state.features = result.features or []
        request.state.session_id = result.session_id
        request.state.gateway_validated = True

        # Also set in dependencies for compatibility
        request.state.dependencies["user_id"] = result.user_email
        request.state.dependencies["user_email"] = result.user_email
        request.state.dependencies["user_name"] = result.user_email.split("@")[0]
        request.state.dependencies["user_role"] = "Admin" if request.state.is_admin else "User"
        request.state.dependencies["user_type"] = result.user_type or "customer"
        request.state.dependencies["tier_slug"] = tier
        request.state.dependencies["tier_level"] = tier_level
        request.state.dependencies["is_admin"] = request.state.is_admin

        logger.debug(f"Gateway auth: {result.user_email} ({tier})")

    def _set_local_context(self, request: StarletteRequest, payload: dict):
        """Set user context from local JWT payload."""
        user_id = payload.get("user_id", payload.get("sub", "anonymous"))
        email = payload.get("email", payload.get("sub", "anonymous"))

        request.state.user_id = user_id
        request.state.user_email = email
        request.state.user_type = payload.get("user_type", "Regular")
        request.state.tier_slug = payload.get("tier_slug", "member")
        request.state.tier_level = payload.get("tier_level", 1)
        request.state.is_admin = payload.get("is_admin", False)
        request.state.platforms = []
        request.state.features = []
        request.state.session_id = None
        request.state.gateway_validated = False

        # Also set in dependencies
        request.state.dependencies["user_id"] = user_id
        request.state.dependencies["user_email"] = email
        request.state.dependencies["user_name"] = payload.get("user_name", payload.get("display_name", "User"))
        request.state.dependencies["user_role"] = payload.get("user_role", "User")
        request.state.dependencies["user_type"] = payload.get("user_type", "Regular")
        request.state.dependencies["tier_slug"] = payload.get("tier_slug", "member")
        request.state.dependencies["tier_level"] = payload.get("tier_level", 1)
        request.state.dependencies["is_admin"] = payload.get("is_admin", False)

        logger.debug(f"Local JWT auth: {email}")

    def _set_anonymous_context(self, request: StarletteRequest):
        """Set anonymous user context."""
        request.state.user_id = "anonymous"
        request.state.user_email = None
        request.state.user_type = "Anonymous"
        request.state.tier_slug = "incognito"
        request.state.tier_level = 0
        request.state.is_admin = False
        request.state.platforms = []
        request.state.features = []
        request.state.session_id = None
        request.state.gateway_validated = False

        # Also set in dependencies
        request.state.dependencies["user_id"] = "anonymous"
        request.state.dependencies["user_name"] = "Guest"
        request.state.dependencies["user_role"] = "Visitor"
        request.state.dependencies["user_type"] = "Anonymous"
        request.state.dependencies["tier_slug"] = "incognito"
        request.state.dependencies["tier_level"] = 0
        request.state.dependencies["is_admin"] = False


# =============================================================================
# STRICT GATEWAY AUTH MIDDLEWARE
# =============================================================================

class StrictGatewayAuthMiddleware(BaseHTTPMiddleware):
    """
    Strict gateway authentication middleware.

    Unlike GatewayAuthMiddleware, this BLOCKS requests if:
    - No token provided (for protected endpoints)
    - Token validation fails
    - User doesn't have access to this platform

    Use this for endpoints that REQUIRE authentication.

    Protected endpoints are configured via PROTECTED_ENDPOINT_PATTERNS.
    """

    # Endpoints that require authentication
    PROTECTED_ENDPOINT_PATTERNS = [
        "/admin/",
        "/api/memories/",
        "/api/knowledge/upload",
        "/api/knowledge/delete",
        "/api/export/",
        "/api/user/",
    ]

    async def dispatch(self, request: StarletteRequest, call_next):
        """Process request - block unauthorized access to protected endpoints."""

        # Skip for OPTIONS
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        # Check if this is a protected endpoint
        is_protected = any(
            path.startswith(pattern)
            for pattern in self.PROTECTED_ENDPOINT_PATTERNS
        )

        if not is_protected:
            return await call_next(request)

        # Protected endpoint - require valid gateway auth
        gateway_validated = getattr(request.state, 'gateway_validated', False)
        user_id = getattr(request.state, 'user_id', 'anonymous')

        if not gateway_validated or user_id == 'anonymous':
            logger.warning(f"Blocked: {path} - not authenticated via gateway")

            return JSONResponse(
                status_code=401,
                content={
                    "error": "authentication_required",
                    "message": "This endpoint requires authentication via CKC Gateway",
                    "gateway_required": True,
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        return await call_next(request)


logger.info("✅ Gateway authentication middleware loaded")
