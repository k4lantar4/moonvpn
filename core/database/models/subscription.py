"""
Subscription model for MoonVPN.

This module contains the Subscription model class that represents a user's VPN subscription.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Subscription(BaseModel):
    """Subscription model."""
    
    id: Optional[int] = None
    user_id: int
    plan_id: str
    status: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True 