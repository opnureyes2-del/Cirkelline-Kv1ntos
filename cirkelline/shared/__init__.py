"""
Cirkelline Shared Utilities
============================
Shared utility functions used across multiple endpoint routers.

UPDATED: 2026-01-09 - P2-INT-2 Gateway Authentication Integration
"""

# Local JWT utilities (for backwards compatibility)
from cirkelline.shared.jwt_utils import (
    decode_jwt_token,
    generate_jwt_token,
    load_admin_profile,
    load_tier_info
)

# CKC Gateway Authentication (P2-INT-2)
from cirkelline.shared.gateway_client import (
    GatewayClient,
    TokenValidationResult,
    TokenExchangeResult,
    GatewayAuthDependency,
    LocalTokenValidator,
    CustomerTier,
)

from cirkelline.shared.gateway_auth import (
    gateway_auth,
    optional_gateway_auth,
    require_tier,
    require_feature,
    require_platform,
    validate_token_direct,
    exchange_token,
    get_user_info,
    get_gateway_client,
    is_gateway_configured,
)

from cirkelline.shared.database import get_db_session, get_db_engine

__all__ = [
    # Local JWT (backwards compatibility)
    'decode_jwt_token',
    'generate_jwt_token',
    'load_admin_profile',
    'load_tier_info',
    # Database
    'get_db_session',
    'get_db_engine',
    # Gateway Client SDK
    'GatewayClient',
    'TokenValidationResult',
    'TokenExchangeResult',
    'GatewayAuthDependency',
    'LocalTokenValidator',
    'CustomerTier',
    # Gateway Auth Dependencies
    'gateway_auth',
    'optional_gateway_auth',
    'require_tier',
    'require_feature',
    'require_platform',
    'validate_token_direct',
    'exchange_token',
    'get_user_info',
    'get_gateway_client',
    'is_gateway_configured',
]
