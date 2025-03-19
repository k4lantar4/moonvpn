"""
Subscription-related models for MoonVPN.
Defines subscription plans and user subscriptions.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Numeric, Enum, JSON
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel

class PlanStatus(enum.Enum):
    """Subscription plan status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class SubscriptionStatus(enum.Enum):
    """User subscription status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"

class Plan(BaseModel):
    """
    Subscription plan model.
    Defines available VPN subscription plans.
    """
    
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    traffic_limit = Column(BigInteger, nullable=True)  # in bytes
    max_devices = Column(Integer, default=1)
    features = Column(JSON, nullable=True)
    status = Column(Enum(PlanStatus), default=PlanStatus.ACTIVE, nullable=False)
    is_featured = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Plan(name='{self.name}', price={self.price})>"
    
    def is_active(self) -> bool:
        """Check if plan is active."""
        return self.status == PlanStatus.ACTIVE
    
    def get_duration(self) -> timedelta:
        """Get plan duration as timedelta."""
        return timedelta(days=self.duration_days)

class Subscription(BaseModel):
    """
    User subscription model.
    Represents a user's subscription to a VPN plan.
    """
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    is_active = Column(Boolean, default=False)
    auto_renew = Column(Boolean, default=False)
    last_renewal = Column(DateTime, nullable=True)
    next_renewal = Column(DateTime, nullable=True)
    cancellation_date = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="subscriptions")
    plan_id = Column(Integer, ForeignKey("plan.id"), nullable=False)
    plan = relationship("Plan", back_populates="subscriptions")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.start_date:
            self.start_date = datetime.utcnow()
        if not self.end_date and self.plan:
            self.end_date = self.start_date + self.plan.get_duration()
    
    def activate(self) -> None:
        """Activate subscription."""
        self.status = SubscriptionStatus.ACTIVE
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate subscription."""
        self.status = SubscriptionStatus.EXPIRED
        self.is_active = False
    
    def cancel(self) -> None:
        """Cancel subscription."""
        self.status = SubscriptionStatus.CANCELLED
        self.is_active = False
        self.cancellation_date = datetime.utcnow()
    
    def renew(self) -> None:
        """Renew subscription."""
        if not self.plan:
            return
        
        self.start_date = datetime.utcnow()
        self.end_date = self.start_date + self.plan.get_duration()
        self.status = SubscriptionStatus.ACTIVE
        self.is_active = True
        self.last_renewal = datetime.utcnow()
        self.next_renewal = self.end_date
    
    def is_expired(self) -> bool:
        """Check if subscription is expired."""
        return datetime.utcnow() > self.end_date
    
    def days_remaining(self) -> int:
        """Get number of days remaining in subscription."""
        if not self.is_active:
            return 0
        return (self.end_date - datetime.utcnow()).days
    
    def should_renew(self) -> bool:
        """Check if subscription should be renewed."""
        return self.auto_renew and self.days_remaining() <= 7 