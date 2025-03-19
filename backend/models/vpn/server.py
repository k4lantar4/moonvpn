"""
Server model for VPN servers.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base

class Server(Base):
    """Server model for VPN servers."""
    
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    
    # Server connection details
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    base_path = Column(String(100), nullable=False, default="")
    use_ssl = Column(Boolean, default=True)
    
    # Server configuration
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    location = relationship("Location", back_populates="servers")
    
    # Tracking fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    last_check = Column(Boolean, default=False)
    
    # Resource usage
    cpu = Column(Float, default=0.0)
    memory = Column(Float, default=0.0)
    disk = Column(Float, default=0.0)
    uptime = Column(Integer, default=0)
    load = Column(String(50), default="0 0 0")
    current_load = Column(Float, default=0.0)
    
    # Traffic
    total_upload = Column(Integer, default=0)
    total_download = Column(Integer, default=0)
    
    # Session management
    session_cookies = Column(Text, nullable=True)
    
    # Relationships
    vpn_accounts = relationship("VPNAccount", back_populates="server")
    
    def __repr__(self):
        return f"<Server {self.name} ({self.host})>"
