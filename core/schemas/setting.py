"""Pydantic models (Schemas) for Settings."""

from pydantic import BaseModel, Field
from typing import Optional

class SettingBase(BaseModel):
    key: str = Field(..., max_length=100, description="Unique key for the setting")
    value: str = Field(..., description="Value of the setting")
    description: Optional[str] = Field(None, description="Description of the setting")

class SettingCreate(SettingBase):
    pass

class SettingUpdate(BaseModel):
    value: Optional[str] = None # Typically only value is updatable
    description: Optional[str] = None

class SettingInDBBase(SettingBase):
    id: int

    class Config:
        from_attributes = True

# Schema for representing a Setting in API responses
class Setting(SettingInDBBase):
    pass 