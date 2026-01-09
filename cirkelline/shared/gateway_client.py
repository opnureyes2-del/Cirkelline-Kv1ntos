"""
Gateway Client SDK - For use by other platforms in the Cirkelline ecosystem
=============================================================================

This module provides a simple client for validating tokens and
exchanging tokens across platforms.

COPIED FROM: cosmic-library/backend/services/gateway_client.py
DATE: 2026-01-09
PURPOSE: P2-INT-2 Fælles Authentication Integration

Usage (in kv1ntos):

    from cirkelline.shared.gateway_client import GatewayClient

    gateway = GatewayClient(
        gateway_url="http://localhost:7779",
        platform_code="kv1ntos",
        api_key="your-platform-api-key"
    )

    # Validate a token
    result = await gateway.validate_token(token)
    if result.valid:
        print(f"User: {result.user_email}, Tier: {result.tier}")

    # Check if user has a feature
    if gateway.has_feature(result, "document_ocr"):
        # User can use OCR

    # Exchange token for another platform
    exchange_token = await gateway.exchange_token(token, "consulting")
"""

import httpx
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class CustomerTier(str, Enum):
    """Customer tiers"""
    INCOGNITO = "incognito"
    NEW_USER = "new_user"
    COMPANY = "company"
    VIP = "vip"
    ENTERPRISE = "enterprise"
    CREATOR = "creator"          # System creator / superadmin


@dataclass
class TokenValidationResult:
    """Result of token validation"""
    valid: bool
    user_email: Optional[str] = None
    user_type: Optional[str] = None
    tier: Optional[str] = None
    platforms: Optional[List[str]] = None
    features: Optional[List[str]] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TokenExchangeResult:
    """Result of token exchange"""
    success: bool
    exchange_token: Optional[str] = None
    expires_in_seconds: int = 300
    error: Optional[str] = None


class GatewayClient:
    """
    Client for the Cirkelline Gateway (CKC).

    Use this in other platforms to:
    - Validate tokens from the gateway
    - Exchange tokens for cross-platform navigation
    - Check user features and tier

    Example:
        gateway = GatewayClient(
            gateway_url="http://localhost:7779",
            platform_code="kv1ntos",
            api_key="your-api-key"
        )

        result = await gateway.validate_token(token)
        if result.valid and "document_ocr" in result.features:
            # User can use OCR
    """

    def __init__(
        self,
        gateway_url: str = "http://localhost:7779",
        platform_code: str = "kv1ntos",
        api_key: Optional[str] = None,
        timeout: float = 5.0
    ):
        """
        Initialize the gateway client.

        Args:
            gateway_url: URL of the CKC gateway
            platform_code: Code of this platform (e.g., "kv1ntos")
            api_key: API key for platform authentication
            timeout: Request timeout in seconds
        """
        self.gateway_url = gateway_url.rstrip("/")
        self.platform_code = platform_code
        self.api_key = api_key
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Check if the gateway client is properly configured"""
        return bool(self.gateway_url and self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for requests"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def validate_token(self, token: str) -> TokenValidationResult:
        """
        Validate a token with the gateway.

        Args:
            token: JWT token to validate

        Returns:
            TokenValidationResult with validation details
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.gateway_url}/api/gateway/token/validate",
                    headers=self._get_headers(),
                    json={
                        "token": token,
                        "requesting_platform": self.platform_code
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return TokenValidationResult(
                        valid=data.get("valid", False),
                        user_email=data.get("user_email"),
                        user_type=data.get("user_type"),
                        tier=data.get("tier"),
                        platforms=data.get("platforms", []),
                        features=data.get("features", []),
                        session_id=data.get("session_id"),
                        error=data.get("error")
                    )
                else:
                    return TokenValidationResult(
                        valid=False,
                        error=f"Gateway returned {response.status_code}"
                    )
        except Exception as e:
            return TokenValidationResult(
                valid=False,
                error=f"Gateway connection failed: {str(e)}"
            )

    async def exchange_token(
        self,
        token: str,
        target_platform: str
    ) -> TokenExchangeResult:
        """
        Exchange a token for a short-lived token for another platform.

        Args:
            token: Current JWT token
            target_platform: Platform to get token for

        Returns:
            TokenExchangeResult with the exchange token
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.gateway_url}/api/gateway/token/exchange",
                    headers=self._get_headers(),
                    json={
                        "token": token,
                        "target_platform": target_platform,
                        "source_platform": self.platform_code
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return TokenExchangeResult(
                        success=data.get("success", False),
                        exchange_token=data.get("exchange_token"),
                        expires_in_seconds=data.get("expires_in_seconds", 300),
                        error=data.get("error")
                    )
                else:
                    return TokenExchangeResult(
                        success=False,
                        error=f"Gateway returned {response.status_code}"
                    )
        except Exception as e:
            return TokenExchangeResult(
                success=False,
                error=f"Gateway connection failed: {str(e)}"
            )

    async def sso_login(
        self,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """
        SSO Login via the CKC Gateway.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with login result including tokens
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.gateway_url}/api/gateway/sso/login",
                    headers=self._get_headers(),
                    json={
                        "email": email,
                        "password": password,
                        "source_platform": self.platform_code
                    }
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "error": f"Gateway returned {response.status_code}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Gateway connection failed: {str(e)}"
            }

    async def refresh_tokens(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            Dict with new access_token and refresh_token
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.gateway_url}/api/gateway/token/refresh",
                    headers=self._get_headers(),
                    json={
                        "refresh_token": refresh_token,
                        "source_platform": self.platform_code
                    }
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "error": f"Gateway returned {response.status_code}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Gateway connection failed: {str(e)}"
            }

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user info from token.

        Args:
            token: JWT token

        Returns:
            Dict with user info
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.gateway_url}/api/gateway/me",
                    headers={
                        **self._get_headers(),
                        "Authorization": f"Bearer {token}"
                    }
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Gateway returned {response.status_code}"}
        except Exception as e:
            return {"error": f"Gateway connection failed: {str(e)}"}

    async def get_platforms(self) -> List[Dict[str, Any]]:
        """
        Get list of registered platforms.

        Returns:
            List of platform info dicts
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.gateway_url}/api/gateway/platforms",
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return []
        except Exception:
            return []

    async def get_tiers(self) -> List[Dict[str, Any]]:
        """
        Get list of available tiers.

        Returns:
            List of tier info dicts
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.gateway_url}/api/gateway/tiers",
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return []
        except Exception:
            return []

    @staticmethod
    def has_feature(result: TokenValidationResult, feature: str) -> bool:
        """
        Check if user has a specific feature.

        Args:
            result: TokenValidationResult from validate_token
            feature: Feature code to check

        Returns:
            True if user has the feature
        """
        if not result.valid or not result.features:
            return False
        return feature in result.features

    @staticmethod
    def has_platform_access(result: TokenValidationResult, platform: str) -> bool:
        """
        Check if user has access to a platform.

        Args:
            result: TokenValidationResult from validate_token
            platform: Platform code to check

        Returns:
            True if user has access
        """
        if not result.valid or not result.platforms:
            return False
        return platform in result.platforms

    @staticmethod
    def is_tier_or_higher(result: TokenValidationResult, min_tier: str) -> bool:
        """
        Check if user is at or above a minimum tier.

        Args:
            result: TokenValidationResult from validate_token
            min_tier: Minimum tier required

        Returns:
            True if user meets the tier requirement
        """
        if not result.valid or not result.tier:
            return False

        tier_order = ["incognito", "new_user", "company", "vip", "enterprise"]
        try:
            user_tier_index = tier_order.index(result.tier)
            min_tier_index = tier_order.index(min_tier)
            return user_tier_index >= min_tier_index
        except ValueError:
            return False


# =============================================================================
# FASTAPI DEPENDENCY FOR OTHER PLATFORMS
# =============================================================================

class GatewayAuthDependency:
    """
    FastAPI dependency for validating gateway tokens.

    Usage in kv1ntos:

        from cirkelline.shared.gateway_client import GatewayClient, GatewayAuthDependency

        gateway = GatewayClient(
            gateway_url="http://localhost:7779",
            platform_code="kv1ntos",
            api_key="your-api-key"
        )

        auth = GatewayAuthDependency(gateway)

        @app.get("/protected")
        async def protected_route(user: TokenValidationResult = Depends(auth)):
            return {"email": user.user_email}

        @app.get("/vip-only")
        async def vip_route(user: TokenValidationResult = Depends(auth.require_tier("vip"))):
            return {"message": "Welcome VIP!"}

        @app.get("/ocr-feature")
        async def ocr_route(user: TokenValidationResult = Depends(auth.require_feature("document_ocr"))):
            return {"message": "OCR enabled"}
    """

    def __init__(self, gateway_client: GatewayClient):
        self.gateway = gateway_client

    async def __call__(
        self,
        authorization: str = None
    ) -> TokenValidationResult:
        """
        Validate token from Authorization header.

        Args:
            authorization: Authorization header value

        Returns:
            TokenValidationResult if valid

        Raises:
            HTTPException if invalid
        """
        from fastapi import HTTPException, status, Header

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Extract token from Bearer scheme
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

        result = await self.gateway.validate_token(token)

        if not result.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.error or "Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return result

    def require_tier(self, min_tier: str):
        """
        Create a dependency that requires a minimum tier.

        Args:
            min_tier: Minimum tier required

        Returns:
            Dependency function
        """
        from fastapi import Header

        async def dependency(
            authorization: str = Header(None, alias="Authorization")
        ) -> TokenValidationResult:
            from fastapi import HTTPException, status

            result = await self(authorization)

            if not GatewayClient.is_tier_or_higher(result, min_tier):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {min_tier} tier or higher"
                )

            return result

        return dependency

    def require_feature(self, feature: str):
        """
        Create a dependency that requires a specific feature.

        Args:
            feature: Feature code required

        Returns:
            Dependency function
        """
        from fastapi import Header

        async def dependency(
            authorization: str = Header(None, alias="Authorization")
        ) -> TokenValidationResult:
            from fastapi import HTTPException, status

            result = await self(authorization)

            if not GatewayClient.has_feature(result, feature):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature not available: {feature}"
                )

            return result

        return dependency


# =============================================================================
# LOCAL TOKEN VALIDATION (FOR PERFORMANCE)
# =============================================================================

class LocalTokenValidator:
    """
    Validate tokens locally without calling the gateway.

    This is faster but requires the shared secret and
    doesn't update session activity on the gateway.

    Use for high-frequency endpoints where performance matters.

    Usage:
        from cirkelline.shared.gateway_client import LocalTokenValidator

        validator = LocalTokenValidator(
            secret_key="your-shared-secret",
            algorithm="HS256"
        )

        result = validator.validate(token)
        if result.valid:
            print(f"User: {result.user_email}")
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize local validator.

        Args:
            secret_key: Shared secret key (same as gateway)
            algorithm: JWT algorithm
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def validate(self, token: str) -> TokenValidationResult:
        """
        Validate token locally.

        Args:
            token: JWT token to validate

        Returns:
            TokenValidationResult with validation details
        """
        try:
            from jose import jwt, JWTError

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            return TokenValidationResult(
                valid=True,
                user_email=payload.get("sub"),
                user_type=payload.get("user_type"),
                tier=payload.get("tier"),
                platforms=payload.get("platforms", []),
                features=payload.get("features", []),
                session_id=payload.get("session_id")
            )

        except JWTError as e:
            return TokenValidationResult(
                valid=False,
                error=str(e)
            )
        except Exception as e:
            return TokenValidationResult(
                valid=False,
                error=f"Validation error: {str(e)}"
            )
