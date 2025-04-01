from typing import Optional
from pydantic import BaseModel, validator, Field
from decimal import Decimal
from enum import Enum
from datetime import datetime

# Supported payment methods
class PaymentMethod(str, Enum):
    MANUAL = "manual"
    CRYPTO = "crypto"
    BANK_TRANSFER = "bank_transfer"
    ONLINE_GATEWAY = "online_gateway"


# Schema for deposit requests
class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod = Field(...)
    payment_reference: Optional[str] = None
    description: Optional[str] = None
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= Decimal('0'):
            raise ValueError('Amount must be positive')
        return v


# Schema for withdrawal requests
class WithdrawRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= Decimal('0'):
            raise ValueError('Amount must be positive')
        return v


# Schema for admin adjustments
class AdminAdjustment(BaseModel):
    user_id: int
    amount: Decimal  # Positive for adding funds, negative for reducing
    description: str
    admin_note: Optional[str] = None
    
    @validator('amount')
    def amount_must_not_be_zero(cls, v):
        if v == Decimal('0'):
            raise ValueError('Amount cannot be zero')
        return v


# Response schemas for transaction history
class TransactionSummary(BaseModel):
    total_deposits: Decimal
    total_withdrawals: Decimal 
    total_purchases: Decimal
    total_refunds: Decimal
    total_adjustments: Decimal
    
    class Config:
        orm_mode = True 