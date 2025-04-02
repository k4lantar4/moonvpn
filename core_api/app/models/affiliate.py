from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, ForeignKey, func
from sqlalchemy.orm import relationship
from enum import Enum

from app.db.base import Base


class CommissionStatus(str, Enum):
    """Enumeration of commission statuses"""
    PENDING = "pending"  # Commission is pending (order not yet paid)
    APPROVED = "approved"  # Commission is approved (order paid, awaiting payout)
    PAID = "paid"  # Commission has been paid to the affiliate
    REJECTED = "rejected"  # Commission was rejected (e.g., fraudulent order)


class CommissionType(str, Enum):
    """Enumeration of commission types"""
    ORDER = "order"  # Commission from an order
    SIGNUP = "signup"  # Commission from a user signup
    BONUS = "bonus"  # Special bonus commission


class WithdrawalStatus(str, Enum):
    """Enumeration of withdrawal statuses"""
    PENDING = "pending"  # Withdrawal is pending admin approval
    APPROVED = "approved"  # Withdrawal is approved but not yet processed
    COMPLETED = "completed"  # Withdrawal has been processed
    REJECTED = "rejected"  # Withdrawal was rejected


class AffiliateCommission(Base):
    """
    Model for tracking affiliate commissions earned by users.
    """
    __tablename__ = "affiliate_commissions"

    id = Column(Integer, primary_key=True)
    
    # User who earned the commission (the referrer)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # User who was referred (optional, may be null for bonus commissions)
    referrer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Associated order (optional, may be null for signup commissions)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Commission amount
    amount = Column(DECIMAL(10, 2), nullable=False)
    
    # Percentage used to calculate commission
    percentage = Column(DECIMAL(5, 2), nullable=False)
    
    # Commission status (pending, approved, paid, rejected)
    status = Column(String(20), nullable=False, default=CommissionStatus.PENDING.value)
    
    # Commission type (order, signup, bonus)
    commission_type = Column(String(20), nullable=False, default=CommissionType.ORDER.value)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional description
    description = Column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="commissions")
    referred_user = relationship("User", foreign_keys=[referrer_id])
    order = relationship("Order", back_populates="commissions")
    
    def __repr__(self):
        return f"<AffiliateCommission(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"


class AffiliateSettings(Base):
    """
    Model for storing global affiliate program settings.
    """
    __tablename__ = "affiliate_settings"

    id = Column(Integer, primary_key=True)
    
    # Default commission percentage (e.g., 10%)
    commission_percentage = Column(DECIMAL(5, 2), nullable=False, default=10.00)
    
    # Minimum amount for withdrawal
    min_withdrawal_amount = Column(DECIMAL(10, 2), nullable=False, default=100000.00)
    
    # Length of generated affiliate codes
    code_length = Column(Integer, nullable=False, default=8)
    
    # Whether the affiliate program is enabled system-wide
    is_enabled = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AffiliateSettings(id={self.id}, commission_percentage={self.commission_percentage}, is_enabled={self.is_enabled})>"


class AffiliateWithdrawal(Base):
    """
    Model for tracking affiliate withdrawal requests.
    """
    __tablename__ = "affiliate_withdrawals"

    id = Column(Integer, primary_key=True)
    
    # User requesting the withdrawal
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Associated transaction (once processed)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    
    # Withdrawal amount
    amount = Column(DECIMAL(10, 2), nullable=False)
    
    # Withdrawal status
    status = Column(String(20), nullable=False, default=WithdrawalStatus.PENDING.value)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Admin who processed the withdrawal
    processed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Optional note
    note = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="withdrawals")
    processor = relationship("User", foreign_keys=[processed_by])
    transaction = relationship("Transaction")
    
    def __repr__(self):
        return f"<AffiliateWithdrawal(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>" 