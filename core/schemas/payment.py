"""Pydantic models (Schemas) for Payments."""

from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from enum import Enum

# Enum for Payment Status (matches the model)
class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class PaymentBase(BaseModel):
    user_id: int
    amount: Decimal = Field(..., decimal_places=2)
    payment_method: str = Field(..., max_length=50)  # card, wallet, zarinpal etc.
    order_id: Optional[int] = None

class PaymentCreate(PaymentBase):
    payment_gateway_id: Optional[str] = Field(None, max_length=100)
    card_number: Optional[str] = Field(None, max_length=20)
    tracking_code: Optional[str] = Field(None, max_length=100)
    receipt_image: Optional[str] = Field(None, max_length=255)

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    admin_id: Optional[int] = None
    verification_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    transaction_id: Optional[str] = Field(None, max_length=255)

class PaymentAdminUpdate(PaymentUpdate):
    # Additional fields that only admins can update
    amount: Optional[Decimal] = Field(None, decimal_places=2)
    payment_method: Optional[str] = Field(None, max_length=50)
    order_id: Optional[int] = None

class PaymentInDBBase(PaymentBase):
    id: int
    payment_gateway_id: Optional[str] = None
    card_number: Optional[str] = None
    tracking_code: Optional[str] = None
    receipt_image: Optional[str] = None
    status: Optional[PaymentStatus] = None
    admin_id: Optional[int] = None
    verification_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema for representing a Payment in API responses
class Payment(PaymentInDBBase):
    pass

# Schema for representing a Payment with minimal data for listings
class PaymentSummary(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    payment_method: str
    status: Optional[PaymentStatus] = None
    created_at: datetime

    class Config:
        from_attributes = True 