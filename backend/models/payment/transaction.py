"""
Transaction model.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base

class TransactionType(enum.Enum):
    """Transaction type enum."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PURCHASE = "purchase"
    REFUND = "refund"
    ADMIN = "admin"
    REFERRAL = "referral"

class TransactionStatus(enum.Enum):
    """Transaction status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Transaction(Base):
    """Transaction model."""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="transactions")
    
    # Transaction details
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    
    # Reference information
    reference_id = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    
    # Payment method
    payment_method = Column(String(50), nullable=True)
    
    # Tracking fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Transaction {self.id} ({self.type.value}, {self.status.value})>"
