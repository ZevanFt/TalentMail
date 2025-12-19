from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal


# --- Plan Schemas ---

class PlanBase(BaseModel):
    name: str
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    storage_quota_bytes: Optional[int] = None
    features: Optional[dict] = None
    max_domains: int = 0
    max_aliases: int = 5
    allow_temp_mail: bool = True
    max_temp_mailboxes: int = 3  # 临时邮箱数量限制


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    storage_quota_bytes: Optional[int] = None
    features: Optional[dict] = None
    max_domains: Optional[int] = None
    max_aliases: Optional[int] = None
    allow_temp_mail: Optional[bool] = None
    max_temp_mailboxes: Optional[int] = None


class PlanRead(PlanBase):
    id: int

    class Config:
        from_attributes = True


# --- Subscription Schemas ---

class SubscriptionBase(BaseModel):
    plan_id: int
    status: str = "active"
    current_period_end: Optional[datetime] = None


class SubscriptionCreate(SubscriptionBase):
    user_id: int


class SubscriptionRead(BaseModel):
    id: int
    user_id: int
    plan_id: int
    status: str
    current_period_end: Optional[datetime] = None
    plan: Optional[PlanRead] = None

    class Config:
        from_attributes = True


# --- Redemption Code Schemas ---

class RedemptionCodeBase(BaseModel):
    plan_id: int
    duration_days: int
    expires_at: Optional[datetime] = None


class RedemptionCodeCreate(RedemptionCodeBase):
    count: int = 1  # 批量生成数量
    prefix: Optional[str] = None  # 兑换码前缀


class RedemptionCodeRead(BaseModel):
    id: int
    code: str
    plan_id: int
    duration_days: int
    status: str
    created_by_id: Optional[int] = None
    used_by_id: Optional[int] = None
    used_by_email: Optional[str] = None  # 使用者邮箱
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    plan: Optional[PlanRead] = None

    class Config:
        from_attributes = True


class RedemptionCodeUse(BaseModel):
    code: str


class RedemptionCodeBatchResponse(BaseModel):
    codes: List[str]
    count: int


# --- User Subscription Status ---

class UserSubscriptionStatus(BaseModel):
    """用户订阅状态"""
    has_subscription: bool
    plan: Optional[PlanRead] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    is_admin: bool = False  # 是否为管理员（管理员不受限制）
    
    # 功能限制 (-1 表示无限)
    storage_quota_bytes: int
    storage_used_bytes: int
    storage_remaining_bytes: int
    max_temp_mailboxes: int
    current_temp_mailboxes: int
    max_aliases: int
    current_aliases: int
    max_domains: int
    current_domains: int
    allow_temp_mail: bool


# --- Redemption History ---

class RedemptionHistoryItem(BaseModel):
    code: str
    plan_name: str
    duration_days: int
    used_at: datetime

    class Config:
        from_attributes = True