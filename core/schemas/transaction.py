"""Pydantic models (Schemas) for Transactions."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

# Enum for Transaction Type (assuming it exists in models)
# from core.database.models.transaction import TransactionType
from enum import Enum
class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT" # Wallet deposit (Card, Gateway)
    PURCHASE = "PURCHASE" # Buying a plan/service
    REFUND = "REFUND" # Refunding a purchase
    COMMISSION = "COMMISSION" # Seller commission
    WITHDRAWAL = "WITHDRAWAL" # Admin withdrawal from user balance
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT" # Admin manual balance change

# Enum for Transaction Status (assuming it exists in models)
# from core.database.models.transaction import TransactionStatus
class TransactionStatus(str, Enum):
    PENDING = "PENDING" # e.g., Waiting for payment verification
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class TransactionBase(BaseModel):
    user_id: int
    amount: Decimal = Field(..., decimal_places=2)
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.COMPLETED
    description: Optional[str] = None
    reference_id: Optional[str] = Field(None, max_length=100, description="e.g., Order ID, Payment Gateway Ref")
    metadata: Optional[Dict[str, Any]] = None # For storing extra details

class TransactionCreate(TransactionBase):
    pass

# Transactions are usually immutable, so Update might not be needed
# or very limited (e.g., updating status from PENDING)
class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    description: Optional[str] = None
    reference_id: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None

class TransactionInDBBase(TransactionBase):
    id: int
    transaction_date: datetime

    class Config:
        from_attributes = True

# Schema for representing a Transaction in API responses
class Transaction(TransactionInDBBase):
    pass 