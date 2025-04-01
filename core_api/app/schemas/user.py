from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

# Import related schemas if needed (e.g., Role)
from .role import Role # Assuming role.py exists and defines Role schema

# Forward declaration for recursive model - REMOVED
# class User(BaseModel): # Define User early for type hinting referrals
#     pass

# --- Base Schema --- #
class UserBase(BaseModel):
    telegram_id: int = Field(..., description="Unique Telegram User ID")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = Field(None, max_length=10)
    is_active: bool = True
    is_superuser: bool = False
    # Note: We don't include sensitive fields like hashed_password here

# --- Schema for Creation --- #
# Fields required when creating a new user via API
class UserCreate(UserBase):
    pass # Inherits all fields from UserBase

# --- Schema for Updating --- #
# Fields that are allowed to be updated via API
# Make all fields optional for updates
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role_id: Optional[int] = None # Allow updating the assigned role

# Additional schema for admin users to update users
class AdminUserUpdate(UserUpdate):
    """Additional fields that only admins can update"""
    is_superuser: Optional[bool] = None

# Schema for updating user's password
class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

# --- Schema for Reading/Response --- #
# Properties to return via API, excluding sensitive data
# Redefine User fully here
class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    role: Optional["Role"] = None # Use string type hint to avoid circular imports
    # referrals: List["User"] = [] # Add referrals relationship (recursive) if needed later
    # wallet_balance: float = 0.0 # Maybe add wallet later

    model_config = ConfigDict(
        from_attributes=True # Enable creating models from ORM objects
    )

# Schema for database representation (including any sensitive fields)
class UserInDB(User):
    hashed_password: Optional[str] = None

# Additional schemas for specific API responses
class UserList(BaseModel):
    """List of users for API response"""
    items: List[User] = []
    total: int = 0

class UserDetail(User):
    """Detailed user information"""
    pass

class UserIds(BaseModel):
    """Simple model for user IDs list"""
    ids: List[int] = []

class UserWithRole(User):
    """User model with expanded role information"""
    role: Optional["Role"] = None

# Update the forward reference
# User.model_rebuild() # Use this in newer Pydantic v2
# In Pydantic v1 style, recursive definitions often work directly or with update_forward_refs
# If using Pydantic v1 and having issues, you might need:
# User.update_forward_refs() # Temporarily removed
