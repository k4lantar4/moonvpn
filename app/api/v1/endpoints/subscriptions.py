"""
Subscription API endpoints for MoonVPN.

This module contains the FastAPI router for subscription-related endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.db.repositories.factory import RepositoryFactory
from app.services.subscription import SubscriptionService
from app.models.subscription import Subscription, SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.models.plan import Plan

router = APIRouter()

@router.get("/me", response_model=SubscriptionResponse)
async def get_current_user_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SubscriptionResponse:
    """Get current user's active subscription."""
    factory = RepositoryFactory(db)
    service = SubscriptionService(factory.subscription_repository, factory.user_repository)
    subscription = await service.get_active_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return SubscriptionResponse.from_orm(subscription)

@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SubscriptionResponse:
    """Get subscription by ID."""
    factory = RepositoryFactory(db)
    service = SubscriptionService(factory.subscription_repository, factory.user_repository)
    subscription = await service.get_by_id(subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    if not current_user.is_admin and subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return SubscriptionResponse.from_orm(subscription)

@router.get("/user/{user_id}", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[SubscriptionResponse]:
    """Get all subscriptions for a user."""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = SubscriptionService(factory.subscription_repository, factory.user_repository)
    subscriptions = await service.get_by_user_id(user_id)
    
    return [SubscriptionResponse.from_orm(sub) for sub in subscriptions]

@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SubscriptionResponse:
    """Create a new subscription (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = SubscriptionService(factory.subscription_repository, factory.user_repository)
    subscription = await service.create(subscription_data)
    
    return SubscriptionResponse.from_orm(subscription)

@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    subscription_data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SubscriptionResponse:
    """Update a subscription (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = SubscriptionService(factory.subscription_repository, factory.user_repository)
    subscription = await service.update(subscription_id, subscription_data)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return SubscriptionResponse.from_orm(subscription)

@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a subscription (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = SubscriptionService(factory.subscription_repository, factory.user_repository)
    success = await service.delete(subscription_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return {"message": "Subscription deleted successfully"}

@router.post("/{subscription_id}/extend")
async def extend_subscription(
    subscription_id: int,
    days: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SubscriptionResponse:
    """Extend a subscription (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = SubscriptionService(factory.subscription_repository, factory.user_repository)
    subscription = await service.extend_subscription(subscription_id, days)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return SubscriptionResponse.from_orm(subscription)

@router.get("/{subscription_id}/stats")
async def get_subscription_stats(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get subscription statistics."""
    factory = RepositoryFactory(db)
    service = SubscriptionService(factory.subscription_repository, factory.user_repository)
    subscription = await service.get_by_id(subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    if not current_user.is_admin and subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await service.get_subscription_stats(subscription.user_id) 