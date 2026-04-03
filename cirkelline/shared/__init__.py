"""
Cirkelline Shared Utilities
============================
Shared utility functions used across multiple endpoint routers.

UPDATED: 2026-01-09 - P2-INT-2 Gateway Authentication Integration
"""

# Local JWT utilities (for backwards compatibility)
from cirkelline.shared.database import get_db_engine, get_db_session
from cirkelline.shared.gateway_auth import (
    exchange_token,
    gateway_auth,
    get_gateway_client,
    get_user_info,
    is_gateway_configured,
    optional_gateway_auth,
    require_feature,
    require_platform,
    require_tier,
    validate_token_direct,
)

# CKC Gateway Authentication (P2-INT-2)
from cirkelline.shared.gateway_client import (
    CustomerTier,
    GatewayAuthDependency,
    GatewayClient,
    LocalTokenValidator,
    TokenExchangeResult,
    TokenValidationResult,
)
from cirkelline.shared.jwt_utils import (
    decode_jwt_token,
    generate_jwt_token,
    load_admin_profile,
    load_tier_info,
)

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
