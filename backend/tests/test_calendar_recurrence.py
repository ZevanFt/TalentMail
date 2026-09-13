"""循环事件展开测试"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from core.calendar_recurrence import expand_event_occurrences


def _ev(**kwargs):
    base = dict(
        id=1,
        title="standup",
        description=None,
        location=None,
        start_time=datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 3, 2, 9, 30, tzinfo=timezone.utc),
        all_day=False,
        color="#3B82F6",
        reminder_minutes=None,
        recurrence="none",
        recurrence_until=None,
        source_email_id=None,
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        updated_at=None,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


WINDOW_START = datetime(2026, 3, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 3, 15, tzinfo=timezone.utc)


class TestExpand:
    def test_none_in_window(self):
        occ = expand_event_occurrences(_ev(), WINDOW_START, WINDOW_END)
        assert len(occ) == 1
        assert occ[0]["start_time"].startswith("2026-03-02")

    def test_none_out_of_window(self):
        ev = _ev(
            start_time=datetime(2026, 4, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
        )
        assert expand_event_occurrences(ev, WINDOW_START, WINDOW_END) == []

    def test_daily_expands(self):
        ev = _ev(recurrence="daily")
        occ = expand_event_occurrences(ev, WINDOW_START, WINDOW_END)
        # 3/2 到 3/14 共 13 天
        assert len(occ) == 13
        assert occ[0]["start_time"].startswith("2026-03-02")
        assert occ[-1]["start_time"].startswith("2026-03-14")

    def test_weekly_expands(self):
        ev = _ev(recurrence="weekly")
        occ = expand_event_occurrences(ev, WINDOW_START, WINDOW_END)
        assert len(occ) >= 2
        assert occ[1]["start_time"].startswith("2026-03-09")

    def test_until_limits(self):
        ev = _ev(
            recurrence="daily",
            recurrence_until=datetime(2026, 3, 4, 23, 59, tzinfo=timezone.utc),
        )
        occ = expand_event_occurrences(ev, WINDOW_START, WINDOW_END)
        assert len(occ) == 3  # 2,3,4

    def test_monthly(self):
        ev = _ev(
            recurrence="monthly",
            start_time=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 15, 11, 0, tzinfo=timezone.utc),
        )
        window_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        window_end = datetime(2026, 4, 1, tzinfo=timezone.utc)
        occ = expand_event_occurrences(ev, window_start, window_end)
        assert len(occ) == 3
        assert occ[1]["start_time"].startswith("2026-02-15")
