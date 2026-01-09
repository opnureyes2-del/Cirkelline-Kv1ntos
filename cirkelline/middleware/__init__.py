"""
Cirkelline Middleware Package
=============================
FastAPI middleware components for:
- Activity logging
- Session management
- RBAC tier enforcement
- Compliance audit trails
- CKC Gateway Authentication (P2-INT-2)

UPDATED: 2026-01-09 - Added Gateway Auth Middleware
"""

from cirkelline.middleware.middleware import (
    # Activity logging
    log_activity,

    # Middleware classes
    AnonymousUserMiddleware,
    SessionLoggingMiddleware,
    SessionsDateFilterMiddleware,
    RBACGatewayMiddleware,
    AuditTrailMiddleware,
    RateLimitMiddleware,
)

# CKC Gateway Authentication Middleware (P2-INT-2)
from cirkelline.middleware.gateway_middleware import (
    GatewayAuthMiddleware,
    StrictGatewayAuthMiddleware,
)

from cirkelline.middleware.rbac import (
    # Permission enum
    Permission,

    # Constants
    TIER_HIERARCHY,
    TIER_NAMES,
    TIER_PERMISSIONS,
    ADMIN_PERMISSIONS,
    AGENT_PERMISSIONS,
    TEAM_PERMISSIONS_MAP,
    TOOL_PERMISSIONS,

    # Permission resolution
    resolve_permissions,
    get_tier_for_permission,
    has_permission,
    has_all_permissions,
    has_any_permission,

    # FastAPI dependencies
    require_permissions,
    require_tier,
    require_admin,
    PermissionChecker,

    # Access checks
    check_agent_access,
    check_team_access,
    check_tool_access,

    # Resource builders
    get_available_agents_for_tier,
    get_available_teams_for_tier,
    get_available_tools_for_tier,

    # Utilities
    get_tier_features_summary,
    format_upgrade_message,
)

__all__ = [
    # Activity logging
    'log_activity',

    # Middleware classes
    'AnonymousUserMiddleware',
    'SessionLoggingMiddleware',
    'SessionsDateFilterMiddleware',
    'RBACGatewayMiddleware',
    'AuditTrailMiddleware',
    'RateLimitMiddleware',

    # Gateway Auth Middleware (P2-INT-2)
    'GatewayAuthMiddleware',
    'StrictGatewayAuthMiddleware',

    # RBAC - Permissions
    'Permission',
    'TIER_HIERARCHY',
    'TIER_NAMES',
    'TIER_PERMISSIONS',
    'ADMIN_PERMISSIONS',
    'AGENT_PERMISSIONS',
    'TEAM_PERMISSIONS_MAP',
    'TOOL_PERMISSIONS',

    # RBAC - Resolution
    'resolve_permissions',
    'get_tier_for_permission',
    'has_permission',
    'has_all_permissions',
    'has_any_permission',

    # RBAC - FastAPI
    'require_permissions',
    'require_tier',
    'require_admin',
    'PermissionChecker',

    # RBAC - Access checks
    'check_agent_access',
    'check_team_access',
    'check_tool_access',

    # RBAC - Builders
    'get_available_agents_for_tier',
    'get_available_teams_for_tier',
    'get_available_tools_for_tier',

    # RBAC - Utilities
    'get_tier_features_summary',
    'format_upgrade_message',
]
