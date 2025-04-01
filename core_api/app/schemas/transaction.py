from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from decimal import Decimal

from app.models.transaction import TransactionType, TransactionStatus


# Base properties shared by all transaction schemas
class TransactionBase(BaseModel):
    """Base schema with common attributes for all Transaction schemas"""
    user_id: int
    amount: Decimal
    type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    order_id: Optional[int] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    description: Optional[str] = None
    admin_note: Optional[str] = None


# Properties to receive on Transaction creation
class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction"""
    balance_after: Optional[Decimal] = None  # Will be calculated in service layer
    
    @validator('amount')
    def amount_not_zero(cls, v):
        if v == 0:
            raise ValueError('Amount cannot be zero')
        return v
        
    class Config:
        arbitrary_types_allowed = True


# Properties to receive on Transaction update
class TransactionUpdate(BaseModel):
    """Schema for updating a transaction"""
    status: Optional[TransactionStatus] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    admin_note: Optional[str] = None
    admin_id: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True


# Properties shared by models stored in DB
class TransactionInDBBase(TransactionBase):
    """Schema for transaction data from database"""
    id: int
    transaction_id: str
    balance_after: Decimal
    admin_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Properties to return to client
class Transaction(TransactionInDBBase):
    """Schema for public transaction representation"""
    pass


# Additional properties stored in DB
class TransactionInDB(TransactionInDBBase):
    """Schema for transaction in database with additional sensitive information"""
    pass


# For deposit operations
class DepositRequest(BaseModel):
    """Schema for initiating a deposit"""
    amount: Decimal = Field(..., gt=0)
    payment_method: str
    payment_reference: Optional[str] = None
    description: Optional[str] = None


# For withdrawal operations
class WithdrawRequest(BaseModel):
    """Schema for initiating a withdrawal"""
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None


# For admin adjustments
class AdminAdjustment(BaseModel):
    """Schema for admin adjustments to user wallet"""
    user_id: int
    amount: Decimal  # Can be positive or negative
    description: str
    admin_note: Optional[str] = None 