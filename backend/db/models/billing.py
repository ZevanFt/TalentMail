from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    BigInteger,
    DateTime,
    func,
    ForeignKey,
    JSON,
    DECIMAL,
)
from sqlalchemy.orm import relationship
from ..database import Base


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = {'comment': '定义了用户可以订阅的不同服务套餐'}
    id = Column(Integer, primary_key=True, comment="套餐唯一标识符")
    name = Column(String, nullable=False, comment="套餐名称 (e.g., 'Free', 'Pro')")
    price_monthly = Column(DECIMAL, comment="月付价格")
    price_yearly = Column(DECIMAL, comment="年付价格")
    storage_quota_bytes = Column(BigInteger, comment="存储空间配额（字节）")
    features = Column(JSON, comment="套餐包含的功能列表 (JSON格式)")
    # V10 Additions
    max_domains = Column(Integer, default=0, comment="允许绑定的最大域名数量")
    max_aliases = Column(Integer, default=5, comment="允许创建的最大别名数量")
    allow_temp_mail = Column(Boolean, default=True, comment="是否允许使用临时邮箱功能")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = {'comment': '记录用户的套餐订阅信息'}
    id = Column(Integer, primary_key=True, comment="订阅记录唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, comment="所订阅套餐的ID")
    status = Column(String, comment="订阅状态 (e.g., 'active', 'canceled', 'past_due')")
    current_period_end = Column(DateTime(timezone=True), comment="当前订阅周期的结束时间")
    user = relationship("User")
    plan = relationship("Plan")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {'comment': '记录所有支付和退款交易'}
    id = Column(Integer, primary_key=True, comment="交易记录唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True, comment="关联的订阅ID (如果适用)")
    amount = Column(DECIMAL, comment="交易金额")
    currency = Column(String, comment="货币单位 (e.g., 'USD')")
    status = Column(String, comment="交易状态 (e.g., 'succeeded', 'failed')")
    payment_gateway_charge_id = Column(String, comment="支付网关返回的交易ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="交易创建时间")
    user = relationship("User")
    subscription = relationship("Subscription")


class RedemptionCode(Base):
    __tablename__ = "redemption_codes"
    __table_args__ = {'comment': '存储用于兑换订阅时长的兑换码'}
    id = Column(Integer, primary_key=True, comment="兑换码唯一标识符")
    code = Column(String, unique=True, index=True, nullable=False, comment="兑换码字符串")
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, comment="关联的套餐ID")
    duration_days = Column(Integer, nullable=False, comment="可兑换的订阅天数")
    status = Column(String, default="unused", comment="状态 ('unused', 'used', 'expired')")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建该码的管理员ID")
    used_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="使用该码的用户ID")
    used_at = Column(DateTime(timezone=True), nullable=True, comment="使用时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    plan = relationship("Plan")
    created_by = relationship("User", foreign_keys=[created_by_id])
    used_by = relationship("User", foreign_keys=[used_by_id])