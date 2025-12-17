from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    func,
    ForeignKey,
    JSON,
    UUID as SQLAlchemy_UUID,
)
from sqlalchemy.orm import relationship
import uuid
from ..database import Base


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = {'comment': '存储用户的联系人信息'}
    id = Column(Integer, primary_key=True, comment="联系人唯一标识符")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="该联系人所属的用户ID")
    name = Column(String, comment="联系人姓名")
    email = Column(String, comment="联系人邮箱")
    phone = Column(String, nullable=True, comment="联系人电话")
    notes = Column(Text, nullable=True, comment="备注信息")
    owner = relationship("User")


class Filter(Base):
    __tablename__ = "filters"
    __table_args__ = {'comment': '存储用户自定义的邮件过滤规则'}
    id = Column(Integer, primary_key=True, comment="过滤器唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    name = Column(String, comment="过滤器名称")
    priority = Column(Integer, comment="执行优先级，数字越小优先级越高")
    conditions = Column(JSON, comment="过滤条件 (JSON格式)")
    actions = Column(JSON, comment="满足条件时执行的操作 (JSON格式)")
    user = relationship("User")


class Template(Base):
    __tablename__ = "templates"
    __table_args__ = {'comment': '存储用户创建的邮件模板'}
    id = Column(Integer, primary_key=True, comment="邮件模板唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    name = Column(String, comment="模板名称")
    subject = Column(String, comment="模板主题")
    body_html = Column(Text, comment="模板HTML内容")
    user = relationship("User")


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = {'comment': '存储用户自定义的邮件标签'}
    id = Column(Integer, primary_key=True, comment="标签唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    name = Column(String, comment="标签名称")
    color = Column(String, comment="标签颜色 (e.g., '#RRGGBB')")
    user = relationship("User")


class EmailTag(Base):
    __tablename__ = "email_tags"
    __table_args__ = {'comment': '邮件与标签的多对多关联表'}
    email_id = Column(Integer, ForeignKey("emails.id"), primary_key=True, comment="邮件ID")
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True, comment="标签ID")


class TrackingPixel(Base):
    __tablename__ = "tracking_pixels"
    __table_args__ = {'comment': '为启用追踪的邮件生成唯一的追踪像素'}
    id = Column(SQLAlchemy_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="追踪像素的唯一UUID")
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False, comment="关联的邮件ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    email = relationship("Email")


class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    __table_args__ = {'comment': '记录邮件追踪事件，如打开、点击链接等'}
    id = Column(Integer, primary_key=True, comment="追踪事件唯一标识符")
    pixel_id = Column(SQLAlchemy_UUID(as_uuid=True), ForeignKey("tracking_pixels.id"), nullable=False, comment="关联的追踪像素ID")
    event_type = Column(String, comment="事件类型 (e.g., 'opened', 'clicked')")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), comment="事件发生时间")
    ip_address = Column(String, nullable=True, comment="客户端IP地址")
    user_agent = Column(String, nullable=True, comment="客户端User Agent")
    pixel = relationship("TrackingPixel")