"""CalDAV 子集 — PROPFIND / OPTIONS / GET / PUT / DELETE / REPORT。

REPORT 支持 calendar-query、calendar-multiget、sync-collection（RFC 6578），
供 Thunderbird / Apple Calendar 增量同步。
"""
from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Tuple
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func
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
# RFC 6578 初始 sync-token（客户端全量同步起点）
INITIAL_SYNC_TOKEN = "http://calconnect.org/ns/caldav"


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
    if not user or not getattr(user, "is_active", True):
        return None
    # 应用专用密码优先（SSO 用户也可用）
    try:
        from core.app_passwords import verify_app_password
        if verify_app_password(db, user.id, password):
            return user
    except Exception as e:
        logger.debug(f"[CalDAV] app password verify failed: {e}")
    # 本地登录密码
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
                "DAV": "1, calendar-access, calendar-schedule, sync-collection",
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
        # REPORT on collection: calendar-query / multiget / sync-collection
        if method == "REPORT":
            return await _handle_report(request, db, user, calendar)

        # PROPFIND calendar-collection
        etag = f'"{user.id}-{int(datetime.now(timezone.utc).timestamp())}"'
        sync_token = _current_sync_token(db, user)
        inner = f'''<D:response>
  <D:href>{calendar}</D:href>
  <D:propstat>
    <D:prop>
      <D:displayname>TalentMail Calendar</D:displayname>
      <D:resourcetype><D:collection/><C:calendar/></D:resourcetype>
      <D:getetag>{etag}</D:getetag>
      <D:sync-token>{sync_token}</D:sync-token>
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


def _event_uid(event: CalendarEvent) -> str:
    return getattr(event, "caldav_uid", None) or f"talentmail-{event.id}@{settings.BASE_DOMAIN}"


def _current_sync_token(db: Session, user: User) -> str:
    """集合当前 sync-token：user_id + max(updated_at) + 事件数。

    数量下降表示发生过删除，旧 token 会失效（客户端需全量重同步，RFC 6578 409）。
    """
    row = (
        db.query(
            func.max(CalendarEvent.updated_at),
            func.count(CalendarEvent.id),
        )
        .filter(CalendarEvent.user_id == user.id)
        .one()
    )
    max_updated, count = row[0], int(row[1] or 0)
    ts = int(max_updated.timestamp() * 1000) if max_updated else 0
    return f"data:,u{user.id}-{ts}-{count}"


def _parse_sync_token_value(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    val = raw.strip()
    if not val or val == INITIAL_SYNC_TOKEN:
        return None
    # 允许带 XML 文本节点空白
    return val


def _token_meta(token: str) -> Optional[Tuple[int, int, int]]:
    """解析 data:,u{uid}-{ts_ms}-{count} → (uid, ts_ms, count)"""
    m = re.fullmatch(r"data:,u(\d+)-(\d+)-(\d+)", token.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _event_resource_xml(event: CalendarEvent, calendar_base: str, include_data: bool = True) -> str:
    uid = _event_uid(event)
    href = f"{calendar_base}{uid}.ics"
    etag = _event_etag(event)
    data_xml = ""
    if include_data:
        cal = _event_vevent_wrapper(event)
        cal_esc = cal.replace("&", "&amp;").replace("<", "&lt;")
        data_xml = f"<C:calendar-data>{cal_esc}</C:calendar-data>"
    return f'''<D:response>
  <D:href>{href}</D:href>
  <D:propstat>
    <D:prop>
      <D:getetag>{etag}</D:getetag>
      <D:getcontenttype>text/calendar; charset=utf-8</D:getcontenttype>
      {data_xml}
    </D:prop>
    <D:status>HTTP/1.1 200 OK</D:status>
  </D:propstat>
</D:response>'''


def _collect_local_names(elem) -> set:
    names = set()
    for el in elem.iter():
        tag = el.tag
        if isinstance(tag, str) and "}" in tag:
            names.add(tag.rsplit("}", 1)[-1])
        elif isinstance(tag, str):
            names.add(tag)
    return names


async def _handle_report(
    request: Request,
    db: Session,
    user: User,
    calendar_base: str,
) -> Response:
    """处理 calendar 集合上的 REPORT。"""
    body = await request.body()
    current_token = _current_sync_token(db, user)
    calendar = calendar_base  # ends with /

    root = None
    local_names: set = set()
    if body:
        try:
            try:
                from defusedxml import ElementTree as SafeET  # type: ignore
            except Exception:
                import xml.etree.ElementTree as SafeET  # type: ignore
            root = SafeET.fromstring(body)
            local_names = _collect_local_names(root)
        except Exception as e:
            logger.warning(f"[CalDAV] REPORT XML 解析失败: {e}")
            return Response(status_code=400, content="Invalid REPORT body")

    # ── sync-collection（RFC 6578）──
    if "sync-collection" in local_names:
        client_token_el = None
        for el in root.iter():
            tag = el.tag
            local = tag.rsplit("}", 1)[-1] if isinstance(tag, str) and "}" in tag else tag
            if local == "sync-token":
                client_token_el = el
                break
        client_token = _parse_sync_token_value(client_token_el.text if client_token_el is not None else None)

        # 初始/空 token → 全量
        if client_token is None:
            events = (
                db.query(CalendarEvent)
                .filter(CalendarEvent.user_id == user.id)
                .order_by(CalendarEvent.updated_at.asc())
                .limit(1000)
                .all()
            )
            inner_responses = "\n".join(_event_resource_xml(ev, calendar) for ev in events)
            inner = f'''{inner_responses}
<D:sync-token>{current_token}</D:sync-token>'''
            return _multistatus(inner)

        meta = _token_meta(client_token)
        if meta is None or meta[0] != user.id:
            # 非法 token → 409，客户端应空 token 重来
            return Response(
                status_code=409,
                media_type="application/xml; charset=utf-8",
                content=f'''<?xml version="1.0" encoding="utf-8"?>
<D:error xmlns:D="{NS_DAV}"><D:valid-sync-token/></D:error>''',
            )

        token_uid, token_ts, token_count = meta
        cur_meta = _token_meta(current_token)
        cur_ts = cur_meta[1] if cur_meta else 0
        cur_count = cur_meta[2] if cur_meta else 0

        # 发生过删除（数量下降）→ 旧 token 失效
        if cur_count < token_count:
            return Response(
                status_code=409,
                media_type="application/xml; charset=utf-8",
                content=f'''<?xml version="1.0" encoding="utf-8"?>
<D:error xmlns:D="{NS_DAV}"><D:valid-sync-token/></D:error>''',
            )

        # 无变化
        if cur_ts == token_ts and cur_count == token_count:
            return _multistatus(f"<D:sync-token>{current_token}</D:sync-token>")

        # 增量：updated_at 毫秒 > token_ts（创建/更新；删除走上面的 409）
        changed = (
            db.query(CalendarEvent)
            .filter(
                CalendarEvent.user_id == user.id,
                CalendarEvent.updated_at > datetime.fromtimestamp(token_ts / 1000.0, tz=timezone.utc),
            )
            .order_by(CalendarEvent.updated_at.asc())
            .limit(1000)
            .all()
        )
        inner_responses = "\n".join(_event_resource_xml(ev, calendar) for ev in changed)
        inner = f'''{inner_responses}
<D:sync-token>{current_token}</D:sync-token>'''
        return _multistatus(inner)

    # ── calendar-multiget ──
    if "calendar-multiget" in local_names:
        hrefs = []
        for el in root.iter():
            tag = el.tag
            local = tag.rsplit("}", 1)[-1] if isinstance(tag, str) and "}" in tag else tag
            if local == "href" and el.text:
                hrefs.append(el.text.strip())
        uids = []
        for href in hrefs:
            name = href.rstrip("/").rsplit("/", 1)[-1]
            if name.endswith(".ics"):
                name = name[:-4]
            if name:
                uids.append(name)
        events = []
        if uids:
            events = (
                db.query(CalendarEvent)
                .filter(CalendarEvent.user_id == user.id, CalendarEvent.caldav_uid.in_(uids))
                .all()
            )
        found = {_event_uid(ev) for ev in events}
        parts = [_event_resource_xml(ev, calendar) for ev in events]
        # 未找到的 href 返回 404
        for uid in uids:
            if uid not in found:
                parts.append(f'''<D:response>
  <D:href>{calendar}{uid}.ics</D:href>
  <D:status>HTTP/1.1 404 Not Found</D:status>
</D:response>''')
        return _multistatus("\n".join(parts) if parts else "")

    # ── calendar-query（全量事件列表，可带 time-range 时仍返回全量，客户端自行过滤）──
    events = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.user_id == user.id)
        .order_by(CalendarEvent.start_time.asc())
        .limit(1000)
        .all()
    )
    parts = [_event_resource_xml(ev, calendar) for ev in events]
    parts.append(f"<D:sync-token>{current_token}</D:sync-token>")
    return _multistatus("\n".join(parts))
