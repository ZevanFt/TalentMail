"""内存限流器测试"""
import time

from utils.rate_limit import MemoryRateLimiter, SlidingWindowLimiter


class TestMemoryRateLimiter:
    def test_first_call_allowed(self):
        limiter = MemoryRateLimiter(cooldown_seconds=1)
        assert limiter.allow("k1") is True

    def test_second_call_blocked_within_cooldown(self):
        limiter = MemoryRateLimiter(cooldown_seconds=60)
        assert limiter.allow("k1") is True
        assert limiter.allow("k1") is False

    def test_different_keys_independent(self):
        limiter = MemoryRateLimiter(cooldown_seconds=60)
        assert limiter.allow("a") is True
        assert limiter.allow("b") is True
        assert limiter.allow("a") is False

    def test_reset_allows_again(self):
        limiter = MemoryRateLimiter(cooldown_seconds=60)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False
        limiter.reset("k")
        assert limiter.allow("k") is True

    def test_cooldown_expiry(self):
        limiter = MemoryRateLimiter(cooldown_seconds=0.2)
        assert limiter.allow("k") is True
        time.sleep(0.25)
        assert limiter.allow("k") is True


class TestSlidingWindowLimiter:
    def test_allows_up_to_max(self):
        limiter = SlidingWindowLimiter(max_attempts=3, window_seconds=60)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is True
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False

    def test_remaining(self):
        limiter = SlidingWindowLimiter(max_attempts=2, window_seconds=60)
        assert limiter.remaining("k") == 2
        limiter.allow("k")
        assert limiter.remaining("k") == 1
        limiter.allow("k")
        assert limiter.remaining("k") == 0

    def test_window_slides(self):
        limiter = SlidingWindowLimiter(max_attempts=2, window_seconds=0.2)
        limiter.allow("k")
        limiter.allow("k")
        assert limiter.allow("k") is False
        time.sleep(0.25)
        assert limiter.allow("k") is True

    def test_reset(self):
        limiter = SlidingWindowLimiter(max_attempts=1, window_seconds=60)
        limiter.allow("k")
        assert limiter.allow("k") is False
        limiter.reset("k")
        assert limiter.allow("k") is True
