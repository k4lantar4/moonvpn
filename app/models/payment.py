"""
Payment model for MoonVPN.

This module contains the Payment model class that represents a payment transaction.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Payment(BaseModel):
    """Payment model."""
    
    id: Optional[int] = None
    telegram_id: int
    plan_id: str
    amount: int
    duration: int
    authority: str
    transaction_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True 