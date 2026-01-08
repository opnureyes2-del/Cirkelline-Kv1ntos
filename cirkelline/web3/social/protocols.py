"""
Decentralized Social Protocols
==============================

Adapters for Web3-native social protocols like Lens Protocol and Farcaster.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from .adapter import SocialMediaAdapter, SocialPlatform, SocialPost, SocialProfile

logger = logging.getLogger(__name__)


class DecentralizedSocialProtocol(ABC):
    """Base class for decentralized social protocols."""

    @abstractmethod
    async def get_profile_by_address(self, wallet_address: str) -> Optional[Dict]:
        """Get profile associated with wallet address."""
        pass

    @abstractmethod
    async def get_profile_by_handle(self, handle: str) -> Optional[Dict]:
        """Get profile by platform-specific handle."""
        pass

    @abstractmethod
    async def get_publications(
        self, profile_id: str, limit: int = 50
    ) -> List[Dict]:
        """Get publications/posts from a profile."""
        pass


@dataclass
class LensProfile:
    """Lens Protocol profile representation."""

    profile_id: str
    handle: str
    owner_address: str
    name: Optional[str] = None
    bio: Optional[str] = None
    picture_uri: Optional[str] = None
    cover_picture_uri: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    is_default: bool = False


@dataclass
class LensPublication:
    """Lens Protocol publication representation."""

    publication_id: str
    profile_id: str
    content_uri: str
    content: str
    created_at: datetime
    publication_type: str  # POST, COMMENT, MIRROR
    collect_count: int = 0
    mirror_count: int = 0
    comment_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class LensProtocolAdapter(DecentralizedSocialProtocol, SocialMediaAdapter):
    """
    Lens Protocol Adapter

    Lens Protocol is a decentralized social graph built on Polygon.
    Uses GraphQL API for data access.
    """

    LENS_API_URL = "https://api-v2.lens.dev"

    def __init__(self):
        SocialMediaAdapter.__init__(self, SocialPlatform.LENS)
        self._access_token: Optional[str] = None

    async def authenticate(self, access_token: str) -> bool:
        """Authenticate with Lens Protocol."""
        self._access_token = access_token
        self._authenticated = True
        logger.info("Lens Protocol adapter authenticated")
        return True

    async def get_profile_by_address(self, wallet_address: str) -> Optional[Dict]:
        """Get Lens profile by wallet address."""
        logger.info(f"Fetching Lens profile for wallet: {wallet_address}")
        # GraphQL query would be:
        # query { defaultProfile(request: { ethereumAddress: "0x..." }) {...} }
        return None

    async def get_profile_by_handle(self, handle: str) -> Optional[Dict]:
        """Get Lens profile by handle."""
        logger.info(f"Fetching Lens profile: {handle}")
        return None

    async def get_profile(self, user_id: str) -> Optional[SocialProfile]:
        """Get profile in unified format."""
        profile_data = await self.get_profile_by_handle(user_id)
        if not profile_data:
            return SocialProfile(
                platform=self.platform,
                user_id=user_id,
                username=user_id,
                display_name=user_id,
            )

        return SocialProfile(
            platform=self.platform,
            user_id=profile_data.get("id", user_id),
            username=profile_data.get("handle", user_id),
            display_name=profile_data.get("name", user_id),
            bio=profile_data.get("bio"),
            avatar_url=profile_data.get("picture", {}).get("uri"),
            raw_data=profile_data,
        )

    async def get_publications(
        self, profile_id: str, limit: int = 50
    ) -> List[Dict]:
        """Get Lens publications from a profile."""
        logger.info(f"Fetching Lens publications for profile: {profile_id}")
        return []

    async def get_posts(
        self,
        user_id: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Get posts in unified format."""
        publications = await self.get_publications(user_id, limit)
        return [
            SocialPost(
                platform=self.platform,
                post_id=pub.get("id", ""),
                author_id=user_id,
                content=pub.get("content", ""),
                created_at=datetime.fromisoformat(pub["createdAt"])
                if "createdAt" in pub
                else datetime.utcnow(),
                raw_data=pub,
            )
            for pub in publications
        ]

    async def search_posts(
        self,
        query: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Search Lens publications."""
        logger.info(f"Searching Lens publications: {query}")
        return []

    async def get_trending_topics(self, location: Optional[str] = None) -> List[str]:
        """Get trending on Lens Protocol."""
        logger.info("Fetching Lens trending topics")
        return []


@dataclass
class FarcasterProfile:
    """Farcaster profile representation."""

    fid: int  # Farcaster ID
    username: str
    display_name: str
    custody_address: str
    bio: Optional[str] = None
    pfp_url: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0


@dataclass
class FarcasterCast:
    """Farcaster cast (post) representation."""

    hash: str
    fid: int
    text: str
    timestamp: datetime
    parent_hash: Optional[str] = None
    parent_fid: Optional[int] = None
    embeds: List[str] = field(default_factory=list)
    mentions: List[int] = field(default_factory=list)
    reactions_count: int = 0
    recasts_count: int = 0
    replies_count: int = 0


class FarcasterAdapter(DecentralizedSocialProtocol, SocialMediaAdapter):
    """
    Farcaster Protocol Adapter

    Farcaster is a decentralized social network built on Optimism.
    Uses hub API or Neynar API for data access.
    """

    FARCASTER_HUB_URL = "https://hub.farcaster.xyz"
    NEYNAR_API_URL = "https://api.neynar.com"

    def __init__(self, neynar_api_key: Optional[str] = None):
        SocialMediaAdapter.__init__(self, SocialPlatform.FARCASTER)
        self.neynar_api_key = neynar_api_key

    async def authenticate(self, access_token: str) -> bool:
        """Authenticate with Farcaster."""
        self._access_token = access_token
        self._authenticated = True
        logger.info("Farcaster adapter authenticated")
        return True

    async def get_profile_by_address(self, wallet_address: str) -> Optional[Dict]:
        """Get Farcaster profile by custody address."""
        logger.info(f"Fetching Farcaster profile for address: {wallet_address}")
        return None

    async def get_profile_by_handle(self, handle: str) -> Optional[Dict]:
        """Get Farcaster profile by username."""
        logger.info(f"Fetching Farcaster profile: {handle}")
        return None

    async def get_profile_by_fid(self, fid: int) -> Optional[Dict]:
        """Get Farcaster profile by FID."""
        logger.info(f"Fetching Farcaster profile by FID: {fid}")
        return None

    async def get_profile(self, user_id: str) -> Optional[SocialProfile]:
        """Get profile in unified format."""
        profile_data = await self.get_profile_by_handle(user_id)
        if not profile_data:
            return SocialProfile(
                platform=self.platform,
                user_id=user_id,
                username=user_id,
                display_name=user_id,
            )

        return SocialProfile(
            platform=self.platform,
            user_id=str(profile_data.get("fid", user_id)),
            username=profile_data.get("username", user_id),
            display_name=profile_data.get("display_name", user_id),
            bio=profile_data.get("bio"),
            avatar_url=profile_data.get("pfp_url"),
            raw_data=profile_data,
        )

    async def get_publications(
        self, profile_id: str, limit: int = 50
    ) -> List[Dict]:
        """Get Farcaster casts from a profile."""
        logger.info(f"Fetching Farcaster casts for FID: {profile_id}")
        return []

    async def get_casts(
        self,
        fid: int,
        limit: int = 50,
    ) -> List[FarcasterCast]:
        """Get casts from a Farcaster user."""
        logger.info(f"Fetching casts for FID: {fid}")
        return []

    async def get_posts(
        self,
        user_id: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Get posts in unified format."""
        try:
            fid = int(user_id)
            casts = await self.get_casts(fid, limit)
            return [
                SocialPost(
                    platform=self.platform,
                    post_id=cast.hash,
                    author_id=str(cast.fid),
                    content=cast.text,
                    created_at=cast.timestamp,
                    likes_count=cast.reactions_count,
                    reposts_count=cast.recasts_count,
                    replies_count=cast.replies_count,
                )
                for cast in casts
            ]
        except ValueError:
            # user_id is username, not FID
            return []

    async def search_posts(
        self,
        query: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """Search Farcaster casts."""
        logger.info(f"Searching Farcaster casts: {query}")
        return []

    async def get_trending_topics(self, location: Optional[str] = None) -> List[str]:
        """Get trending on Farcaster."""
        logger.info("Fetching Farcaster trending")
        return []

    async def get_channel_casts(
        self, channel_id: str, limit: int = 50
    ) -> List[Dict]:
        """Get casts from a Farcaster channel."""
        logger.info(f"Fetching casts from channel: {channel_id}")
        return []
