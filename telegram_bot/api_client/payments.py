from typing import Dict, Any, Optional, List

from httpx import AsyncClient, HTTPStatusError, RequestError

from app.schemas import PaymentRequestResponse # Assuming schema exists in shared location or copied
from .base import BaseAPIClient, APIError
from app.core.config import settings # Assuming bot has access to some shared config or gets URL from env
from app.models.order import PaymentMethod # Assuming enum is shared or copied

class PaymentsAPIClient(BaseAPIClient):
    """API Client for payment related operations."""
    
    async def request_zarinpal_payment(self, order_id: int) -> str:
        """
        Requests a Zarinpal payment URL for the given order.

        Args:
            order_id: The ID of the order.

        Returns:
            The payment URL from Zarinpal.
            
        Raises:
            APIError: If the API request fails.
        """
        endpoint = f"/payments/zarinpal/request/{order_id}"
        try:
            response = await self.post(endpoint)
            response.raise_for_status()
            data = response.json()
            # Assuming the response schema is like: {"payment_url": "..."}
            payment_url = data.get("payment_url")
            if not payment_url:
                 raise APIError(f"Payment URL not found in response for order {order_id}", status_code=response.status_code)
            return payment_url
        except HTTPStatusError as e:
            error_detail = self._parse_error_response(e.response)
            raise APIError(f"Failed to request Zarinpal payment for order {order_id}: {error_detail}", status_code=e.response.status_code)
        except RequestError as e:
            raise APIError(f"Network error requesting Zarinpal payment for order {order_id}: {e}")
        except Exception as e:
            # Catch unexpected errors
             raise APIError(f"An unexpected error occurred requesting Zarinpal payment for order {order_id}: {e}")

    async def get_available_payment_methods(self) -> List[PaymentMethod]:
        """
        Gets a list of available payment methods from the API.
        
        Returns:
            List of PaymentMethod enums representing the available payment methods.
            
        Raises:
            APIError: If the API request fails.
        """
        # Base method - always include card-to-card as it's our primary method
        enabled_methods = [PaymentMethod.CARD_TO_CARD]
        
        try:
            # Check if Zarinpal is enabled on the server
            # We can use a dedicated endpoint for checking payment method status
            # or infer from a general settings endpoint
            
            # Option 1: Dedicated endpoint (if available)
            try:
                response = await self.get("/settings/payment-methods")
                if response.status_code == 200:
                    methods_data = response.json()
                    
                    # Check for Zarinpal
                    if methods_data.get("zarinpal_enabled", False):
                        enabled_methods.append(PaymentMethod.ZARINPAL)
                    
                    # Check for wallet
                    if methods_data.get("wallet_enabled", False):
                        enabled_methods.append(PaymentMethod.WALLET)
                        
                    # Check for crypto
                    if methods_data.get("crypto_enabled", False):
                        enabled_methods.append(PaymentMethod.CRYPTO)
                        
                    return enabled_methods
            except (APIError, HTTPStatusError):
                # If dedicated endpoint fails, try fallback approach
                pass
                
            # Option 2: Try directly calling the Zarinpal endpoint with a head request
            # This is a fallback to see if the endpoint exists and doesn't return a 404
            try:
                response = await self.head("/payments/zarinpal/info")
                if response.status_code == 200:
                    enabled_methods.append(PaymentMethod.ZARINPAL)
            except (APIError, HTTPStatusError):
                # If endpoint doesn't exist, Zarinpal is probably not enabled
                pass
                
            # In a real implementation, you might want to check for wallet balance
            # to determine if wallet payment should be enabled for this specific user
            # For now, we'll assume wallet is not yet implemented
                
            return enabled_methods
            
        except Exception as e:
            # If we can't determine available methods, return just card-to-card as fallback
            return [PaymentMethod.CARD_TO_CARD]


# Instantiate the client
payments_client = PaymentsAPIClient(base_url=settings.CORE_API_BASE_URL + "/api/v1") 