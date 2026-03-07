from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from sqlalchemy.orm import Session

from db import models
from core.mailserver_sync import delete_mail_user

logger = logging.getLogger(__name__)

STATUS_ACTIVE = "active"
STATUS_EXPIRED_RECOVERABLE = "expired_recoverable"
STATUS_PURGED = "purged"

DEFAULT_TTL_HOURS = 24
DEFAULT_RECOVERABLE_DAYS = 10
DEFAULT_CLEANUP_INTERVAL_HOURS = 24
DEFAULT_CLEANUP_BATCH_SIZE = 500


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_policy(db: Session) -> models.TempMailboxPolicy:
    policy = db.query(models.TempMailboxPolicy).filter(models.TempMailboxPolicy.id == 1).first()
    if policy:
        return policy

    policy = models.TempMailboxPolicy(
        id=1,
        cleanup_enabled=True,
        ttl_hours=DEFAULT_TTL_HOURS,
        recoverable_days=DEFAULT_RECOVERABLE_DAYS,
        cleanup_interval_hours=DEFAULT_CLEANUP_INTERVAL_HOURS,
        cleanup_batch_size=DEFAULT_CLEANUP_BATCH_SIZE,
        delete_emails_on_purge=True,
        last_cleanup_count=0,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def compute_new_expiry_windows(
    now: datetime, policy: models.TempMailboxPolicy
) -> tuple[datetime, datetime]:
    expires_at = now + timedelta(hours=max(1, int(policy.ttl_hours or DEFAULT_TTL_HOURS)))
    recovery_until = expires_at + timedelta(days=max(1, int(policy.recoverable_days or DEFAULT_RECOVERABLE_DAYS)))
    return expires_at, recovery_until


def normalize_mailbox_windows(
    mailbox: models.TempMailbox, policy: models.TempMailboxPolicy, now: Optional[datetime] = None
) -> None:
    now = now or _now_utc()
    if mailbox.expires_at is None:
        mailbox.expires_at = (mailbox.created_at or now) + timedelta(hours=max(1, int(policy.ttl_hours or DEFAULT_TTL_HOURS)))
    if mailbox.recovery_until is None:
        mailbox.recovery_until = mailbox.expires_at + timedelta(days=max(1, int(policy.recoverable_days or DEFAULT_RECOVERABLE_DAYS)))


def expire_due_mailboxes(
    db: Session,
    policy: models.TempMailboxPolicy,
    owner_id: Optional[int] = None,
    now: Optional[datetime] = None,
) -> int:
    now = now or _now_utc()
    query = db.query(models.TempMailbox).filter(
        models.TempMailbox.status == STATUS_ACTIVE,
        models.TempMailbox.is_active == True,  # noqa: E712
        models.TempMailbox.email.isnot(None),
    )
    if owner_id is not None:
        query = query.filter(models.TempMailbox.owner_id == owner_id)

    due_mailboxes = []
    for mailbox in query.all():
        normalize_mailbox_windows(mailbox, policy, now=now)
        if mailbox.expires_at and mailbox.expires_at <= now:
            due_mailboxes.append(mailbox)

    for mailbox in due_mailboxes:
        mailbox.status = STATUS_EXPIRED_RECOVERABLE
        mailbox.is_active = False
        if mailbox.expired_at is None:
            mailbox.expired_at = now
        if mailbox.recovery_until is None and mailbox.expires_at:
            mailbox.recovery_until = mailbox.expires_at + timedelta(days=max(1, int(policy.recoverable_days or DEFAULT_RECOVERABLE_DAYS)))
        try:
            delete_mail_user(mailbox.email)
        except Exception as e:
            logger.warning(f"过期停用邮箱时删除 mailserver 账户失败: {mailbox.email}, err={e}")
    return len(due_mailboxes)


def purge_expired_mailboxes(
    db: Session,
    policy: models.TempMailboxPolicy,
    now: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> int:
    now = now or _now_utc()
    batch_size = max(1, int(limit or policy.cleanup_batch_size or DEFAULT_CLEANUP_BATCH_SIZE))
    to_purge = db.query(models.TempMailbox).filter(
        models.TempMailbox.status == STATUS_EXPIRED_RECOVERABLE,
        models.TempMailbox.recovery_until.isnot(None),
        models.TempMailbox.recovery_until <= now,
    ).order_by(models.TempMailbox.recovery_until.asc()).limit(batch_size).all()

    for mailbox in to_purge:
        try:
            delete_mail_user(mailbox.email)
        except Exception as e:
            logger.warning(f"清理邮箱时删除 mailserver 账户失败: {mailbox.email}, err={e}")

        if policy.delete_emails_on_purge:
            db.query(models.Email).filter(models.Email.mailbox_address == mailbox.email).delete(synchronize_session=False)

        mailbox.status = STATUS_PURGED
        mailbox.is_active = False
        mailbox.purged_at = now

    return len(to_purge)


def run_temp_mailbox_maintenance(
    db: Session,
    *,
    force_cleanup: bool = False,
    owner_id: Optional[int] = None,
) -> dict:
    now = _now_utc()
    policy = get_or_create_policy(db)

    expired_count = expire_due_mailboxes(db, policy, owner_id=owner_id, now=now)

    should_run_cleanup = False
    if force_cleanup:
        should_run_cleanup = True
    elif policy.cleanup_enabled:
        if not policy.last_cleanup_at:
            should_run_cleanup = True
        else:
            gap = now - policy.last_cleanup_at
            should_run_cleanup = gap >= timedelta(hours=max(1, int(policy.cleanup_interval_hours or DEFAULT_CLEANUP_INTERVAL_HOURS)))

    purged_count = 0
    if should_run_cleanup:
        purged_count = purge_expired_mailboxes(db, policy, now=now)
        policy.last_cleanup_at = now
        policy.last_cleanup_count = purged_count

    db.commit()
    return {
        "expired_count": expired_count,
        "purged_count": purged_count,
        "cleanup_ran": should_run_cleanup,
        "policy": {
            "cleanup_enabled": policy.cleanup_enabled,
            "ttl_hours": policy.ttl_hours,
            "recoverable_days": policy.recoverable_days,
            "cleanup_interval_hours": policy.cleanup_interval_hours,
            "cleanup_batch_size": policy.cleanup_batch_size,
            "delete_emails_on_purge": policy.delete_emails_on_purge,
            "last_cleanup_at": policy.last_cleanup_at.isoformat() if policy.last_cleanup_at else None,
            "last_cleanup_count": policy.last_cleanup_count,
        },
    }

