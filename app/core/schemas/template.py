"""
Template schemas for system health monitoring.

This module defines the Pydantic schemas for recovery action templates
and template categories.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class TemplateCategoryBase(BaseModel):
    """Base schema for template categories."""
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")

class TemplateCategoryCreate(TemplateCategoryBase):
    """Schema for creating template categories."""
    pass

class TemplateCategoryUpdate(TemplateCategoryBase):
    """Schema for updating template categories."""
    name: Optional[str] = None
    description: Optional[str] = None

class TemplateCategory(TemplateCategoryBase):
    """Schema for template category responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ValidationRuleBase(BaseModel):
    """Base schema for template validation rules."""
    field: str = Field(..., description="Field to validate")
    type: str = Field(..., description="Validation type (required, min, max, pattern, custom)")
    value: str = Field(..., description="Validation value")
    message: str = Field(..., description="Error message")
    is_active: bool = Field(True, description="Whether the rule is active")

class ValidationRuleCreate(ValidationRuleBase):
    """Schema for creating validation rules."""
    template_id: int = Field(..., description="Template ID")

class ValidationRuleUpdate(ValidationRuleBase):
    """Schema for updating validation rules."""
    field: Optional[str] = None
    type: Optional[str] = None
    value: Optional[str] = None
    message: Optional[str] = None
    is_active: Optional[bool] = None

class ValidationRule(ValidationRuleBase):
    """Schema for validation rule responses."""
    id: int
    template_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RecoveryTemplateBase(BaseModel):
    """Base schema for recovery templates."""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category_id: Optional[int] = Field(None, description="Category ID")
    strategy: str = Field(..., description="Recovery strategy")
    parameters: Dict[str, Any] = Field(..., description="Template parameters")
    is_active: bool = Field(True, description="Template active status")
    validation_rules: Optional[List[ValidationRuleBase]] = Field(None, description="Template validation rules")

class RecoveryTemplateCreate(RecoveryTemplateBase):
    """Schema for creating recovery templates."""
    pass

class RecoveryTemplateUpdate(RecoveryTemplateBase):
    """Schema for updating recovery templates."""
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    strategy: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    validation_rules: Optional[List[ValidationRuleBase]] = None

class RecoveryTemplate(RecoveryTemplateBase):
    """Schema for recovery template responses."""
    id: int
    category: Optional[TemplateCategory] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 