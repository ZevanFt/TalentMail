from pydantic import BaseModel, EmailStr, field_serializer, field_validator
from typing import Optional
from datetime import datetime, date
from .common import CustomEmailStr

# --- User Schemas ---

# Schema for creating a new user (input)
class UserCreate(BaseModel):
    email: CustomEmailStr  # Use our new, globally effective custom type
    password: str
    display_name: Optional[str] = None
    phone: Optional[str] = None
    invite_code: str  # 邀请码，必填

# Schema for reading user data (output)
class UserRead(BaseModel):
    id: int
    email: CustomEmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: str
    storage_used_bytes: int
    role: str  # 用户角色
    pool_enabled: bool = False
    recovery_email: Optional[str] = None  # 安全辅助邮箱
    # 通知设置
    enable_desktop_notifications: bool = True
    enable_sound_notifications: bool = True
    enable_pool_notifications: bool = False
    # 自动回复
    auto_reply_enabled: bool = False
    auto_reply_start_date: Optional[date] = None
    auto_reply_end_date: Optional[date] = None
    auto_reply_message: Optional[str] = None
    # 隐私设置
    spam_filter_level: str = "standard"
    block_external_images: bool = True
    created_at: datetime

    class Config:
        from_attributes = True
    
    @field_validator('spam_filter_level', mode='before')
    @classmethod
    def default_spam_filter_level(cls, v):
        return v if v is not None else "standard"
    
    @field_validator('block_external_images', mode='before')
    @classmethod
    def default_block_external_images(cls, v):
        return v if v is not None else True
    
    @field_serializer('auto_reply_start_date', 'auto_reply_end_date')
    def serialize_date(self, v: Optional[date]) -> Optional[str]:
        return v.isoformat() if v else None

# Schema for the development password reset endpoint
class UserPasswordReset(BaseModel):
    email: CustomEmailStr
    new_password: str


# Schema for updating user profile
class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: Optional[str] = None
    # 通知设置
    enable_desktop_notifications: Optional[bool] = None
    enable_sound_notifications: Optional[bool] = None
    enable_pool_notifications: Optional[bool] = None
    # 自动回复
    auto_reply_enabled: Optional[bool] = None
    auto_reply_start_date: Optional[str] = None
    auto_reply_end_date: Optional[str] = None
    auto_reply_message: Optional[str] = None
    # 隐私设置
    spam_filter_level: Optional[str] = None
    block_external_images: Optional[bool] = None


# Schema for changing password
class PasswordChange(BaseModel):
    current_password: str
    new_password: str