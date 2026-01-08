"""
CKC Kreativ Kommandant (Creative Commander)
============================================

Den kreative kommandant der orkestrerer alle kreative opgaver.

Ansvar:
    - Modtage kreative forespørgsler (billeder, animationer, stil, vektor)
    - Analysere og optimere prompts
    - Koordinere med kreative specialister
    - Håndtere multi-step workflows (f.eks. generer -> animator -> stil)
    - Omkostningsestimering og -styring
    - Kvalitetskontrol og iteration

Integration:
    - Replicate API (SDXL) til text-to-image
    - Luma AI til animation
    - Prodia API til style transfer
    - Vectorizer.AI til vektorisering
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


# ========== Enums ==========

class CreativeCapability(Enum):
    """Kreative evner i Tegne-enheden."""
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"
    IMAGE_TO_ANIMATION = "image_to_animation"
    STYLE_TRANSFER = "style_transfer"
    VECTORIZATION = "vectorization"
    UPSCALING = "upscaling"
    INPAINTING = "inpainting"
    OUTPAINTING = "outpainting"


class CreativeTaskType(Enum):
    """Typer af kreative opgaver."""
    GENERATE = "generate"
    TRANSFORM = "transform"
    ANIMATE = "animate"
    STYLIZE = "stylize"
    VECTORIZE = "vectorize"
    COMPOSITE = "composite"  # Multi-step workflow


class OutputFormat(Enum):
    """Output formater."""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
    MP4 = "mp4"
    SVG = "svg"
    PDF = "pdf"


class TaskPriority(Enum):
    """Opgaveprioriteter."""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class KommandantStatus(Enum):
    """Status for Kreativ Kommandant."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PROCESSING = "processing"
    DELEGATING = "delegating"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    ERROR = "error"
    STOPPED = "stopped"


# ========== Data Classes ==========

@dataclass
class StyleConfig:
    """Konfiguration for stil-parametre."""
    style_name: str
    intensity: float = 0.8  # 0.0 - 1.0
    preserve_content: float = 0.5  # 0.0 - 1.0
    color_palette: Optional[List[str]] = None
    reference_image: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "style_name": self.style_name,
            "intensity": self.intensity,
            "preserve_content": self.preserve_content,
            "color_palette": self.color_palette,
            "reference_image": self.reference_image
        }


@dataclass
class AnimationConfig:
    """Konfiguration for animation."""
    motion_type: str = "zoom_out"  # zoom_in, zoom_out, pan_left, pan_right, rotate
    duration_seconds: float = 5.0
    fps: int = 24
    loop: bool = False
    easing: str = "ease_in_out"
    camera_movement: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "motion_type": self.motion_type,
            "duration_seconds": self.duration_seconds,
            "fps": self.fps,
            "loop": self.loop,
            "easing": self.easing,
            "camera_movement": self.camera_movement
        }


@dataclass
class CreativeRequest:
    """En kreativ forespørgsel."""
    request_id: str
    task_type: CreativeTaskType
    capability: CreativeCapability
    prompt: str
    priority: TaskPriority = TaskPriority.NORMAL

    # Input
    input_image: Optional[str] = None
    input_images: List[str] = field(default_factory=list)

    # Output
    output_format: OutputFormat = OutputFormat.PNG
    output_size: str = "1024x1024"
    output_path: Optional[str] = None

    # Style & Animation
    style_config: Optional[StyleConfig] = None
    animation_config: Optional[AnimationConfig] = None

    # Generation params
    num_outputs: int = 1
    seed: Optional[int] = None
    negative_prompt: Optional[str] = None
    guidance_scale: float = 7.5
    num_inference_steps: int = 30

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_type": self.task_type.value,
            "capability": self.capability.value,
            "prompt": self.prompt,
            "priority": self.priority.value,
            "input_image": self.input_image,
            "output_format": self.output_format.value,
            "output_size": self.output_size,
            "num_outputs": self.num_outputs,
            "style_config": self.style_config.to_dict() if self.style_config else None,
            "animation_config": self.animation_config.to_dict() if self.animation_config else None,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class CreativeResult:
    """Resultat af en kreativ opgave."""
    request_id: str
    success: bool
    task_type: CreativeTaskType
    capability: CreativeCapability

    # Output
    output_paths: List[str] = field(default_factory=list)
    output_urls: List[str] = field(default_factory=list)
    output_format: OutputFormat = OutputFormat.PNG

    # Quality metrics
    quality_score: float = 0.0  # 0.0 - 1.0
    aesthetic_score: float = 0.0  # 0.0 - 1.0

    # Cost & Performance
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    api_calls: int = 0

    # Metadata
    specialist_used: str = ""
    model_used: str = ""
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "success": self.success,
            "task_type": self.task_type.value,
            "capability": self.capability.value,
            "output_paths": self.output_paths,
            "output_urls": self.output_urls,
            "output_format": self.output_format.value,
            "quality_score": self.quality_score,
            "aesthetic_score": self.aesthetic_score,
            "cost_usd": self.cost_usd,
            "duration_seconds": self.duration_seconds,
            "specialist_used": self.specialist_used,
            "model_used": self.model_used,
            "error": self.error,
            "completed_at": self.completed_at.isoformat()
        }


@dataclass
class AuditEntry:
    """Audit log entry for creative operations."""
    entry_id: str
    timestamp: datetime
    action: str
    actor: str
    target: str
    details: Dict[str, Any]
    outcome: str
    cost_usd: float = 0.0
    severity: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "actor": self.actor,
            "target": self.target,
            "details": self.details,
            "outcome": self.outcome,
            "cost_usd": self.cost_usd,
            "severity": self.severity
        }


# ========== Capability Mapping ==========

CAPABILITY_TO_SPECIALIST = {
    CreativeCapability.TEXT_TO_IMAGE: "image-generator",
    CreativeCapability.IMAGE_TO_IMAGE: "image-generator",
    CreativeCapability.IMAGE_TO_ANIMATION: "animator",
    CreativeCapability.STYLE_TRANSFER: "style-transfer",
    CreativeCapability.VECTORIZATION: "vectorizer",
    CreativeCapability.UPSCALING: "image-generator",
    CreativeCapability.INPAINTING: "image-generator",
    CreativeCapability.OUTPAINTING: "image-generator",
}

SPECIALIST_CAPABILITIES = {
    "image-generator": [
        CreativeCapability.TEXT_TO_IMAGE,
        CreativeCapability.IMAGE_TO_IMAGE,
        CreativeCapability.UPSCALING,
        CreativeCapability.INPAINTING,
        CreativeCapability.OUTPAINTING,
    ],
    "animator": [
        CreativeCapability.IMAGE_TO_ANIMATION,
    ],
    "style-transfer": [
        CreativeCapability.STYLE_TRANSFER,
    ],
    "vectorizer": [
        CreativeCapability.VECTORIZATION,
    ],
}

# Cost estimates per operation (USD)
COST_ESTIMATES = {
    CreativeCapability.TEXT_TO_IMAGE: 0.01,
    CreativeCapability.IMAGE_TO_IMAGE: 0.015,
    CreativeCapability.IMAGE_TO_ANIMATION: 0.75,
    CreativeCapability.STYLE_TRANSFER: 0.005,
    CreativeCapability.VECTORIZATION: 0.10,
    CreativeCapability.UPSCALING: 0.02,
    CreativeCapability.INPAINTING: 0.02,
    CreativeCapability.OUTPAINTING: 0.03,
}


# ========== Kreativ Kommandant ==========

class KreativKommandant:
    """
    Kreativ Kommandant - Orkestrerer alle kreative opgaver.

    Hovedansvar:
        1. Modtage og analysere kreative forespørgsler
        2. Optimere prompts for bedre resultater
        3. Delegere til rette specialist
        4. Håndtere multi-step workflows
        5. Kvalitetskontrol og iteration
        6. Omkostningsstyring
    """

    def __init__(
        self,
        room_id: int,
        name: str = "Kreativ Kommandant",
        description: str = "",
        budget_limit_usd: float = 10.0,
        auto_optimize_prompts: bool = True
    ):
        self.kommandant_id = f"kreativ_{room_id}_{uuid.uuid4().hex[:8]}"
        self.room_id = room_id
        self.name = name
        self.description = description
        self.budget_limit_usd = budget_limit_usd
        self.auto_optimize_prompts = auto_optimize_prompts

        # Status
        self.status = KommandantStatus.INITIALIZING
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)

        # Statistics
        self.requests_received = 0
        self.requests_completed = 0
        self.requests_failed = 0
        self.total_cost_usd = 0.0
        self.images_generated = 0
        self.animations_created = 0
        self.styles_applied = 0
        self.vectors_created = 0

        # Internal storage
        self._active_requests: Dict[str, CreativeRequest] = {}
        self._completed_results: Dict[str, CreativeResult] = {}
        self._audit_log: List[AuditEntry] = []

        # Specialists registry
        self._specialists: Dict[str, Any] = {}

        # Quality thresholds
        self._min_quality_score = 0.6
        self._max_retries = 2

        # API clients (lazy loaded)
        self._api_clients: Dict[str, Any] = {}

        # Running state
        self._running = False
        self._request_queue: asyncio.Queue = asyncio.Queue()

        logger.info(f"KreativKommandant created: {self.name} (Room {room_id})")

    # ========== Lifecycle ==========

    async def start(self) -> bool:
        """Start Kreativ Kommandant."""
        if self._running:
            logger.warning(f"KreativKommandant {self.name} already running")
            return True

        try:
            self._audit("start", "kommandant", "system", {}, "initiated")

            # Initialize specialists
            await self._initialize_specialists()

            # Initialize API clients
            await self._initialize_api_clients()

            self._running = True
            self.status = KommandantStatus.IDLE
            self.last_activity = datetime.now(timezone.utc)

            self._audit("start", "kommandant", "system", {
                "specialists_count": len(self._specialists),
                "api_clients_count": len(self._api_clients)
            }, "success")

            logger.info(f"KreativKommandant {self.name} started successfully")
            return True

        except Exception as e:
            self.status = KommandantStatus.ERROR
            self._audit("start", "kommandant", "system", {"error": str(e)}, "failure", severity="error")
            logger.error(f"Failed to start KreativKommandant {self.name}: {e}")
            return False

    async def stop(self) -> None:
        """Stop Kreativ Kommandant."""
        if not self._running:
            return

        self._audit("stop", "kommandant", "system", {
            "total_cost": self.total_cost_usd
        }, "initiated")

        self._running = False

        # Cleanup API clients
        for client in self._api_clients.values():
            if hasattr(client, 'close'):
                await client.close()

        self.status = KommandantStatus.STOPPED
        self._audit("stop", "kommandant", "system", {}, "success")
        logger.info(f"KreativKommandant {self.name} stopped")

    # ========== Main Operations ==========

    async def generate_image(
        self,
        prompt: str,
        style: Optional[str] = None,
        size: str = "1024x1024",
        num_images: int = 1,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        **kwargs
    ) -> CreativeResult:
        """
        Generer billede fra tekstprompt.

        Args:
            prompt: Beskrivelse af ønsket billede
            style: Stil (fantasy, realistic, anime, etc.)
            size: Output størrelse (1024x1024, 768x1024, etc.)
            num_images: Antal billeder at generere
            negative_prompt: Hvad der IKKE skal være i billedet
            seed: Seed for reproducerbarhed

        Returns:
            CreativeResult med output paths/URLs
        """
        request = CreativeRequest(
            request_id=f"img_{uuid.uuid4().hex[:12]}",
            task_type=CreativeTaskType.GENERATE,
            capability=CreativeCapability.TEXT_TO_IMAGE,
            prompt=prompt,
            output_size=size,
            num_outputs=num_images,
            negative_prompt=negative_prompt,
            seed=seed,
            metadata={"style": style, **kwargs}
        )

        if style:
            request.style_config = StyleConfig(style_name=style)

        return await self._execute_request(request)

    async def create_animation(
        self,
        image_path: str,
        motion_type: str = "zoom_out",
        duration_seconds: float = 5.0,
        fps: int = 24,
        **kwargs
    ) -> CreativeResult:
        """
        Skab animation fra et stillbillede.

        Args:
            image_path: Sti til input billede
            motion_type: Type bevægelse (zoom_in, zoom_out, pan_left, etc.)
            duration_seconds: Varighed i sekunder
            fps: Frames per second

        Returns:
            CreativeResult med animation path/URL
        """
        request = CreativeRequest(
            request_id=f"anim_{uuid.uuid4().hex[:12]}",
            task_type=CreativeTaskType.ANIMATE,
            capability=CreativeCapability.IMAGE_TO_ANIMATION,
            prompt=f"Animate image with {motion_type} motion",
            input_image=image_path,
            output_format=OutputFormat.MP4,
            animation_config=AnimationConfig(
                motion_type=motion_type,
                duration_seconds=duration_seconds,
                fps=fps
            ),
            metadata=kwargs
        )

        return await self._execute_request(request)

    async def apply_style(
        self,
        image_path: str,
        style_name: str,
        intensity: float = 0.8,
        reference_image: Optional[str] = None,
        **kwargs
    ) -> CreativeResult:
        """
        Anvend stil på et billede.

        Args:
            image_path: Sti til input billede
            style_name: Navn på stil (van_gogh, anime, watercolor, etc.)
            intensity: Styrke af stil (0.0 - 1.0)
            reference_image: Optional reference billede for stil

        Returns:
            CreativeResult med stiliseret billede
        """
        request = CreativeRequest(
            request_id=f"style_{uuid.uuid4().hex[:12]}",
            task_type=CreativeTaskType.STYLIZE,
            capability=CreativeCapability.STYLE_TRANSFER,
            prompt=f"Apply {style_name} style",
            input_image=image_path,
            style_config=StyleConfig(
                style_name=style_name,
                intensity=intensity,
                reference_image=reference_image
            ),
            metadata=kwargs
        )

        return await self._execute_request(request)

    async def vectorize(
        self,
        image_path: str,
        output_format: str = "svg",
        detail_level: str = "medium",
        **kwargs
    ) -> CreativeResult:
        """
        Konverter rasterbillede til vektor.

        Args:
            image_path: Sti til input billede
            output_format: Output format (svg, pdf, eps)
            detail_level: Detaljeniveau (low, medium, high)

        Returns:
            CreativeResult med vektor fil
        """
        format_map = {"svg": OutputFormat.SVG, "pdf": OutputFormat.PDF}

        request = CreativeRequest(
            request_id=f"vec_{uuid.uuid4().hex[:12]}",
            task_type=CreativeTaskType.VECTORIZE,
            capability=CreativeCapability.VECTORIZATION,
            prompt=f"Vectorize image with {detail_level} detail",
            input_image=image_path,
            output_format=format_map.get(output_format, OutputFormat.SVG),
            metadata={"detail_level": detail_level, **kwargs}
        )

        return await self._execute_request(request)

    async def creative_workflow(
        self,
        steps: List[Dict[str, Any]]
    ) -> List[CreativeResult]:
        """
        Udfør et multi-step kreativt workflow.

        Args:
            steps: Liste af trin, hver med 'action' og parametre
                   Eksempel: [
                       {"action": "generate", "prompt": "A dragon"},
                       {"action": "style", "style_name": "watercolor"},
                       {"action": "animate", "motion_type": "zoom_out"}
                   ]

        Returns:
            Liste af CreativeResult for hvert trin
        """
        results = []
        current_image = None

        for i, step in enumerate(steps):
            action = step.get("action")
            self._audit("workflow_step", "workflow", f"step_{i}", {
                "action": action,
                "step_index": i
            }, "started")

            try:
                if action == "generate":
                    result = await self.generate_image(
                        prompt=step.get("prompt", ""),
                        style=step.get("style"),
                        size=step.get("size", "1024x1024"),
                        **{k: v for k, v in step.items() if k not in ["action", "prompt", "style", "size"]}
                    )
                    if result.success and result.output_paths:
                        current_image = result.output_paths[0]

                elif action == "style":
                    if not current_image and not step.get("image_path"):
                        raise ValueError("No input image for style transfer")
                    result = await self.apply_style(
                        image_path=step.get("image_path", current_image),
                        style_name=step.get("style_name", "default"),
                        intensity=step.get("intensity", 0.8),
                        **{k: v for k, v in step.items() if k not in ["action", "image_path", "style_name", "intensity"]}
                    )
                    if result.success and result.output_paths:
                        current_image = result.output_paths[0]

                elif action == "animate":
                    if not current_image and not step.get("image_path"):
                        raise ValueError("No input image for animation")
                    result = await self.create_animation(
                        image_path=step.get("image_path", current_image),
                        motion_type=step.get("motion_type", "zoom_out"),
                        duration_seconds=step.get("duration_seconds", 5.0),
                        **{k: v for k, v in step.items() if k not in ["action", "image_path", "motion_type", "duration_seconds"]}
                    )

                elif action == "vectorize":
                    if not current_image and not step.get("image_path"):
                        raise ValueError("No input image for vectorization")
                    result = await self.vectorize(
                        image_path=step.get("image_path", current_image),
                        output_format=step.get("output_format", "svg"),
                        **{k: v for k, v in step.items() if k not in ["action", "image_path", "output_format"]}
                    )

                else:
                    raise ValueError(f"Unknown action: {action}")

                results.append(result)

                self._audit("workflow_step", "workflow", f"step_{i}", {
                    "action": action,
                    "success": result.success
                }, "completed" if result.success else "failed")

            except Exception as e:
                error_result = CreativeResult(
                    request_id=f"err_{uuid.uuid4().hex[:8]}",
                    success=False,
                    task_type=CreativeTaskType.COMPOSITE,
                    capability=CreativeCapability.TEXT_TO_IMAGE,
                    error=str(e)
                )
                results.append(error_result)

                self._audit("workflow_step", "workflow", f"step_{i}", {
                    "action": action,
                    "error": str(e)
                }, "error", severity="error")

        return results

    # ========== Internal Processing ==========

    async def _execute_request(self, request: CreativeRequest) -> CreativeResult:
        """Execute a creative request."""
        self.requests_received += 1
        self.last_activity = datetime.now(timezone.utc)
        self._active_requests[request.request_id] = request

        start_time = datetime.now(timezone.utc)

        self._audit("execute_request", "request", request.request_id, {
            "task_type": request.task_type.value,
            "capability": request.capability.value
        }, "started")

        try:
            # Check budget
            estimated_cost = COST_ESTIMATES.get(request.capability, 0.05)
            if self.total_cost_usd + estimated_cost > self.budget_limit_usd:
                raise ValueError(f"Budget limit exceeded: ${self.total_cost_usd:.2f} + ${estimated_cost:.2f} > ${self.budget_limit_usd:.2f}")

            self.status = KommandantStatus.PROCESSING

            # Optimize prompt if enabled
            if self.auto_optimize_prompts:
                request = await self._optimize_prompt(request)

            # Delegate to specialist
            self.status = KommandantStatus.DELEGATING
            specialist_id = CAPABILITY_TO_SPECIALIST.get(request.capability)

            if specialist_id not in self._specialists:
                # Use mock specialist for MVP
                result = await self._execute_with_mock_specialist(request, specialist_id)
            else:
                result = await self._delegate_to_specialist(request, specialist_id)

            # Quality check
            self.status = KommandantStatus.REVIEWING
            if result.success and result.quality_score < self._min_quality_score:
                # Retry with enhanced prompt
                for retry in range(self._max_retries):
                    enhanced_request = await self._enhance_for_retry(request, result, retry + 1)
                    result = await self._execute_with_mock_specialist(enhanced_request, specialist_id)
                    if result.quality_score >= self._min_quality_score:
                        break

            # Update statistics
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            result.duration_seconds = duration

            if result.success:
                self.requests_completed += 1
                self.total_cost_usd += result.cost_usd
                self._update_capability_stats(request.capability)
            else:
                self.requests_failed += 1

            self._completed_results[request.request_id] = result
            self.status = KommandantStatus.IDLE

            self._audit("execute_request", "request", request.request_id, {
                "success": result.success,
                "cost_usd": result.cost_usd,
                "duration_seconds": duration
            }, "completed" if result.success else "failed", cost_usd=result.cost_usd)

            return result

        except Exception as e:
            self.requests_failed += 1
            self.status = KommandantStatus.ERROR

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            result = CreativeResult(
                request_id=request.request_id,
                success=False,
                task_type=request.task_type,
                capability=request.capability,
                error=str(e),
                duration_seconds=duration
            )

            self._completed_results[request.request_id] = result

            self._audit("execute_request", "request", request.request_id, {
                "error": str(e)
            }, "error", severity="error")

            logger.error(f"Request {request.request_id} failed: {e}")
            return result

        finally:
            if request.request_id in self._active_requests:
                del self._active_requests[request.request_id]

    async def _optimize_prompt(self, request: CreativeRequest) -> CreativeRequest:
        """Optimize prompt for better results."""
        # Add quality modifiers
        quality_modifiers = [
            "high quality",
            "detailed",
            "professional",
            "masterpiece"
        ]

        # Add style-specific modifiers
        style_modifiers = {
            "fantasy": ["epic", "magical", "ethereal lighting"],
            "realistic": ["photorealistic", "8k", "sharp focus"],
            "anime": ["anime style", "vibrant colors", "clean lines"],
            "watercolor": ["watercolor painting", "soft edges", "artistic"]
        }

        style = request.metadata.get("style") or (
            request.style_config.style_name if request.style_config else None
        )

        optimized_prompt = request.prompt

        # Add quality modifiers if not present
        for modifier in quality_modifiers[:2]:
            if modifier.lower() not in optimized_prompt.lower():
                optimized_prompt = f"{optimized_prompt}, {modifier}"

        # Add style modifiers
        if style and style in style_modifiers:
            for mod in style_modifiers[style][:2]:
                if mod.lower() not in optimized_prompt.lower():
                    optimized_prompt = f"{optimized_prompt}, {mod}"

        request.prompt = optimized_prompt
        request.metadata["original_prompt"] = request.prompt
        request.metadata["optimized"] = True

        return request

    async def _enhance_for_retry(
        self,
        request: CreativeRequest,
        previous_result: CreativeResult,
        retry_num: int
    ) -> CreativeRequest:
        """Enhance request for retry after quality failure."""
        enhanced_prompt = f"{request.prompt}, ultra high quality, best quality"

        if retry_num > 1:
            enhanced_prompt += ", intricate details, masterwork"

        # Increase inference steps
        request.prompt = enhanced_prompt
        request.num_inference_steps = min(50, request.num_inference_steps + 10)
        request.guidance_scale = min(12.0, request.guidance_scale + 1.0)

        return request

    async def _execute_with_mock_specialist(
        self,
        request: CreativeRequest,
        specialist_id: str
    ) -> CreativeResult:
        """Execute with mock specialist for MVP."""
        await asyncio.sleep(0.5)  # Simulate API call

        # Generate mock output
        output_path = f"/tmp/creative/{request.request_id}.{request.output_format.value}"

        # Calculate mock cost
        cost = COST_ESTIMATES.get(request.capability, 0.01) * request.num_outputs

        result = CreativeResult(
            request_id=request.request_id,
            success=True,
            task_type=request.task_type,
            capability=request.capability,
            output_paths=[output_path],
            output_urls=[f"https://cdn.cirkelline.com/creative/{request.request_id}.{request.output_format.value}"],
            output_format=request.output_format,
            quality_score=0.85,
            aesthetic_score=0.80,
            cost_usd=cost,
            api_calls=1,
            specialist_used=specialist_id,
            model_used="mock_model",
            metadata={
                "mock": True,
                "prompt_used": request.prompt
            }
        )

        return result

    async def _delegate_to_specialist(
        self,
        request: CreativeRequest,
        specialist_id: str
    ) -> CreativeResult:
        """Delegate to actual specialist."""
        specialist = self._specialists.get(specialist_id)
        if not specialist:
            raise ValueError(f"Specialist {specialist_id} not found")

        return await specialist.process(request)

    def _update_capability_stats(self, capability: CreativeCapability) -> None:
        """Update capability-specific statistics."""
        if capability in [CreativeCapability.TEXT_TO_IMAGE, CreativeCapability.IMAGE_TO_IMAGE]:
            self.images_generated += 1
        elif capability == CreativeCapability.IMAGE_TO_ANIMATION:
            self.animations_created += 1
        elif capability == CreativeCapability.STYLE_TRANSFER:
            self.styles_applied += 1
        elif capability == CreativeCapability.VECTORIZATION:
            self.vectors_created += 1

    # ========== Initialization ==========

    async def _initialize_specialists(self) -> None:
        """Initialize creative specialists."""
        # Specialists will be loaded from specialists.py
        logger.info(f"Initializing specialists for {self.name}")

    async def _initialize_api_clients(self) -> None:
        """Initialize API clients."""
        # API clients will be loaded from api_integrations.py
        logger.info(f"Initializing API clients for {self.name}")

    # ========== Audit ==========

    def _audit(
        self,
        action: str,
        target_type: str,
        target_id: str,
        details: Dict[str, Any],
        outcome: str,
        cost_usd: float = 0.0,
        severity: str = "info"
    ) -> None:
        """Record an audit entry."""
        entry = AuditEntry(
            entry_id=f"audit_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc),
            action=action,
            actor=self.kommandant_id,
            target=f"{target_type}:{target_id}",
            details=details,
            outcome=outcome,
            cost_usd=cost_usd,
            severity=severity
        )

        self._audit_log.append(entry)

        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]

        if severity in ["error", "critical"]:
            logger.warning(f"Audit [{severity}]: {action} on {target_type}:{target_id} - {outcome}")

    # ========== Status & Statistics ==========

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "kommandant_id": self.kommandant_id,
            "room_id": self.room_id,
            "name": self.name,
            "status": self.status.value,
            "running": self._running,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "budget_limit_usd": self.budget_limit_usd,
            "total_cost_usd": self.total_cost_usd,
            "budget_remaining_usd": self.budget_limit_usd - self.total_cost_usd,
            "statistics": self.get_statistics(),
            "active_requests": len(self._active_requests)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics."""
        return {
            "requests_received": self.requests_received,
            "requests_completed": self.requests_completed,
            "requests_failed": self.requests_failed,
            "success_rate": self.requests_completed / max(1, self.requests_received),
            "total_cost_usd": self.total_cost_usd,
            "images_generated": self.images_generated,
            "animations_created": self.animations_created,
            "styles_applied": self.styles_applied,
            "vectors_created": self.vectors_created,
            "avg_cost_per_request": self.total_cost_usd / max(1, self.requests_completed)
        }

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log."""
        return [entry.to_dict() for entry in self._audit_log[-limit:]]

    def estimate_cost(self, request: CreativeRequest) -> float:
        """Estimate cost for a request."""
        base_cost = COST_ESTIMATES.get(request.capability, 0.05)
        return base_cost * request.num_outputs


# ========== Factory ==========

_kreativ_kommandanter: Dict[int, KreativKommandant] = {}


async def create_kreativ_kommandant(
    room_id: int,
    name: str = "Kreativ Kommandant",
    description: str = "",
    budget_limit_usd: float = 10.0,
    auto_start: bool = True
) -> KreativKommandant:
    """
    Create a new Kreativ Kommandant.

    Args:
        room_id: Creative learning room ID
        name: Kommandant name
        description: Description
        budget_limit_usd: Budget limit
        auto_start: Start immediately

    Returns:
        Created KreativKommandant
    """
    kommandant = KreativKommandant(
        room_id=room_id,
        name=name,
        description=description,
        budget_limit_usd=budget_limit_usd
    )

    if auto_start:
        await kommandant.start()

    _kreativ_kommandanter[room_id] = kommandant

    logger.info(f"KreativKommandant created for room {room_id}: {name}")
    return kommandant


async def get_kreativ_kommandant(room_id: int) -> Optional[KreativKommandant]:
    """Get Kreativ Kommandant for a room."""
    return _kreativ_kommandanter.get(room_id)


def list_kreativ_kommandanter() -> List[Dict[str, Any]]:
    """List all Kreativ Kommandanter."""
    return [k.get_status() for k in _kreativ_kommandanter.values()]


logger.info("CKC Tegne-enhed Core module loaded")
