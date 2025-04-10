"""
Health check utility for the Telegram bot.

This module provides functions to check the health of the bot.
"""

import logging
import asyncio
import aiohttp
import sys
import os

# Adjust path for core imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir)) # Assuming scripts/monitoring is two levels down
sys.path.insert(0, project_root)

from core.config import settings # Changed from get_settings
from core.database.session import engine, Base, async_session_factory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to stdout for Docker
    ]
)
logger = logging.getLogger("bot_healthcheck")

async def check_telegram_api(bot_token: str) -> bool:
    """
    Check if the Telegram API is accessible.
    
    Args:
        bot_token (str): The Telegram bot token
        
    Returns:
        bool: True if the API is accessible, False otherwise
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    return True
                else:
                    logger.error(f"Telegram API error: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Error connecting to Telegram API: {e}")
        return False

def check_health() -> bool:
    """
    Check the overall health of the bot.
    
    Returns:
        bool: True if the bot is healthy, False otherwise
    """
    try:
        # Run async check in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Check Telegram API
        telegram_healthy = loop.run_until_complete(
            check_telegram_api(settings.TELEGRAM_BOT_TOKEN)
        )
        
        # Close the loop
        loop.close()
        
        # Return overall health status
        return telegram_healthy
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return False

async def check_db_connection(session: AsyncSession) -> bool:
    """Checks if a basic query can be executed against the database."""
    try:
        # A simple query to check connectivity
        await session.execute(text("SELECT 1"))
        logger.info("Database connection successful.")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        return False

async def main():
    logger.info("Starting bot healthcheck...")
    
    # 1. Check Database Connection
    logger.info("Checking database connection...")
    is_db_ok = False
    try:
        async with async_session_factory() as session:
            is_db_ok = await check_db_connection(session)
    except Exception as e:
        logger.error(f"Failed to create database session: {e}", exc_info=True)
        is_db_ok = False

    # 2. Check Redis Connection (if configured)
    # TODO: Add Redis check if REDIS_URL is set in settings
    is_redis_ok = True # Assume OK if not configured
    logger.info("Redis check skipped (or not configured).")

    # 3. Check Bot Token (Basic Check)
    is_token_ok = bool(settings.BOT_TOKEN and len(settings.BOT_TOKEN) > 10)
    if is_token_ok:
        logger.info("Bot token seems present.")
    else:
        logger.error("Bot token is missing or invalid!")

    # Determine overall health
    is_healthy = is_db_ok and is_redis_ok and is_token_ok

    if is_healthy:
        logger.info("Bot healthcheck passed successfully! ✅")
        sys.exit(0) # Exit with 0 for success
    else:
        logger.error("Bot healthcheck failed! ❌")
        sys.exit(1) # Exit with 1 for failure

if __name__ == "__main__":
    asyncio.run(main()) 