"""
مدل ClientAccount برای مدیریت اکانت‌های VPN کاربران
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, Column, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped

from . import Base


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
    remote_uuid = Column(String(36), default=lambda: str(uuid.uuid4()), nullable=False)
    client_name = Column(String(255), nullable=False)
    email_name = Column(String(255), nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    traffic_limit = Column(Integer, nullable=False)  # حجم کل به GB
    traffic_used = Column(Integer, default=0, nullable=False)  # حجم مصرف‌شده به GB
    status = Column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False)
    config_url = Column(Text, nullable=True)
    qr_code_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    user: Mapped["User"] = relationship(back_populates="client_accounts")
    panel: Mapped["Panel"] = relationship(back_populates="client_accounts")
    inbound: Mapped["Inbound"] = relationship("Inbound", back_populates="client_accounts")
    plan: Mapped["Plan"] = relationship()
    order: Mapped["Order"] = relationship()
    
    def __repr__(self) -> str:
        return f"<ClientAccount(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
