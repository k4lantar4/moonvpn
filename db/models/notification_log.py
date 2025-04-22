"""
مدل NotificationLog برای مدیریت نوتیفیکیشن‌ها
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, Column, Enum as SQLEnum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .user import User


class NotificationStatus(str, Enum):
    """وضعیت‌های نوتیفیکیشن"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationType(str, Enum):
    """انواع نوتیفیکیشن"""
    RECEIPT = "receipt"
    ORDER = "order"
    EXPIRY = "expiry"
    BALANCE = "balance"
    SYSTEM = "system"


class NotificationChannel(str, Enum):
    """کانال‌های ارسال نوتیفیکیشن"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"


class NotificationLog(Base):
    """مدل لاگ نوتیفیکیشن‌ها"""
    
    __tablename__ = "notification_logs"
    
    # فیلدهای اصلی
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), default=NotificationChannel.TELEGRAM, nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(JSON, nullable=True)  # For batch sends: success/failed/pending count
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="notification_logs")
    
    def __repr__(self) -> str:
        return f"<NotificationLog(id={self.id}, type={self.type}, status={self.status})>" 