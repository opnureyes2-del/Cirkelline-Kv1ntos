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

# CKC Gateway Authentication Middleware (P2-INT-2)
from cirkelline.middleware.gateway_middleware import (
    GatewayAuthMiddleware,
    StrictGatewayAuthMiddleware,
)
from cirkelline.middleware.middleware import (
    # Middleware classes
    AnonymousUserMiddleware,
    AuditTrailMiddleware,
    RateLimitMiddleware,
    RBACGatewayMiddleware,
    SessionLoggingMiddleware,
    SessionsDateFilterMiddleware,
    # Activity logging
    log_activity,
)
from cirkelline.middleware.rbac import (
    ADMIN_PERMISSIONS,
    AGENT_PERMISSIONS,
    TEAM_PERMISSIONS_MAP,
    # Constants
    TIER_HIERARCHY,
    TIER_NAMES,
    TIER_PERMISSIONS,
    TOOL_PERMISSIONS,
    # Permission enum
    Permission,
    PermissionChecker,
    # Access checks
    check_agent_access,
    check_team_access,
    check_tool_access,
    format_upgrade_message,
    # Resource builders
    get_available_agents_for_tier,
    get_available_teams_for_tier,
    get_available_tools_for_tier,
    # Utilities
    get_tier_features_summary,
    get_tier_for_permission,
    has_all_permissions,
    has_any_permission,
    has_permission,
    require_admin,
    # FastAPI dependencies
    require_permissions,
    require_tier,
    # Permission resolution
    resolve_permissions,
)

__all__ = [
    # Activity logging
    "log_activity",
    # Middleware classes
    "AnonymousUserMiddleware",
    "SessionLoggingMiddleware",
    "SessionsDateFilterMiddleware",
    "RBACGatewayMiddleware",
    "AuditTrailMiddleware",
    "RateLimitMiddleware",
    # Gateway Auth Middleware (P2-INT-2)
    "GatewayAuthMiddleware",
    "StrictGatewayAuthMiddleware",
    # RBAC - Permissions
    "Permission",
    "TIER_HIERARCHY",
    "TIER_NAMES",
    "TIER_PERMISSIONS",
    "ADMIN_PERMISSIONS",
    "AGENT_PERMISSIONS",
    "TEAM_PERMISSIONS_MAP",
    "TOOL_PERMISSIONS",
    # RBAC - Resolution
    "resolve_permissions",
    "get_tier_for_permission",
    "has_permission",
    "has_all_permissions",
    "has_any_permission",
    # RBAC - FastAPI
    "require_permissions",
    "require_tier",
    "require_admin",
    "PermissionChecker",
    # RBAC - Access checks
    "check_agent_access",
    "check_team_access",
    "check_tool_access",
    # RBAC - Builders
    "get_available_agents_for_tier",
    "get_available_teams_for_tier",
    "get_available_tools_for_tier",
    # RBAC - Utilities
    "get_tier_features_summary",
    "format_upgrade_message",
]
