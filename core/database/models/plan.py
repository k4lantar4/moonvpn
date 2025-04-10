from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, func, BigInteger,
    ForeignKey, DECIMAL
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .plan_category import PlanCategory
#     from .client_account import ClientAccount
#     from .order import Order

class Plan(Base):
    """Model for VPN plans using Mapped syntax."""
    
    __tablename__ = "plans"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    traffic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_clients: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    protocols: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    features: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("plan_categories.id"), nullable=False)
    is_featured: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    sorting_order: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)
    
    # Relationships (Forward references as strings)
    category: Mapped["PlanCategory"] = relationship(back_populates="plans")
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="plan")
    orders: Mapped[List["Order"]] = relationship(back_populates="plan")

    def __repr__(self) -> str:
        return f"<Plan(id={self.id}, name='{self.name}')>" 