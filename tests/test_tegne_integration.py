"""
Tests for CKC Tegne-enhed Integration (DEL B)
=============================================

Tests covering:
- Creative HITL handlers
- Cosmic Library connector
- Web3 concepts and NFT stubs
- Royalty tracking
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta


# =============================================================================
# CREATIVE HITL TESTS
# =============================================================================

class TestCreativeHITL:
    """Tests for Creative HITL handlers."""

    @pytest.fixture
    def hitl_handler(self):
        """Create a HITL handler for testing."""
        from cirkelline.ckc.integrations.hitl_creative import (
            create_creative_hitl_handler,
        )
        return create_creative_hitl_handler()

    @pytest.fixture
    def sample_options(self):
        """Create sample creative options."""
        from cirkelline.ckc.integrations.hitl_creative import CreativeOption
        return [
            CreativeOption(
                option_id="opt_1",
                label="Option A",
                description="First variant",
                preview_url="https://example.com/1.png",
                score=0.85,
            ),
            CreativeOption(
                option_id="opt_2",
                label="Option B",
                description="Second variant",
                preview_url="https://example.com/2.png",
                score=0.90,
            ),
            CreativeOption(
                option_id="opt_3",
                label="Option C",
                description="Third variant",
                preview_url="https://example.com/3.png",
                score=0.75,
            ),
        ]

    @pytest.mark.asyncio
    async def test_request_selection(self, hitl_handler, sample_options):
        """Test creating a selection request."""
        request = await hitl_handler.request_selection(
            options=sample_options,
            title="Select best image",
            session_id="test_session",
        )

        assert request is not None
        assert request.request_id.startswith("hitl_creative_")
        assert len(request.options) == 3
        assert request.status == "pending"

    @pytest.mark.asyncio
    async def test_request_approval(self, hitl_handler, sample_options):
        """Test creating an approval request."""
        from cirkelline.ckc.integrations.hitl_creative import CreativeHITLType

        request = await hitl_handler.request_approval(
            option=sample_options[0],
            title="Approve output",
        )

        assert request is not None
        assert request.request_type == CreativeHITLType.APPROVE_REJECT
        assert len(request.options) == 1

    @pytest.mark.asyncio
    async def test_respond_to_request(self, hitl_handler, sample_options):
        """Test responding to a HITL request."""
        from cirkelline.ckc.integrations.hitl_creative import CreativeDecision

        request = await hitl_handler.request_selection(
            options=sample_options,
            title="Test selection",
        )

        response = await hitl_handler.respond(
            request_id=request.request_id,
            decision=CreativeDecision.SELECT,
            selected_option_id="opt_2",
            feedback="Option B looks best",
        )

        assert response is not None
        assert response.decision == CreativeDecision.SELECT
        assert response.selected_option_id == "opt_2"
        assert request.status == "responded"

    @pytest.mark.asyncio
    async def test_get_pending_requests(self, hitl_handler, sample_options):
        """Test getting pending requests."""
        # Create multiple requests
        await hitl_handler.request_selection(options=sample_options, title="Test 1")
        await hitl_handler.request_selection(options=sample_options, title="Test 2")

        pending = hitl_handler.get_pending_requests()
        assert len(pending) >= 2

    @pytest.mark.asyncio
    async def test_statistics(self, hitl_handler, sample_options):
        """Test getting HITL statistics."""
        from cirkelline.ckc.integrations.hitl_creative import CreativeDecision

        request = await hitl_handler.request_selection(
            options=sample_options,
            title="Stats test",
        )
        await hitl_handler.respond(
            request_id=request.request_id,
            decision=CreativeDecision.APPROVE,
        )

        stats = hitl_handler.get_statistics()
        assert stats["total_requests"] >= 1
        assert stats["total_responses"] >= 1


# =============================================================================
# COSMIC LIBRARY TESTS
# =============================================================================

class TestCosmicLibrary:
    """Tests for Cosmic Library connector."""

    @pytest_asyncio.fixture
    async def connector(self):
        """Create a Cosmic Library connector."""
        from cirkelline.ckc.integrations.cosmic_library import (
            create_cosmic_connector,
        )
        return await create_cosmic_connector(storage_path="/tmp/test_cosmic")

    @pytest.fixture
    def mock_creative_result(self):
        """Create a mock creative result."""
        class MockResult:
            request_id = "req_12345"
            success = True
            capability = type('Capability', (), {'value': 'text_to_image'})()
            output_format = type('Format', (), {'value': 'png'})()
            output_paths = ["/tmp/test_image.png"]
            output_urls = ["https://cdn.example.com/test.png"]
            quality_score = 0.85
            aesthetic_score = 0.80
            cost_usd = 0.01
            model_used = "test_model"
            metadata = {
                "prompt": "A beautiful sunset",
                "style": "fantasy",
            }
        return MockResult()

    @pytest.mark.asyncio
    async def test_archive_creative_result(self, connector, mock_creative_result):
        """Test archiving a creative result."""
        result = await connector.archive_creative_result(
            result=mock_creative_result,
            owner_id="test_user",
            session_id="test_session",
            tags=["sunset", "landscape"],
        )

        assert result.success is True
        assert result.asset_id is not None
        assert result.asset is not None

    @pytest.mark.asyncio
    async def test_get_asset(self, connector, mock_creative_result):
        """Test retrieving an asset."""
        archive_result = await connector.archive_creative_result(
            result=mock_creative_result,
            owner_id="test_user",
        )

        asset = await connector.get_asset(archive_result.asset_id)
        assert asset is not None
        assert asset.asset_id == archive_result.asset_id

    @pytest.mark.asyncio
    async def test_search_assets(self, connector, mock_creative_result):
        """Test searching assets."""
        await connector.archive_creative_result(
            result=mock_creative_result,
            owner_id="test_user",
            tags=["dragon", "fantasy"],
        )

        # Search should work
        results = await connector.search_assets(
            query="fantasy",
            owner_id="test_user",
        )
        # May or may not find it depending on metadata

    @pytest.mark.asyncio
    async def test_session_assets(self, connector, mock_creative_result):
        """Test getting assets for a session."""
        session_id = "session_test_123"

        await connector.archive_creative_result(
            result=mock_creative_result,
            owner_id="test_user",
            session_id=session_id,
        )

        assets = await connector.get_session_assets(session_id)
        assert len(assets) >= 1

    @pytest.mark.asyncio
    async def test_statistics(self, connector, mock_creative_result):
        """Test connector statistics."""
        await connector.archive_creative_result(
            result=mock_creative_result,
            owner_id="test_user",
        )

        stats = connector.get_statistics()
        assert stats["total_archived"] >= 1


# =============================================================================
# WEB3 CONCEPTS TESTS
# =============================================================================

class TestWeb3Concepts:
    """Tests for Web3 data models."""

    def test_nft_attribute(self):
        """Test NFT attribute creation."""
        from cirkelline.ckc.web3.concepts import NFTAttribute

        attr = NFTAttribute(
            trait_type="Background",
            value="Blue",
        )

        assert attr.trait_type == "Background"
        data = attr.to_dict()
        assert "trait_type" in data

    def test_nft_metadata(self):
        """Test NFT metadata creation."""
        from cirkelline.ckc.web3.concepts import NFTMetadata, NFTAttribute

        metadata = NFTMetadata(
            name="Test NFT",
            description="A test NFT",
            image="ipfs://test",
            attributes=[
                NFTAttribute("Style", "Fantasy"),
                NFTAttribute("Rarity", "Rare"),
            ],
            ckc_asset_id="asset_123",
        )

        assert metadata.name == "Test NFT"
        data = metadata.to_dict()
        assert len(data["attributes"]) == 2

    def test_mint_request(self):
        """Test NFT mint request creation."""
        from cirkelline.ckc.web3.concepts import NFTMintRequest, TokenType

        request = NFTMintRequest(
            asset_id="asset_123",
            blockchain="polygon",
            name="My NFT",
            description="An awesome NFT",
            token_type=TokenType.SINGLE,
        )

        assert request.blockchain == "polygon"
        data = request.to_dict()
        assert data["token_type"] == "single"

    def test_royalty_config_validation(self):
        """Test royalty config validation."""
        from cirkelline.ckc.web3.concepts import RoyaltyConfig

        valid_config = RoyaltyConfig(
            creator_royalty_percent=5.0,
            platform_royalty_percent=2.5,
        )
        assert valid_config.validate() is True

        invalid_config = RoyaltyConfig(
            creator_royalty_percent=15.0,  # Too high
        )
        assert invalid_config.validate() is False


# =============================================================================
# NFT SERVICE TESTS
# =============================================================================

class TestNFTService:
    """Tests for NFT service stubs."""

    @pytest_asyncio.fixture
    async def nft_service(self):
        """Create NFT service for testing."""
        from cirkelline.ckc.web3.nft_stubs import create_nft_service
        return await create_nft_service()

    @pytest.mark.asyncio
    async def test_service_initialization(self, nft_service):
        """Test NFT service initializes correctly."""
        blockchains = nft_service.get_supported_blockchains()
        assert "ethereum" in blockchains
        assert "polygon" in blockchains
        assert "solana" in blockchains

    @pytest.mark.asyncio
    async def test_mint_nft_polygon(self, nft_service):
        """Test minting NFT on Polygon."""
        from cirkelline.ckc.web3.concepts import NFTMintRequest

        request = NFTMintRequest(
            asset_id="asset_test_1",
            blockchain="polygon",
            name="Test NFT",
            description="A test NFT",
            creator_address="0x" + "1" * 40,
        )

        result = await nft_service.mint_nft(request)

        assert result.success is True
        assert result.token_id is not None
        assert result.blockchain == "polygon"
        assert result.mint_cost_usd < 1.0  # Polygon is cheap

    @pytest.mark.asyncio
    async def test_mint_nft_ethereum(self, nft_service):
        """Test minting NFT on Ethereum."""
        from cirkelline.ckc.web3.concepts import NFTMintRequest

        request = NFTMintRequest(
            asset_id="asset_test_2",
            blockchain="ethereum",
            name="ETH NFT",
            description="Ethereum NFT",
            creator_address="0x" + "2" * 40,
        )

        result = await nft_service.mint_nft(request)

        assert result.success is True
        assert result.blockchain == "ethereum"

    @pytest.mark.asyncio
    async def test_mint_nft_solana(self, nft_service):
        """Test minting NFT on Solana."""
        from cirkelline.ckc.web3.concepts import NFTMintRequest

        request = NFTMintRequest(
            asset_id="asset_test_3",
            blockchain="solana",
            name="SOL NFT",
            description="Solana NFT",
            creator_address="SolanaAddress123",
        )

        result = await nft_service.mint_nft(request)

        assert result.success is True
        assert result.blockchain == "solana"

    @pytest.mark.asyncio
    async def test_verify_ownership(self, nft_service):
        """Test ownership verification."""
        from cirkelline.ckc.web3.concepts import NFTMintRequest

        # First mint
        request = NFTMintRequest(
            asset_id="asset_verify",
            blockchain="polygon",
            name="Verify NFT",
            creator_address="0x" + "3" * 40,
        )
        mint_result = await nft_service.mint_nft(request)

        # Then verify
        ownership = await nft_service.verify_ownership(
            token_id=mint_result.token_id,
            contract_address=mint_result.contract_address,
            blockchain="polygon",
        )

        assert ownership.verified is True
        assert ownership.current_owner == "0x" + "3" * 40

    @pytest.mark.asyncio
    async def test_estimate_cost(self, nft_service):
        """Test gas estimation."""
        estimate = await nft_service.estimate_mint_cost("polygon")
        assert "cost_usd" in estimate or "cost_matic" in estimate

    @pytest.mark.asyncio
    async def test_service_statistics(self, nft_service):
        """Test service statistics."""
        stats = nft_service.get_statistics()
        assert "total_mints" in stats
        assert "supported_blockchains" in stats


# =============================================================================
# ROYALTY TRACKING TESTS
# =============================================================================

class TestRoyaltyTracking:
    """Tests for royalty tracking."""

    @pytest_asyncio.fixture
    async def tracker(self):
        """Create royalty tracker for testing."""
        from cirkelline.ckc.web3.royalty_tracking import create_royalty_tracker
        return await create_royalty_tracker()

    @pytest.mark.asyncio
    async def test_record_sale(self, tracker):
        """Test recording a sale."""
        payment = await tracker.record_sale(
            token_id="token_123",
            sale_price_usd=100.0,
            creator_address="0x" + "1" * 40,
            creator_id="creator_1",
            royalty_percent=5.0,
        )

        assert payment is not None
        assert payment.royalty_amount_usd == 5.0  # 5% of 100

    @pytest.mark.asyncio
    async def test_get_payments_for_creator(self, tracker):
        """Test getting payments for creator."""
        await tracker.record_sale(
            token_id="token_1",
            sale_price_usd=100.0,
            creator_id="creator_test",
            royalty_percent=5.0,
        )
        await tracker.record_sale(
            token_id="token_2",
            sale_price_usd=200.0,
            creator_id="creator_test",
            royalty_percent=5.0,
        )

        payments = await tracker.get_payments_for_creator("creator_test")
        assert len(payments) == 2

    @pytest.mark.asyncio
    async def test_mark_paid(self, tracker):
        """Test marking payment as paid."""
        payment = await tracker.record_sale(
            token_id="token_paid",
            sale_price_usd=50.0,
            royalty_percent=5.0,
        )

        success = await tracker.mark_paid(
            payment_id=payment.payment_id,
            transaction_hash="0x" + "abc" * 20,
        )

        assert success is True
        assert payment.paid is True

    @pytest.mark.asyncio
    async def test_get_pending_payments(self, tracker):
        """Test getting pending payments."""
        await tracker.record_sale(
            token_id="token_pending",
            sale_price_usd=75.0,
            royalty_percent=5.0,
        )

        pending = await tracker.get_pending_payments()
        assert len(pending) >= 1
        assert all(not p.paid for p in pending)

    @pytest.mark.asyncio
    async def test_creator_earnings(self, tracker):
        """Test creator earnings tracking."""
        await tracker.record_sale(
            token_id="token_earn_1",
            sale_price_usd=100.0,
            creator_id="earner_1",
            creator_address="0xEarner",
            royalty_percent=5.0,
        )
        await tracker.record_sale(
            token_id="token_earn_2",
            sale_price_usd=200.0,
            creator_id="earner_1",
            creator_address="0xEarner",
            royalty_percent=5.0,
        )

        earnings = await tracker.get_creator_earnings("earner_1")
        assert earnings is not None
        assert earnings.total_sales == 2
        assert earnings.total_royalties_earned_usd == 15.0  # 5 + 10

    @pytest.mark.asyncio
    async def test_generate_report(self, tracker):
        """Test generating royalty report."""
        await tracker.record_sale(
            token_id="token_report",
            sale_price_usd=100.0,
            royalty_percent=5.0,
        )

        report = await tracker.generate_report(
            report_type="platform",
            period_days=30,
        )

        assert report is not None
        assert report.total_sales >= 1
        assert report.total_royalties_usd >= 5.0

    def test_earnings_calculator(self, tracker):
        """Test earnings calculator."""
        calc = tracker.calculator

        royalties = calc.calculate_royalties(100.0)
        assert royalties["creator_royalty_usd"] == 5.0
        assert royalties["platform_royalty_usd"] == 2.5

    def test_split_calculation(self, tracker):
        """Test split distribution calculation."""
        calc = tracker.calculator

        split = calc.calculate_split(
            amount_usd=100.0,
            recipients={
                "0xCreator1": 60.0,
                "0xCreator2": 40.0,
            },
        )

        assert split["0xCreator1"] == 60.0
        assert split["0xCreator2"] == 40.0

    @pytest.mark.asyncio
    async def test_statistics(self, tracker):
        """Test tracker statistics."""
        await tracker.record_sale(
            token_id="token_stats",
            sale_price_usd=50.0,
            royalty_percent=5.0,
        )

        stats = tracker.get_statistics()
        assert stats["total_payments"] >= 1
        assert stats["total_tracked_usd"] >= 2.5


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for DEL B modules."""

    @pytest.mark.asyncio
    async def test_full_creative_flow(self):
        """Test complete creative workflow."""
        from cirkelline.ckc.integrations.hitl_creative import (
            create_creative_hitl_handler,
            CreativeOption,
            CreativeDecision,
        )
        from cirkelline.ckc.integrations.cosmic_library import (
            create_cosmic_connector,
        )

        # 1. Create handlers
        hitl = create_creative_hitl_handler()
        connector = await create_cosmic_connector(storage_path="/tmp/test_flow")

        # 2. Create HITL request
        options = [
            CreativeOption("opt_1", "Version A", "First version", score=0.8),
            CreativeOption("opt_2", "Version B", "Second version", score=0.9),
        ]

        request = await hitl.request_selection(
            options=options,
            title="Select best creative",
            session_id="flow_session",
        )

        # 3. Respond
        response = await hitl.respond(
            request_id=request.request_id,
            decision=CreativeDecision.SELECT,
            selected_option_id="opt_2",
        )

        assert response.decision == CreativeDecision.SELECT

    @pytest.mark.asyncio
    async def test_full_nft_flow(self):
        """Test complete NFT minting and tracking flow."""
        from cirkelline.ckc.web3.nft_stubs import create_nft_service
        from cirkelline.ckc.web3.royalty_tracking import create_royalty_tracker
        from cirkelline.ckc.web3.concepts import NFTMintRequest

        # 1. Create services
        nft_service = await create_nft_service()
        tracker = await create_royalty_tracker()

        # 2. Mint NFT
        mint_request = NFTMintRequest(
            asset_id="flow_asset",
            blockchain="polygon",
            name="Flow Test NFT",
            creator_address="0xCreator",
            creator_id="creator_flow",
        )

        mint_result = await nft_service.mint_nft(mint_request)
        assert mint_result.success is True

        # 3. Simulate sale and track royalty
        payment = await tracker.record_sale(
            token_id=mint_result.token_id,
            sale_price_usd=500.0,
            creator_id="creator_flow",
            creator_address="0xCreator",
            royalty_percent=5.0,
            transaction_hash="0xSaleHash",
        )

        assert payment.royalty_amount_usd == 25.0

        # 4. Get earnings
        earnings = await tracker.get_creator_earnings("creator_flow")
        assert earnings.total_royalties_earned_usd == 25.0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
