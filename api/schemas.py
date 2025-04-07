"""
API Schemas

This module defines Pydantic models for API request and response validation.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator


# Panel Schemas
class PanelBase(BaseModel):
    """Base schema for panels."""
    name: str = Field(..., description="Unique name for the panel", min_length=3, max_length=100)
    url: str = Field(..., description="Panel URL including protocol and port")
    username: str = Field(..., description="Admin username for the panel")
    login_path: Optional[str] = Field(default="/login", description="Path for login endpoint")
    notes: Optional[str] = Field(default=None, description="Optional notes about the panel")
    is_active: Optional[bool] = Field(default=True, description="Whether the panel is active")
    timeout: Optional[float] = Field(default=10.0, description="Request timeout in seconds")
    max_retries: Optional[int] = Field(default=3, description="Maximum retry attempts for requests")
    retry_delay: Optional[float] = Field(default=1.0, description="Delay between retries in seconds")


class PanelCreate(PanelBase):
    """Schema for creating a new panel."""
    password: str = Field(..., description="Admin password for the panel")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class PanelUpdate(BaseModel):
    """Schema for updating a panel."""
    name: Optional[str] = Field(None, description="Unique name for the panel", min_length=3, max_length=100)
    url: Optional[str] = Field(None, description="Panel URL including protocol and port")
    username: Optional[str] = Field(None, description="Admin username for the panel")
    password: Optional[str] = Field(None, description="Admin password for the panel")
    login_path: Optional[str] = Field(None, description="Path for login endpoint")
    notes: Optional[str] = Field(None, description="Optional notes about the panel")
    is_active: Optional[bool] = Field(None, description="Whether the panel is active")
    timeout: Optional[float] = Field(None, description="Request timeout in seconds")
    max_retries: Optional[int] = Field(None, description="Maximum retry attempts for requests")
    retry_delay: Optional[float] = Field(None, description="Delay between retries in seconds")
    
    @validator('url')
    def validate_url(cls, v):
        if v is None:
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class PanelHealthCheckResponse(BaseModel):
    """Schema for panel health check response."""
    id: int
    panel_id: int
    status: str
    response_time_ms: Optional[int]
    details: Optional[Dict[str, Any]]
    checked_at: datetime
    
    class Config:
        orm_mode = True


class PanelResponse(PanelBase):
    """Schema for panel response."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_connected_at: Optional[datetime] = None
    latest_health_check: Optional[PanelHealthCheckResponse] = None
    
    # Don't include sensitive data in responses
    password: Optional[str] = Field(None, exclude=True)
    
    class Config:
        orm_mode = True


class PanelDetailResponse(PanelResponse):
    """Schema for detailed panel response including recent health checks."""
    health_checks: List[PanelHealthCheckResponse] = Field(default_factory=list)


# Client Management Schemas
class ClientCreate(BaseModel):
    """Schema for creating a client on a panel."""
    email: str = Field(..., description="Client email (used as identifier)")
    id: Optional[str] = Field(None, description="Client UUID (generated if not provided)")
    flow: Optional[str] = Field(None, description="Flow setting for the client")
    limit: Optional[int] = Field(None, description="Data transfer limit in bytes")
    total_gb: Optional[int] = Field(None, description="Total GB allowed (alternative to limit)")
    expire_days: Optional[int] = Field(None, description="Number of days until expiration")
    enable: Optional[bool] = Field(True, description="Whether the client is enabled")
    
    class Config:
        extra = "allow"  # Allow additional fields for different protocols


class ClientResponse(BaseModel):
    """Schema for client response."""
    id: str
    email: str
    inbound_id: int
    enable: bool
    traffic: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class HealthCheckRequest(BaseModel):
    """Schema for manual health check request."""
    panel_id: Optional[int] = Field(None, description="Panel ID to check (None for all panels)")


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    panel_id: int
    panel_name: str
    health_check: Dict[str, Any]


class PanelStatsResponse(BaseModel):
    """Schema for panel statistics response."""
    total_panels: int
    active_panels: int
    inactive_panels: int
    healthy_panels: int
    unhealthy_panels: int
    last_checked: Optional[datetime] = None
