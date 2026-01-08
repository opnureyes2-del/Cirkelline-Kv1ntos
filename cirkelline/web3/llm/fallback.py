"""
Local LLM Fallback System
=========================

Provides automatic fallback to local LLM models when cloud
services are unavailable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)


class FallbackMode(Enum):
    """LLM fallback strategy modes."""

    CLOUD_FIRST = "cloud_first"  # Try cloud, fallback to local
    LOCAL_FIRST = "local_first"  # Try local, fallback to cloud
    LOCAL_ONLY = "local_only"  # Only use local models
    CLOUD_ONLY = "cloud_only"  # Only use cloud models


@dataclass
class ModelInfo:
    """Information about an available LLM model."""

    name: str
    provider: str  # "ollama", "llamacpp", "cloud"
    size_bytes: int = 0
    context_length: int = 4096
    quantization: Optional[str] = None
    loaded: bool = False
    capabilities: List[str] = field(default_factory=list)

    @property
    def size_gb(self) -> float:
        """Get model size in gigabytes."""
        return self.size_bytes / (1024 ** 3)


@dataclass
class FallbackConfig:
    """Configuration for LLM fallback system."""

    mode: FallbackMode = FallbackMode.CLOUD_FIRST
    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.2"
    timeout_seconds: int = 30
    max_retries: int = 3
    auto_load_models: bool = True
    preferred_models: List[str] = field(
        default_factory=lambda: ["llama3.2", "mistral", "phi3"]
    )


@dataclass
class LLMResponse:
    """Response from LLM generation."""

    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    fallback_used: bool = False


class LocalLLMProvider(ABC):
    """Abstract base class for local LLM providers."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available."""
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion."""
        pass


class LocalLLMFallback:
    """
    Local LLM Fallback System

    Provides intelligent fallback between cloud and local LLM
    providers for resilient AI operations.
    """

    def __init__(self, config: Optional[FallbackConfig] = None):
        self.config = config or FallbackConfig()
        self._ollama_client: Optional["OllamaClient"] = None
        self._llamacpp_engine: Optional["LlamaCppEngine"] = None
        self._available_models: List[ModelInfo] = []
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize fallback system and discover available models."""
        logger.info("Initializing Local LLM Fallback system...")

        # Try to initialize Ollama
        try:
            from .ollama import OllamaClient

            self._ollama_client = OllamaClient(self.config.ollama_url)
            if await self._ollama_client.is_available():
                models = await self._ollama_client.list_models()
                self._available_models.extend(models)
                logger.info(f"Ollama available with {len(models)} models")
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")

        # Try to initialize llama.cpp
        try:
            from .llamacpp import LlamaCppEngine

            self._llamacpp_engine = LlamaCppEngine()
            if await self._llamacpp_engine.is_available():
                models = await self._llamacpp_engine.list_models()
                self._available_models.extend(models)
                logger.info(f"llama.cpp available with {len(models)} models")
        except Exception as e:
            logger.warning(f"llama.cpp not available: {e}")

        self._initialized = len(self._available_models) > 0
        logger.info(
            f"Fallback system initialized: {len(self._available_models)} models available"
        )
        return self._initialized

    @property
    def is_available(self) -> bool:
        """Check if any local provider is available."""
        return self._initialized and len(self._available_models) > 0

    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models."""
        if not self._initialized:
            await self.initialize()
        return self._available_models

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate completion using appropriate provider based on mode.
        """
        if not self._initialized:
            await self.initialize()

        model_name = model or self.config.default_model

        # Determine provider based on mode
        if self.config.mode == FallbackMode.LOCAL_ONLY:
            return await self._generate_local(
                prompt, model_name, system_prompt, temperature, max_tokens, **kwargs
            )
        elif self.config.mode == FallbackMode.CLOUD_ONLY:
            raise NotImplementedError("Cloud provider not configured")
        elif self.config.mode == FallbackMode.CLOUD_FIRST:
            try:
                # Try cloud first (placeholder)
                raise ConnectionError("Cloud unavailable")
            except Exception:
                logger.info("Cloud unavailable, falling back to local")
                response = await self._generate_local(
                    prompt, model_name, system_prompt, temperature, max_tokens, **kwargs
                )
                response.fallback_used = True
                return response
        else:  # LOCAL_FIRST
            try:
                return await self._generate_local(
                    prompt, model_name, system_prompt, temperature, max_tokens, **kwargs
                )
            except Exception:
                raise NotImplementedError("Cloud fallback not configured")

    async def _generate_local(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> LLMResponse:
        """Generate using local providers."""
        # Try Ollama first
        if self._ollama_client and await self._ollama_client.is_available():
            return await self._ollama_client.generate(
                prompt=prompt,
                model=model,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

        # Try llama.cpp
        if self._llamacpp_engine and await self._llamacpp_engine.is_available():
            return await self._llamacpp_engine.generate(
                prompt=prompt,
                model=model,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

        raise RuntimeError("No local LLM provider available")

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion."""
        if not self._initialized:
            await self.initialize()

        model_name = model or self.config.default_model

        if self._ollama_client and await self._ollama_client.is_available():
            async for chunk in self._ollama_client.generate_stream(
                prompt=prompt, model=model_name, **kwargs
            ):
                yield chunk
        else:
            raise RuntimeError("No streaming provider available")

    def get_status(self) -> Dict[str, Any]:
        """Get current fallback system status."""
        return {
            "initialized": self._initialized,
            "mode": self.config.mode.value,
            "available_models": len(self._available_models),
            "ollama_available": self._ollama_client is not None,
            "llamacpp_available": self._llamacpp_engine is not None,
            "default_model": self.config.default_model,
        }


# Singleton instance
_fallback_instance: Optional[LocalLLMFallback] = None


def get_llm_fallback(config: Optional[FallbackConfig] = None) -> LocalLLMFallback:
    """Get singleton instance of LLM fallback system."""
    global _fallback_instance

    if _fallback_instance is None:
        _fallback_instance = LocalLLMFallback(config)

    return _fallback_instance
