"""日历循环事件展开（简化 RRULE：daily/weekly/monthly）"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

RECURRENCE_NONE = "none"
RECURRENCE_DAILY = "daily"
RECURRENCE_WEEKLY = "weekly"
RECURRENCE_MONTHLY = "monthly"
VALID_RECURRENCES = {RECURRENCE_NONE, RECURRENCE_DAILY, RECURRENCE_WEEKLY, RECURRENCE_MONTHLY}

MAX_OCCURRENCES_PER_EVENT = 120


def _add_months(dt: datetime, months: int) -> datetime:
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return dt.replace(year=year, month=month, day=day)


def _next_occurrence(start: datetime, recurrence: str, index: int) -> datetime:
    if recurrence == RECURRENCE_DAILY:
        return start + timedelta(days=index)
    if recurrence == RECURRENCE_WEEKLY:
        return start + timedelta(weeks=index)
    if recurrence == RECURRENCE_MONTHLY:
        return _add_months(start, index)
    return start


def expand_event_occurrences(
    event: Any,
    window_start: datetime,
    window_end: datetime,
    *,
    id_field: str = "id",
) -> List[Dict[str, Any]]:
    """把单个事件展开为查询窗口内的实例列表。

    - 无重复：落在窗口内则返回 1 条
    - daily/weekly/monthly：从 start 起逐次推进，直到超出 until/窗口/上限
    返回的 dict 保留原事件字段，并附加 occurrence_start / occurrence_end。
    """
    start: datetime = event.start_time
    end: datetime = event.end_time
    if start.tzinfo is None:
        # 粗暴补 UTC，避免 naive/aware 比较失败
        start = start.replace(tzinfo=timezone.utc)
        end = end.replace(tzinfo=timezone.utc)
        if getattr(event, "recurrence_until", None) is not None and event.recurrence_until.tzinfo is None:
            recurrence_until = event.recurrence_until.replace(tzinfo=timezone.utc)
        else:
            recurrence_until = getattr(event, "recurrence_until", None)
    else:
        recurrence_until = getattr(event, "recurrence_until", None)

    recurrence = (getattr(event, "recurrence", None) or RECURRENCE_NONE).lower()
    duration = end - start

    base: Dict[str, Any] = {
        "id": getattr(event, id_field),
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "all_day": event.all_day,
        "color": event.color,
        "reminder_minutes": event.reminder_minutes,
        "recurrence": recurrence,
        "recurrence_until": recurrence_until.isoformat() if recurrence_until else None,
        "source_email_id": getattr(event, "source_email_id", None),
        "created_at": getattr(event, "created_at", None).isoformat() if getattr(event, "created_at", None) else None,
        "updated_at": getattr(event, "updated_at", None).isoformat() if getattr(event, "updated_at", None) else None,
    }

    if recurrence not in VALID_RECURRENCES or recurrence == RECURRENCE_NONE:
        if start < window_end and end > window_start:
            return [base]
        return []

    occurrences: List[Dict[str, Any]] = []
    i = 0
    while i < MAX_OCCURRENCES_PER_EVENT:
        occ_start = _next_occurrence(start, recurrence, i)
        if recurrence_until and occ_start > recurrence_until:
            break
        if occ_start >= window_end:
            break
        occ_end = occ_start + duration
        if occ_end > window_start:
            item = dict(base)
            item["start_time"] = occ_start.isoformat()
            item["end_time"] = occ_end.isoformat()
            occurrences.append(item)
        i += 1
    return occurrences
