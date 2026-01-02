"""文件中转站模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Boolean
from sqlalchemy.sql import func
from db.database import Base


class DriveFile(Base):
    """文件中转站文件"""
    __tablename__ = "drive_files"
    __table_args__ = {'comment': '文件中转站'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    filename = Column(String(255), nullable=False, comment="文件名")
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    content_type = Column(String(100), comment="MIME类型")
    size = Column(BigInteger, default=0, comment="文件大小(字节)")
    storage_path = Column(String(500), nullable=False, comment="存储路径")
    share_code = Column(String(32), unique=True, index=True, comment="分享码")
    share_password = Column(String(32), comment="分享密码")
    share_expires_at = Column(DateTime, comment="分享过期时间")
    download_count = Column(Integer, default=0, comment="下载次数")
    is_public = Column(Boolean, default=False, comment="是否公开分享")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")