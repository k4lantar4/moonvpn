from typing import Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator


# Shared properties
class BankCardBase(BaseModel):
    """Base schema for bank card with common attributes"""
    bank_name: str = Field(..., example="Bank Mellat")
    card_number: str = Field(..., min_length=16, max_length=19, example="6104337712345678")
    card_holder_name: str = Field(..., example="Mohammad Reza Mohammadi")
    account_number: Optional[str] = Field(None, example="1234567890")
    sheba_number: Optional[str] = Field(None, example="IR123456789012345678901234")
    is_active: Optional[bool] = Field(True, example=True)
    priority: Optional[int] = Field(0, example=0)
    description: Optional[str] = Field(None, example="Main bank card for receiving payments")

    @validator('card_number')
    def validate_card_number(cls, v):
        """Validate that card_number contains only digits and has proper length"""
        # Strip any spaces or dashes
        v = v.replace(' ', '').replace('-', '')
        if not v.isdigit():
            raise ValueError('Card number must contain only digits')
        if not (16 <= len(v) <= 19):
            raise ValueError('Card number must be between 16 and 19 digits')
        return v

    @validator('sheba_number')
    def validate_sheba(cls, v):
        """Validate SHEBA format if provided"""
        if v:
            v = v.replace(' ', '')
            if not v.startswith('IR'):
                raise ValueError('SHEBA number must start with IR')
            if len(v) != 26:
                raise ValueError('SHEBA number must be 24 digits plus IR prefix')
            # Additional validation could be added here
        return v


# Properties to receive on bank card creation
class BankCardCreate(BankCardBase):
    """Schema for creating a new bank card"""
    user_id: Optional[int] = None


# Properties to receive on bank card update
class BankCardUpdate(BaseModel):
    """Schema for updating an existing bank card"""
    bank_name: Optional[str] = None
    card_number: Optional[str] = None
    card_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    sheba_number: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    user_id: Optional[int] = None

    @validator('card_number')
    def validate_card_number(cls, v):
        """Validate card_number if provided"""
        if v:
            v = v.replace(' ', '').replace('-', '')
            if not v.isdigit():
                raise ValueError('Card number must contain only digits')
            if not (16 <= len(v) <= 19):
                raise ValueError('Card number must be between 16 and 19 digits')
        return v

    @validator('sheba_number')
    def validate_sheba(cls, v):
        """Validate SHEBA format if provided"""
        if v:
            v = v.replace(' ', '')
            if not v.startswith('IR'):
                raise ValueError('SHEBA number must start with IR')
            if len(v) != 26:
                raise ValueError('SHEBA number must be 24 digits plus IR prefix')
        return v


# Properties shared by models stored in DB
class BankCardInDBBase(BankCardBase):
    """Base schema for bank card from database"""
    id: int
    user_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Properties to return to client
class BankCard(BankCardInDBBase):
    """Schema for bank card data returned to client"""
    # This class can add additional computed properties or exclude sensitive ones
    pass


# Properties stored in DB
class BankCardInDB(BankCardInDBBase):
    """Schema for bank card data stored in database"""
    pass


# Properties for bank card list view
class BankCardList(BaseModel):
    """Schema for returning a list of bank cards"""
    items: List[BankCard]
    total: int


# Properties for bank card detail view
class BankCardDetail(BankCardInDBBase):
    """Schema for detailed bank card view with additional information"""
    user_name: Optional[str] = None
    creator_name: Optional[str] = None 