"""
User schemas for request/response models.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    status: str = "active"

class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)
    confirm_password: str

class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    status: Optional[str] = None

class UserInDB(UserBase):
    """User database schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False
    password_hash: str

    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    """User response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False

    model_config = ConfigDict(from_attributes=True)

class UserProfile(BaseModel):
    """User profile schema."""
    user: User
    points: int = 0
    traffic_used: int = 0
    traffic_limit: int = 0
    subscription_end: Optional[datetime] = None
    referral_code: Optional[str] = None
    referral_count: int = 0

class UserActivity(BaseModel):
    """User activity schema."""
    id: int
    user_id: int
    action: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserList(BaseModel):
    """User list response schema."""
    total: int
    users: List[User]
    page: int
    size: int
    pages: int 