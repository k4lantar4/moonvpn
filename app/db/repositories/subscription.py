"""
Subscription repository for MoonVPN.

This module contains the Subscription repository class that handles database operations for subscriptions.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.db.models.subscription import Subscription
from app.models.subscription import Subscription as SubscriptionSchema

class SubscriptionRepository(BaseRepository[Subscription]):
    """Subscription repository class."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(Subscription, session)
    
    async def get_by_user_id(self, user_id: int) -> List[Subscription]:
        """Get all subscriptions for a user."""
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get a user's active subscription."""
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.status == "active",
            self.model.end_date > datetime.utcnow()
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_expiring_subscriptions(self, days: int) -> List[Subscription]:
        """Get subscriptions expiring in the given number of days."""
        expiry_date = datetime.utcnow() + datetime.timedelta(days=days)
        query = select(self.model).where(
            self.model.status == "active",
            self.model.end_date <= expiry_date
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_from_schema(self, subscription: SubscriptionSchema) -> Subscription:
        """Create a subscription from a Pydantic schema."""
        subscription_data = subscription.model_dump(exclude={"id"})
        return await self.create(subscription_data)
    
    async def update_status(self, subscription_id: int, status: str) -> Optional[Subscription]:
        """Update a subscription's status."""
        subscription = await self.get(subscription_id)
        if subscription:
            return await self.update(db_obj=subscription, obj_in={"status": status})
        return None
    
    async def extend_subscription(
        self,
        subscription_id: int,
        days: int
    ) -> Optional[Subscription]:
        """Extend a subscription by the given number of days."""
        subscription = await self.get(subscription_id)
        if subscription:
            new_end_date = subscription.end_date + datetime.timedelta(days=days)
            return await self.update(
                db_obj=subscription,
                obj_in={"end_date": new_end_date}
            )
        return None 