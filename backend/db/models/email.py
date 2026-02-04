from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    func,
    ForeignKey,
    UUID as SQLAlchemy_UUID,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
import uuid
from ..database import Base


class Folder(Base):
    __tablename__ = "folders"
    __table_args__ = {'comment': '存储用户自定义和系统的邮件文件夹'}
    id = Column(Integer, primary_key=True, comment="文件夹唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    name = Column(String, nullable=False, comment="文件夹显示名称")
    parent_id = Column(Integer, ForeignKey("folders.id"), nullable=True, comment="父文件夹ID，用于支持文件夹嵌套")
    role = Column(String, default="user", comment="文件夹角色 ('inbox', 'sent', 'drafts', 'trash', 'spam', 'archive' 等系统角色, 或 'user' 自定义文件夹)")
    user = relationship("User")
    parent = relationship("Folder", remote_side=[id])


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = {'comment': '存储所有邮件的核心内容和元数据'}
    id = Column(Integer, primary_key=True, comment="邮件唯一标识符")
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=False, comment="邮件所在的文件夹ID")
    mailbox_address = Column(String, index=True, comment="接收该邮件的邮箱地址（用于区分不同别名/域名收到的邮件）")
    message_id = Column(String, unique=False, nullable=True, comment="邮件的全局唯一Message-ID（发送后才有）")
    in_reply_to = Column(String, nullable=True, comment="回复的邮件的Message-ID")
    references = Column(Text, nullable=True, comment="邮件引用链（空格分隔的Message-ID列表）")
    thread_id = Column(String, nullable=True, index=True, comment="邮件所属线索的ID")
    subject = Column(String, comment="邮件主题")
    sender = Column(String, comment="发件人地址")
    recipients = Column(Text, comment="收件人地址列表 (JSON或逗号分隔)")
    body_text = Column(Text, nullable=True, comment="邮件内容的纯文本版本")
    body_html = Column(Text, nullable=True, comment="邮件内容的HTML版本")
    received_at = Column(DateTime(timezone=True), server_default=func.now(), comment="邮件接收时间")
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_starred = Column(Boolean, default=False, comment="是否已加星标")
    is_draft = Column(Boolean, default=False, comment="是否为草稿")
    sent_at = Column(DateTime(timezone=True), nullable=True, comment="邮件发送时间")
    scheduled_send_at = Column(DateTime(timezone=True), nullable=True, comment="计划发送时间")
    snoozed_until = Column(DateTime(timezone=True), nullable=True, comment="邮件被推迟到何时显示")
    is_tracked = Column(Boolean, default=False, comment="是否启用邮件追踪")
    delivery_status = Column(String, default="pending", comment="投递状态: pending/sending/sent/delivered/failed")
    delivery_error = Column(Text, nullable=True, comment="投递失败的错误信息")
    # Soft delete fields
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="软删除时间戳，非空表示已移入回收站")
    is_purged = Column(Boolean, default=False, comment="是否已从回收站彻底清除")
    # Full-text search vector (PostgreSQL tsvector)
    search_vector = Column(TSVECTOR, nullable=True, comment="全文搜索向量，包含主题、发件人和正文的分词结果")
    folder = relationship("Folder")
    tags = relationship("Tag", secondary="email_tags", backref="emails")


class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = {'comment': '存储邮件附件的信息'}
    id = Column(Integer, primary_key=True, comment="附件唯一标识符")
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=True, comment="所属邮件的ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上传用户ID")
    filename = Column(String, comment="附件原始文件名")
    content_type = Column(String, comment="附件的MIME类型")
    size = Column(Integer, default=0, comment="文件大小(字节)")
    file_path = Column(String, nullable=True, comment="附件在存储系统中的路径")
    attached_email_id = Column(Integer, ForeignKey("emails.id"), nullable=True, comment="如果附件本身是一封邮件(eml)，则关联其ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="上传时间")
    email = relationship("Email", foreign_keys=[email_id])
    user = relationship("User")


class Signature(Base):
    __tablename__ = "signatures"
    __table_args__ = {'comment': '存储用户的邮件签名'}
    id = Column(Integer, primary_key=True, comment="签名唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    name = Column(String, comment="签名名称")
    content_html = Column(Text, comment="签名的HTML内容")
    is_default = Column(Boolean, default=False, comment="是否为默认签名")
    user = relationship("User")


class Alias(Base):
    __tablename__ = "aliases"
    __table_args__ = {'comment': '存储用户的邮箱别名'}
    id = Column(Integer, primary_key=True, comment="邮箱别名唯一标识符")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    alias_email = Column(String, unique=True, nullable=False, comment="别名邮箱地址")
    name = Column(String, nullable=True, comment="别名名称/描述")
    is_active = Column(Boolean, default=True, comment="别名是否激活")
    user = relationship("User")


class TempMailbox(Base):
    __tablename__ = "temp_mailboxes"
    __table_args__ = {'comment': '存储用户创建的临时邮箱'}
    id = Column(Integer, primary_key=True, comment="临时邮箱唯一标识符")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    email = Column(String, unique=True, nullable=False, comment="临时邮箱地址")
    purpose = Column(String, nullable=True, comment="创建该临时邮箱的用途")
    auto_verify_codes = Column(Boolean, default=False, comment="是否自动提取邮件中的验证码")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    owner = relationship("User")


class Domain(Base):
    __tablename__ = "domains"
    __table_args__ = {'comment': '存储用户绑定的自定义域名'}
    id = Column(Integer, primary_key=True, comment="自定义域名唯一标识符")
    domain_name = Column(String, unique=True, nullable=False, comment="域名名称")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户的ID")
    dkim_selector = Column(String, default="default", comment="DKIM选择器")
    dkim_private_key = Column(Text, nullable=True, comment="DKIM私钥")
    dkim_public_key = Column(Text, nullable=True, comment="DKIM公钥")
    is_verified = Column(Boolean, default=False, comment="域名所有权是否已验证")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="添加时间")
    owner = relationship("User")