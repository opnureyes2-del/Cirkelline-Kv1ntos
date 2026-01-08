"""
Rate Limiter
============
Protection against abuse and denial of service.

Responsibilities:
- Implement token bucket rate limiting
- Support sliding window rate limiting
- Track per-user and per-IP limits
- Provide graceful degradation
"""

import logging
import time
import threading
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"  # Allows bursts
    SLIDING_WINDOW = "sliding_window"  # Smooth limiting
    FIXED_WINDOW = "fixed_window"  # Simple counting
    LEAKY_BUCKET = "leaky_bucket"  # Constant rate


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10  # Max burst for token bucket
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    block_duration_seconds: int = 60  # How long to block after limit exceeded


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_at: float  # Unix timestamp
    retry_after: Optional[int] = None  # Seconds until retry
    limit: int = 0
    current: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "remaining": self.remaining,
            "reset_at": self.reset_at,
            "retry_after": self.retry_after,
            "limit": self.limit,
            "current": self.current,
        }

    def to_headers(self) -> Dict[str, str]:
        """Generate rate limit headers."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_at)),
        }
        if self.retry_after:
            headers["Retry-After"] = str(self.retry_after)
        return headers


# ═══════════════════════════════════════════════════════════════════════════════
# TOKEN BUCKET
# ═══════════════════════════════════════════════════════════════════════════════

class TokenBucket:
    """
    Token bucket rate limiter.

    Allows bursts up to bucket capacity, then limits to
    a steady rate of token refill.
    """

    def __init__(
        self,
        capacity: int,
        refill_rate: float,  # Tokens per second
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_update = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Returns True if successful, False if not enough tokens.
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_update = now

    def get_state(self) -> Dict[str, Any]:
        """Get current bucket state."""
        with self._lock:
            self._refill()
            return {
                "tokens": int(self.tokens),
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
            }


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDING WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class SlidingWindow:
    """
    Sliding window rate limiter.

    Tracks requests over a sliding time window for smooth
    rate limiting.
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self._lock = threading.Lock()

    def check(self) -> Tuple[bool, int]:
        """
        Check if request is allowed.

        Returns (allowed, remaining)
        """
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Remove old requests
            self.requests = [t for t in self.requests if t > cutoff]

            remaining = self.max_requests - len(self.requests)

            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True, remaining - 1

            return False, 0

    def get_reset_time(self) -> float:
        """Get time when oldest request expires."""
        with self._lock:
            if not self.requests:
                return time.time()
            return self.requests[0] + self.window_seconds

    def get_state(self) -> Dict[str, Any]:
        """Get current window state."""
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            active = [t for t in self.requests if t > cutoff]
            return {
                "current_requests": len(active),
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
            }


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """
    Comprehensive rate limiting engine.

    Supports multiple strategies and tracks limits per
    identifier (user ID, IP address, API key, etc.)
    """

    def __init__(self, default_config: Optional[RateLimitConfig] = None):
        self._default_config = default_config or RateLimitConfig()
        self._configs: Dict[str, RateLimitConfig] = {}

        # Per-identifier limiters
        self._token_buckets: Dict[str, TokenBucket] = {}
        self._sliding_windows: Dict[str, SlidingWindow] = {}

        # Blocked identifiers
        self._blocked: Dict[str, float] = {}  # identifier -> unblock_time

        # Statistics
        self._stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
        }

        self._lock = threading.Lock()

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════

    def set_config(self, identifier: str, config: RateLimitConfig) -> None:
        """Set rate limit config for a specific identifier."""
        self._configs[identifier] = config

    def set_default_config(self, config: RateLimitConfig) -> None:
        """Set default rate limit config."""
        self._default_config = config

    def _get_config(self, identifier: str) -> RateLimitConfig:
        """Get config for identifier."""
        return self._configs.get(identifier, self._default_config)

    # ═══════════════════════════════════════════════════════════════════════════
    # RATE LIMITING
    # ═══════════════════════════════════════════════════════════════════════════

    def check(
        self,
        identifier: str,
        cost: int = 1,
    ) -> RateLimitResult:
        """
        Check if request is allowed for identifier.

        Args:
            identifier: User ID, IP, or API key
            cost: Request cost (default 1)

        Returns:
            RateLimitResult
        """
        with self._lock:
            self._stats["total_requests"] += 1

        config = self._get_config(identifier)

        # Check if blocked
        if self._is_blocked(identifier):
            unblock_time = self._blocked.get(identifier, 0)
            retry_after = max(1, int(unblock_time - time.time()))
            self._stats["blocked_requests"] += 1
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=unblock_time,
                retry_after=retry_after,
                limit=config.requests_per_minute,
                current=config.requests_per_minute,
            )

        # Apply strategy
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            result = self._check_token_bucket(identifier, config, cost)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            result = self._check_sliding_window(identifier, config)
        else:
            result = self._check_sliding_window(identifier, config)

        if result.allowed:
            self._stats["allowed_requests"] += 1
        else:
            self._stats["blocked_requests"] += 1
            # Block identifier
            self._block(identifier, config.block_duration_seconds)

        return result

    def _check_token_bucket(
        self,
        identifier: str,
        config: RateLimitConfig,
        cost: int,
    ) -> RateLimitResult:
        """Check using token bucket strategy."""
        bucket = self._get_token_bucket(identifier, config)

        if bucket.consume(cost):
            state = bucket.get_state()
            return RateLimitResult(
                allowed=True,
                remaining=int(state["tokens"]),
                reset_at=time.time() + 60,  # Approximate
                limit=config.burst_size,
                current=config.burst_size - int(state["tokens"]),
            )
        else:
            state = bucket.get_state()
            tokens_needed = cost - int(state["tokens"])
            retry_after = int(tokens_needed / config.burst_size * 60)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=time.time() + retry_after,
                retry_after=retry_after,
                limit=config.burst_size,
                current=config.burst_size,
            )

    def _check_sliding_window(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check using sliding window strategy."""
        window = self._get_sliding_window(identifier, config)

        allowed, remaining = window.check()
        reset_at = window.get_reset_time()

        if allowed:
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_at=reset_at,
                limit=config.requests_per_minute,
                current=config.requests_per_minute - remaining,
            )
        else:
            retry_after = max(1, int(reset_at - time.time()))
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after,
                limit=config.requests_per_minute,
                current=config.requests_per_minute,
            )

    def _get_token_bucket(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> TokenBucket:
        """Get or create token bucket for identifier."""
        if identifier not in self._token_buckets:
            # Refill rate: requests per minute / 60 = requests per second
            refill_rate = config.requests_per_minute / 60.0
            self._token_buckets[identifier] = TokenBucket(
                capacity=config.burst_size,
                refill_rate=refill_rate,
            )
        return self._token_buckets[identifier]

    def _get_sliding_window(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> SlidingWindow:
        """Get or create sliding window for identifier."""
        if identifier not in self._sliding_windows:
            self._sliding_windows[identifier] = SlidingWindow(
                max_requests=config.requests_per_minute,
                window_seconds=60,
            )
        return self._sliding_windows[identifier]

    # ═══════════════════════════════════════════════════════════════════════════
    # BLOCKING
    # ═══════════════════════════════════════════════════════════════════════════

    def _is_blocked(self, identifier: str) -> bool:
        """Check if identifier is blocked."""
        if identifier not in self._blocked:
            return False

        unblock_time = self._blocked[identifier]
        if time.time() >= unblock_time:
            del self._blocked[identifier]
            return False

        return True

    def _block(self, identifier: str, duration_seconds: int) -> None:
        """Block an identifier."""
        self._blocked[identifier] = time.time() + duration_seconds
        logger.warning(f"Rate limited identifier: {identifier[:20]}...")

    def unblock(self, identifier: str) -> bool:
        """Manually unblock an identifier."""
        if identifier in self._blocked:
            del self._blocked[identifier]
            return True
        return False

    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is blocked (public API)."""
        return self._is_blocked(identifier)

    # ═══════════════════════════════════════════════════════════════════════════
    # MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def reset(self, identifier: str) -> None:
        """Reset all limits for an identifier."""
        with self._lock:
            self._token_buckets.pop(identifier, None)
            self._sliding_windows.pop(identifier, None)
            self._blocked.pop(identifier, None)

    def reset_all(self) -> None:
        """Reset all limits."""
        with self._lock:
            self._token_buckets.clear()
            self._sliding_windows.clear()
            self._blocked.clear()

    def cleanup_expired(self) -> int:
        """Remove expired blocks and stale limiters."""
        now = time.time()
        removed = 0

        with self._lock:
            # Clean up expired blocks
            expired = [k for k, v in self._blocked.items() if v <= now]
            for k in expired:
                del self._blocked[k]
                removed += 1

        return removed

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            **self._stats,
            "active_token_buckets": len(self._token_buckets),
            "active_sliding_windows": len(self._sliding_windows),
            "blocked_identifiers": len(self._blocked),
            "default_strategy": self._default_config.strategy.value,
            "default_requests_per_minute": self._default_config.requests_per_minute,
        }

    def get_identifier_stats(self, identifier: str) -> Dict[str, Any]:
        """Get stats for a specific identifier."""
        result = {
            "identifier": identifier[:20] + "...",
            "blocked": self._is_blocked(identifier),
        }

        if identifier in self._token_buckets:
            result["token_bucket"] = self._token_buckets[identifier].get_state()

        if identifier in self._sliding_windows:
            result["sliding_window"] = self._sliding_windows[identifier].get_state()

        if identifier in self._blocked:
            result["unblock_at"] = self._blocked[identifier]

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the singleton RateLimiter instance."""
    global _limiter_instance

    if _limiter_instance is None:
        _limiter_instance = RateLimiter(RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_size=20,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            block_duration_seconds=60,
        ))

    return _limiter_instance


async def init_rate_limiter() -> RateLimiter:
    """Initialize and return the rate limiter."""
    return get_rate_limiter()
