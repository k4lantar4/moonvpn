"""
مدل Inbound برای ذخیره اطلاعات inbound‌های پنل‌ها
"""

from datetime import datetime
from enum import Enum
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship, backref, Mapped

from . import Base
from .panel import Panel
from .client_account import ClientAccount


class InboundStatus(str, Enum):
    """وضعیت‌های ممکن برای inbound"""
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


class Inbound(Base):
    """مدل Inbound برای ذخیره اطلاعات inbound‌های پنل‌ها"""
    
    __tablename__ = "inbound"
    
    id = Column(Integer, primary_key=True)
    panel_id = Column(Integer, ForeignKey("panels.id", ondelete="CASCADE"), nullable=False, index=True)
    remote_id = Column(Integer, nullable=False)  # شناسه inbound در پنل
    protocol = Column(String(50), nullable=False)  # نوع پروتکل
    tag = Column(String(100), nullable=False)  # برچسب inbound
    port = Column(Integer, nullable=False)  # پورت
    settings_json = Column(JSON, nullable=True)  # تنظیمات به صورت JSON
    sniffing = Column(JSON, nullable=True)  # تنظیمات sniffing
    status = Column(SQLEnum(InboundStatus), default=InboundStatus.ACTIVE, nullable=False)  # وضعیت
    max_clients = Column(Integer, default=0)  # حداکثر تعداد کلاینت‌ها
    last_synced = Column(DateTime, default=datetime.utcnow)  # آخرین همگام‌سازی
    listen = Column(String(100), nullable=True)  # آدرس یا میزبان برای گوش دادن
    stream_settings = Column(JSON, nullable=True)  # تنظیمات stream
    allocate_settings = Column(JSON, nullable=True)  # تنظیمات allocate
    receive_original_dest = Column(Boolean, default=False)  # اجازه دریافت مقصد اصلی
    allow_transparent = Column(Boolean, default=False)  # اجازه تراسپرنت
    security_settings = Column(JSON, nullable=True)  # تنظیمات امنیتی
    remark = Column(String(255), nullable=True)  # توضیحات
    
    # روابط
    panel = relationship("Panel", back_populates="inbounds")
    client_accounts: Mapped[List["ClientAccount"]] = relationship(
        "ClientAccount",
        back_populates="inbound"
    )
    
    def __repr__(self):
        """نمایش رشته‌ای مدل"""
        return f"<Inbound {self.protocol}:{self.port} ({self.tag})>"
