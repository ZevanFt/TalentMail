"""CalDAV PUT 时解析 VEVENT → 本地字段"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _to_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def parse_vevent_from_ics(body: bytes | str) -> Optional[Dict[str, Any]]:
    """从 ICS 内容解析第一个 VEVENT。失败返回 None。"""
    try:
        from icalendar import Calendar
    except ImportError:
        return None

    if isinstance(body, bytes):
        raw = body
    else:
        raw = body.encode("utf-8", errors="replace")

    try:
        cal = Calendar.from_ical(raw)
    except Exception:
        return None

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        uid = str(component.get("UID") or "").strip() or None
        summary = str(component.get("SUMMARY") or "").strip() or "(no title)"
        description = component.get("DESCRIPTION")
        location = component.get("LOCATION")
        dtstart = component.get("DTSTART")
        dtend = component.get("DTEND")
        if dtstart is None:
            return None
        start = _to_aware(getattr(dtstart, "dt", None))
        if start is None:
            return None
        if dtend is not None:
            end = _to_aware(getattr(dtend, "dt", None))
        else:
            # 无 DTEND：全天默认 +1 天，否则 +1 小时
            from datetime import timedelta
            end = start + timedelta(days=1 if getattr(dtstart, "dt", None) and not isinstance(dtstart.dt, datetime) else 0)
            if end == start:
                end = start + timedelta(hours=1)
        if end is None:
            end = start

        all_day = False
        try:
            raw_start = getattr(dtstart, "dt", None)
            if raw_start is not None and not isinstance(raw_start, datetime):
                all_day = True
        except Exception:
            pass

        # RRULE → 简化 recurrence
        recurrence = "none"
        recurrence_until = None
        rrule = component.get("RRULE")
        if rrule is not None:
            def _first(val):
                if isinstance(val, (list, tuple)):
                    return val[0] if val else None
                return val

            freq = str(_first(rrule.get("FREQ")) or "").upper()
            mapping = {"DAILY": "daily", "WEEKLY": "weekly", "MONTHLY": "monthly"}
            recurrence = mapping.get(freq, "none")
            until = _first(rrule.get("UNTIL"))
            if until is not None:
                recurrence_until = _to_aware(getattr(until, "dt", None) if hasattr(until, "dt") else until)

        return {
            "uid": uid,
            "title": summary[:255],
            "description": str(description) if description is not None else None,
            "location": str(location) if location is not None else None,
            "start_time": start,
            "end_time": end,
            "all_day": all_day,
            "recurrence": recurrence,
            "recurrence_until": recurrence_until,
        }
    return None
