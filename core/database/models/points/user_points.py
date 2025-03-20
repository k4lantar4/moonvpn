"""
UserPoints model for managing user points and rewards.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from ..base import BaseModel

class UserPoints(BaseModel):
    """
    UserPoints model for managing user points and rewards.
    
    Attributes:
        user_id: Reference to user
        points: Current points balance
        total_earned: Total points earned
        total_spent: Total points spent
        last_updated: Last points update timestamp
        metadata: Additional points data
    """
    
    # Points identification
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="points")
    transactions: Mapped[List["PointsTransaction"]] = relationship(
        back_populates="user_points",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the user points."""
        return f"<UserPoints(user_id={self.user_id}, points={self.points})>" 