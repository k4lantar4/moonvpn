"""
VPN Account model.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.db.base import Base

class VPNAccount(Base):
    """VPN Account model for user subscriptions."""
    
    __tablename__ = "vpn_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="vpn_accounts")
    
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    server = relationship("Server", back_populates="vpn_accounts")
    
    # Account details
    email = Column(String(255), nullable=False, unique=True)
    uuid = Column(String(100), nullable=False)
    inbound_id = Column(Integer, nullable=False)
    
    # Subscription details
    traffic_limit = Column(Integer, default=0)  # In GB, 0 means unlimited
    expire_days = Column(Integer, default=30)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_trial = Column(Boolean, default=False)
    
    # Usage metrics
    used_traffic = Column(Float, default=0.0)  # In GB
    last_used = Column(DateTime, nullable=True)
    
    # Tracking fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))
    
    def __repr__(self):
        return f"<VPNAccount {self.email} (User ID: {self.user_id})>"
    
    @property
    def traffic_usage_percent(self) -> float:
        """Get traffic usage as percentage."""
        if self.traffic_limit <= 0:
            return 0.0
        return min(100.0, (self.used_traffic / self.traffic_limit) * 100)
    
    @property
    def days_remaining(self) -> int:
        """Get remaining days until expiration."""
        if not self.expires_at:
            return 0
        
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def expired(self) -> bool:
        """Check if account is expired."""
        return self.days_remaining <= 0
