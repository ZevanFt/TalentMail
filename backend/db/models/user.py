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
    totp_secret = Column(String(32), nullable=True, comment="TOTP密钥，用于双因素认证")
    storage_used_bytes = Column(BigInteger, default=0, comment="已使用的存储空间（字节）")
    auto_reply_enabled = Column(Boolean, default=False, comment="是否启用自动回复")
    auto_reply_start_date = Column(Date, nullable=True, comment="自动回复开始日期")
    auto_reply_end_date = Column(Date, nullable=True, comment="自动回复结束日期")
    auto_reply_message = Column(Text, nullable=True, comment="自动回复的邮件内容")
    enable_desktop_notifications = Column(Boolean, default=True, comment="是否启用桌面通知")
    enable_sound_notifications = Column(Boolean, default=True, comment="是否启用声音通知")
    enable_pool_notifications = Column(Boolean, default=False, comment="是否启用邮件池通知")
    pool_enabled = Column(Boolean, default=False, comment="是否允许使用账号池功能")
    spam_filter_level = Column(String, default="standard", comment="垃圾邮件过滤级别 ('standard' 或 'strict')")
    block_external_images = Column(Boolean, default=True, comment="是否阻止外部图片加载")
    auto_clean_trash = Column(Boolean, default=True, comment="是否自动清空垃圾箱（30天）")
    auto_archive_old = Column(Boolean, default=False, comment="是否自动归档旧邮件（1年）")
    role = Column(String, default="user", comment="用户角色 ('admin' 或 'user')")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="用户账户创建时间")
    
    # 关系
    automation_rules = relationship("AutomationRule", back_populates="owner", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="owner", cascade="all, delete-orphan")


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


class BlockedSender(Base):
    __tablename__ = "blocked_senders"
    __table_args__ = {'comment': '用户屏蔽的发件人黑名单'}
    id = Column(Integer, primary_key=True, comment="黑名单记录ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所属用户ID")
    email = Column(String(255), nullable=False, comment="被屏蔽的邮箱地址")
    reason = Column(String(255), nullable=True, comment="屏蔽原因")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="添加时间")
    user = relationship("User")


class TrustedSender(Base):
    """白名单 - 信任的发件人"""
    __tablename__ = "trusted_senders"
    __table_args__ = {'comment': '用户信任的发件人白名单'}
    id = Column(Integer, primary_key=True, comment="白名单记录ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所属用户ID")
    email = Column(String(255), nullable=False, comment="信任的邮箱地址（可以是完整地址或域名如 @example.com）")
    sender_type = Column(String(20), nullable=False, default="email", comment="类型: 'email'(完整地址) 或 'domain'(整个域名)")
    note = Column(String(255), nullable=True, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="添加时间")
    user = relationship("User")


class SpamReport(Base):
    """垃圾邮件报告记录"""
    __tablename__ = "spam_reports"
    __table_args__ = {'comment': '垃圾邮件报告记录，用于训练过滤器'}
    id = Column(Integer, primary_key=True, comment="报告ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="报告用户ID")
    email_id = Column(Integer, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, comment="被报告的邮件ID")
    report_type = Column(String(20), nullable=False, comment="报告类型: 'spam'(标记为垃圾) 或 'ham'(标记为非垃圾)")
    original_folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, comment="邮件原始文件夹ID")
    learned = Column(Boolean, default=False, comment="是否已学习到 SpamAssassin")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="报告时间")
    user = relationship("User")
    email = relationship("Email", foreign_keys=[email_id])