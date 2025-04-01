from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, constr
from decimal import Decimal

from app.models.order import OrderStatus, PaymentMethod


# Shared properties
class OrderBase(BaseModel):
    """Base schema with common attributes for all Order schemas"""
    user_id: int
    plan_id: int
    panel_id: Optional[int] = None
    status: OrderStatus = OrderStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    amount: Decimal
    discount_amount: Decimal = Decimal('0.00')
    final_amount: Decimal
    discount_code: Optional[str] = None
    config_protocol: Optional[str] = None
    config_days: Optional[int] = None
    config_traffic_gb: Optional[int] = None
    config_details: Optional[Dict[str, Any]] = None
    admin_note: Optional[str] = None


# Properties to receive on Order creation
class OrderCreate(OrderBase):
    """Schema for creating a new order"""
    # Override required fields that shouldn't be required during creation
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    
    @validator('final_amount', pre=True)
    def calculate_final_amount(cls, v, values):
        """Calculate final amount if not explicitly provided"""
        if v is None and 'amount' in values and 'discount_amount' in values:
            return values['amount'] - values['discount_amount']
        return v


# Properties to receive on Order update
class OrderUpdate(BaseModel):
    """Schema for updating an order"""
    status: Optional[OrderStatus] = None
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    payment_proof: Optional[str] = None
    panel_id: Optional[int] = None
    inbound_id: Optional[int] = None
    client_uuid: Optional[str] = None
    client_email: Optional[str] = None
    subscription_id: Optional[int] = None
    admin_note: Optional[str] = None
    admin_id: Optional[int] = None
    paid_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


# Properties to return from API
class OrderInDB(OrderBase):
    """Schema for order data from database"""
    id: int
    order_id: str
    inbound_id: Optional[int] = None
    client_uuid: Optional[str] = None
    client_email: Optional[str] = None
    subscription_id: Optional[int] = None
    payment_proof: Optional[str] = None
    admin_id: Optional[int] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


# Public representation
class Order(OrderInDB):
    """Schema for public order representation"""
    # Include any calculated fields or extra info to return
    plan_name: Optional[str] = None
    panel_name: Optional[str] = None
    subscription_id: Optional[int] = None
    
    class Config:
        orm_mode = True


# For admin dashboard and detailed order information
class OrderDetail(Order):
    """Schema for detailed order info with nested objects"""
    # Nested models can be defined if needed
    class Config:
        orm_mode = True


# For order status filtering and listing
class OrderStatusList(BaseModel):
    """Schema for listing orders with status filters"""
    statuses: List[OrderStatus] = []


# For bulk operations
class OrderIds(BaseModel):
    """Schema for bulk order operations"""
    order_ids: List[int] 