"""
Payment model for managing user payments and transactions.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""
    CRYPTO = "crypto"
    CARD = "card"
    BANK = "bank"
    WALLET = "wallet"

class Payment(BaseModel):
    """
    Payment model for managing user payments.
    
    Attributes:
        user_id: Reference to user
        amount: Payment amount
        currency: Payment currency
        status: Payment status
        method: Payment method
        transaction_id: External transaction ID
        payment_date: Payment completion date
        description: Payment description
        metadata: Additional payment data
    """
    
    # Payment identification
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    
    # Transaction details
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="payments")
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the payment."""
        return f"<Payment(amount={self.amount} {self.currency}, status={self.status})>" 