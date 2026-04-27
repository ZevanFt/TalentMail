"""日历事件模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class CalendarEvent(Base):
    """日历事件"""
    __tablename__ = "calendar_events"
    __table_args__ = {'comment': '日历事件'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    title = Column(String(255), nullable=False, comment="事件标题")
    description = Column(Text, nullable=True, comment="事件描述")
    location = Column(String(500), nullable=True, comment="地点")
    start_time = Column(DateTime(timezone=True), nullable=False, index=True, comment="开始时间")
    end_time = Column(DateTime(timezone=True), nullable=False, comment="结束时间")
    all_day = Column(Boolean, default=False, comment="是否全天事件")
    color = Column(String(20), default="#3B82F6", comment="颜色标记")
    reminder_minutes = Column(Integer, nullable=True, comment="提前提醒分钟数")
    source_email_id = Column(Integer, ForeignKey("emails.id", ondelete="SET NULL"), nullable=True, comment="关联的邮件ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("User")
