#!/usr/bin/env python
"""Minimal entry point for the MoonVPN Telegram Bot (startup focus)."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
# from aiogram.fsm.storage.redis import RedisStorage # Removed FSM
# from redis.asyncio import Redis # Removed FSM
from dotenv import load_dotenv

# --- Import Core Components ---
try:
    from core.config import settings
    from core.logging_config import setup_logging
    # Import routers with correct names/aliases
    from bot.handlers.common import common_router
    from bot.handlers.admin import router as admin_router # Use alias
    from bot.handlers.admin.panel_handlers import router as admin_panel_router
    # Import middlewares
    from bot.middlewares.db_session import DbSessionMiddleware # Uncommented DB Middleware
    # from bot.middlewares.auth import AuthMiddleware
    # Import session factory (might still be needed by services called from handlers)
    from core.database.session import async_session_factory # Uncommented session factory
    # Import PanelService for background task
    # from bot.services.panel_service import PanelService # Removed Background Task
except ImportError as e:
    # Keep this basic error check
    print(f"Error importing core/bot modules: {e}. Ensure project structure is correct.")
    sys.exit(1)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

async def main() -> None:
    """Initializes and runs the Telegram bot (minimal version)."""
    logger.info("🚀 Starting Minimal MoonVPN Bot...")

    # --- Bot Initialization ---
    if not settings.BOT_TOKEN:
        logger.critical("BOT_TOKEN not found in environment variables! Exiting.")
        sys.exit(1)
    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    logger.debug("Bot instance created.")

    # --- FSM Storage (Removed) --- 
    # try:
    #     redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
    #     await redis_client.ping() # Test connection
    #     storage = RedisStorage(redis=redis_client)
    #     logger.info(f"Connected to Redis for FSM storage: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    # except Exception as e:
    #     logger.error(f"❌ Could not connect to Redis: {e}", exc_info=True)
    #     logger.warning("Falling back to MemoryStorage (not recommended for production)")
    #     # from aiogram.fsm.storage.memory import MemoryStorage
    #     # storage = MemoryStorage()
    #     # For now, let's exit if Redis is unavailable, as it's crucial
    #     sys.exit(1)

    # --- Dispatcher Setup (No Storage) ---
    dp = Dispatcher() # Removed storage=storage
    logger.debug("Dispatcher instance created.")

    # --- Include Routers (Using correct names/aliases) ---
    dp.include_router(common_router)
    dp.include_router(admin_router) # This should include all admin sub-routers
    # dp.include_router(admin_panel_router) # REMOVE: This router is likely included in admin_router
    logger.info("Included routers: common, admin.") # Updated log message

    # --- Register Middlewares ---
    # Register DbSessionMiddleware for all updates
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session_factory)) # Uncommented DB Middleware registration
    logger.info("Registered DbSessionMiddleware.")
    # dp.update.middleware(AuthMiddleware(session_pool=async_session_factory))
    # logger.info("Registered AuthMiddleware.")

    # --- Start Background Tasks (Removed) ---
    # health_check_task = None
    # try:
    #     async with async_session_factory() as temp_session:
    #          panel_service_instance = PanelService(temp_session)
    #          health_check_task = asyncio.create_task(panel_service_instance.run_periodic_health_checks(interval_seconds=settings.PANEL_HEALTH_CHECK_INTERVAL))
    #          logger.info(f"Started background task for periodic panel health checks (interval: {settings.PANEL_HEALTH_CHECK_INTERVAL}s).")
    # except Exception as task_err:
    #     logger.error(f"Failed to start panel health check task: {task_err}", exc_info=True)
    #     health_check_task = None

    # --- Simplified Shutdown --- 
    async def on_shutdown():
        logger.info("Shutting down...")
        # if health_check_task and not health_check_task.done(): # Removed background task check
        #     health_check_task.cancel()
        #     logger.info("Cancelled background health check task.")
        #     try:
        #         await health_check_task
        #     except asyncio.CancelledError:
        #         logger.info("Health check task cancellation confirmed.")
        if bot.session:
             await bot.session.close()
        # await redis_client.close() # Removed Redis shutdown
        logger.info("Bot connections closed.")

    # --- Start Polling ---
    logger.info("Starting polling...")
    polling_task = None
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        polling_task = asyncio.create_task(dp.start_polling(bot))
        await polling_task
    except asyncio.CancelledError:
        logger.info("Polling task cancelled.")
    except Exception as e:
        logger.critical(f"❌ Bot polling failed unexpectedly: {e}", exc_info=True)
    finally:
        await on_shutdown()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested via KeyboardInterrupt.")
