"""
مدل Setting برای مدیریت تنظیمات سیستم
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Column, Text
from sqlalchemy.orm import relationship

from . import Base


class Setting(Base):
    """مدل تنظیمات سیستم"""
    
    __tablename__ = "settings"
    
    # فیلدهای اصلی
    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # str, int, float, bool, json
    scope = Column(String(50), nullable=False)  # system, bot, panel, payment
    description = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Setting(key={self.key}, type={self.type}, scope={self.scope})>" 