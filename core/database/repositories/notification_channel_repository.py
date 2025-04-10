"""Repository for NotificationChannel model operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Sequence

from core.database.models.notification_channel import NotificationChannel, NotificationEvent # Assuming models
from .base_repo import BaseRepository
# Assuming schemas exist or create them in core/schemas/notification_channel.py
from core.schemas.notification_channel import NotificationChannelCreate, NotificationChannelUpdate

class NotificationChannelRepository(BaseRepository[NotificationChannel, NotificationChannelCreate, NotificationChannelUpdate]):
    """Provides data access methods for NotificationChannel entities."""

    def __init__(self):
        # Do not store session
        super().__init__(model=NotificationChannel) # Pass model correctly

    async def get_by_event(self, db_session: AsyncSession, event: NotificationEvent) -> Sequence[NotificationChannel]:
        """Get all active notification channels for a specific event type."""
        stmt = (
            select(self.model)
            .where(self.model.event == event)
            .where(self.model.is_active == True)
            .order_by(self.model.name) # Or another relevant field
        )
        result = await db_session.execute(stmt) # Use passed session
        return result.scalars().all()

    async def get_by_channel_id(self, db_session: AsyncSession, channel_id: int) -> Optional[NotificationChannel]:
        """Get a notification channel by its Telegram channel ID."""
        stmt = select(self.model).where(self.model.channel_id == channel_id)
        result = await db_session.execute(stmt) # Use passed session
        return result.scalars().first()

# Need to create core/schemas/notification_channel.py
# Example:
# from pydantic import BaseModel
# from typing import Optional
# from enum import Enum
#
# class NotificationEvent(str, Enum):
#     NEW_USER = "NEW_USER"
#     PAYMENT_VERIFICATION = "PAYMENT_VERIFICATION"
#     PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
#     PANEL_DOWN = "PANEL_DOWN"
#     LOW_BALANCE = "LOW_BALANCE"
#     DB_BACKUP = "DB_BACKUP"
#     # Add other events
#
# class NotificationChannelBase(BaseModel):
#     name: str
#     channel_id: int # Telegram Channel ID
#     event: NotificationEvent
#     is_active: bool = True
#
# class NotificationChannelCreate(NotificationChannelBase):
#     pass
#
# class NotificationChannelUpdate(BaseModel):
#     name: Optional[str] = None
#     channel_id: Optional[int] = None
#     event: Optional[NotificationEvent] = None
#     is_active: Optional[bool] = None
#
# class NotificationChannelInDB(NotificationChannelBase):
#     id: int
#     class Config:
#         from_attributes = True 