"""日历事件校验测试"""
import pytest
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError

from api.calendar import EventCreate, PRESET_COLORS


class TestEventCreate:
    def _base_payload(self):
        start = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
        return {
            "title": "站会",
            "start_time": start,
            "end_time": start + timedelta(hours=1),
        }

    def test_valid_event(self):
        event = EventCreate(**self._base_payload())
        assert event.title == "站会"
        assert event.all_day is False
        assert event.color == "#3B82F6"

    def test_title_stripped(self):
        payload = self._base_payload()
        payload["title"] = "  周会  "
        event = EventCreate(**payload)
        assert event.title == "周会"

    def test_empty_title_rejected(self):
        payload = self._base_payload()
        payload["title"] = "   "
        with pytest.raises(ValidationError):
            EventCreate(**payload)

    def test_end_before_start_rejected(self):
        payload = self._base_payload()
        payload["end_time"] = payload["start_time"] - timedelta(minutes=5)
        with pytest.raises(ValidationError):
            EventCreate(**payload)

    def test_title_max_length(self):
        payload = self._base_payload()
        payload["title"] = "x" * 300
        event = EventCreate(**payload)
        assert len(event.title) == 255

    def test_preset_colors_eight(self):
        assert len(PRESET_COLORS) == 8
        assert all(c.startswith("#") for c in PRESET_COLORS)
