"""
自动化规则相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class AutomationRule(Base):
    """
    自动化规则表
    存储用户或系统创建的自动化规则
    """
    __tablename__ = "automation_rules"
    __table_args__ = {'comment': '自动化规则表'}

    id = Column(Integer, primary_key=True, index=True, comment='规则ID')
    name = Column(String(100), nullable=False, comment='规则名称')
    description = Column(Text, nullable=True, comment='规则描述')
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, comment='创建者ID (NULL表示系统规则)')
    is_system = Column(Boolean, default=False, comment='是否系统规则')
    is_active = Column(Boolean, default=True, comment='是否启用')
    priority = Column(Integer, default=0, comment='优先级 (数字越大越先执行)')
    
    # 触发器配置
    trigger_type = Column(String(50), nullable=False, comment='触发器类型: email_received/scheduled/user_event')
    trigger_config = Column(JSON, nullable=False, default=dict, comment='触发器详细配置')
    
    # 条件配置
    conditions = Column(JSON, nullable=True, comment='条件列表 (AND 关系)')
    
    # 动作配置
    actions = Column(JSON, nullable=False, default=list, comment='动作列表 (顺序执行)')
    
    # 统计
    execution_count = Column(Integer, default=0, comment='执行次数')
    last_executed_at = Column(DateTime(timezone=True), nullable=True, comment='最后执行时间')
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    owner = relationship("User", back_populates="automation_rules")
    logs = relationship("AutomationLog", back_populates="rule", cascade="all, delete-orphan")


class AutomationLog(Base):
    """
    规则执行日志表
    记录每次规则执行的详细信息
    """
    __tablename__ = "automation_logs"
    __table_args__ = {'comment': '规则执行日志表'}

    id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    rule_id = Column(Integer, ForeignKey("automation_rules.id", ondelete="CASCADE"), nullable=False, comment='规则ID')
    trigger_type = Column(String(50), nullable=False, comment='触发器类型')
    trigger_data = Column(JSON, nullable=True, comment='触发时的上下文数据')
    conditions_matched = Column(Boolean, default=False, comment='条件是否匹配')
    actions_executed = Column(JSON, nullable=True, comment='执行的动作及结果')
    status = Column(String(20), nullable=False, comment='执行状态: success/failed/partial')
    error_message = Column(Text, nullable=True, comment='错误信息')
    execution_time_ms = Column(Integer, nullable=True, comment='执行耗时(毫秒)')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    
    # 关系
    rule = relationship("AutomationRule", back_populates="logs")