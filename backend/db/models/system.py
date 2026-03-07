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


class Changelog(Base):
    """系统更新日志，记录项目版本更新历史"""
    __tablename__ = "changelogs"
    __table_args__ = {'comment': '系统更新日志表，记录项目版本更新历史和功能变更'}
    
    id = Column(Integer, primary_key=True, comment="更新日志唯一标识符")
    version = Column(String(50), nullable=False, index=True, comment="版本号，如 1.0.0, 1.1.0")
    title = Column(String(255), nullable=False, comment="更新标题")
    content = Column(Text, nullable=False, comment="更新内容（支持Markdown格式）")
    type = Column(String(50), nullable=False, default="release", comment="类型：release/hotfix/beta/alpha")
    category = Column(String(50), nullable=True, comment="分类：feature/bugfix/improvement/security")
    is_major = Column(Boolean, default=False, comment="是否为重大更新")
    is_published = Column(Boolean, default=True, comment="是否已发布（未发布的只有管理员可见）")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="发布时间")
    author = Column(String(100), nullable=True, comment="更新作者/负责人")
    tags = Column(JSON, nullable=True, comment="标签列表，如 ['新功能', '工作流', '模板']")
    breaking_changes = Column(Text, nullable=True, comment="破坏性变更说明")
    migration_notes = Column(Text, nullable=True, comment="迁移说明")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class TempMailboxPolicy(Base):
    """临时邮箱生命周期与清理策略（系统级单例）"""
    __tablename__ = "temp_mailbox_policies"
    __table_args__ = {'comment': '临时邮箱生命周期与自动清理策略配置'}

    id = Column(Integer, primary_key=True, comment="策略唯一标识符（单例）")
    cleanup_enabled = Column(Boolean, default=True, nullable=False, comment="是否启用自动清理")
    ttl_hours = Column(Integer, default=24, nullable=False, comment="临时邮箱有效期（小时）")
    recoverable_days = Column(Integer, default=10, nullable=False, comment="过期后可恢复天数")
    cleanup_interval_hours = Column(Integer, default=24, nullable=False, comment="自动清理执行周期（小时）")
    cleanup_batch_size = Column(Integer, default=500, nullable=False, comment="单次清理最大处理数量")
    delete_emails_on_purge = Column(Boolean, default=True, nullable=False, comment="清理邮箱时是否删除关联邮件")
    last_cleanup_at = Column(DateTime(timezone=True), nullable=True, comment="最近一次清理执行时间")
    last_cleanup_count = Column(Integer, default=0, nullable=False, comment="最近一次清理处理数量")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
