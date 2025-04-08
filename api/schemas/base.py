from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

class BaseSchema(BaseModel):
    """Base schema for all models with common fields"""
    
    class Config:
        """Config for the base schema"""
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class TimestampedSchema(BaseSchema):
    """Schema with creation and update timestamps"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
class IDSchema(BaseSchema):
    """Schema with ID field"""
    id: int 