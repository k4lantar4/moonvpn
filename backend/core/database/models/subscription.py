"""Subscription models for managing VPN service plans and subscriptions."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class SubscriptionStatus(str, enum.Enum):
    """Subscription status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"
    FAILED = "failed"

class Plan(Base):
    """VPN service plan model."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Plan information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Pricing
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Features
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    traffic_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in bytes
    max_connections: Mapped[int] = mapped_column(Integer, default=1)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="plan",
        lazy="selectin"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the plan."""
        return f"<Plan {self.name}>"
    
    @property
    def formatted_price(self) -> str:
        """Get formatted price with currency."""
        return f"{self.currency} {self.price:.2f}"

class Subscription(Base):
    """VPN service subscription model."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Subscription information
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus),
        default=SubscriptionStatus.PENDING,
        nullable=False
    )
    
    # Relationships
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plan.id"), nullable=False)
    
    # Timestamps
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Payment information
    payment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("payment.id"), nullable=True)
    amount_paid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")
    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="subscriptions")
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the subscription."""
        return f"<Subscription {self.user.username} {self.plan.name}>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return (
            self.status == SubscriptionStatus.ACTIVE
            and datetime.now(self.start_date.tzinfo) <= self.end_date
        )
    
    @property
    def days_remaining(self) -> int:
        """Get number of days remaining in subscription."""
        if not self.is_active:
            return 0
        return (self.end_date - datetime.now(self.end_date.tzinfo)).days
    
    def cancel(self) -> None:
        """Cancel the subscription."""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.now(self.start_date.tzinfo)
    
    def renew(self, payment_id: int, amount: float, currency: str) -> None:
        """Renew the subscription."""
        self.status = SubscriptionStatus.ACTIVE
        self.payment_id = payment_id
        self.amount_paid = amount
        self.currency = currency
        self.start_date = datetime.now(self.start_date.tzinfo)
        self.end_date = self.start_date + timedelta(days=self.plan.duration_days) 