"""
User model for MoonVPN.

This module contains the User model class that represents a user in the system.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    """User model."""
    
    id: Optional[int] = None
    telegram_id: int
    email: EmailStr
    panel_id: int
    username: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True 