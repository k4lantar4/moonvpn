"""Pydantic models (Schemas) for Wallet."""

from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

# Avoid circular imports with ForwardRef
from typing import ForwardRef
Transaction = ForwardRef("Transaction")

class WalletBase(BaseModel):
    user_id: int
    balance: Decimal = Field(0.00, decimal_places=2)

class WalletCreate(WalletBase):
    pass

class WalletUpdate(BaseModel):
    balance: Optional[Decimal] = Field(None, decimal_places=2)

class WalletInDBBase(WalletBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for representing a Wallet in API responses
class Wallet(WalletInDBBase):
    pass

# Schema for representing a Wallet with related transactions
class WalletWithTransactions(Wallet):
    transactions: Optional[List[Transaction]] = None

# Resolve forward references
from core.schemas.transaction import Transaction
WalletWithTransactions.update_forward_refs() 