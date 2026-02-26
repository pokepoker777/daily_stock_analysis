# -*- coding: utf-8 -*-
"""
===================================
Token-Bucket Rate Limiter
===================================

Thread-safe rate limiter using the token-bucket algorithm.
Designed for throttling AI API calls (Gemini, OpenAI, etc.)
to stay within per-minute or per-second quotas.

Usage::

    from src.rate_limiter import RateLimiter

    # Allow 15 requests per minute
    limiter = RateLimiter(max_tokens=15, refill_period=60.0)

    limiter.acquire()  # blocks until a token is available
    response = call_ai_api(...)
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """
    Thread-safe token-bucket rate limiter.

    Parameters
    ----------
    max_tokens : int
        Maximum number of tokens (burst capacity).
    refill_period : float
        Seconds to fully refill the bucket from 0 → max_tokens.
    name : str
        Label used in log messages.
    """

    max_tokens: int = 15
    refill_period: float = 60.0
    name: str = "default"

    # internal state
    _tokens: float = field(init=False, repr=False)
    _last_refill: float = field(init=False, repr=False)
    _lock: threading.Lock = field(init=False, repr=False, default_factory=threading.Lock)

    def __post_init__(self):
        self._tokens = float(self.max_tokens)
        self._last_refill = time.monotonic()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def acquire(self, tokens: int = 1, timeout: float = 120.0) -> bool:
        """
        Block until *tokens* are available (or *timeout* expires).

        Returns True if tokens were acquired, False on timeout.
        """
        deadline = time.monotonic() + timeout

        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

            # Not enough tokens — wait for the next refill tick
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.warning(
                    f"[RateLimiter:{self.name}] acquire() timed out after {timeout}s"
                )
                return False

            # Sleep for a fraction of the refill interval
            wait = min(self.refill_period / self.max_tokens, remaining, 1.0)
            time.sleep(wait)

    def try_acquire(self, tokens: int = 1) -> bool:
        """Non-blocking acquire.  Returns True if tokens were available."""
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @property
    def available_tokens(self) -> float:
        """Current number of available tokens (approximate)."""
        with self._lock:
            self._refill()
            return self._tokens

    # ------------------------------------------------------------------ #
    #  Internal
    # ------------------------------------------------------------------ #

    def _refill(self):
        """Add tokens based on elapsed time since last refill."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return
        # tokens_per_second = max_tokens / refill_period
        new_tokens = elapsed * (self.max_tokens / self.refill_period)
        self._tokens = min(self.max_tokens, self._tokens + new_tokens)
        self._last_refill = now


# ------------------------------------------------------------------ #
#  Pre-configured limiters (singletons)
# ------------------------------------------------------------------ #

_registry: dict[str, RateLimiter] = {}
_registry_lock = threading.Lock()


def get_limiter(
    name: str,
    max_tokens: int = 15,
    refill_period: float = 60.0,
) -> RateLimiter:
    """
    Get or create a named rate limiter.

    The first call with a given *name* creates the limiter;
    subsequent calls return the same instance (singleton per name).
    """
    with _registry_lock:
        if name not in _registry:
            _registry[name] = RateLimiter(
                max_tokens=max_tokens,
                refill_period=refill_period,
                name=name,
            )
            logger.debug(
                f"[RateLimiter] Created '{name}': "
                f"{max_tokens} tokens / {refill_period}s"
            )
        return _registry[name]
