"""
Tests for DEL J: Markedsspace & Fællesskab
===========================================

Tests for:
- MarketplaceConnector
- CommunityHub
- AssetListing
- ReviewSystem
- DiscoveryEngine
"""

import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal

from cirkelline.ckc.mastermind.marketplace import (
    # Enums
    AssetType,
    AssetStatus,
    PricingModel,
    CommunityRole,
    ReviewStatus,
    DiscoverySort,
    # Data classes
    Asset,
    AssetVersion,
    CommunityMember,
    Review,
    SearchResult,
    DiscoveryQuery,
    DiscoveryResponse,
    # Classes
    MarketplaceConnector,
    CommunityHub,
    AssetListing,
    ReviewSystem,
    DiscoveryEngine,
    # Factory functions
    create_marketplace_connector,
    get_marketplace_connector,
    create_community_hub,
    get_community_hub,
    create_asset_listing,
    get_asset_listing,
    create_review_system,
    get_review_system,
    create_discovery_engine,
    get_discovery_engine,
)


# =============================================================================
# TEST ENUMS
# =============================================================================

class TestMarketplaceEnums:
    """Tests for marketplace enums."""

    def test_asset_type_values(self):
        """Test AssetType enum values."""
        assert AssetType.TEMPLATE.value == "template"
        assert AssetType.PLUGIN.value == "plugin"
        assert AssetType.AGENT.value == "agent"
        assert len(AssetType) == 7

    def test_asset_status_values(self):
        """Test AssetStatus enum values."""
        assert AssetStatus.DRAFT.value == "draft"
        assert AssetStatus.PUBLISHED.value == "published"
        assert len(AssetStatus) == 5

    def test_pricing_model_values(self):
        """Test PricingModel enum values."""
        assert PricingModel.FREE.value == "free"
        assert PricingModel.SUBSCRIPTION.value == "subscription"
        assert len(PricingModel) == 5

    def test_community_role_values(self):
        """Test CommunityRole enum values."""
        assert CommunityRole.MEMBER.value == "member"
        assert CommunityRole.ADMIN.value == "admin"
        assert len(CommunityRole) == 5

    def test_review_status_values(self):
        """Test ReviewStatus enum values."""
        assert ReviewStatus.PENDING.value == "pending"
        assert ReviewStatus.APPROVED.value == "approved"
        assert len(ReviewStatus) == 4

    def test_discovery_sort_values(self):
        """Test DiscoverySort enum values."""
        assert DiscoverySort.RELEVANCE.value == "relevance"
        assert DiscoverySort.POPULARITY.value == "popularity"
        assert len(DiscoverySort) == 6


# =============================================================================
# TEST DATA CLASSES
# =============================================================================

class TestMarketplaceDataClasses:
    """Tests for marketplace data classes."""

    def test_asset_creation(self):
        """Test Asset creation."""
        asset = Asset(
            asset_id="asset_123",
            asset_type=AssetType.PLUGIN,
            name="Test Plugin",
            description="A test plugin",
            publisher_id="pub_456",
            status=AssetStatus.PUBLISHED,
            pricing_model=PricingModel.FREE
        )

        assert asset.asset_id == "asset_123"
        assert asset.asset_type == AssetType.PLUGIN
        assert asset.downloads == 0

    def test_review_rating_validation(self):
        """Test Review rating validation."""
        with pytest.raises(ValueError):
            Review(
                review_id="rev_123",
                asset_id="asset_456",
                reviewer_id="user_789",
                rating=6,  # Invalid
                title="Test",
                content="Content"
            )

    def test_community_member_creation(self):
        """Test CommunityMember creation."""
        member = CommunityMember(
            member_id="member_123",
            user_id="user_456",
            display_name="TestUser",
            role=CommunityRole.CONTRIBUTOR
        )

        assert member.reputation == 0
        assert member.contributions == 0

    def test_discovery_query_defaults(self):
        """Test DiscoveryQuery defaults."""
        query = DiscoveryQuery(query="test")

        assert query.page == 1
        assert query.page_size == 20
        assert query.sort_by == DiscoverySort.RELEVANCE


# =============================================================================
# TEST MARKETPLACE CONNECTOR
# =============================================================================

class TestMarketplaceConnector:
    """Tests for MarketplaceConnector class."""

    @pytest_asyncio.fixture
    async def marketplace(self):
        """Create marketplace connector fixture."""
        return create_marketplace_connector()

    @pytest.mark.asyncio
    async def test_publish_asset(self, marketplace):
        """Test publishing an asset."""
        asset = await marketplace.publish_asset(
            publisher_id="pub_123",
            asset_type=AssetType.TEMPLATE,
            name="My Template",
            description="A great template",
            pricing_model=PricingModel.FREE,
            tags=["productivity", "automation"]
        )

        assert asset.asset_id.startswith("asset_")
        assert asset.status == AssetStatus.PENDING_REVIEW
        assert "productivity" in asset.tags

    @pytest.mark.asyncio
    async def test_approve_asset(self, marketplace):
        """Test approving an asset."""
        asset = await marketplace.publish_asset(
            "pub_123", AssetType.PLUGIN, "Plugin", "Desc", PricingModel.ONE_TIME
        )
        approved = await marketplace.approve_asset(asset.asset_id)

        assert approved.status == AssetStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_purchase_asset(self, marketplace):
        """Test purchasing an asset."""
        asset = await marketplace.publish_asset(
            "pub_123", AssetType.WORKFLOW, "Workflow", "Desc", PricingModel.ONE_TIME
        )
        await marketplace.approve_asset(asset.asset_id)

        result = await marketplace.purchase_asset("user_456", asset.asset_id)

        assert result is True
        updated_asset = await marketplace.get_asset(asset.asset_id)
        assert updated_asset.downloads == 1

    @pytest.mark.asyncio
    async def test_get_user_purchases(self, marketplace):
        """Test getting user purchases."""
        asset1 = await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "T1", "D1", PricingModel.FREE
        )
        asset2 = await marketplace.publish_asset(
            "pub_2", AssetType.PLUGIN, "T2", "D2", PricingModel.FREE
        )
        await marketplace.approve_asset(asset1.asset_id)
        await marketplace.approve_asset(asset2.asset_id)

        await marketplace.purchase_asset("user_123", asset1.asset_id)
        await marketplace.purchase_asset("user_123", asset2.asset_id)

        purchases = await marketplace.get_user_purchases("user_123")
        assert len(purchases) == 2

    @pytest.mark.asyncio
    async def test_add_version(self, marketplace):
        """Test adding a new version."""
        asset = await marketplace.publish_asset(
            "pub_123", AssetType.PLUGIN, "Plugin", "Desc", PricingModel.FREE
        )

        version = await marketplace.add_version(
            asset.asset_id,
            version="2.0.0",
            changelog="New features",
            download_url="https://example.com/v2",
            file_size_bytes=1024000
        )

        assert version.version == "2.0.0"
        updated_asset = await marketplace.get_asset(asset.asset_id)
        assert updated_asset.version == "2.0.0"


# =============================================================================
# TEST COMMUNITY HUB
# =============================================================================

class TestCommunityHub:
    """Tests for CommunityHub class."""

    @pytest_asyncio.fixture
    async def hub(self):
        """Create community hub fixture."""
        return create_community_hub()

    @pytest.mark.asyncio
    async def test_register_member(self, hub):
        """Test registering a member."""
        member = await hub.register_member(
            user_id="user_123",
            display_name="TestUser",
            bio="Hello world"
        )

        assert member.member_id.startswith("member_")
        assert member.role == CommunityRole.MEMBER
        assert member.reputation == 0

    @pytest.mark.asyncio
    async def test_update_role(self, hub):
        """Test updating member role."""
        await hub.register_member("user_123", "TestUser")
        updated = await hub.update_role("user_123", CommunityRole.MODERATOR)

        assert updated.role == CommunityRole.MODERATOR

    @pytest.mark.asyncio
    async def test_add_reputation(self, hub):
        """Test adding reputation points."""
        await hub.register_member("user_123", "TestUser")
        updated = await hub.add_reputation("user_123", 50, "Helpful answer")

        assert updated.reputation == 50

    @pytest.mark.asyncio
    async def test_award_badge(self, hub):
        """Test awarding badge."""
        await hub.register_member("user_123", "TestUser")
        updated = await hub.award_badge("user_123", "first_post")

        assert "first_post" in updated.badges

    @pytest.mark.asyncio
    async def test_follow_unfollow(self, hub):
        """Test following and unfollowing users."""
        await hub.register_member("user_1", "User1")
        await hub.register_member("user_2", "User2")

        await hub.follow_user("user_1", "user_2")

        following = await hub.get_following("user_1")
        assert "user_2" in following

        followers = await hub.get_followers("user_2")
        assert "user_1" in followers

        await hub.unfollow_user("user_1", "user_2")
        following = await hub.get_following("user_1")
        assert "user_2" not in following

    @pytest.mark.asyncio
    async def test_leaderboard(self, hub):
        """Test reputation leaderboard."""
        await hub.register_member("user_1", "User1")
        await hub.register_member("user_2", "User2")
        await hub.register_member("user_3", "User3")

        await hub.add_reputation("user_1", 100, "")
        await hub.add_reputation("user_2", 50, "")
        await hub.add_reputation("user_3", 200, "")

        leaderboard = await hub.get_leaderboard(limit=3)

        assert leaderboard[0].user_id == "user_3"
        assert leaderboard[1].user_id == "user_1"
        assert leaderboard[2].user_id == "user_2"


# =============================================================================
# TEST ASSET LISTING
# =============================================================================

class TestAssetListing:
    """Tests for AssetListing class."""

    @pytest_asyncio.fixture
    async def listing(self):
        """Create asset listing fixture."""
        marketplace = create_marketplace_connector()
        return create_asset_listing(marketplace), marketplace

    @pytest.mark.asyncio
    async def test_add_to_category(self, listing):
        """Test adding asset to category."""
        listing_obj, marketplace = listing

        asset = await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "Test", "Desc", PricingModel.FREE
        )
        await marketplace.approve_asset(asset.asset_id)

        result = await listing_obj.add_to_category(asset.asset_id, "productivity")
        assert result is True

        categories = await listing_obj.get_categories()
        assert "productivity" in categories

    @pytest.mark.asyncio
    async def test_get_category_assets(self, listing):
        """Test getting assets in a category."""
        listing_obj, marketplace = listing

        asset = await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "Test", "Desc", PricingModel.FREE
        )
        await marketplace.approve_asset(asset.asset_id)
        await listing_obj.add_to_category(asset.asset_id, "tools")

        assets = await listing_obj.get_category_assets("tools")
        assert len(assets) == 1

    @pytest.mark.asyncio
    async def test_featured_assets(self, listing):
        """Test featured assets."""
        listing_obj, marketplace = listing

        asset = await marketplace.publish_asset(
            "pub_1", AssetType.PLUGIN, "Featured", "Desc", PricingModel.FREE
        )
        await marketplace.approve_asset(asset.asset_id)

        await listing_obj.set_featured([asset.asset_id])
        featured = await listing_obj.get_featured()

        assert len(featured) == 1
        assert featured[0].name == "Featured"


# =============================================================================
# TEST REVIEW SYSTEM
# =============================================================================

class TestReviewSystem:
    """Tests for ReviewSystem class."""

    @pytest_asyncio.fixture
    async def review_system(self):
        """Create review system fixture."""
        marketplace = create_marketplace_connector()
        return create_review_system(marketplace), marketplace

    @pytest.mark.asyncio
    async def test_submit_review(self, review_system):
        """Test submitting a review."""
        system, marketplace = review_system

        asset = await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "Test", "Desc", PricingModel.FREE
        )

        review = await system.submit_review(
            asset_id=asset.asset_id,
            reviewer_id="user_123",
            rating=5,
            title="Great template!",
            content="Very useful and well documented."
        )

        assert review.review_id.startswith("review_")
        assert review.rating == 5
        assert review.status == ReviewStatus.PENDING

    @pytest.mark.asyncio
    async def test_approve_review_updates_rating(self, review_system):
        """Test that approving review updates asset rating."""
        system, marketplace = review_system

        asset = await marketplace.publish_asset(
            "pub_1", AssetType.PLUGIN, "Test", "Desc", PricingModel.FREE
        )

        review = await system.submit_review(
            asset.asset_id, "user_1", 4, "Good", "Nice plugin"
        )
        await system.approve_review(review.review_id)

        updated_asset = await marketplace.get_asset(asset.asset_id)
        assert updated_asset.rating_avg == 4.0
        assert updated_asset.rating_count == 1

    @pytest.mark.asyncio
    async def test_mark_helpful(self, review_system):
        """Test marking review as helpful."""
        system, marketplace = review_system

        asset = await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "Test", "Desc", PricingModel.FREE
        )

        review = await system.submit_review(
            asset.asset_id, "user_1", 5, "Great", "Love it"
        )

        updated = await system.mark_helpful(review.review_id)
        assert updated.helpful_count == 1

    @pytest.mark.asyncio
    async def test_get_reviewer_stats(self, review_system):
        """Test getting reviewer statistics."""
        system, marketplace = review_system

        asset = await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "Test", "Desc", PricingModel.FREE
        )

        review1 = await system.submit_review(
            asset.asset_id, "user_1", 5, "Great", "Content"
        )
        review2 = await system.submit_review(
            asset.asset_id, "user_1", 4, "Good", "Content"
        )

        await system.approve_review(review1.review_id)
        await system.approve_review(review2.review_id)

        stats = await system.get_reviewer_stats("user_1")

        assert stats["total_reviews"] == 2
        assert stats["approved_reviews"] == 2
        assert stats["average_rating_given"] == 4.5


# =============================================================================
# TEST DISCOVERY ENGINE
# =============================================================================

class TestDiscoveryEngine:
    """Tests for DiscoveryEngine class."""

    @pytest_asyncio.fixture
    async def discovery(self):
        """Create discovery engine fixture."""
        marketplace = create_marketplace_connector()
        reviews = create_review_system(marketplace)
        return create_discovery_engine(marketplace, reviews), marketplace

    @pytest.mark.asyncio
    async def test_search_by_query(self, discovery):
        """Test searching by text query."""
        engine, marketplace = discovery

        await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "Productivity Template", "For work", PricingModel.FREE
        )
        await marketplace.publish_asset(
            "pub_2", AssetType.PLUGIN, "Gaming Plugin", "For fun", PricingModel.FREE
        )

        # Approve both
        for asset_id in marketplace._assets:
            await marketplace.approve_asset(asset_id)

        query = DiscoveryQuery(query="productivity")
        response = await engine.search(query)

        assert response.total_count == 1
        assert response.results[0].asset.name == "Productivity Template"

    @pytest.mark.asyncio
    async def test_search_by_asset_type(self, discovery):
        """Test filtering by asset type."""
        engine, marketplace = discovery

        await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "T1", "D1", PricingModel.FREE
        )
        await marketplace.publish_asset(
            "pub_2", AssetType.PLUGIN, "P1", "D2", PricingModel.FREE
        )

        for asset_id in marketplace._assets:
            await marketplace.approve_asset(asset_id)

        query = DiscoveryQuery(asset_types=[AssetType.PLUGIN])
        response = await engine.search(query)

        assert response.total_count == 1
        assert response.results[0].asset.asset_type == AssetType.PLUGIN

    @pytest.mark.asyncio
    async def test_search_with_sorting(self, discovery):
        """Test search with sorting."""
        engine, marketplace = discovery

        a1 = await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "Old", "D1", PricingModel.FREE
        )
        a2 = await marketplace.publish_asset(
            "pub_2", AssetType.TEMPLATE, "New", "D2", PricingModel.FREE
        )

        await marketplace.approve_asset(a1.asset_id)
        await marketplace.approve_asset(a2.asset_id)

        # Add downloads
        marketplace._assets[a1.asset_id].downloads = 100
        marketplace._assets[a2.asset_id].downloads = 50

        query = DiscoveryQuery(sort_by=DiscoverySort.POPULARITY)
        response = await engine.search(query)

        assert response.results[0].asset.downloads == 100

    @pytest.mark.asyncio
    async def test_facets(self, discovery):
        """Test facets in search results."""
        engine, marketplace = discovery

        await marketplace.publish_asset(
            "pub_1", AssetType.TEMPLATE, "T1", "D1", PricingModel.FREE, tags=["productivity"]
        )
        await marketplace.publish_asset(
            "pub_2", AssetType.PLUGIN, "P1", "D2", PricingModel.ONE_TIME, tags=["automation"]
        )

        for asset_id in marketplace._assets:
            await marketplace.approve_asset(asset_id)

        query = DiscoveryQuery()
        response = await engine.search(query)

        assert "asset_type" in response.facets
        assert "pricing_model" in response.facets
        assert "tags" in response.facets

    @pytest.mark.asyncio
    async def test_search_history(self, discovery):
        """Test search history recording."""
        engine, marketplace = discovery

        await engine.record_search("user_123", "templates")
        await engine.record_search("user_123", "plugins")

        history = await engine.get_search_history("user_123")

        assert "templates" in history
        assert "plugins" in history


# =============================================================================
# TEST FACTORY FUNCTIONS
# =============================================================================

class TestMarketplaceFactoryFunctions:
    """Tests for marketplace factory functions."""

    def test_create_marketplace_connector(self):
        """Test creating marketplace connector."""
        connector = create_marketplace_connector()
        assert isinstance(connector, MarketplaceConnector)

    def test_create_community_hub(self):
        """Test creating community hub."""
        hub = create_community_hub()
        assert isinstance(hub, CommunityHub)

    def test_create_asset_listing(self):
        """Test creating asset listing."""
        listing = create_asset_listing()
        assert isinstance(listing, AssetListing)

    def test_create_review_system(self):
        """Test creating review system."""
        system = create_review_system()
        assert isinstance(system, ReviewSystem)

    def test_create_discovery_engine(self):
        """Test creating discovery engine."""
        engine = create_discovery_engine()
        assert isinstance(engine, DiscoveryEngine)


# =============================================================================
# TEST MODULE IMPORTS
# =============================================================================

class TestMarketplaceModuleImports:
    """Tests for marketplace module imports."""

    def test_import_all_enums(self):
        """Test importing all enums from mastermind."""
        from cirkelline.ckc.mastermind import (
            AssetType,
            AssetStatus,
            PricingModel,
            CommunityRole,
            ReviewStatus,
            DiscoverySort,
        )
        assert AssetType is not None
        assert DiscoverySort is not None

    def test_import_all_dataclasses(self):
        """Test importing all dataclasses from mastermind."""
        from cirkelline.ckc.mastermind import (
            Asset,
            AssetVersion,
            CommunityMember,
            Review,
            SearchResult,
            DiscoveryQuery,
            DiscoveryResponse,
        )
        assert Asset is not None
        assert DiscoveryResponse is not None

    def test_import_all_classes(self):
        """Test importing all classes from mastermind."""
        from cirkelline.ckc.mastermind import (
            MarketplaceConnector,
            CommunityHub,
            AssetListing,
            ReviewSystem,
            DiscoveryEngine,
        )
        assert MarketplaceConnector is not None
        assert DiscoveryEngine is not None

    def test_all_exports(self):
        """Test all exports are in __all__."""
        from cirkelline.ckc.mastermind import __all__

        expected = [
            "AssetType", "AssetStatus", "PricingModel",
            "CommunityRole", "ReviewStatus", "DiscoverySort",
            "Asset", "AssetVersion", "CommunityMember",
            "Review", "SearchResult", "DiscoveryQuery", "DiscoveryResponse",
            "MarketplaceConnector", "CommunityHub", "AssetListing",
            "ReviewSystem", "DiscoveryEngine",
        ]

        for item in expected:
            assert item in __all__, f"{item} should be in __all__"
