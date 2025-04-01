from pydantic import BaseModel, Field
from typing import Optional, List
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

# --- Schema for Reading/Response --- #
# Properties to return via API, excluding sensitive data
# Redefine User fully here
class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    role: Optional[Role] = None # Include role information
    # referrals: List['User'] = [] # Add referrals relationship (recursive) # Temporarily removed
    # wallet_balance: float = 0.0 # Maybe add wallet later

    class Config:
        from_attributes = True # Enable ORM mode (formerly orm_mode)

# Update the forward reference
# User.model_rebuild() # Use this in newer Pydantic v2
# In Pydantic v1 style, recursive definitions often work directly or with update_forward_refs
# If using Pydantic v1 and having issues, you might need:
# User.update_forward_refs() # Temporarily removed
