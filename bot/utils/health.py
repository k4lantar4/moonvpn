import logging
import httpx
import asyncio
import sys
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
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            if not data.get("ok"):
                logger.error("Telegram API returned not OK")
                return False
                
            logger.info(f"Bot health check passed. Connected to {data.get('result', {}).get('username', 'Unknown')}")
            return True
            
    except httpx.TimeoutException:
        logger.error("Bot health check failed: Connection to Telegram API timed out")
        return False
    except httpx.HTTPStatusError as e:
        logger.error(f"Bot health check failed: HTTP error {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Bot health check failed: Request error {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Bot health check failed with unexpected error: {str(e)}")
        return False

def check_health() -> bool:
    """Synchronous wrapper for async_check_health"""
    try:
        return asyncio.run(async_check_health())
    except RuntimeError as e:
        # Handle the case when there's already an event loop running
        if "There is no current event loop in thread" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_check_health())
            finally:
                loop.close()
        else:
            logger.error(f"Event loop error during health check: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Failed to run health check: {str(e)}")
        return False

if __name__ == "__main__":
    # Can be run directly for testing
    is_healthy = check_health()
    print(f"Bot health status: {'healthy' if is_healthy else 'unhealthy'}")
    sys.exit(0 if is_healthy else 1) 