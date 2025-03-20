"""
User repository for MoonVPN.

This module contains the User repository class that handles database operations for users.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.db.models.user import User
from app.models.user import User as UserSchema

class UserRepository(BaseRepository[User]):
    """User repository class."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(User, session)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get a user by Telegram ID."""
        query = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        query = select(self.model).where(self.model.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_users(self) -> List[User]:
        """Get all active users."""
        query = select(self.model).where(self.model.status == "active")
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_from_schema(self, user: UserSchema) -> User:
        """Create a user from a Pydantic schema."""
        user_data = user.model_dump(exclude={"id"})
        return await self.create(user_data)
    
    async def update_status(self, user_id: int, status: str) -> Optional[User]:
        """Update a user's status."""
        user = await self.get(user_id)
        if user:
            return await self.update(db_obj=user, obj_in={"status": status})
        return None 