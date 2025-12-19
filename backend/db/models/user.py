from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    BigInteger,
    Date,
    Text,
    DateTime,
    func,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {'comment': '存储所有用户账户的核心信息'}
    id = Column(Integer, primary_key=True, index=True, comment="用户唯一标识符")
    email = Column(String, unique=True, nullable=False, index=True, comment="用户主邮箱地址，用于登录")
    phone = Column(String, unique=True, nullable=True, comment="用户手机号，可选，也可用于登录或恢复")
    password_hash = Column(String, nullable=False, comment="哈希处理后的用户密码")
    display_name = Column(String, comment="用户显示名称")
    avatar_url = Column(String, nullable=True, comment="用户头像图片的URL")
    theme = Column(String, default="system", comment="用户界面主题 (e.g., 'light', 'dark', 'system')")
    recovery_email = Column(String, nullable=True, comment="备用恢复邮箱")
    two_factor_enabled = Column(Boolean, default=False, comment="是否启用双因素认证")
    storage_used_bytes = Column(BigInteger, default=0, comment="已使用的存储空间（字节）")
    auto_reply_enabled = Column(Boolean, default=False, comment="是否启用自动回复")
    auto_reply_start_date = Column(Date, nullable=True, comment="自动回复开始日期")
    auto_reply_end_date = Column(Date, nullable=True, comment="自动回复结束日期")
    auto_reply_message = Column(Text, nullable=True, comment="自动回复的邮件内容")
    enable_desktop_notifications = Column(Boolean, default=True, comment="是否启用桌面通知")
    enable_sound_notifications = Column(Boolean, default=True, comment="是否启用声音通知")
    enable_pool_notifications = Column(Boolean, default=False, comment="是否启用邮件池通知")
    pool_enabled = Column(Boolean, default=False, comment="是否允许使用账号池功能")
    role = Column(String, default="user", comment="用户角色 ('admin' 或 'user')")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="用户账户创建时间")


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = {'comment': '记录用户的活跃会话，用于安全审计和设备管理'}
    id = Column(Integer, primary_key=True, comment="用户会话唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所属用户的ID")
    token_hash = Column(String(64), nullable=True, index=True, comment="Token哈希值，用于识别会话")
    device_info = Column(String, comment="设备信息 (e.g., 'Chrome on Windows')")
    browser = Column(String(100), nullable=True, comment="浏览器名称")
    os = Column(String(100), nullable=True, comment="操作系统")
    ip_address = Column(String(45), comment="登录IP地址")
    location = Column(String, nullable=True, comment="地理位置信息")
    is_active = Column(Boolean, default=True, comment="会话是否有效")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="登录时间")
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="最后活跃时间")
    user = relationship("User")


class PoolActivityLog(Base):
    __tablename__ = "pool_activity_logs"
    __table_args__ = {'comment': '账号池操作日志'}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False, comment="操作类型: create, delete")
    mailbox_email = Column(String(255), nullable=False, comment="邮箱地址")
    details = Column(Text, nullable=True, comment="详细信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now())