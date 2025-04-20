"""
مدل Panel برای مدیریت پنل‌های VPN
"""

from typing import List, Optional

from sqlalchemy import Boolean, Integer, String, Text, Column
from sqlalchemy.orm import relationship, Mapped

from . import Base


class Panel(Base):
    """مدل پنل‌های 3x-ui در سیستم MoonVPN"""
    
    __tablename__ = "panels"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    location = Column(String(100), nullable=False)
    flag_emoji = Column(String(5), nullable=True)
    url = Column(Text, nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    status = Column(Boolean, default=True, nullable=False)
    default_label = Column(String(50), nullable=False)
    
    # ارتباط با سایر مدل‌ها
    inbounds: Mapped[List["Inbound"]] = relationship(back_populates="panel")
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="panel")
    
    def __repr__(self) -> str:
        return f"<Panel(id={self.id}, name={self.name}, location={self.location})>"
