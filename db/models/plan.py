"""
ماژول Plan - مدل مدیریت پلن‌های سرویس MoonVPN
"""

from sqlalchemy import Boolean, Column, Integer, String, DECIMAL, JSON, Enum as SQLEnum, BigInteger, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime

from db.models import Base

if TYPE_CHECKING:
    from .user import User
    from .order import Order
    from .test_account_log import TestAccountLog
    from .client_account import ClientAccount

class PlanStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Plan(Base):
    """مدل پلن‌های سرویس VPN"""
    
    __tablename__ = "plans"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True, comment="شناسه پلن")
    name = Column(String(100), nullable=False, index=True, comment="نام پلن")
    description = Column(Text, nullable=True, comment="توضیحات پلن")
    traffic_gb = Column(Integer, nullable=False, comment="حجم ترافیک به گیگابایت")
    duration_days = Column(Integer, nullable=False, comment="مدت اعتبار به روز")
    price = Column(DECIMAL(10, 2), nullable=False, comment="قیمت")
    available_locations = Column(JSON, nullable=True, comment="لیست لوکیشن‌های مجاز")
    created_by_id = Column(BigInteger, ForeignKey("users.id"), nullable=True) # Nullable if admin can create, or specific creator
    status = Column(SQLEnum(PlanStatus), default=PlanStatus.ACTIVE, nullable=False, comment="آیا پلن فعال است؟")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="زمان ایجاد")
    # is_trial = Column(Boolean, default=False, nullable=False, comment="آیا پلن تستی است؟") # Moved to test_account_log
    # is_active = Column(Boolean, default=True, nullable=False, comment="آیا پلن فعال است؟") # Replaced by status
    
    # تعریف روابط با سایر مدل‌ها
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id], back_populates="created_plans")
    orders: Mapped[List["Order"]] = relationship(back_populates="plan")
    test_account_logs: Mapped[List["TestAccountLog"]] = relationship(back_populates="plan")
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="plan")
    
    def __repr__(self) -> str:
        """نمایش متنی مدل"""
        return f"<Plan(id={self.id}, name='{self.name}', traffic={self.traffic_gb}GB, days={self.duration_days})>"
