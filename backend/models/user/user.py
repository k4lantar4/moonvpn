"""
User model.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.orm import relationship

from app.db.base import Base

class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Telegram details
    telegram_id = Column(Integer, nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    language_code = Column(String(10), default="en")
    
    # User details
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    
    # Points system
    points = Column(Integer, default=0)
    
    # Tracking fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Wallet
    balance = Column(Float, default=0.0)
    
    # Relationships
    vpn_accounts = relationship("VPNAccount", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.username or 'No username'})>"
