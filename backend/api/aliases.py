from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from db import models
from db.models.email import Alias
from db.models.billing import Subscription, Plan
from api import deps
from core.config import settings
from datetime import datetime, timezone

router = APIRouter()


class AliasCreate(BaseModel):
    alias_prefix: str  # 别名前缀，不含域名
    name: Optional[str] = None


class AliasUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class AliasRead(BaseModel):
    id: int
    alias_email: str
    name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


def get_user_alias_limit(db: Session, user: models.User) -> int:
    """获取用户的别名数量限制"""
    if user.role == "admin":
        return -1  # 无限
    
    # 查找用户的活跃订阅
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()
    
    if subscription and subscription.current_period_end:
        if subscription.current_period_end > datetime.now(timezone.utc):
            plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
            if plan:
                return plan.max_aliases
    
    # 默认套餐
    default_plan = db.query(Plan).filter(Plan.is_default == True).first()
    return default_plan.max_aliases if default_plan else 0


@router.get("/", response_model=List[AliasRead])
def get_aliases(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取当前用户的别名列表"""
    items = db.query(Alias).filter(Alias.user_id == current_user.id).all()
    return items


@router.post("/", response_model=AliasRead)
def create_alias(
    data: AliasCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """创建新别名"""
    # 检查配额
    limit = get_user_alias_limit(db, current_user)
    current_count = db.query(Alias).filter(Alias.user_id == current_user.id).count()
    
    if limit != -1 and current_count >= limit:
        raise HTTPException(status_code=400, detail=f"已达到别名数量上限 ({limit})")
    
    # 构建完整别名邮箱
    prefix = data.alias_prefix.lower().strip()
    if not prefix:
        raise HTTPException(status_code=400, detail="别名前缀不能为空")
    
    alias_email = f"{prefix}@{settings.BASE_DOMAIN}"
    
    # 检查是否已存在
    existing = db.query(Alias).filter(Alias.alias_email == alias_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该别名已被使用")
    
    # 检查是否与用户邮箱冲突
    user_exists = db.query(models.User).filter(models.User.email == alias_email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="该地址已被注册为用户邮箱")
    
    alias = Alias(
        user_id=current_user.id,
        alias_email=alias_email,
        name=data.name,
        is_active=True
    )
    db.add(alias)
    db.commit()
    db.refresh(alias)
    
    return alias


@router.put("/{alias_id}", response_model=AliasRead)
def update_alias(
    alias_id: int,
    data: AliasUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """更新别名"""
    alias = db.query(Alias).filter(
        Alias.id == alias_id,
        Alias.user_id == current_user.id
    ).first()
    
    if not alias:
        raise HTTPException(status_code=404, detail="别名不存在")
    
    if data.name is not None:
        alias.name = data.name
    if data.is_active is not None:
        alias.is_active = data.is_active
    
    db.commit()
    db.refresh(alias)
    
    return alias


@router.delete("/{alias_id}")
def delete_alias(
    alias_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """删除别名"""
    alias = db.query(Alias).filter(
        Alias.id == alias_id,
        Alias.user_id == current_user.id
    ).first()
    
    if not alias:
        raise HTTPException(status_code=404, detail="别名不存在")
    
    db.delete(alias)
    db.commit()
    
    return {"status": "success", "message": "别名已删除"}