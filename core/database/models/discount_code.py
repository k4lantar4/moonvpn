from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import enum

from sqlalchemy import (
    String, Text, DateTime, ForeignKey, Enum as SQLAlchemyEnum,
    DECIMAL, Integer, Boolean, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .user import User
#     from .order import Order

class DiscountType(enum.Enum):
    FIXED = 'FIXED'
    PERCENTAGE = 'PERCENTAGE'

class DiscountCode(Base):
    """Model for discount codes using Mapped syntax."""

    __tablename__ = "discount_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(SQLAlchemyEnum(DiscountType, name='discount_type_enum'), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), name="created_by", nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)

    # Relationships
    # Need to add back_populates="created_discount_codes" to User model if uncommenting
    # creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id]) 
    orders: Mapped[List["Order"]] = relationship(back_populates="discount_code")

    def __repr__(self) -> str:
        return f"<DiscountCode(id={self.id}, code='{self.code}', active={self.is_active})>"