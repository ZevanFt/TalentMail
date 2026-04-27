from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
from .common import CustomEmailStr

# --- Email Schemas ---

class EmailRecipient(BaseModel):
    """Represents a single email recipient."""
    name: Optional[str] = Field(default=None, max_length=200)
    email: CustomEmailStr

class EmailCreate(BaseModel):
    """Schema for creating/sending a new email (input)."""
    to: List[EmailRecipient] = Field(..., max_length=100)  # 最多 100 个收件人
    cc: Optional[List[EmailRecipient]] = Field(default=[], max_length=100)
    bcc: Optional[List[EmailRecipient]] = Field(default=[], max_length=100)
    subject: str = Field(default="", max_length=998)  # RFC 2822 行长度限制
    body_html: str = Field(default="", max_length=5_000_000)  # 5MB 上限
    body_text: Optional[str] = Field(default=None, max_length=2_000_000)
    reply_to_id: Optional[int] = None  # 回复的邮件ID
    is_tracked: bool = False  # 是否启用追踪
    attachment_ids: Optional[List[int]] = Field(default=[], max_length=50)  # 最多 50 个附件
    scheduled_send_at: Optional[datetime] = None  # 定时发送时间（UTC）
    from_alias_id: Optional[int] = None  # 使用别名地址发送

class EmailRead(BaseModel):
    """Schema for reading email data (output)."""
    id: int
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    subject: str
    sender: str
    recipients: str # In the DB, this is a simple text field for now
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    received_at: datetime
    is_read: bool
    is_starred: bool
    is_draft: bool
    sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- 邮件列表响应 ---
class EmailListItem(BaseModel):
    """邮件列表项"""
    id: int
    subject: str
    sender: str
    snippet: str
    received_at: datetime
    is_read: bool
    is_starred: bool
    has_attachments: bool = False
    is_tracked: bool = False
    delivery_status: Optional[str] = None  # pending/sending/sent/delivered/failed


class EmailListData(BaseModel):
    """邮件列表数据"""
    items: List[EmailListItem]
    total: int
    page: int
    limit: int


class EmailListResponse(BaseModel):
    """邮件列表响应"""
    status: str = "success"
    data: EmailListData


# --- 邮件详情响应 ---
class AttachmentInfo(BaseModel):
    """附件信息"""
    id: int
    filename: str
    content_type: str = "application/octet-stream"
    size: int = 0


class TagInfo(BaseModel):
    """标签信息"""
    id: int
    name: str
    color: str


class EmailDetail(BaseModel):
    """邮件详情"""
    id: int
    subject: str
    sender: str
    recipients: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    received_at: datetime
    is_read: bool
    is_starred: bool
    is_tracked: bool = False
    tracking_pixel_id: Optional[str] = None
    tracking_open_url: Optional[str] = None
    delivery_status: Optional[str] = None
    delivery_error: Optional[str] = None
    thread_id: Optional[str] = None
    attachments: List[AttachmentInfo] = []
    tags: List[TagInfo] = []


class ThreadEmailItem(BaseModel):
    """线程中的邮件项"""
    id: int
    subject: str
    sender: str
    snippet: str
    received_at: datetime
    is_read: bool

    class Config:
        from_attributes = True


class ThreadResponse(BaseModel):
    """邮件线程响应"""
    status: str = "success"
    thread_id: Optional[str] = None
    data: List[ThreadEmailItem] = []


class EmailDetailResponse(BaseModel):
    """邮件详情响应"""
    status: str = "success"
    data: EmailDetail


# --- 草稿 Schemas ---
class DraftCreate(BaseModel):
    """创建/更新草稿"""
    to: Optional[str] = Field(default="", max_length=10_000)
    cc: Optional[str] = Field(default="", max_length=10_000)
    subject: Optional[str] = Field(default="", max_length=998)
    body_text: Optional[str] = Field(default="", max_length=2_000_000)
    body_html: Optional[str] = Field(default="", max_length=5_000_000)
    reply_to_id: Optional[int] = None


class DraftResponse(BaseModel):
    """草稿响应"""
    status: str = "success"
    data: dict
