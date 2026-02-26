# -*- coding: utf-8 -*-
"""Unit tests for the token-bucket rate limiter."""

import threading
import time
import unittest

from src.rate_limiter import RateLimiter, get_limiter


class TestRateLimiter(unittest.TestCase):
    def test_initial_tokens(self):
        rl = RateLimiter(max_tokens=10, refill_period=60.0, name="test_init")
        self.assertAlmostEqual(rl.available_tokens, 10.0, places=0)

    def test_acquire_decrements(self):
        rl = RateLimiter(max_tokens=5, refill_period=60.0, name="test_dec")
        self.assertTrue(rl.acquire(tokens=1, timeout=1))
        self.assertAlmostEqual(rl.available_tokens, 4.0, delta=0.5)

    def test_try_acquire_non_blocking(self):
        rl = RateLimiter(max_tokens=2, refill_period=60.0, name="test_try")
        self.assertTrue(rl.try_acquire())
        self.assertTrue(rl.try_acquire())
        # All tokens consumed
        self.assertFalse(rl.try_acquire())

    def test_refill_over_time(self):
        rl = RateLimiter(max_tokens=10, refill_period=1.0, name="test_refill")
        # Drain all tokens
        for _ in range(10):
            rl.try_acquire()
        self.assertAlmostEqual(rl.available_tokens, 0.0, delta=0.5)
        # Wait for partial refill
        time.sleep(0.3)
        tokens = rl.available_tokens
        self.assertGreater(tokens, 0.0)

    def test_acquire_blocks_until_refill(self):
        rl = RateLimiter(max_tokens=1, refill_period=0.5, name="test_block")
        rl.try_acquire()  # drain
        start = time.monotonic()
        ok = rl.acquire(tokens=1, timeout=2.0)
        elapsed = time.monotonic() - start
        self.assertTrue(ok)
        self.assertGreater(elapsed, 0.1)  # had to wait

    def test_acquire_timeout(self):
        rl = RateLimiter(max_tokens=1, refill_period=999.0, name="test_timeout")
        rl.try_acquire()  # drain
        ok = rl.acquire(tokens=1, timeout=0.2)
        self.assertFalse(ok)

    def test_max_tokens_cap(self):
        rl = RateLimiter(max_tokens=3, refill_period=0.1, name="test_cap")
        time.sleep(0.5)  # way more than refill period
        # Tokens should be capped at max_tokens
        self.assertAlmostEqual(rl.available_tokens, 3.0, delta=0.5)

    def test_thread_safety(self):
        rl = RateLimiter(max_tokens=100, refill_period=60.0, name="test_thread")
        results = []

        def worker():
            for _ in range(10):
                results.append(rl.try_acquire())

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 100 should succeed
        self.assertEqual(sum(results), 100)
        self.assertEqual(len(results), 100)


class TestGetLimiter(unittest.TestCase):
    def test_singleton_per_name(self):
        a = get_limiter("singleton_test_a", max_tokens=5, refill_period=10.0)
        b = get_limiter("singleton_test_a", max_tokens=99, refill_period=1.0)
        self.assertIs(a, b)
        # Original params should be retained
        self.assertEqual(a.max_tokens, 5)

    def test_different_names(self):
        a = get_limiter("test_name_1", max_tokens=5)
        b = get_limiter("test_name_2", max_tokens=10)
        self.assertIsNot(a, b)
        self.assertEqual(a.max_tokens, 5)
        self.assertEqual(b.max_tokens, 10)


if __name__ == "__main__":
    unittest.main()
