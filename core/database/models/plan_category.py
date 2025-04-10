from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .plan import Plan

class PlanCategory(Base):
    """Model for plan categories using Mapped syntax."""
    
    __tablename__ = "plan_categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sorting_order: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)
    
    # Relationships (Forward references as strings)
    plans: Mapped[List["Plan"]] = relationship("Plan", back_populates="category", cascade="all, delete-orphan") 

    def __repr__(self) -> str:
        return f"<PlanCategory(id={self.id}, name='{self.name}')>" 