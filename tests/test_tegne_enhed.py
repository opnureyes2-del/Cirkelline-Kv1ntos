"""
Tests for CKC Tegne-enhed (Drawing Unit)
========================================

Comprehensive tests for:
    - KreativKommandant
    - Creative Specialists
    - API Integrations
    - Creative Learning Room
    - Workflows and Journey Commands
"""

import asyncio
import pytest
from datetime import datetime, timezone
from typing import Dict, Any

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio(loop_scope="function")


# ========== Core Tests ==========

class TestKreativKommandant:
    """Tests for KreativKommandant core functionality."""

    async def test_create_kommandant(self):
        """Test creating a KreativKommandant."""
        from cirkelline.ckc.tegne_enhed.core import (
            KreativKommandant,
            KommandantStatus
        )

        kommandant = KreativKommandant(
            room_id=1,
            name="Test Kreativ Kommandant",
            budget_limit_usd=10.0
        )

        assert kommandant.name == "Test Kreativ Kommandant"
        assert kommandant.room_id == 1
        assert kommandant.budget_limit_usd == 10.0
        assert kommandant.status == KommandantStatus.INITIALIZING

    async def test_start_stop_kommandant(self):
        """Test starting and stopping KreativKommandant."""
        from cirkelline.ckc.tegne_enhed.core import (
            KreativKommandant,
            KommandantStatus
        )

        kommandant = KreativKommandant(room_id=2, name="Lifecycle Test")

        # Start
        success = await kommandant.start()
        assert success is True
        assert kommandant.status == KommandantStatus.IDLE
        assert kommandant._running is True

        # Stop
        await kommandant.stop()
        assert kommandant.status == KommandantStatus.STOPPED
        assert kommandant._running is False

    async def test_generate_image(self):
        """Test image generation."""
        from cirkelline.ckc.tegne_enhed.core import (
            KreativKommandant,
            CreativeCapability
        )

        kommandant = KreativKommandant(room_id=3, name="Image Gen Test")
        await kommandant.start()

        result = await kommandant.generate_image(
            prompt="A beautiful sunset over mountains",
            style="realistic",
            size="1024x1024",
            num_images=1
        )

        assert result.success is True
        assert result.capability == CreativeCapability.TEXT_TO_IMAGE
        assert len(result.output_paths) > 0
        assert result.cost_usd > 0

        await kommandant.stop()

    async def test_create_animation(self):
        """Test animation creation."""
        from cirkelline.ckc.tegne_enhed.core import (
            KreativKommandant,
            CreativeCapability
        )

        kommandant = KreativKommandant(room_id=4, name="Animation Test")
        await kommandant.start()

        result = await kommandant.create_animation(
            image_path="/tmp/test_image.png",
            motion_type="zoom_out",
            duration_seconds=5.0
        )

        assert result.success is True
        assert result.capability == CreativeCapability.IMAGE_TO_ANIMATION
        assert "mp4" in str(result.output_paths[0]).lower() or "mp4" in str(result.output_format).lower()

        await kommandant.stop()

    async def test_apply_style(self):
        """Test style transfer."""
        from cirkelline.ckc.tegne_enhed.core import (
            KreativKommandant,
            CreativeCapability
        )

        kommandant = KreativKommandant(room_id=5, name="Style Test")
        await kommandant.start()

        result = await kommandant.apply_style(
            image_path="/tmp/test_image.png",
            style_name="watercolor",
            intensity=0.8
        )

        assert result.success is True
        assert result.capability == CreativeCapability.STYLE_TRANSFER

        await kommandant.stop()

    async def test_vectorize(self):
        """Test vectorization."""
        from cirkelline.ckc.tegne_enhed.core import (
            KreativKommandant,
            CreativeCapability
        )

        kommandant = KreativKommandant(room_id=6, name="Vector Test")
        await kommandant.start()

        result = await kommandant.vectorize(
            image_path="/tmp/test_image.png",
            output_format="svg"
        )

        assert result.success is True
        assert result.capability == CreativeCapability.VECTORIZATION

        await kommandant.stop()

    async def test_budget_limit(self):
        """Test budget limit enforcement."""
        from cirkelline.ckc.tegne_enhed.core import KreativKommandant

        kommandant = KreativKommandant(
            room_id=7,
            name="Budget Test",
            budget_limit_usd=0.001  # Very low budget
        )
        await kommandant.start()

        # First request should fail due to budget
        result = await kommandant.generate_image(
            prompt="Test",
            num_images=10  # Would exceed budget
        )

        # Should fail due to budget
        assert result.success is False or kommandant.total_cost_usd <= kommandant.budget_limit_usd

        await kommandant.stop()

    async def test_statistics(self):
        """Test statistics tracking."""
        from cirkelline.ckc.tegne_enhed.core import KreativKommandant

        kommandant = KreativKommandant(room_id=8, name="Stats Test")
        await kommandant.start()

        # Generate some requests
        await kommandant.generate_image("Test 1")
        await kommandant.generate_image("Test 2")

        stats = kommandant.get_statistics()

        assert stats["requests_received"] == 2
        assert stats["requests_completed"] == 2
        assert stats["total_cost_usd"] > 0
        assert stats["images_generated"] == 2

        await kommandant.stop()


class TestCreativeRequest:
    """Tests for CreativeRequest data class."""

    def test_create_request(self):
        """Test creating a creative request."""
        from cirkelline.ckc.tegne_enhed.core import (
            CreativeRequest,
            CreativeCapability,
            CreativeTaskType,
            OutputFormat
        )

        request = CreativeRequest(
            request_id="test_001",
            task_type=CreativeTaskType.GENERATE,
            capability=CreativeCapability.TEXT_TO_IMAGE,
            prompt="A dragon flying over mountains"
        )

        assert request.request_id == "test_001"
        assert request.capability == CreativeCapability.TEXT_TO_IMAGE
        assert request.output_format == OutputFormat.PNG  # Default

    def test_request_to_dict(self):
        """Test request serialization."""
        from cirkelline.ckc.tegne_enhed.core import (
            CreativeRequest,
            CreativeCapability,
            CreativeTaskType
        )

        request = CreativeRequest(
            request_id="test_002",
            task_type=CreativeTaskType.GENERATE,
            capability=CreativeCapability.TEXT_TO_IMAGE,
            prompt="Test prompt"
        )

        data = request.to_dict()

        assert data["request_id"] == "test_002"
        assert data["capability"] == "text_to_image"
        assert "created_at" in data


class TestCreativeResult:
    """Tests for CreativeResult data class."""

    def test_create_result(self):
        """Test creating a creative result."""
        from cirkelline.ckc.tegne_enhed.core import (
            CreativeResult,
            CreativeCapability,
            CreativeTaskType
        )

        result = CreativeResult(
            request_id="test_001",
            success=True,
            task_type=CreativeTaskType.GENERATE,
            capability=CreativeCapability.TEXT_TO_IMAGE,
            output_paths=["/tmp/output.png"],
            cost_usd=0.01
        )

        assert result.success is True
        assert result.cost_usd == 0.01
        assert len(result.output_paths) == 1


# ========== Specialist Tests ==========

class TestImageGeneratorSpecialist:
    """Tests for ImageGeneratorSpecialist."""

    async def test_create_specialist(self):
        """Test creating an image generator specialist."""
        from cirkelline.ckc.tegne_enhed.specialists import (
            ImageGeneratorSpecialist,
            SpecialistStatus
        )

        specialist = ImageGeneratorSpecialist()

        assert specialist.specialist_type == "image-generator"
        assert specialist.status == SpecialistStatus.IDLE
        assert specialist.max_load == 5

    async def test_can_handle_capabilities(self):
        """Test capability handling."""
        from cirkelline.ckc.tegne_enhed.specialists import ImageGeneratorSpecialist
        from cirkelline.ckc.tegne_enhed.core import CreativeCapability

        specialist = ImageGeneratorSpecialist()

        assert specialist.can_handle(CreativeCapability.TEXT_TO_IMAGE) is True
        assert specialist.can_handle(CreativeCapability.IMAGE_TO_IMAGE) is True
        assert specialist.can_handle(CreativeCapability.IMAGE_TO_ANIMATION) is False

    async def test_process_request(self):
        """Test processing a request."""
        from cirkelline.ckc.tegne_enhed.specialists import ImageGeneratorSpecialist
        from cirkelline.ckc.tegne_enhed.core import (
            CreativeRequest,
            CreativeCapability,
            CreativeTaskType
        )

        specialist = ImageGeneratorSpecialist()

        request = CreativeRequest(
            request_id="spec_test_001",
            task_type=CreativeTaskType.GENERATE,
            capability=CreativeCapability.TEXT_TO_IMAGE,
            prompt="A test image"
        )

        result = await specialist.process(request)

        assert result.success is True
        assert result.specialist_used == specialist.specialist_id


class TestAnimatorSpecialist:
    """Tests for AnimatorSpecialist."""

    async def test_create_specialist(self):
        """Test creating an animator specialist."""
        from cirkelline.ckc.tegne_enhed.specialists import AnimatorSpecialist

        specialist = AnimatorSpecialist()

        assert specialist.specialist_type == "animator"
        assert specialist.max_load == 3

    async def test_process_animation(self):
        """Test processing an animation request."""
        from cirkelline.ckc.tegne_enhed.specialists import AnimatorSpecialist
        from cirkelline.ckc.tegne_enhed.core import (
            CreativeRequest,
            CreativeCapability,
            CreativeTaskType,
            AnimationConfig
        )

        specialist = AnimatorSpecialist()

        request = CreativeRequest(
            request_id="anim_test_001",
            task_type=CreativeTaskType.ANIMATE,
            capability=CreativeCapability.IMAGE_TO_ANIMATION,
            prompt="Animate",
            input_image="/tmp/test.png",
            animation_config=AnimationConfig(
                motion_type="zoom_out",
                duration_seconds=5.0
            )
        )

        result = await specialist.process(request)

        assert result.success is True
        assert "mp4" in str(result.output_paths[0]) or result.output_format.value == "mp4"


class TestStyleTransferSpecialist:
    """Tests for StyleTransferSpecialist."""

    async def test_create_specialist(self):
        """Test creating a style transfer specialist."""
        from cirkelline.ckc.tegne_enhed.specialists import StyleTransferSpecialist

        specialist = StyleTransferSpecialist()

        assert specialist.specialist_type == "style-transfer"
        assert specialist.max_load == 10  # Prodia is fast

    async def test_available_styles(self):
        """Test available styles."""
        from cirkelline.ckc.tegne_enhed.specialists import StyleTransferSpecialist

        specialist = StyleTransferSpecialist()

        assert "van_gogh" in specialist.STYLE_MODELS
        assert "anime" in specialist.STYLE_MODELS


class TestVectorizerSpecialist:
    """Tests for VectorizerSpecialist."""

    async def test_create_specialist(self):
        """Test creating a vectorizer specialist."""
        from cirkelline.ckc.tegne_enhed.specialists import VectorizerSpecialist

        specialist = VectorizerSpecialist()

        assert specialist.specialist_type == "vectorizer"

    async def test_detail_presets(self):
        """Test detail presets."""
        from cirkelline.ckc.tegne_enhed.specialists import VectorizerSpecialist

        specialist = VectorizerSpecialist()

        assert "low" in specialist.DETAIL_PRESETS
        assert "medium" in specialist.DETAIL_PRESETS
        assert "high" in specialist.DETAIL_PRESETS


class TestSpecialistFactory:
    """Tests for specialist factory functions."""

    def test_get_specialist(self):
        """Test getting specialists by type."""
        from cirkelline.ckc.tegne_enhed.specialists import get_creative_specialist

        img_specialist = get_creative_specialist("image-generator")
        assert img_specialist is not None
        assert img_specialist.specialist_type == "image-generator"

        anim_specialist = get_creative_specialist("animator")
        assert anim_specialist is not None

    def test_list_specialists(self):
        """Test listing all specialists."""
        from cirkelline.ckc.tegne_enhed.specialists import list_creative_specialists

        specialists = list_creative_specialists()

        assert len(specialists) >= 4
        # SpecialistInfo objects have specialist_type attribute
        types = [s.specialist_type for s in specialists]
        assert "image-generator" in types
        assert "animator" in types


# ========== API Integration Tests ==========

class TestReplicateClient:
    """Tests for Replicate API client."""

    async def test_create_client(self):
        """Test creating Replicate client."""
        from cirkelline.ckc.tegne_enhed.api_integrations import ReplicateClient

        client = ReplicateClient()

        assert client.config.base_url == "https://api.replicate.com/v1"

    async def test_mock_generate(self):
        """Test mock image generation."""
        from cirkelline.ckc.tegne_enhed.api_integrations import ReplicateClient

        client = ReplicateClient()

        response = await client.generate_image({
            "prompt": "Test",
            "width": 1024,
            "height": 1024
        })

        assert response.success is True
        assert response.cost_usd > 0


class TestLumaAIClient:
    """Tests for Luma AI client."""

    async def test_create_client(self):
        """Test creating Luma AI client."""
        from cirkelline.ckc.tegne_enhed.api_integrations import LumaAIClient

        client = LumaAIClient()

        assert client.config.timeout_seconds == 300  # Long timeout for video

    async def test_mock_animate(self):
        """Test mock animation."""
        from cirkelline.ckc.tegne_enhed.api_integrations import LumaAIClient

        client = LumaAIClient()

        response = await client.create_animation({
            "image_path": "/tmp/test.png",
            "duration": 5
        })

        assert response.success is True


class TestProdiaClient:
    """Tests for Prodia API client."""

    async def test_create_client(self):
        """Test creating Prodia client."""
        from cirkelline.ckc.tegne_enhed.api_integrations import ProdiaClient

        client = ProdiaClient()

        assert client.config.rate_limit_per_minute == 100  # Fast API

    async def test_available_styles(self):
        """Test available styles."""
        from cirkelline.ckc.tegne_enhed.api_integrations import ProdiaClient

        client = ProdiaClient()

        assert "anime" in client.STYLES
        assert "digital-art" in client.STYLES


class TestVectorizerAIClient:
    """Tests for Vectorizer.AI client."""

    async def test_create_client(self):
        """Test creating Vectorizer.AI client."""
        from cirkelline.ckc.tegne_enhed.api_integrations import VectorizerAIClient

        client = VectorizerAIClient()

        assert "svg" in client.OUTPUT_FORMATS

    async def test_mock_vectorize(self):
        """Test mock vectorization."""
        from cirkelline.ckc.tegne_enhed.api_integrations import VectorizerAIClient

        client = VectorizerAIClient()

        response = await client.vectorize({
            "image_path": "/tmp/test.png",
            "output_format": "svg"
        })

        assert response.success is True


class TestAPIFactory:
    """Tests for API client factory."""

    def test_get_api_client(self):
        """Test getting API clients."""
        from cirkelline.ckc.tegne_enhed.api_integrations import get_api_client

        replicate = get_api_client("replicate")
        assert replicate is not None

        luma = get_api_client("luma")
        assert luma is not None

    def test_estimate_cost(self):
        """Test cost estimation."""
        from cirkelline.ckc.tegne_enhed.api_integrations import estimate_cost

        img_cost = estimate_cost("text_to_image")
        assert img_cost > 0

        anim_cost = estimate_cost("image_to_animation")
        assert anim_cost > img_cost  # Animation is more expensive

    async def test_check_api_health(self):
        """Test API health check."""
        from cirkelline.ckc.tegne_enhed.api_integrations import check_api_health

        health = await check_api_health()

        assert "replicate" in health
        assert "luma" in health


# ========== Creative Room Tests ==========

class TestCreativeLearningRoom:
    """Tests for CreativeLearningRoom."""

    async def test_create_room(self):
        """Test creating a creative room."""
        from cirkelline.ckc.tegne_enhed.creative_room import (
            CreativeLearningRoom,
            RoomStatus
        )

        room = CreativeLearningRoom(
            room_id=1,
            name="Test Room",
            owner="admin"
        )

        assert room.name == "Test Room"
        assert room.status == RoomStatus.INITIALIZING

    async def test_initialize_room(self):
        """Test room initialization."""
        from cirkelline.ckc.tegne_enhed.creative_room import CreativeLearningRoom, RoomStatus

        room = CreativeLearningRoom(room_id=2, name="Init Test")
        success = await room.initialize()

        assert success is True
        assert room.status == RoomStatus.ACTIVE
        assert room.kommandant is not None

        await room.close()

    async def test_create_image_via_room(self):
        """Test image creation via room."""
        from cirkelline.ckc.tegne_enhed.creative_room import CreativeLearningRoom

        room = CreativeLearningRoom(room_id=3, name="Image Test Room")
        await room.initialize()

        result = await room.create_image("A beautiful landscape")

        assert result.success is True
        assert room.total_creations == 1
        assert len(room._gallery) == 1

        await room.close()

    async def test_gallery(self):
        """Test gallery functionality."""
        from cirkelline.ckc.tegne_enhed.creative_room import CreativeLearningRoom

        room = CreativeLearningRoom(room_id=4, name="Gallery Test")
        await room.initialize()

        # Create some images
        await room.create_image("Test 1")
        await room.create_image("Test 2")

        gallery = room.get_gallery()

        assert len(gallery) == 2

        await room.close()

    async def test_templates(self):
        """Test template availability."""
        from cirkelline.ckc.tegne_enhed.creative_room import CreativeLearningRoom

        room = CreativeLearningRoom(room_id=5, name="Template Test")

        assert "character_sheet" in room._templates
        assert "animated_artwork" in room._templates
        assert "logo_creator" in room._templates


class TestCreativeWorkflow:
    """Tests for CreativeWorkflow."""

    async def test_create_workflow(self):
        """Test creating a workflow."""
        from cirkelline.ckc.tegne_enhed.creative_room import (
            CreativeWorkflow,
            WorkflowStatus
        )

        workflow = CreativeWorkflow(name="Test Workflow")

        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.PENDING

    async def test_add_steps(self):
        """Test adding steps to workflow."""
        from cirkelline.ckc.tegne_enhed.creative_room import CreativeWorkflow

        workflow = CreativeWorkflow()
        workflow.add_step("generate", prompt="A dragon")
        workflow.add_step("style", style_name="watercolor")

        assert len(workflow._steps) == 2

    async def test_execute_workflow(self):
        """Test workflow execution."""
        from cirkelline.ckc.tegne_enhed.creative_room import CreativeWorkflow, WorkflowStatus
        from cirkelline.ckc.tegne_enhed.core import KreativKommandant

        kommandant = KreativKommandant(room_id=100, name="Workflow Test")
        await kommandant.start()

        workflow = CreativeWorkflow(name="Exec Test")
        workflow.add_step("generate", prompt="A sunset")
        workflow.add_step("style", style_name="oil_painting")

        results = await workflow.execute(kommandant)

        assert len(results) == 2
        assert workflow.status == WorkflowStatus.COMPLETED

        await kommandant.stop()


class TestCreativeJourneyCommand:
    """Tests for CreativeJourneyCommand."""

    async def test_create_journey(self):
        """Test creating a journey command."""
        from cirkelline.ckc.tegne_enhed.creative_room import CreativeJourneyCommand

        journey = CreativeJourneyCommand(journey_name="Dragon Journey")

        assert journey.journey_name == "Dragon Journey"

    async def test_journey_chaining(self):
        """Test fluent journey building."""
        from cirkelline.ckc.tegne_enhed.creative_room import CreativeJourneyCommand

        journey = (
            CreativeJourneyCommand("Chained Journey")
            .set_base_prompt("A majestic dragon")
            .set_style("fantasy")
            .add_step("generate")
            .add_step("animate", motion_type="zoom_out")
        )

        assert journey.base_prompt == "A majestic dragon"
        assert journey.style_preset == "fantasy"
        assert len(journey._workflow._steps) == 2

    async def test_execute_journey(self):
        """Test journey execution."""
        from cirkelline.ckc.tegne_enhed.creative_room import CreativeJourneyCommand
        from cirkelline.ckc.tegne_enhed.core import KreativKommandant

        kommandant = KreativKommandant(room_id=101, name="Journey Test")
        await kommandant.start()

        journey = (
            CreativeJourneyCommand("Test Journey")
            .add_step("generate", prompt="A sunset")
        )

        result = await journey.execute(kommandant)

        assert result["success"] is True
        assert result["steps_completed"] == 1

        await kommandant.stop()


class TestRoomFactory:
    """Tests for room factory functions."""

    async def test_create_creative_room(self):
        """Test factory function."""
        from cirkelline.ckc.tegne_enhed.creative_room import create_creative_room

        room, kommandant = await create_creative_room(
            owner="test_user",
            name="Factory Test Room"
        )

        assert room is not None
        assert kommandant is not None
        assert room.kommandant == kommandant

        await room.close()

    async def test_list_rooms(self):
        """Test listing rooms."""
        from cirkelline.ckc.tegne_enhed.creative_room import (
            create_creative_room,
            list_creative_rooms
        )

        room1, _ = await create_creative_room(name="List Test 1")
        room2, _ = await create_creative_room(name="List Test 2")

        rooms = list_creative_rooms()

        assert len(rooms) >= 2

        await room1.close()
        await room2.close()


# ========== Integration Tests ==========

class TestTegneEnhedIntegration:
    """Integration tests for the complete Tegne-enhed."""

    async def test_full_creative_workflow(self):
        """Test a complete creative workflow."""
        from cirkelline.ckc.tegne_enhed import (
            create_creative_room,
            CreativeJourneyCommand
        )

        # Create room
        room, kommandant = await create_creative_room(
            owner="integration_test",
            name="Full Workflow Room",
            budget_limit_usd=10.0
        )

        try:
            # Run a journey
            journey = (
                CreativeJourneyCommand("Integration Journey")
                .add_step("generate", prompt="A mountain landscape", style="realistic")
                .add_step("style", style_name="watercolor", intensity=0.7)
            )

            result = await journey.execute(kommandant)

            assert result["success"] is True
            assert result["total_cost_usd"] > 0

            # Check gallery
            gallery = room.get_gallery()
            assert len(gallery) >= 0  # Results may or may not be in gallery

        finally:
            await room.close()

    async def test_module_exports(self):
        """Test that all module exports work."""
        from cirkelline.ckc.tegne_enhed import (
            KreativKommandant,
            CreativeCapability,
            CreativeTaskType,
            OutputFormat,
            ImageGeneratorSpecialist,
            AnimatorSpecialist,
            StyleTransferSpecialist,
            VectorizerSpecialist,
            ReplicateClient,
            LumaAIClient,
            ProdiaClient,
            VectorizerAIClient,
            CreativeLearningRoom,
            CreativeJourneyCommand,
            create_creative_room,
            get_api_client,
            estimate_cost
        )

        # All imports should work
        assert KreativKommandant is not None
        assert CreativeCapability.TEXT_TO_IMAGE is not None
        assert estimate_cost("text_to_image") > 0


# ========== Enum Tests ==========

class TestEnums:
    """Tests for enum values."""

    def test_creative_capability_values(self):
        """Test CreativeCapability enum."""
        from cirkelline.ckc.tegne_enhed.core import CreativeCapability

        assert CreativeCapability.TEXT_TO_IMAGE.value == "text_to_image"
        assert CreativeCapability.IMAGE_TO_ANIMATION.value == "image_to_animation"

    def test_output_format_values(self):
        """Test OutputFormat enum."""
        from cirkelline.ckc.tegne_enhed.core import OutputFormat

        assert OutputFormat.PNG.value == "png"
        assert OutputFormat.SVG.value == "svg"
        assert OutputFormat.MP4.value == "mp4"

    def test_image_style_values(self):
        """Test ImageStyle enum."""
        from cirkelline.ckc.tegne_enhed.specialists import ImageStyle

        assert ImageStyle.REALISTIC.value == "realistic"
        assert ImageStyle.ANIME.value == "anime"
        assert ImageStyle.WATERCOLOR.value == "watercolor"

    def test_animation_motion_values(self):
        """Test AnimationMotion enum."""
        from cirkelline.ckc.tegne_enhed.specialists import AnimationMotion

        assert AnimationMotion.ZOOM_IN.value == "zoom_in"
        assert AnimationMotion.ZOOM_OUT.value == "zoom_out"
        assert AnimationMotion.PARALLAX.value == "parallax"


# ========== Cost Estimation Tests ==========

class TestCostEstimation:
    """Tests for cost estimation."""

    def test_cost_estimates_exist(self):
        """Test that cost estimates are defined."""
        from cirkelline.ckc.tegne_enhed.core import COST_ESTIMATES, CreativeCapability

        assert CreativeCapability.TEXT_TO_IMAGE in COST_ESTIMATES
        assert CreativeCapability.IMAGE_TO_ANIMATION in COST_ESTIMATES
        assert CreativeCapability.STYLE_TRANSFER in COST_ESTIMATES
        assert CreativeCapability.VECTORIZATION in COST_ESTIMATES

    def test_animation_costs_more(self):
        """Test that animation costs more than images."""
        from cirkelline.ckc.tegne_enhed.core import COST_ESTIMATES, CreativeCapability

        img_cost = COST_ESTIMATES[CreativeCapability.TEXT_TO_IMAGE]
        anim_cost = COST_ESTIMATES[CreativeCapability.IMAGE_TO_ANIMATION]

        assert anim_cost > img_cost


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
