"""
MoonVPN Telegram Bot - Main Entry Point
"""

import os
import asyncio
import logging
from typing import Any, Dict

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from aiogram.client.default import DefaultBotProperties

from core.settings import DATABASE_URL, BOT_TOKEN
from core.services.notification_service import NotificationService
from core.services.panel_service import PanelService
from bot.commands import (
    start_router,
    register_buy_command,
    register_admin_commands,
    register_wallet_command,
    register_plans_command,
    register_profile_command,
)
from bot.callbacks import (
    register_buy_callbacks,
    register_wallet_callbacks,
    register_admin_callbacks
)
from bot.middlewares import AuthMiddleware, ErrorMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Database setup
engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Global services
notification_service: NotificationService | None = None

async def setup_bot() -> Bot:
    """Initialize and configure the bot"""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables!")
    
    return Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

async def setup_dispatcher() -> Dispatcher:
    """Initialize and configure the dispatcher"""
    # Initialize storage and dispatcher
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Create main router
    router = Router(name="main_router")
    
    # Register middlewares
    dp.message.middleware(AuthMiddleware(SessionLocal))
    dp.callback_query.middleware(AuthMiddleware(SessionLocal))
    dp.message.middleware(ErrorMiddleware())
    dp.callback_query.middleware(ErrorMiddleware())
    
    # Register command handlers
    register_buy_command(router, SessionLocal)
    register_admin_commands(router, SessionLocal)
    register_wallet_command(router, SessionLocal)
    register_plans_command(router, SessionLocal)
    register_profile_command(router, SessionLocal)
    
    # Register callback handlers
    register_buy_callbacks(router, SessionLocal)
    register_wallet_callbacks(router, SessionLocal)
    register_admin_callbacks(router, SessionLocal)
    
    # Include router in dispatcher
    dp.include_router(start_router)
    dp.include_router(router)
    
    return dp

async def init_services():
    """Initialize core services"""
    global notification_service
    
    async with SessionLocal() as session:
        # Initialize notification service
        notification_service = NotificationService(session)
        
        # Sync panel inbounds
        panel_service = PanelService(session)
        try:
            sync_results = await panel_service.sync_all_panels_inbounds()
            logger.info(f"Successfully synced inbounds for {len(sync_results)} panels")
            await notification_service.notify_admins(
                f"🔄 Panel inbounds synced successfully\n"
                f"Total panels synced: {len(sync_results)}"
            )
        except Exception as e:
            logger.error(f"Error syncing inbounds: {e}", exc_info=True)
            await notification_service.notify_admins(
                f"⚠️ Error syncing inbounds:\n{str(e)}"
            )

async def main():
    """Main entry point for the bot"""
    try:
        logger.info("Starting MoonVPN bot...")
        
        # Initialize services
        await init_services()
        
        # Setup bot and dispatcher
        bot = await setup_bot()
        dp = await setup_dispatcher()
        
        # Set bot instance for notification service
        if notification_service:
            notification_service.set_bot(bot)
        
        # Start polling
        logger.info("MoonVPN bot is ready!")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
        raise
    finally:
        if notification_service:
            await notification_service.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
