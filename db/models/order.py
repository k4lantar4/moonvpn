"""
مدل Order برای مدیریت سفارشات VPN
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Column, ForeignKey, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped

from . import Base


class OrderStatus(str, Enum):
    """وضعیت‌های سفارش"""
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    DONE = "done"


class Order(Base):
    """مدل سفارشات VPN در سیستم MoonVPN"""
    
    __tablename__ = "orders"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    discount_code_id = Column(Integer, ForeignKey("discount_codes.id"), nullable=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # ارتباط با سایر مدل‌ها
    user: Mapped["User"] = relationship(back_populates="orders")
    plan: Mapped["Plan"] = relationship(back_populates="orders")
    discount_code: Mapped[Optional["DiscountCode"]] = relationship(back_populates="orders")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="order")
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"
