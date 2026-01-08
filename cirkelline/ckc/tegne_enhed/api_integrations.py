"""
CKC Tegne-enhed API Integrations
================================

Integration med eksterne kreative API'er.

API'er:
    - Replicate (SDXL): Text-to-image, upscaling
    - Luma AI: Image-to-animation
    - Prodia: Style transfer
    - Vectorizer.AI: Raster-to-vector

Alle API'er implementerer samme interface for nem udskiftning.
"""

import asyncio
import logging
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


# ========== Data Classes ==========

@dataclass
class APIResponse:
    """Standard API response."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 200
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "status_code": self.status_code,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "metadata": self.metadata
        }


@dataclass
class APIConfig:
    """API client configuration."""
    api_key: str
    base_url: str
    timeout_seconds: int = 60
    max_retries: int = 3
    rate_limit_per_minute: int = 60


# ========== Base API Client ==========

class CreativeAPIClient(ABC):
    """
    Base class for creative API clients.

    All API clients implement this interface for consistency.
    """

    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config
        self.client_id = f"api_{uuid.uuid4().hex[:8]}"

        # Statistics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_cost_usd = 0.0
        self.total_latency_ms = 0.0

        # Rate limiting
        self._call_timestamps: List[datetime] = []

        logger.info(f"API Client created: {self.__class__.__name__}")

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if API is available."""
        pass

    @abstractmethod
    async def call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Make an API call."""
        pass

    async def close(self) -> None:
        """Clean up resources."""
        pass

    def _track_call(self, response: APIResponse) -> None:
        """Track API call statistics."""
        self.total_calls += 1
        if response.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        self.total_cost_usd += response.cost_usd
        self.total_latency_ms += response.latency_ms

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        if not self.config:
            return True

        now = datetime.now(timezone.utc)
        minute_ago = now.replace(second=0, microsecond=0)

        # Clean old timestamps
        self._call_timestamps = [
            ts for ts in self._call_timestamps
            if ts > minute_ago
        ]

        return len(self._call_timestamps) < self.config.rate_limit_per_minute

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "client_id": self.client_id,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.successful_calls / max(1, self.total_calls),
            "total_cost_usd": self.total_cost_usd,
            "avg_latency_ms": self.total_latency_ms / max(1, self.total_calls)
        }


# ========== Replicate Client (SDXL) ==========

class ReplicateClient(CreativeAPIClient):
    """
    Replicate API client for SDXL image generation.

    Pricing (approximate):
        - SDXL: ~$0.01 per image
        - SDXL Turbo: ~$0.005 per image
        - Upscaling: ~$0.02 per image

    API Docs: https://replicate.com/docs
    """

    # Model versions (Replicate uses versioned models)
    MODELS = {
        "sdxl": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "sdxl_turbo": "stability-ai/sdxl-turbo:2d80f67a8c04ab9a5cc4f85a63b8c9c8",
        "real_esrgan": "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b"
    }

    PRICING = {
        "sdxl": 0.01,
        "sdxl_turbo": 0.005,
        "real_esrgan": 0.02
    }

    def __init__(self, api_key: Optional[str] = None):
        config = APIConfig(
            api_key=api_key or os.getenv("REPLICATE_API_KEY", ""),
            base_url="https://api.replicate.com/v1",
            timeout_seconds=120,
            rate_limit_per_minute=60
        )
        super().__init__(config)

    async def health_check(self) -> bool:
        """Check Replicate API availability."""
        # In production, would make actual API call
        return bool(self.config.api_key)

    async def call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Make Replicate API call."""
        start_time = datetime.now(timezone.utc)

        if not self._check_rate_limit():
            return APIResponse(
                success=False,
                error="Rate limit exceeded",
                status_code=429
            )

        try:
            # Mock implementation for MVP
            response = await self._mock_call(endpoint, params)
            self._track_call(response)
            return response

        except Exception as e:
            latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            response = APIResponse(
                success=False,
                error=str(e),
                status_code=500,
                latency_ms=latency
            )
            self._track_call(response)
            return response

    async def generate_image(self, params: Dict[str, Any]) -> APIResponse:
        """Generate image using SDXL."""
        return await self.call("predictions", {
            "model": self.MODELS["sdxl"],
            "input": params
        })

    async def upscale_image(self, image_url: str, scale: int = 4) -> APIResponse:
        """Upscale image using Real-ESRGAN."""
        return await self.call("predictions", {
            "model": self.MODELS["real_esrgan"],
            "input": {
                "image": image_url,
                "scale": scale
            }
        })

    async def _mock_call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Mock API call for MVP testing."""
        await asyncio.sleep(1.0)  # Simulate network latency

        model = params.get("model", "")
        model_name = next((k for k, v in self.MODELS.items() if v == model), "sdxl")
        cost = self.PRICING.get(model_name, 0.01)

        return APIResponse(
            success=True,
            data={
                "id": f"pred_{uuid.uuid4().hex[:12]}",
                "status": "succeeded",
                "output": [
                    f"https://replicate.delivery/mock/{uuid.uuid4().hex}.png"
                ],
                "metrics": {
                    "predict_time": 5.2
                }
            },
            status_code=200,
            latency_ms=1000,
            cost_usd=cost,
            metadata={"model": model_name}
        )


# ========== Luma AI Client ==========

class LumaAIClient(CreativeAPIClient):
    """
    Luma AI Dream Machine client for image-to-video.

    Pricing (approximate):
        - 5-second video: ~$0.50
        - 10-second video: ~$1.00

    API Docs: https://docs.lumalabs.ai/
    """

    PRICING = {
        "5s": 0.50,
        "10s": 1.00
    }

    def __init__(self, api_key: Optional[str] = None):
        config = APIConfig(
            api_key=api_key or os.getenv("LUMA_API_KEY", ""),
            base_url="https://api.lumalabs.ai/v1",
            timeout_seconds=300,  # Video generation takes time
            rate_limit_per_minute=10
        )
        super().__init__(config)

    async def health_check(self) -> bool:
        """Check Luma AI API availability."""
        return bool(self.config.api_key)

    async def call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Make Luma AI API call."""
        start_time = datetime.now(timezone.utc)

        if not self._check_rate_limit():
            return APIResponse(
                success=False,
                error="Rate limit exceeded",
                status_code=429
            )

        try:
            response = await self._mock_call(endpoint, params)
            self._track_call(response)
            return response

        except Exception as e:
            latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            response = APIResponse(
                success=False,
                error=str(e),
                status_code=500,
                latency_ms=latency
            )
            self._track_call(response)
            return response

    async def create_animation(self, params: Dict[str, Any]) -> APIResponse:
        """Create animation from image."""
        return await self.call("dream-machine/generations", {
            "image_url": params.get("image_path"),
            "prompt": params.get("prompt", ""),
            "duration": params.get("duration", 5),
            "motion": params.get("motion", "zoom_out")
        })

    async def _mock_call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Mock API call for MVP testing."""
        await asyncio.sleep(3.0)  # Video generation is slow

        duration = params.get("duration", 5)
        cost = self.PRICING.get(f"{duration}s", 0.50)

        return APIResponse(
            success=True,
            data={
                "id": f"gen_{uuid.uuid4().hex[:12]}",
                "status": "completed",
                "video_url": f"https://storage.lumalabs.ai/mock/{uuid.uuid4().hex}.mp4",
                "duration_seconds": duration
            },
            status_code=200,
            latency_ms=3000,
            cost_usd=cost,
            metadata={"duration": duration}
        )


# ========== Prodia Client ==========

class ProdiaClient(CreativeAPIClient):
    """
    Prodia API client for fast style transfer.

    Pricing (approximate):
        - Style transfer: ~$0.005 per image
        - Average latency: 190ms

    API Docs: https://docs.prodia.com/
    """

    STYLES = [
        "anime", "3d-model", "analog-film", "cinematic",
        "comic-book", "digital-art", "enhance", "fantasy-art",
        "isometric", "line-art", "low-poly", "neon-punk",
        "origami", "photographic", "pixel-art", "texture"
    ]

    PRICING = {
        "style_transfer": 0.005,
        "sd_generate": 0.003
    }

    def __init__(self, api_key: Optional[str] = None):
        config = APIConfig(
            api_key=api_key or os.getenv("PRODIA_API_KEY", ""),
            base_url="https://api.prodia.com/v1",
            timeout_seconds=30,
            rate_limit_per_minute=100  # Prodia is fast
        )
        super().__init__(config)

    async def health_check(self) -> bool:
        """Check Prodia API availability."""
        return bool(self.config.api_key)

    async def call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Make Prodia API call."""
        start_time = datetime.now(timezone.utc)

        if not self._check_rate_limit():
            return APIResponse(
                success=False,
                error="Rate limit exceeded",
                status_code=429
            )

        try:
            response = await self._mock_call(endpoint, params)
            self._track_call(response)
            return response

        except Exception as e:
            latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            response = APIResponse(
                success=False,
                error=str(e),
                status_code=500,
                latency_ms=latency
            )
            self._track_call(response)
            return response

    async def transfer_style(self, params: Dict[str, Any]) -> APIResponse:
        """Apply style transfer to image."""
        return await self.call("sd/transform", {
            "imageUrl": params.get("image_path"),
            "style_preset": params.get("style_name", "digital-art"),
            "denoising_strength": 1.0 - params.get("preserve_content", 0.5)
        })

    async def _mock_call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Mock API call for MVP testing."""
        await asyncio.sleep(0.2)  # Prodia is very fast

        return APIResponse(
            success=True,
            data={
                "job": f"job_{uuid.uuid4().hex[:12]}",
                "status": "succeeded",
                "imageUrl": f"https://images.prodia.xyz/mock/{uuid.uuid4().hex}.png"
            },
            status_code=200,
            latency_ms=190,
            cost_usd=self.PRICING["style_transfer"],
            metadata={"style": params.get("style_preset")}
        )


# ========== Vectorizer.AI Client ==========

class VectorizerAIClient(CreativeAPIClient):
    """
    Vectorizer.AI client for raster-to-vector conversion.

    Pricing tiers:
        - Starter: $9.99/mo (100 vectors)
        - Pro: $49.99/mo (1000 vectors)
        - Enterprise: Custom

    API Docs: https://vectorizer.ai/api
    """

    OUTPUT_FORMATS = ["svg", "pdf", "eps", "dxf"]

    PRICING = {
        "vectorize": 0.10  # ~$0.10 per image on Pro tier
    }

    def __init__(self, api_key: Optional[str] = None):
        config = APIConfig(
            api_key=api_key or os.getenv("VECTORIZER_API_KEY", ""),
            base_url="https://api.vectorizer.ai/api/v1",
            timeout_seconds=120,
            rate_limit_per_minute=30
        )
        super().__init__(config)

    async def health_check(self) -> bool:
        """Check Vectorizer.AI API availability."""
        return bool(self.config.api_key)

    async def call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Make Vectorizer.AI API call."""
        start_time = datetime.now(timezone.utc)

        if not self._check_rate_limit():
            return APIResponse(
                success=False,
                error="Rate limit exceeded",
                status_code=429
            )

        try:
            response = await self._mock_call(endpoint, params)
            self._track_call(response)
            return response

        except Exception as e:
            latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            response = APIResponse(
                success=False,
                error=str(e),
                status_code=500,
                latency_ms=latency
            )
            self._track_call(response)
            return response

    async def vectorize(self, params: Dict[str, Any]) -> APIResponse:
        """Convert raster image to vector."""
        output_format = params.get("output_format", "svg")
        if output_format not in self.OUTPUT_FORMATS:
            output_format = "svg"

        return await self.call("vectorize", {
            "image_url": params.get("image_path"),
            "output.format": output_format,
            "processing.max_colors": params.get("max_colors", 32),
            "output.size.scale": 1.0
        })

    async def _mock_call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Mock API call for MVP testing."""
        await asyncio.sleep(2.0)  # Vectorization takes time

        output_format = params.get("output.format", "svg")

        return APIResponse(
            success=True,
            data={
                "job_id": f"vec_{uuid.uuid4().hex[:12]}",
                "status": "completed",
                "result_url": f"https://api.vectorizer.ai/results/{uuid.uuid4().hex}.{output_format}",
                "format": output_format,
                "colors_used": params.get("processing.max_colors", 32)
            },
            status_code=200,
            latency_ms=2000,
            cost_usd=self.PRICING["vectorize"],
            metadata={"format": output_format}
        )


# ========== Factory Functions ==========

_api_clients: Dict[str, CreativeAPIClient] = {}


def get_api_client(client_type: str) -> Optional[CreativeAPIClient]:
    """
    Get or create an API client.

    Args:
        client_type: One of "replicate", "luma", "prodia", "vectorizer"

    Returns:
        API client instance or None
    """
    if client_type in _api_clients:
        return _api_clients[client_type]

    if client_type == "replicate":
        client = ReplicateClient()
    elif client_type == "luma":
        client = LumaAIClient()
    elif client_type == "prodia":
        client = ProdiaClient()
    elif client_type == "vectorizer":
        client = VectorizerAIClient()
    else:
        logger.warning(f"Unknown API client type: {client_type}")
        return None

    _api_clients[client_type] = client
    return client


def estimate_cost(capability: str, params: Optional[Dict[str, Any]] = None) -> float:
    """
    Estimate cost for a creative operation.

    Args:
        capability: Creative capability name
        params: Optional parameters affecting cost

    Returns:
        Estimated cost in USD
    """
    from .core import CreativeCapability, COST_ESTIMATES

    try:
        cap = CreativeCapability(capability)
        base_cost = COST_ESTIMATES.get(cap, 0.01)

        # Adjust for parameters
        if params:
            num_outputs = params.get("num_outputs", 1)
            base_cost *= num_outputs

            # Animation duration affects cost
            if cap == CreativeCapability.IMAGE_TO_ANIMATION:
                duration = params.get("duration_seconds", 5)
                if duration > 5:
                    base_cost *= 2

        return round(base_cost, 4)

    except ValueError:
        return 0.01


async def check_api_health() -> Dict[str, bool]:
    """
    Check health of all API clients.

    Returns:
        Dict mapping client name to health status
    """
    results = {}

    for client_type in ["replicate", "luma", "prodia", "vectorizer"]:
        client = get_api_client(client_type)
        if client:
            results[client_type] = await client.health_check()
        else:
            results[client_type] = False

    return results


logger.info("CKC Tegne-enhed API Integrations module loaded")
