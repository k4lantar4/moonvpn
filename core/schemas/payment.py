"""
Payment schemas for request/response models.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class PaymentBase(BaseModel):
    """Base payment schema."""
    user_id: int
    amount: Decimal = Field(..., ge=0)
    currency: str = "USD"
    status: str = "pending"
    payment_method: str
    payment_provider: str
    transaction_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PaymentCreate(PaymentBase):
    """Payment creation schema."""
    pass

class PaymentUpdate(BaseModel):
    """Payment update schema."""
    status: Optional[str] = None
    transaction_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Payment(PaymentBase):
    """Payment response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    user_id: int
    plan_id: int
    status: str = "active"
    start_date: datetime
    end_date: Optional[datetime] = None
    auto_renew: bool = True
    payment_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class SubscriptionCreate(SubscriptionBase):
    """Subscription creation schema."""
    pass

class SubscriptionUpdate(BaseModel):
    """Subscription update schema."""
    status: Optional[str] = None
    end_date: Optional[datetime] = None
    auto_renew: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class Subscription(SubscriptionBase):
    """Subscription response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    payment: Optional[Payment] = None

    model_config = ConfigDict(from_attributes=True)

class PlanBase(BaseModel):
    """Base plan schema."""
    name: str
    description: str
    price: Decimal = Field(..., ge=0)
    currency: str = "USD"
    duration_days: int = Field(..., ge=1)
    features: List[str]
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None

class PlanCreate(PlanBase):
    """Plan creation schema."""
    pass

class PlanUpdate(BaseModel):
    """Plan update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = None
    duration_days: Optional[int] = Field(None, ge=1)
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class Plan(PlanBase):
    """Plan response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaymentList(BaseModel):
    """Payment list response schema."""
    total: int
    payments: List[Payment]
    page: int
    size: int
    pages: int

class SubscriptionList(BaseModel):
    """Subscription list response schema."""
    total: int
    subscriptions: List[Subscription]
    page: int
    size: int
    pages: int

class PlanList(BaseModel):
    """Plan list response schema."""
    total: int
    plans: List[Plan]
    page: int
    size: int
    pages: int

class PaymentStats(BaseModel):
    """Payment statistics schema."""
    total_amount: Decimal
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    pending_transactions: int
    refunded_transactions: int
    last_24h_amount: Decimal
    last_7d_amount: Decimal
    last_30d_amount: Decimal
    last_24h_transactions: int
    last_7d_transactions: int
    last_30d_transactions: int
    metadata: Optional[Dict[str, Any]] = None 