"""账号池 API - 临时邮箱管理"""
import random
import string
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

from db import models
from api import deps
from core.mailserver_sync import create_mail_user, get_docker_client, MAILSERVER_CONTAINER_NAME

logger = logging.getLogger(__name__)

router = APIRouter()


# Schemas
class TempMailboxCreate(BaseModel):
    prefix: Optional[str] = None  # 邮箱前缀，为空则随机生成
    purpose: Optional[str] = None  # 用途标签
    auto_verify_codes: bool = True  # 自动识别验证码


class TempMailboxRead(BaseModel):
    id: int
    email: str
    purpose: Optional[str]
    auto_verify_codes: bool
    is_active: bool
    created_at: datetime
    unread_count: int = 0

    class Config:
        from_attributes = True


class TempMailboxListResponse(BaseModel):
    items: List[TempMailboxRead]
    total: int


def generate_random_prefix(length: int = 8) -> str:
    """生成随机邮箱前缀"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


@router.get("/", response_model=TempMailboxListResponse)
def list_temp_mailboxes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取当前用户的临时邮箱列表"""
    # 检查用户是否有账号池权限
    if not current_user.pool_enabled and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="您没有账号池功能权限")
    
    query = db.query(models.TempMailbox).filter(
        models.TempMailbox.owner_id == current_user.id,
        models.TempMailbox.is_active == True
    )
    total = query.count()
    mailboxes = query.order_by(models.TempMailbox.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # 获取每个邮箱的未读数
    items = []
    for mailbox in mailboxes:
        unread = db.query(models.Email).filter(
            models.Email.mailbox_address == mailbox.email,
            models.Email.is_read == False
        ).count()
        items.append({
            "id": mailbox.id,
            "email": mailbox.email,
            "purpose": mailbox.purpose,
            "auto_verify_codes": mailbox.auto_verify_codes,
            "is_active": mailbox.is_active,
            "created_at": mailbox.created_at,
            "unread_count": unread
        })
    
    return {"items": items, "total": total}


@router.post("/", response_model=TempMailboxRead)
def create_temp_mailbox(
    data: TempMailboxCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """创建临时邮箱"""
    # 检查用户是否有账号池权限
    if not current_user.pool_enabled and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="您没有账号池功能权限")
    
    # 生成邮箱地址
    prefix = data.prefix.strip().lower() if data.prefix else generate_random_prefix()
    
    # 验证前缀格式
    if not prefix.replace('_', '').replace('-', '').isalnum():
        raise HTTPException(status_code=400, detail="邮箱前缀只能包含字母、数字、下划线和连字符")
    
    # 从用户邮箱获取域名
    domain = current_user.email.split('@')[1]
    email = f"{prefix}@{domain}"
    
    # 检查是否已存在
    existing = db.query(models.TempMailbox).filter(models.TempMailbox.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱地址已存在")
    
    # 创建临时邮箱
    mailbox = models.TempMailbox(
        owner_id=current_user.id,
        email=email,
        purpose=data.purpose,
        auto_verify_codes=data.auto_verify_codes,
        is_active=True
    )
    db.add(mailbox)
    db.commit()
    db.refresh(mailbox)
    
    # 记录操作日志
    log = models.PoolActivityLog(
        user_id=current_user.id,
        action="create",
        mailbox_email=email,
        details=f"用途: {data.purpose or '未指定'}"
    )
    db.add(log)
    db.commit()
    
    # 同步到邮件服务器（创建虚拟别名，转发到所有者邮箱）
    try:
        sync_temp_mailbox_to_server(email, current_user.email)
    except Exception as e:
        logger.error(f"同步临时邮箱到邮件服务器失败: {e}")
        # 不影响创建，继续返回
    
    return mailbox


def sync_temp_mailbox_to_server(temp_email: str, owner_email: str):
    """将临时邮箱同步到邮件服务器（创建虚拟邮箱账户）"""
    client = get_docker_client()
    if client is None:
        logger.warning("无法连接到 Docker，跳过邮件服务器同步")
        return
    
    try:
        container = client.containers.get(MAILSERVER_CONTAINER_NAME)
        
        # 使用 setup email add 创建邮箱账户（使用随机密码，因为不需要登录）
        import secrets
        random_password = secrets.token_urlsafe(16)
        result = container.exec_run(
            ["setup", "email", "add", temp_email, random_password],
            demux=True
        )
        
        if result.exit_code == 0:
            logger.info(f"✔ 成功创建临时邮箱: {temp_email}")
        else:
            stderr = result.output[1].decode('utf-8') if result.output[1] else ''
            # 如果邮箱已存在，不算错误
            if 'already exists' in stderr.lower():
                logger.info(f"临时邮箱已存在: {temp_email}")
            else:
                logger.error(f"✖ 创建临时邮箱失败: {stderr}")
    except Exception as e:
        logger.error(f"同步临时邮箱失败: {e}")


def remove_temp_mailbox_from_server(temp_email: str):
    """从邮件服务器删除临时邮箱"""
    client = get_docker_client()
    if client is None:
        return
    
    try:
        container = client.containers.get(MAILSERVER_CONTAINER_NAME)
        result = container.exec_run(
            ["setup", "email", "del", "-y", temp_email],
            demux=True
        )
        if result.exit_code == 0:
            logger.info(f"✔ 成功删除临时邮箱: {temp_email}")
    except Exception as e:
        logger.error(f"删除临时邮箱失败: {e}")


@router.delete("/{mailbox_id}")
def delete_temp_mailbox(
    mailbox_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """删除临时邮箱（软删除）"""
    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == current_user.id
    ).first()
    
    if not mailbox:
        raise HTTPException(status_code=404, detail="临时邮箱不存在")
    
    # 从邮件服务器删除别名
    try:
        remove_temp_mailbox_from_server(mailbox.email)
    except Exception as e:
        logger.error(f"删除邮件服务器别名失败: {e}")
    
    mailbox.is_active = False
    
    # 记录操作日志
    log = models.PoolActivityLog(
        user_id=current_user.id,
        action="delete",
        mailbox_email=mailbox.email,
        details=None
    )
    db.add(log)
    db.commit()
    
    return {"status": "success", "message": "临时邮箱已删除"}


@router.get("/{mailbox_id}/emails")
def get_mailbox_emails(
    mailbox_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取临时邮箱收到的邮件"""
    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == current_user.id
    ).first()
    
    if not mailbox:
        raise HTTPException(status_code=404, detail="临时邮箱不存在")
    
    # 查询该邮箱地址收到的邮件
    query = db.query(models.Email).filter(
        models.Email.mailbox_address == mailbox.email
    )
    total = query.count()
    emails = query.order_by(models.Email.received_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # 提取验证码（如果启用）
    result = []
    for email in emails:
        email_data = {
            "id": email.id,
            "sender": email.sender,
            "subject": email.subject,
            "received_at": email.received_at.isoformat() if email.received_at else None,
            "is_read": email.is_read,
            "verification_code": None
        }
        
        if mailbox.auto_verify_codes:
            # 尝试从邮件内容中提取验证码
            code = extract_verification_code(email.body_text or email.body_html or "")
            email_data["verification_code"] = code
        
        result.append(email_data)
    
    return {"items": result, "total": total}


def extract_verification_code(text: str) -> Optional[str]:
    """从文本中提取验证码"""
    import re
    
    # 常见验证码模式
    patterns = [
        r'验证码[：:]\s*([A-Za-z0-9]{4,8})',
        r'verification code[：:\s]+([A-Za-z0-9]{4,8})',
        r'code[：:\s]+([A-Za-z0-9]{4,8})',
        r'(?:^|\s)(\d{4,8})(?:\s|$)',  # 独立的4-8位数字
        r'([A-Z0-9]{6})',  # 6位大写字母数字组合
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


@router.get("/stats")
def get_pool_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取账号池统计信息"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    if not current_user.pool_enabled and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="您没有账号池功能权限")
    
    # 总邮箱数（包括已删除）
    total_mailboxes = db.query(models.TempMailbox).filter(
        models.TempMailbox.owner_id == current_user.id
    ).count()
    
    # 活跃邮箱数
    active_count = db.query(models.TempMailbox).filter(
        models.TempMailbox.owner_id == current_user.id,
        models.TempMailbox.is_active == True
    ).count()
    
    # 获取所有临时邮箱地址
    mailboxes = db.query(models.TempMailbox.email).filter(
        models.TempMailbox.owner_id == current_user.id
    ).all()
    mailbox_emails = [m.email for m in mailboxes]
    
    # 总邮件数
    total_emails = 0
    unread_emails = 0
    today_emails = 0
    recent_emails = []
    
    if mailbox_emails:
        total_emails = db.query(models.Email).filter(
            models.Email.mailbox_address.in_(mailbox_emails)
        ).count()
        
        unread_emails = db.query(models.Email).filter(
            models.Email.mailbox_address.in_(mailbox_emails),
            models.Email.is_read == False
        ).count()
        
        # 今日邮件数
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_emails = db.query(models.Email).filter(
            models.Email.mailbox_address.in_(mailbox_emails),
            models.Email.received_at >= today
        ).count()
        
        # 最近5封邮件
        recent = db.query(models.Email).filter(
            models.Email.mailbox_address.in_(mailbox_emails)
        ).order_by(models.Email.received_at.desc()).limit(5).all()
        
        recent_emails = [{
            "id": e.id,
            "mailbox": e.mailbox_address,
            "sender": e.sender,
            "subject": e.subject,
            "received_at": e.received_at.isoformat() if e.received_at else None
        } for e in recent]
    
    return {
        "total_mailboxes": total_mailboxes,
        "active_mailboxes": active_count,
        "total_emails": total_emails,
        "unread_emails": unread_emails,
        "today_emails": today_emails,
        "recent_emails": recent_emails
    }


@router.get("/activity")
def get_activity_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取操作日志"""
    if not current_user.pool_enabled and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="您没有账号池功能权限")
    
    query = db.query(models.PoolActivityLog).filter(
        models.PoolActivityLog.user_id == current_user.id
    )
    total = query.count()
    logs = query.order_by(models.PoolActivityLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "items": [{
            "id": log.id,
            "action": log.action,
            "mailbox_email": log.mailbox_email,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None
        } for log in logs],
        "total": total
    }