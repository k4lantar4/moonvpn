"""
مدل Wallet برای مدیریت کیف پول کاربران در سیستم MoonVPN
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Column, DECIMAL
from sqlalchemy.orm import relationship, Mapped

from . import Base

if TYPE_CHECKING:
    from .user import User
    from .transaction import Transaction


class Wallet(Base):
    """مدل کیف پول کاربران"""
    
    __tablename__ = "wallets"
    
    # فیلدهای اصلی
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    balance = Column(DECIMAL(precision=10, scale=2), default=0, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    user: Mapped["User"] = relationship(back_populates="wallet")
    
    def __repr__(self) -> str:
        return f"<Wallet(id={self.id}, user_id={self.user_id}, balance={self.balance})>" 