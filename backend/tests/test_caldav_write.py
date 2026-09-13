"""CalDAV VEVENT 解析测试"""
from datetime import datetime, timezone

from core.caldav_write import parse_vevent_from_ics


SAMPLE = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:abc-123@example.com
SUMMARY:Team Sync
DESCRIPTION:Weekly sync\\nBring notes
LOCATION:Room B
DTSTART:20260310T090000Z
DTEND:20260310T100000Z
RRULE:FREQ=WEEKLY;UNTIL=20260401T000000Z
END:VEVENT
END:VCALENDAR
"""


class TestParseVevent:
    def test_basic_fields(self):
        parsed = parse_vevent_from_ics(SAMPLE)
        assert parsed is not None
        assert parsed["uid"] == "abc-123@example.com"
        assert parsed["title"] == "Team Sync"
        assert parsed["location"] == "Room B"
        assert parsed["start_time"] == datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
        assert parsed["end_time"] == datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
        assert parsed["recurrence"] == "weekly"
        assert parsed["recurrence_until"] == datetime(2026, 4, 1, tzinfo=timezone.utc)

    def test_invalid_body(self):
        assert parse_vevent_from_ics(b"not ics") is None

    def test_no_vevent(self):
        assert parse_vevent_from_ics(b"BEGIN:VCALENDAR\nEND:VCALENDAR\n") is None
