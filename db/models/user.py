"""
مدل User برای مدیریت کاربران
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, String, Column, Enum as SQLEnum, ForeignKey, Text, JSON, DECIMAL
from sqlalchemy.orm import relationship, Mapped, mapped_column

from . import Base
from .plan import Plan
from .receipt_log import ReceiptLog
from .test_account_log import TestAccountLog

if TYPE_CHECKING:
    from .client_account import ClientAccount
    from .order import Order
    from .transaction import Transaction
    from .bank_card import BankCard
    # from .receipt_log import ReceiptLog
    # from .test_account_log import TestAccountLog

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
    balance = Column(DECIMAL(precision=10, scale=2), default=0, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="user")
    test_account_logs: Mapped[List["TestAccountLog"]] = relationship(back_populates="user")
    
    # Relationships related to ReceiptLog
    receipt_logs: Mapped[List["ReceiptLog"]] = relationship(
        "ReceiptLog",
        back_populates="user",
        foreign_keys="ReceiptLog.user_id"
    )
    reviewed_receipts: Mapped[List["ReceiptLog"]] = relationship(
        "ReceiptLog",
        back_populates="admin",
        foreign_keys="ReceiptLog.admin_id"
    )

    # Relationship related to Plan creation
    created_plans: Mapped[List["Plan"]] = relationship(back_populates="created_by")
    
    # Added relationships
    bank_cards: Mapped[List["BankCard"]] = relationship(back_populates="admin_user")
    # Relationship related to NotificationLog
    notification_logs: Mapped[List["NotificationLog"]] = relationship(
        "NotificationLog",
        back_populates="user"
    )
    
    # Add to relationships section
    renewal_logs = relationship("ClientRenewalLog", back_populates="user")
    
    # Wallet relationship
    wallet: Mapped[Optional["Wallet"]] = relationship(back_populates="user", uselist=False)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role})>"
