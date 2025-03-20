"""
Pydantic schemas for health check data validation.
"""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field

from app.core.models.health import HealthStatus

class HealthCheckBase(BaseModel):
    """Base schema for health check data."""
    component: str = Field(..., description="Component being checked")
    status: HealthStatus = Field(..., description="Health status of the component")
    message: str = Field(..., description="Human-readable status message")
    metrics: Optional[Dict] = Field(None, description="Component-specific metrics")

class HealthCheckCreate(HealthCheckBase):
    """Schema for creating a new health check."""
    pass

class HealthCheckUpdate(BaseModel):
    """Schema for updating an existing health check."""
    status: Optional[HealthStatus] = None
    message: Optional[str] = None
    metrics: Optional[Dict] = None

class HealthCheck(HealthCheckBase):
    """Schema for health check response."""
    id: int
    last_check: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True

class SystemStatus(BaseModel):
    """Schema for system-wide health status."""
    status: Dict[str, HealthStatus] = Field(..., description="Status of all system components")
    last_updated: datetime = Field(default_factory=datetime.utcnow) 