import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from schemas.user import UserRead, UserPasswordReset, UserUpdate, PasswordChange
from db import models
from api import deps
from crud import user as crud_user
from core import security

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


# Admin schemas
class UserAdminRead(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None
    role: str
    pool_enabled: bool
    created_at: str

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: List[UserAdminRead]
    total: int


class UserPermissionUpdate(BaseModel):
    role: Optional[str] = None
    pool_enabled: Optional[bool] = None


@router.get("/me", response_model=UserRead)
def read_users_me(current_user: models.User = Depends(deps.get_current_active_user)):
    """获取当前用户信息"""
    return current_user


@router.patch("/me", response_model=UserRead)
def update_users_me(
    user_update: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """更新当前用户信息"""
    if user_update.display_name is not None:
        current_user.display_name = user_update.display_name
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    if user_update.theme is not None:
        current_user.theme = user_update.theme
    # 通知设置
    if user_update.enable_desktop_notifications is not None:
        current_user.enable_desktop_notifications = user_update.enable_desktop_notifications
    if user_update.enable_sound_notifications is not None:
        current_user.enable_sound_notifications = user_update.enable_sound_notifications
    if user_update.enable_pool_notifications is not None:
        current_user.enable_pool_notifications = user_update.enable_pool_notifications
    # 自动回复
    if user_update.auto_reply_enabled is not None:
        current_user.auto_reply_enabled = user_update.auto_reply_enabled
    if user_update.auto_reply_start_date is not None:
        current_user.auto_reply_start_date = datetime.strptime(user_update.auto_reply_start_date, "%Y-%m-%d").date() if user_update.auto_reply_start_date else None
    if user_update.auto_reply_end_date is not None:
        current_user.auto_reply_end_date = datetime.strptime(user_update.auto_reply_end_date, "%Y-%m-%d").date() if user_update.auto_reply_end_date else None
    if user_update.auto_reply_message is not None:
        current_user.auto_reply_message = user_update.auto_reply_message
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password")
def change_password(
    data: PasswordChange,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """修改当前用户密码"""
    if not security.verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    current_user.password_hash = security.get_password_hash(data.new_password)
    db.add(current_user)
    db.commit()
    
    # 同步到邮件服务器
    crud_user.sync_user_to_mailserver(current_user.email, data.new_password)
    
    return {"status": "success", "message": "密码修改成功"}


@router.post("/reset-password-dev", status_code=200)
def reset_password_dev(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserPasswordReset,
):
    """开发接口：无需认证重置密码"""
    user = crud_user.reset_user_password(
        db=db, email=user_in.email, new_password=user_in.new_password
    )
    
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {user_in.email} 不存在")
        


# ========== Admin APIs ==========

@router.get("/admin/list")
def list_users(
    q: Optional[str] = Query(None, description="搜索关键词（邮箱或名称）"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取用户列表（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    query = db.query(models.User)
    
    if q:
        query = query.filter(
            (models.User.email.ilike(f"%{q}%")) | 
            (models.User.display_name.ilike(f"%{q}%"))
        )
    
    total = query.count()
    users = query.order_by(models.User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role,
                "pool_enabled": u.pool_enabled,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ],
        "total": total
    }


@router.patch("/admin/{user_id}/permissions")
def update_user_permissions(
    user_id: int,
    data: UserPermissionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """更新用户权限（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能修改自己的角色
    if data.role is not None and user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    
    if data.role is not None:
        if data.role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="无效的角色")
        user.role = data.role
        # admin 角色自动开启账号池
        if data.role == "admin":
            user.pool_enabled = True
    
    if data.pool_enabled is not None:
        user.pool_enabled = data.pool_enabled
    
    db.add(user)
    db.commit()
    
    return {"status": "success", "user_id": user_id, "role": user.role, "pool_enabled": user.pool_enabled}


@router.get("/me/storage")
def get_storage_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取当前用户存储统计"""
    from db.models.email import Email, Folder
    
    # 获取用户所有文件夹
    folders = db.query(Folder).filter(Folder.user_id == current_user.id).all()
    folder_ids = [f.id for f in folders]
    
    # 统计邮件数量
    total_emails = db.query(Email).filter(Email.folder_id.in_(folder_ids)).count() if folder_ids else 0
    
    # 简单估算存储（每封邮件约 10KB）
    estimated_bytes = total_emails * 10240
    
    # 默认 1GB，管理员 10GB
    storage_limit = 10 * 1024 * 1024 * 1024 if current_user.role == 'admin' else 1 * 1024 * 1024 * 1024
    
    return {
        "storage_used_bytes": current_user.storage_used_bytes or estimated_bytes,
        "storage_limit_bytes": storage_limit,
        "email_count": total_emails,
        "email_bytes": estimated_bytes
    }