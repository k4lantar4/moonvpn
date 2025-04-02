from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime
from decimal import Decimal
from pydantic import EmailStr

# Import related schemas if needed (e.g., Role)
from .role import Role # Assuming role.py exists and defines Role schema

# Forward declaration for recursive model - REMOVED
# class User(BaseModel): # Define User early for type hinting referrals
#     pass

# --- Base Schema --- #
class UserBase(BaseModel):
    telegram_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    # New affiliate fields
    affiliate_code: Optional[str] = None
    affiliate_balance: Optional[Decimal] = Field(None, description="User's affiliate earnings balance")
    is_affiliate_enabled: Optional[bool] = Field(True, description="Whether the user can participate in the affiliate program")

# --- Schema for Creation --- #
# Fields required when creating a new user via API
class UserCreate(UserBase):
    telegram_id: str
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[int] = 1  # Default to User role
    affiliate_code: Optional[str] = None

# --- Schema for Updating --- #
# Fields that are allowed to be updated via API
# Make all fields optional for updates
class UserUpdate(UserBase):
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None

# Additional schema for admin users to update users
class AdminUserUpdate(UserUpdate):
    telegram_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    affiliate_balance: Optional[Decimal] = None
    is_affiliate_enabled: Optional[bool] = None

# Schema for updating user's password
class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

# --- Schema for Reading/Response --- #
# Properties to return via API, excluding sensitive data
# Redefine User fully here
class User(UserBase):
    id: int
    email: Optional[EmailStr] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    role: Optional[Role] = None
    role_id: Optional[int] = None
    # Affiliate stats
    referred_users_count: Optional[int] = Field(0, description="Number of users referred by this user")
    total_commissions: Optional[Decimal] = Field(Decimal('0'), description="Total earnings from affiliate commissions")
    pending_commissions: Optional[Decimal] = Field(Decimal('0'), description="Pending earnings from affiliate commissions")
    
    model_config = ConfigDict(
        from_attributes=True, # Enable creating models from ORM objects
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }
    )

# Schema for database representation (including any sensitive fields)
class UserInDB(User):
    hashed_password: Optional[str] = None

# Additional schemas for specific API responses
class UserList(BaseModel):
    """List of users for API response"""
    users: List[User]
    total: int

class UserDetail(User):
    """Detailed user information"""
    total_orders: Optional[int] = None
    total_spent: Optional[Decimal] = None
    latest_order_date: Optional[datetime] = None
    # Affiliate data
    referrer: Optional[Dict[str, Any]] = None  # Information about the user who referred this user

class UserIds(BaseModel):
    """Simple model for user IDs list"""
    ids: List[int]

class UserWithRole(User):
    """User model with expanded role information"""
    role: Optional[Role] = None

# Update the forward reference
# User.model_rebuild() # Use this in newer Pydantic v2
# In Pydantic v1 style, recursive definitions often work directly or with update_forward_refs
# If using Pydantic v1 and having issues, you might need:
# User.update_forward_refs() # Temporarily removed
