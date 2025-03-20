"""
Recovery schemas for system health monitoring.

This module defines the Pydantic schemas for validating recovery action data
in the system.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class RecoveryActionBase(BaseModel):
    """Base schema for recovery action data."""
    component: str = Field(..., description="The system component requiring recovery")
    failure_type: str = Field(..., description="Type of failure encountered")
    strategy: str = Field(..., description="Recovery strategy to apply")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters for the recovery action")

class RecoveryActionCreate(RecoveryActionBase):
    """Schema for creating a new recovery action."""
    pass

class RecoveryActionUpdate(BaseModel):
    """Schema for updating an existing recovery action."""
    status: Optional[str] = Field(None, description="New status of the recovery action")
    result: Optional[Dict[str, Any]] = Field(None, description="Result of the recovery action")
    error_message: Optional[str] = Field(None, description="Error message if the action failed")
    started_at: Optional[datetime] = Field(None, description="When the action started")
    completed_at: Optional[datetime] = Field(None, description="When the action completed")

class RecoveryAction(RecoveryActionBase):
    """Schema for recovery action responses."""
    id: int = Field(..., description="Unique identifier of the recovery action")
    status: str = Field(..., description="Current status of the recovery action")
    result: Optional[Dict[str, Any]] = Field(None, description="Result of the recovery action")
    created_at: datetime = Field(..., description="When the action was created")
    started_at: Optional[datetime] = Field(None, description="When the action started")
    completed_at: Optional[datetime] = Field(None, description="When the action completed")
    error_message: Optional[str] = Field(None, description="Error message if the action failed")

    class Config:
        """Pydantic configuration."""
        orm_mode = True 