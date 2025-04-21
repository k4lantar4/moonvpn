"""Bot initialization and configuration.

This module initializes the Telegram bot and sets up all required routers,
middlewares, and handlers following the MoonVPN architecture.
"""

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from core.services.settings_service import SettingsService
from .middlewares.auth import AuthMiddleware
from .middlewares.throttling import ThrottlingMiddleware
from .commands import (
    start,
    profile,
    buy,
    wallet,
    plans,
    admin
)

async def setup_bot(token: str) -> Bot:
    """Initialize and configure the bot instance."""
    bot = Bot(token=token, parse_mode=ParseMode.HTML)
    return bot

async def setup_dispatcher() -> Dispatcher:
    """Initialize and configure the dispatcher with all required components."""
    # Initialize dispatcher with memory storage
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register middlewares
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    
    # Include routers
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(buy.router)
    dp.include_router(wallet.router)
    dp.include_router(plans.router)
    
    return dp

async def setup_bot_commands(bot: Bot):
    """Set up bot commands that appear in the menu."""
    commands = [
        ("start", "شروع کار با ربات 🚀"),
        ("profile", "پروفایل کاربری 👤"),
        ("buy", "خرید سرویس 💳"),
        ("wallet", "کیف پول 💰"),
        ("plans", "لیست پلن‌ها 📋"),
        ("help", "راهنما ❓")
    ]
    await bot.set_my_commands(commands)

__all__ = ["setup_bot", "setup_dispatcher", "setup_bot_commands"]
