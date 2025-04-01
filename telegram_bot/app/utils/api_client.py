import httpx
import logging
from typing import Optional, Dict, Any

from app.core.config import CORE_API_URL

# Get logger instance
logger = logging.getLogger(__name__)

# --- User API Functions ---

async def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Fetches user data from the Core API based on their Telegram ID.

    Args:
        telegram_id: The user's Telegram ID.

    Returns:
        A dictionary containing user data if found, otherwise None.
    """
    url = f"{CORE_API_URL}/users/telegram/{telegram_id}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                logger.info(f"User {telegram_id} found via API.")
                return response.json()
            elif response.status_code == 404:
                logger.info(f"User {telegram_id} not found via API.")
                return None
            else:
                logger.error(f"API Error fetching user {telegram_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except httpx.RequestError as e:
            logger.error(f"HTTP Error fetching user {telegram_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching user {telegram_id}: {e}")
            return None

async def register_user(
    telegram_id: int,
    first_name: str,
    username: Optional[str] = None,
    phone_number: Optional[str] = None # Added phone_number
) -> Optional[Dict[str, Any]]:
    """Registers a new user via the Core API.

    Args:
        telegram_id: The user's Telegram ID.
        first_name: The user's first name.
        username: The user's Telegram username (optional).
        phone_number: The user's phone number (optional but needed for registration).

    Returns:
        A dictionary containing the newly created user data if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/users/"
    user_data = {
        "telegram_id": telegram_id,
        "first_name": first_name,
        "username": username,
        "phone_number": phone_number,
        # Add other default fields if required by the API, e.g., role_id
        # "role_id": default_role_id, # Assuming a default role for new users
    }
    # Filter out None values if the API doesn't handle them gracefully
    payload = {k: v for k, v in user_data.items() if v is not None}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 201: # Assuming 201 Created for successful registration
                logger.info(f"User {telegram_id} registered successfully via API.")
                return response.json()
            elif response.status_code == 409: # Conflict, user might already exist
                 logger.warning(f"Attempted to register existing user {telegram_id} (API returned 409 Conflict).")
                 # Optionally, fetch the user data again here if needed
                 return await get_user_by_telegram_id(telegram_id)
            else:
                logger.error(f"API Error registering user {telegram_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except httpx.RequestError as e:
            logger.error(f"HTTP Error registering user {telegram_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error registering user {telegram_id}: {e}")
            return None

# --- Add other API client functions as needed (e.g., for plans, orders) ---

async def get_active_plans() -> Optional[list[Dict[str, Any]]]:
    """Fetches the list of active service plans from the Core API.

    Returns:
        A list of active plan dictionaries if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/plans/active/"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                plans = response.json()
                logger.info(f"Fetched {len(plans)} active plans from API.")
                return plans
            else:
                logger.error(f"API Error fetching active plans: Status {response.status_code}, Response: {response.text}")
                return None
        except httpx.RequestError as e:
            logger.error(f"HTTP Error fetching active plans: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching active plans: {e}")
            return None 