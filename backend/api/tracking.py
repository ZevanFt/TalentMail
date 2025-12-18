from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from api import deps
from db.models.features import TrackingPixel, TrackingEvent
from db.models.email import Email, Folder
from db.models import User
import uuid
import base64
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 1x1 透明 GIF 图片（base64 编码）
TRANSPARENT_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


@router.get("/open/{pixel_id}")
async def track_open(
    pixel_id: str,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """追踪邮件打开事件，返回 1x1 透明 GIF"""
    try:
        pixel_uuid = uuid.UUID(pixel_id)
    except ValueError:
        # 无效的 UUID，仍返回图片避免暴露追踪
        return Response(content=TRANSPARENT_GIF, media_type="image/gif")
    
    # 查找追踪像素
    pixel = db.query(TrackingPixel).filter(TrackingPixel.id == pixel_uuid).first()
    if not pixel:
        return Response(content=TRANSPARENT_GIF, media_type="image/gif")
    
    # 获取客户端信息
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    
    # 记录追踪事件
    event = TrackingEvent(
        pixel_id=pixel_uuid,
        event_type="opened",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    
    # 更新邮件的追踪状态
    if pixel.email:
        email = pixel.email
        # 更新首次打开时间和打开次数
        if not hasattr(email, 'first_opened_at') or email.first_opened_at is None:
            from datetime import datetime, timezone
            email.first_opened_at = datetime.now(timezone.utc)
        if hasattr(email, 'open_count'):
            email.open_count = (email.open_count or 0) + 1
    
    db.commit()
    logger.info(f"追踪事件记录: pixel={pixel_id}, ip={ip_address}")
    
    # 返回透明 GIF，设置不缓存
    return Response(
        content=TRANSPARENT_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )


@router.get("/stats/{email_id}")
async def get_tracking_stats(
    email_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取邮件追踪统计"""
    # 验证邮件属于当前用户
    email = db.query(Email).join(Folder).filter(
        Email.id == email_id,
        Folder.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if not email.is_tracked:
        return {"status": "success", "data": {"is_tracked": False}}
    
    # 获取追踪像素
    pixel = db.query(TrackingPixel).filter(TrackingPixel.email_id == email_id).first()
    if not pixel:
        return {"status": "success", "data": {"is_tracked": True, "events": [], "open_count": 0}}
    
    # 获取所有追踪事件
    events = db.query(TrackingEvent).filter(
        TrackingEvent.pixel_id == pixel.id
    ).order_by(TrackingEvent.timestamp.desc()).all()
    
    # 解析设备信息
    def parse_device(user_agent: str) -> dict:
        ua = user_agent.lower() if user_agent else ""
        if "iphone" in ua or "ipad" in ua:
            device = "📱 iPhone/iPad"
        elif "android" in ua:
            device = "📱 Android"
        elif "windows" in ua:
            device = "💻 Windows"
        elif "mac" in ua:
            device = "💻 Mac"
        elif "linux" in ua:
            device = "💻 Linux"
        else:
            device = "🖥️ 未知设备"
        return {"device": device, "raw": user_agent}
    
    event_list = []
    for e in events:
        event_list.append({
            "id": e.id,
            "event_type": e.event_type,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "ip_address": e.ip_address,
            "device": parse_device(e.user_agent),
        })
    
    return {
        "status": "success",
        "data": {
            "is_tracked": True,
            "open_count": len([e for e in events if e.event_type == "opened"]),
            "first_opened_at": events[-1].timestamp.isoformat() if events else None,
            "last_opened_at": events[0].timestamp.isoformat() if events else None,
            "events": event_list,
        }
    }