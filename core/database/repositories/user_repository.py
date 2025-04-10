from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Assuming schemas exist in a 'schemas' directory, adjust import as needed
# from schemas.user import UserCreate, UserUpdate # Example schema import
from pydantic import BaseModel # Placeholder for schemas

from .base_repo import BaseRepository # Import from base_repo.py
from core.database.models import User

# Define Placeholder Schemas if real ones aren't ready
class UserCreate(BaseModel): # Placeholder
    telegram_id: int
    role_id: int
    # ... other required fields
    username: Optional[str] = None
    full_name: Optional[str] = None

class UserUpdate(BaseModel): # Placeholder
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_banned: Optional[bool] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
    balance: Optional[float] = None
    # ... other optional fields


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self):
        # Pass the User model to the parent class
        super().__init__(User)

    async def get_by_telegram_id(self, db_session: AsyncSession, *, telegram_id: int) -> Optional[User]:
        """Get a user by their Telegram ID."""
        statement = select(self._model).where(self._model.telegram_id == telegram_id)
        result = await db_session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_username(self, db_session: AsyncSession, *, username: str) -> Optional[User]:
        """Get a user by their username."""
        # Ensure case-insensitive comparison if needed (depends on DB collation)
        statement = select(self._model).where(self._model.username == username)
        # For case-insensitive:
        # from sqlalchemy import func
        # statement = select(self._model).where(func.lower(self._model.username) == func.lower(username))
        result = await db_session.execute(statement)
        return result.scalar_one_or_none()

    # create, get_by_id, update, delete etc. are inherited from BaseRepository
    # No need to redefine them unless specific logic is needed for User 