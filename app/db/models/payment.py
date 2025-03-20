"""
SQLAlchemy Payment model for MoonVPN.

This module contains the SQLAlchemy Payment model class that represents a payment in the database.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base

class Payment(Base):
    """SQLAlchemy Payment model."""
    
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    plan_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    authority = Column(String, nullable=False)
    transaction_id = Column(String, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="payments") 