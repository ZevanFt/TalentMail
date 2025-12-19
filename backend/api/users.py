import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel

from schemas.user import UserRead, UserPasswordReset, UserUpdate, PasswordChange
from db import models
from db.models.user import UserSession
from db.models.billing import Plan, Subscription
from api import deps
from crud import user as crud_user
from core import security
from core.config import settings

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
    plan_name: Optional[str] = None  # 当前套餐名称
    plan_id: Optional[int] = None  # 当前套餐ID
    subscription_expires_at: Optional[str] = None  # 订阅到期时间

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: List[UserAdminRead]
    total: int


class UserPermissionUpdate(BaseModel):
    role: Optional[str] = None
    pool_enabled: Optional[bool] = None
    plan_id: Optional[int] = None  # 修改用户套餐
    subscription_days: Optional[int] = None  # 订阅天数（用于新建/续费）


class AdminUserCreate(BaseModel):
    """管理员创建用户的请求体"""
    email_prefix: str  # 邮箱前缀
    password: str
    display_name: Optional[str] = None
    role: str = "user"  # user 或 admin
    pool_enabled: bool = False
    plan_id: Optional[int] = None
    subscription_days: Optional[int] = 30


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
    
    # 获取默认套餐
    default_plan = db.query(Plan).filter(Plan.is_default == True).first()
    
    # 构建用户列表，包含订阅信息
    items = []
    for u in users:
        # 查找用户的活跃订阅
        subscription = db.query(Subscription).filter(
            Subscription.user_id == u.id,
            Subscription.status == "active"
        ).first()
        
        plan_name = None
        plan_id = None
        subscription_expires_at = None
        
        if u.role == "admin":
            plan_name = "管理员 (无限)"
        elif subscription and subscription.current_period_end:
            if subscription.current_period_end > datetime.now(timezone.utc):
                plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
                plan_name = plan.name if plan else "未知"
                plan_id = subscription.plan_id
                subscription_expires_at = subscription.current_period_end.isoformat()
            else:
                # 订阅已过期
                plan_name = default_plan.name if default_plan else "Free"
                plan_id = default_plan.id if default_plan else None
        else:
            plan_name = default_plan.name if default_plan else "Free"
            plan_id = default_plan.id if default_plan else None
        
        items.append({
            "id": u.id,
            "email": u.email,
            "display_name": u.display_name,
            "role": u.role,
            "pool_enabled": u.pool_enabled,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "plan_name": plan_name,
            "plan_id": plan_id,
            "subscription_expires_at": subscription_expires_at
        })
    
    return {
        "items": items,
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
    
    # 修改用户套餐
    if data.plan_id is not None:
        plan = db.query(Plan).filter(Plan.id == data.plan_id).first()
        if not plan:
            raise HTTPException(status_code=400, detail="套餐不存在")
        
        # 查找现有订阅
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active"
        ).first()
        
        now = datetime.now(timezone.utc)
        days = data.subscription_days or 30  # 默认30天
        
        if subscription:
            # 更新现有订阅
            if subscription.plan_id == data.plan_id:
                # 同套餐续费
                if subscription.current_period_end and subscription.current_period_end > now:
                    subscription.current_period_end = subscription.current_period_end + timedelta(days=days)
                else:
                    subscription.current_period_end = now + timedelta(days=days)
            else:
                # 切换套餐
                subscription.plan_id = data.plan_id
                subscription.current_period_end = now + timedelta(days=days)
            subscription.status = "active"
        else:
            # 创建新订阅
            subscription = Subscription(
                user_id=user_id,
                plan_id=data.plan_id,
                status="active",
                current_period_end=now + timedelta(days=days)
            )
            db.add(subscription)
    
    db.add(user)
    db.commit()
    
    # 获取更新后的订阅信息
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active"
    ).first()
    
    plan_name = None
    plan_id = None
    subscription_expires_at = None
    
    if subscription and subscription.current_period_end:
        plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
        plan_name = plan.name if plan else None
        plan_id = subscription.plan_id
        subscription_expires_at = subscription.current_period_end.isoformat()
    
    return {
        "status": "success",
        "user_id": user_id,
        "role": user.role,
        "pool_enabled": user.pool_enabled,
        "plan_name": plan_name,
        "plan_id": plan_id,
        "subscription_expires_at": subscription_expires_at
    }


@router.post("/admin/create")
def admin_create_user(
    data: AdminUserCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    管理员创建用户（绕过保留前缀检查和邀请码验证）
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    # 构建完整邮箱
    email_prefix = data.email_prefix.lower().strip()
    email = f"{email_prefix}@{settings.BASE_DOMAIN}"
    
    # 检查邮箱是否已存在
    existing_user = crud_user.get_user_by_email(db, email=email)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"邮箱 {email} 已被注册")
    
    # 验证角色
    if data.role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="无效的角色，只能是 admin 或 user")
    
    # 创建用户（不需要邀请码）
    password_hash = security.get_password_hash(data.password)
    
    new_user = models.User(
        email=email,
        password_hash=password_hash,
        display_name=data.display_name or email_prefix,
        role=data.role,
        pool_enabled=data.pool_enabled or (data.role == "admin")  # admin 自动开启
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 创建默认文件夹
    try:
        crud_user.create_default_folders_for_user(db, user_id=new_user.id)
    except Exception as e:
        logger.error(f"创建默认文件夹失败: {e}")
    
    # 同步到邮件服务器
    try:
        crud_user.sync_user_to_mailserver(email, data.password)
    except Exception as e:
        logger.error(f"同步到邮件服务器失败: {e}")
    
    # 如果指定了套餐，创建订阅
    plan_name = None
    subscription_expires_at = None
    
    if data.plan_id:
        plan = db.query(Plan).filter(Plan.id == data.plan_id).first()
        if plan:
            now = datetime.now(timezone.utc)
            days = data.subscription_days or 30
            subscription = Subscription(
                user_id=new_user.id,
                plan_id=data.plan_id,
                status="active",
                current_period_end=now + timedelta(days=days)
            )
            db.add(subscription)
            db.commit()
            plan_name = plan.name
            subscription_expires_at = subscription.current_period_end.isoformat()
    else:
        # 使用默认套餐
        default_plan = db.query(Plan).filter(Plan.is_default == True).first()
        if default_plan:
            plan_name = default_plan.name
    
    logger.info(f"管理员 {current_user.email} 创建了用户 {email}")
    
    return {
        "status": "success",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "display_name": new_user.display_name,
            "role": new_user.role,
            "pool_enabled": new_user.pool_enabled,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
            "plan_name": plan_name,
            "subscription_expires_at": subscription_expires_at
        }
    }


@router.delete("/admin/{user_id}")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    管理员删除用户
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    email = user.email
    
    # 删除用户相关数据
    # 1. 删除订阅
    db.query(Subscription).filter(Subscription.user_id == user_id).delete()
    
    # 2. 删除登录会话
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    
    # 3. 删除用户
    db.delete(user)
    db.commit()
    
    logger.info(f"管理员 {current_user.email} 删除了用户 {email}")
    
    return {"status": "success", "message": f"用户 {email} 已删除"}


# ========== Login Sessions APIs ==========

class LoginSessionRead(BaseModel):
    id: int
    device_info: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None
    last_active_at: Optional[str] = None
    is_current: bool = False

    class Config:
        from_attributes = True


@router.get("/me/sessions", response_model=List[LoginSessionRead])
def get_login_sessions(
    limit: int = Query(10, ge=1, le=50, description="返回记录数量"),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取当前用户的登录历史"""
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id
    ).order_by(desc(UserSession.created_at)).limit(limit).all()
    
    result = []
    for s in sessions:
        result.append({
            "id": s.id,
            "device_info": s.device_info,
            "browser": s.browser,
            "os": s.os,
            "ip_address": s.ip_address,
            "location": s.location,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "last_active_at": s.last_active_at.isoformat() if s.last_active_at else None,
            "is_current": False  # TODO: 可以通过 token_hash 判断
        })
    
    return result


@router.delete("/me/sessions/{session_id}")
def revoke_session(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """撤销指定的登录会话"""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session.is_active = False
    db.commit()
    
    return {"status": "success", "message": "会话已撤销"}


@router.delete("/me/sessions")
def revoke_all_sessions(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """撤销所有登录会话（除当前会话外）"""
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).update({"is_active": False})
    db.commit()
    
    return {"status": "success", "message": "所有会话已撤销"}


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