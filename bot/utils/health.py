import logging
import httpx
import asyncio
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def async_check_health() -> bool:
    """Check if the bot is healthy by making a request to Telegram API.
    
    Returns:
        bool: True if healthy, False otherwise
    """
    try:
        # Try to get bot info from Telegram
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            
            data = response.json()
            if not data.get("ok"):
                logger.error("Telegram API returned not OK")
                return False
                
            logger.info("Bot health check passed")
            return True
            
    except Exception as e:
        logger.error(f"Bot health check failed: {str(e)}")
        return False

def check_health() -> bool:
    """Synchronous wrapper for async_check_health"""
    return asyncio.run(async_check_health())

if __name__ == "__main__":
    # Can be run directly for testing
    is_healthy = check_health()
    print(f"Bot health status: {'healthy' if is_healthy else 'unhealthy'}")
    exit(0 if is_healthy else 1) 