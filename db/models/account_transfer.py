"""
مدل AccountTransfer برای مدیریت انتقال اکانت‌های VPN بین پنل‌ها
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from . import Base


class AccountTransfer(Base):
    """مدل انتقال اکانت‌های VPN بین پنل‌ها در سیستم MoonVPN"""
    
    __tablename__ = "account_transfer"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    old_account_id = Column(Integer, ForeignKey("client_accounts.id"), nullable=False)
    new_account_id = Column(Integer, ForeignKey("client_accounts.id"), nullable=False)
    from_panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    to_panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ارتباط با سایر مدل‌ها
    old_account: Mapped["ClientAccount"] = relationship(
        foreign_keys=[old_account_id], 
        back_populates="from_transfers"
    )
    new_account: Mapped["ClientAccount"] = relationship(
        foreign_keys=[new_account_id], 
        back_populates="to_transfers"
    )
    
    def __repr__(self) -> str:
        return f"<AccountTransfer(id={self.id}, old_account_id={self.old_account_id}, new_account_id={self.new_account_id})>"
