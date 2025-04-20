"""
مدل User برای مدیریت کاربران
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, Column, Enum as SQLEnum, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship, Mapped

from . import Base


class UserRole(str, Enum):
    """نقش‌های کاربران در سیستم"""
    USER = "user"
    ADMIN = "admin"
    RESELLER = "reseller"


class User(Base):
    """مدل کاربران سیستم MoonVPN"""
    
    __tablename__ = "users"
    
    # فیلدهای اصلی
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    balance = Column(DECIMAL(10, 2), default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Boolean, default=True, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="user")
    test_account_logs: Mapped[List["TestAccountLog"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role})>"
