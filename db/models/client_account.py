"""
مدل ClientAccount برای مدیریت اکانت‌های VPN کاربران
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, Column, ForeignKey, Integer, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship, Mapped

from . import Base
from .enums import AccountStatus

if TYPE_CHECKING:
    from .user import User
    from .panel import Panel
    from .inbound import Inbound
    from .plan import Plan
    from .order import Order
    from .account_transfer import AccountTransfer
    from .client_renewal_log import ClientRenewalLog


class AccountStatus(str, Enum):
    """وضعیت‌های اکانت VPN"""
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"
    SWITCHED = "switched"


class ClientAccount(Base):
    """مدل اکانت‌های VPN کاربران در سیستم MoonVPN"""
    
    __tablename__ = "client_accounts"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    inbound_id = Column(Integer, ForeignKey("inbound.id", ondelete="CASCADE"), nullable=False)
    remote_uuid = Column(String(36), default=lambda: str(uuid.uuid4()), nullable=False) # شناسه UUID منحصر به فرد در پنل
    client_name = Column(String(255), nullable=False) # نام کلاینت یا برچسب (label/remark) برای نمایش
    email_name = Column(String(255), nullable=True) # آدرس ایمیل مورد استفاده در پنل
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False) # تاریخ انقضا به صورت DateTime در دیتابیس
    expiry_time = Column(BigInteger, nullable=False) # تاریخ انقضا (Timestamp ms از پنل XUI)
    traffic_limit = Column(Integer, nullable=False) # حجم کل به GB
    data_limit = Column(BigInteger, nullable=False) # محدودیت ترافیک (بایت از پنل XUI)
    traffic_used = Column(Integer, default=0, nullable=False) # حجم مصرف‌شده به GB
    data_used = Column(BigInteger, default=0, nullable=False) # ترافیک مصرفی (بایت از پنل XUI)
    status = Column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False)
    enable = Column(Boolean, nullable=False, default=True) # وضعیت فعال/غیرفعال در پنل XUI
    config_url = Column(Text, nullable=True) # لینک کانفیگ برای اتصال
    qr_code_path = Column(String(255), nullable=True) # مسیر فایل QR Code تصویری 
    inbound_ids = Column(JSON, nullable=True) # لیست IDهای Inbound فعال برای این اکانت
    ip_limit = Column(Integer, nullable=True) # محدودیت تعداد IP مجاز
    sub_updated_at = Column(DateTime, nullable=True) # زمان آخرین به‌روزرسانی لینک اشتراک
    sub_last_user_agent = Column(String(255), nullable=True) # آخرین User Agent برای آپدیت اشتراک
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    user: Mapped["User"] = relationship(back_populates="client_accounts")
    panel: Mapped["Panel"] = relationship(back_populates="client_accounts")
    inbound: Mapped["Inbound"] = relationship("Inbound", back_populates="client_accounts")
    plan: Mapped["Plan"] = relationship(back_populates="client_accounts")
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="client_account", 
        foreign_keys="Order.client_account_id"
    )
    
    # Relationships for AccountTransfer
    from_transfers: Mapped[List["AccountTransfer"]] = relationship(
        "AccountTransfer",
        foreign_keys="AccountTransfer.old_account_id",
        back_populates="old_account"
    )
    to_transfers: Mapped[List["AccountTransfer"]] = relationship(
        "AccountTransfer",
        foreign_keys="AccountTransfer.new_account_id",
        back_populates="new_account"
    )
    
    # Relationship for renewal logs
    renewal_logs: Mapped[List["ClientRenewalLog"]] = relationship(
        "ClientRenewalLog",
        back_populates="client"
    )
    
    def __repr__(self) -> str:
        return f"<ClientAccount(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
