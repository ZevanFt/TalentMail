"""ICS 导出 RRULE 映射逻辑（纯规则，不依赖 icalendar）"""
from datetime import datetime, timezone

FREQ_MAP = {"daily": "DAILY", "weekly": "WEEKLY", "monthly": "MONTHLY"}


def build_rrule(recurrence: str | None, recurrence_until: datetime | None) -> str | None:
    freq = FREQ_MAP.get((recurrence or "none").lower())
    if not freq:
        return None
    rrule = f"FREQ={freq}"
    if recurrence_until:
        until = recurrence_until
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        rrule += f";UNTIL={until.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    return rrule
