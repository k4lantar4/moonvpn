"""
مدل Inbound برای مدیریت inbound‌های پنل‌های VPN
"""

from typing import List, Optional

from sqlalchemy import Boolean, Integer, String, Text, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from . import Base


class Inbound(Base):
    """مدل inbound‌های پنل‌های VPN در سیستم MoonVPN"""
    
    __tablename__ = "inbounds"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    inbound_id = Column(Integer, nullable=False)
    protocol = Column(String(50), nullable=False)
    tag = Column(String(100), nullable=False)
    client_limit = Column(Integer, nullable=False)
    traffic_limit = Column(Integer, nullable=True)  # حجم به GB
    
    # ارتباط با سایر مدل‌ها
    panel: Mapped["Panel"] = relationship(back_populates="inbounds")
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="inbound")
    
    def __repr__(self) -> str:
        return f"<Inbound(id={self.id}, panel_id={self.panel_id}, protocol={self.protocol})>"
