from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .plan import Plan

class PlanCategory(Base):
    """ Represents a category for organizing subscription plans. """
    __tablename__ = "plan_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship (One-to-Many: PlanCategory to Plans)
    plans: "List[Plan]" = relationship("Plan", back_populates="category")

    def __repr__(self) -> str:
        return f"<PlanCategory(id={self.id}, name='{self.name}')>" 