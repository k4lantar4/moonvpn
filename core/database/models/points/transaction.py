"""
PointsTransaction model for managing points transactions and history.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class TransactionType(str, enum.Enum):
    """Transaction type enumeration."""
    EARN = "earn"
    SPEND = "spend"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"

class TransactionStatus(str, enum.Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PointsTransaction(BaseModel):
    """
    PointsTransaction model for managing points transactions.
    
    Attributes:
        points_account_id: Reference to points account
        user_id: Reference to user
        type: Transaction type
        status: Transaction status
        amount: Transaction amount
        balance_before: Balance before transaction
        balance_after: Balance after transaction
        description: Transaction description
        metadata: Additional transaction data
    """
    
    # Transaction identification
    points_account_id: Mapped[int] = mapped_column(ForeignKey("user_points.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), nullable=False)
    
    # Transaction details
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Additional data
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    points_account: Mapped["UserPoints"] = relationship(back_populates="transactions")
    user: Mapped["User"] = relationship(back_populates="transactions")
    
    def __repr__(self) -> str:
        """String representation of the points transaction."""
        return f"<PointsTransaction(type={self.type}, amount={self.amount})>" 