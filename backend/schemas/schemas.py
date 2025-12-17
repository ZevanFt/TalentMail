from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime

from .common import CustomEmailStr

# --- Attachment Schemas ---
class AttachmentRead(BaseModel):
    id: int
    filename: str
    content_type: str
    size_bytes: int

    class Config:
        from_attributes = True


# --- Email Schemas ---

# Schema for creating/sending an email
class EmailCreate(BaseModel):
    to: list[CustomEmailStr]
    cc: Optional[list[CustomEmailStr]] = None
    bcc: Optional[list[CustomEmailStr]] = None
    subject: str
    body_html: str
    action: str  # "send" or "draft"


# Schema for items in an email list
class EmailListItem(BaseModel):
    id: int
    subject: str
    sender: str
    is_read: bool
    is_starred: bool
    received_at: datetime
    has_attachments: bool = False # Default to false, will be computed

    class Config:
        from_attributes = True


# Schema for reading a single email's full details
class EmailRead(EmailListItem):
    recipients: list[str]
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    attachments: list[AttachmentRead] = []

    class Config:
        from_attributes = True


# Schema for paginated email list response
class EmailListResponse(BaseModel):
    items: list[EmailListItem]
    total: int
    page: int
    limit: int


# Schema for bulk-updating emails
class EmailAction(BaseModel):
    move_to_folder: Optional[int] = None
    mark_as_read: Optional[bool] = None
    toggle_star: Optional[bool] = None


class EmailUpdate(BaseModel):
    email_ids: list[int]
    action: EmailAction


# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    sub: str # 'sub' is the standard JWT claim for the subject (user identifier)


# --- Folder Schemas ---
class FolderBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class FolderCreate(FolderBase):
    pass


class FolderUpdate(FolderBase):
    pass


class FolderRead(FolderBase):
    id: int
    role: str
    unread_count: int = 0 # Default to 0, will be computed

    class Config:
        from_attributes = True


# --- Tag Schemas ---
class TagBase(BaseModel):
    name: str
    color: str


class TagCreate(TagBase):
    pass


class TagUpdate(TagBase):
    pass


class TagRead(TagBase):
    id: int

    class Config:
        from_attributes = True


# --- Settings Schemas ---

# 5.1 Profile
class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


# 5.2 Security
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


# 5.3 Domains
class DomainVerificationRecords(BaseModel):
    dkim: dict[str, str]
    spf: dict[str, str]


class DomainRead(BaseModel):
    id: int
    domain_name: str
    is_verified: bool
    created_at: datetime
    verification_records: Optional[DomainVerificationRecords] = None

    class Config:
        from_attributes = True


class DomainCreate(BaseModel):
    domain_name: str


# 5.4 Aliases
class AliasBase(BaseModel):
    display_name: Optional[str] = None


class AliasCreate(AliasBase):
    local_part: str
    domain_id: int


class AliasUpdate(AliasBase):
    is_default: Optional[bool] = None


class AliasRead(AliasBase):
    id: int
    email: str
    domain_id: int
    is_default: bool

    class Config:
        from_attributes = True


# 5.5 Signatures
class SignatureBase(BaseModel):
    name: str
    content_html: str


class SignatureCreate(SignatureBase):
    pass


class SignatureUpdate(SignatureBase):
    is_default: Optional[bool] = None


class SignatureRead(SignatureBase):
    id: int
    is_default: bool

    class Config:
        from_attributes = True


# 5.6 Filters
class FilterCondition(BaseModel):
    field: str
    operator: str
    value: Any


class FilterAction(BaseModel):
    action: str
    value: Any


class FilterBase(BaseModel):
    name: str
    conditions: list[FilterCondition]
    actions: list[FilterAction]
    is_active: bool = True


class FilterCreate(FilterBase):
    pass


class FilterUpdate(FilterBase):
    pass


class FilterRead(FilterBase):
    id: int

    class Config:
        from_attributes = True
