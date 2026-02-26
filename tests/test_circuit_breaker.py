# -*- coding: utf-8 -*-
"""Unit tests for the circuit breaker module."""

import time
import unittest

from src.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    get_circuit_breaker,
)


class TestCircuitBreakerStates(unittest.TestCase):
    def test_initial_state_closed(self):
        cb = CircuitBreaker(name="t1", failure_threshold=3, cooldown=1.0)
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertTrue(cb.is_closed)

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(name="t2", failure_threshold=3, cooldown=60.0)
        for _ in range(3):
            cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreaker(name="t3", failure_threshold=5, cooldown=60.0)
        for _ in range(4):
            cb.record_failure()
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(name="t4", failure_threshold=3, cooldown=60.0)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # reset
        cb.record_failure()
        cb.record_failure()
        # Should still be closed (2 consecutive, not 3)
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_half_open_after_cooldown(self):
        cb = CircuitBreaker(name="t5", failure_threshold=2, cooldown=0.2)
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        time.sleep(0.3)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)

    def test_half_open_success_closes(self):
        cb = CircuitBreaker(
            name="t6", failure_threshold=2, cooldown=0.1, success_threshold=2
        )
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
        cb.record_success()
        cb.record_success()
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_half_open_failure_reopens(self):
        cb = CircuitBreaker(name="t7", failure_threshold=2, cooldown=0.1)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)


class TestCircuitBreakerContextManager(unittest.TestCase):
    def test_success_path(self):
        cb = CircuitBreaker(name="ctx1", failure_threshold=3)
        with cb:
            pass  # no exception = success
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_failure_path(self):
        cb = CircuitBreaker(name="ctx2", failure_threshold=2)
        for _ in range(2):
            try:
                with cb:
                    raise ValueError("boom")
            except ValueError:
                pass
        self.assertEqual(cb.state, CircuitState.OPEN)

    def test_open_raises_circuit_open_error(self):
        cb = CircuitBreaker(name="ctx3", failure_threshold=1, cooldown=60.0)
        try:
            with cb:
                raise RuntimeError("fail")
        except RuntimeError:
            pass
        self.assertEqual(cb.state, CircuitState.OPEN)
        with self.assertRaises(CircuitOpenError) as ctx:
            with cb:
                pass  # should not reach here
        self.assertEqual(ctx.exception.name, "ctx3")
        self.assertGreater(ctx.exception.remaining_seconds, 0)

    def test_allow_request(self):
        cb = CircuitBreaker(name="ctx4", failure_threshold=1, cooldown=60.0)
        self.assertTrue(cb.allow_request())
        cb.record_failure()
        self.assertFalse(cb.allow_request())


class TestCircuitBreakerReset(unittest.TestCase):
    def test_reset_to_closed(self):
        cb = CircuitBreaker(name="rst", failure_threshold=1, cooldown=60.0)
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        cb.reset()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertTrue(cb.allow_request())


class TestCircuitBreakerStats(unittest.TestCase):
    def test_stats_dict(self):
        cb = CircuitBreaker(name="stats_test", failure_threshold=3, cooldown=30.0)
        cb.record_failure()
        s = cb.stats()
        self.assertEqual(s["name"], "stats_test")
        self.assertEqual(s["state"], "closed")
        self.assertEqual(s["failure_count"], 1)
        self.assertEqual(s["failure_threshold"], 3)


class TestGetCircuitBreaker(unittest.TestCase):
    def test_singleton(self):
        a = get_circuit_breaker("singleton_cb_test", failure_threshold=3)
        b = get_circuit_breaker("singleton_cb_test", failure_threshold=99)
        self.assertIs(a, b)
        self.assertEqual(a.failure_threshold, 3)

    def test_different_names(self):
        a = get_circuit_breaker("cb_a")
        b = get_circuit_breaker("cb_b")
        self.assertIsNot(a, b)


if __name__ == "__main__":
    unittest.main()
