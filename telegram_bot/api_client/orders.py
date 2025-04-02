async def create_order(self, user_id: int, plan_id: int, payment_method: str = "CARD_TO_CARD") -> dict:
    """
    Creates a new order.
    
    Args:
        user_id: The ID of the user creating the order.
        plan_id: The ID of the plan being ordered.
        payment_method: The payment method to use (default: "CARD_TO_CARD").
        
    Returns:
        The created order as a dictionary.
        
    Raises:
        APIError: If the API request fails.
    """
    // ... existing code ...

async def get_order(self, order_id: int) -> dict:
    """
    Gets details for a specific order.
    
    Args:
        order_id: The ID of the order to fetch.
        
    Returns:
        The order details as a dictionary.
        
    Raises:
        APIError: If the API request fails.
    """
    endpoint = f"/orders/{order_id}"
    try:
        response = await self.get(endpoint)
        response.raise_for_status()
        return response.json()
    except HTTPStatusError as e:
        error_detail = self._parse_error_response(e.response)
        if e.response.status_code == 404:
            # Order not found
            return None
        raise APIError(f"Failed to get order {order_id}: {error_detail}", status_code=e.response.status_code)
    except RequestError as e:
        raise APIError(f"Network error fetching order {order_id}: {e}")
    except Exception as e:
        raise APIError(f"Unexpected error getting order {order_id}: {e}")
        
async def cancel_order(self, order_id: int) -> bool:
    """
    Cancels an order that has not been paid yet.
    
    Args:
        order_id: The ID of the order to cancel.
        
    Returns:
        True if the order was successfully cancelled, False otherwise.
        
    Raises:
        APIError: If the API request fails.
    """
    endpoint = f"/orders/{order_id}/cancel"
    try:
        response = await self.post(endpoint)
        response.raise_for_status()
        return True
    except HTTPStatusError as e:
        error_detail = self._parse_error_response(e.response)
        if e.response.status_code == 404:
            # Order not found
            return False
        raise APIError(f"Failed to cancel order {order_id}: {error_detail}", status_code=e.response.status_code)
    except RequestError as e:
        raise APIError(f"Network error cancelling order {order_id}: {e}")
    except Exception as e:
        raise APIError(f"Unexpected error cancelling order {order_id}: {e}")

async def get_user_orders(self, user_id: int, status: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[dict]:
    """
    Gets orders for a specific user, optionally filtered by status.
    
    Args:
        user_id: The ID of the user.
        status: Optional filter for order status.
        limit: Maximum number of orders to return.
        offset: Number of orders to skip for pagination.
        
    Returns:
        List of order dictionaries.
        
    Raises:
        APIError: If the API request fails.
    """
    endpoint = f"/orders/user/{user_id}"
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
        
    try:
        response = await self.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except HTTPStatusError as e:
        error_detail = self._parse_error_response(e.response)
        raise APIError(f"Failed to get orders for user {user_id}: {error_detail}", status_code=e.response.status_code)
    except RequestError as e:
        raise APIError(f"Network error fetching orders for user {user_id}: {e}")
    except Exception as e:
        raise APIError(f"Unexpected error getting orders for user {user_id}: {e}")
// ... existing code ... 