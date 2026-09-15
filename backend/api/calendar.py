"""日历 API — 事件 CRUD + .ics 导入"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator

from db.database import get_db
from api.deps import get_current_user
from core.config import settings
from db.models.user import User
from db.models.calendar import CalendarEvent
from core.calendar_recurrence import expand_event_occurrences
from core.calendar_ics import build_rrule
from utils.rate_limit import SlidingWindowLimiter

logger = logging.getLogger(__name__)
_event_limiter = SlidingWindowLimiter(max_attempts=30, window_seconds=60)
_ics_limiter = SlidingWindowLimiter(max_attempts=5, window_seconds=60)
router = APIRouter(prefix="/calendar", tags=["Calendar"])

MAX_EVENTS_PER_USER = 500
MAX_ICS_SIZE = 5 * 1024 * 1024  # 5 MB

# 预设颜色
PRESET_COLORS = [
    "#3B82F6",  # 蓝
    "#EF4444",  # 红
    "#10B981",  # 绿
    "#F59E0B",  # 橙
    "#8B5CF6",  # 紫
    "#EC4899",  # 粉
    "#06B6D4",  # 青
    "#6B7280",  # 灰
]


# ---- Schemas ----

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    color: str = "#3B82F6"
    reminder_minutes: Optional[int] = None
    recurrence: str = "none"
    recurrence_until: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("标题不能为空")
        return v.strip()[:255]

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        start = info.data.get("start_time")
        if start and v < start:
            raise ValueError("结束时间不能早于开始时间")
        return v

    @field_validator("recurrence")
    @classmethod
    def valid_recurrence(cls, v: str) -> str:
        allowed = {"none", "daily", "weekly", "monthly"}
        value = (v or "none").lower()
        if value not in allowed:
            raise ValueError(f"recurrence 必须是 {sorted(allowed)} 之一")
        return value


class EventUpdate(EventCreate):
    pass


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    location: Optional[str]
    start_time: datetime
    end_time: datetime
    all_day: bool
    color: str
    reminder_minutes: Optional[int]
    recurrence: str = "none"
    recurrence_until: Optional[datetime] = None
    source_email_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class IcsImportResult(BaseModel):
    total_found: int
    imported: int
    skipped: int
    errors: list[str]


# ---- Endpoints ----

@router.get("", response_model=List[EventResponse])
def list_events(
    start: Optional[datetime] = Query(None, description="范围开始（含）"),
    end: Optional[datetime] = Query(None, description="范围结束（含）"),
    expand: bool = Query(True, description="是否展开循环事件实例"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取日期范围内的事件（默认当月，最多 500 条；循环事件可展开）"""
    from datetime import timezone as _tz
    now = datetime.now(_tz.utc)
    window_start = start or now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    window_end = end or (window_start + timedelta(days=62))

    query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user.id)
    # 宽松过滤：非循环事件用 end/start；循环事件只要原始开始不晚于窗口结束
    query = query.filter(
        (CalendarEvent.recurrence.is_(None))
        | (CalendarEvent.recurrence == "none")
        | (CalendarEvent.start_time <= window_end)
    )
    query = query.order_by(CalendarEvent.start_time.asc())
    rows = query.limit(MAX_EVENTS_PER_USER).all()

    if not expand:
        return rows

    expanded: List[EventResponse] = []
    for ev in rows:
        for occ in expand_event_occurrences(ev, window_start, window_end):
            expanded.append(EventResponse(
                id=occ["id"],
                title=occ["title"],
                description=occ["description"],
                location=occ["location"],
                start_time=datetime.fromisoformat(occ["start_time"]),
                end_time=datetime.fromisoformat(occ["end_time"]),
                all_day=occ["all_day"],
                color=occ["color"],
                reminder_minutes=occ["reminder_minutes"],
                recurrence=occ["recurrence"],
                recurrence_until=datetime.fromisoformat(occ["recurrence_until"]) if occ["recurrence_until"] else None,
                source_email_id=occ["source_email_id"],
                created_at=datetime.fromisoformat(occ["created_at"]) if occ["created_at"] else now,
                updated_at=datetime.fromisoformat(occ["updated_at"]) if occ["updated_at"] else None,
            ))
    expanded.sort(key=lambda e: e.start_time)
    return expanded


@router.post("", response_model=EventResponse)
def create_event(
    data: EventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建日历事件"""
    if not _event_limiter.allow(f"cal_create:{user.id}"):
        raise HTTPException(429, "操作过于频繁，请稍后再试")
    count = db.query(CalendarEvent).filter(CalendarEvent.user_id == user.id).count()
    if count >= MAX_EVENTS_PER_USER:
        raise HTTPException(400, f"事件数量已达上限（{MAX_EVENTS_PER_USER}）")

    event = CalendarEvent(
        user_id=user.id,
        title=data.title,
        description=data.description,
        location=data.location,
        start_time=data.start_time,
        end_time=data.end_time,
        all_day=data.all_day,
        color=data.color,
        reminder_minutes=data.reminder_minutes,
        recurrence=data.recurrence or "none",
        recurrence_until=data.recurrence_until,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info(f"用户 {user.id} 创建日历事件: id={event.id}, title={event.title}")
    return event


# 注意：固定路径必须注册在 /{event_id} 之前，否则会被当成 event_id
@router.get("/export.ics")
def export_ics(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """导出用户日历为标准 .ics 文件"""
    if not _ics_limiter.allow(f"ics_export:{user.id}"):
        raise HTTPException(429, "导出过于频繁，请稍后再试")

    query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user.id)
    if start:
        query = query.filter(CalendarEvent.end_time >= start)
    if end:
        query = query.filter(CalendarEvent.start_time <= end)
    events = query.order_by(CalendarEvent.start_time.asc()).limit(MAX_EVENTS_PER_USER).all()

    try:
        from icalendar import Calendar, Event as ICalEvent
    except ImportError:
        raise HTTPException(500, "服务端缺少 icalendar 依赖")

    from datetime import timezone as _tz
    cal = Calendar()
    cal.add("prodid", "-//TalentMail//Calendar Export//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")

    now = datetime.now(_tz.utc)
    for ev in events:
        item = ICalEvent()
        item.add("uid", f"talentmail-{ev.id}@{settings.BASE_DOMAIN}")
        item.add("summary", ev.title or "(no title)")
        item.add("dtstart", ev.start_time)
        item.add("dtend", ev.end_time)
        item.add("dtstamp", now)
        if ev.description:
            item.add("description", ev.description)
        if ev.location:
            item.add("location", ev.location)
        if ev.all_day:
            item.add("transp", "TRANSPARENT")
        # 简化 RRULE 映射
        rrule = build_rrule(ev.recurrence, ev.recurrence_until)
        if rrule:
            item.add("rrule", rrule)
        cal.add_component(item)

    body = cal.to_ical()
    from fastapi.responses import Response
    return Response(
        content=body,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="talentmail-calendar-{now.strftime("%Y%m%d")}.ics"',
        },
    )


@router.post("/import-ics", response_model=IcsImportResult)
async def import_ics(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """导入 .ics 日历文件"""
    if not _ics_limiter.allow(f"ics_import:{user.id}"):
        raise HTTPException(429, "导入过于频繁，请稍后再试")
    filename = (file.filename or "").lower()
    if not filename.endswith(".ics"):
        raise HTTPException(400, "仅支持 .ics 格式")

    content = await file.read()
    if len(content) > MAX_ICS_SIZE:
        raise HTTPException(413, f"文件大小超过限制 ({MAX_ICS_SIZE // 1024 // 1024}MB)")

    try:
        from icalendar import Calendar
    except ImportError:
        raise HTTPException(500, "服务端缺少 icalendar 依赖")

    try:
        cal = Calendar.from_ical(content)
    except Exception as e:
        raise HTTPException(400, f"无法解析 .ics 文件: {str(e)[:200]}")

    # 统计现有事件数
    existing_count = db.query(CalendarEvent).filter(CalendarEvent.user_id == user.id).count()

    total_found = 0
    imported = 0
    skipped = 0
    errors: list[str] = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        total_found += 1

        if existing_count + imported >= MAX_EVENTS_PER_USER:
            skipped += 1
            errors.append(f"事件数量已达上限 ({MAX_EVENTS_PER_USER})")
            continue

        try:
            title = str(component.get("SUMMARY", "无标题"))[:255]
            description = str(component.get("DESCRIPTION", "")) or None
            location = str(component.get("LOCATION", "")) or None

            dt_start = component.get("DTSTART")
            dt_end = component.get("DTEND")

            if not dt_start:
                skipped += 1
                errors.append(f"「{title}」: 缺少开始时间")
                continue

            start_dt = dt_start.dt
            # 处理 date 类型（全天事件）
            is_all_day = not isinstance(start_dt, datetime)
            if is_all_day:
                start_time = datetime.combine(start_dt, datetime.min.time(), tzinfo=timezone.utc)
                if dt_end:
                    end_dt = dt_end.dt
                    end_time = datetime.combine(end_dt, datetime.min.time(), tzinfo=timezone.utc)
                else:
                    end_time = start_time + timedelta(days=1)
            else:
                start_time = start_dt if start_dt.tzinfo else start_dt.replace(tzinfo=timezone.utc)
                if dt_end:
                    end_dt = dt_end.dt
                    end_time = end_dt if end_dt.tzinfo else end_dt.replace(tzinfo=timezone.utc)
                else:
                    end_time = start_time + timedelta(hours=1)

            event = CalendarEvent(
                user_id=user.id,
                title=title,
                description=description[:5000] if description else None,
                location=location[:500] if location else None,
                start_time=start_time,
                end_time=end_time,
                all_day=is_all_day,
                color="#3B82F6",
            )
            db.add(event)
            imported += 1

        except Exception as e:
            skipped += 1
            errors.append(f"解析事件失败: {str(e)[:100]}")

    db.commit()
    logger.info(f"用户 {user.id} 导入日历: 找到 {total_found}, 导入 {imported}, 跳过 {skipped}")

    return IcsImportResult(
        total_found=total_found,
        imported=imported,
        skipped=skipped,
        errors=errors[:20],
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取事件详情"""
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.user_id == user.id,
    ).first()
    if not event:
        raise HTTPException(404, "事件不存在")
    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    data: EventUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新日历事件"""
    if not _event_limiter.allow(f"cal_update:{user.id}"):
        raise HTTPException(429, "操作过于频繁，请稍后再试")
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.user_id == user.id,
    ).first()
    if not event:
        raise HTTPException(404, "事件不存在")

    event.title = data.title
    event.description = data.description
    event.location = data.location
    event.start_time = data.start_time
    event.end_time = data.end_time
    event.all_day = data.all_day
    event.color = data.color
    event.reminder_minutes = data.reminder_minutes
    event.recurrence = data.recurrence or "none"
    event.recurrence_until = data.recurrence_until
    db.commit()
    db.refresh(event)
    logger.info(f"用户 {user.id} 更新日历事件: id={event.id}, title={event.title}")
    return event


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除日历事件"""
    event = db.query(CalendarEvent).filter(
        CalendarEvent.id == event_id,
        CalendarEvent.user_id == user.id,
    ).first()
    if not event:
        raise HTTPException(404, "事件不存在")

    event_title = event.title
    db.delete(event)
    db.commit()
    logger.info(f"用户 {user.id} 删除日历事件: id={event_id}, title={event_title}")
    return {"status": "success", "message": "事件已删除"}

