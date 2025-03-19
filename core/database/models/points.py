"""
Points-related models for MoonVPN.
Defines points transactions, redemption rules, and redemptions.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Numeric, Enum, JSON
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel

class PointsTransactionType(enum.Enum):
    """Points transaction types."""
    EARN = "earn"
    REDEEM = "redeem"
    ADJUST = "adjust"
    EXPIRE = "expire"

class PointsTransaction(BaseModel):
    """
    Points transaction model.
    Records all points-related transactions.
    """
    
    amount = Column(Integer, nullable=False)
    type = Column(Enum(PointsTransactionType), nullable=False)
    description = Column(String(500), nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="points_transactions")
    
    def __repr__(self) -> str:
        return f"<PointsTransaction(type='{self.type.value}', amount={self.amount})>"

class PointsRedemptionRule(BaseModel):
    """
    Points redemption rule model.
    Defines rules for redeeming points.
    """
    
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    points_cost = Column(Integer, nullable=False)
    discount_percentage = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0)
    min_subscription_days = Column(Integer, nullable=True)
    applicable_plans = Column(JSON, nullable=True)  # List of plan IDs
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    redemptions = relationship("PointsRedemption", back_populates="rule", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<PointsRedemptionRule(name='{self.name}', points={self.points_cost})>"
    
    def is_valid(self) -> bool:
        """Check if rule is currently valid."""
        now = datetime.utcnow()
        
        if not self.is_active:
            return False
        
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def can_be_used(self, user_points: int, subscription_days: Optional[int] = None) -> bool:
        """Check if rule can be used by a user."""
        if not self.is_valid():
            return False
        
        if user_points < self.points_cost:
            return False
        
        if self.min_subscription_days and subscription_days and subscription_days < self.min_subscription_days:
            return False
        
        return True
    
    def increment_uses(self) -> None:
        """Increment the number of times this rule has been used."""
        if self.max_uses:
            self.current_uses += 1
            if self.current_uses >= self.max_uses:
                self.is_active = False

class PointsRedemption(BaseModel):
    """
    Points redemption model.
    Records when users redeem points using rules.
    """
    
    points_cost = Column(Integer, nullable=False)
    discount_applied = Column(Integer, nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscription.id"), nullable=True)
    subscription = relationship("Subscription")
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User")
    rule_id = Column(Integer, ForeignKey("pointsredemptionrule.id"), nullable=False)
    rule = relationship("PointsRedemptionRule", back_populates="redemptions")
    
    def __repr__(self) -> str:
        return f"<PointsRedemption(points={self.points_cost}, discount={self.discount_applied})>"
    
    def apply_discount(self, subscription: "Subscription") -> None:
        """Apply discount to subscription."""
        if not subscription or not subscription.plan:
            return
        
        original_price = subscription.plan.price
        discount_amount = (original_price * self.discount_applied) / 100
        subscription.price = original_price - discount_amount 