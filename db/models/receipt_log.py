"""
مدل ReceiptLog برای مدیریت رسیدهای پرداخت
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, Column, Enum as SQLEnum, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship

from . import Base


class ReceiptStatus(str, Enum):
    """وضعیت‌های رسید پرداخت"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ReceiptLog(Base):
    """مدل رسیدهای پرداخت کارت به کارت"""
    
    __tablename__ = "receipt_log"
    
    # فیلدهای اصلی
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    text_reference = Column(Text, nullable=True)
    photo_file_id = Column(String(255), nullable=True)
    status = Column(SQLEnum(ReceiptStatus), default=ReceiptStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    is_flagged = Column(Boolean, default=False, nullable=False)
    tracking_code = Column(String(50), unique=True, nullable=False)
    auto_detected_amount = Column(DECIMAL(10, 2), nullable=True)
    auto_validated = Column(Boolean, default=False, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)
    
    # ارتباط با سایر مدل‌ها
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="receipt_logs")
    
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=True)
    order = relationship("Order", back_populates="receipt")
    
    transaction_id = Column(BigInteger, ForeignKey("transactions.id"), nullable=True)
    transaction = relationship("Transaction", back_populates="receipt_logs")
    
    card_id = Column(BigInteger, ForeignKey("bank_cards.id"), nullable=False)
    bank_card = relationship("BankCard", back_populates="receipt_logs")
    
    admin_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    admin = relationship("User", foreign_keys=[admin_id], backref="reviewed_receipts")
    
    def __repr__(self) -> str:
        return f"<ReceiptLog(id={self.id}, amount={self.amount}, status={self.status})>" 