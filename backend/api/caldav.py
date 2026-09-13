"""CalDAV 只读子集 — 支持 PROPFIND / OPTIONS / GET / 简化 REPORT。

客户端可用账号密码（HTTP Basic）拉取日历，适用于 Thunderbird / Apple Calendar 只读订阅。
完整读写 CalDAV（PUT/DELETE/sync-token）后续再扩。
"""
from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Tuple
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from core.config import settings
from core.security import verify_password
from db.database import get_db
from db.models.calendar import CalendarEvent
from db.models.user import User
from core.calendar_ics import build_rrule

logger = logging.getLogger(__name__)
router = APIRouter(tags=["CalDAV"])

NS_DAV = "DAV:"
NS_CALENDAR = "urn:ietf:params:xml:ns:caldav"


def _parse_basic_auth(request: Request) -> Optional[Tuple[str, str]]:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return None
    try:
        raw = base64.b64decode(header[6:]).decode("utf-8")
        username, _, password = raw.partition(":")
        return unquote(username), password
    except Exception:
        return None


def _authenticate(request: Request, db: Session) -> Optional[User]:
    creds = _parse_basic_auth(request)
    if not creds:
        return None
    username, password = creds
    user = db.query(User).filter(User.email == username).first()
    if not user or not user.is_active:
        return None
    # SSO 用户无可用密码
    if not user.password_hash or user.password_hash == "!SSO_USER_NO_PASSWORD":
        return None
    try:
        if not verify_password(password, user.password_hash):
            return None
    except Exception:
        return None
    return user


def _unauthorized() -> Response:
    return Response(
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="TalentMail CalDAV"', "Content-Type": "text/plain"},
        content="Unauthorized",
    )


def _xml_escape(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _multistatus(inner: str) -> Response:
    body = f'''<?xml version="1.0" encoding="utf-8"?>
<D:multistatus xmlns:D="{NS_DAV}" xmlns:C="{NS_CALENDAR}">
{inner}
</D:multistatus>'''.encode("utf-8")
    return Response(content=body, status_code=207, media_type="application/xml; charset=utf-8")


def _event_to_ics(event: CalendarEvent) -> str:
    lines = ["BEGIN:VEVENT"]
    uid = getattr(event, "caldav_uid", None) or f"talentmail-{event.id}@{settings.BASE_DOMAIN}"
    lines.append(f"UID:{uid}")
    lines.append(f"SUMMARY:{(event.title or '').replace(chr(13), ' ').replace(chr(10), ' ')}")
    start = event.start_time
    end = event.end_time
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    lines.append(f"DTSTART:{start.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    lines.append(f"DTEND:{end.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    if event.location:
        lines.append(f"LOCATION:{event.location}")
    if event.description:
        desc = (event.description or "").replace("\n", "\\n")
        lines.append(f"DESCRIPTION:{desc}")
    rrule = build_rrule(event.recurrence, event.recurrence_until)
    if rrule:
        lines.append(f"RRULE:{rrule}")
    lines.append("END:VEVENT")
    return "\r\n".join(lines)


def _calendar_ics(db: Session, user: User) -> str:
    events = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.user_id == user.id)
        .order_by(CalendarEvent.start_time.asc())
        .limit(500)
        .all()
    )
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parts = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TalentMail//CalDAV//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{user.email}",
    ]
    for ev in events:
        parts.append(_event_to_ics(ev))
    parts.append("END:VCALENDAR")
    return "\r\n".join(parts) + "\r\n"


@router.api_route("/.well-known/caldav", methods=["GET", "OPTIONS", "PROPFIND", "REPORT", "PUT", "DELETE", "HEAD"])
@router.api_route("/caldav", methods=["GET", "OPTIONS", "PROPFIND", "REPORT", "PUT", "DELETE", "HEAD"])
@router.api_route("/caldav/{path:path}", methods=["GET", "OPTIONS", "PROPFIND", "REPORT", "PUT", "DELETE", "HEAD"])
async def caldav_entry(
    request: Request,
    path: str = "",
    db: Session = Depends(get_db),
):
    method = request.method.upper()
    user_path = unquote(path or "").strip("/")

    if method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "DAV": "1, calendar-access, calendar-schedule",
                "Allow": "OPTIONS, GET, HEAD, PUT, DELETE, PROPFIND, REPORT",
            },
        )

    user = _authenticate(request, db)
    if not user:
        return _unauthorized()

    base = f"/caldav/{user.email}"
    home = f"{base}/"
    calendar = f"{base}/calendar/"

    # 根 / well-known → 重定向到用户 home
    if user_path in ("", ".well-known/caldav"):
        if method == "GET":
            return Response(status_code=301, headers={"Location": home})
        # PROPFIND 当前用户 principal
        principal_href = home
        inner = f'''<D:response>
  <D:href>/caldav/</D:href>
  <D:propstat>
    <D:prop>
      <D:current-user-principal><D:href>{principal_href}</D:href></D:current-user-principal>
      <D:resourcetype><D:collection/></D:resourcetype>
    </D:prop>
    <D:status>HTTP/1.1 200 OK</D:status>
  </D:propstat>
</D:response>'''
        return _multistatus(inner)

    # 用户 home
    if user_path in (user.email, f"{user.email}/"):
        if method == "GET":
            return Response(status_code=301, headers={"Location": calendar})
        inner = f'''<D:response>
  <D:href>{home}</D:href>
  <D:propstat>
    <D:prop>
      <D:displayname>{_xml_escape(user.email)}</D:displayname>
      <D:resourcetype><D:collection/><D:principal/></D:resourcetype>
      <C:calendar-home-set><D:href>{home}</D:href></C:calendar-home-set>
    </D:prop>
    <D:status>HTTP/1.1 200 OK</D:status>
  </D:propstat>
</D:response>'''
        return _multistatus(inner)

    # calendar 集合
    if user_path in (f"{user.email}/calendar", f"{user.email}/calendar/"):
        if method == "GET":
            ics = _calendar_ics(db, user)
            return Response(
                content=ics,
                media_type="text/calendar; charset=utf-8",
                headers={"Content-Disposition": 'attachment; filename="talentmail.ics"'},
            )
        # PROPFIND / REPORT calendar-collection
        etag = f'"{user.id}-{int(datetime.now(timezone.utc).timestamp())}"'
        inner = f'''<D:response>
  <D:href>{calendar}</D:href>
  <D:propstat>
    <D:prop>
      <D:displayname>TalentMail Calendar</D:displayname>
      <D:resourcetype><D:collection/><C:calendar/></D:resourcetype>
      <D:getetag>{etag}</D:getetag>
      <C:supported-calendar-component-set>
        <C:comp name="VEVENT"/>
      </C:supported-calendar-component-set>
      <C:calendar-timezone>UTC</C:calendar-timezone>
    </D:prop>
    <D:status>HTTP/1.1 200 OK</D:status>
  </D:propstat>
</D:response>'''
        return _multistatus(inner)

    # 单个事件资源: {email}/calendar/{uid}.ics
    event_prefix = f"{user.email}/calendar/"
    if user_path.startswith(event_prefix) and user_path != event_prefix:
        filename = user_path[len(event_prefix):]
        if filename in ("", "calendar.ics"):
            ics = _calendar_ics(db, user)
            return Response(content=ics, media_type="text/calendar; charset=utf-8")
        # 去掉 .ics 后缀得到 UID
        uid = filename[:-4] if filename.endswith(".ics") else filename
        href = f"{calendar}{uid}.ics"
        event = (
            db.query(CalendarEvent)
            .filter(CalendarEvent.user_id == user.id, CalendarEvent.caldav_uid == uid)
            .first()
        )

        if method in ("GET", "HEAD"):
            if not event:
                return Response(status_code=404, content="Not Found")
            ics_body = _event_vevent_wrapper(event)
            headers = {"ETag": _event_etag(event), "Content-Type": "text/calendar; charset=utf-8"}
            if method == "HEAD":
                return Response(status_code=200, headers=headers)
            return Response(content=ics_body, media_type="text/calendar; charset=utf-8", headers=headers)

        if method == "PROPFIND":
            status = "HTTP/1.1 200 OK" if event else "HTTP/1.1 404 Not Found"
            etag = _event_etag(event) if event else ""
            getetag = f"<D:getetag>{etag}</D:getetag>" if event else ""
            inner = f'''<D:response>
  <D:href>{href}</D:href>
  <D:propstat>
    <D:prop>
      <D:resourcetype/>
      {getetag}
      <D:getcontenttype>text/calendar; charset=utf-8</D:getcontenttype>
    </D:prop>
    <D:status>{status}</D:status>
  </D:propstat>
</D:response>'''
            return _multistatus(inner)

        if method == "PUT":
            from core.caldav_write import parse_vevent_from_ics
            body = await request.body()
            parsed = parse_vevent_from_ics(body)
            if not parsed or not parsed.get("start_time"):
                return Response(status_code=400, content="Invalid VEVENT body")
            if not event:
                if db.query(CalendarEvent).filter(CalendarEvent.user_id == user.id).count() >= 500:
                    return Response(status_code=403, content="Calendar event limit reached")
                event = CalendarEvent(
                    user_id=user.id,
                    caldav_uid=uid,
                    title=parsed["title"],
                    start_time=parsed["start_time"],
                    end_time=parsed["end_time"] or parsed["start_time"],
                    color="#3B82F6",
                    recurrence="none",
                )
                db.add(event)
                created = True
            else:
                created = False
            event.title = parsed["title"]
            event.description = parsed.get("description")
            event.location = parsed.get("location")
            event.start_time = parsed["start_time"]
            event.end_time = parsed.get("end_time") or parsed["start_time"]
            event.all_day = bool(parsed.get("all_day"))
            event.recurrence = parsed.get("recurrence") or "none"
            event.recurrence_until = parsed.get("recurrence_until")
            db.commit()
            db.refresh(event)
            return Response(
                status_code=201 if created else 204,
                headers={"ETag": _event_etag(event)},
            )

        if method == "DELETE":
            if not event:
                return Response(status_code=404, content="Not Found")
            db.delete(event)
            db.commit()
            return Response(status_code=204)

    # calendar.ics 直链
    if user_path.endswith("calendar.ics") or user_path.endswith("calendar/export.ics"):
        ics = _calendar_ics(db, user)
        return Response(content=ics, media_type="text/calendar; charset=utf-8")

    return Response(status_code=404, content="Not Found")


def _event_etag(event: CalendarEvent) -> str:
    updated = event.updated_at.isoformat() if event.updated_at else str(event.id)
    return f'"{event.id}-{updated}"'


def _event_vevent_wrapper(event: CalendarEvent) -> str:
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//TalentMail//CalDAV//EN\r\n"
        f"{_event_to_ics(event)}\r\n"
        "END:VCALENDAR\r\n"
    )
