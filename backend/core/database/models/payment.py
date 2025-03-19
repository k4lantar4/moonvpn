"""Payment models for managing transactions and payment methods."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class PaymentStatus(str, enum.Enum):
    """Payment status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    """Payment method types."""
    CARD = "card"
    ZARINPAL = "zarinpal"
    CRYPTO = "crypto"
    WALLET = "wallet"

class Payment(Base):
    """Payment model for managing transactions."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Payment information
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod),
        nullable=False
    )
    
    # Transaction details
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="payment",
        lazy="selectin"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the payment."""
        return f"<Payment {self.id} {self.amount} {self.currency}>"
    
    def complete(self, transaction_id: str, payment_data: Optional[dict] = None) -> None:
        """Mark payment as completed."""
        self.status = PaymentStatus.COMPLETED
        self.transaction_id = transaction_id
        self.payment_data = payment_data
        self.completed_at = datetime.now(self.created_at.tzinfo)
    
    def fail(self, payment_data: Optional[dict] = None) -> None:
        """Mark payment as failed."""
        self.status = PaymentStatus.FAILED
        self.payment_data = payment_data
        self.failed_at = datetime.now(self.created_at.tzinfo)
    
    def refund(self, payment_data: Optional[dict] = None) -> None:
        """Mark payment as refunded."""
        self.status = PaymentStatus.REFUNDED
        self.payment_data = payment_data
        self.refunded_at = datetime.now(self.created_at.tzinfo)

class CardPayment(Base):
    """Card payment model for managing card transactions."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Payment relationship
    payment_id: Mapped[int] = mapped_column(ForeignKey("payment.id"), nullable=False)
    
    # Card information
    card_number: Mapped[str] = mapped_column(String(16), nullable=False)
    card_holder: Mapped[str] = mapped_column(String(100), nullable=False)
    expiry_month: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cvv: Mapped[str] = mapped_column(String(4), nullable=False)
    
    # Relationships
    payment: Mapped["Payment"] = relationship("Payment", back_populates="card_payment")
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the card payment."""
        return f"<CardPayment {self.card_holder} {self.card_number[-4:]}>"

class ZarinpalPayment(Base):
    """Zarinpal payment model for managing Zarinpal transactions."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Payment relationship
    payment_id: Mapped[int] = mapped_column(ForeignKey("payment.id"), nullable=False)
    
    # Zarinpal information
    authority: Mapped[str] = mapped_column(String(100), nullable=False)
    ref_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    payment: Mapped["Payment"] = relationship("Payment", back_populates="zarinpal_payment")
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the Zarinpal payment."""
        return f"<ZarinpalPayment {self.authority}>" 