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

# Define a placeholder Role model or ID if RoleRepository is not available
# DEFAULT_USER_ROLE_ID = 1 # IMPORTANT: Verify this ID in your database 'roles' table later <-- Remove this
DEFAULT_ROLE_NAME = "USER" # Define the default role name

class UserService:
    """User service class for handling user-related operations."""

    def __init__(self):
        """Initialize UserService with required repositories."""
        # Instantiate repositories directly
        self.user_repo = UserRepository()
        self.role_repo = RoleRepository()

    async def get_or_create_user(
        self,
        db_session: AsyncSession,
        *,
        user_id: int,
        username: str,
        full_name: str
    ) -> Tuple[User, bool]:
        """
        Gets a user by Telegram ID or creates a new one if not found.
        Assumes commit/rollback is handled by the caller (handler).

        Args:
            db_session: The database session.
            user_id: Telegram user ID.
            username: Telegram username (can be empty).
            full_name: Telegram user's full name.

        Returns:
            A tuple containing the User object and a boolean indicating if the user was newly created.
        Raises:
            CoreError: If the default role ('USER') cannot be found in the database.
        """
        logger.debug(f"Attempting to get user by telegram_id={user_id}")
        user = await self.user_repo.get_by_telegram_id(db_session=db_session, telegram_id=user_id)
        is_new = False
        if user:
            logger.debug(f"Found existing user: id={user.id}, telegram_id={user_id}")
            # Optional update logic removed for simplicity, can be added later if needed
        else:
            logger.info(f"User with telegram_id={user_id} not found. Creating new user.")
            default_role = await self.role_repo.get_by_name(db_session=db_session, name=DEFAULT_ROLE_NAME)
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
            # No need for explicit commit here, BaseRepo create handles it.
            user = await self.user_repo.create(db_session=db_session, obj_in=user_in)
            is_new = True
            logger.info(f"Successfully created new user: id={user.id}, telegram_id={user_id} with role_id={role_id} ('{DEFAULT_ROLE_NAME}')")

        return user, is_new

    async def get_user_by_id(self, db_session: AsyncSession, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        # Correction: BaseRepository uses 'get', not 'get_by_id'
        return await self.user_repo.get(db_session=db_session, id=user_id)

    async def get_user_by_username(self, db_session: AsyncSession, username: str) -> Optional[User]:
        """Get a user by username."""
        return await self.user_repo.get_by_username(db_session=db_session, username=username)

    async def get_user_by_telegram_id(self, db_session: AsyncSession, telegram_id: int) -> User:
        """Fetches a user by their Telegram ID."""
        # Pass db_session
        user = await self.user_repo.get_by_telegram_id(db_session=db_session, telegram_id=telegram_id)
        if not user:
            raise UserNotFoundError(entity="User", identifier=f"Telegram ID {telegram_id}") 
        return user

    async def authenticate_user(self, db_session: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = await self.get_user_by_username(db_session, username)
        if not user or not user.password:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    async def create_user_manual(self, db_session: AsyncSession, user_data: Dict[str, Any]) -> User:
        """Create a new user manually (e.g., admin panel). Assumes commit by caller."""
        if "password" in user_data:
            user_data["password"] = get_password_hash(user_data["password"])
        user_in = UserCreate(**user_data)
        # BaseRepo create handles commit
        return await self.user_repo.create(db_session=db_session, obj_in=user_in)

    async def update_user(self, db_session: AsyncSession, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        """Update a user. Assumes commit by caller."""
        db_obj = await self.user_repo.get(db_session=db_session, id=user_id) # Use get
        if not db_obj:
            return None
        if "password" in user_data:
            user_data["password"] = get_password_hash(user_data["password"])
        # BaseRepo update handles commit
        return await self.user_repo.update(db_session=db_session, db_obj=db_obj, obj_in=user_data)

    async def delete_user(self, db_session: AsyncSession, user_id: int) -> bool:
        """Delete a user. Assumes commit by caller."""
        # BaseRepo delete handles commit
        deleted_user = await self.user_repo.delete(db_session=db_session, id=user_id)
        return deleted_user is not None

    async def list_users(self, db_session: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination."""
        return await self.user_repo.get_multi(db_session=db_session, skip=skip, limit=limit)

    # count_users method seems missing in BaseRepository, let's comment it out for now
    # async def count_users(self, db_session: AsyncSession) -> int:
    #     """Count total number of users."""
    #     return await self.user_repo.count(db_session=db_session)

    async def get_user_language(self, db_session: AsyncSession, telegram_id: int) -> Optional[str]:
        """Gets the language code for a user by their Telegram ID."""
        user = await self.user_repo.get_by_telegram_id(db_session=db_session, telegram_id=telegram_id)
        if not user:
            # Should not happen if called after /start, but handle defensively
            logger.warning(f"Attempted to get language for non-existent user telegram_id={telegram_id}")
            return None 
        return user.lang # Return the lang field

    async def update_user_language(self, db_session: AsyncSession, telegram_id: int, lang_code: str) -> Optional[User]:
        """Updates the language code for a user by their Telegram ID. Assumes commit by caller."""
        user = await self.user_repo.get_by_telegram_id(db_session=db_session, telegram_id=telegram_id)
        if not user:
            logger.warning(f"Attempted to update language for non-existent user telegram_id={telegram_id}")
            return None
        
        # Validate lang_code maybe? (e.g., check against allowed languages)
        # For now, just update
        
        # BaseRepo update handles commit
        updated_user = await self.user_repo.update(db_session=db_session, db_obj=user, obj_in={"lang": lang_code})
        return updated_user

    async def ban_user(self, db_session: AsyncSession, user_id: int) -> Optional[User]:
        """Ban a user. Assumes commit by caller."""
        # Use update method directly
        db_user = await self.user_repo.get(db_session=db_session, id=user_id)
        if not db_user:
            return None
        return await self.user_repo.update(db_session=db_session, db_obj=db_user, obj_in={"is_banned": True})

    async def unban_user(self, db_session: AsyncSession, user_id: int) -> Optional[User]:
        """Unban a user. Assumes commit by caller."""
        db_user = await self.user_repo.get(db_session=db_session, id=user_id)
        if not db_user:
            return None
        return await self.user_repo.update(db_session=db_session, db_obj=db_user, obj_in={"is_banned": False})

    # Commenting out the old create_user method as get_or_create_user is preferred
    # async def create_user(self, db_session: AsyncSession, telegram_id: int, username: Optional[str] = None) -> User:
    #     """Creates a new user with the default 'USER' role."""
    #     logger.info(f"Attempting to create user for Telegram ID: {telegram_id}")
    #     existing_user = await self.user_repo.get_by_telegram_id(db_session=db_session, telegram_id=telegram_id)
    #     if existing_user:
    #         logger.warning(f"User with Telegram ID {telegram_id} already exists.")
    #         return existing_user
            
    #     default_role = await self.role_repo.get_by_name(db_session=db_session, name="USER")
    #     if not default_role:
    #         logger.error("Default 'USER' role not found.")
    #         raise RoleNotFoundException("Default user role configuration is missing.")

    #     user_in = UserCreate(
    #         telegram_id=telegram_id,
    #         username=username,
    #         role_id=default_role.id,
    #         balance=0.0
    #     )
    #     try:
    #         # Use create method from BaseRepo which handles commit
    #         created_user = await self.user_repo.create(db_session=db_session, obj_in=user_in)
    #         logger.info(f"Successfully created new user with Telegram ID: {telegram_id}, role ID: {default_role.id}")
    #         return created_user
    #     except Exception as e:
    #         # DuplicateUserException handling might need adjustment based on BaseRepo behavior
    #         logger.exception(f"Database error while adding user {telegram_id}: {e}")
    #         raise BusinessLogicError(f"Could not create user due to DB issue.") from e
             
    # ... rest of the service 