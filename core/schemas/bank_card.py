"""Pydantic models (Schemas) for Bank Cards."""

from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

class BankCardBase(BaseModel):
    bank_name: str = Field(..., max_length=100)
    card_number: str = Field(..., max_length=20)
    owner_name: str = Field(..., max_length=100)
    account_number: Optional[str] = Field(None, max_length=30)

class BankCardCreate(BankCardBase):
    is_active: Optional[bool] = True
    rotation_priority: Optional[int] = None
    daily_limit: Optional[Decimal] = Field(None, decimal_places=2)
    monthly_limit: Optional[Decimal] = Field(None, decimal_places=2)

class BankCardUpdate(BaseModel):
    bank_name: Optional[str] = Field(None, max_length=100)
    card_number: Optional[str] = Field(None, max_length=20)
    owner_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=30)
    is_active: Optional[bool] = None
    rotation_priority: Optional[int] = None
    last_used: Optional[datetime] = None
    daily_limit: Optional[Decimal] = Field(None, decimal_places=2)
    monthly_limit: Optional[Decimal] = Field(None, decimal_places=2)

class BankCardInDBBase(BankCardBase):
    id: int
    is_active: Optional[bool] = None
    rotation_priority: Optional[int] = None
    last_used: Optional[datetime] = None
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema for representing a BankCard in API responses
class BankCard(BankCardInDBBase):
    # Optionally mask the sensitive card number in responses
    @property
    def masked_card_number(self) -> str:
        if len(self.card_number) >= 16:
            return f"{'*' * 12}{self.card_number[-4:]}"
        return f"****{self.card_number[-4:]}"

# Schema for listing cards with less detail
class BankCardSummary(BaseModel):
    id: int
    bank_name: str
    # masked_card_number: str  # Removed to avoid conflict with property
    owner_name: str
    is_active: Optional[bool] = None
    card_number: str  # Added to be used by the property

    class Config:
        from_attributes = True

    @property
    def masked_card_number(self) -> str:
        if hasattr(self, 'card_number'):
            if len(self.card_number) >= 16:
                return f"{'*' * 12}{self.card_number[-4:]}"
            return f"****{self.card_number[-4:]}"
        return "******" 