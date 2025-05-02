"""
Authentication middleware for Telegram bot.

This middleware handles user authentication, session management, and automatic
user creation for new users.
"""

from typing import Any, Awaitable, Callable, Dict, Optional
import logging

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, User as TelegramUser, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.user_service import UserService
from db.models.user import User
from db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    """
    میدل‌ور برای احراز هویت کاربر و تزریق session و user به context.
    """
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        
        # Try to get user ID from the event
        user_id = None
        telegram_user = data.get('event_from_user')
        if telegram_user:
            user_id = telegram_user.id
        
        if not user_id:
             # If user_id cannot be determined, proceed without auth context
             # This might be needed for certain events or initial interactions
            logger.warning("Could not determine user ID from the event.")
            # Pass control to the next middleware or handler without adding session/user
            # Decide if you want to pass an empty session or None. Passing None might be safer.
            data["session"] = None
            data["user"] = None
            return await handler(event, data)
            

        # Create a new session for this request
        async with self.session_pool() as session:
            data["session"] = session
            user_repo = UserRepository(session)
            
            # Find or create user in the database
            user = await user_repo.get_or_create_user(
                telegram_id=user_id,
                username=telegram_user.username,
            )
            data["user"] = user

            # Check if user is banned (optional, implement based on requirements)
            # if user and user.is_banned:
            #     logger.info(f"Banned user {user_id} tried to interact.")
            #     # Optionally send a message to the banned user
            #     # await event.answer("You are banned.") 
            #     return # Stop processing for banned users

            # Pass control to the next middleware or handler
            result = await handler(event, data)
        
        return result

    async def _get_or_create_user(
        self,
        session: AsyncSession,
        tg_user: TelegramUser
    ) -> Optional[User]:
        """Get existing user or create new one if not exists."""
        try:
            user_service = UserService(session)
            
            # Try to get existing user
            user = await user_service.get_user_by_telegram_id(tg_user.id)
            if user:
                # Update user info if needed
                full_name = " ".join(filter(None, [tg_user.first_name, tg_user.last_name]))
                if (
                    user.username != tg_user.username or
                    user.full_name != full_name
                ):
                    user = await user_service.update_user(
                        user.id,
                        username=tg_user.username,
                        first_name=tg_user.first_name,
                        last_name=tg_user.last_name
                    )
                return user
                
            # Create new user
            return await user_service.create_user(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name
            )
            
        except Exception as e:
            logger.exception(f"خطا در get_or_create_user: {e}")
            return None 