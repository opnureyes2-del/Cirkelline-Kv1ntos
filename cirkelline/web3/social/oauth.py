"""
OAuth2 Manager for Social Media APIs
====================================

Handles OAuth2 authentication flows for social media platforms.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional
import secrets
import logging

logger = logging.getLogger(__name__)


@dataclass
class OAuthTokens:
    """OAuth2 token container."""

    access_token: str
    token_type: str = "Bearer"
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scope: str = ""

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "refresh_token": self.refresh_token or "",
            "expires_at": self.expires_at.isoformat() if self.expires_at else "",
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "OAuthTokens":
        """Create from dictionary."""
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])

        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            refresh_token=data.get("refresh_token") or None,
            expires_at=expires_at,
            scope=data.get("scope", ""),
        )


class OAuthManager:
    """
    OAuth2 flow manager for social media platforms.

    Handles authorization URL generation, token exchange,
    and token refresh operations.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorize_url: str,
        token_url: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorize_url = authorize_url
        self.token_url = token_url
        self._state_store: Dict[str, datetime] = {}

    def generate_authorization_url(
        self,
        scopes: list[str],
        extra_params: Optional[Dict[str, str]] = None,
    ) -> tuple[str, str]:
        """
        Generate OAuth2 authorization URL.

        Returns:
            Tuple of (authorization_url, state_token)
        """
        state = secrets.token_urlsafe(32)
        self._state_store[state] = datetime.utcnow()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
        }

        if extra_params:
            params.update(extra_params)

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"{self.authorize_url}?{query_string}"

        logger.info(f"Generated authorization URL with state: {state[:8]}...")
        return auth_url, state

    def validate_state(self, state: str) -> bool:
        """Validate state token from callback."""
        if state not in self._state_store:
            return False

        created_at = self._state_store[state]
        if datetime.utcnow() - created_at > timedelta(minutes=10):
            del self._state_store[state]
            return False

        del self._state_store[state]
        return True

    async def exchange_code(self, code: str) -> Optional[OAuthTokens]:
        """
        Exchange authorization code for tokens.

        Note: Implementation requires httpx for actual API calls.
        Currently returns placeholder for API key availability.
        """
        logger.info("Exchanging authorization code for tokens")

        # Placeholder - actual implementation would use httpx:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         self.token_url,
        #         data={
        #             "grant_type": "authorization_code",
        #             "code": code,
        #             "client_id": self.client_id,
        #             "client_secret": self.client_secret,
        #             "redirect_uri": self.redirect_uri,
        #         }
        #     )
        #     data = response.json()
        #     return OAuthTokens(...)

        return None

    async def refresh_tokens(self, refresh_token: str) -> Optional[OAuthTokens]:
        """
        Refresh expired access token.

        Note: Implementation requires httpx for actual API calls.
        """
        logger.info("Refreshing access token")
        return None

    def clear_expired_states(self) -> int:
        """Clear expired state tokens from store."""
        now = datetime.utcnow()
        expired = [
            state
            for state, created in self._state_store.items()
            if now - created > timedelta(minutes=10)
        ]

        for state in expired:
            del self._state_store[state]

        return len(expired)


# Platform-specific OAuth configurations
TWITTER_OAUTH_CONFIG = {
    "authorize_url": "https://twitter.com/i/oauth2/authorize",
    "token_url": "https://api.twitter.com/2/oauth2/token",
    "scopes": ["tweet.read", "users.read", "offline.access"],
}

MASTODON_OAUTH_CONFIG = {
    "authorize_url": "/oauth/authorize",  # Appended to instance URL
    "token_url": "/oauth/token",
    "scopes": ["read", "write", "follow"],
}
