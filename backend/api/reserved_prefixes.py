"""
保留邮箱前缀管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from db.database import get_db
from db.models.system import ReservedPrefix
from db import models
from api import deps

router = APIRouter()


# Schemas
class ReservedPrefixCreate(BaseModel):
    prefix: str
    category: str = "custom"
    description: Optional[str] = None


class ReservedPrefixUpdate(BaseModel):
    prefix: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ReservedPrefixRead(BaseModel):
    id: int
    prefix: str
    category: str
    description: Optional[str]
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ReservedPrefixListResponse(BaseModel):
    items: List[ReservedPrefixRead]
    total: int


# Helper function
def is_prefix_reserved(db: Session, prefix: str) -> bool:
    """检查前缀是否被保留"""
    prefix_lower = prefix.lower().strip()
    return db.query(ReservedPrefix).filter(
        ReservedPrefix.prefix == prefix_lower,
        ReservedPrefix.is_active == True
    ).first() is not None


# Public API - 检查前缀是否可用
@router.get("/check/{prefix}")
def check_prefix_availability(
    prefix: str,
    db: Session = Depends(get_db)
):
    """
    检查邮箱前缀是否可用（公开接口，注册时使用）
    """
    prefix_lower = prefix.lower().strip()
    
    # 检查是否是保留前缀
    reserved = db.query(ReservedPrefix).filter(
        ReservedPrefix.prefix == prefix_lower,
        ReservedPrefix.is_active == True
    ).first()
    
    if reserved:
        return {
            "available": False,
            "reason": "reserved",
            "message": f"前缀 '{prefix}' 是系统保留前缀，不允许注册"
        }
    
    # 检查是否已被注册
    existing_user = db.query(models.User).filter(
        func.lower(func.split_part(models.User.email, '@', 1)) == prefix_lower
    ).first()
    
    if existing_user:
        return {
            "available": False,
            "reason": "taken",
            "message": f"前缀 '{prefix}' 已被注册"
        }
    
    return {
        "available": True,
        "reason": None,
        "message": f"前缀 '{prefix}' 可以使用"
    }


# Admin APIs
@router.get("/", response_model=ReservedPrefixListResponse)
def list_reserved_prefixes(
    category: Optional[str] = Query(None, description="按分类筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    q: Optional[str] = Query(None, description="搜索前缀"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取保留前缀列表（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    query = db.query(ReservedPrefix)
    
    if category:
        query = query.filter(ReservedPrefix.category == category)
    if is_active is not None:
        query = query.filter(ReservedPrefix.is_active == is_active)
    if q:
        query = query.filter(ReservedPrefix.prefix.ilike(f"%{q}%"))
    
    total = query.count()
    prefixes = query.order_by(ReservedPrefix.category, ReservedPrefix.prefix).offset((page - 1) * limit).limit(limit).all()
    
    items = []
    for p in prefixes:
        # 检查该前缀是否被用户使用
        user_with_prefix = db.query(models.User).filter(
            func.lower(func.split_part(models.User.email, '@', 1)) == p.prefix
        ).first()
        
        items.append({
            "id": p.id,
            "prefix": p.prefix,
            "category": p.category,
            "description": p.description,
            "is_active": p.is_active,
            "is_used": user_with_prefix is not None,
            "used_by": user_with_prefix.email if user_with_prefix else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None
        })
    
    return {"items": items, "total": total}


@router.post("/", response_model=ReservedPrefixRead)
def create_reserved_prefix(
    data: ReservedPrefixCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """创建保留前缀（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    prefix_lower = data.prefix.lower().strip()
    
    # 检查是否已存在
    existing = db.query(ReservedPrefix).filter(ReservedPrefix.prefix == prefix_lower).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"前缀 '{prefix_lower}' 已存在")
    
    prefix = ReservedPrefix(
        prefix=prefix_lower,
        category=data.category,
        description=data.description,
        is_active=True
    )
    db.add(prefix)
    db.commit()
    db.refresh(prefix)
    
    return {
        "id": prefix.id,
        "prefix": prefix.prefix,
        "category": prefix.category,
        "description": prefix.description,
        "is_active": prefix.is_active,
        "created_at": prefix.created_at.isoformat() if prefix.created_at else None,
        "updated_at": prefix.updated_at.isoformat() if prefix.updated_at else None
    }


@router.put("/{prefix_id}", response_model=ReservedPrefixRead)
def update_reserved_prefix(
    prefix_id: int,
    data: ReservedPrefixUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """更新保留前缀（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    prefix = db.query(ReservedPrefix).filter(ReservedPrefix.id == prefix_id).first()
    if not prefix:
        raise HTTPException(status_code=404, detail="前缀不存在")
    
    if data.prefix is not None:
        new_prefix = data.prefix.lower().strip()
        # 检查新前缀是否已存在
        existing = db.query(ReservedPrefix).filter(
            ReservedPrefix.prefix == new_prefix,
            ReservedPrefix.id != prefix_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"前缀 '{new_prefix}' 已存在")
        prefix.prefix = new_prefix
    
    if data.category is not None:
        prefix.category = data.category
    if data.description is not None:
        prefix.description = data.description
    if data.is_active is not None:
        prefix.is_active = data.is_active
    
    db.commit()
    db.refresh(prefix)
    
    return {
        "id": prefix.id,
        "prefix": prefix.prefix,
        "category": prefix.category,
        "description": prefix.description,
        "is_active": prefix.is_active,
        "created_at": prefix.created_at.isoformat() if prefix.created_at else None,
        "updated_at": prefix.updated_at.isoformat() if prefix.updated_at else None
    }


@router.delete("/{prefix_id}")
def delete_reserved_prefix(
    prefix_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """删除保留前缀（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    prefix = db.query(ReservedPrefix).filter(ReservedPrefix.id == prefix_id).first()
    if not prefix:
        raise HTTPException(status_code=404, detail="前缀不存在")
    
    db.delete(prefix)
    db.commit()
    
    return {"status": "success", "message": f"前缀 '{prefix.prefix}' 已删除"}


@router.get("/categories")
def get_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取所有分类（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    categories = db.query(ReservedPrefix.category).distinct().all()
    return [c[0] for c in categories]


@router.post("/batch")
def batch_create_prefixes(
    prefixes: List[ReservedPrefixCreate],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """批量创建保留前缀（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    created = 0
    skipped = 0
    
    for data in prefixes:
        prefix_lower = data.prefix.lower().strip()
        existing = db.query(ReservedPrefix).filter(ReservedPrefix.prefix == prefix_lower).first()
        if existing:
            skipped += 1
            continue
        
        prefix = ReservedPrefix(
            prefix=prefix_lower,
            category=data.category,
            description=data.description,
            is_active=True
        )
        db.add(prefix)
        created += 1
    
    db.commit()
    
    return {
        "status": "success",
        "created": created,
        "skipped": skipped,
        "message": f"创建了 {created} 个前缀，跳过了 {skipped} 个已存在的前缀"
    }