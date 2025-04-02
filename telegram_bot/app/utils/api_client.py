import httpx
import logging
from typing import Optional, Dict, Any, List

from core.config import CORE_API_URL

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

async def get_user_info(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Fetches user data including wallet balance from the Core API.
    
    Args:
        telegram_id: The user's Telegram ID.
        
    Returns:
        A dictionary containing user data if found, otherwise None.
    """
    # First try to get user by telegram_id
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        logger.warning(f"User {telegram_id} not found when fetching wallet info")
        return None
        
    # If we have a user ID, fetch the full user info including wallet balance
    user_id = user.get('id')
    if not user_id:
        logger.warning(f"User {telegram_id} found but has no ID")
        return user  # Return what we have
        
    url = f"{CORE_API_URL}/users/{user_id}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Fetched user info for user {telegram_id}")
                return user_data
            else:
                logger.error(f"API Error fetching user info for {telegram_id}: Status {response.status_code}, Response: {response.text}")
                return user  # Fall back to the basic user data
        except Exception as e:
            logger.error(f"Error fetching user info for {telegram_id}: {e}")
            return user  # Fall back to the basic user data

async def create_order(
    user_id: int,
    plan_id: int,
    payment_method: Optional[str] = None, 
    discount_code: Optional[str] = None,
    config_protocol: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Creates a new order via the Core API.
    
    Args:
        user_id: The user's ID from the database.
        plan_id: The ID of the plan being ordered.
        payment_method: Optional payment method.
        discount_code: Optional discount code.
        config_protocol: Optional protocol preference.
        
    Returns:
        A dictionary containing the created order data if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/orders/"
    
    # Prepare order data
    order_data = {
        "user_id": user_id,
        "plan_id": plan_id,
        "payment_method": payment_method,
        "discount_code": discount_code,
        "config_protocol": config_protocol
    }
    
    # Remove None values
    payload = {k: v for k, v in order_data.items() if v is not None}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"Order created successfully for user {user_id}, plan {plan_id}")
                return response.json()
            else:
                logger.error(f"API Error creating order: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None

async def get_payment_methods() -> Optional[List[Dict[str, Any]]]:
    """Fetches available payment methods from the Core API.
    
    Returns:
        A list of payment method dictionaries if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/payment-methods/active/"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                payment_methods = response.json()
                logger.info(f"Fetched {len(payment_methods)} payment methods from API")
                return payment_methods
            else:
                logger.error(f"API Error fetching payment methods: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching payment methods: {e}")
            return None

# --- Add other API client functions as needed (e.g., for plans, orders) ---

async def get_active_plans() -> Optional[List[Dict[str, Any]]]:
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

async def get_user_subscriptions(user_id: int) -> Optional[List[Dict[str, Any]]]:
    """Fetches a user's subscriptions from the Core API.
    
    Args:
        user_id: The user's ID from the database.
        
    Returns:
        A list of subscription dictionaries if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/users/{user_id}/subscriptions"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                subscriptions = response.json()
                logger.info(f"Fetched {len(subscriptions)} subscriptions for user {user_id}")
                return subscriptions
            else:
                logger.error(f"API Error fetching subscriptions for user {user_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching subscriptions for user {user_id}: {e}")
            return None

async def get_subscription_details(subscription_id: int) -> Optional[Dict[str, Any]]:
    """Fetches details for a specific subscription from the Core API.
    
    Args:
        subscription_id: The ID of the subscription.
        
    Returns:
        A dictionary containing subscription details if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/subscriptions/{subscription_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                subscription = response.json()
                logger.info(f"Fetched details for subscription {subscription_id}")
                return subscription
            else:
                logger.error(f"API Error fetching subscription {subscription_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching subscription {subscription_id}: {e}")
            return None

async def get_subscription_qrcode(subscription_id: int, protocol: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches QR code for a subscription from the Core API.
    
    Args:
        subscription_id: The ID of the subscription.
        protocol: Optional protocol preference (vmess, vless, trojan).
        
    Returns:
        A dictionary containing QR code and connection data if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/subscriptions/{subscription_id}/qrcode"
    params = {}
    if protocol:
        params["protocol"] = protocol
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                qrcode_data = response.json()
                logger.info(f"Fetched QR code for subscription {subscription_id}")
                return qrcode_data
            else:
                logger.error(f"API Error fetching QR code for subscription {subscription_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching QR code for subscription {subscription_id}: {e}")
            return None

async def get_subscription_traffic(subscription_id: int) -> Optional[Dict[str, Any]]:
    """Fetches traffic statistics for a subscription from the Core API.
    
    Args:
        subscription_id: The ID of the subscription.
        
    Returns:
        A dictionary containing traffic statistics if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/subscriptions/{subscription_id}/traffic"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                traffic_data = response.json()
                logger.info(f"Fetched traffic statistics for subscription {subscription_id}")
                return traffic_data
            else:
                logger.error(f"API Error fetching traffic for subscription {subscription_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching traffic for subscription {subscription_id}: {e}")
            return None

async def freeze_subscription(subscription_id: int, freeze_end_date: Optional[str] = None, freeze_reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Freezes a subscription via the Core API.
    
    Args:
        subscription_id: The ID of the subscription to freeze.
        freeze_end_date: Optional end date for the freeze period (ISO format).
        freeze_reason: Optional reason for freezing.
        
    Returns:
        Updated subscription data if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/subscriptions/{subscription_id}/freeze"
    
    # Prepare request data
    data = {}
    if freeze_end_date:
        data["freeze_end_date"] = freeze_end_date
    if freeze_reason:
        data["freeze_reason"] = freeze_reason
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            if response.status_code == 200:
                subscription = response.json()
                logger.info(f"Successfully froze subscription {subscription_id}")
                return subscription
            else:
                logger.error(f"API Error freezing subscription {subscription_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error freezing subscription {subscription_id}: {e}")
            return None

async def unfreeze_subscription(subscription_id: int) -> Optional[Dict[str, Any]]:
    """Unfreezes a subscription via the Core API.
    
    Args:
        subscription_id: The ID of the subscription to unfreeze.
        
    Returns:
        Updated subscription data if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/subscriptions/{subscription_id}/unfreeze"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url)
            if response.status_code == 200:
                subscription = response.json()
                logger.info(f"Successfully unfroze subscription {subscription_id}")
                return subscription
            else:
                logger.error(f"API Error unfreezing subscription {subscription_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error unfreezing subscription {subscription_id}: {e}")
            return None

async def add_subscription_note(subscription_id: int, note: str) -> Optional[Dict[str, Any]]:
    """Adds a note to a subscription via the Core API.
    
    Args:
        subscription_id: The ID of the subscription.
        note: The note text to add.
        
    Returns:
        Updated subscription data if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/subscriptions/{subscription_id}/notes"
    
    data = {"note": note}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            if response.status_code == 200:
                subscription = response.json()
                logger.info(f"Successfully added note to subscription {subscription_id}")
                return subscription
            else:
                logger.error(f"API Error adding note to subscription {subscription_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error adding note to subscription {subscription_id}: {e}")
            return None

async def toggle_subscription_auto_renew(subscription_id: int, auto_renew: bool, payment_method: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Toggles auto-renew setting for a subscription via the Core API.
    
    Args:
        subscription_id: The ID of the subscription.
        auto_renew: Boolean indicating whether auto-renew should be enabled.
        payment_method: Optional payment method to use for auto-renewal.
        
    Returns:
        Updated subscription data if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/subscriptions/{subscription_id}/auto-renew"
    
    data = {"auto_renew": auto_renew}
    if payment_method:
        data["auto_renew_payment_method"] = payment_method
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            if response.status_code == 200:
                subscription = response.json()
                logger.info(f"Successfully {('enabled' if auto_renew else 'disabled')} auto-renew for subscription {subscription_id}")
                return subscription
            else:
                logger.error(f"API Error toggling auto-renew for subscription {subscription_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error toggling auto-renew for subscription {subscription_id}: {e}")
            return None

async def change_subscription_protocol_location(subscription_id: int, new_inbound_id: Optional[int] = None, new_panel_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Changes the protocol or location for a subscription via the Core API.
    
    Args:
        subscription_id: The ID of the subscription.
        new_inbound_id: Optional ID of the new inbound (protocol).
        new_panel_id: Optional ID of the new panel (location).
        
    Returns:
        Updated subscription data if successful, otherwise None.
    """
    url = f"{CORE_API_URL}/subscriptions/{subscription_id}/protocol-location"
    
    data = {}
    if new_inbound_id is not None:
        data["new_inbound_id"] = new_inbound_id
    if new_panel_id is not None:
        data["new_panel_id"] = new_panel_id
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(url, json=data)
            if response.status_code == 200:
                subscription = response.json()
                logger.info(f"Successfully changed protocol/location for subscription {subscription_id}")
                return subscription
            else:
                logger.error(f"API Error changing protocol/location for subscription {subscription_id}: Status {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error changing protocol/location for subscription {subscription_id}: {e}")
            return None 