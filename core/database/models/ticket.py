"""
Ticket model for MoonVPN.

This module contains the Ticket model class that represents a support ticket.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Ticket(BaseModel):
    """Ticket model."""
    
    id: Optional[int] = None
    user_id: int
    message: str
    status: str
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True 