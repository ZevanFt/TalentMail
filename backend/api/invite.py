import logging
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from db import models
from db.models.billing import InviteCodeUsage
from api import deps

logger = logging.getLogger(__name__)
router = APIRouter()


class InviteCodeCreate(BaseModel):
    max_uses: int = Field(default=1, ge=0, le=10000)  # 0 表示无限
    expires_days: Optional[int] = Field(default=None, ge=1, le=3650)  # 最长10年


class InviteCodeUsageResponse(BaseModel):
    id: int
    user_email: str
    used_at: datetime

    class Config:
        from_attributes = True


class InviteCodeResponse(BaseModel):
    id: int
    code: str
    max_uses: int
    used_count: int
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.post("/", response_model=InviteCodeResponse)
def create_invite_code(
    data: InviteCodeCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """创建邀请码（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可创建邀请码")
    
    code = secrets.token_urlsafe(8)  # 生成 11 字符的随机码
    expires_at = None
    if data.expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_days)
    
    invite = models.InviteCode(
        code=code,
        max_uses=data.max_uses,
        expires_at=expires_at,
        created_by_id=current_user.id
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.get("/")
def list_invite_codes(
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取邀请码列表（仅管理员，分页）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可查看邀请码")

    query = db.query(models.InviteCode).order_by(models.InviteCode.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return {"items": items, "total": total}


@router.delete("/{code_id}")
def delete_invite_code(
    code_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """软删除邀请码（仅管理员）
    
    不会真正删除，只是标记为已删除，以保留历史使用记录
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可删除邀请码")
    
    invite = db.query(models.InviteCode).filter(models.InviteCode.id == code_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="邀请码不存在")
    
    if invite.deleted_at:
        raise HTTPException(status_code=400, detail="邀请码已被删除")
    
    # 软删除：设置 deleted_at 和 is_active
    invite.deleted_at = datetime.now(timezone.utc)
    invite.is_active = False
    db.commit()
    return {"status": "success", "message": "邀请码已删除"}


@router.get("/{code_id}/usages", response_model=List[InviteCodeUsageResponse])
def get_invite_code_usages(
    code_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取邀请码使用记录（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可查看")
    
    invite = db.query(models.InviteCode).filter(models.InviteCode.id == code_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="邀请码不存在")
    
    usages = db.query(InviteCodeUsage).filter(InviteCodeUsage.invite_code_id == code_id).order_by(InviteCodeUsage.used_at.desc()).all()
    
    result = []
    for usage in usages:
        user = db.query(models.User).filter(models.User.id == usage.user_id).first()
        result.append({
            "id": usage.id,
            "user_email": user.email if user else "未知用户",
            "used_at": usage.used_at
        })
    
    return result