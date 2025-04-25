import asyncio
import logging
from py3xui import AsyncApi
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Panel credentials from phpMyAdmin screenshot (Panel ID 9)
# Ensure environment variables are set or replace placeholders directly for testing
PANEL_URL = os.getenv("TEST_PANEL_URL", "http://65.109.189.171:9999/xvuEl4a9wJ") # Use correct base URL without trailing slash
PANEL_USER = os.getenv("TEST_PANEL_USER", "bcb7d44b")
PANEL_PASS = os.getenv("TEST_PANEL_PASS", "e9296605")

async def test_login():
    logging.info(f"Attempting to login to {PANEL_URL} with user {PANEL_USER}")
    
    # Ensure URL doesn't have a trailing slash for py3xui
    api = AsyncApi(PANEL_URL.rstrip('/'), PANEL_USER, PANEL_PASS)
    
    try:
        result = await api.login()
        logging.info(f"Login result type: {type(result)}")
        logging.info(f"Login result value: {result}")
        
        if result is True or (isinstance(result, dict) and result.get("success") is True):
            logging.info("Login successful according to py3xui.")
        elif result is None:
             logging.warning("Login returned None. This might indicate an issue with the panel API response or py3xui parsing.")
        else:
            logging.warning(f"Login failed or returned unexpected result: {result}")
            
    except Exception as e:
        logging.error(f"An exception occurred during login attempt: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_login()) 