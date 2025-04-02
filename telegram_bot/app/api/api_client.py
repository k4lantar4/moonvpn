import logging
import httpx
from typing import Dict, List, Optional, Any
import aiohttp

from app.utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

# API constants
BASE_URL = "http://core-api:8000/api/v1"
TIMEOUT = 10.0  # seconds

def get_auth_headers() -> Dict[str, str]:
    """Get authorization headers for API requests."""
    # Note: In a real setup, this would include actual authentication
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

# Subscription-related API functions
async def get_user_subscriptions(user_id: int) -> Optional[List[Dict]]:
    """
    Fetch user's subscriptions from the API.
    
    Args:
        user_id: The user ID to fetch subscriptions for
        
    Returns:
        List of subscription dictionaries or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get(
                f"/users/{user_id}/subscriptions",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch subscriptions for user {user_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error fetching subscriptions for user {user_id}: {str(e)}")
        return None

async def get_subscription_details(subscription_id: str) -> Optional[Dict]:
    """
    Fetch details for a specific subscription.
    
    Args:
        subscription_id: The ID of the subscription
        
    Returns:
        Subscription details as a dictionary or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get(
                f"/subscriptions/{subscription_id}",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch details for subscription {subscription_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error fetching subscription details: {str(e)}")
        return None

async def get_subscription_qrcode(subscription_id: str, protocol: Optional[str] = None) -> Optional[Dict]:
    """
    Fetch QR code for a subscription.
    
    Args:
        subscription_id: The ID of the subscription
        protocol: Optional protocol to get QR code for
        
    Returns:
        Dictionary containing QR code data or None if unsuccessful
    """
    try:
        params = {}
        if protocol:
            params["protocol"] = protocol
            
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get(
                f"/subscriptions/{subscription_id}/qrcode",
                params=params,
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch QR code for subscription {subscription_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error fetching subscription QR code: {str(e)}")
        return None

async def get_subscription_traffic(subscription_id: str) -> Optional[Dict]:
    """
    Fetch traffic statistics for a subscription.
    
    Args:
        subscription_id: The ID of the subscription
        
    Returns:
        Dictionary containing traffic data or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get(
                f"/subscriptions/{subscription_id}/traffic",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch traffic for subscription {subscription_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error fetching subscription traffic: {str(e)}")
        return None

async def freeze_subscription(
    subscription_id: str, 
    end_date: Optional[str] = None,
    reason: Optional[str] = None
) -> Optional[Dict]:
    """
    Freeze a subscription.
    
    Args:
        subscription_id: The ID of the subscription
        end_date: Optional end date for the freeze period (ISO format)
        reason: Optional reason for freezing
        
    Returns:
        Updated subscription data or None if unsuccessful
    """
    try:
        payload = {}
        if end_date:
            payload["end_date"] = end_date
        if reason:
            payload["reason"] = reason
            
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                f"/subscriptions/{subscription_id}/freeze",
                json=payload,
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to freeze subscription {subscription_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error freezing subscription: {str(e)}")
        return None

async def unfreeze_subscription(subscription_id: str) -> Optional[Dict]:
    """
    Unfreeze a subscription.
    
    Args:
        subscription_id: The ID of the subscription
        
    Returns:
        Updated subscription data or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                f"/subscriptions/{subscription_id}/unfreeze",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to unfreeze subscription {subscription_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error unfreezing subscription: {str(e)}")
        return None

async def add_subscription_note(subscription_id: str, note: str) -> Optional[Dict]:
    """
    Add a note to a subscription.
    
    Args:
        subscription_id: The ID of the subscription
        note: The note text to add
        
    Returns:
        Updated subscription data or None if unsuccessful
    """
    try:
        payload = {"note": note}
            
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                f"/subscriptions/{subscription_id}/note",
                json=payload,
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to add note to subscription {subscription_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error adding note to subscription: {str(e)}")
        return None

async def toggle_subscription_auto_renew(subscription_id: str) -> Optional[Dict]:
    """
    Toggle the auto-renew setting for a subscription.
    
    Args:
        subscription_id: The ID of the subscription
        
    Returns:
        Updated subscription data or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                f"/subscriptions/{subscription_id}/toggle-auto-renew",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to toggle auto-renew for subscription {subscription_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error toggling auto-renew: {str(e)}")
        return None

async def change_subscription_protocol_location(
    subscription_id: str,
    protocol: Optional[str] = None,
    location: Optional[str] = None
) -> Optional[Dict]:
    """
    Change the protocol or location for a subscription.
    
    Args:
        subscription_id: The ID of the subscription
        protocol: Optional new protocol 
        location: Optional new location
        
    Returns:
        Updated subscription data or None if unsuccessful
    """
    try:
        payload = {}
        if protocol:
            payload["protocol"] = protocol
        if location:
            payload["location"] = location
            
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                f"/subscriptions/{subscription_id}/protocol-location",
                json=payload,
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to change protocol/location for subscription {subscription_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error changing protocol/location: {str(e)}")
        return None

# Order-related API functions
async def create_order(user_id: int, plan_id: str, payment_method_id: str) -> Optional[Dict]:
    """
    Create a new order for a subscription plan.
    
    Args:
        user_id: The ID of the user placing the order
        plan_id: The ID of the subscription plan
        payment_method_id: The ID of the selected payment method
        
    Returns:
        Order details as a dictionary or None if unsuccessful
    """
    try:
        payload = {
            "user_id": user_id,
            "plan_id": plan_id,
            "payment_method_id": payment_method_id
        }
            
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/orders",
                json=payload,
                headers=get_auth_headers()
            )
            
            if response.status_code in (200, 201):
                return response.json()
            else:
                logger.error(
                    f"Failed to create order. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return None

async def get_payment_methods() -> Optional[List[Dict]]:
    """
    Fetch available payment methods from the API.
    
    Returns:
        List of payment method dictionaries or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get(
                "/payment-methods",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch payment methods. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error fetching payment methods: {str(e)}")
        return None

async def confirm_order_payment(
    order_id: int,
    admin_id: int,
    admin_note: Optional[str] = None
) -> Optional[Dict]:
    """
    Confirm payment for an order and create a client on the panel.
    
    Args:
        order_id: The ID of the order to confirm
        admin_id: The ID of the admin confirming the order
        admin_note: Optional note from the admin
        
    Returns:
        Updated order data if successful, otherwise None
    """
    try:
        payload = {
            "admin_note": admin_note
        }
        
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                f"/orders/{order_id}/create-client",
                json=payload,
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully confirmed order {order_id} and created client")
                return response.json()
            else:
                logger.error(
                    f"Failed to confirm order {order_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error confirming order {order_id}: {str(e)}")
        return None

async def reject_order_payment(
    order_id: int,
    admin_id: int,
    rejection_reason: str
) -> Optional[Dict]:
    """
    Reject payment for an order.
    
    Args:
        order_id: The ID of the order to reject
        admin_id: The ID of the admin rejecting the order
        rejection_reason: Reason for rejection
        
    Returns:
        Updated order data if successful, otherwise None
    """
    try:
        payload = {
            "status": "REJECTED",
            "admin_id": admin_id,
            "admin_note": f"Payment rejected: {rejection_reason}"
        }
        
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.patch(
                f"/orders/{order_id}",
                json=payload,
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully rejected order {order_id}")
                return response.json()
            else:
                logger.error(
                    f"Failed to reject order {order_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error rejecting order {order_id}: {str(e)}")
        return None

# Bank Card-related API functions
async def get_bank_cards_for_payment() -> Optional[List[Dict]]:
    """
    Fetch active bank cards for payment purposes.
    
    Returns:
        List of bank card dictionaries or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get(
                "/bank-cards/for-payment",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch bank cards for payment. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error fetching bank cards for payment: {str(e)}")
        return None

async def get_user_bank_cards(user_id: int) -> Optional[Dict]:
    """
    Fetch bank cards for a specific user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        Dictionary containing bank cards data or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get(
                "/bank-cards",
                params={"user_id": user_id},
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch bank cards for user {user_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error fetching user bank cards: {str(e)}")
        return None

async def get_bank_card_details(bank_card_id: int) -> Optional[Dict]:
    """
    Fetch detailed information for a specific bank card.
    
    Args:
        bank_card_id: The ID of the bank card
        
    Returns:
        Dictionary containing bank card details or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get(
                f"/bank-cards/{bank_card_id}/details",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch details for bank card {bank_card_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error fetching bank card details: {str(e)}")
        return None

async def create_bank_card(
    bank_name: str,
    card_number: str,
    card_holder_name: str,
    account_number: Optional[str] = None,
    sheba_number: Optional[str] = None,
    description: Optional[str] = None,
    user_id: Optional[int] = None
) -> Optional[Dict]:
    """
    Create a new bank card.
    
    Args:
        bank_name: Name of the bank
        card_number: Card number
        card_holder_name: Name of the card holder
        account_number: Optional account number
        sheba_number: Optional SHEBA number
        description: Optional description
        user_id: Optional ID of the user who owns the card
        
    Returns:
        Created bank card data or None if unsuccessful
    """
    try:
        payload = {
            "bank_name": bank_name,
            "card_number": card_number,
            "card_holder_name": card_holder_name
        }
        
        if account_number:
            payload["account_number"] = account_number
        if sheba_number:
            payload["sheba_number"] = sheba_number
        if description:
            payload["description"] = description
        if user_id:
            payload["user_id"] = user_id
            
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/bank-cards",
                json=payload,
                headers=get_auth_headers()
            )
            
            if response.status_code in (200, 201):
                return response.json()
            else:
                logger.error(
                    f"Failed to create bank card. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error creating bank card: {str(e)}")
        return None

async def update_bank_card(
    bank_card_id: int,
    bank_name: Optional[str] = None,
    card_number: Optional[str] = None,
    card_holder_name: Optional[str] = None,
    account_number: Optional[str] = None,
    sheba_number: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    priority: Optional[int] = None,
    user_id: Optional[int] = None
) -> Optional[Dict]:
    """
    Update an existing bank card.
    
    Args:
        bank_card_id: ID of the bank card to update
        bank_name: Optional name of the bank
        card_number: Optional card number
        card_holder_name: Optional name of the card holder
        account_number: Optional account number
        sheba_number: Optional SHEBA number
        description: Optional description
        is_active: Optional active status
        priority: Optional priority
        user_id: Optional ID of the user who owns the card
        
    Returns:
        Updated bank card data or None if unsuccessful
    """
    try:
        payload = {}
        
        if bank_name is not None:
            payload["bank_name"] = bank_name
        if card_number is not None:
            payload["card_number"] = card_number
        if card_holder_name is not None:
            payload["card_holder_name"] = card_holder_name
        if account_number is not None:
            payload["account_number"] = account_number
        if sheba_number is not None:
            payload["sheba_number"] = sheba_number
        if description is not None:
            payload["description"] = description
        if is_active is not None:
            payload["is_active"] = is_active
        if priority is not None:
            payload["priority"] = priority
        if user_id is not None:
            payload["user_id"] = user_id
            
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.put(
                f"/bank-cards/{bank_card_id}",
                json=payload,
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to update bank card {bank_card_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error updating bank card: {str(e)}")
        return None

async def toggle_bank_card_status(bank_card_id: int) -> Optional[Dict]:
    """
    Toggle the active status of a bank card.
    
    Args:
        bank_card_id: ID of the bank card
        
    Returns:
        Updated bank card data or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.put(
                f"/bank-cards/{bank_card_id}/toggle-status",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to toggle status for bank card {bank_card_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error toggling bank card status: {str(e)}")
        return None

async def update_bank_card_priority(bank_card_id: int, priority: int) -> Optional[Dict]:
    """
    Update the priority of a bank card.
    
    Args:
        bank_card_id: ID of the bank card
        priority: New priority value
        
    Returns:
        Updated bank card data or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.put(
                f"/bank-cards/{bank_card_id}/priority",
                json={"priority": priority},
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to update priority for bank card {bank_card_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error updating bank card priority: {str(e)}")
        return None

async def delete_bank_card(bank_card_id: int) -> Optional[Dict]:
    """
    Delete a bank card.
    
    Args:
        bank_card_id: ID of the bank card
        
    Returns:
        Deleted bank card data or None if unsuccessful
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.delete(
                f"/bank-cards/{bank_card_id}",
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to delete bank card {bank_card_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None
    except Exception as e:
        logger.error(f"Error deleting bank card: {str(e)}")
        return None

async def submit_payment_proof(
    order_id: int,
    payment_reference: str,
    payment_proof: bytes,
    payment_method: str = "card_to_card",
    notes: str = None
) -> dict:
    """
    Submit payment proof for an order.
    
    Args:
        order_id: Order ID to submit payment for
        payment_reference: Reference/tracking number of the payment
        payment_proof: Image file of the payment proof as bytes
        payment_method: Payment method used (default: card_to_card)
        notes: Additional notes about the payment
        
    Returns:
        dict: API response with status and details
    """
    try:
        token = await get_auth_token()
        if not token:
            logger.error("Failed to get auth token for submitting payment proof")
            return {"success": False, "detail": "Authentication failed"}
        
        # Prepare request data
        url = f"{BASE_URL}/payment-proofs/"
        
        # Create form data with the image file
        form_data = aiohttp.FormData()
        form_data.add_field("order_id", str(order_id))
        form_data.add_field("payment_reference", payment_reference)
        form_data.add_field("payment_method", payment_method)
        
        if notes:
            form_data.add_field("notes", notes)
        
        # Add the payment proof image
        form_data.add_field(
            "payment_proof_image",
            payment_proof,
            filename="payment_proof.jpg",
            content_type="image/jpeg"
        )
        
        # Send request
        async with aiohttp.ClientSession() as session:
            headers = get_auth_headers()
            headers["Authorization"] = f"Bearer {token}"
            # No Content-Type header as it's automatically set by aiohttp for FormData
            async with session.post(url, data=form_data, headers=headers) as response:
                response_json = await response.json()
                status_code = response.status
                
                if status_code == 201:  # Created
                    logger.info(f"Successfully submitted payment proof for order {order_id}")
                    return {"success": True, "data": response_json}
                else:
                    logger.error(f"Failed to submit payment proof for order {order_id}. Status: {status_code}, Response: {response_json}")
                    return {"success": False, "detail": response_json.get("detail", "Failed to submit payment proof")}
    
    except Exception as e:
        logger.error(f"Error in submit_payment_proof: {str(e)}")
        return {"success": False, "detail": str(e)}

async def get_payment_admin_for_card(bank_card_id: int) -> Optional[Dict]:
    """
    Get the assigned payment admin for a bank card.
    
    Args:
        bank_card_id: ID of the bank card
    
    Returns:
        Dictionary containing the admin assignment information or None if no assignment exists
    """
    endpoint = f"{BASE_URL}/payment-admins/assignments/card/{bank_card_id}"
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Error getting payment admin for card: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"Exception getting payment admin for card: {str(e)}")
        return None

async def update_payment_proof_telegram_msg_id(
    order_id: int,
    telegram_msg_id: int,
    telegram_group_id: str
) -> Optional[Dict]:
    """
    Update an order with the Telegram message ID of the payment proof notification.
    
    Args:
        order_id: ID of the order
        telegram_msg_id: Telegram message ID of the notification
        telegram_group_id: ID of the Telegram group where the message was sent
    
    Returns:
        Updated order data or None on failure
    """
    endpoint = f"{BASE_URL}/payment-proofs/{order_id}/telegram-message"
    headers = get_auth_headers()
    data = {
        "telegram_msg_id": telegram_msg_id,
        "telegram_group_id": telegram_group_id
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(endpoint, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Error updating payment proof telegram message ID: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"Exception updating payment proof telegram message ID: {str(e)}")
        return None

async def get_user_permissions(user_id: int) -> Optional[List[str]]:
    """
    Get permissions for a user.
    
    Args:
        user_id: User ID (Telegram ID)
    
    Returns:
        List of permission keys or None on failure
    """
    endpoint = f"{BASE_URL}/users/{user_id}/permissions"
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("permissions", [])
                else:
                    error_text = await response.text()
                    logger.error(f"Error getting user permissions: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"Exception getting user permissions: {str(e)}")
        return None

async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Get user information by internal user ID.
    
    Args:
        user_id: Internal user ID
    
    Returns:
        User data or None on failure
    """
    endpoint = f"{BASE_URL}/users/{user_id}"
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Error getting user by ID: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"Exception getting user by ID: {str(e)}")
        return None

async def get_order_details(order_id: int) -> Optional[Dict]:
    """
    Get detailed order information.
    
    Args:
        order_id: ID of the order
    
    Returns:
        Order data or None on failure
    """
    endpoint = f"{BASE_URL}/orders/{order_id}"
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Error getting order details: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"Exception getting order details: {str(e)}")
        return None

async def get_next_bank_card_for_payment(last_used_id: Optional[int] = None) -> Optional[Dict]:
    """
    Get the next bank card for payment based on rotation logic.
    
    Args:
        last_used_id: Optional ID of the last card used (to avoid consecutive use)
        
    Returns:
        Bank card data or None if no active cards are available
    """
    endpoint = f"{BASE_URL}/bank-cards/next-for-payment"
    params = {}
    
    if last_used_id is not None:
        params["last_used_id"] = last_used_id
        
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success") and "data" in result:
                        return result["data"]
                    return None
                else:
                    logger.error(f"Error getting next bank card: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Exception getting next bank card: {str(e)}")
        return None

async def get_payment_admin_reports(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    admin_id: Optional[int] = None
) -> Optional[Dict]:
    """
    Get detailed performance reports for payment admins.
    
    Args:
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
        admin_id: Optional admin ID to filter for a specific admin
        
    Returns:
        Report data or None if an error occurs
    """
    endpoint = f"{BASE_URL}/payment-admins/reports"
    params = {}
    
    # Add optional parameters if provided
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if admin_id:
        params["admin_id"] = admin_id
        
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success") and "data" in result:
                        return result["data"]
                    return None
                else:
                    logger.error(f"Error getting payment admin reports: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Exception getting payment admin reports: {str(e)}")
        return None

async def get_payment_admin_assignments(
    user_id: Optional[int] = None,
    bank_card_id: Optional[int] = None,
    telegram_group_id: Optional[str] = None
) -> Optional[List[Dict]]:
    """
    Get list of payment admin assignments with optional filtering.
    
    Args:
        user_id: Optional filter by admin user ID
        bank_card_id: Optional filter by bank card ID
        telegram_group_id: Optional filter by Telegram group ID
        
    Returns:
        List of payment admin assignments or None if an error occurs
    """
    endpoint = f"{BASE_URL}/payment-admins"
    params = {}
    
    if user_id:
        params["user_id"] = user_id
    if bank_card_id:
        params["bank_card_id"] = bank_card_id
    if telegram_group_id:
        params["telegram_group_id"] = telegram_group_id
        
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"Error getting payment admin assignments: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Exception getting payment admin assignments: {str(e)}")
        return None

async def get_payment_admin_assignment(assignment_id: int) -> Optional[Dict]:
    """
    Get details of a specific payment admin assignment.
    
    Args:
        assignment_id: ID of the payment admin assignment
        
    Returns:
        Payment admin assignment details or None if an error occurs
    """
    endpoint = f"{BASE_URL}/payment-admins/{assignment_id}"
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"Error getting payment admin assignment: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Exception getting payment admin assignment: {str(e)}")
        return None

async def create_payment_admin_assignment(
    user_id: int,
    bank_card_id: Optional[int] = None,
    telegram_group_id: Optional[str] = None,
    is_active: bool = True
) -> Optional[Dict]:
    """
    Create a new payment admin assignment.
    
    Args:
        user_id: ID of the user to be assigned as payment admin
        bank_card_id: Optional ID of the bank card to assign
        telegram_group_id: Optional Telegram group ID to assign
        is_active: Whether the assignment is active
        
    Returns:
        Created payment admin assignment or None if an error occurs
    """
    endpoint = f"{BASE_URL}/payment-admins"
    payload = {
        "user_id": user_id,
        "is_active": is_active
    }
    
    if bank_card_id:
        payload["bank_card_id"] = bank_card_id
    if telegram_group_id:
        payload["telegram_group_id"] = telegram_group_id
        
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers) as response:
                if response.status == 201:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"Error creating payment admin assignment: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Exception creating payment admin assignment: {str(e)}")
        return None

async def update_payment_admin_assignment(
    assignment_id: int,
    bank_card_id: Optional[int] = None,
    telegram_group_id: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Optional[Dict]:
    """
    Update an existing payment admin assignment.
    
    Args:
        assignment_id: ID of the payment admin assignment to update
        bank_card_id: Optional new bank card ID
        telegram_group_id: Optional new Telegram group ID
        is_active: Optional new active status
        
    Returns:
        Updated payment admin assignment or None if an error occurs
    """
    endpoint = f"{BASE_URL}/payment-admins/{assignment_id}"
    payload = {}
    
    if bank_card_id is not None:
        payload["bank_card_id"] = bank_card_id
    if telegram_group_id is not None:
        payload["telegram_group_id"] = telegram_group_id
    if is_active is not None:
        payload["is_active"] = is_active
        
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(endpoint, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"Error updating payment admin assignment: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Exception updating payment admin assignment: {str(e)}")
        return None

async def delete_payment_admin_assignment(assignment_id: int) -> bool:
    """
    Delete a payment admin assignment.
    
    Args:
        assignment_id: ID of the payment admin assignment to delete
        
    Returns:
        True if successful, False otherwise
    """
    endpoint = f"{BASE_URL}/payment-admins/{assignment_id}"
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(endpoint, headers=headers) as response:
                if response.status == 200:
                    return True
                else:
                    logger.error(f"Error deleting payment admin assignment: {await response.text()}")
                    return False
    except Exception as e:
        logger.error(f"Exception deleting payment admin assignment: {str(e)}")
        return False

async def get_users_available_for_payment_admin() -> Optional[List[Dict]]:
    """
    Get list of users that can be assigned as payment admins.
    
    Returns:
        List of available users or None if an error occurs
    """
    endpoint = f"{BASE_URL}/users/available-for-payment-admin"
    headers = get_auth_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"Error getting available payment admin users: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Exception getting available payment admin users: {str(e)}")
        return None

async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    """
    Get a list of orders for a specific user.
    
    Args:
        user_id: The user's Telegram ID.
        
    Returns:
        A list of order objects, or None if an error occurred.
    """
    try:
        # First get the api user
        api_user = await get_user_by_telegram_id(user_id)
        if not api_user or 'id' not in api_user:
            logger.error(f"Could not find API user for Telegram ID {user_id}")
            return None
            
        # Then get orders using the real user ID from the API
        api_user_id = api_user['id']
        url = f"{BASE_URL}/orders/user/{api_user_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=get_auth_headers()) as response:
                response.raise_for_status()
                return await response.json()
    except Exception as e:
        logger.error(f"Error getting orders for user {user_id}: {e}")
        return None