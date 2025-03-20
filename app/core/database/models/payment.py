"""
Payment models for MoonVPN.

This module contains all the SQLAlchemy models for payment-related data
including transactions, wallets, and orders.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database.base import Base
from app.core.database.models.user import User

class PaymentMethod(str, Enum):
    """Supported payment methods."""
    WALLET = "wallet"
    CARD = "card"
    BANK = "bank"
    ZARINPAL = "zarinpal"

class TransactionStatus(str, Enum):
    """Transaction statuses."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class TransactionType(str, Enum):
    """Transaction types."""
    PURCHASE = "purchase"
    DEPOSIT = "deposit"
    REFUND = "refund"
    WITHDRAWAL = "withdrawal"

class Transaction(Base):
    """Model for payment transactions."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(TransactionStatus), nullable=False)
    order_id = Column(String, nullable=True)
    authority = Column(String, nullable=True)
    ref_id = Column(String, nullable=True)
    transaction_data = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    order = relationship("Order", back_populates="transactions", uselist=False)

    def __repr__(self):
        return f"<Transaction {self.id}>"

class Wallet(Base):
    """Model for user wallets."""
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    balance = Column(Float, nullable=False, default=0.0)
    currency = Column(String, nullable=False, default="USD")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="wallet")

    def __repr__(self):
        return f"<Wallet {self.id}>"

class Order(Base):
    """Model for payment orders."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="orders")
    plan = relationship("Plan", back_populates="orders")
    transactions = relationship("Transaction", back_populates="order")

    def __repr__(self):
        return f"<Order {self.id}>" 