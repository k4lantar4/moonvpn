"""
مدل DiscountCode برای مدیریت کدهای تخفیف
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Column, ForeignKey, DECIMAL, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship, Mapped

from . import Base


class DiscountCode(Base):
    """مدل کدهای تخفیف در سیستم MoonVPN"""
    
    __tablename__ = "discount_codes"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    discount_type = Column(String(20), nullable=False, default="percentage")  # percentage or fixed
    discount_value = Column(DECIMAL(10, 2), nullable=False)  # percentage or amount
    
    # محدودیت‌های زمانی و استفاده
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # null means no expiration
    max_uses = Column(Integer, nullable=True)  # null means unlimited
    use_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # محدودیت‌های مبلغ
    min_order_amount = Column(DECIMAL(10, 2), nullable=True)  # minimum order amount to apply
    max_discount_amount = Column(DECIMAL(10, 2), nullable=True)  # maximum discount amount for percentage discounts
    
    # محدودیت‌های کاربر و پلن
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null means for all users
    plan_ids = Column(Text, nullable=True)  # comma-separated list of plan IDs, null means all plans
    
    # توضیحات
    description = Column(String(255), nullable=True)
    
    # ارتباط با سایر مدل‌ها
    # No order relationship for now to avoid errors
    
    def __repr__(self) -> str:
        return f"<DiscountCode(id={self.id}, code={self.code}, type={self.discount_type}, value={self.discount_value})>"
