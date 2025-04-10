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
#     from .order import Order

class PaymentStatus(enum.Enum):
    PENDING = 'PENDING'
    VERIFIED = 'VERIFIED'
    REJECTED = 'REJECTED'

class Payment(Base):
    """Model for user payments using Mapped syntax."""
    
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)  # card, wallet, zarinpal etc.
    payment_gateway_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    card_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tracking_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    receipt_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[Optional[PaymentStatus]] = mapped_column(SQLAlchemyEnum(PaymentStatus, name='payment_status_enum'), default=None, nullable=True)
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)
    
    # Relationships (Forward references as strings)
    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="payments")
    admin: Mapped[Optional["User"]] = relationship(foreign_keys=[admin_id], back_populates="approved_payments")
    order: Mapped[Optional["Order"]] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, order_id={self.order_id}, status={self.status})>"