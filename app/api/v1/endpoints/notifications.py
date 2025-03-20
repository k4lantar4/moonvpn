"""
Notification API endpoints for MoonVPN.

This module contains the FastAPI router for notification-related endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.db.repositories.factory import RepositoryFactory
from app.services.notification import NotificationService
from app.models.notification import Notification, NotificationCreate, NotificationUpdate, NotificationResponse
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=List[NotificationResponse])
async def get_current_user_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[NotificationResponse]:
    """Get current user's notifications."""
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notifications = await service.get_by_user_id(current_user.id)
    
    return [NotificationResponse.from_orm(notification) for notification in notifications]

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Get notification by ID."""
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notification = await service.get_by_id(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if not current_user.is_admin and notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return NotificationResponse.from_orm(notification)

@router.get("/type/{notification_type}", response_model=List[NotificationResponse])
async def get_notifications_by_type(
    notification_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[NotificationResponse]:
    """Get all notifications of a specific type (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notifications = await service.get_by_type(notification_type)
    
    return [NotificationResponse.from_orm(notification) for notification in notifications]

@router.get("/sender/{sender_id}", response_model=List[NotificationResponse])
async def get_notifications_by_sender(
    sender_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[NotificationResponse]:
    """Get all notifications sent by a specific user (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notifications = await service.get_by_sender(sender_id)
    
    return [NotificationResponse.from_orm(notification) for notification in notifications]

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Create a new notification (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notification = await service.create(notification_data)
    
    return NotificationResponse.from_orm(notification)

@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_data: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Update a notification (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notification = await service.update(notification_id, notification_data)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return NotificationResponse.from_orm(notification)

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a notification (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    success = await service.delete(notification_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification deleted successfully"}

@router.post("/broadcast")
async def create_broadcast(
    message: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Create a broadcast notification (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notification = await service.create_broadcast(message, current_user.id)
    
    return NotificationResponse.from_orm(notification)

@router.post("/subscription/{user_id}")
async def create_subscription_notification(
    user_id: int,
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Create a subscription notification (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notification = await service.create_subscription_notification(user_id, plan_id)
    
    return NotificationResponse.from_orm(notification)

@router.post("/expiration/{user_id}")
async def create_expiration_notification(
    user_id: int,
    days_left: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Create an expiration notification (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notification = await service.create_expiration_notification(user_id, days_left)
    
    return NotificationResponse.from_orm(notification)

@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Mark a notification as read."""
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notification = await service.get_by_id(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if not current_user.is_admin and notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_notification = await service.mark_as_read(notification_id)
    return NotificationResponse.from_orm(updated_notification)

@router.post("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Mark all notifications as read."""
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    success = await service.mark_all_as_read(current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )
    
    return {"message": "All notifications marked as read"}

@router.get("/{notification_id}/stats")
async def get_notification_stats(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get notification statistics."""
    factory = RepositoryFactory(db)
    service = NotificationService(factory.notification_repository, factory.user_repository)
    notification = await service.get_by_id(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if not current_user.is_admin and notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await service.get_notification_stats(notification.user_id) 