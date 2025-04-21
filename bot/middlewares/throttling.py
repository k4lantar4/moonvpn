"""Rate limiting middleware for the Telegram bot.

This middleware prevents spam and abuse by limiting how frequently users can
send commands and interact with the bot.
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from cachetools import TTLCache
from datetime import datetime

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 1):
        """Initialize the throttling middleware.
        
        Args:
            rate_limit: Number of seconds between allowed requests
        """
        self.rate_limit = rate_limit
        # Cache storing last request times, entries expire after rate_limit seconds
        self.cache = TTLCache(maxsize=10000, ttl=rate_limit)
        
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Process update and throttle if needed."""
        # Get user ID from either message or callback query
        user_id = event.from_user.id if event.from_user else None
        
        if not user_id:
            return await handler(event, data)
            
        # Check if user is in cooldown
        now = datetime.now().timestamp()
        last_request = self.cache.get(user_id)
        
        if last_request and (now - last_request) < self.rate_limit:
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ لطفاً کمی صبر کنید و سپس دوباره تلاش کنید."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⚠️ لطفاً کمی صبر کنید و سپس دوباره تلاش کنید.",
                    show_alert=True
                )
            return
            
        # Update last request time
        self.cache[user_id] = now
        
        # Process the update
        return await handler(event, data) 