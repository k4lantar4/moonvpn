"""
Template test schemas for system health monitoring.

This module defines the Pydantic schemas for template testing data validation.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel

class TemplateTestBase(BaseModel):
    """Base schema for template test data."""
    parameters: Dict[str, Any]

class TemplateTestCreate(TemplateTestBase):
    """Schema for creating a new template test."""
    template_id: int

class TemplateTestResult(TemplateTestBase):
    """Schema for template test results."""
    id: int
    template_id: int
    status: str
    message: str
    execution_time: float
    errors: Optional[Dict[str, str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True 