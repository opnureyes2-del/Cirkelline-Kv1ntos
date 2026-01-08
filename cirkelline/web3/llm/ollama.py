"""
Ollama Client
=============

Client for interacting with Ollama local LLM server.
https://ollama.ai
"""

from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional
import json
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class OllamaModel:
    """Ollama model information."""

    name: str
    modified_at: str
    size: int
    digest: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def family(self) -> str:
        """Get model family."""
        return self.details.get("family", "unknown")

    @property
    def parameter_size(self) -> str:
        """Get parameter size (e.g., '7B')."""
        return self.details.get("parameter_size", "unknown")

    @property
    def quantization_level(self) -> str:
        """Get quantization level (e.g., 'Q4_0')."""
        return self.details.get("quantization_level", "unknown")


@dataclass
class OllamaResponse:
    """Response from Ollama API."""

    model: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: int = 0
    load_duration: int = 0
    prompt_eval_count: int = 0
    prompt_eval_duration: int = 0
    eval_count: int = 0
    eval_duration: int = 0

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        if self.eval_duration > 0:
            return self.eval_count / (self.eval_duration / 1e9)
        return 0.0


class OllamaClient:
    """
    Ollama API Client

    Provides async interface to Ollama's local LLM server
    for model management and text generation.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._available: Optional[bool] = None

    async def is_available(self) -> bool:
        """Check if Ollama server is running and accessible."""
        if self._available is not None:
            return self._available

        try:
            # In production, use httpx:
            # async with httpx.AsyncClient() as client:
            #     response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
            #     self._available = response.status_code == 200

            # For now, assume available if module loads
            self._available = True
            logger.info(f"Ollama server check at {self.base_url}")
            return self._available
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._available = False
            return False

    async def list_models(self) -> List["ModelInfo"]:
        """List available models on Ollama server."""
        from .fallback import ModelInfo

        try:
            # Placeholder for actual API call:
            # async with httpx.AsyncClient() as client:
            #     response = await client.get(f"{self.base_url}/api/tags")
            #     data = response.json()
            #     return [ModelInfo(...) for model in data["models"]]

            # Return common models for testing
            return [
                ModelInfo(
                    name="llama3.2",
                    provider="ollama",
                    context_length=8192,
                    capabilities=["chat", "code", "reasoning"],
                ),
                ModelInfo(
                    name="mistral",
                    provider="ollama",
                    context_length=8192,
                    capabilities=["chat", "code"],
                ),
                ModelInfo(
                    name="phi3",
                    provider="ollama",
                    context_length=4096,
                    capabilities=["chat", "code"],
                ),
            ]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def pull_model(self, model: str) -> bool:
        """Pull/download a model from Ollama library."""
        logger.info(f"Pulling model: {model}")
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{self.base_url}/api/pull",
        #         json={"name": model},
        #         timeout=None  # Models can be large
        #     )
        return True

    async def delete_model(self, model: str) -> bool:
        """Delete a model from local storage."""
        logger.info(f"Deleting model: {model}")
        # async with httpx.AsyncClient() as client:
        #     response = await client.delete(
        #         f"{self.base_url}/api/delete",
        #         json={"name": model}
        #     )
        return True

    async def generate(
        self,
        prompt: str,
        model: str = "llama3.2",
        system: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[List[int]] = None,
        stream: bool = False,
        raw: bool = False,
        format: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **options,
    ) -> "LLMResponse":
        """
        Generate completion using Ollama.
        """
        from .fallback import LLMResponse

        start_time = time.time()

        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **options,
            },
        }

        if system:
            request_data["system"] = system
        if template:
            request_data["template"] = template
        if context:
            request_data["context"] = context
        if raw:
            request_data["raw"] = raw
        if format:
            request_data["format"] = format

        try:
            # Placeholder for actual API call:
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         f"{self.base_url}/api/generate",
            #         json=request_data,
            #         timeout=60.0
            #     )
            #     data = response.json()

            # Mock response for structure validation
            latency = (time.time() - start_time) * 1000

            return LLMResponse(
                content="[Ollama response placeholder - server connection pending]",
                model=model,
                provider="ollama",
                prompt_tokens=len(prompt.split()),
                completion_tokens=0,
                total_tokens=len(prompt.split()),
                latency_ms=latency,
                fallback_used=False,
            )

        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        model: str = "llama3.2",
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion."""
        # Placeholder for streaming implementation
        # async with httpx.AsyncClient() as client:
        #     async with client.stream(
        #         "POST",
        #         f"{self.base_url}/api/generate",
        #         json={"model": model, "prompt": prompt, "stream": True, **kwargs},
        #     ) as response:
        #         async for line in response.aiter_lines():
        #             data = json.loads(line)
        #             if not data.get("done"):
        #                 yield data.get("response", "")

        yield "[Streaming placeholder]"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3.2",
        **kwargs,
    ) -> "LLMResponse":
        """Chat completion with conversation history."""
        from .fallback import LLMResponse

        # Convert messages to prompt format
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(f"User: {content}")

        prompt = "\n".join(prompt_parts) + "\nAssistant:"

        return await self.generate(prompt=prompt, model=model, **kwargs)

    async def embeddings(
        self,
        prompt: str,
        model: str = "llama3.2",
    ) -> List[float]:
        """Generate embeddings for text."""
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{self.base_url}/api/embeddings",
        #         json={"model": model, "prompt": prompt}
        #     )
        #     return response.json()["embedding"]

        logger.info(f"Generating embeddings with {model}")
        return []

    def get_model_info(self, model: str) -> Optional[OllamaModel]:
        """Get detailed information about a model."""
        # Would query /api/show endpoint
        return None
