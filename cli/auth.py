"""
Authentication Module
=====================
Secure authentication for Cirkelline Terminal CLI.
Handles JWT token management and secure storage.
"""

import os
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import httpx

from cli.config import get_token_path, load_config

logger = logging.getLogger(__name__)


@dataclass
class AuthToken:
    """Authentication token container."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[float] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    tier: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def needs_refresh(self, buffer_seconds: int = 300) -> bool:
        """Check if token needs refresh (within buffer time of expiry)."""
        if self.expires_at is None:
            return False
        return time.time() > (self.expires_at - buffer_seconds)


class AuthManager:
    """Manages authentication state and token lifecycle."""

    def __init__(self):
        self.config = load_config()
        self._token: Optional[AuthToken] = None
        self._load_cached_token()

    def _load_cached_token(self) -> None:
        """Load token from cache file."""
        token_path = get_token_path()

        if not token_path.exists():
            return

        try:
            with open(token_path) as f:
                data = json.load(f)
            self._token = AuthToken(**data)

            if self._token.is_expired():
                logger.info("Cached token expired, clearing")
                self._token = None
                token_path.unlink(missing_ok=True)

        except Exception as e:
            logger.warning(f"Failed to load cached token: {e}")

    def _save_token(self) -> None:
        """Save token to cache file."""
        if not self._token:
            return

        token_path = get_token_path()
        token_path.parent.mkdir(parents=True, exist_ok=True)

        # Secure file permissions (600)
        with open(token_path, "w") as f:
            json.dump({
                "access_token": self._token.access_token,
                "refresh_token": self._token.refresh_token,
                "expires_at": self._token.expires_at,
                "user_id": self._token.user_id,
                "user_email": self._token.user_email,
                "tier": self._token.tier,
            }, f)

        os.chmod(token_path, 0o600)

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid token."""
        return self._token is not None and not self._token.is_expired()

    @property
    def token(self) -> Optional[AuthToken]:
        """Get current token."""
        return self._token

    @property
    def access_token(self) -> Optional[str]:
        """Get access token string."""
        return self._token.access_token if self._token else None

    async def login(self, email: str, password: str) -> bool:
        """
        Authenticate with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            True if login successful
        """
        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
                response = await client.post(
                    f"{self.config.api_base_url}/api/auth/login",
                    json={"email": email, "password": password}
                )

                if response.status_code == 200:
                    data = response.json()
                    self._token = AuthToken(
                        access_token=data["access_token"],
                        refresh_token=data.get("refresh_token"),
                        expires_at=data.get("expires_at", time.time() + 3600),
                        user_id=data.get("user_id"),
                        user_email=email,
                        tier=data.get("tier", "member"),
                    )
                    self._save_token()
                    logger.info(f"Login successful for {email}")
                    return True
                else:
                    error = response.json().get("detail", "Authentication failed")
                    logger.warning(f"Login failed: {error}")
                    return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def refresh(self) -> bool:
        """Refresh access token using refresh token."""
        if not self._token or not self._token.refresh_token:
            return False

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
                response = await client.post(
                    f"{self.config.api_base_url}/api/auth/refresh",
                    json={"refresh_token": self._token.refresh_token}
                )

                if response.status_code == 200:
                    data = response.json()
                    self._token.access_token = data["access_token"]
                    self._token.expires_at = data.get("expires_at", time.time() + 3600)
                    if "refresh_token" in data:
                        self._token.refresh_token = data["refresh_token"]
                    self._save_token()
                    logger.info("Token refreshed successfully")
                    return True

        except Exception as e:
            logger.error(f"Token refresh error: {e}")

        return False

    def logout(self) -> None:
        """Clear authentication state."""
        self._token = None
        token_path = get_token_path()
        token_path.unlink(missing_ok=True)
        logger.info("Logged out")

    def get_auth_headers(self) -> dict:
        """Get HTTP headers with authorization."""
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token.access_token}"}


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
