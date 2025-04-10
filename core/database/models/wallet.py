"""Wallet model definition."""

from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from typing import List

from core.database.models.base import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    # Consider precision and scale for your currency
    balance: Mapped[Numeric] = mapped_column(Numeric(15, 2), nullable=False, default=0.00) 

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="wallet")
    transactions: Mapped[List["WalletTransaction"]] = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, balance={self.balance})>" 