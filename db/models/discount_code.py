"""
مدل DiscountCode برای مدیریت کدهای تخفیف
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Column, ForeignKey, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped

from . import Base


class DiscountType(str, Enum):
    """انواع تخفیف"""
    PERCENT = "percent"
    FIXED = "fixed"


class DiscountCode(Base):
    """مدل کدهای تخفیف در سیستم MoonVPN"""
    
    __tablename__ = "discount_codes"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    type = Column(SQLEnum(DiscountType), nullable=False)
    value = Column(DECIMAL(10, 2), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    usage_limit = Column(Integer, nullable=False)
    used_count = Column(Integer, default=0, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    max_discount = Column(DECIMAL(10, 2), nullable=True)
    min_order = Column(DECIMAL(10, 2), nullable=True)
    
    # ارتباط با سایر مدل‌ها
    orders: Mapped[List["Order"]] = relationship(back_populates="discount_code")
    
    def __repr__(self) -> str:
        return f"<DiscountCode(id={self.id}, code={self.code}, type={self.type}, value={self.value})>"
