"""
Error handling middleware for Telegram bot
"""

import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)

# TODO: Define more specific error types if needed

class ErrorMiddleware(BaseMiddleware):
    """میدلور برای مدیریت خطاهای مدیریت نشده در هندلرها."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception(f"Caught exception in handler for update {type(event).__name__}: {e}")

            # TODO: Implement more sophisticated error reporting/user notification
            # For example, notify admin or send a generic error message to the user
            
            # Attempt to inform the user generically if it's an Update event with a chat_id
            if isinstance(event, Update) and event.message and event.message.chat:
                try:
                    # Make sure bot instance is available. This requires passing it during middleware setup or accessing via context
                    bot = data.get('bot') 
                    if bot:
                         await bot.send_message(
                             event.message.chat.id,
                             "앗! مشکلی پیش آمده. 😥 لطفا دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                         )
                    else:
                        logger.warning("Bot instance not found in data for error reporting to user.")
                except Exception as send_error:
                    logger.exception(f"Failed to send error message to user: {send_error}")

            # Important: re-raise exception if you want aiogram's default error handlers to process it
            # Or return a response to signify the error was handled here.
            # For now, we log and potentially inform user, then suppress further propagation.
            return True # Indicate that the exception has been handled 