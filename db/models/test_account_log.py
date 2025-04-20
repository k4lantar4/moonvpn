"""
مدل TestAccountLog برای مدیریت سوابق دریافت اکانت تست توسط کاربران
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from . import Base


class TestAccountLog(Base):
    """مدل سوابق دریافت اکانت تست در سیستم MoonVPN"""
    
    __tablename__ = "test_account_log"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    user: Mapped["User"] = relationship(back_populates="test_account_logs")
    plan: Mapped["Plan"] = relationship(back_populates="test_account_logs")
    
    def __repr__(self) -> str:
        return f"<TestAccountLog(id={self.id}, user_id={self.user_id}, plan_id={self.plan_id})>"
