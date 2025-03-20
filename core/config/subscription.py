"""
Subscription service for MoonVPN.

This module contains the subscription service implementation using the repository pattern.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.db.repositories.subscription import SubscriptionRepository
from app.db.repositories.user import UserRepository
from app.models.subscription import Subscription, SubscriptionCreate, SubscriptionUpdate
from app.models.plan import Plan

class SubscriptionService:
    """Subscription service class."""
    
    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        user_repository: UserRepository
    ):
        """Initialize service."""
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
    
    async def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get a subscription by ID."""
        return await self.subscription_repository.get(subscription_id)
    
    async def get_by_user_id(self, user_id: int) -> List[Subscription]:
        """Get all subscriptions for a user."""
        return await self.subscription_repository.get_by_user_id(user_id)
    
    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get a user's active subscription."""
        return await self.subscription_repository.get_active_subscription(user_id)
    
    async def get_expiring_subscriptions(self, days: int) -> List[Subscription]:
        """Get subscriptions expiring in the given number of days."""
        return await self.subscription_repository.get_expiring_subscriptions(days)
    
    async def create(self, subscription_data: SubscriptionCreate) -> Subscription:
        """Create a new subscription."""
        # Check if user exists
        user = await self.user_repository.get(subscription_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user already has an active subscription
        active_subscription = await self.get_active_subscription(subscription_data.user_id)
        if active_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active subscription"
            )
        
        # Create subscription
        subscription_dict = subscription_data.model_dump()
        subscription_dict["created_at"] = datetime.utcnow()
        subscription_dict["status"] = "active"
        
        return await self.subscription_repository.create(subscription_dict)
    
    async def update(self, subscription_id: int, subscription_data: SubscriptionUpdate) -> Optional[Subscription]:
        """Update a subscription."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        update_data = subscription_data.model_dump(exclude_unset=True)
        return await self.subscription_repository.update(db_obj=subscription, obj_in=update_data)
    
    async def delete(self, subscription_id: int) -> bool:
        """Delete a subscription."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        return await self.subscription_repository.delete(subscription)
    
    async def update_status(self, subscription_id: int, status: str) -> Optional[Subscription]:
        """Update a subscription's status."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        return await self.subscription_repository.update_status(subscription_id, status)
    
    async def extend_subscription(self, subscription_id: int, days: int) -> Optional[Subscription]:
        """Extend a subscription by the given number of days."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        return await self.subscription_repository.extend_subscription(subscription_id, days)
    
    async def get_subscription_stats(self, user_id: int) -> dict:
        """Get subscription statistics for a user."""
        subscriptions = await self.get_by_user_id(user_id)
        
        total_subscriptions = len(subscriptions)
        active_subscriptions = sum(1 for sub in subscriptions if sub.status == "active")
        expired_subscriptions = sum(1 for sub in subscriptions if sub.status == "expired")
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "current_plan": subscriptions[-1].plan_id if subscriptions else None
        } 