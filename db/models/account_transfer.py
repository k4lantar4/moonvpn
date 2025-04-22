"""
مدل AccountTransfer برای مدیریت انتقال اکانت‌های VPN بین پنل‌ها
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from . import Base
from .client_account import ClientAccount


class AccountTransfer(Base):
    """مدل انتقال اکانت‌های VPN بین پنل‌ها در سیستم MoonVPN"""
    
    __tablename__ = "account_transfers"
    
    # فیلدهای اصلی
    id: Mapped[int] = mapped_column(primary_key=True)
    old_account_id: Mapped[int] = mapped_column(ForeignKey("client_accounts.id"))
    new_account_id: Mapped[int] = mapped_column(ForeignKey("client_accounts.id"))
    from_panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    to_panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    old_account: Mapped["ClientAccount"] = relationship(
        "ClientAccount",
        foreign_keys=[old_account_id],
        back_populates="from_transfers"
    )
    new_account: Mapped["ClientAccount"] = relationship(
        "ClientAccount",
        foreign_keys=[new_account_id],
        back_populates="to_transfers"
    )
    
    def __repr__(self) -> str:
        return f"<AccountTransfer(id={self.id}, old_account_id={self.old_account_id}, new_account_id={self.new_account_id})>"
