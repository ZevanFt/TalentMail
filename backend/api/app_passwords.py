"""应用专用密码管理 API（CalDAV 等客户端）"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_active_user, get_db
from core.app_passwords import MAX_ACTIVE_PER_USER, count_active, generate_app_password
from db.models.user import AppPassword, User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/app-passwords", tags=["App Passwords"])


class AppPasswordCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class AppPasswordItem(BaseModel):
    id: int
    name: str
    prefix: str
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AppPasswordCreateResponse(BaseModel):
    password: str
    item: AppPasswordItem


@router.get("/", response_model=List[AppPasswordItem])
def list_app_passwords(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return (
        db.query(AppPassword)
        .filter(AppPassword.user_id == current_user.id, AppPassword.revoked_at.is_(None))
        .order_by(AppPassword.created_at.desc())
        .all()
    )


@router.post("/", response_model=AppPasswordCreateResponse)
def create_app_password(
    payload: AppPasswordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if count_active(db, current_user.id) >= MAX_ACTIVE_PER_USER:
        raise HTTPException(400, f"最多同时保留 {MAX_ACTIVE_PER_USER} 个应用专用密码")

    plaintext, prefix, pwd_hash = generate_app_password()
    row = AppPassword(
        user_id=current_user.id,
        name=payload.name.strip(),
        password_hash=pwd_hash,
        prefix=prefix,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    try:
        from core.audit import record_operation
        record_operation(
            db,
            action="app_password.create",
            user_id=current_user.id,
            resource_type="app_password",
            resource_id=row.id,
            detail={"name": row.name, "prefix": row.prefix},
        )
    except Exception as e:
        logger.error(f"应用密码审计失败: {e}")

    return AppPasswordCreateResponse(password=plaintext, item=row)


@router.delete("/{password_id}")
def revoke_app_password(
    password_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    row = (
        db.query(AppPassword)
        .filter(AppPassword.id == password_id, AppPassword.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(404, "应用专用密码不存在")
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.commit()

    try:
        from core.audit import record_operation
        record_operation(
            db,
            action="app_password.revoke",
            user_id=current_user.id,
            resource_type="app_password",
            resource_id=row.id,
            detail={"name": row.name, "prefix": row.prefix},
        )
    except Exception as e:
        logger.error(f"应用密码吊销审计失败: {e}")

    return {"message": "已吊销"}
