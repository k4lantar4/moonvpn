"""
UserPoints model for managing user points and rewards.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class PointsStatus(str, enum.Enum):
    """Points status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FROZEN = "frozen"

class UserPoints(BaseModel):
    """
    UserPoints model for managing user points.
    
    Attributes:
        user_id: Reference to user
        points: Current points balance
        total_earned: Total points earned
        total_spent: Total points spent
        status: Points status
        is_active: Whether the points account is active
        last_updated: Last update timestamp
        metadata: Additional points data
    """
    
    # Points identification
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, nullable=False)
    
    # Points details
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[PointsStatus] = mapped_column(Enum(PointsStatus), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Tracking
    last_updated: Mapped[datetime] = mapped_column(nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="points")
    transactions: Mapped[List["PointsTransaction"]] = relationship(back_populates="points_account")
    
    def __repr__(self) -> str:
        """String representation of the user points."""
        return f"<UserPoints(user_id={self.user_id}, points={self.points})>" 