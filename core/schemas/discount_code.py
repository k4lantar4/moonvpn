"""Pydantic schemas for DiscountCode model serialization."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator, validator
from enum import Enum

from core.database.models.discount_code import DiscountType

class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"

class DiscountCodeBase(BaseModel):
    """Base schema for discount code data."""
    code: str = Field(..., description="Unique discount code")
    description: Optional[str] = Field(None, description="Description of the discount code")
    discount_type: DiscountType = Field(..., description="Type of discount (percentage or fixed amount)")
    discount_value: float = Field(..., description="Value of the discount (percentage or amount)")
    start_date: datetime = Field(..., description="Start date of validity")
    end_date: datetime = Field(..., description="End date of validity")
    max_uses: Optional[int] = Field(None, description="Maximum number of times this code can be used")
    current_uses: int = Field(0, description="Current number of times this code has been used")
    is_active: bool = Field(True, description="Whether the discount code is currently active")
    min_order_amount: Optional[float] = Field(None, description="Minimum order amount required to use this code")
    max_discount_amount: Optional[float] = Field(None, description="Maximum discount amount (for percentage discounts)")

    @validator('discount_value')
    def validate_discount_value(cls, v, values):
        if 'discount_type' in values and values['discount_type'] == DiscountType.PERCENTAGE and (v <= 0 or v > 100):
            raise ValueError('Percentage discount must be between 0 and 100')
        if v < 0:
            raise ValueError('Discount value cannot be negative')
        return v

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class DiscountCodeCreate(DiscountCodeBase):
    """Schema for creating a new discount code."""
    created_by_id: Optional[int] = None

class DiscountCodeUpdate(BaseModel):
    """Schema for updating an existing discount code."""
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_uses: Optional[int] = None
    is_active: Optional[bool] = None
    min_order_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    
    @model_validator(mode='after')
    def validate_discount_value(self) -> 'DiscountCodeUpdate':
        """Validate discount value based on type."""
        if (self.discount_type is not None and 
            self.discount_value is not None and 
            self.discount_type == DiscountType.PERCENTAGE and 
            self.discount_value > 100):
            raise ValueError('Percentage discount cannot exceed 100%')
        
        return self

class DiscountCodeInDB(DiscountCodeBase):
    """Schema for a discount code as stored in the database."""
    id: int
    used_count: Optional[int] = 0
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DiscountCodeRead(DiscountCodeInDB):
    """Schema for reading discount code data."""
    pass

class DiscountCodeValidationResult(BaseModel):
    """Schema for discount code validation result."""
    is_valid: bool
    message: str
    discount_code: Optional[DiscountCodeRead] = None
    discount_amount: Optional[Decimal] = None
    
class DiscountCodeWithStats(DiscountCodeRead):
    """Schema for discount code with usage statistics."""
    total_used: int = 0
    total_discount_amount: Decimal = Decimal(0)
    
    class Config:
        from_attributes = True

class DiscountCodeDB(DiscountCodeBase):
    """Schema for discount code as stored in database."""
    id: int = Field(..., description="Unique identifier for the discount code")
    created_at: datetime = Field(..., description="Timestamp when the discount code was created")
    updated_at: datetime = Field(..., description="Timestamp when the discount code was last updated")

    class Config:
        orm_mode = True

class DiscountCodePublic(DiscountCodeBase):
    """Schema for public discount code information (for users)."""
    id: int
    
    class Config:
        orm_mode = True

class DiscountCodeWithUsage(DiscountCodeDB):
    """Schema for discount code with usage statistics."""
    remaining_uses: Optional[int] = Field(None, description="Remaining number of times this code can be used")
    is_valid: bool = Field(True, description="Whether the code is currently valid for use")
    days_until_expiry: Optional[int] = Field(None, description="Number of days until the code expires")
    
    class Config:
        orm_mode = True 