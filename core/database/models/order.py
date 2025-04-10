from datetime import datetime
from decimal import Decimal
from typing import List, Optional
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
#     from .plan import Plan
#     from .discount_code import DiscountCode
#     from .payment import Payment
#     from .client_account import ClientAccount

class OrderStatus(enum.Enum):
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'

class Order(Base):
    """Model representing a user order for a plan using Mapped syntax."""
    
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False)
    discount_code_id: Mapped[Optional[int]] = mapped_column(ForeignKey("discount_codes.id"), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'wallet', 'card', 'zarinpal'
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    discount_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), default=None, nullable=True)
    final_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[Optional[OrderStatus]] = mapped_column(SQLAlchemyEnum(OrderStatus, name='order_status_enum'), default=None, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    plan: Mapped["Plan"] = relationship(back_populates="orders")
    discount_code: Mapped[Optional["DiscountCode"]] = relationship(foreign_keys=[discount_code_id], back_populates="orders")
    payments: Mapped[List["Payment"]] = relationship(back_populates="order")
    # An order should ideally result in one client account, but using List for flexibility?
    # Let's assume one-to-many for now, can be changed to one-to-one if needed.
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="order")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, plan_id={self.plan_id}, status={self.status})>" 