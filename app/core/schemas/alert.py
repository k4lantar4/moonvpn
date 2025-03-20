"""
Pydantic schemas for alert data validation.
"""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field

from app.core.models.alert import AlertSeverity, AlertStatus

class AlertBase(BaseModel):
    """Base schema for alert data."""
    component: str = Field(..., description="Component generating the alert")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    metrics: Optional[Dict] = Field(None, description="Component-specific metrics")

class AlertCreate(AlertBase):
    """Schema for creating a new alert."""
    pass

class AlertUpdate(BaseModel):
    """Schema for updating an existing alert."""
    status: Optional[AlertStatus] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class Alert(AlertBase):
    """Schema for alert response."""
    id: int
    status: AlertStatus
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True

class AlertRuleBase(BaseModel):
    """Base schema for alert rule data."""
    component: str = Field(..., description="Component to monitor")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    condition: Dict = Field(..., description="Alert condition logic")
    is_active: bool = Field(True, description="Whether the rule is active")

class AlertRuleCreate(AlertRuleBase):
    """Schema for creating a new alert rule."""
    pass

class AlertRuleUpdate(BaseModel):
    """Schema for updating an existing alert rule."""
    description: Optional[str] = None
    condition: Optional[Dict] = None
    is_active: Optional[bool] = None

class AlertRule(AlertRuleBase):
    """Schema for alert rule response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True 