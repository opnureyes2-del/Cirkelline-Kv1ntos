"""
CIRKELLINE WEB3 SOCIAL MEDIA INTEGRATION MODULE
================================================

MP-001: Social Media API Integration with OAuth2 Support

This module provides a unified adapter for social media platform APIs,
enabling backwards engineering research on decentralized social protocols.

Supported Platforms:
- Twitter/X API v2
- Mastodon API
- Lens Protocol
- Farcaster

Status: IMPLEMENTED (awaiting API keys for production deployment)
"""

from .adapter import (
    SocialMediaAdapter,
    SocialPlatform,
    SocialPost,
    SocialProfile,
    OAuthConfig,
    get_social_adapter,
)
from .oauth import OAuthManager, OAuthTokens
from .protocols import (
    DecentralizedSocialProtocol,
    LensProtocolAdapter,
    FarcasterAdapter,
)

__all__ = [
    "SocialMediaAdapter",
    "SocialPlatform",
    "SocialPost",
    "SocialProfile",
    "OAuthConfig",
    "OAuthManager",
    "OAuthTokens",
    "DecentralizedSocialProtocol",
    "LensProtocolAdapter",
    "FarcasterAdapter",
    "get_social_adapter",
]
