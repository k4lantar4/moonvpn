"""
Transaction model for tracking payment transactions and their status.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class TransactionStatus(str, enum.Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class TransactionType(str, enum.Enum):
    """Transaction type enumeration."""
    PURCHASE = "purchase"
    REFUND = "refund"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

class Transaction(BaseModel):
    """
    Transaction model for tracking payment transactions.
    
    Attributes:
        payment_id: Reference to payment
        amount: Transaction amount
        currency: Transaction currency
        status: Transaction status
        type: Transaction type
        external_id: External transaction ID
        completed_at: Transaction completion timestamp
        description: Transaction description
        metadata: Additional transaction data
    """
    
    # Transaction identification
    payment_id: Mapped[int] = mapped_column(ForeignKey("payment.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    
    # Transaction details
    external_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    payment: Mapped["Payment"] = relationship(back_populates="transactions")
    
    def __repr__(self) -> str:
        """String representation of the transaction."""
        return f"<Transaction(amount={self.amount} {self.currency}, status={self.status})>" 