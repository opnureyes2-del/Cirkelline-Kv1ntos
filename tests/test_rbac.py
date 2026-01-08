"""
RBAC System Tests for Cirkelline
================================
Tests for role-based access control with tier inheritance.

Test Coverage:
- Permission Resolution (RBAC1 hierarchical model)
- Tier Hierarchy and Inheritance
- Agent/Team/Tool Access Control
- FastAPI Dependency Injection
- Admin Override Behavior
- Edge Cases
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from fastapi import HTTPException, Request

from cirkelline.middleware.rbac import (
    # Enums
    Permission,
    # Constants
    TIER_HIERARCHY,
    TIER_NAMES,
    TIER_PERMISSIONS,
    ADMIN_PERMISSIONS,
    AGENT_PERMISSIONS,
    TEAM_PERMISSIONS_MAP,
    TOOL_PERMISSIONS,
    # Resolution functions
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
    # Builders
    get_available_agents_for_tier,
    get_available_teams_for_tier,
    get_available_tools_for_tier,
    # Utilities
    get_tier_features_summary,
    format_upgrade_message,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TIER HIERARCHY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestTierHierarchy:
    """Tests for tier hierarchy definitions."""

    def test_all_tiers_defined(self):
        """All expected tiers exist."""
        expected_tiers = ["member", "pro", "business", "elite", "family"]
        for tier in expected_tiers:
            assert tier in TIER_HIERARCHY
            assert tier in TIER_NAMES
            assert tier in TIER_PERMISSIONS

    def test_tier_levels_ascending(self):
        """Tier levels are in correct order (member=1 to family=5)."""
        assert TIER_HIERARCHY["member"] == 1
        assert TIER_HIERARCHY["pro"] == 2
        assert TIER_HIERARCHY["business"] == 3
        assert TIER_HIERARCHY["elite"] == 4
        assert TIER_HIERARCHY["family"] == 5

    def test_tier_names_are_strings(self):
        """All tier names are non-empty strings."""
        for tier, name in TIER_NAMES.items():
            assert isinstance(name, str)
            assert len(name) > 0

    def test_tier_permissions_are_sets(self):
        """All tier permission mappings are sets of Permission enums."""
        for tier, permissions in TIER_PERMISSIONS.items():
            assert isinstance(permissions, set), f"Tier {tier} has invalid permission type: {type(permissions)}"
            for perm in permissions:
                assert isinstance(perm, Permission)


# ═══════════════════════════════════════════════════════════════════════════════
# PERMISSION RESOLUTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPermissionResolution:
    """Tests for RBAC1 hierarchical permission resolution."""

    def test_member_has_basic_permissions(self):
        """Member tier has basic permissions."""
        perms = resolve_permissions("member")

        # Member should have
        assert Permission.CHAT_BASIC in perms
        assert Permission.AGENT_AUDIO in perms
        assert Permission.AGENT_IMAGE in perms
        assert Permission.AGENT_DOCUMENT in perms
        assert Permission.SEARCH_DUCKDUCKGO in perms

        # Member should NOT have
        assert Permission.AGENT_VIDEO not in perms
        assert Permission.TEAM_RESEARCH not in perms
        assert Permission.TEAM_LEGAL not in perms

    def test_pro_inherits_from_member(self):
        """Pro tier inherits all member permissions plus pro-specific."""
        pro_perms = resolve_permissions("pro")
        member_perms = resolve_permissions("member")

        # Pro should have all member permissions
        for perm in member_perms:
            assert perm in pro_perms, f"Pro missing inherited permission: {perm}"

        # Pro-specific
        assert Permission.AGENT_VIDEO in pro_perms
        assert Permission.TEAM_RESEARCH in pro_perms
        assert Permission.SEARCH_EXA in pro_perms
        assert Permission.DEEP_RESEARCH in pro_perms

        # Pro should NOT have
        assert Permission.TEAM_LEGAL not in pro_perms

    def test_business_inherits_from_pro(self):
        """Business tier inherits from pro."""
        business_perms = resolve_permissions("business")
        pro_perms = resolve_permissions("pro")

        for perm in pro_perms:
            assert perm in business_perms, f"Business missing inherited permission: {perm}"

        # Business-specific
        assert Permission.TEAM_LEGAL in business_perms
        assert Permission.SEARCH_TAVILY in business_perms
        assert Permission.PRIORITY_SUPPORT in business_perms

    def test_elite_inherits_from_business(self):
        """Elite tier inherits from business."""
        elite_perms = resolve_permissions("elite")
        business_perms = resolve_permissions("business")

        for perm in business_perms:
            assert perm in elite_perms, f"Elite missing inherited permission: {perm}"

        # Elite-specific
        assert Permission.AGENT_CUSTOM in elite_perms
        assert Permission.TEAM_CUSTOM in elite_perms
        assert Permission.DATA_EXPORT in elite_perms

    def test_family_inherits_from_elite(self):
        """Family tier inherits from elite."""
        family_perms = resolve_permissions("family")
        elite_perms = resolve_permissions("elite")

        for perm in elite_perms:
            assert perm in family_perms, f"Family missing inherited permission: {perm}"

    def test_admin_has_all_permissions(self):
        """Admin flag grants all permissions regardless of tier."""
        admin_perms = resolve_permissions("member", is_admin=True)

        # Admin should have every permission in the enum
        for perm in Permission:
            assert perm in admin_perms, f"Admin missing permission: {perm}"

    def test_unknown_tier_defaults_to_member(self):
        """Unknown tier slug defaults to member permissions."""
        unknown_perms = resolve_permissions("unknown_tier")
        member_perms = resolve_permissions("member")

        assert unknown_perms == member_perms

    def test_permission_count_increases_with_tier(self):
        """Higher tiers have more permissions."""
        member_count = len(resolve_permissions("member"))
        pro_count = len(resolve_permissions("pro"))
        business_count = len(resolve_permissions("business"))
        elite_count = len(resolve_permissions("elite"))

        assert pro_count > member_count
        assert business_count > pro_count
        assert elite_count >= business_count  # >= because family may not add new


# ═══════════════════════════════════════════════════════════════════════════════
# PERMISSION HELPER FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPermissionHelpers:
    """Tests for permission helper functions."""

    def test_get_tier_for_permission_basic(self):
        """get_tier_for_permission returns correct minimum tier."""
        # Member-level
        assert get_tier_for_permission(Permission.CHAT_BASIC) == "member"
        assert get_tier_for_permission(Permission.AGENT_AUDIO) == "member"

        # Pro-level
        assert get_tier_for_permission(Permission.AGENT_VIDEO) == "pro"
        assert get_tier_for_permission(Permission.TEAM_RESEARCH) == "pro"

        # Business-level
        assert get_tier_for_permission(Permission.TEAM_LEGAL) == "business"
        assert get_tier_for_permission(Permission.SEARCH_TAVILY) == "business"

        # Elite-level
        assert get_tier_for_permission(Permission.AGENT_CUSTOM) == "elite"

    def test_has_permission(self):
        """has_permission correctly checks single permission."""
        member_perms = resolve_permissions("member")

        assert has_permission(member_perms, Permission.CHAT_BASIC)
        assert not has_permission(member_perms, Permission.AGENT_VIDEO)

    def test_has_all_permissions(self):
        """has_all_permissions requires ALL permissions."""
        pro_perms = resolve_permissions("pro")

        # Pro has both
        assert has_all_permissions(pro_perms, [Permission.AGENT_AUDIO, Permission.AGENT_VIDEO])

        # Pro doesn't have TEAM_LEGAL
        assert not has_all_permissions(pro_perms, [Permission.AGENT_VIDEO, Permission.TEAM_LEGAL])

    def test_has_any_permission(self):
        """has_any_permission requires ANY one permission."""
        member_perms = resolve_permissions("member")

        # Member has AGENT_AUDIO but not AGENT_VIDEO
        assert has_any_permission(member_perms, [Permission.AGENT_AUDIO, Permission.AGENT_VIDEO])

        # Member has neither AGENT_VIDEO nor TEAM_LEGAL
        assert not has_any_permission(member_perms, [Permission.AGENT_VIDEO, Permission.TEAM_LEGAL])


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT ACCESS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentAccess:
    """Tests for agent-level access control."""

    @pytest.mark.asyncio
    async def test_member_can_access_audio_specialist(self):
        """Member can access audio specialist."""
        result = await check_agent_access("user-123", "audio-specialist", "member")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_member_cannot_access_video_specialist(self):
        """Member cannot access video specialist."""
        result = await check_agent_access("user-123", "video-specialist", "member")
        assert result["allowed"] is False
        assert "required_tier" in result
        assert result["required_tier"] == "pro"

    @pytest.mark.asyncio
    async def test_pro_can_access_video_specialist(self):
        """Pro can access video specialist."""
        result = await check_agent_access("user-123", "video-specialist", "pro")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_admin_can_access_any_agent(self):
        """Admin bypasses all agent restrictions."""
        result = await check_agent_access("admin-123", "video-specialist", "member", is_admin=True)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_unknown_agent_allowed_by_default(self):
        """Unknown agents (no permission mapping) are allowed by default."""
        result = await check_agent_access("user-123", "unknown-agent", "member")
        assert result["allowed"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# TEAM ACCESS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestTeamAccess:
    """Tests for team-level access control."""

    @pytest.mark.asyncio
    async def test_member_cannot_access_research_team(self):
        """Member cannot access research team."""
        result = await check_team_access("user-123", "research-team", "member")
        assert result["allowed"] is False
        assert result["required_tier"] == "pro"

    @pytest.mark.asyncio
    async def test_pro_can_access_research_team(self):
        """Pro can access research team."""
        result = await check_team_access("user-123", "research-team", "pro")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_pro_cannot_access_law_team(self):
        """Pro cannot access law team."""
        result = await check_team_access("user-123", "law-team", "pro")
        assert result["allowed"] is False
        assert result["required_tier"] == "business"

    @pytest.mark.asyncio
    async def test_business_can_access_law_team(self):
        """Business can access law team."""
        result = await check_team_access("user-123", "law-team", "business")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_admin_can_access_any_team(self):
        """Admin bypasses all team restrictions."""
        result = await check_team_access("admin-123", "law-team", "member", is_admin=True)
        assert result["allowed"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL ACCESS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolAccess:
    """Tests for search tool access control."""

    @pytest.mark.asyncio
    async def test_member_can_use_duckduckgo(self):
        """Member can use DuckDuckGo tools."""
        result = await check_tool_access("DuckDuckGoTools", "member")
        assert result is True

    @pytest.mark.asyncio
    async def test_member_cannot_use_exa(self):
        """Member cannot use Exa tools."""
        result = await check_tool_access("ExaTools", "member")
        assert result is False

    @pytest.mark.asyncio
    async def test_pro_can_use_exa(self):
        """Pro can use Exa tools."""
        result = await check_tool_access("ExaTools", "pro")
        assert result is True

    @pytest.mark.asyncio
    async def test_business_can_use_tavily(self):
        """Business can use Tavily tools."""
        result = await check_tool_access("TavilyTools", "business")
        assert result is True

    @pytest.mark.asyncio
    async def test_admin_can_use_all_tools(self):
        """Admin can use all tools."""
        for tool_name in TOOL_PERMISSIONS.keys():
            result = await check_tool_access(tool_name, "member", is_admin=True)
            assert result is True


# ═══════════════════════════════════════════════════════════════════════════════
# AVAILABLE RESOURCES BUILDER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestResourceBuilders:
    """Tests for get_available_* functions."""

    def test_member_available_agents(self):
        """Member gets correct agent list."""
        agents = get_available_agents_for_tier("member")

        assert "audio-specialist" in agents
        assert "image-specialist" in agents
        assert "document-specialist" in agents
        assert "video-specialist" not in agents

    def test_pro_available_agents(self):
        """Pro gets additional agents."""
        agents = get_available_agents_for_tier("pro")

        assert "video-specialist" in agents
        assert "audio-specialist" in agents  # inherited

    def test_member_available_teams(self):
        """Member gets no teams."""
        teams = get_available_teams_for_tier("member")
        assert len(teams) == 0

    def test_pro_available_teams(self):
        """Pro gets research team."""
        teams = get_available_teams_for_tier("pro")

        assert "research-team" in teams
        assert "law-team" not in teams

    def test_business_available_teams(self):
        """Business gets all teams."""
        teams = get_available_teams_for_tier("business")

        assert "research-team" in teams
        assert "law-team" in teams

    def test_member_available_tools(self):
        """Member gets DuckDuckGo only."""
        tools = get_available_tools_for_tier("member")

        assert "DuckDuckGoTools" in tools
        assert "ExaTools" not in tools
        assert "TavilyTools" not in tools

    def test_admin_gets_all_resources(self):
        """Admin gets all agents, teams, and tools."""
        agents = get_available_agents_for_tier("member", is_admin=True)
        teams = get_available_teams_for_tier("member", is_admin=True)
        tools = get_available_tools_for_tier("member", is_admin=True)

        # Admin should get everything
        assert len(agents) == len(AGENT_PERMISSIONS)
        assert len(teams) == len(TEAM_PERMISSIONS_MAP)
        assert len(tools) == len(TOOL_PERMISSIONS)


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI DEPENDENCY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFastAPIDependencies:
    """Tests for FastAPI dependency injection."""

    def _create_mock_request(self, user_id=None, tier_slug="member", is_admin=False):
        """Create a mock FastAPI request with state."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = user_id
        request.state.tier_slug = tier_slug
        request.state.is_admin = is_admin
        return request

    @pytest.mark.asyncio
    async def test_permission_checker_allows_authorized_user(self):
        """PermissionChecker allows user with required permission."""
        request = self._create_mock_request(user_id="user-123", tier_slug="pro")
        checker = PermissionChecker([Permission.AGENT_VIDEO], require_all=True)

        result = await checker(request)

        assert result["user_id"] == "user-123"
        assert result["tier_slug"] == "pro"
        assert Permission.AGENT_VIDEO in result["permissions"]

    @pytest.mark.asyncio
    async def test_permission_checker_denies_unauthorized_user(self):
        """PermissionChecker raises 403 for missing permissions."""
        request = self._create_mock_request(user_id="user-123", tier_slug="member")
        checker = PermissionChecker([Permission.AGENT_VIDEO], require_all=True)

        with pytest.raises(HTTPException) as exc_info:
            await checker(request)

        assert exc_info.value.status_code == 403
        assert "insufficient_permissions" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_permission_checker_requires_auth(self):
        """PermissionChecker raises 401 for unauthenticated user."""
        request = self._create_mock_request(user_id=None)
        checker = PermissionChecker([Permission.CHAT_BASIC], require_all=True)

        with pytest.raises(HTTPException) as exc_info:
            await checker(request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_any_permission(self):
        """require_all=False allows user with ANY of the permissions."""
        request = self._create_mock_request(user_id="user-123", tier_slug="pro")
        checker = PermissionChecker(
            [Permission.TEAM_LEGAL, Permission.TEAM_RESEARCH],  # Pro has TEAM_RESEARCH only
            require_all=False
        )

        result = await checker(request)
        assert result["user_id"] == "user-123"

    @pytest.mark.asyncio
    async def test_require_tier_allows_correct_tier(self):
        """require_tier allows user at or above required tier."""
        request = self._create_mock_request(user_id="user-123", tier_slug="business")
        tier_checker = require_tier("pro")

        result = await tier_checker(request)
        assert result["user_id"] == "user-123"
        assert result["tier_level"] == 3  # business = 3

    @pytest.mark.asyncio
    async def test_require_tier_denies_lower_tier(self):
        """require_tier raises 403 for lower tier."""
        request = self._create_mock_request(user_id="user-123", tier_slug="member")
        tier_checker = require_tier("pro")

        with pytest.raises(HTTPException) as exc_info:
            await tier_checker(request)

        assert exc_info.value.status_code == 403
        assert "insufficient_tier" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_admin_allows_admin(self):
        """require_admin allows admin users."""
        request = self._create_mock_request(user_id="admin-123", tier_slug="member", is_admin=True)
        admin_checker = require_admin()

        result = await admin_checker(request)
        assert result["is_admin"] is True

    @pytest.mark.asyncio
    async def test_require_admin_denies_non_admin(self):
        """require_admin raises 403 for non-admin."""
        request = self._create_mock_request(user_id="user-123", tier_slug="elite", is_admin=False)
        admin_checker = require_admin()

        with pytest.raises(HTTPException) as exc_info:
            await admin_checker(request)

        assert exc_info.value.status_code == 403
        assert "admin_required" in str(exc_info.value.detail)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_get_tier_features_summary(self):
        """get_tier_features_summary returns correct structure."""
        summary = get_tier_features_summary("pro")

        assert summary["tier"] == "pro"
        assert summary["tier_name"] == "Pro"
        assert summary["tier_level"] == 2
        assert isinstance(summary["agents"], list)
        assert isinstance(summary["teams"], list)
        assert isinstance(summary["tools"], list)
        assert isinstance(summary["features"], dict)

        # Pro should have deep_research
        assert summary["features"]["deep_research"] is True

    def test_format_upgrade_message(self):
        """format_upgrade_message creates readable message."""
        msg = format_upgrade_message("member", Permission.AGENT_VIDEO)

        assert "Pro" in msg  # Required tier
        assert "Member" in msg  # Current tier
        assert "cirkelline.com/pricing" in msg

    def test_tier_features_summary_for_all_tiers(self):
        """All tiers produce valid summaries."""
        for tier in TIER_HIERARCHY.keys():
            summary = get_tier_features_summary(tier)

            assert summary["tier"] == tier
            assert "tier_name" in summary
            assert "agents" in summary
            assert "teams" in summary
            assert "tools" in summary


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_permission_list(self):
        """Empty permission list in has_all_permissions returns True."""
        perms = resolve_permissions("member")
        assert has_all_permissions(perms, [])

    def test_empty_permission_list_has_any(self):
        """Empty permission list in has_any_permission returns False."""
        perms = resolve_permissions("member")
        assert not has_any_permission(perms, [])

    def test_admin_permissions_is_complete_set(self):
        """ADMIN_PERMISSIONS contains all Permission enum values."""
        assert ADMIN_PERMISSIONS == set(Permission)

    def test_all_permission_values_unique(self):
        """All permission values are unique strings."""
        values = [p.value for p in Permission]
        assert len(values) == len(set(values))

    def test_permission_naming_convention(self):
        """All permissions follow resource:action naming."""
        for perm in Permission:
            parts = perm.value.split(":")
            assert len(parts) >= 2, f"Permission {perm.value} doesn't follow resource:action pattern"

    @pytest.mark.asyncio
    async def test_case_sensitivity_tier_slug(self):
        """Tier slug is case-sensitive (lowercase expected)."""
        # Uppercase should default to member (unknown tier)
        perms = resolve_permissions("PRO")
        member_perms = resolve_permissions("member")

        assert perms == member_perms  # PRO is unknown, defaults to member

    def test_permission_checker_factory(self):
        """require_permissions returns a PermissionChecker instance."""
        checker = require_permissions([Permission.CHAT_BASIC])
        assert isinstance(checker, PermissionChecker)


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS (would need real FastAPI app)
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegrationScenarios:
    """Integration-style tests for common scenarios."""

    def test_tier_upgrade_path_member_to_elite(self):
        """Simulates user upgrading from member to elite."""
        user_tier = "member"

        # Member can't access video
        member_perms = resolve_permissions(user_tier)
        assert Permission.AGENT_VIDEO not in member_perms

        # After upgrade to pro
        user_tier = "pro"
        pro_perms = resolve_permissions(user_tier)
        assert Permission.AGENT_VIDEO in pro_perms

        # After upgrade to business
        user_tier = "business"
        business_perms = resolve_permissions(user_tier)
        assert Permission.TEAM_LEGAL in business_perms

        # After upgrade to elite
        user_tier = "elite"
        elite_perms = resolve_permissions(user_tier)
        assert Permission.AGENT_CUSTOM in elite_perms
        assert Permission.DATA_EXPORT in elite_perms

    @pytest.mark.asyncio
    async def test_cirkelline_team_routing_scenario(self):
        """Tests agent routing based on tier permissions."""
        # Member user asks for video analysis
        user_tier = "member"

        # Check if video specialist accessible
        video_access = await check_agent_access("user-123", "video-specialist", user_tier)
        assert video_access["allowed"] is False

        # System should fall back to available agents
        available = get_available_agents_for_tier(user_tier)
        assert "audio-specialist" in available
        assert "image-specialist" in available
        assert "document-specialist" in available

    def test_permission_inheritance_chain(self):
        """Full inheritance chain test."""
        # Get all tier permissions
        member = resolve_permissions("member")
        pro = resolve_permissions("pro")
        business = resolve_permissions("business")
        elite = resolve_permissions("elite")
        family = resolve_permissions("family")

        # Each tier should be superset of previous
        assert member.issubset(pro)
        assert pro.issubset(business)
        assert business.issubset(elite)
        assert elite.issubset(family)


# ═══════════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
