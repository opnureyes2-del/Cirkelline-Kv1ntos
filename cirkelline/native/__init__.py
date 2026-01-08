"""
Cirkelline Native Extensions
============================

High-performance Rust implementations with Python fallbacks.

Build native module:
    cd cirkelline/native
    maturin develop --release

Usage:
    from cirkelline.native import NativeCache, fast_hash

    # Uses Rust if available, falls back to Python
    cache = NativeCache(max_size=10000, ttl_seconds=300)
    cache.set("key", "value")
    value = cache.get("key")
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# Try to import native Rust module
NATIVE_AVAILABLE = False
try:
    from cirkelline_native import (
        NativeCache as _RustCache,
        fast_hash as _rust_hash,
        build_cache_key as _rust_build_key,
        batch_hash as _rust_batch_hash,
        extract_json_keys as _rust_extract_keys,
    )
    NATIVE_AVAILABLE = True
    logger.info("Native Rust extensions loaded - performance mode enabled")
except ImportError:
    logger.warning(
        "Native Rust extensions not available. "
        "Build with: cd cirkelline/native && maturin develop --release"
    )


# Python fallback implementations
class _PythonCache:
    """Pure Python LRU cache fallback."""

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, str] = {}
        self._stats = {"hits": 0, "misses": 0}

    def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            self._stats["hits"] += 1
            return self._cache[key]
        self._stats["misses"] += 1
        return None

    def set(self, key: str, value: str) -> None:
        if len(self._cache) >= self.max_size:
            # Simple eviction: remove first item
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[key] = value

    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        return key in self._cache

    def clear(self) -> None:
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "size": len(self._cache),
            "hit_rate": hit_rate,
        }

    def size(self) -> int:
        return len(self._cache)


def _python_hash(data: str) -> int:
    """Python fallback for fast_hash."""
    return int(hashlib.md5(data.encode()).hexdigest()[:16], 16)


def _python_build_key(parts: List[str]) -> str:
    """Python fallback for build_cache_key."""
    combined = ":".join(parts)
    if len(combined) > 200:
        return f"hash:{hashlib.md5(combined.encode()).hexdigest()}"
    return combined


def _python_batch_hash(items: List[str]) -> List[int]:
    """Python fallback for batch_hash."""
    return [_python_hash(item) for item in items]


def _python_extract_keys(json_str: str, keys: List[str]) -> Dict[str, str]:
    """Python fallback for extract_json_keys."""
    import json
    try:
        data = json.loads(json_str)
        return {k: str(data.get(k, "")) for k in keys if k in data}
    except json.JSONDecodeError:
        return {}


# Export the appropriate implementation
if NATIVE_AVAILABLE:
    NativeCache = _RustCache
    fast_hash = _rust_hash
    build_cache_key = _rust_build_key
    batch_hash = _rust_batch_hash
    extract_json_keys = _rust_extract_keys
else:
    NativeCache = _PythonCache
    fast_hash = _python_hash
    build_cache_key = _python_build_key
    batch_hash = _python_batch_hash
    extract_json_keys = _python_extract_keys


__all__ = [
    "NativeCache",
    "fast_hash",
    "build_cache_key",
    "batch_hash",
    "extract_json_keys",
    "NATIVE_AVAILABLE",
]
