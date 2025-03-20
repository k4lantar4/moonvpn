"""
Authentication schemas for request/response models.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: datetime

class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: int  # user_id
    exp: datetime
    iat: datetime
    type: str  # access or refresh

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    """Register request schema."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str

class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

class VerifyEmail(BaseModel):
    """Email verification schema."""
    token: str

class RefreshToken(BaseModel):
    """Refresh token request schema."""
    refresh_token: str 