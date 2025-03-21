"""
Payment schemas for MoonVPN.

This module contains all the Pydantic models for payment-related data
including transactions, wallets, and orders.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
from app.core.database.models.payment import PaymentMethod, TransactionStatus, TransactionType

class PaymentMethod(str, Enum):
    """Supported payment methods."""
    WALLET = "wallet"
    CARD = "card"
    BANK = "bank"
    ZARINPAL = "zarinpal"

class TransactionStatus(str, Enum):
    """Transaction statuses."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class TransactionType(str, Enum):
    """Transaction types."""
    PURCHASE = "purchase"
    DEPOSIT = "deposit"
    REFUND = "refund"
    WITHDRAWAL = "withdrawal"

class PaymentRequest(BaseModel):
    """Request model for payment processing."""
    user_id: int = Field(..., description="ID of the user making the payment")
    order_id: str = Field(..., description="Unique order ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Selected payment method")
    callback_url: str = Field(..., description="URL to redirect after payment")

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class PaymentResponse(BaseModel):
    """Response model for payment operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    transaction_id: Optional[int] = Field(None, description="ID of the created transaction")
    payment_url: Optional[str] = Field(None, description="URL to redirect for payment")
    authority: Optional[str] = Field(None, description="Payment gateway authority")
    transaction_data: Optional[Dict[str, Any]] = Field(None, description="Additional transaction data")

class TransactionBase(BaseModel):
    """Base model for transaction data."""
    user_id: int = Field(..., description="ID of the user")
    amount: float = Field(..., gt=0, description="Transaction amount")
    type: TransactionType = Field(..., description="Transaction type")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    status: TransactionStatus = Field(..., description="Transaction status")
    order_id: Optional[str] = Field(None, description="Associated order ID")
    authority: Optional[str] = Field(None, description="Payment gateway authority")
    ref_id: Optional[str] = Field(None, description="Payment gateway reference ID")
    transaction_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional transaction data")

class TransactionCreate(TransactionBase):
    """Model for creating a new transaction."""
    pass

class Transaction(TransactionBase):
    """Model for transaction data."""
    id: int = Field(..., description="Transaction ID")
    created_at: datetime = Field(..., description="Transaction creation timestamp")
    updated_at: datetime = Field(..., description="Transaction last update timestamp")

    class Config:
        orm_mode = True

class WalletBase(BaseModel):
    """Base model for wallet data."""
    user_id: int = Field(..., description="ID of the wallet owner")
    balance: float = Field(..., ge=0, description="Current wallet balance")
    currency: str = Field(default="USD", description="Wallet currency")

class WalletCreate(WalletBase):
    """Model for creating a new wallet."""
    pass

class Wallet(WalletBase):
    """Model for wallet data."""
    id: int = Field(..., description="Wallet ID")
    created_at: datetime = Field(..., description="Wallet creation timestamp")
    updated_at: datetime = Field(..., description="Wallet last update timestamp")

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    """Base model for order data."""
    user_id: int = Field(..., description="ID of the order owner")
    plan_id: int = Field(..., description="ID of the purchased plan")
    amount: float = Field(..., gt=0, description="Order amount")
    status: str = Field(..., description="Order status")

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class OrderCreate(OrderBase):
    """Model for creating a new order."""
    pass

class Order(OrderBase):
    """Model for order data."""
    id: int = Field(..., description="Order ID")
    created_at: datetime = Field(..., description="Order creation timestamp")
    updated_at: datetime = Field(..., description="Order last update timestamp")

    class Config:
        orm_mode = True

class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    status: Optional[TransactionStatus] = None
    authority: Optional[str] = None
    ref_id: Optional[str] = None
    transaction_data: Optional[Dict[str, Any]] = None

class WalletUpdate(BaseModel):
    """Schema for updating a wallet."""
    balance: Optional[float] = None

class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    status: Optional[str] = None

class PaymentVerification(BaseModel):
    """Schema for payment verification."""
    authority: str
    status: str
    ref_id: Optional[str] = None 