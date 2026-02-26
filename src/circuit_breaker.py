# -*- coding: utf-8 -*-
"""
===================================
Generic Circuit Breaker
===================================

Implements the Circuit Breaker pattern for external service calls.
Prevents cascading failures by short-circuiting requests to a
service that has been failing repeatedly.

States
------
- **CLOSED**  – Normal operation. Failures are counted.
- **OPEN**    – Service is considered down. Calls fail fast
                without hitting the real service.
- **HALF_OPEN** – After the cooldown, one probe request is
                  allowed through to test recovery.

Usage::

    from src.circuit_breaker import CircuitBreaker, CircuitOpenError

    cb = CircuitBreaker(name="gemini", failure_threshold=5, cooldown=60)

    try:
        with cb:
            result = call_external_api(...)
    except CircuitOpenError:
        # Service is down, use fallback
        ...
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a call is rejected because the circuit is open."""

    def __init__(self, name: str, remaining_seconds: float):
        self.name = name
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Circuit '{name}' is OPEN, retry in {remaining_seconds:.0f}s"
        )


@dataclass
class CircuitBreaker:
    """
    Thread-safe circuit breaker.

    Parameters
    ----------
    name : str
        Label for logging.
    failure_threshold : int
        Number of consecutive failures before opening the circuit.
    cooldown : float
        Seconds the circuit stays open before allowing a probe.
    success_threshold : int
        Consecutive successes in HALF_OPEN needed to close the circuit.
    """

    name: str = "default"
    failure_threshold: int = 5
    cooldown: float = 60.0
    success_threshold: int = 2

    # Internal state
    _state: CircuitState = field(init=False, default=CircuitState.CLOSED)
    _failure_count: int = field(init=False, default=0)
    _success_count: int = field(init=False, default=0)
    _last_failure_time: float = field(init=False, default=0.0)
    _lock: threading.Lock = field(init=False, default_factory=threading.Lock)

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_transition_to_half_open()
            return self._state

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._transition(CircuitState.CLOSED)
            else:
                # Reset failure count on any success in CLOSED state
                self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                # Probe failed, go back to OPEN
                self._transition(CircuitState.OPEN)
            elif (
                self._state == CircuitState.CLOSED
                and self._failure_count >= self.failure_threshold
            ):
                self._transition(CircuitState.OPEN)

    def allow_request(self) -> bool:
        """
        Check whether a request should be allowed.

        Returns True for CLOSED and HALF_OPEN states, False for OPEN.
        Automatically transitions OPEN → HALF_OPEN after cooldown.
        """
        with self._lock:
            self._maybe_transition_to_half_open()
            if self._state == CircuitState.OPEN:
                return False
            return True

    def reset(self) -> None:
        """Force-reset the circuit to CLOSED."""
        with self._lock:
            self._transition(CircuitState.CLOSED)

    # ------------------------------------------------------------------ #
    #  Context manager
    # ------------------------------------------------------------------ #

    def __enter__(self):
        with self._lock:
            self._maybe_transition_to_half_open()
            if self._state == CircuitState.OPEN:
                remaining = self.cooldown - (
                    time.monotonic() - self._last_failure_time
                )
                raise CircuitOpenError(self.name, max(remaining, 0))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.record_success()
        else:
            # Don't count CircuitOpenError as a failure
            if not isinstance(exc_val, CircuitOpenError):
                self.record_failure()
        return False  # don't suppress exceptions

    # ------------------------------------------------------------------ #
    #  Diagnostics
    # ------------------------------------------------------------------ #

    def stats(self) -> dict:
        """Return a snapshot of current circuit state for monitoring."""
        with self._lock:
            self._maybe_transition_to_half_open()
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "cooldown": self.cooldown,
            }

    # ------------------------------------------------------------------ #
    #  Internal
    # ------------------------------------------------------------------ #

    def _maybe_transition_to_half_open(self) -> None:
        """Transition OPEN → HALF_OPEN if cooldown has elapsed (caller holds lock)."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.cooldown:
                self._transition(CircuitState.HALF_OPEN)

    def _transition(self, new_state: CircuitState) -> None:
        """Perform a state transition (caller holds lock)."""
        old = self._state
        self._state = new_state
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0
        logger.info(
            f"[CircuitBreaker:{self.name}] {old.value} → {new_state.value}"
        )


# ------------------------------------------------------------------ #
#  Registry (singleton per name)
# ------------------------------------------------------------------ #

_registry: dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    cooldown: float = 60.0,
    success_threshold: int = 2,
) -> CircuitBreaker:
    """Get or create a named circuit breaker (singleton per name)."""
    with _registry_lock:
        if name not in _registry:
            _registry[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                cooldown=cooldown,
                success_threshold=success_threshold,
            )
        return _registry[name]
