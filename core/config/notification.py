"""
Notification service for MoonVPN.

This module contains the notification service implementation using the repository pattern.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status

from app.db.repositories.notification import NotificationRepository
from app.db.repositories.user import UserRepository
from app.models.notification import Notification, NotificationCreate, NotificationUpdate

class NotificationService:
    """Notification service class."""
    
    def __init__(
        self,
        notification_repository: NotificationRepository,
        user_repository: UserRepository
    ):
        """Initialize service."""
        self.notification_repository = notification_repository
        self.user_repository = user_repository
    
    async def get_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get a notification by ID."""
        return await self.notification_repository.get(notification_id)
    
    async def get_by_user_id(self, user_id: int) -> List[Notification]:
        """Get all notifications for a user."""
        return await self.notification_repository.get_by_user_id(user_id)
    
    async def get_by_type(self, notification_type: str) -> List[Notification]:
        """Get all notifications of a specific type."""
        return await self.notification_repository.get_by_type(notification_type)
    
    async def get_by_sender(self, sender_id: int) -> List[Notification]:
        """Get all notifications sent by a specific user."""
        return await self.notification_repository.get_by_sender(sender_id)
    
    async def create(self, notification_data: NotificationCreate) -> Notification:
        """Create a new notification."""
        # Check if user exists
        if notification_data.user_id:
            user = await self.user_repository.get(notification_data.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        # Create notification
        notification_dict = notification_data.model_dump()
        notification_dict["created_at"] = datetime.utcnow()
        
        return await self.notification_repository.create(notification_dict)
    
    async def update(self, notification_id: int, notification_data: NotificationUpdate) -> Optional[Notification]:
        """Update a notification."""
        notification = await self.get_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        update_data = notification_data.model_dump(exclude_unset=True)
        return await self.notification_repository.update(db_obj=notification, obj_in=update_data)
    
    async def delete(self, notification_id: int) -> bool:
        """Delete a notification."""
        notification = await self.get_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return await self.notification_repository.delete(notification)
    
    async def create_broadcast(self, message: str, sender_id: int) -> Notification:
        """Create a broadcast notification."""
        # Check if sender exists and is admin
        sender = await self.user_repository.get(sender_id)
        if not sender or not sender.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create broadcast notifications"
            )
        
        return await self.notification_repository.create_broadcast(message, sender_id)
    
    async def create_subscription_notification(self, user_id: int, plan_id: str) -> Notification:
        """Create a subscription notification."""
        # Check if user exists
        user = await self.user_repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return await self.notification_repository.create_subscription_notification(user_id, plan_id)
    
    async def create_expiration_notification(self, user_id: int, days_left: int) -> Notification:
        """Create an expiration notification."""
        # Check if user exists
        user = await self.user_repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return await self.notification_repository.create_expiration_notification(user_id, days_left)
    
    async def get_notification_stats(self, user_id: int) -> dict:
        """Get notification statistics for a user."""
        return await self.notification_repository.get_user_notification_stats(user_id)
    
    async def mark_as_read(self, notification_id: int) -> Optional[Notification]:
        """Mark a notification as read."""
        notification = await self.get_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return await self.update(notification_id, NotificationUpdate(is_read=True))
    
    async def mark_all_as_read(self, user_id: int) -> bool:
        """Mark all notifications as read for a user."""
        notifications = await self.get_by_user_id(user_id)
        for notification in notifications:
            await self.mark_as_read(notification.id)
        return True 