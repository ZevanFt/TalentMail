from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from .common import CustomEmailStr

# --- Email Schemas ---

class EmailRecipient(BaseModel):
    """Represents a single email recipient."""
    name: Optional[str] = None
    email: CustomEmailStr

class EmailCreate(BaseModel):
    """Schema for creating/sending a new email (input)."""
    to: List[EmailRecipient]
    cc: Optional[List[EmailRecipient]] = []
    bcc: Optional[List[EmailRecipient]] = []
    subject: str = ""
    body_html: str = ""
    body_text: Optional[str] = None
    reply_to_id: Optional[int] = None  # 回复的邮件ID
    is_tracked: bool = False  # 是否启用追踪

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
    size_bytes: int = 0


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
    delivery_status: Optional[str] = None
    delivery_error: Optional[str] = None
    attachments: List[AttachmentInfo] = []


class EmailDetailResponse(BaseModel):
    """邮件详情响应"""
    status: str = "success"
    data: EmailDetail


# --- 草稿 Schemas ---
class DraftCreate(BaseModel):
    """创建/更新草稿"""
    to: Optional[str] = ""
    cc: Optional[str] = ""
    subject: Optional[str] = ""
    body_text: Optional[str] = ""
    body_html: Optional[str] = ""
    reply_to_id: Optional[int] = None


class DraftResponse(BaseModel):
    """草稿响应"""
    status: str = "success"
    data: dict