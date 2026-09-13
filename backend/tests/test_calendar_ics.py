"""ICS RRULE 构建测试"""
from datetime import datetime, timezone

from core.calendar_ics import build_rrule


class TestBuildRrule:
    def test_none_returns_none(self):
        assert build_rrule("none", None) is None
        assert build_rrule(None, None) is None

    def test_daily(self):
        assert build_rrule("daily", None) == "FREQ=DAILY"

    def test_weekly_with_until(self):
        until = datetime(2026, 3, 31, 23, 59, 59, tzinfo=timezone.utc)
        assert build_rrule("weekly", until) == "FREQ=WEEKLY;UNTIL=20260331T235959Z"

    def test_monthly_naive_until_assumed_utc(self):
        until = datetime(2026, 6, 1, 12, 0, 0)
        assert build_rrule("monthly", until) == "FREQ=MONTHLY;UNTIL=20260601T120000Z"
