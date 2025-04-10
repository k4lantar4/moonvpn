from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Integer, String, Boolean, DateTime, DECIMAL, func
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database.session import Base

class BankCard(Base):
    """Model for bank cards used for payments using Mapped syntax."""
    
    __tablename__ = "bank_cards"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    card_number: Mapped[str] = mapped_column(String(20), nullable=False)
    account_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    owner_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    rotation_priority: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    daily_limit: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2), nullable=True)
    monthly_limit: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)

    def __repr__(self) -> str:
        return f"<BankCard(id={self.id}, bank_name='{self.bank_name}', card_number='****{self.card_number[-4:]}')>" 