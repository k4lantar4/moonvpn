"""
Notification model for MoonVPN.

This module contains the Notification model class that represents a system notification.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Notification(BaseModel):
    """Notification model."""
    
    id: Optional[int] = None
    type: str
    user_id: Optional[int] = None
    message: str
    sent_by: Optional[int] = None
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True 