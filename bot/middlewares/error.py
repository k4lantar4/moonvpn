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
    """میدلور برای مدیریت خطاها هنگام پردازش آپدیت."""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """اجرای میدلور"""
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
            logger.exception("خطای پیش‌بینی نشده رخ داد: %s", e)
            error_msg = (
                "⚠️ An unexpected error occurred.\n"
                "Our team has been notified and will fix this soon."
            )
            if isinstance(event, Message):
                await event.answer(error_msg)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(error_msg)
                await event.answer()
            
            # Determine the target to send the error message to
            target = None
            if event.message:
                target = event.message
            elif event.callback_query:
                target = event.callback_query.message
                # Try to answer callback query first to dismiss the loading state
                try:
                    await event.callback_query.answer(
                        "خطایی رخ داد. لطفاً بعداً دوباره تلاش کنید.", 
                        show_alert=True
                    )
                except Exception as callback_err:
                    logger.error(f"پاسخ به callback query هنگام خطا ناموفق بود: {callback_err}")

            # Send error message to the user if possible
            if target and isinstance(target, Message):
                try:
                    await target.answer(
                        "⚠️ وای! مشکلی پیش آمد.\n"
                        "ما مطلع شدیم و در حال رفع آن هستیم. لطفاً بعداً دوباره تلاش کنید."
                    )
                except Exception as send_err:
                    logger.error(f"ارسال پیام خطا به کاربر ناموفق بود: {send_err}")
            
            # Optionally, re-raise the exception if you want it to be handled further up
            # or if you have other error handling mechanisms
            return None # Stop processing this update further down the chain
            
            # Re-raise error for global error handler
            # raise e 