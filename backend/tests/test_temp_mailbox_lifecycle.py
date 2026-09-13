"""临时邮箱生命周期纯函数测试"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from core.temp_mailbox_lifecycle import (
    DEFAULT_RECOVERABLE_DAYS,
    DEFAULT_TTL_HOURS,
    compute_new_expiry_windows,
)


def _policy(ttl_hours=DEFAULT_TTL_HOURS, recoverable_days=DEFAULT_RECOVERABLE_DAYS):
    return SimpleNamespace(ttl_hours=ttl_hours, recoverable_days=recoverable_days)


class TestComputeNewExpiryWindows:
    def test_default_windows(self):
        now = datetime(2026, 3, 8, 12, 0, 0, tzinfo=timezone.utc)
        expires, recovery = compute_new_expiry_windows(now, _policy())
        assert expires == now + timedelta(hours=DEFAULT_TTL_HOURS)
        assert recovery == expires + timedelta(days=DEFAULT_RECOVERABLE_DAYS)

    def test_custom_policy(self):
        now = datetime(2026, 3, 8, 12, 0, 0, tzinfo=timezone.utc)
        expires, recovery = compute_new_expiry_windows(now, _policy(ttl_hours=2, recoverable_days=3))
        assert expires == now + timedelta(hours=2)
        assert recovery == expires + timedelta(days=3)

    def test_minimum_ttl_enforced(self):
        now = datetime(2026, 3, 8, 12, 0, 0, tzinfo=timezone.utc)
        expires, _ = compute_new_expiry_windows(now, _policy(ttl_hours=0, recoverable_days=1))
        assert expires == now + timedelta(hours=1)

    def test_none_falls_back_to_default(self):
        now = datetime(2026, 3, 8, 12, 0, 0, tzinfo=timezone.utc)
        expires, recovery = compute_new_expiry_windows(now, _policy(ttl_hours=None, recoverable_days=None))
        assert expires == now + timedelta(hours=DEFAULT_TTL_HOURS)
        assert recovery == expires + timedelta(days=DEFAULT_RECOVERABLE_DAYS)
