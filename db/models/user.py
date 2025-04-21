"""
مدل User برای مدیریت کاربران
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, String, Column, Enum as SQLEnum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship, Mapped

from . import Base


class UserRole(str, Enum):
    """نقش‌های کاربران در سیستم"""
    USER = "user"
    ADMIN = "admin"
    SELLER = "seller"


class UserStatus(str, Enum):
    """وضعیت‌های کاربر"""
    ACTIVE = "active"
    BLOCKED = "blocked"


class User(Base):
    """مدل کاربران سیستم MoonVPN"""
    
    __tablename__ = "users"
    
    # فیلدهای اصلی
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    settings = Column(JSON, nullable=True)
    
    # ارتباط با سایر مدل‌ها
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="user")
    test_account_logs: Mapped[List["TestAccountLog"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role})>"
