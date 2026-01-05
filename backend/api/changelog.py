"""
更新日志 API
提供系统更新日志的 CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from api.deps import get_db, get_current_user_from_token, get_current_admin_user
from db.models.system import Changelog
from db.models.user import User
from schemas.changelog import (
    ChangelogCreate,
    ChangelogUpdate,
    ChangelogResponse,
    ChangelogListResponse
)

router = APIRouter()

# 可选的认证
security = HTTPBearer(auto_error=False)


def get_optional_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """获取可选的当前用户（不强制要求认证）"""
    if not credentials:
        return None
    try:
        user = get_current_user_from_token(db, credentials.credentials)
        return user
    except:
        return None


@router.get("", response_model=ChangelogListResponse)
async def list_changelogs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    type: Optional[str] = Query(None, description="类型筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_major: Optional[bool] = Query(None, description="是否重大更新"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取更新日志列表
    - 普通用户只能看到已发布的日志
    - 管理员可以看到所有日志（包括未发布的）
    """
    query = db.query(Changelog)
    
    # 非管理员只能看到已发布的
    is_admin = current_user and current_user.role == "admin"
    if not is_admin:
        query = query.filter(Changelog.is_published == True)
    
    # 类型筛选
    if type:
        query = query.filter(Changelog.type == type)
    
    # 分类筛选
    if category:
        query = query.filter(Changelog.category == category)
    
    # 重大更新筛选
    if is_major is not None:
        query = query.filter(Changelog.is_major == is_major)
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    items = query.order_by(desc(Changelog.created_at)).offset(offset).limit(page_size).all()
    
    return ChangelogListResponse(
        items=[ChangelogResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=offset + len(items) < total
    )


@router.get("/latest", response_model=ChangelogResponse)
async def get_latest_changelog(
    db: Session = Depends(get_db)
):
    """获取最新的更新日志"""
    changelog = db.query(Changelog).filter(
        Changelog.is_published == True
    ).order_by(desc(Changelog.created_at)).first()
    
    if not changelog:
        raise HTTPException(status_code=404, detail="暂无更新日志")
    
    return changelog


@router.get("/{changelog_id}", response_model=ChangelogResponse)
async def get_changelog(
    changelog_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取单个更新日志"""
    changelog = db.query(Changelog).filter(Changelog.id == changelog_id).first()
    
    if not changelog:
        raise HTTPException(status_code=404, detail="更新日志不存在")
    
    # 非管理员不能查看未发布的
    is_admin = current_user and current_user.role == "admin"
    if not changelog.is_published and not is_admin:
        raise HTTPException(status_code=404, detail="更新日志不存在")
    
    return changelog


@router.post("", response_model=ChangelogResponse)
async def create_changelog(
    data: ChangelogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建更新日志（仅管理员）"""
    changelog = Changelog(
        version=data.version,
        title=data.title,
        content=data.content,
        type=data.type,
        category=data.category,
        is_major=data.is_major,
        is_published=data.is_published,
        published_at=datetime.utcnow() if data.is_published else None,
        author=data.author or current_user.display_name or current_user.email,
        tags=data.tags,
        breaking_changes=data.breaking_changes,
        migration_notes=data.migration_notes
    )
    
    db.add(changelog)
    db.commit()
    db.refresh(changelog)
    
    return changelog


@router.put("/{changelog_id}", response_model=ChangelogResponse)
async def update_changelog(
    changelog_id: int,
    data: ChangelogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新更新日志（仅管理员）"""
    changelog = db.query(Changelog).filter(Changelog.id == changelog_id).first()
    
    if not changelog:
        raise HTTPException(status_code=404, detail="更新日志不存在")
    
    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    
    # 如果从未发布变为已发布，设置发布时间
    if "is_published" in update_data and update_data["is_published"] and not changelog.is_published:
        update_data["published_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(changelog, field, value)
    
    db.commit()
    db.refresh(changelog)
    
    return changelog


@router.delete("/{changelog_id}")
async def delete_changelog(
    changelog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除更新日志（仅管理员）"""
    changelog = db.query(Changelog).filter(Changelog.id == changelog_id).first()
    
    if not changelog:
        raise HTTPException(status_code=404, detail="更新日志不存在")
    
    db.delete(changelog)
    db.commit()
    
    return {"message": "删除成功"}


@router.post("/{changelog_id}/publish", response_model=ChangelogResponse)
async def publish_changelog(
    changelog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """发布更新日志（仅管理员）"""
    changelog = db.query(Changelog).filter(Changelog.id == changelog_id).first()
    
    if not changelog:
        raise HTTPException(status_code=404, detail="更新日志不存在")
    
    if changelog.is_published:
        raise HTTPException(status_code=400, detail="该日志已发布")
    
    changelog.is_published = True
    changelog.published_at = datetime.utcnow()
    
    db.commit()
    db.refresh(changelog)
    
    return changelog


@router.post("/{changelog_id}/unpublish", response_model=ChangelogResponse)
async def unpublish_changelog(
    changelog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """取消发布更新日志（仅管理员）"""
    changelog = db.query(Changelog).filter(Changelog.id == changelog_id).first()
    
    if not changelog:
        raise HTTPException(status_code=404, detail="更新日志不存在")
    
    if not changelog.is_published:
        raise HTTPException(status_code=400, detail="该日志未发布")
    
    changelog.is_published = False
    
    db.commit()
    db.refresh(changelog)
    
    return changelog