from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    telegram_username = Column(String(100), nullable=True)
    phone_number = Column(String(20), index=True, nullable=True)
    first_name = Column(String(100), nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    wallet_balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    is_iranian_verified = Column(Boolean, default=False)
    joined_channel = Column(Boolean, default=False)
    free_trial_used = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    referrer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Affiliate system fields
    affiliate_code = Column(String(20), unique=True, nullable=True, index=True)
    affiliate_balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    is_affiliate_enabled = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship (Many-to-One: User to Role)
    role = relationship("Role", back_populates="users")
    
    # Relationship (One-to-Many: User to Orders)
    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    
    # Relationship (One-to-Many: User to Transactions)
    transactions = relationship("Transaction", back_populates="user", foreign_keys="Transaction.user_id")
    
    # Admin-created transactions
    created_transactions = relationship("Transaction", back_populates="admin", foreign_keys="Transaction.admin_id")
    
    # Relationship (One-to-Many: User to Subscriptions)
    subscriptions = relationship("Subscription", back_populates="user", foreign_keys="Subscription.user_id")
    
    # Relationship (One-to-Many: User to BankCards)
    bank_cards = relationship("BankCard", back_populates="user", foreign_keys="BankCard.user_id")
    
    # Roles through association table
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    # Referral relationships
    referrer = relationship("User", remote_side=[id], backref="referred_users", foreign_keys=[referrer_user_id])
    
    # Affiliate system relationships
    commissions = relationship("AffiliateCommission", back_populates="user", foreign_keys="AffiliateCommission.user_id")
    withdrawals = relationship("AffiliateWithdrawal", back_populates="user", foreign_keys="AffiliateWithdrawal.user_id")

    # Payment admin relationships
    payment_admin_assignments = relationship("PaymentAdminAssignment", back_populates="user")
    payment_admin_metrics = relationship("PaymentAdminMetrics", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role_id={self.role_id})>" 