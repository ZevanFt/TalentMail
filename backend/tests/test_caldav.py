"""CalDAV XML / ICS 构造纯函数测试"""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from api.caldav import _event_to_ics, _multistatus, _xml_escape


class TestXmlHelpers:
    def test_escape(self):
        assert _xml_escape('a<b>&"c') == "a&lt;b&gt;&amp;&quot;c"

    def test_multistatus_xml(self):
        resp = _multistatus("<D:response/>")
        assert resp.status_code == 207
        body = resp.body.decode("utf-8")
        assert body.startswith("<?xml")
        assert "multistatus" in body


class TestEventIcs:
    def _ev(self):
        return SimpleNamespace(
            id=9,
            title="Standup\nDaily",
            description=None,
            location="Room A",
            start_time=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
            recurrence="weekly",
            recurrence_until=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )

    def test_ics_fields(self):
        text = _event_to_ics(self._ev())
        assert "BEGIN:VEVENT" in text
        assert "UID:talentmail-9@" in text
        assert "SUMMARY:Standup Daily" in text
        assert "DTSTART:20260310T090000Z" in text
        assert "LOCATION:Room A" in text
        assert "RRULE:FREQ=WEEKLY;UNTIL=20260401T000000Z" in text
