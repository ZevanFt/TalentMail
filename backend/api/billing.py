"""
会员订阅制度 API
- 套餐管理 (管理员)
- 兑换码管理 (管理员)
- 用户订阅状态
- 兑换码使用
- 订阅历史记录
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
import string

from api import deps
from db.models import User
from db.models.billing import Plan, Subscription, RedemptionCode, SubscriptionHistory
from db.models.email import TempMailbox, Alias, Domain
from schemas import billing as billing_schema

router = APIRouter()


def generate_code(prefix: str = "", length: int = 16) -> str:
    """生成兑换码"""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(length))
    if prefix:
        return f"{prefix}-{code[:4]}-{code[4:8]}-{code[8:12]}-{code[12:]}"
    return f"{code[:4]}-{code[4:8]}-{code[8:12]}-{code[12:]}"


# ==================== 套餐管理 (管理员) ====================

@router.get("/plans", response_model=List[billing_schema.PlanRead])
def list_plans(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取所有套餐列表"""
    plans = db.query(Plan).all()
    return plans


@router.post("/plans", response_model=billing_schema.PlanRead)
def create_plan(
    plan_in: billing_schema.PlanCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """创建套餐 (管理员)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    
    plan = Plan(
        name=plan_in.name,
        price_monthly=plan_in.price_monthly,
        price_yearly=plan_in.price_yearly,
        storage_quota_bytes=plan_in.storage_quota_bytes,
        features=plan_in.features,
        max_domains=plan_in.max_domains,
        max_aliases=plan_in.max_aliases,
        allow_temp_mail=plan_in.allow_temp_mail,
        max_temp_mailboxes=plan_in.max_temp_mailboxes,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.put("/plans/{plan_id}", response_model=billing_schema.PlanRead)
def update_plan(
    plan_id: int,
    plan_in: billing_schema.PlanUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """更新套餐 (管理员)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    update_data = plan_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """删除套餐 (管理员)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    # 检查是否有用户正在使用此套餐
    active_subs = db.query(Subscription).filter(
        Subscription.plan_id == plan_id,
        Subscription.status == "active"
    ).count()
    if active_subs > 0:
        raise HTTPException(status_code=400, detail=f"有 {active_subs} 个用户正在使用此套餐，无法删除")
    
    db.delete(plan)
    db.commit()
    return {"status": "success"}


# ==================== 兑换码管理 (管理员) ====================

@router.get("/codes")
def list_redemption_codes(
    status: Optional[str] = Query(None, description="筛选状态: unused/used/expired"),
    plan_id: Optional[int] = Query(None, description="筛选套餐"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取兑换码列表 (管理员)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    
    query = db.query(RedemptionCode)
    if status:
        query = query.filter(RedemptionCode.status == status)
    if plan_id:
        query = query.filter(RedemptionCode.plan_id == plan_id)
    
    codes = query.order_by(RedemptionCode.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # 构建返回数据，包含使用者邮箱
    result = []
    for code in codes:
        used_by_email = None
        if code.used_by_id:
            used_by = db.query(User).filter(User.id == code.used_by_id).first()
            used_by_email = used_by.email if used_by else None
        
        result.append({
            "id": code.id,
            "code": code.code,
            "plan_id": code.plan_id,
            "duration_days": code.duration_days,
            "status": code.status,
            "created_by_id": code.created_by_id,
            "used_by_id": code.used_by_id,
            "used_by_email": used_by_email,
            "used_at": code.used_at,
            "expires_at": code.expires_at,
            "created_at": code.created_at,
        })
    
    return result


@router.post("/codes", response_model=billing_schema.RedemptionCodeBatchResponse)
def generate_redemption_codes(
    code_in: billing_schema.RedemptionCodeCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """批量生成兑换码 (管理员)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    
    # 验证套餐存在
    plan = db.query(Plan).filter(Plan.id == code_in.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    generated_codes = []
    for _ in range(code_in.count):
        # 生成唯一兑换码
        while True:
            code = generate_code(prefix=code_in.prefix or plan.name.upper())
            existing = db.query(RedemptionCode).filter(RedemptionCode.code == code).first()
            if not existing:
                break
        
        redemption_code = RedemptionCode(
            code=code,
            plan_id=code_in.plan_id,
            duration_days=code_in.duration_days,
            status="unused",
            created_by_id=current_user.id,
            expires_at=code_in.expires_at,
        )
        db.add(redemption_code)
        generated_codes.append(code)
    
    db.commit()
    return {"codes": generated_codes, "count": len(generated_codes)}


@router.get("/codes/stats")
def get_codes_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取兑换码统计 (管理员)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    
    total = db.query(RedemptionCode).count()
    unused = db.query(RedemptionCode).filter(RedemptionCode.status == "unused").count()
    used = db.query(RedemptionCode).filter(RedemptionCode.status == "used").count()
    expired = db.query(RedemptionCode).filter(RedemptionCode.status == "expired").count()
    
    return {
        "total": total,
        "unused": unused,
        "used": used,
        "expired": expired,
    }


@router.delete("/codes/{code_id}")
def revoke_redemption_code(
    code_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """作废兑换码 (管理员)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    
    code = db.query(RedemptionCode).filter(RedemptionCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="兑换码不存在")
    
    if code.status == "used":
        raise HTTPException(status_code=400, detail="已使用的兑换码无法作废")
    
    code.status = "expired"
    db.commit()
    return {"status": "success"}


# ==================== 用户订阅 ====================

@router.get("/subscription", response_model=billing_schema.UserSubscriptionStatus)
def get_subscription_status(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取当前用户的订阅状态
    
    管理员特权：管理员不受套餐限制，拥有无限资源
    """
    is_admin = current_user.role == "admin"
    
    # 查找用户的活跃订阅
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    # 获取默认套餐（Free）
    default_plan = db.query(Plan).filter(Plan.is_default == True).first()
    if not default_plan:
        # 如果没有默认套餐，使用第一个套餐或创建一个
        default_plan = db.query(Plan).first()
    
    # 确定当前套餐
    if subscription and subscription.current_period_end:
        if subscription.current_period_end > datetime.now(timezone.utc):
            current_plan = subscription.plan
            expires_at = subscription.current_period_end
            days_remaining = (subscription.current_period_end - datetime.now(timezone.utc)).days
        else:
            # 订阅已过期
            subscription.status = "expired"
            db.commit()
            current_plan = default_plan
            expires_at = None
            days_remaining = None
    else:
        current_plan = default_plan
        expires_at = None
        days_remaining = None
    
    # 统计用户当前使用量
    temp_mailbox_count = db.query(TempMailbox).filter(
        TempMailbox.owner_id == current_user.id,
        TempMailbox.is_active == True
    ).count()
    
    alias_count = db.query(Alias).filter(
        Alias.user_id == current_user.id,
        Alias.is_active == True
    ).count() if hasattr(Alias, 'user_id') else 0
    
    domain_count = db.query(Domain).filter(
        Domain.owner_id == current_user.id
    ).count() if hasattr(Domain, 'owner_id') else 0
    
    storage_used = current_user.storage_used_bytes or 0
    
    # 管理员特权：无限资源
    if is_admin:
        return billing_schema.UserSubscriptionStatus(
            has_subscription=True,  # 管理员视为永久订阅
            plan=current_plan,
            status="admin",  # 特殊状态标识
            expires_at=None,  # 永不过期
            days_remaining=None,
            is_admin=True,
            storage_quota_bytes=-1,  # -1 表示无限
            storage_used_bytes=storage_used,
            storage_remaining_bytes=-1,
            max_temp_mailboxes=-1,  # -1 表示无限
            current_temp_mailboxes=temp_mailbox_count,
            max_aliases=-1,
            current_aliases=alias_count,
            max_domains=-1,
            current_domains=domain_count,
            allow_temp_mail=True,
        )
    
    # 普通用户
    storage_quota = current_plan.storage_quota_bytes if current_plan else 1 * 1024 * 1024 * 1024  # 默认 1GB
    
    return billing_schema.UserSubscriptionStatus(
        has_subscription=subscription is not None and subscription.status == "active",
        plan=current_plan,
        status=subscription.status if subscription else None,
        expires_at=expires_at,
        days_remaining=days_remaining,
        is_admin=False,
        storage_quota_bytes=storage_quota or 1 * 1024 * 1024 * 1024,
        storage_used_bytes=storage_used,
        storage_remaining_bytes=max(0, (storage_quota or 0) - storage_used),
        max_temp_mailboxes=current_plan.max_temp_mailboxes if current_plan else 3,
        current_temp_mailboxes=temp_mailbox_count,
        max_aliases=current_plan.max_aliases if current_plan else 5,
        current_aliases=alias_count,
        max_domains=current_plan.max_domains if current_plan else 0,
        current_domains=domain_count,
        allow_temp_mail=current_plan.allow_temp_mail if current_plan else True,
    )


@router.post("/redeem")
def redeem_code(
    redeem_in: billing_schema.RedemptionCodeUse,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """使用兑换码"""
    # 查找兑换码
    code = db.query(RedemptionCode).filter(
        RedemptionCode.code == redeem_in.code.upper().strip()
    ).first()
    
    if not code:
        raise HTTPException(status_code=404, detail="兑换码不存在")
    
    if code.status == "used":
        raise HTTPException(status_code=400, detail="兑换码已被使用")
    
    if code.status == "expired":
        raise HTTPException(status_code=400, detail="兑换码已过期")
    
    if code.expires_at and code.expires_at < datetime.now(timezone.utc):
        code.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="兑换码已过期")
    
    # 获取套餐
    plan = db.query(Plan).filter(Plan.id == code.plan_id).first()
    if not plan:
        raise HTTPException(status_code=400, detail="套餐不存在")
    
    # 查找用户现有订阅
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.plan_id == code.plan_id,
        Subscription.status == "active"
    ).first()
    
    now = datetime.now(timezone.utc)
    
    if subscription:
        # 续费：在现有到期时间基础上增加
        if subscription.current_period_end and subscription.current_period_end > now:
            new_end = subscription.current_period_end + timedelta(days=code.duration_days)
        else:
            new_end = now + timedelta(days=code.duration_days)
        subscription.current_period_end = new_end
        subscription.status = "active"
    else:
        # 新订阅或升级
        # 先取消其他活跃订阅
        db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        ).update({"status": "canceled"})
        
        subscription = Subscription(
            user_id=current_user.id,
            plan_id=code.plan_id,
            status="active",
            current_period_end=now + timedelta(days=code.duration_days),
        )
        db.add(subscription)
    
    # 标记兑换码已使用
    code.status = "used"
    code.used_by_id = current_user.id
    code.used_at = now
    
    # 记录订阅历史
    history = SubscriptionHistory(
        user_id=current_user.id,
        plan_id=code.plan_id,
        action="redeem",
        duration_days=code.duration_days,
        redemption_code=code.code,
        operator_id=current_user.id,  # 自己兑换
        note=f"使用兑换码 {code.code} 激活 {plan.name} 套餐"
    )
    db.add(history)
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"成功激活 {plan.name} 套餐，有效期 {code.duration_days} 天",
        "plan_name": plan.name,
        "duration_days": code.duration_days,
        "expires_at": subscription.current_period_end.isoformat(),
    }


@router.get("/history")
def get_subscription_history(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取用户的订阅历史（包括自己兑换和管理员赠送）"""
    histories = db.query(SubscriptionHistory).filter(
        SubscriptionHistory.user_id == current_user.id
    ).order_by(SubscriptionHistory.created_at.desc()).all()
    
    result = []
    for h in histories:
        plan = db.query(Plan).filter(Plan.id == h.plan_id).first()
        operator = db.query(User).filter(User.id == h.operator_id).first() if h.operator_id else None
        
        # 判断操作者
        if h.operator_id == current_user.id:
            operator_name = "自己"
        elif operator:
            operator_name = operator.display_name or operator.email
        else:
            operator_name = "系统"
        
        result.append({
            "id": h.id,
            "action": h.action,
            "action_text": {
                "redeem": "兑换码激活",
                "admin_grant": "管理员赠送",
                "admin_modify": "管理员修改",
                "expire": "订阅过期",
            }.get(h.action, h.action),
            "plan_name": plan.name if plan else "未知套餐",
            "duration_days": h.duration_days,
            "redemption_code": h.redemption_code,
            "operator_name": operator_name,
            "note": h.note,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        })
    
    return result