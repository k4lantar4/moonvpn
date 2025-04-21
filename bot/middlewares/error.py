"""
Error handling middleware for Telegram bot
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, ErrorEvent
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

class ErrorMiddleware(BaseMiddleware):
    """Middleware to handle errors in bot handlers"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        try:
            # Call next handler
            return await handler(event, data)
            
        except TelegramBadRequest as e:
            # Handle Telegram API errors
            logger.error(f"Telegram API error: {e}")
            error_msg = "⚠️ Sorry, there was an error processing your request."
            if isinstance(event, Message):
                await event.answer(error_msg)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(error_msg)
                await event.answer()
                
        except Exception as e:
            # Handle all other errors
            logger.error(f"Unhandled error in handler: {e}", exc_info=True)
            error_msg = (
                "⚠️ An unexpected error occurred.\n"
                "Our team has been notified and will fix this soon."
            )
            if isinstance(event, Message):
                await event.answer(error_msg)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(error_msg)
                await event.answer()
            
            # Re-raise error for global error handler
            raise 