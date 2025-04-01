from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
import uuid

from app.db.base import Base


class TransactionType(enum.Enum):
    """Enumeration of transaction types"""
    DEPOSIT = "deposit"  # Money added to wallet
    WITHDRAW = "withdraw"  # Money taken from wallet
    ORDER_PAYMENT = "order_payment"  # Payment for an order
    REFUND = "refund"  # Refund for a canceled order
    REFERRAL_BONUS = "referral_bonus"  # Bonus for referring new users
    ADMIN_ADJUSTMENT = "admin_adjustment"  # Manual adjustment by admin


class TransactionStatus(enum.Enum):
    """Enumeration of transaction statuses"""
    PENDING = "pending"  # Transaction initiated but not completed
    COMPLETED = "completed"  # Transaction successfully completed
    FAILED = "failed"  # Transaction failed
    CANCELED = "canceled"  # Transaction canceled


class Transaction(Base):
    """
    Transaction model for tracking all wallet operations.
    Each transaction affects the user's wallet balance.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # User who owns the wallet
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Associated order (optional)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    
    # Transaction details
    amount = Column(Float, nullable=False)  # Positive for deposits, negative for withdrawals
    balance_after = Column(Float, nullable=False)  # Wallet balance after the transaction
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    
    # Payment details (for deposits)
    payment_method = Column(String(50), nullable=True)  # Card, crypto, etc.
    payment_reference = Column(String(100), nullable=True)  # Reference/tracking number
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Description and notes
    description = Column(Text, nullable=True)
    admin_note = Column(Text, nullable=True)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Admin who processed the transaction
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="transactions")
    order = relationship("Order", back_populates="transactions")
    admin = relationship("User", foreign_keys=[admin_id])
    
    def __repr__(self):
        return f"<Transaction {self.transaction_id} - {self.type.value}: {self.amount}>" 