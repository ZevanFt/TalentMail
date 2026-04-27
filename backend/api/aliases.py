from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from db import models
from db.models.email import Alias
from db.models.billing import Subscription, Plan
from api import deps
from core.config import settings
from utils.rate_limit import SlidingWindowLimiter
from datetime import datetime, timezone
import logging
import re

logger = logging.getLogger(__name__)
_alias_limiter = SlidingWindowLimiter(max_attempts=10, window_seconds=60)

router = APIRouter()


# 别名前缀正则：仅允许字母、数字、点、短横线、下划线（RFC 5321 local-part 安全子集）
_ALIAS_PREFIX_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')


class AliasCreate(BaseModel):
    alias_prefix: str = Field(..., min_length=1, max_length=64)  # 别名前缀，不含域名
    name: Optional[str] = Field(default=None, max_length=200)


class AliasUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
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


@router.get("/")
def get_aliases(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取当前用户的别名列表（分页）"""
    query = db.query(Alias).filter(Alias.user_id == current_user.id)
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return {"items": items, "total": total}


@router.post("/", response_model=AliasRead)
def create_alias(
    data: AliasCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """创建新别名"""
    if not _alias_limiter.allow(f"alias_create:{current_user.id}"):
        raise HTTPException(429, "操作过于频繁，请稍后再试")
    # 检查配额
    limit = get_user_alias_limit(db, current_user)
    current_count = db.query(Alias).filter(Alias.user_id == current_user.id).count()
    
    if limit != -1 and current_count >= limit:
        raise HTTPException(status_code=400, detail=f"已达到别名数量上限 ({limit})")
    
    # 构建完整别名邮箱
    prefix = data.alias_prefix.lower().strip()
    if not prefix:
        raise HTTPException(status_code=400, detail="别名前缀不能为空")
    if not _ALIAS_PREFIX_RE.match(prefix):
        raise HTTPException(status_code=400, detail="别名前缀只能包含字母、数字、点、短横线和下划线，且必须以字母或数字开头")
    
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
    logger.info(f"用户 {current_user.id} 创建别名: {alias_email}")

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
    logger.info(f"用户 {current_user.id} 更新别名 {alias_id}: active={alias.is_active}")

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
    
    alias_email = alias.alias_email
    db.delete(alias)
    db.commit()
    logger.info(f"用户 {current_user.id} 删除别名: {alias_email}")

    return {"status": "success", "message": "别名已删除"}