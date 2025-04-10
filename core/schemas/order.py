"""Pydantic schemas for Order model serialization."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator, validator
from enum import Enum

from core.database.models.order import OrderStatus
from core.schemas.discount_code import DiscountCodeRead, DiscountCodePublic
from core.schemas.plan import Plan

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class OrderBase(BaseModel):
    """Base schema for order data."""
    user_id: int = Field(..., description="User ID who placed the order")
    plan_id: int = Field(..., description="ID of the plan being ordered")
    quantity: int = Field(1, ge=1, description="Quantity of the plan ordered")
    original_amount: float = Field(..., description="Original amount before discount")
    final_amount: float = Field(..., description="Final amount after discount")
    discount_code_id: Optional[int] = Field(None, description="ID of the applied discount code")
    status: OrderStatus = Field(OrderStatus.PENDING, description="Current status of the order")
    notes: Optional[str] = Field(None, description="Additional notes for the order")
    
    @validator('final_amount')
    def validate_final_amount(cls, v, values):
        if 'original_amount' in values and v > values['original_amount']:
            raise ValueError('Final amount cannot be greater than original amount')
        if v < 0:
            raise ValueError('Final amount cannot be negative')
        return v

class OrderCreate(BaseModel):
    """Schema for creating a new order."""
    plan_id: int
    quantity: int = Field(1, ge=1)
    discount_code: Optional[str] = None
    notes: Optional[str] = None

class OrderUpdate(BaseModel):
    """Schema for updating an existing order."""
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None

class OrderDB(OrderBase):
    """Schema for order as stored in database."""
    id: int = Field(..., description="Unique identifier for the order")
    created_at: datetime = Field(..., description="Timestamp when the order was created")
    updated_at: datetime = Field(..., description="Timestamp when the order was last updated")
    payment_id: Optional[int] = Field(None, description="ID of the payment transaction if paid")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when the order was completed")

    class Config:
        from_attributes = True

class OrderRead(OrderDB):
    """Schema for reading an order with additional details."""
    plan: Optional[Plan] = None
    discount_code: Optional[DiscountCodePublic] = None
    
    class Config:
        from_attributes = True

class OrderWithRelations(OrderRead):
    """Schema for order with related entities."""
    # Will include user and plan schemas when they're defined
    # user: UserRead
    # plan: Plan

    class Config:
        from_attributes = True

class OrderSummary(BaseModel):
    """Schema for order summary statistics."""
    total_orders: int
    total_completed: int
    total_pending: int
    total_cancelled: int
    total_revenue: float
    average_order_value: float 