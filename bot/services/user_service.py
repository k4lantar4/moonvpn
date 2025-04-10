"""
User Service

This module provides user-related service functions.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database.models.user import User
from core.database.repositories.user_repository import UserRepository, UserCreate
from core.database.repositories.role_repository import RoleRepository
from core.security import verify_password, get_password_hash
from core.exceptions import UserNotFoundError, CoreError, NotFoundError, BusinessLogicError, RoleNotFoundException, DuplicateUserException
from core.config import settings

# Get logger instance for this module
logger = logging.getLogger(__name__)

# Define the default role name
DEFAULT_ROLE_NAME = "USER"

class UserService:
    """User service class for handling user-related operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize UserService with required dependencies.
        
        Args:
            db: Database session to be used for database operations
        """
        self.db = db
        # Instantiate repositories
        self.user_repo = UserRepository()
        self.role_repo = RoleRepository()

    async def get_or_create_user(
        self,
        *,
        user_id: int,
        username: str,
        full_name: str
    ) -> Tuple[User, bool]:
        """
        Gets a user by Telegram ID or creates a new one if not found.

        Args:
            user_id: Telegram user ID.
            username: Telegram username (can be empty).
            full_name: Telegram user's full name.

        Returns:
            A tuple containing the User object and a boolean indicating if the user was newly created.
        Raises:
            CoreError: If the default role ('USER') cannot be found in the database.
        """
        logger.debug(f"Attempting to get user by telegram_id={user_id}")
        user = await self.user_repo.get_by_telegram_id(db_session=self.db, telegram_id=user_id)
        is_new = False
        if user:
            logger.debug(f"Found existing user: id={user.id}, telegram_id={user_id}")
            # Optional update logic removed for simplicity, can be added later if needed
        else:
            logger.info(f"User with telegram_id={user_id} not found. Creating new user.")
            default_role = await self.role_repo.get_by_name(db_session=self.db, name=DEFAULT_ROLE_NAME)
            if not default_role:
                logger.error(f"CRITICAL: Default role '{DEFAULT_ROLE_NAME}' not found.")
                raise CoreError(f"Default role '{DEFAULT_ROLE_NAME}' not found.")
            
            role_id = default_role.id
            logger.debug(f"Found default role '{DEFAULT_ROLE_NAME}' with id={role_id}")

            user_in = UserCreate(
                telegram_id=user_id,
                username=username,
                full_name=full_name,
                role_id=role_id,
            )
            # create method in BaseRepo already handles commit and refresh
            user = await self.user_repo.create(db_session=self.db, obj_in=user_in)
            is_new = True
            logger.info(f"Successfully created new user: id={user.id}, telegram_id={user_id} with role_id={role_id} ('{DEFAULT_ROLE_NAME}')")

        return user, is_new

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return await self.user_repo.get(db_session=self.db, id=user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return await self.user_repo.get_by_username(db_session=self.db, username=username)

    async def get_user_by_telegram_id(self, telegram_id: int) -> User:
        """Fetches a user by their Telegram ID."""
        user = await self.user_repo.get_by_telegram_id(db_session=self.db, telegram_id=telegram_id)
        if not user:
            raise UserNotFoundError(entity="User", identifier=f"Telegram ID {telegram_id}") 
        return user

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = await self.get_user_by_username(username)
        if not user or not user.password:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    async def create_user_manual(self, user_data: Dict[str, Any]) -> User:
        """Create a new user manually (e.g., admin panel)."""
        if "password" in user_data:
            user_data["password"] = get_password_hash(user_data["password"])
        user_in = UserCreate(**user_data)
        return await self.user_repo.create(db_session=self.db, obj_in=user_in)

    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        """Update a user."""
        db_obj = await self.user_repo.get(db_session=self.db, id=user_id)
        if not db_obj:
            return None
        if "password" in user_data:
            user_data["password"] = get_password_hash(user_data["password"])
        return await self.user_repo.update(db_session=self.db, db_obj=db_obj, obj_in=user_data)

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        deleted_user = await self.user_repo.delete(db_session=self.db, id=user_id)
        return deleted_user is not None

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination."""
        return await self.user_repo.get_multi(db_session=self.db, skip=skip, limit=limit)

    async def get_user_language(self, telegram_id: int) -> Optional[str]:
        """Gets the language code for a user by their Telegram ID."""
        user = await self.user_repo.get_by_telegram_id(db_session=self.db, telegram_id=telegram_id)
        if not user:
            logger.warning(f"Attempted to get language for non-existent user telegram_id={telegram_id}")
            return None 
        return user.lang # Return the lang field

    async def update_user_language(self, telegram_id: int, lang_code: str) -> Optional[User]:
        """Updates the language code for a user by their Telegram ID."""
        user = await self.user_repo.get_by_telegram_id(db_session=self.db, telegram_id=telegram_id)
        if not user:
            logger.warning(f"Attempted to update language for non-existent user telegram_id={telegram_id}")
            return None
        
        # Validate lang_code maybe? (e.g., check against allowed languages)
        
        updated_user = await self.user_repo.update(db_session=self.db, db_obj=user, obj_in={"lang": lang_code})
        return updated_user

    async def ban_user(self, user_id: int) -> Optional[User]:
        """Ban a user."""
        db_user = await self.user_repo.get(db_session=self.db, id=user_id)
        if not db_user:
            return None
        return await self.user_repo.update(db_session=self.db, db_obj=db_user, obj_in={"is_banned": True})

    async def unban_user(self, user_id: int) -> Optional[User]:
        """Unban a user."""
        db_user = await self.user_repo.get(db_session=self.db, id=user_id)
        if not db_user:
            return None
        return await self.user_repo.update(db_session=self.db, db_obj=db_user, obj_in={"is_banned": False}) 