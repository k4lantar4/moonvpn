"""
Scheduler schemas for system health monitoring.

This module defines the Pydantic schemas for scheduling recovery actions
and managing scheduled tasks.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ScheduleParams(BaseModel):
    """Base schema for schedule parameters."""
    schedule_type: str = Field(..., description="Type of schedule (cron, interval, date)")
    schedule_params: Dict[str, Any] = Field(..., description="Schedule-specific parameters")

class CronScheduleParams(ScheduleParams):
    """Schema for cron-based scheduling."""
    schedule_type: str = Field("cron", description="Schedule type is cron")
    schedule_params: Dict[str, Any] = Field(
        ...,
        description="Cron parameters (year, month, day, week, day_of_week, hour, minute, second)",
        example={
            "hour": "*/4",  # Every 4 hours
            "minute": "0"
        }
    )

class IntervalScheduleParams(ScheduleParams):
    """Schema for interval-based scheduling."""
    schedule_type: str = Field("interval", description="Schedule type is interval")
    schedule_params: Dict[str, Any] = Field(
        ...,
        description="Interval parameters (weeks, days, hours, minutes, seconds)",
        example={
            "hours": 4  # Every 4 hours
        }
    )

class DateScheduleParams(ScheduleParams):
    """Schema for date-based scheduling."""
    schedule_type: str = Field("date", description="Schedule type is date")
    schedule_params: Dict[str, Any] = Field(
        ...,
        description="Date parameters (date)",
        example={
            "date": "2024-03-25T00:00:00Z"  # Specific date and time
        }
    )

class ScheduledAction(BaseModel):
    """Schema for scheduled action details."""
    job_id: str = Field(..., description="Unique identifier of the scheduled job")
    action_id: str = Field(..., description="ID of the recovery action")
    next_run_time: Optional[datetime] = Field(None, description="Next scheduled run time")
    trigger: str = Field(..., description="Schedule trigger description")
    action: Dict[str, Any] = Field(..., description="Recovery action details")

class ScheduleResponse(BaseModel):
    """Schema for schedule operation response."""
    job_id: str = Field(..., description="ID of the scheduled job")
    message: str = Field(..., description="Operation result message")
    next_run_time: Optional[datetime] = Field(None, description="Next scheduled run time") 