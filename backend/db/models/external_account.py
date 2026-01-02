from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base


class ExternalAccount(Base):
    """外部邮箱账号（如 Gmail、Outlook 等）"""
    __tablename__ = "external_accounts"
    __table_args__ = {'comment': '存储用户绑定的外部邮箱账号'}
    
    id = Column(Integer, primary_key=True, comment="账号唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户ID")
    email = Column(String, nullable=False, comment="外部邮箱地址")
    display_name = Column(String, nullable=True, comment="显示名称")
    provider = Column(String, default="custom", comment="邮箱提供商: gmail/outlook/custom")
    
    # IMAP 配置
    imap_host = Column(String, nullable=False, comment="IMAP 服务器地址")
    imap_port = Column(Integer, default=993, comment="IMAP 端口")
    imap_ssl = Column(Boolean, default=True, comment="是否使用 SSL")
    
    # SMTP 配置
    smtp_host = Column(String, nullable=False, comment="SMTP 服务器地址")
    smtp_port = Column(Integer, default=587, comment="SMTP 端口")
    smtp_ssl = Column(Boolean, default=False, comment="是否使用 SSL")
    smtp_starttls = Column(Boolean, default=True, comment="是否使用 STARTTLS")
    
    # 认证信息（加密存储）
    username = Column(String, nullable=False, comment="登录用户名")
    password = Column(Text, nullable=True, comment="登录密码（加密）")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    sync_enabled = Column(Boolean, default=True, comment="是否启用同步")
    last_sync_at = Column(DateTime(timezone=True), nullable=True, comment="最后同步时间")
    sync_error = Column(Text, nullable=True, comment="同步错误信息")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    user = relationship("User")