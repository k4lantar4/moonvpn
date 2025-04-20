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


class ClientAccount(Base):
    """مدل اکانت‌های VPN کاربران در سیستم MoonVPN"""
    
    __tablename__ = "client_accounts"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    inbound_id = Column(Integer, ForeignKey("inbounds.id"), nullable=False)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), nullable=False)
    label = Column(String(255), nullable=False)
    transfer_id = Column(String(100), unique=True, nullable=False)
    transfer_count = Column(Integer, default=0, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    traffic_total = Column(Integer, nullable=False)  # حجم کل به GB
    traffic_used = Column(Integer, default=0, nullable=False)  # حجم مصرف‌شده به GB
    status = Column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False)
    config_url = Column(Text, nullable=True)
    
    # ارتباط با سایر مدل‌ها
    user: Mapped["User"] = relationship(back_populates="client_accounts")
    panel: Mapped["Panel"] = relationship(back_populates="client_accounts")
    inbound: Mapped["Inbound"] = relationship(back_populates="client_accounts")
    from_transfers: Mapped[List["AccountTransfer"]] = relationship(
        foreign_keys="AccountTransfer.old_account_id",
        back_populates="old_account"
    )
    to_transfers: Mapped[List["AccountTransfer"]] = relationship(
        foreign_keys="AccountTransfer.new_account_id",
        back_populates="new_account"
    )
    
    def __repr__(self) -> str:
        return f"<ClientAccount(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
