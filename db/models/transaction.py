"""
مدل Transaction برای مدیریت تراکنش‌های مالی
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Column, ForeignKey, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from . import Base


class TransactionType(str, Enum):
    """انواع تراکنش‌های مالی"""
    DEPOSIT = "DEPOSIT"  # For wallet top-up
    # PAYMENT = "PAYMENT"  # Alias for DEPOSIT (for compatibility)
    PURCHASE = "PURCHASE"  # For buying plans
    REFUND = "REFUND"  # For refunds


class TransactionStatus(str, Enum):
    """وضعیت‌های تراکنش"""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Transaction(Base):
    """مدل تراکنش‌های مالی در سیستم MoonVPN"""
    
    __tablename__ = "transactions"
    
    # فیلدهای اصلی
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    related_order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=True, index=True) # Nullable if transaction isn't always linked to an order
    amount = Column(DECIMAL(10, 2), nullable=False) # Assuming 2 decimal places for currency
    type = Column(SQLEnum(TransactionType), nullable=False, default=TransactionType.DEPOSIT)
    status = Column(SQLEnum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    gateway = Column(String(100), nullable=True) # e.g., bank_transfer, wallet
    reference = Column(String(255), nullable=True) # External reference ID
    tracking_code = Column(String(50), unique=True, nullable=True) # Internal tracking code
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    user: Mapped["User"] = relationship(back_populates="transactions")
    order: Mapped[Optional["Order"]] = relationship(back_populates="transactions", foreign_keys=[related_order_id])
    receipt_logs: Mapped[List["ReceiptLog"]] = relationship(back_populates="transaction")
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, user_id={self.user_id}, related_order_id={self.related_order_id}, amount={self.amount}, status='{self.status.value}')>"
