from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from .common import CustomEmailStr

# --- User Schemas ---

# Schema for creating a new user (input)
class UserCreate(BaseModel):
    email: CustomEmailStr  # Use our new, globally effective custom type
    password: str
    display_name: Optional[str] = None
    phone: Optional[str] = None
    redemption_code: str

# Schema for reading user data (output)
class UserRead(BaseModel):
    id: int
    email: CustomEmailStr # Use our custom email type to allow .test domains in responses
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: str
    storage_used_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True # Updated from orm_mode for Pydantic v2

# Schema for the development password reset endpoint
class UserPasswordReset(BaseModel):
    email: CustomEmailStr
    new_password: str