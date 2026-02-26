import time
import pytest

from src.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_allows_calls_within_limit(self):
        limiter = RateLimiter(max_calls=3, period_seconds=1.0)
        start = time.monotonic()
        for _ in range(3):
            limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5

    def test_throttles_when_exceeded(self):
        limiter = RateLimiter(max_calls=2, period_seconds=1.0)
        limiter.wait()
        limiter.wait()
        start = time.monotonic()
        limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.5

    def test_reset(self):
        limiter = RateLimiter(max_calls=1, period_seconds=10.0)
        limiter.wait()
        limiter.reset()
        start = time.monotonic()
        limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5
