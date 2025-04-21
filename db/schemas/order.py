"""
Pydantic Schemas for Order Model
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

from db.models.enums import OrderStatus

class OrderBase(BaseModel):
    user_id: int
    plan_id: int
    inbound_id: int
    amount: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        use_enum_values = True # Ensure Enum values are used

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    # Add other updatable fields if needed
    updated_at: datetime = datetime.utcnow()

    class Config:
        orm_mode = True
        use_enum_values = True

class OrderSchema(OrderBase):
    id: int
    # Include relationships or other fields if needed 