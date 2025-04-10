from datetime import datetime
from decimal import Decimal
from typing import Optional
import enum

from sqlalchemy import (
    String, Text, DateTime, ForeignKey, Enum as SQLAlchemyEnum,
    DECIMAL, Integer, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .user import User

class TransactionType(enum.Enum):
    DEPOSIT = 'DEPOSIT'
    WITHDRAW = 'WITHDRAW'
    PURCHASE = 'PURCHASE'
    REFUND = 'REFUND'
    COMMISSION = 'COMMISSION'

class Transaction(Base):
    """Model for financial transactions using Mapped syntax."""
    
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    type: Mapped[TransactionType] = mapped_column(SQLAlchemyEnum(TransactionType, name='transaction_type_enum'), nullable=False)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Ref to payment_id or order_id
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    balance_after: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="transactions")
    # Add relationship for reference_id later when its target is clear (Payment? Order?)

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, user_id={self.user_id}, type={self.type}, amount={self.amount})>" 