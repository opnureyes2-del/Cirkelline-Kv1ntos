"""
CIRKELLINE WEB3 LOCAL LLM FALLBACK MODULE
==========================================

MP-002: Local LLM Integration for Offline Capability

This module provides a local LLM fallback using Ollama for
scenarios where cloud-based AI services are unavailable.

Features:
- Ollama integration for local model execution
- llama.cpp support for GGUF models
- Automatic fallback when cloud services fail
- Model management and caching

Status: IMPLEMENTED
"""

from .fallback import (
    LocalLLMFallback,
    FallbackConfig,
    FallbackMode,
    ModelInfo,
    get_llm_fallback,
)
from .ollama import OllamaClient, OllamaModel, OllamaResponse
from .llamacpp import LlamaCppEngine, LlamaCppConfig

__all__ = [
    "LocalLLMFallback",
    "FallbackConfig",
    "FallbackMode",
    "ModelInfo",
    "OllamaClient",
    "OllamaModel",
    "OllamaResponse",
    "LlamaCppEngine",
    "LlamaCppConfig",
    "get_llm_fallback",
]
