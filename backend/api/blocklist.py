from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from db import models
from db.models.user import BlockedSender
from api import deps

router = APIRouter()


class BlockedSenderCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    reason: Optional[str] = Field(default=None, max_length=500)


class BlockedSenderRead(BaseModel):
    id: int
    email: str
    reason: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/")
def get_blocked_senders(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取当前用户的黑名单列表（分页）"""
    query = db.query(BlockedSender).filter(
        BlockedSender.user_id == current_user.id
    ).order_by(BlockedSender.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "items": [
            {
                "id": item.id,
                "email": item.email,
                "reason": item.reason,
                "created_at": item.created_at.isoformat() if item.created_at else None
            }
            for item in items
        ],
        "total": total,
    }


@router.post("/", response_model=BlockedSenderRead)
def add_blocked_sender(
    data: BlockedSenderCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """添加邮箱到黑名单"""
    email = data.email.lower().strip()
    
    # 检查是否已存在
    existing = db.query(BlockedSender).filter(
        BlockedSender.user_id == current_user.id,
        BlockedSender.email == email
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已在黑名单中")
    
    blocked = BlockedSender(
        user_id=current_user.id,
        email=email,
        reason=data.reason
    )
    db.add(blocked)
    db.commit()
    db.refresh(blocked)
    
    return {
        "id": blocked.id,
        "email": blocked.email,
        "reason": blocked.reason,
        "created_at": blocked.created_at.isoformat() if blocked.created_at else None
    }


@router.delete("/{blocked_id}")
def remove_blocked_sender(
    blocked_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """从黑名单移除邮箱"""
    blocked = db.query(BlockedSender).filter(
        BlockedSender.id == blocked_id,
        BlockedSender.user_id == current_user.id
    ).first()
    
    if not blocked:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    db.delete(blocked)
    db.commit()
    
    return {"status": "success", "message": "已从黑名单移除"}