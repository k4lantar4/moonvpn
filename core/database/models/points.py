"""Points models for managing user points and rewards."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class TransactionType(str, enum.Enum):
    """Points transaction types."""
    EARN = "earn"
    REDEEM = "redeem"
    EXPIRE = "expire"
    ADJUST = "adjust"

class PointsTransaction(Base):
    """Points transaction model for tracking points changes."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Transaction information
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Reference information
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Transaction data
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="points_transactions")
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the points transaction."""
        return f"<PointsTransaction {self.type} {self.points}>"

class PointsRedemptionRule(Base):
    """Points redemption rule model for managing reward rules."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Rule information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Points requirements
    points_required: Mapped[int] = mapped_column(Integer, nullable=False)
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Reward information
    reward_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reward_value: Mapped[float] = mapped_column(Float, nullable=False)
    reward_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Rule settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    redemptions: Mapped[List["PointsRedemption"]] = relationship(
        "PointsRedemption",
        back_populates="rule",
        lazy="selectin"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the redemption rule."""
        return f"<PointsRedemptionRule {self.name}>"
    
    def is_valid(self) -> bool:
        """Check if rule is currently valid."""
        now = datetime.now(self.start_date.tzinfo if self.start_date else None)
        return (
            self.is_active
            and (self.start_date is None or now >= self.start_date)
            and (self.end_date is None or now <= self.end_date)
        )

class PointsRedemption(Base):
    """Points redemption model for tracking reward redemptions."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Redemption information
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    points_used: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    rule_id: Mapped[int] = mapped_column(ForeignKey("pointsredemptionrule.id"), nullable=False)
    
    # Timestamps
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Redemption data
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="points_redemptions")
    rule: Mapped["PointsRedemptionRule"] = relationship(
        "PointsRedemptionRule",
        back_populates="redemptions"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the points redemption."""
        return f"<PointsRedemption {self.rule.name} {self.points_used}>"
    
    def complete(self, metadata: Optional[dict] = None) -> None:
        """Mark redemption as completed."""
        self.status = "completed"
        self.completed_at = datetime.now(self.redeemed_at.tzinfo)
        if metadata:
            self.metadata = metadata
    
    def fail(self, metadata: Optional[dict] = None) -> None:
        """Mark redemption as failed."""
        self.status = "failed"
        self.failed_at = datetime.now(self.redeemed_at.tzinfo)
        if metadata:
            self.metadata = metadata 