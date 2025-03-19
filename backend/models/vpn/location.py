"""
Location model for VPN server locations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base

class Location(Base):
    """Location model for VPN server locations."""
    
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country_code = Column(String(2), nullable=False)
    flag_emoji = Column(String(10), nullable=True)
    description = Column(String(255), nullable=True)
    
    # Tracking fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    servers = relationship("Server", back_populates="location")
    
    def __repr__(self):
        return f"<Location {self.name} ({self.country_code})>"
