"""Pydantic models (Schemas) for Plans and Plan Categories."""

from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
from decimal import Decimal
from datetime import datetime

# --- Plan Category Schemas ---

class PlanCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    sorting_order: Optional[int] = None

class PlanCategoryCreate(PlanCategoryBase):
    pass

class PlanCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    sorting_order: Optional[int] = None

class PlanCategoryInDBBase(PlanCategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Replace orm_mode

# Optional: Schema for response, potentially including related plans
class PlanCategory(PlanCategoryInDBBase):
    pass # Add relationships later if needed

# --- Plan Schemas ---

class PlanBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    days: int = Field(..., gt=0)
    traffic: int = Field(..., gt=0) # Assuming GB, so positive integer
    max_clients: Optional[int] = Field(None, gt=0)
    protocols: Optional[str] = Field(None, max_length=255)
    features: Optional[str] = None
    category_id: int
    is_featured: Optional[bool] = False
    is_active: Optional[bool] = True
    sorting_order: Optional[int] = None

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    days: Optional[int] = Field(None, gt=0)
    traffic: Optional[int] = Field(None, gt=0)
    max_clients: Optional[int] = Field(None, gt=0)
    protocols: Optional[str] = Field(None, max_length=255)
    features: Optional[str] = None
    category_id: Optional[int] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    sorting_order: Optional[int] = None

class PlanInDBBase(PlanBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Replace orm_mode

# Schema for representing a Plan in API responses, potentially including category info
class Plan(PlanInDBBase):
    category: Optional[PlanCategory] = None # Include nested category info

# Update PlanCategory to include nested plans if needed for full representation
class PlanCategoryWithPlans(PlanCategory):
    plans: List[Plan] = [] 