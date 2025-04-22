"""
Authentication middleware for Telegram bot.

This middleware handles user authentication, session management, and automatic
user creation for new users.
"""

from typing import Any, Awaitable, Callable, Dict, Optional
import logging

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.user_service import UserService
from db.models.user import User

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    """Middleware to handle user authentication and session management."""
    
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        """Initialize the auth middleware.
        
        Args:
            session_pool: SQLAlchemy async session pool
        """
        self.session_pool = session_pool
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Process update and handle authentication."""
        # Create database session
        session = self.session_pool()
        data["session"] = session
        
        try:
            # Get Telegram user info
            tg_user = event.from_user
            if not tg_user:
                logger.warning("No user found in update")
                return await handler(event, data)
                
            # Get or create user
            user = await self._get_or_create_user(session, tg_user)
            if not user:
                logger.error(f"Failed to get/create user for Telegram ID: {tg_user.id}")
                if isinstance(event, Message):
                    await event.answer(
                        "⚠️ متأسفانه مشکلی در سیستم رخ داده است. لطفاً بعداً دوباره تلاش کنید."
                    )
                return
                
            # Add user to context
            data["user"] = user
            
            # Call next handler
            return await handler(event, data)
            
        except Exception as e:
            logger.exception(f"Error in auth middleware: {e}")
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ متأسفانه مشکلی در سیستم رخ داده است. لطفاً بعداً دوباره تلاش کنید."
                )
            return
            
        finally:
            await session.close()
            
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
            logger.exception(f"Error in get_or_create_user: {e}")
            return None 