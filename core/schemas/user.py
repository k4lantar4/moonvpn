"""Pydantic models (Schemas) for Users."""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from decimal import Decimal
from datetime import datetime

# Assuming Role schema is defined elsewhere or create a basic one
# from core.schemas.role import Role
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class Role(RoleBase):
    id: int
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    user_id: int = Field(..., description="Telegram User ID")
    username: Optional[str] = Field(None, max_length=100)
    full_name: str = Field(..., max_length=255)
    balance: Decimal = Field(0.0, decimal_places=2)
    is_active: bool = True
    is_banned: bool = False
    language_code: Optional[str] = Field(None, max_length=10)
    referred_by: Optional[int] = None # Telegram ID of referrer

class UserCreate(UserBase):
    role_id: int # Role must be assigned on creation

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    balance: Optional[Decimal] = Field(None, decimal_places=2)
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    language_code: Optional[str] = Field(None, max_length=10)
    role_id: Optional[int] = None
    referred_by: Optional[int] = None

# Used for updating balance specifically
class UserBalanceUpdate(BaseModel):
    amount: Decimal # Positive for deposit, negative for withdrawal/purchase

class UserInDBBase(UserBase):
    id: int # Internal DB ID
    role_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema for representing a User in API responses, including Role info
class User(UserInDBBase):
    role: Optional[Role] = None 