from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api import deps
from api.pool import (
    ensure_pool_access,
    extract_verification_code,
    generate_random_prefix,
    get_user_temp_mailbox_limit,
    mailbox_to_read,
    sync_temp_mailbox_to_server,
    TempMailboxCreate,
    TempMailboxRead,
)
from core.temp_mailbox_lifecycle import (
    STATUS_ACTIVE,
    STATUS_EXPIRED_RECOVERABLE,
    STATUS_PURGED,
    compute_new_expiry_windows,
    get_or_create_policy,
    run_temp_mailbox_maintenance,
)
from db import models
from db.models.system import ApiKey

router = APIRouter(prefix="/automation/temp-mailboxes", tags=["Automation Temp Mailboxes"])


class TempMailboxEmailItem(BaseModel):
    id: int
    sender: Optional[str] = None
    subject: Optional[str] = None
    received_at: Optional[str] = None
    is_read: bool
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    verification_code: Optional[str] = None


class TempMailboxEmailListResponse(BaseModel):
    items: List[TempMailboxEmailItem]
    total: int


class TempMailboxCodeRead(BaseModel):
    mailbox_id: int
    mailbox_email: str
    email_id: int
    sender: Optional[str] = None
    subject: Optional[str] = None
    received_at: Optional[str] = None
    code: str


class ExtendRestoreResponse(BaseModel):
    status: str
    message: str
    mailbox: TempMailboxRead


def _get_api_key_user(
    db: Session,
    api_key: ApiKey,
) -> models.User:
    user = db.query(models.User).filter(models.User.id == api_key.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="API Key user not found")
    ensure_pool_access(user)
    return user


def _get_owned_mailbox_or_404(db: Session, user_id: int, mailbox_id: int) -> models.TempMailbox:
    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == user_id,
    ).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="临时邮箱不存在")
    return mailbox


@router.get("", response_model=List[TempMailboxRead])
def list_temp_mailboxes_for_api_key(
    include_purged: bool = Query(False),
    db: Session = Depends(deps.get_db),
    api_key: ApiKey = Depends(deps.require_api_key_scopes(["temp_mailbox:read"])),
):
    user = _get_api_key_user(db, api_key)
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=user.id)

    query = db.query(models.TempMailbox).filter(models.TempMailbox.owner_id == user.id)
    if not include_purged:
        query = query.filter(models.TempMailbox.status != STATUS_PURGED)
    items = query.order_by(models.TempMailbox.created_at.desc()).all()
    return [mailbox_to_read(db, mailbox) for mailbox in items]


@router.post("", response_model=TempMailboxRead)
def create_temp_mailbox_for_api_key(
    data: TempMailboxCreate,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(deps.get_db),
    api_key: ApiKey = Depends(deps.require_api_key_scopes(["temp_mailbox:create"])),
):
    user = _get_api_key_user(db, api_key)
    policy = get_or_create_policy(db)

    normalized_idempotency_key: Optional[str] = None
    if idempotency_key is not None:
        normalized_idempotency_key = idempotency_key.strip()
        if not normalized_idempotency_key:
            raise HTTPException(status_code=400, detail="Idempotency-Key 不能为空字符串")
        if len(normalized_idempotency_key) > 128:
            raise HTTPException(status_code=400, detail="Idempotency-Key 长度不能超过 128")

        existing_by_idempotency = db.query(models.TempMailbox).filter(
            models.TempMailbox.owner_id == user.id,
            models.TempMailbox.api_idempotency_key == normalized_idempotency_key,
            models.TempMailbox.status != STATUS_PURGED,
        ).first()
        if existing_by_idempotency:
            return mailbox_to_read(db, existing_by_idempotency)

    limit = get_user_temp_mailbox_limit(db, user)
    if limit != -1:
        current_count = db.query(models.TempMailbox).filter(
            models.TempMailbox.owner_id == user.id,
            models.TempMailbox.status == STATUS_ACTIVE,
            models.TempMailbox.is_active == True,  # noqa: E712
        ).count()
        if current_count >= limit:
            raise HTTPException(
                status_code=403,
                detail=f"已达到临时邮箱数量上限 ({limit} 个)，请升级套餐或删除不需要的邮箱",
            )

    prefix = data.prefix.strip().lower() if data.prefix else generate_random_prefix()
    if not prefix.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="邮箱前缀只能包含字母、数字、下划线和连字符")

    domain = user.email.split("@")[1]
    email = f"{prefix}@{domain}"

    existing = db.query(models.TempMailbox).filter(models.TempMailbox.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱地址已存在")

    now = datetime.now(timezone.utc)
    expires_at, recovery_until = compute_new_expiry_windows(now, policy)

    mailbox = models.TempMailbox(
        owner_id=user.id,
        email=email,
        purpose=data.purpose,
        auto_verify_codes=data.auto_verify_codes,
        api_idempotency_key=normalized_idempotency_key,
        status=STATUS_ACTIVE,
        is_active=True,
        expires_at=expires_at,
        recovery_until=recovery_until,
        last_extended_at=now,
    )
    db.add(mailbox)
    db.add(
        models.PoolActivityLog(
            user_id=user.id,
            action="api_create",
            mailbox_email=email,
            details=f"用途: {data.purpose or '未指定'}",
        )
    )
    db.commit()
    db.refresh(mailbox)

    sync_temp_mailbox_to_server(email)
    return mailbox_to_read(db, mailbox)


@router.get("/{mailbox_id}/emails", response_model=TempMailboxEmailListResponse)
def get_mailbox_emails_for_api_key(
    mailbox_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    include_body: bool = Query(False),
    db: Session = Depends(deps.get_db),
    api_key: ApiKey = Depends(deps.require_api_key_scopes(["temp_email:read"])),
):
    user = _get_api_key_user(db, api_key)
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=user.id)

    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == user.id,
        models.TempMailbox.status != STATUS_PURGED,
    ).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="临时邮箱不存在")

    query = db.query(models.Email).filter(models.Email.mailbox_address == mailbox.email)
    total = query.count()
    emails = query.order_by(models.Email.received_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items: List[TempMailboxEmailItem] = []
    for email in emails:
        text_source = email.body_text or email.body_html or ""
        code = extract_verification_code(text_source) if mailbox.auto_verify_codes else None
        items.append(
            TempMailboxEmailItem(
                id=email.id,
                sender=email.sender,
                subject=email.subject,
                received_at=email.received_at.isoformat() if email.received_at else None,
                is_read=email.is_read,
                body_text=email.body_text if include_body else None,
                body_html=email.body_html if include_body else None,
                verification_code=code,
            )
        )
    return TempMailboxEmailListResponse(items=items, total=total)


@router.get("/{mailbox_id}/codes/latest", response_model=Optional[TempMailboxCodeRead])
def get_latest_verification_code(
    mailbox_id: int,
    sender_contains: Optional[str] = Query(default=None),
    subject_contains: Optional[str] = Query(default=None),
    unread_only: bool = Query(default=False),
    within_minutes: int = Query(default=1440, ge=1, le=10080),
    db: Session = Depends(deps.get_db),
    api_key: ApiKey = Depends(deps.require_api_key_scopes(["temp_code:read"])),
):
    user = _get_api_key_user(db, api_key)
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=user.id)

    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == user.id,
        models.TempMailbox.status != STATUS_PURGED,
    ).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="临时邮箱不存在")

    since_time = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)
    query = db.query(models.Email).filter(
        models.Email.mailbox_address == mailbox.email,
        models.Email.received_at >= since_time,
    )
    if unread_only:
        query = query.filter(models.Email.is_read == False)  # noqa: E712
    if sender_contains:
        query = query.filter(models.Email.sender.ilike(f"%{sender_contains.strip()}%"))
    if subject_contains:
        query = query.filter(models.Email.subject.ilike(f"%{subject_contains.strip()}%"))

    emails = query.order_by(models.Email.received_at.desc()).limit(200).all()
    for email in emails:
        code = extract_verification_code(email.body_text or email.body_html or "")
        if code:
            return TempMailboxCodeRead(
                mailbox_id=mailbox.id,
                mailbox_email=mailbox.email,
                email_id=email.id,
                sender=email.sender,
                subject=email.subject,
                received_at=email.received_at.isoformat() if email.received_at else None,
                code=code,
            )
    return None


@router.post("/{mailbox_id}/extend", response_model=ExtendRestoreResponse)
def extend_temp_mailbox_for_api_key(
    mailbox_id: int,
    db: Session = Depends(deps.get_db),
    api_key: ApiKey = Depends(deps.require_api_key_scopes(["temp_mailbox:extend"])),
):
    user = _get_api_key_user(db, api_key)
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=user.id)

    mailbox = db.query(models.TempMailbox).filter(
        models.TempMailbox.id == mailbox_id,
        models.TempMailbox.owner_id == user.id,
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

    db.add(
        models.PoolActivityLog(
            user_id=user.id,
            action="api_extend",
            mailbox_email=mailbox.email,
            details=f"续期到 {mailbox.expires_at.isoformat()}",
        )
    )
    db.commit()
    db.refresh(mailbox)
    sync_temp_mailbox_to_server(mailbox.email)
    return ExtendRestoreResponse(status="success", message="临时邮箱已续期", mailbox=mailbox_to_read(db, mailbox))


@router.post("/{mailbox_id}/restore", response_model=ExtendRestoreResponse)
def restore_temp_mailbox_for_api_key(
    mailbox_id: int,
    db: Session = Depends(deps.get_db),
    api_key: ApiKey = Depends(deps.require_api_key_scopes(["temp_mailbox:restore"])),
):
    user = _get_api_key_user(db, api_key)
    run_temp_mailbox_maintenance(db, force_cleanup=False, owner_id=user.id)

    mailbox = _get_owned_mailbox_or_404(db, user.id, mailbox_id)
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

    db.add(
        models.PoolActivityLog(
            user_id=user.id,
            action="api_restore",
            mailbox_email=mailbox.email,
            details=f"恢复并延长到 {mailbox.expires_at.isoformat()}",
        )
    )
    db.commit()
    db.refresh(mailbox)
    sync_temp_mailbox_to_server(mailbox.email)
    return ExtendRestoreResponse(status="success", message="临时邮箱已恢复", mailbox=mailbox_to_read(db, mailbox))
