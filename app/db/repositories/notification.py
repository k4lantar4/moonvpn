"""
Notification repository for MoonVPN.

This module contains the Notification repository class that handles database operations for notifications.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.db.models.notification import Notification
from app.models.notification import Notification as NotificationSchema

class NotificationRepository(BaseRepository[Notification]):
    """Notification repository class."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(Notification, session)
    
    async def get_by_user_id(self, user_id: int) -> List[Notification]:
        """Get all notifications for a user."""
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_type(self, notification_type: str) -> List[Notification]:
        """Get all notifications of a specific type."""
        query = select(self.model).where(self.model.type == notification_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_sender(self, sender_id: int) -> List[Notification]:
        """Get all notifications sent by a specific user."""
        query = select(self.model).where(self.model.sent_by == sender_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_from_schema(self, notification: NotificationSchema) -> Notification:
        """Create a notification from a Pydantic schema."""
        notification_data = notification.model_dump(exclude={"id"})
        return await self.create(notification_data)
    
    async def create_broadcast(
        self,
        message: str,
        sender_id: int
    ) -> Notification:
        """Create a broadcast notification."""
        notification_data = {
            "type": "broadcast",
            "message": message,
            "sent_by": sender_id,
            "created_at": datetime.utcnow()
        }
        return await self.create(notification_data)
    
    async def create_subscription_notification(
        self,
        user_id: int,
        plan_id: str
    ) -> Notification:
        """Create a subscription notification."""
        notification_data = {
            "type": "subscription",
            "user_id": user_id,
            "message": f"Your subscription has been activated! Plan: {plan_id}",
            "created_at": datetime.utcnow()
        }
        return await self.create(notification_data)
    
    async def create_expiration_notification(
        self,
        user_id: int,
        days_left: int
    ) -> Notification:
        """Create an expiration notification."""
        notification_data = {
            "type": "expiration",
            "user_id": user_id,
            "message": f"Your subscription will expire in {days_left} days",
            "created_at": datetime.utcnow()
        }
        return await self.create(notification_data)
    
    async def get_user_notification_stats(self, user_id: int) -> dict:
        """Get notification statistics for a user."""
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        notifications = list(result.scalars().all())
        
        total_notifications = len(notifications)
        notification_types = {}
        
        for notification in notifications:
            notification_types[notification.type] = notification_types.get(notification.type, 0) + 1
        
        return {
            "total_notifications": total_notifications,
            "notification_types": notification_types
        } 