import logging
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from db import models
from api import deps

logger = logging.getLogger(__name__)
router = APIRouter()


class InviteCodeCreate(BaseModel):
    max_uses: int = 1  # 0 表示无限
    expires_days: Optional[int] = None  # None 表示永不过期


class InviteCodeResponse(BaseModel):
    id: int
    code: str
    max_uses: int
    used_count: int
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool

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


@router.get("/", response_model=List[InviteCodeResponse])
def list_invite_codes(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取邀请码列表（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可查看邀请码")
    
    return db.query(models.InviteCode).order_by(models.InviteCode.created_at.desc()).all()


@router.delete("/{code_id}")
def delete_invite_code(
    code_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """删除邀请码（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可删除邀请码")
    
    invite = db.query(models.InviteCode).filter(models.InviteCode.id == code_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="邀请码不存在")
    
    db.delete(invite)
    db.commit()
    return {"status": "success"}