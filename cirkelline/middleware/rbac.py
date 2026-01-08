"""
RBAC Permission Enforcement for Cirkelline
===========================================
Implements role-based access control with dependency injection.

Based on RBAC1 (Hierarchical) model with permission inheritance.
Tier hierarchy: Member → Pro → Business → Elite → Family

Usage:
    from cirkelline.middleware.rbac import require_permissions, Permission

    @router.post("/endpoint", dependencies=[Depends(require_permissions([Permission.AGENT_VIDEO]))])
    async def protected_endpoint():
        ...
"""

from enum import Enum
from typing import List, Optional, Set, Dict, Any
from fastapi import Depends, HTTPException, Request
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# PERMISSION DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

class Permission(str, Enum):
    """
    Enumeration of all system permissions.

    Naming convention: resource:action[:scope]
    - resource: What is being accessed (chat, agent, team, etc.)
    - action: What operation is being performed (basic, advanced, use, etc.)
    - scope: Optional qualifier (unlimited, export, etc.)
    """

    # ─────────────────────────────────────────────────────────────────────────
    # CHAT & MESSAGING
    # ─────────────────────────────────────────────────────────────────────────
    CHAT_BASIC = "chat:basic"
    CHAT_ADVANCED = "chat:advanced"
    CHAT_UNLIMITED = "chat:unlimited"

    # ─────────────────────────────────────────────────────────────────────────
    # DOCUMENT MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_EXPORT = "document:export"
    DOCUMENT_UNLIMITED = "document:unlimited"

    # ─────────────────────────────────────────────────────────────────────────
    # AGENT ACCESS (Specialist Agents)
    # ─────────────────────────────────────────────────────────────────────────
    AGENT_AUDIO = "agent:audio"
    AGENT_VIDEO = "agent:video"
    AGENT_IMAGE = "agent:image"
    AGENT_DOCUMENT = "agent:document"
    AGENT_CUSTOM = "agent:custom"

    # ─────────────────────────────────────────────────────────────────────────
    # TEAM ACCESS (Agent Teams)
    # ─────────────────────────────────────────────────────────────────────────
    TEAM_RESEARCH = "team:research"
    TEAM_LEGAL = "team:legal"
    TEAM_CUSTOM = "team:custom"

    # ─────────────────────────────────────────────────────────────────────────
    # SEARCH TOOLS
    # ─────────────────────────────────────────────────────────────────────────
    SEARCH_DUCKDUCKGO = "search:duckduckgo"
    SEARCH_EXA = "search:exa"
    SEARCH_TAVILY = "search:tavily"
    DEEP_RESEARCH = "deep_research:enable"

    # ─────────────────────────────────────────────────────────────────────────
    # INTEGRATIONS
    # ─────────────────────────────────────────────────────────────────────────
    INTEGRATION_GOOGLE = "integration:google"
    INTEGRATION_NOTION = "integration:notion"

    # ─────────────────────────────────────────────────────────────────────────
    # MEMORY & KNOWLEDGE
    # ─────────────────────────────────────────────────────────────────────────
    MEMORY_BASIC = "memory:basic"
    MEMORY_UNLIMITED = "memory:unlimited"
    KNOWLEDGE_UPLOAD = "knowledge:upload"
    KNOWLEDGE_SEARCH = "knowledge:search"

    # ─────────────────────────────────────────────────────────────────────────
    # API ACCESS
    # ─────────────────────────────────────────────────────────────────────────
    API_ACCESS = "api:access"
    API_UNLIMITED = "api:unlimited"

    # ─────────────────────────────────────────────────────────────────────────
    # ADMIN PERMISSIONS
    # ─────────────────────────────────────────────────────────────────────────
    ADMIN_USERS = "admin:users"
    ADMIN_SUBSCRIPTIONS = "admin:subscriptions"
    ADMIN_METRICS = "admin:metrics"
    ADMIN_ACTIVITY = "admin:activity"
    ADMIN_SYSTEM = "admin:system"

    # ─────────────────────────────────────────────────────────────────────────
    # PREMIUM FEATURES
    # ─────────────────────────────────────────────────────────────────────────
    PRIORITY_SUPPORT = "support:priority"
    CUSTOM_INSTRUCTIONS = "custom:instructions"
    DATA_EXPORT = "data:export"


# ═══════════════════════════════════════════════════════════════════════════════
# TIER HIERARCHY
# ═══════════════════════════════════════════════════════════════════════════════

TIER_HIERARCHY: Dict[str, int] = {
    "member": 1,
    "pro": 2,
    "business": 3,
    "elite": 4,
    "family": 5
}

TIER_NAMES: Dict[str, str] = {
    "member": "Member (Free)",
    "pro": "Pro",
    "business": "Business",
    "elite": "Elite",
    "family": "Family"
}


# ═══════════════════════════════════════════════════════════════════════════════
# TIER-TO-PERMISSION MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════════

# Base permissions for each tier (additive - higher tiers inherit from lower)
TIER_PERMISSIONS: Dict[str, Set[Permission]] = {
    # ─────────────────────────────────────────────────────────────────────────
    # MEMBER (Free Tier) - Level 1
    # Basic access to core features
    # ─────────────────────────────────────────────────────────────────────────
    "member": {
        # Chat
        Permission.CHAT_BASIC,

        # Core Specialists (all available)
        Permission.AGENT_AUDIO,
        Permission.AGENT_IMAGE,
        Permission.AGENT_DOCUMENT,

        # Basic Search
        Permission.SEARCH_DUCKDUCKGO,

        # Documents (limited)
        Permission.DOCUMENT_UPLOAD,
        Permission.KNOWLEDGE_UPLOAD,
        Permission.KNOWLEDGE_SEARCH,

        # Memory (limited)
        Permission.MEMORY_BASIC,

        # Google Integration
        Permission.INTEGRATION_GOOGLE,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # PRO - Level 2
    # Power users: Advanced search, Research Team, Video
    # ─────────────────────────────────────────────────────────────────────────
    "pro": {
        # Advanced Chat
        Permission.CHAT_ADVANCED,

        # Video Specialist
        Permission.AGENT_VIDEO,

        # Research Team
        Permission.TEAM_RESEARCH,

        # Advanced Search
        Permission.SEARCH_EXA,
        Permission.DEEP_RESEARCH,

        # Notion Integration
        Permission.INTEGRATION_NOTION,

        # Unlimited Memory
        Permission.MEMORY_UNLIMITED,

        # API Access
        Permission.API_ACCESS,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BUSINESS - Level 3
    # Enterprise: Law Team, Tavily, Priority Support
    # ─────────────────────────────────────────────────────────────────────────
    "business": {
        # Law Team
        Permission.TEAM_LEGAL,

        # Tavily Deep Search
        Permission.SEARCH_TAVILY,

        # Document Export
        Permission.DOCUMENT_EXPORT,
        Permission.DOCUMENT_UNLIMITED,

        # Unlimited Chat
        Permission.CHAT_UNLIMITED,

        # API Unlimited
        Permission.API_UNLIMITED,

        # Priority Support
        Permission.PRIORITY_SUPPORT,

        # Custom Instructions
        Permission.CUSTOM_INSTRUCTIONS,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # ELITE - Level 4
    # Premium: Custom Agents, Data Export, Full Admin
    # ─────────────────────────────────────────────────────────────────────────
    "elite": {
        # Custom Agents
        Permission.AGENT_CUSTOM,
        Permission.TEAM_CUSTOM,

        # Data Export (GDPR)
        Permission.DATA_EXPORT,

        # Document Management
        Permission.DOCUMENT_DELETE,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # FAMILY - Level 5
    # Full Suite: All Elite features + Family sharing
    # (Same as Elite for now, family features can be added)
    # ─────────────────────────────────────────────────────────────────────────
    "family": set(),  # All Elite permissions inherited, family-specific can be added
}

# Admin gets ALL permissions
ADMIN_PERMISSIONS: Set[Permission] = set(Permission)


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT/TEAM PERMISSION MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════════

AGENT_PERMISSIONS: Dict[str, Permission] = {
    "audio-specialist": Permission.AGENT_AUDIO,
    "video-specialist": Permission.AGENT_VIDEO,
    "image-specialist": Permission.AGENT_IMAGE,
    "document-specialist": Permission.AGENT_DOCUMENT,
}

TEAM_PERMISSIONS_MAP: Dict[str, Permission] = {
    "research-team": Permission.TEAM_RESEARCH,
    "law-team": Permission.TEAM_LEGAL,
}

TOOL_PERMISSIONS: Dict[str, Permission] = {
    "DuckDuckGoTools": Permission.SEARCH_DUCKDUCKGO,
    "ExaTools": Permission.SEARCH_EXA,
    "TavilyTools": Permission.SEARCH_TAVILY,
}


# ═══════════════════════════════════════════════════════════════════════════════
# PERMISSION RESOLUTION
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_permissions(tier_slug: str, is_admin: bool = False) -> Set[Permission]:
    """
    Resolve all permissions for a tier including inherited permissions.

    Implements RBAC1 hierarchical model: higher tiers inherit all permissions
    from lower tiers.

    Args:
        tier_slug: User's tier (member, pro, business, elite, family)
        is_admin: Whether user is an admin (gets all permissions)

    Returns:
        Set of all Permission enums the user has access to

    Example:
        >>> permissions = resolve_permissions("pro", is_admin=False)
        >>> Permission.TEAM_RESEARCH in permissions
        True
        >>> Permission.TEAM_LEGAL in permissions
        False
    """
    if is_admin:
        return ADMIN_PERMISSIONS.copy()

    tier_level = TIER_HIERARCHY.get(tier_slug, 1)
    permissions: Set[Permission] = set()

    # Accumulate permissions from all lower tiers (inheritance)
    for tier, level in TIER_HIERARCHY.items():
        if level <= tier_level:
            permissions.update(TIER_PERMISSIONS.get(tier, set()))

    return permissions


def get_tier_for_permission(permission: Permission) -> str:
    """
    Get the minimum tier required for a permission.

    Args:
        permission: The permission to check

    Returns:
        Tier slug (member, pro, business, elite, family)
    """
    for tier in ["member", "pro", "business", "elite", "family"]:
        if permission in TIER_PERMISSIONS.get(tier, set()):
            return tier
    return "elite"  # Default to highest tier for unknown permissions


def has_permission(user_permissions: Set[Permission], required: Permission) -> bool:
    """Check if user has a specific permission."""
    return required in user_permissions


def has_all_permissions(user_permissions: Set[Permission], required: List[Permission]) -> bool:
    """Check if user has all required permissions."""
    return all(p in user_permissions for p in required)


def has_any_permission(user_permissions: Set[Permission], required: List[Permission]) -> bool:
    """Check if user has any of the required permissions."""
    return any(p in user_permissions for p in required)


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI DEPENDENCY INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

class PermissionChecker:
    """
    FastAPI dependency for checking user permissions.

    Usage:
        @router.get("/endpoint", dependencies=[Depends(require_permissions([Permission.AGENT_VIDEO]))])
        async def endpoint():
            ...
    """

    def __init__(self, required_permissions: List[Permission], require_all: bool = True):
        """
        Initialize permission checker.

        Args:
            required_permissions: List of permissions to check
            require_all: If True, user must have ALL permissions. If False, ANY permission.
        """
        self.required_permissions = required_permissions
        self.require_all = require_all

    async def __call__(self, request: Request) -> Dict[str, Any]:
        """
        Verify user has required permissions.

        Raises:
            HTTPException 401: If not authenticated
            HTTPException 403: If missing required permissions

        Returns:
            User context dict with user_id, tier_slug, is_admin, permissions
        """
        # Extract user info from request state (set by JWT middleware)
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )

        # Get tier info from request state or JWT payload
        tier_slug = getattr(request.state, 'tier_slug', 'member')
        is_admin = getattr(request.state, 'is_admin', False)

        # Resolve user's permissions
        user_permissions = resolve_permissions(tier_slug, is_admin)

        # Check permissions
        if self.require_all:
            missing = set(self.required_permissions) - user_permissions
            has_access = len(missing) == 0
        else:
            has_access = has_any_permission(user_permissions, self.required_permissions)
            missing = set(self.required_permissions) if not has_access else set()

        if not has_access:
            missing_perms = [p.value for p in missing]
            min_tier = get_tier_for_permission(list(missing)[0]) if missing else "pro"

            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_permissions",
                    "message": f"This feature requires {TIER_NAMES.get(min_tier, min_tier)} tier or higher",
                    "missing_permissions": missing_perms,
                    "required_tier": min_tier,
                    "current_tier": tier_slug,
                    "upgrade_url": "https://cirkelline.com/pricing"
                }
            )

        # Return user context for downstream use
        return {
            "user_id": user_id,
            "tier_slug": tier_slug,
            "tier_level": TIER_HIERARCHY.get(tier_slug, 1),
            "is_admin": is_admin,
            "permissions": user_permissions
        }


def require_permissions(permissions: List[Permission], require_all: bool = True):
    """
    Create a permission checker dependency.

    Args:
        permissions: List of required permissions
        require_all: If True, all permissions required. If False, any one is sufficient.

    Usage:
        @router.get("/video", dependencies=[Depends(require_permissions([Permission.AGENT_VIDEO]))])
        async def video_endpoint():
            ...
    """
    return PermissionChecker(permissions, require_all)


def require_tier(min_tier: str):
    """
    Require minimum tier level.

    Args:
        min_tier: Minimum tier slug (member, pro, business, elite, family)

    Usage:
        @router.get("/pro-only", dependencies=[Depends(require_tier("pro"))])
        async def pro_feature():
            ...
    """
    async def tier_checker(request: Request) -> Dict[str, Any]:
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        tier_slug = getattr(request.state, 'tier_slug', 'member')
        is_admin = getattr(request.state, 'is_admin', False)

        # Admins bypass tier checks
        if is_admin:
            return {
                "user_id": user_id,
                "tier_slug": tier_slug,
                "tier_level": 99,
                "is_admin": True
            }

        user_level = TIER_HIERARCHY.get(tier_slug, 1)
        required_level = TIER_HIERARCHY.get(min_tier, 1)

        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_tier",
                    "message": f"This feature requires {TIER_NAMES.get(min_tier, min_tier)} tier or higher",
                    "required_tier": min_tier,
                    "current_tier": tier_slug,
                    "upgrade_url": "https://cirkelline.com/pricing"
                }
            )

        return {
            "user_id": user_id,
            "tier_slug": tier_slug,
            "tier_level": user_level,
            "is_admin": False
        }

    return tier_checker


def require_admin():
    """
    Require admin privileges.

    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_admin())])
        async def list_users():
            ...
    """
    async def admin_checker(request: Request) -> Dict[str, Any]:
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        is_admin = getattr(request.state, 'is_admin', False)

        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "admin_required",
                    "message": "Admin privileges required"
                }
            )

        return {
            "user_id": user_id,
            "is_admin": True,
            "permissions": ADMIN_PERMISSIONS
        }

    return admin_checker


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT/TEAM ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════════════════════

async def check_agent_access(
    user_id: str,
    agent_id: str,
    tier_slug: str,
    is_admin: bool = False
) -> Dict[str, Any]:
    """
    Check if user can access specific agent.

    Args:
        user_id: User's UUID
        agent_id: Agent identifier (e.g., "video-specialist")
        tier_slug: User's subscription tier
        is_admin: Whether user is admin

    Returns:
        Dict with 'allowed' boolean and optional 'message' for denial reason
    """
    # Admins have access to all agents
    if is_admin:
        return {"allowed": True}

    # Get required permission for agent
    required_permission = AGENT_PERMISSIONS.get(agent_id)

    # If agent doesn't have specific permission requirement, allow
    if not required_permission:
        return {"allowed": True}

    # Check user's permissions
    user_permissions = resolve_permissions(tier_slug, is_admin)

    if required_permission in user_permissions:
        return {"allowed": True}

    # Access denied - return helpful message
    min_tier = get_tier_for_permission(required_permission)
    return {
        "allowed": False,
        "message": f"The {agent_id.replace('-', ' ').title()} requires {TIER_NAMES.get(min_tier, min_tier)} tier or higher.",
        "required_tier": min_tier,
        "current_tier": tier_slug,
        "upgrade_url": "https://cirkelline.com/pricing"
    }


async def check_team_access(
    user_id: str,
    team_id: str,
    tier_slug: str,
    is_admin: bool = False
) -> Dict[str, Any]:
    """
    Check if user can access specific team.

    Args:
        user_id: User's UUID
        team_id: Team identifier (e.g., "research-team", "law-team")
        tier_slug: User's subscription tier
        is_admin: Whether user is admin

    Returns:
        Dict with 'allowed' boolean and optional 'message' for denial reason
    """
    # Admins have access to all teams
    if is_admin:
        return {"allowed": True}

    # Get required permission for team
    required_permission = TEAM_PERMISSIONS_MAP.get(team_id)

    # If team doesn't have specific permission requirement, allow
    if not required_permission:
        return {"allowed": True}

    # Check user's permissions
    user_permissions = resolve_permissions(tier_slug, is_admin)

    if required_permission in user_permissions:
        return {"allowed": True}

    # Access denied - return helpful message
    min_tier = get_tier_for_permission(required_permission)
    return {
        "allowed": False,
        "message": f"The {team_id.replace('-', ' ').title()} requires {TIER_NAMES.get(min_tier, min_tier)} tier or higher.",
        "required_tier": min_tier,
        "current_tier": tier_slug,
        "upgrade_url": "https://cirkelline.com/pricing"
    }


async def check_tool_access(
    tool_name: str,
    tier_slug: str,
    is_admin: bool = False
) -> bool:
    """
    Check if user can access specific search tool.

    Args:
        tool_name: Tool class name (e.g., "ExaTools", "TavilyTools")
        tier_slug: User's subscription tier
        is_admin: Whether user is admin

    Returns:
        True if access granted, False otherwise
    """
    if is_admin:
        return True

    required_permission = TOOL_PERMISSIONS.get(tool_name)

    if not required_permission:
        return True  # No specific permission required

    user_permissions = resolve_permissions(tier_slug, is_admin)
    return required_permission in user_permissions


# ═══════════════════════════════════════════════════════════════════════════════
# DYNAMIC MEMBER/TOOL BUILDERS FOR CIRKELLINE TEAM
# ═══════════════════════════════════════════════════════════════════════════════

def get_available_agents_for_tier(tier_slug: str, is_admin: bool = False) -> List[str]:
    """
    Get list of available agent IDs for a tier.

    Args:
        tier_slug: User's subscription tier
        is_admin: Whether user is admin

    Returns:
        List of agent IDs user can access
    """
    if is_admin:
        return list(AGENT_PERMISSIONS.keys())

    user_permissions = resolve_permissions(tier_slug, is_admin)
    available = []

    for agent_id, required_permission in AGENT_PERMISSIONS.items():
        if required_permission in user_permissions:
            available.append(agent_id)

    return available


def get_available_teams_for_tier(tier_slug: str, is_admin: bool = False) -> List[str]:
    """
    Get list of available team IDs for a tier.

    Args:
        tier_slug: User's subscription tier
        is_admin: Whether user is admin

    Returns:
        List of team IDs user can access
    """
    if is_admin:
        return list(TEAM_PERMISSIONS_MAP.keys())

    user_permissions = resolve_permissions(tier_slug, is_admin)
    available = []

    for team_id, required_permission in TEAM_PERMISSIONS_MAP.items():
        if required_permission in user_permissions:
            available.append(team_id)

    return available


def get_available_tools_for_tier(tier_slug: str, is_admin: bool = False) -> List[str]:
    """
    Get list of available tool names for a tier.

    Args:
        tier_slug: User's subscription tier
        is_admin: Whether user is admin

    Returns:
        List of tool names user can access
    """
    if is_admin:
        return list(TOOL_PERMISSIONS.keys())

    user_permissions = resolve_permissions(tier_slug, is_admin)
    available = []

    for tool_name, required_permission in TOOL_PERMISSIONS.items():
        if required_permission in user_permissions:
            available.append(tool_name)

    return available


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_tier_features_summary(tier_slug: str) -> Dict[str, Any]:
    """
    Get a summary of features available for a tier.

    Useful for displaying to users what they have access to.

    Args:
        tier_slug: User's subscription tier

    Returns:
        Dict with categorized features
    """
    permissions = resolve_permissions(tier_slug, is_admin=False)

    return {
        "tier": tier_slug,
        "tier_name": TIER_NAMES.get(tier_slug, tier_slug),
        "tier_level": TIER_HIERARCHY.get(tier_slug, 1),
        "agents": get_available_agents_for_tier(tier_slug),
        "teams": get_available_teams_for_tier(tier_slug),
        "tools": get_available_tools_for_tier(tier_slug),
        "features": {
            "chat_advanced": Permission.CHAT_ADVANCED in permissions,
            "deep_research": Permission.DEEP_RESEARCH in permissions,
            "notion_integration": Permission.INTEGRATION_NOTION in permissions,
            "api_access": Permission.API_ACCESS in permissions,
            "priority_support": Permission.PRIORITY_SUPPORT in permissions,
            "data_export": Permission.DATA_EXPORT in permissions,
        }
    }


def format_upgrade_message(current_tier: str, required_permission: Permission) -> str:
    """
    Format a user-friendly upgrade message.

    Args:
        current_tier: User's current tier
        required_permission: The permission they need

    Returns:
        Formatted message string
    """
    required_tier = get_tier_for_permission(required_permission)
    required_name = TIER_NAMES.get(required_tier, required_tier)
    current_name = TIER_NAMES.get(current_tier, current_tier)

    return (
        f"This feature requires {required_name} tier. "
        f"You're currently on {current_name}. "
        f"Upgrade at cirkelline.com/pricing to unlock this feature!"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Enums
    'Permission',

    # Constants
    'TIER_HIERARCHY',
    'TIER_NAMES',
    'TIER_PERMISSIONS',
    'ADMIN_PERMISSIONS',
    'AGENT_PERMISSIONS',
    'TEAM_PERMISSIONS_MAP',
    'TOOL_PERMISSIONS',

    # Resolution functions
    'resolve_permissions',
    'get_tier_for_permission',
    'has_permission',
    'has_all_permissions',
    'has_any_permission',

    # FastAPI dependencies
    'require_permissions',
    'require_tier',
    'require_admin',
    'PermissionChecker',

    # Access checks
    'check_agent_access',
    'check_team_access',
    'check_tool_access',

    # Builders
    'get_available_agents_for_tier',
    'get_available_teams_for_tier',
    'get_available_tools_for_tier',

    # Utilities
    'get_tier_features_summary',
    'format_upgrade_message',
]


logger.info("RBAC module loaded with %d permissions, %d tiers", len(Permission), len(TIER_HIERARCHY))
