from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    Text,
    DateTime,
    func,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from ..database import Base


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