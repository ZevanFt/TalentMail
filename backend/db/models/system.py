from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    Boolean,
    Text,
    DateTime,
    func,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from ..database import Base


class VerificationCode(Base):
    """邮箱验证码，用于注册时验证外部邮箱"""
    __tablename__ = "verification_codes"
    __table_args__ = {'comment': '邮箱验证码表，用于注册时验证用户的外部邮箱'}
    
    id = Column(Integer, primary_key=True, comment="验证码唯一标识符")
    email = Column(String(255), nullable=False, index=True, comment="接收验证码的邮箱地址")
    code = Column(String(10), nullable=False, comment="6位数字验证码")
    purpose = Column(String(50), nullable=False, default="register", comment="用途：register/reset_password")
    is_used = Column(Boolean, default=False, comment="是否已使用")
    attempts = Column(Integer, default=0, comment="验证尝试次数")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


class ServerLog(Base):
    __tablename__ = "server_logs"
    __table_args__ = {'comment': '记录服务器的关键运行日志'}
    id = Column(BigInteger, primary_key=True, comment="日志唯一标识符")
    level = Column(String, comment="日志级别 ('INFO', 'WARN', 'ERROR')")
    source = Column(String, comment="日志来源 ('smtp', 'imap', 'web', 'system')")
    message = Column(Text, comment="日志内容")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="记录时间")


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = {'comment': '存储用户生成的用于API访问的密钥'}
    id = Column(Integer, primary_key=True, comment="API密钥唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    key = Column(String, unique=True, index=True, nullable=False, comment="API密钥字符串")
    permissions = Column(JSON, comment="密钥拥有的权限 (JSON格式)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    last_used_at = Column(DateTime(timezone=True), nullable=True, comment="最后使用时间")
    user = relationship("User")


class ReservedPrefix(Base):
    """保留的邮箱前缀，不允许普通用户注册"""
    __tablename__ = "reserved_prefixes"
    __table_args__ = {'comment': '保留的邮箱前缀列表，这些前缀不允许普通用户注册'}
    
    id = Column(Integer, primary_key=True, comment="保留前缀唯一标识符")
    prefix = Column(String(100), unique=True, nullable=False, index=True, comment="保留的前缀（小写）")
    category = Column(String(50), nullable=False, comment="分类：system/business/test/security/common")
    description = Column(String(255), nullable=True, comment="描述说明")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class SystemEmailTemplate(Base):
    """系统邮件模板，用于验证码、欢迎邮件、通知等系统邮件"""
    __tablename__ = "system_email_templates"
    __table_args__ = {'comment': '系统邮件模板表，存储验证码、欢迎邮件等系统级邮件模板'}
    
    id = Column(Integer, primary_key=True, comment="模板唯一标识符")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="模板代码，如 verification_code_register")
    name = Column(String(100), nullable=False, comment="模板名称")
    category = Column(String(50), nullable=False, default="system", comment="分类：system/notification/marketing")
    description = Column(String(255), nullable=True, comment="模板描述")
    subject = Column(String(255), nullable=False, comment="邮件主题，支持变量如 {{code}}")
    body_html = Column(Text, nullable=False, comment="HTML 邮件内容，支持变量")
    body_text = Column(Text, nullable=True, comment="纯文本邮件内容，支持变量")
    variables = Column(JSON, nullable=True, comment="可用变量列表，如 ['code', 'username', 'expires_minutes']")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")