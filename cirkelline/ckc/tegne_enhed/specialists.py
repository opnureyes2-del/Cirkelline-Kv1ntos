"""
CKC Tegne-enhed Specialister
============================

Kreative specialistagenter for forskellige kreative opgaver.

Specialister:
    - ImageGeneratorSpecialist: Text-to-image via Replicate/SDXL
    - AnimatorSpecialist: Image-to-animation via Luma AI
    - StyleTransferSpecialist: Style transfer via Prodia API
    - VectorizerSpecialist: Raster-to-vector via Vectorizer.AI
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from .core import (
    CreativeRequest,
    CreativeResult,
    CreativeCapability,
    CreativeTaskType,
    OutputFormat,
    COST_ESTIMATES
)

logger = logging.getLogger(__name__)


# ========== Enums ==========

class ImageStyle(Enum):
    """Forudefinerede billedstile."""
    REALISTIC = "realistic"
    FANTASY = "fantasy"
    ANIME = "anime"
    WATERCOLOR = "watercolor"
    OIL_PAINTING = "oil_painting"
    DIGITAL_ART = "digital_art"
    PIXEL_ART = "pixel_art"
    SKETCH = "sketch"
    MINIMALIST = "minimalist"
    CYBERPUNK = "cyberpunk"
    STEAMPUNK = "steampunk"
    ABSTRACT = "abstract"


class AnimationMotion(Enum):
    """Animationsbevægelser."""
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    ROTATE_CW = "rotate_cw"
    ROTATE_CCW = "rotate_ccw"
    PARALLAX = "parallax"
    FLOAT = "float"
    BREATHE = "breathe"
    CINEMATIC = "cinematic"


class VectorFormat(Enum):
    """Vektor output formater."""
    SVG = "svg"
    PDF = "pdf"
    EPS = "eps"
    AI = "ai"


class SpecialistStatus(Enum):
    """Specialist status."""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    MAINTENANCE = "maintenance"


# ========== Data Classes ==========

@dataclass
class SpecialistInfo:
    """Information om en specialist."""
    specialist_id: str
    specialist_type: str
    capabilities: List[CreativeCapability]
    status: SpecialistStatus
    current_load: int = 0
    max_load: int = 10
    avg_processing_time: float = 5.0
    success_rate: float = 0.95
    cost_per_operation: float = 0.01

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specialist_id": self.specialist_id,
            "specialist_type": self.specialist_type,
            "capabilities": [c.value for c in self.capabilities],
            "status": self.status.value,
            "current_load": self.current_load,
            "max_load": self.max_load,
            "avg_processing_time": self.avg_processing_time,
            "success_rate": self.success_rate,
            "cost_per_operation": self.cost_per_operation
        }


@dataclass
class ProcessingStats:
    """Statistik for specialist processing."""
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    total_cost_usd: float = 0.0
    total_time_seconds: float = 0.0
    last_processed: Optional[datetime] = None

    def update(self, success: bool, cost: float, duration: float) -> None:
        self.total_processed += 1
        if success:
            self.successful += 1
        else:
            self.failed += 1
        self.total_cost_usd += cost
        self.total_time_seconds += duration
        self.last_processed = datetime.now(timezone.utc)

    @property
    def success_rate(self) -> float:
        return self.successful / max(1, self.total_processed)

    @property
    def avg_time(self) -> float:
        return self.total_time_seconds / max(1, self.total_processed)


# ========== Base Specialist ==========

class CreativeSpecialist(ABC):
    """
    Base class for creative specialists.

    All creative specialists inherit from this and implement
    the specific processing logic for their domain.
    """

    def __init__(
        self,
        specialist_type: str,
        capabilities: List[CreativeCapability],
        max_load: int = 10
    ):
        self.specialist_id = f"{specialist_type}_{uuid.uuid4().hex[:8]}"
        self.specialist_type = specialist_type
        self.capabilities = capabilities
        self.status = SpecialistStatus.IDLE
        self.max_load = max_load
        self.current_load = 0

        # Statistics
        self.stats = ProcessingStats()

        # API client (injected)
        self._api_client = None

        # Processing queue
        self._queue: asyncio.Queue = asyncio.Queue()
        self._processing = False

        logger.info(f"CreativeSpecialist created: {self.specialist_type}")

    @abstractmethod
    async def process(self, request: CreativeRequest) -> CreativeResult:
        """Process a creative request."""
        pass

    def can_handle(self, capability: CreativeCapability) -> bool:
        """Check if specialist can handle a capability."""
        return capability in self.capabilities

    def is_available(self) -> bool:
        """Check if specialist is available for work."""
        return (
            self.status == SpecialistStatus.IDLE and
            self.current_load < self.max_load
        )

    def get_info(self) -> SpecialistInfo:
        """Get specialist info."""
        return SpecialistInfo(
            specialist_id=self.specialist_id,
            specialist_type=self.specialist_type,
            capabilities=self.capabilities,
            status=self.status,
            current_load=self.current_load,
            max_load=self.max_load,
            avg_processing_time=self.stats.avg_time,
            success_rate=self.stats.success_rate,
            cost_per_operation=self._estimate_cost()
        )

    def _estimate_cost(self) -> float:
        """Estimate cost per operation."""
        if self.capabilities:
            costs = [COST_ESTIMATES.get(cap, 0.01) for cap in self.capabilities]
            return sum(costs) / len(costs)
        return 0.01

    async def _track_processing(
        self,
        request: CreativeRequest,
        processor: callable
    ) -> CreativeResult:
        """Track processing with stats."""
        self.current_load += 1
        self.status = SpecialistStatus.PROCESSING
        start_time = datetime.now(timezone.utc)

        try:
            result = await processor(request)

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.stats.update(result.success, result.cost_usd, duration)

            return result

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.stats.update(False, 0.0, duration)

            return CreativeResult(
                request_id=request.request_id,
                success=False,
                task_type=request.task_type,
                capability=request.capability,
                error=str(e),
                specialist_used=self.specialist_id
            )

        finally:
            self.current_load -= 1
            if self.current_load == 0:
                self.status = SpecialistStatus.IDLE


# ========== Image Generator Specialist ==========

class ImageGeneratorSpecialist(CreativeSpecialist):
    """
    Specialist for image generation.

    Uses Replicate API with SDXL for high-quality image generation.
    Supports: text-to-image, image-to-image, upscaling, inpainting.
    """

    # Style prompts for different styles
    STYLE_PROMPTS = {
        ImageStyle.REALISTIC: "photorealistic, hyperrealistic, 8k uhd, detailed",
        ImageStyle.FANTASY: "fantasy art, epic, magical, ethereal lighting",
        ImageStyle.ANIME: "anime style, manga, vibrant colors, clean lines",
        ImageStyle.WATERCOLOR: "watercolor painting, soft edges, artistic, wet on wet",
        ImageStyle.OIL_PAINTING: "oil painting, thick brushstrokes, classical, rich colors",
        ImageStyle.DIGITAL_ART: "digital art, concept art, trending on artstation",
        ImageStyle.PIXEL_ART: "pixel art, 16-bit, retro game style, crisp pixels",
        ImageStyle.SKETCH: "pencil sketch, detailed drawing, line art, artistic",
        ImageStyle.MINIMALIST: "minimalist, simple, clean, modern, geometric",
        ImageStyle.CYBERPUNK: "cyberpunk, neon lights, futuristic, dark atmosphere",
        ImageStyle.STEAMPUNK: "steampunk, Victorian, brass, gears, industrial",
        ImageStyle.ABSTRACT: "abstract art, non-representational, expressive, colorful"
    }

    # Negative prompts for quality
    DEFAULT_NEGATIVE = (
        "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
        "watermark, text, signature, cropped, worst quality, jpeg artifacts"
    )

    def __init__(self, max_load: int = 5):
        super().__init__(
            specialist_type="image-generator",
            capabilities=[
                CreativeCapability.TEXT_TO_IMAGE,
                CreativeCapability.IMAGE_TO_IMAGE,
                CreativeCapability.UPSCALING,
                CreativeCapability.INPAINTING,
                CreativeCapability.OUTPAINTING
            ],
            max_load=max_load
        )

        # Model configuration
        self.model_id = "sdxl"
        self.default_size = "1024x1024"
        self.default_steps = 30
        self.default_guidance = 7.5

    async def process(self, request: CreativeRequest) -> CreativeResult:
        """Process image generation request."""
        return await self._track_processing(request, self._generate)

    async def _generate(self, request: CreativeRequest) -> CreativeResult:
        """Internal generation logic."""
        # Enhance prompt with style
        enhanced_prompt = self._enhance_prompt(request)

        # Prepare parameters
        params = {
            "prompt": enhanced_prompt,
            "negative_prompt": request.negative_prompt or self.DEFAULT_NEGATIVE,
            "width": int(request.output_size.split("x")[0]),
            "height": int(request.output_size.split("x")[1]),
            "num_inference_steps": request.num_inference_steps or self.default_steps,
            "guidance_scale": request.guidance_scale or self.default_guidance,
            "num_outputs": request.num_outputs
        }

        if request.seed:
            params["seed"] = request.seed

        # Call API (mock for MVP)
        if self._api_client:
            response = await self._api_client.generate_image(params)
        else:
            response = await self._mock_generate(request, params)

        return response

    def _enhance_prompt(self, request: CreativeRequest) -> str:
        """Enhance prompt with style modifiers."""
        prompt = request.prompt

        # Add style modifiers
        if request.style_config:
            style_name = request.style_config.style_name
            try:
                style = ImageStyle(style_name)
                style_prompt = self.STYLE_PROMPTS.get(style, "")
                if style_prompt:
                    prompt = f"{prompt}, {style_prompt}"
            except ValueError:
                # Custom style name
                prompt = f"{prompt}, {style_name} style"

        return prompt

    async def _mock_generate(
        self,
        request: CreativeRequest,
        params: Dict[str, Any]
    ) -> CreativeResult:
        """Mock generation for MVP testing."""
        await asyncio.sleep(1.0)  # Simulate API latency

        output_paths = []
        output_urls = []

        for i in range(request.num_outputs):
            path = f"/tmp/creative/{request.request_id}_{i}.png"
            url = f"https://cdn.cirkelline.com/creative/{request.request_id}_{i}.png"
            output_paths.append(path)
            output_urls.append(url)

        cost = COST_ESTIMATES[CreativeCapability.TEXT_TO_IMAGE] * request.num_outputs

        return CreativeResult(
            request_id=request.request_id,
            success=True,
            task_type=request.task_type,
            capability=request.capability,
            output_paths=output_paths,
            output_urls=output_urls,
            output_format=OutputFormat.PNG,
            quality_score=0.85,
            aesthetic_score=0.82,
            cost_usd=cost,
            api_calls=1,
            specialist_used=self.specialist_id,
            model_used=self.model_id,
            metadata={
                "prompt_used": params["prompt"],
                "params": params
            }
        )


# ========== Animator Specialist ==========

class AnimatorSpecialist(CreativeSpecialist):
    """
    Specialist for animation.

    Uses Luma AI Dream Machine for image-to-video animation.
    """

    # Motion presets
    MOTION_PRESETS = {
        AnimationMotion.ZOOM_IN: {"scale_start": 1.0, "scale_end": 1.3, "rotation": 0},
        AnimationMotion.ZOOM_OUT: {"scale_start": 1.3, "scale_end": 1.0, "rotation": 0},
        AnimationMotion.PAN_LEFT: {"translate_x": -100, "translate_y": 0},
        AnimationMotion.PAN_RIGHT: {"translate_x": 100, "translate_y": 0},
        AnimationMotion.PAN_UP: {"translate_x": 0, "translate_y": -100},
        AnimationMotion.PAN_DOWN: {"translate_x": 0, "translate_y": 100},
        AnimationMotion.ROTATE_CW: {"rotation": 15, "scale_start": 1.0, "scale_end": 1.0},
        AnimationMotion.ROTATE_CCW: {"rotation": -15, "scale_start": 1.0, "scale_end": 1.0},
        AnimationMotion.PARALLAX: {"parallax_depth": 0.3, "motion": "lateral"},
        AnimationMotion.FLOAT: {"float_amplitude": 10, "float_speed": 0.5},
        AnimationMotion.BREATHE: {"scale_variance": 0.05, "cycle_speed": 2.0},
        AnimationMotion.CINEMATIC: {"camera_path": "smooth_arc", "focus_shift": True}
    }

    def __init__(self, max_load: int = 3):
        super().__init__(
            specialist_type="animator",
            capabilities=[
                CreativeCapability.IMAGE_TO_ANIMATION
            ],
            max_load=max_load
        )

        self.model_id = "luma-dream-machine"
        self.default_duration = 5.0
        self.default_fps = 24

    async def process(self, request: CreativeRequest) -> CreativeResult:
        """Process animation request."""
        return await self._track_processing(request, self._animate)

    async def _animate(self, request: CreativeRequest) -> CreativeResult:
        """Internal animation logic."""
        if not request.input_image:
            return CreativeResult(
                request_id=request.request_id,
                success=False,
                task_type=request.task_type,
                capability=request.capability,
                error="No input image provided for animation",
                specialist_used=self.specialist_id
            )

        # Get animation config
        config = request.animation_config
        if not config:
            from .core import AnimationConfig
            config = AnimationConfig()

        # Get motion preset
        try:
            motion = AnimationMotion(config.motion_type)
            motion_params = self.MOTION_PRESETS.get(motion, {})
        except ValueError:
            motion_params = {}

        params = {
            "image_path": request.input_image,
            "duration": config.duration_seconds,
            "fps": config.fps,
            "motion": config.motion_type,
            "motion_params": motion_params,
            "loop": config.loop
        }

        # Call API (mock for MVP)
        if self._api_client:
            response = await self._api_client.create_animation(params)
        else:
            response = await self._mock_animate(request, params)

        return response

    async def _mock_animate(
        self,
        request: CreativeRequest,
        params: Dict[str, Any]
    ) -> CreativeResult:
        """Mock animation for MVP testing."""
        await asyncio.sleep(3.0)  # Animation takes longer

        output_path = f"/tmp/creative/{request.request_id}.mp4"
        output_url = f"https://cdn.cirkelline.com/creative/{request.request_id}.mp4"

        cost = COST_ESTIMATES[CreativeCapability.IMAGE_TO_ANIMATION]

        return CreativeResult(
            request_id=request.request_id,
            success=True,
            task_type=request.task_type,
            capability=request.capability,
            output_paths=[output_path],
            output_urls=[output_url],
            output_format=OutputFormat.MP4,
            quality_score=0.80,
            aesthetic_score=0.78,
            cost_usd=cost,
            api_calls=1,
            specialist_used=self.specialist_id,
            model_used=self.model_id,
            metadata={
                "motion_type": params["motion"],
                "duration": params["duration"],
                "fps": params["fps"]
            }
        )


# ========== Style Transfer Specialist ==========

class StyleTransferSpecialist(CreativeSpecialist):
    """
    Specialist for style transfer.

    Uses Prodia API for fast neural style transfer.
    """

    # Pre-trained style models
    STYLE_MODELS = {
        "van_gogh": "Van Gogh's Starry Night style",
        "monet": "Claude Monet impressionist style",
        "picasso": "Pablo Picasso cubist style",
        "anime": "Japanese anime style",
        "watercolor": "Watercolor painting style",
        "oil_painting": "Classical oil painting style",
        "sketch": "Pencil sketch style",
        "pop_art": "Andy Warhol pop art style",
        "art_deco": "Art Deco geometric style",
        "gothic": "Gothic dark fantasy style"
    }

    def __init__(self, max_load: int = 10):
        super().__init__(
            specialist_type="style-transfer",
            capabilities=[
                CreativeCapability.STYLE_TRANSFER
            ],
            max_load=max_load
        )

        self.model_id = "prodia-style-transfer"
        self.default_intensity = 0.8

    async def process(self, request: CreativeRequest) -> CreativeResult:
        """Process style transfer request."""
        return await self._track_processing(request, self._stylize)

    async def _stylize(self, request: CreativeRequest) -> CreativeResult:
        """Internal style transfer logic."""
        if not request.input_image:
            return CreativeResult(
                request_id=request.request_id,
                success=False,
                task_type=request.task_type,
                capability=request.capability,
                error="No input image provided for style transfer",
                specialist_used=self.specialist_id
            )

        # Get style config
        config = request.style_config
        if not config:
            return CreativeResult(
                request_id=request.request_id,
                success=False,
                task_type=request.task_type,
                capability=request.capability,
                error="No style configuration provided",
                specialist_used=self.specialist_id
            )

        # Validate style
        style_name = config.style_name.lower()
        if style_name not in self.STYLE_MODELS and not config.reference_image:
            # Use custom style name as-is
            pass

        params = {
            "image_path": request.input_image,
            "style_name": style_name,
            "intensity": config.intensity,
            "preserve_content": config.preserve_content,
            "reference_image": config.reference_image
        }

        # Call API (mock for MVP)
        if self._api_client:
            response = await self._api_client.transfer_style(params)
        else:
            response = await self._mock_stylize(request, params)

        return response

    async def _mock_stylize(
        self,
        request: CreativeRequest,
        params: Dict[str, Any]
    ) -> CreativeResult:
        """Mock style transfer for MVP testing."""
        await asyncio.sleep(0.5)  # Prodia is fast

        output_path = f"/tmp/creative/{request.request_id}_styled.png"
        output_url = f"https://cdn.cirkelline.com/creative/{request.request_id}_styled.png"

        cost = COST_ESTIMATES[CreativeCapability.STYLE_TRANSFER]

        return CreativeResult(
            request_id=request.request_id,
            success=True,
            task_type=request.task_type,
            capability=request.capability,
            output_paths=[output_path],
            output_urls=[output_url],
            output_format=OutputFormat.PNG,
            quality_score=0.88,
            aesthetic_score=0.85,
            cost_usd=cost,
            api_calls=1,
            specialist_used=self.specialist_id,
            model_used=self.model_id,
            metadata={
                "style_applied": params["style_name"],
                "intensity": params["intensity"]
            }
        )


# ========== Vectorizer Specialist ==========

class VectorizerSpecialist(CreativeSpecialist):
    """
    Specialist for vectorization.

    Uses Vectorizer.AI for raster-to-vector conversion.
    """

    # Detail presets
    DETAIL_PRESETS = {
        "low": {"max_colors": 8, "path_simplification": 0.8},
        "medium": {"max_colors": 32, "path_simplification": 0.5},
        "high": {"max_colors": 128, "path_simplification": 0.2},
        "photo": {"max_colors": 256, "path_simplification": 0.1}
    }

    def __init__(self, max_load: int = 5):
        super().__init__(
            specialist_type="vectorizer",
            capabilities=[
                CreativeCapability.VECTORIZATION
            ],
            max_load=max_load
        )

        self.model_id = "vectorizer-ai"
        self.default_format = VectorFormat.SVG

    async def process(self, request: CreativeRequest) -> CreativeResult:
        """Process vectorization request."""
        return await self._track_processing(request, self._vectorize)

    async def _vectorize(self, request: CreativeRequest) -> CreativeResult:
        """Internal vectorization logic."""
        if not request.input_image:
            return CreativeResult(
                request_id=request.request_id,
                success=False,
                task_type=request.task_type,
                capability=request.capability,
                error="No input image provided for vectorization",
                specialist_used=self.specialist_id
            )

        # Get detail level
        detail_level = request.metadata.get("detail_level", "medium")
        detail_params = self.DETAIL_PRESETS.get(detail_level, self.DETAIL_PRESETS["medium"])

        # Determine output format
        output_format = request.output_format
        if output_format not in [OutputFormat.SVG, OutputFormat.PDF]:
            output_format = OutputFormat.SVG

        params = {
            "image_path": request.input_image,
            "output_format": output_format.value,
            "detail_level": detail_level,
            **detail_params
        }

        # Call API (mock for MVP)
        if self._api_client:
            response = await self._api_client.vectorize(params)
        else:
            response = await self._mock_vectorize(request, params)

        return response

    async def _mock_vectorize(
        self,
        request: CreativeRequest,
        params: Dict[str, Any]
    ) -> CreativeResult:
        """Mock vectorization for MVP testing."""
        await asyncio.sleep(2.0)  # Vectorization takes time

        ext = params["output_format"]
        output_path = f"/tmp/creative/{request.request_id}.{ext}"
        output_url = f"https://cdn.cirkelline.com/creative/{request.request_id}.{ext}"

        cost = COST_ESTIMATES[CreativeCapability.VECTORIZATION]

        return CreativeResult(
            request_id=request.request_id,
            success=True,
            task_type=request.task_type,
            capability=request.capability,
            output_paths=[output_path],
            output_urls=[output_url],
            output_format=OutputFormat(ext) if ext in ["svg", "pdf"] else OutputFormat.SVG,
            quality_score=0.90,
            aesthetic_score=0.85,
            cost_usd=cost,
            api_calls=1,
            specialist_used=self.specialist_id,
            model_used=self.model_id,
            metadata={
                "detail_level": params["detail_level"],
                "output_format": params["output_format"]
            }
        )


# ========== Factory Functions ==========

_specialists: Dict[str, CreativeSpecialist] = {}


def get_creative_specialist(specialist_type: str) -> Optional[CreativeSpecialist]:
    """Get or create a creative specialist by type."""
    if specialist_type in _specialists:
        return _specialists[specialist_type]

    # Create new specialist
    if specialist_type == "image-generator":
        specialist = ImageGeneratorSpecialist()
    elif specialist_type == "animator":
        specialist = AnimatorSpecialist()
    elif specialist_type == "style-transfer":
        specialist = StyleTransferSpecialist()
    elif specialist_type == "vectorizer":
        specialist = VectorizerSpecialist()
    else:
        logger.warning(f"Unknown specialist type: {specialist_type}")
        return None

    _specialists[specialist_type] = specialist
    return specialist


def list_creative_specialists() -> List[SpecialistInfo]:
    """List all available creative specialists."""
    # Ensure all specialists are created
    for stype in ["image-generator", "animator", "style-transfer", "vectorizer"]:
        get_creative_specialist(stype)

    return [s.get_info() for s in _specialists.values()]


logger.info("CKC Tegne-enhed Specialists module loaded")
