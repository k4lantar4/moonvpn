import logging
import httpx
from typing import Dict, List, Optional

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