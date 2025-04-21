"""
مدل BankCard برای مدیریت کارت‌های بانکی
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, Column, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped

from . import Base


class RotationPolicy(str, Enum):
    """سیاست چرخش کارت‌ها"""
    MANUAL = "manual"
    INTERVAL = "interval"
    LOAD_BALANCE = "load_balance"


class BankCard(Base):
    """مدل کارت‌های بانکی برای پرداخت"""
    
    __tablename__ = "bank_cards"
    
    # فیلدهای اصلی
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    card_number = Column(String(16), nullable=False)
    holder_name = Column(String(255), nullable=False)
    bank_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    rotation_policy = Column(SQLEnum(RotationPolicy), default=RotationPolicy.MANUAL, nullable=False)
    rotation_interval_minutes = Column(Integer, nullable=True)
    telegram_channel_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    admin_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    admin_user = relationship("User", backref="bank_cards")
    receipt_logs: Mapped[List["ReceiptLog"]] = relationship(back_populates="bank_card")
    
    def __repr__(self) -> str:
        return f"<BankCard(id={self.id}, card_number=****{self.card_number[-4:]}, bank={self.bank_name})>" 