"""
Server model for MoonVPN.

This module contains the Server model class that represents a VPN server.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Server(BaseModel):
    """Server model."""
    
    id: Optional[int] = None
    name: str
    host: str
    port: int
    protocol: str
    status: str
    load: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True 