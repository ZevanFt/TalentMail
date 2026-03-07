"""账号池 API - 临时邮箱管理"""
import random
import string
import secrets
import re
from datetime import datetime, timezone
from typing import Optional, List
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api import deps
from core.mailserver_sync import create_mail_user, delete_mail_user
from core.temp_mailbox_lifecycle import (
    STATUS_ACTIVE,
    STATUS_EXPIRED_RECOVERABLE,
    STATUS_PURGED,
    compute_new_expiry_windows,
    get_or_create_policy,
    run_temp_mailbox_maintenance,
)
from db import models
from db.models.billing import Plan, Subscription

logger = logging.getLogger(__name__)
router = APIRouter()


class TempMailboxCreate(BaseModel):
    prefix: Optional[str] = None
    purpose: Optional[str] = None
    auto_verify_codes: bool = True


class TempMailboxRead(BaseModel):
    id: int
    email: str
    purpose: Optional[str]
    auto_verify_codes: bool
    is_active: bool
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    recovery_until: Optional[datetime] = None
    unread_count: int = 0

    class Config:
        from_attributes = True


class TempMailboxListResponse(BaseModel):
    items: List[TempMailboxRead]
    total: int


class TempMailboxPolicyRead(BaseModel):
    cleanup_enabled: bool
    ttl_hours: int
    recoverable_days: int
    cleanup_interval_hours: int
    cleanup_batch_size: int
    delete_emails_on_purge: bool
    last_cleanup_at: Optional[datetime] = None
    last_cleanup_count: int


class TempMailboxPolicyUpdate(BaseModel):
    cleanup_enabled: Optional[bool] = None
    ttl_hours: Optional[int] = Field(default=None, ge=1, le=168)
    recoverable_days: Optional[int] = Field(default=None, ge=1, le=30)
    cleanup_interval_hours: Optional[int] = Field(default=None, ge=1, le=168)
    cleanup_batch_size: Optional[int] = Field(default=None, ge=10, le=5000)
    delete_emails_on_purge: Optional[bool] = None


class CleanupRunResponse(BaseModel):
    expired_count: int
    purged_count: int
    cleanup_ran: bool


class ExtendRestoreResponse(BaseModel):
    status: str
    message: str
    mailbox: TempMailboxRead


def generate_random_prefix(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def get_user_temp_mailbox_limit(db: Session, user: models.User) -> int:
    if user.role == "admin":
        return -1

    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()

    if subscription and subscription.current_period_end:
        if subscription.current_period_end > datetime.now(timezone.utc):
            plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
            if plan:
                return plan.max_temp_mailboxes

    default_plan = db.query(Plan).filter(Plan.is_default == True).first()
    if default_plan:
        return default_plan.max_temp_mailboxes

    return 3


def ensure_pool_access(user: models.User):
    if not user.pool_enabled and user.role != "admin":
        raise HTTPException(status_code=403, detail="您没有账号池功能权限")


def mailbox_to_read(db: Session, mailbox: models.TempMailbox) -> TempMailboxRead:
    unread = db.query(models.Email).filter(
        models.Email.mailbox_address == mailbox.email,
        models.Email.is_read == False
    ).count()
    return TempMailboxRead(
        id=mailbox.id,
        email=mailbox.email,
        purpose=mailbox.purpose,
        auto_verify_codes=mailbox.auto_verify_codes,
        is_active=mailbox.is_active,
        status=mailbox.status or STATUS_ACTIVE,
        created_at=mailbox.created_at,
        expires_at=mailbox.expires_at,
        recovery_until=mailbox.recovery_until,
        unread_count=unread,
    )


def sync_temp_mailbox_to_server(temp_email: str):
    random_password = secrets.token_urlsafe(16)
    ok = create_mail_user(temp_email, random_password)
    if not ok:
        logger.warning(f"同步临时邮箱到邮件服务器失败: {temp_email}")


@router.get("/", response_model=TempMailboxListResponse)
def list_temp_mailboxes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    include_purged: bool = Query(False),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    ensure_pool_access(current_user)

    # 懒更新：访问列表时推进过期状态
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=current_user.id)

    query = db.query(models.TempMailbox).filter(models.TempMailbox.owner_id == current_user.id)
    if not include_purged:
        query = query.filter(models.TempMailbox.status != STATUS_PURGED)

    total = query.count()
    mailboxes = query.order_by(models.TempMailbox.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "items": [mailbox_to_read(db, mailbox) for mailbox in mailboxes],
        "total": total,
    }


@router.post("/", response_model=TempMailboxRead)
def create_temp_mailbox(
    data: TempMailboxCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    ensure_pool_access(current_user)

    policy = get_or_create_policy(db)

    limit = get_user_temp_mailbox_limit(db, current_user)
    if limit != -1:
        current_count = db.query(models.TempMailbox).filter(
            models.TempMailbox.owner_id == current_user.id,
            models.TempMailbox.status == STATUS_ACTIVE,
            models.TempMailbox.is_active == True,
        ).count()
        if current_count >= limit:
            raise HTTPException(
                status_code=403,
                detail=f"已达到临时邮箱数量上限 ({limit} 个)，请升级套餐或删除不需要的邮箱"
            )

    prefix = data.prefix.strip().lower() if data.prefix else generate_random_prefix()
    if not prefix.replace('_', '').replace('-', '').isalnum():
        raise HTTPException(status_code=400, detail="邮箱前缀只能包含字母、数字、下划线和连字符")

    domain = current_user.email.split('@')[1]
    email = f"{prefix}@{domain}"

    existing = db.query(models.TempMailbox).filter(models.TempMailbox.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱地址已存在")

    now = datetime.now(timezone.utc)
    expires_at, recovery_until = compute_new_expiry_windows(now, policy)

    mailbox = models.TempMailbox(
        owner_id=current_user.id,
        email=email,
        purpose=data.purpose,
        auto_verify_codes=data.auto_verify_codes,
        status=STATUS_ACTIVE,
        is_active=True,
        expires_at=expires_at,
        recovery_until=recovery_until,
        last_extended_at=now,
    )
    db.add(mailbox)

    log = models.PoolActivityLog(
        user_id=current_user.id,
        action="create",
        mailbox_email=email,
        details=f"用途: {data.purpose or '未指定'}"
    )
    db.add(log)
    db.commit()
    db.refresh(mailbox)

    try:
        sync_temp_mailbox_to_server(email)
    except Exception as e:
        logger.error(f"同步临时邮箱到邮件服务器失败: {e}")

    return mailbox_to_read(db, mailbox)


@router.post("/{mailbox_id}/extend", response_model=ExtendRestoreResponse)
def extend_temp_mailbox(
    mailbox_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    ensure_pool_access(current_user)
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=current_user.id)

    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == current_user.id,
        models.TempMailbox.status != STATUS_PURGED,
    ).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="临时邮箱不存在")

    if mailbox.status == STATUS_EXPIRED_RECOVERABLE and mailbox.recovery_until and mailbox.recovery_until < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="该临时邮箱已超过恢复窗口，无法续期")

    policy = get_or_create_policy(db)
    now = datetime.now(timezone.utc)
    mailbox.expires_at, mailbox.recovery_until = compute_new_expiry_windows(now, policy)
    mailbox.status = STATUS_ACTIVE
    mailbox.is_active = True
    mailbox.last_extended_at = now

    db.add(models.PoolActivityLog(
        user_id=current_user.id,
        action="extend",
        mailbox_email=mailbox.email,
        details=f"续期到 {mailbox.expires_at.isoformat()}"
    ))
    db.commit()

    try:
        sync_temp_mailbox_to_server(mailbox.email)
    except Exception as e:
        logger.warning(f"续期后同步邮箱失败: {mailbox.email}, err={e}")

    db.refresh(mailbox)
    return {
        "status": "success",
        "message": "临时邮箱已续期",
        "mailbox": mailbox_to_read(db, mailbox),
    }


@router.post("/{mailbox_id}/restore", response_model=ExtendRestoreResponse)
def restore_temp_mailbox(
    mailbox_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    ensure_pool_access(current_user)
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=current_user.id)

    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == current_user.id,
    ).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="临时邮箱不存在")
    if mailbox.status != STATUS_EXPIRED_RECOVERABLE:
        raise HTTPException(status_code=400, detail="当前邮箱不处于可恢复状态")

    now = datetime.now(timezone.utc)
    if mailbox.recovery_until and mailbox.recovery_until < now:
        raise HTTPException(status_code=400, detail="恢复窗口已过，无法恢复")

    policy = get_or_create_policy(db)
    mailbox.expires_at, mailbox.recovery_until = compute_new_expiry_windows(now, policy)
    mailbox.status = STATUS_ACTIVE
    mailbox.is_active = True
    mailbox.last_extended_at = now

    db.add(models.PoolActivityLog(
        user_id=current_user.id,
        action="restore",
        mailbox_email=mailbox.email,
        details=f"恢复并延长到 {mailbox.expires_at.isoformat()}"
    ))
    db.commit()

    try:
        sync_temp_mailbox_to_server(mailbox.email)
    except Exception as e:
        logger.warning(f"恢复后同步邮箱失败: {mailbox.email}, err={e}")

    db.refresh(mailbox)
    return {
        "status": "success",
        "message": "临时邮箱已恢复",
        "mailbox": mailbox_to_read(db, mailbox),
    }


@router.delete("/{mailbox_id}")
def delete_temp_mailbox(
    mailbox_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == current_user.id
    ).first()

    if not mailbox:
        raise HTTPException(status_code=404, detail="临时邮箱不存在")

    try:
        delete_mail_user(mailbox.email)
    except Exception as e:
        logger.error(f"删除邮件服务器邮箱失败: {e}")

    mailbox.status = STATUS_PURGED
    mailbox.is_active = False
    mailbox.purged_at = datetime.now(timezone.utc)

    log = models.PoolActivityLog(
        user_id=current_user.id,
        action="delete",
        mailbox_email=mailbox.email,
        details="用户主动删除"
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
    ensure_pool_access(current_user)
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=current_user.id)

    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == current_user.id,
        models.TempMailbox.status != STATUS_PURGED,
    ).first()

    if not mailbox:
        raise HTTPException(status_code=404, detail="临时邮箱不存在")

    query = db.query(models.Email).filter(models.Email.mailbox_address == mailbox.email)
    total = query.count()
    emails = query.order_by(models.Email.received_at.desc()).offset((page - 1) * limit).limit(limit).all()

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
            code = extract_verification_code(email.body_text or email.body_html or "")
            email_data["verification_code"] = code

        result.append(email_data)

    return {"items": result, "total": total}


def extract_verification_code(text: str) -> Optional[str]:
    patterns = [
        r'验证码(?:是)?[：:\s]*([A-Za-z0-9]{4,8})',
        r'verification code(?: is)?[：:\s]*([A-Za-z0-9]{4,8})',
        r'code[：:\s]+([A-Za-z0-9]{4,8})',
        r'(?:^|\s)(\d{4,8})(?:\s|$)',
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
    ensure_pool_access(current_user)
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=current_user.id)

    total_mailboxes = db.query(models.TempMailbox).filter(
        models.TempMailbox.owner_id == current_user.id,
        models.TempMailbox.status != STATUS_PURGED,
    ).count()

    active_count = db.query(models.TempMailbox).filter(
        models.TempMailbox.owner_id == current_user.id,
        models.TempMailbox.status == STATUS_ACTIVE,
    ).count()

    recoverable_count = db.query(models.TempMailbox).filter(
        models.TempMailbox.owner_id == current_user.id,
        models.TempMailbox.status == STATUS_EXPIRED_RECOVERABLE,
    ).count()

    mailboxes = db.query(models.TempMailbox.email).filter(
        models.TempMailbox.owner_id == current_user.id,
        models.TempMailbox.status != STATUS_PURGED,
    ).all()
    mailbox_emails = [m.email for m in mailboxes]

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

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_emails = db.query(models.Email).filter(
            models.Email.mailbox_address.in_(mailbox_emails),
            models.Email.received_at >= today
        ).count()

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
        "recoverable_mailboxes": recoverable_count,
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
    ensure_pool_access(current_user)

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


@router.get("/admin/settings", response_model=TempMailboxPolicyRead)
def get_temp_mailbox_policy(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
):
    policy = get_or_create_policy(db)
    return policy


@router.patch("/admin/settings", response_model=TempMailboxPolicyRead)
def update_temp_mailbox_policy(
    data: TempMailboxPolicyUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
):
    policy = get_or_create_policy(db)

    for key, value in data.model_dump(exclude_none=True).items():
        setattr(policy, key, value)

    db.add(models.PoolActivityLog(
        user_id=current_user.id,
        action="admin_policy_update",
        mailbox_email="*",
        details=str(data.model_dump(exclude_none=True)),
    ))

    db.commit()
    db.refresh(policy)
    return policy


@router.post("/admin/cleanup/run", response_model=CleanupRunResponse)
def run_temp_mailbox_cleanup_now(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
):
    result = run_temp_mailbox_maintenance(db, force_cleanup=True, owner_id=None)

    db.add(models.PoolActivityLog(
        user_id=current_user.id,
        action="admin_cleanup_run",
        mailbox_email="*",
        details=f"expired={result['expired_count']},purged={result['purged_count']}",
    ))
    db.commit()

    return {
        "expired_count": result["expired_count"],
        "purged_count": result["purged_count"],
        "cleanup_ran": result["cleanup_ran"],
    }
