"""Model for Notification Channels."""

from datetime import datetime
import enum
from typing import Optional

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, func, Enum as SQLAlchemyEnum, BigInteger
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database.session import Base

# Define the Enum for notification events
class NotificationEvent(str, enum.Enum):
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
    # Add other events from requirements

class NotificationChannel(Base):
    """Model for storing Telegram channel IDs for notifications using Mapped syntax."""
    
    __tablename__ = "notification_channels"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True) # e.g., 'ADMIN', 'PAYMENT', 'LOG', 'ALERT'
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True) # Telegram channel ID (can be string or number)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notification_types: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Store JSON array? e.g., ['new_user', 'panel_down']
    event: Mapped[NotificationEvent] = mapped_column(SQLAlchemyEnum(NotificationEvent), nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)

    def __repr__(self) -> str:
        return f"<NotificationChannel(id={self.id}, name='{self.name}', channel_id='{self.channel_id}')>" 