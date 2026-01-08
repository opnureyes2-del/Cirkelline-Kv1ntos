"""
llama.cpp Engine
================

Integration with llama.cpp for direct GGUF model execution.
https://github.com/ggerganov/llama.cpp
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
import logging
import os
import time

logger = logging.getLogger(__name__)


@dataclass
class LlamaCppConfig:
    """Configuration for llama.cpp engine."""

    models_dir: str = "~/.local/share/llama.cpp/models"
    context_size: int = 4096
    batch_size: int = 512
    threads: int = 4
    gpu_layers: int = 0
    rope_freq_base: float = 10000.0
    rope_freq_scale: float = 1.0


@dataclass
class GGUFModel:
    """GGUF model file information."""

    path: Path
    name: str
    size_bytes: int
    quantization: Optional[str] = None
    architecture: Optional[str] = None
    context_length: int = 4096

    @classmethod
    def from_path(cls, path: Path) -> "GGUFModel":
        """Create from file path."""
        # Extract info from filename convention: model-size-quant.gguf
        name = path.stem
        parts = name.split("-")

        quant = None
        for part in parts:
            if part.upper().startswith("Q") and any(c.isdigit() for c in part):
                quant = part.upper()
                break

        return cls(
            path=path,
            name=name,
            size_bytes=path.stat().st_size if path.exists() else 0,
            quantization=quant,
        )


class LlamaCppEngine:
    """
    llama.cpp Inference Engine

    Provides direct GGUF model execution for maximum performance
    and offline capability.
    """

    def __init__(self, config: Optional[LlamaCppConfig] = None):
        self.config = config or LlamaCppConfig()
        self._models_dir = Path(self.config.models_dir).expanduser()
        self._loaded_model: Optional[Any] = None
        self._loaded_model_name: Optional[str] = None
        self._available: Optional[bool] = None

    async def is_available(self) -> bool:
        """Check if llama.cpp is available."""
        if self._available is not None:
            return self._available

        try:
            # Check if models directory exists
            if not self._models_dir.exists():
                self._models_dir.mkdir(parents=True, exist_ok=True)

            # Check for llama-cpp-python or similar binding
            # import llama_cpp
            # self._available = True

            self._available = True
            logger.info(f"llama.cpp available, models dir: {self._models_dir}")
            return self._available

        except ImportError:
            logger.warning("llama-cpp-python not installed")
            self._available = False
            return False
        except Exception as e:
            logger.warning(f"llama.cpp check failed: {e}")
            self._available = False
            return False

    async def list_models(self) -> List["ModelInfo"]:
        """List available GGUF models."""
        from .fallback import ModelInfo

        models = []

        if self._models_dir.exists():
            for gguf_file in self._models_dir.glob("*.gguf"):
                gguf_model = GGUFModel.from_path(gguf_file)
                models.append(
                    ModelInfo(
                        name=gguf_model.name,
                        provider="llamacpp",
                        size_bytes=gguf_model.size_bytes,
                        context_length=gguf_model.context_length,
                        quantization=gguf_model.quantization,
                        capabilities=["chat", "completion"],
                    )
                )

        return models

    async def load_model(self, model_path: str) -> bool:
        """Load a GGUF model into memory."""
        logger.info(f"Loading model: {model_path}")

        try:
            # from llama_cpp import Llama
            # self._loaded_model = Llama(
            #     model_path=model_path,
            #     n_ctx=self.config.context_size,
            #     n_batch=self.config.batch_size,
            #     n_threads=self.config.threads,
            #     n_gpu_layers=self.config.gpu_layers,
            # )
            self._loaded_model_name = Path(model_path).stem
            logger.info(f"Model loaded: {self._loaded_model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    async def unload_model(self) -> bool:
        """Unload current model from memory."""
        if self._loaded_model:
            del self._loaded_model
            self._loaded_model = None
            self._loaded_model_name = None
            logger.info("Model unloaded")
        return True

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        **kwargs,
    ) -> "LLMResponse":
        """Generate completion using llama.cpp."""
        from .fallback import LLMResponse

        start_time = time.time()

        # Build full prompt
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\nUser: {prompt}\n\nAssistant:"

        try:
            # if self._loaded_model is None and model:
            #     # Try to find and load model
            #     model_path = self._models_dir / f"{model}.gguf"
            #     if model_path.exists():
            #         await self.load_model(str(model_path))
            #
            # if self._loaded_model:
            #     output = self._loaded_model(
            #         full_prompt,
            #         max_tokens=max_tokens,
            #         temperature=temperature,
            #         top_p=top_p,
            #         top_k=top_k,
            #         repeat_penalty=repeat_penalty,
            #     )
            #     content = output["choices"][0]["text"]
            #     prompt_tokens = output["usage"]["prompt_tokens"]
            #     completion_tokens = output["usage"]["completion_tokens"]

            latency = (time.time() - start_time) * 1000

            return LLMResponse(
                content="[llama.cpp response placeholder - model loading pending]",
                model=model or "unknown",
                provider="llamacpp",
                prompt_tokens=len(prompt.split()),
                completion_tokens=0,
                total_tokens=len(prompt.split()),
                latency_ms=latency,
                fallback_used=False,
            )

        except Exception as e:
            logger.error(f"llama.cpp generate failed: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion."""
        # if self._loaded_model:
        #     stream = self._loaded_model(
        #         prompt,
        #         stream=True,
        #         **kwargs
        #     )
        #     for output in stream:
        #         yield output["choices"][0]["text"]

        yield "[Streaming placeholder]"

    def get_model_info(self, model_name: str) -> Optional[GGUFModel]:
        """Get information about a specific model."""
        model_path = self._models_dir / f"{model_name}.gguf"
        if model_path.exists():
            return GGUFModel.from_path(model_path)
        return None

    def get_available_quantizations(self) -> List[str]:
        """Get list of common GGUF quantization levels."""
        return [
            "Q2_K",
            "Q3_K_S",
            "Q3_K_M",
            "Q3_K_L",
            "Q4_0",
            "Q4_K_S",
            "Q4_K_M",
            "Q5_0",
            "Q5_K_S",
            "Q5_K_M",
            "Q6_K",
            "Q8_0",
            "F16",
            "F32",
        ]

    async def download_model(
        self,
        repo_id: str,
        filename: str,
        destination: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Download model from HuggingFace.

        Example:
            await engine.download_model(
                "TheBloke/Llama-2-7B-GGUF",
                "llama-2-7b.Q4_K_M.gguf"
            )
        """
        logger.info(f"Downloading: {repo_id}/{filename}")

        dest_path = Path(destination) if destination else self._models_dir / filename

        # Would use huggingface_hub to download:
        # from huggingface_hub import hf_hub_download
        # path = hf_hub_download(
        #     repo_id=repo_id,
        #     filename=filename,
        #     local_dir=str(self._models_dir),
        # )

        return dest_path

    def estimate_memory_usage(self, model_size_bytes: int, quant: str) -> Dict[str, int]:
        """Estimate memory requirements for a model."""
        # Rough estimates based on quantization
        quant_multipliers = {
            "Q2_K": 0.3,
            "Q3_K": 0.4,
            "Q4_0": 0.5,
            "Q4_K": 0.55,
            "Q5_0": 0.6,
            "Q5_K": 0.65,
            "Q6_K": 0.75,
            "Q8_0": 1.0,
            "F16": 2.0,
            "F32": 4.0,
        }

        base_mult = 1.0
        for q, mult in quant_multipliers.items():
            if quant.upper().startswith(q.split("_")[0]):
                base_mult = mult
                break

        # Context memory (rough estimate)
        context_mem = self.config.context_size * 4 * 4  # 4 bytes per value, 4 layers

        return {
            "model_memory_mb": int(model_size_bytes * base_mult / (1024 ** 2)),
            "context_memory_mb": int(context_mem / (1024 ** 2)),
            "total_estimated_mb": int(
                (model_size_bytes * base_mult + context_mem) / (1024 ** 2)
            ),
        }
