from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api import deps
from core.api_keys import generate_api_key
from core.config import settings
from db import models
from db.models.system import ApiKey, ApiKeyAuditLog

router = APIRouter()


ALLOWED_API_KEY_SCOPES = {
    "temp_mailbox:create",
    "temp_mailbox:read",
    "temp_mailbox:extend",
    "temp_mailbox:restore",
    "temp_email:read",
    "temp_code:read",
}


class ApiKeyCreate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=255)
    scopes: List[str] = Field(..., min_items=1)
    expires_in_days: int = Field(default=settings.API_KEY_DEFAULT_EXPIRES_DAYS, ge=1)
    rate_limit_per_minute: int = Field(default=settings.API_KEY_DEFAULT_RATE_LIMIT_PER_MINUTE, ge=1)


class ApiKeyItem(BaseModel):
    id: int
    key_prefix: str
    scopes: List[str]
    description: Optional[str] = None
    rate_limit_per_minute: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    api_key: str
    key: ApiKeyItem


class ApiKeyAuditItem(BaseModel):
    id: int
    api_key_id: Optional[int] = None
    user_id: Optional[int] = None
    method: Optional[str] = None
    path: Optional[str] = None
    ip_address: Optional[str] = None
    status_code: Optional[int] = None
    decision: str
    error_code: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


def _normalize_scopes(scopes: List[str]) -> List[str]:
    normalized: List[str] = []
    seen = set()
    for scope in scopes:
        item = scope.strip()
        if not item:
            continue
        if item not in ALLOWED_API_KEY_SCOPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的 scope: {item}",
            )
        if item not in seen:
            normalized.append(item)
            seen.add(item)
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少提供一个有效 scope")
    return normalized


@router.get("/", response_model=List[ApiKeyItem])
def list_api_keys(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    return (
        db.query(ApiKey)
        .filter(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


@router.post("/", response_model=ApiKeyCreateResponse)
def create_api_key(
    payload: ApiKeyCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    if payload.expires_in_days > settings.API_KEY_MAX_EXPIRES_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"expires_in_days 不能大于 {settings.API_KEY_MAX_EXPIRES_DAYS}",
        )
    if payload.rate_limit_per_minute < settings.API_KEY_MIN_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"rate_limit_per_minute 不能小于 {settings.API_KEY_MIN_RATE_LIMIT_PER_MINUTE}",
        )
    if payload.rate_limit_per_minute > settings.API_KEY_MAX_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"rate_limit_per_minute 不能大于 {settings.API_KEY_MAX_RATE_LIMIT_PER_MINUTE}",
        )

    scopes = _normalize_scopes(payload.scopes)
    raw_key, key_prefix, key_hash = generate_api_key()

    api_key = ApiKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=scopes,
        description=payload.description,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        expires_at=datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days),
    )
    db.add(api_key)
    db.flush()
    db.refresh(api_key)

    return ApiKeyCreateResponse(api_key=raw_key, key=api_key)


@router.delete("/{key_id}")
def revoke_api_key(
    key_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key 不存在")

    if api_key.revoked_at is not None:
        return {"message": "API Key 已吊销"}

    api_key.revoked_at = datetime.now(timezone.utc)
    return {"message": "API Key 已吊销"}


@router.get("/audit/logs", response_model=List[ApiKeyAuditItem])
def list_api_key_audit_logs(
    key_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    key_ids_query = db.query(ApiKey.id).filter(ApiKey.user_id == current_user.id)
    if key_id is not None:
        key_ids_query = key_ids_query.filter(ApiKey.id == key_id)
    key_ids = [row[0] for row in key_ids_query.all()]
    if not key_ids:
        return []

    return (
        db.query(ApiKeyAuditLog)
        .filter(ApiKeyAuditLog.api_key_id.in_(key_ids))
        .order_by(ApiKeyAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
