"""
مدل Order برای مدیریت سفارشات VPN
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Integer, String, Column, ForeignKey, DECIMAL, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from . import Base
from .receipt_log import ReceiptLog
from .transaction import Transaction
from .client_account import ClientAccount

if TYPE_CHECKING:
    from .user import User
    from .plan import Plan
    from .discount_code import DiscountCode
    from .receipt_log import ReceiptLog
    from .transaction import Transaction
    from .client_account import ClientAccount


class OrderStatus(str, Enum):
    """وضعیت‌های سفارش"""
    PENDING = "pending"
    PAID = "paid"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class Order(Base):
    """مدل سفارشات VPN در سیستم MoonVPN"""
    
    __tablename__ = "orders"
    
    # فیلدهای اصلی
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    location_name = Column(String(100), nullable=False)
    client_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("client_accounts.id"), nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    final_amount = Column(DECIMAL(10, 2), nullable=True)
    discount_code_id = Column(Integer, ForeignKey("discount_codes.id"), nullable=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    receipt_required = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    fulfilled_at = Column(DateTime, nullable=True)
    
    # ارتباط با سایر مدل‌ها
    user: Mapped["User"] = relationship(back_populates="orders")
    plan: Mapped["Plan"] = relationship(back_populates="orders")
    discount_code: Mapped[Optional["DiscountCode"]] = relationship(back_populates="orders")
    receipt: Mapped[Optional["ReceiptLog"]] = relationship(back_populates="order")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="order")
    client_account: Mapped[Optional["ClientAccount"]] = relationship(
        back_populates="orders", 
        foreign_keys=[client_account_id]
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"
