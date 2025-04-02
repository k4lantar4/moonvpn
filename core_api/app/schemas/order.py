from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, constr, HttpUrl
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
    payment_authority: Optional[str] = None
    amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    final_amount: Optional[Decimal] = None
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
    amount: Optional[Decimal] = Field(None, exclude=True)
    discount_amount: Optional[Decimal] = Field(None, exclude=True)
    final_amount: Optional[Decimal] = Field(None, exclude=True)


# Properties to receive on Order update
class OrderUpdate(BaseModel):
    """Schema for updating an order"""
    status: Optional[OrderStatus] = None
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    payment_authority: Optional[str] = None
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


# Payment proof submission schema
class PaymentProofSubmit(BaseModel):
    """Schema for submitting payment proof"""
    payment_reference: constr(min_length=4, max_length=100)
    payment_method: PaymentMethod = PaymentMethod.CARD_TO_CARD
    notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "payment_reference": "1234567890",
                "payment_method": "card_to_card",
                "notes": "Payment from my personal card"
            }
        }


# Payment proof verification schema
class PaymentProofVerify(BaseModel):
    """Schema for verifying or rejecting payment proof"""
    is_approved: bool
    admin_note: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    @validator('rejection_reason')
    def validate_rejection_reason(cls, v, values):
        """Require rejection reason if not approved"""
        if 'is_approved' in values and not values['is_approved'] and not v:
            raise ValueError('Rejection reason is required when rejecting payment')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "is_approved": True,
                "admin_note": "Payment verified successfully",
                "rejection_reason": None
            }
        }


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
    payment_proof_img_url: Optional[str] = None
    payment_proof_submitted_at: Optional[datetime] = None
    payment_verified_at: Optional[datetime] = None
    payment_verification_admin_id: Optional[int] = None
    payment_rejection_reason: Optional[str] = None
    payment_authority: Optional[str] = None
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
    payment_verification_admin_name: Optional[str] = None
    
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