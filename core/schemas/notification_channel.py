"""Pydantic models (Schemas) for Notification Channels."""

from pydantic import BaseModel
from typing import Optional
from enum import Enum

# Assuming NotificationEvent enum is defined in models
# from core.database.models.notification_channel import NotificationEvent
class NotificationEvent(str, Enum):
    NEW_USER = "NEW_USER"
    PAYMENT_VERIFICATION = "PAYMENT_VERIFICATION"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    PANEL_DOWN = "PANEL_DOWN"
    PANEL_RECOVERED = "PANEL_RECOVERED"
    LOW_BALANCE = "LOW_BALANCE"
    EXPIRY_WARNING = "EXPIRY_WARNING"
    DB_BACKUP_SUCCESS = "DB_BACKUP_SUCCESS"
    DB_BACKUP_FAILURE = "DB_BACKUP_FAILURE"
    CRITICAL_ERROR = "CRITICAL_ERROR"
    SALES_REPORT = "SALES_REPORT"
    USAGE_REPORT = "USAGE_REPORT"
    # Add other events as needed from requirements

class NotificationChannelBase(BaseModel):
    name: str
    channel_id: int # Telegram Channel ID (should be bigint in db, handle large numbers)
    event: NotificationEvent
    is_active: bool = True

class NotificationChannelCreate(NotificationChannelBase):
    pass

class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = None
    channel_id: Optional[int] = None
    event: Optional[NotificationEvent] = None
    is_active: Optional[bool] = None

class NotificationChannelInDBBase(NotificationChannelBase):
    id: int

    class Config:
        from_attributes = True

# Schema for representing a NotificationChannel in API responses
class NotificationChannel(NotificationChannelInDBBase):
    pass 