"""
Social Media Platform Adapter
=============================

Unified interface for interacting with social media platforms
for backwards engineering research purposes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import os
import logging

logger = logging.getLogger(__name__)


class SocialPlatform(Enum):
    """Supported social media platforms."""

    TWITTER = "twitter"
    MASTODON = "mastodon"
    LENS = "lens"
    FARCASTER = "farcaster"
    BLUESKY = "bluesky"


@dataclass
class OAuthConfig:
    """OAuth2 configuration for social media APIs."""

    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str] = field(default_factory=list)
    authorize_url: Optional[str] = None
    token_url: Optional[str] = None


@dataclass
class SocialProfile:
    """Unified social media profile representation."""

    platform: SocialPlatform
    user_id: str
    username: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    verified: bool = False
    created_at: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SocialPost:
    """Unified social media post representation."""

    platform: SocialPlatform
    post_id: str
    author_id: str
    content: str
    created_at: datetime
    likes_count: int = 0
    reposts_count: int = 0
    replies_count: int = 0
    media_urls: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)


class SocialMediaAdapter(ABC):
    """
    Abstract base class for social media platform adapters.

    Provides unified interface for research operations across
    different social media platforms.
    """

    def __init__(
        self, platform: SocialPlatform, oauth_config: Optional[OAuthConfig] = None
    ):
        self.platform = platform
        self.oauth_config = oauth_config
        self._authenticated = False
        self._access_token: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        """Check if adapter is authenticated."""
        return self._authenticated

    @abstractmethod
    async def authenticate(self, access_token: str) -> bool:
        """Authenticate with the platform using access token."""
        pass

    @abstractmethod
    async def get_profile(self, user_id: str) -> Optional[SocialProfile]:
        """Fetch user profile by ID."""
        pass

    @abstractmethod
    async def get_posts(
        self,
        user_id: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Fetch posts from a user."""
        pass

    @abstractmethod
    async def search_posts(
        self,
        query: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Search posts by query."""
        pass

    @abstractmethod
    async def get_trending_topics(self, location: Optional[str] = None) -> List[str]:
        """Get trending topics/hashtags."""
        pass

    async def analyze_engagement(
        self, posts: List[SocialPost]
    ) -> Dict[str, Any]:
        """Analyze engagement metrics from posts."""
        if not posts:
            return {"total_posts": 0}

        total_likes = sum(p.likes_count for p in posts)
        total_reposts = sum(p.reposts_count for p in posts)
        total_replies = sum(p.replies_count for p in posts)

        return {
            "total_posts": len(posts),
            "total_likes": total_likes,
            "total_reposts": total_reposts,
            "total_replies": total_replies,
            "avg_likes": total_likes / len(posts),
            "avg_reposts": total_reposts / len(posts),
            "avg_replies": total_replies / len(posts),
            "engagement_rate": (total_likes + total_reposts + total_replies)
            / len(posts),
        }


class TwitterAdapter(SocialMediaAdapter):
    """Twitter/X API v2 adapter."""

    API_BASE_URL = "https://api.twitter.com/2"

    def __init__(self, oauth_config: Optional[OAuthConfig] = None):
        super().__init__(SocialPlatform.TWITTER, oauth_config)
        self._bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    async def authenticate(self, access_token: str) -> bool:
        """Authenticate with Twitter API."""
        self._access_token = access_token
        self._authenticated = True
        logger.info("Twitter adapter authenticated")
        return True

    async def get_profile(self, user_id: str) -> Optional[SocialProfile]:
        """Fetch Twitter user profile."""
        # Implementation would use httpx to call Twitter API
        # Placeholder for when API keys are available
        logger.info(f"Fetching Twitter profile: {user_id}")
        return SocialProfile(
            platform=self.platform,
            user_id=user_id,
            username=f"@{user_id}",
            display_name=user_id,
        )

    async def get_posts(
        self,
        user_id: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Fetch tweets from a user."""
        logger.info(f"Fetching tweets for user: {user_id}")
        return []

    async def search_posts(
        self,
        query: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Search tweets by query."""
        logger.info(f"Searching tweets: {query}")
        return []

    async def get_trending_topics(self, location: Optional[str] = None) -> List[str]:
        """Get Twitter trending topics."""
        logger.info(f"Fetching trending topics for: {location or 'global'}")
        return []


class MastodonAdapter(SocialMediaAdapter):
    """Mastodon API adapter for decentralized social network."""

    def __init__(
        self,
        instance_url: str = "https://mastodon.social",
        oauth_config: Optional[OAuthConfig] = None,
    ):
        super().__init__(SocialPlatform.MASTODON, oauth_config)
        self.instance_url = instance_url

    async def authenticate(self, access_token: str) -> bool:
        """Authenticate with Mastodon instance."""
        self._access_token = access_token
        self._authenticated = True
        logger.info(f"Mastodon adapter authenticated for {self.instance_url}")
        return True

    async def get_profile(self, user_id: str) -> Optional[SocialProfile]:
        """Fetch Mastodon user profile."""
        logger.info(f"Fetching Mastodon profile: {user_id}")
        return SocialProfile(
            platform=self.platform,
            user_id=user_id,
            username=user_id,
            display_name=user_id,
        )

    async def get_posts(
        self,
        user_id: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Fetch toots from a user."""
        logger.info(f"Fetching toots for user: {user_id}")
        return []

    async def search_posts(
        self,
        query: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Search toots by query."""
        logger.info(f"Searching toots: {query}")
        return []

    async def get_trending_topics(self, location: Optional[str] = None) -> List[str]:
        """Get Mastodon trending hashtags."""
        logger.info("Fetching Mastodon trending hashtags")
        return []


# Singleton instance
_social_adapter: Optional[SocialMediaAdapter] = None


def get_social_adapter(
    platform: SocialPlatform = SocialPlatform.TWITTER,
) -> SocialMediaAdapter:
    """Get singleton instance of social media adapter."""
    global _social_adapter

    if _social_adapter is None or _social_adapter.platform != platform:
        if platform == SocialPlatform.TWITTER:
            _social_adapter = TwitterAdapter()
        elif platform == SocialPlatform.MASTODON:
            _social_adapter = MastodonAdapter()
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    return _social_adapter
