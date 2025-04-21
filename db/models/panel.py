"""
مدل Panel برای مدیریت پنل‌های VPN
"""

from typing import List, Optional
from enum import Enum

from sqlalchemy import Integer, String, Text, Column, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped

from . import Base


class PanelStatus(str, Enum):
    """وضعیت‌های ممکن برای پنل"""
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


class PanelType(str, Enum):
    """نوع پنل"""
    XUI = "xui"


class Panel(Base):
    """مدل پنل‌های 3x-ui در سیستم MoonVPN"""
    
    __tablename__ = "panels"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    location_name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    type = Column(SQLEnum(PanelType), default=PanelType.XUI, nullable=False)
    status = Column(SQLEnum(PanelStatus), default=PanelStatus.ACTIVE, nullable=False)
    notes = Column(Text, nullable=True)
    
    # ارتباط با سایر مدل‌ها
    inbounds: Mapped[List["Inbound"]] = relationship(back_populates="panel")
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="panel")
    
    def __repr__(self) -> str:
        return f"<Panel(id={self.id}, name={self.name}, location={self.location_name})>"
