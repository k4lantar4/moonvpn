import requests
import logging
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

class ZarinpalAPIError(Exception):
    """Custom exception for Zarinpal API errors."""
    def __init__(self, code: int, message: str, authority: Optional[str] = None):
        self.code = code
        self.message = message
        self.authority = authority
        super().__init__(f"Zarinpal API Error {code}: {message}")

class ZarinpalService:
    """
    Service for interacting with the Zarinpal payment gateway API.
    """

    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.request_url = settings.ZARINPAL_API_URL_REQUEST
        self.verify_url = settings.ZARINPAL_API_URL_VERIFY
        self.start_pay_url = settings.ZARINPAL_START_PAY_URL
        self.enabled = settings.ZARINPAL_ENABLED
        
        if self.enabled and not self.merchant_id:
            logger.error("Zarinpal is enabled but ZARINPAL_MERCHANT_ID is not set.")
            self.enabled = False # Disable if merchant ID is missing
            
        if self.enabled and not settings.ZARINPAL_CALLBACK_URL_BASE:
             logger.error("Zarinpal is enabled but ZARINPAL_CALLBACK_URL_BASE is not set.")
             self.enabled = False # Disable if callback base URL is missing

    def _build_callback_url(self, order_id: int) -> str:
        """Builds the full callback URL for a specific order."""
        # Ensure base URL doesn't end with '/' and path doesn't start with '/'
        base_url = settings.ZARINPAL_CALLBACK_URL_BASE.rstrip('/')
        callback_path = settings.ZARINPAL_CALLBACK_PATH.lstrip('/')
        # Include order_id in the callback URL for easier tracking
        return f"{base_url}/{callback_path}/{order_id}" 

    def request_payment(
        self,
        amount: Decimal,
        description: str,
        order_id: int, # Used to build unique callback URL
        user_email: Optional[str] = None,
        user_mobile: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Request a payment transaction from Zarinpal.

        Args:
            amount: The amount to be paid (in Toman).
            description: Description of the transaction.
            order_id: The unique ID of the order this payment is for.
            user_email: Optional user email.
            user_mobile: Optional user mobile number.

        Returns:
            Tuple of (payment_url, authority_token)

        Raises:
            ZarinpalAPIError: If the API request fails or Zarinpal is disabled.
        """
        if not self.enabled:
            raise ZarinpalAPIError(-1, "Zarinpal payment gateway is disabled in settings.")

        callback_url = self._build_callback_url(order_id)
        
        payload = {
            "merchant_id": self.merchant_id,
            "amount": int(amount),  # Zarinpal expects integer amount (Toman)
            "description": description,
            "callback_url": callback_url,
            "metadata": {
                "order_id": order_id, # Include order_id in metadata
                "email": user_email,
                "mobile": user_mobile,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            logger.info(f"Requesting Zarinpal payment for order {order_id}, amount: {amount}")
            response = requests.post(self.request_url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            
            response_data = response.json()
            
            if response_data.get("data") and response_data["data"].get("code") == 100:
                authority = response_data["data"]["authority"]
                payment_url = f"{self.start_pay_url}{authority}"
                logger.info(f"Zarinpal payment request successful for order {order_id}. Authority: {authority}")
                return payment_url, authority
            else:
                # Handle Zarinpal specific errors
                error_code = response_data.get("errors", {}).get("code", -1)
                error_message = response_data.get("errors", {}).get("message", "Unknown Zarinpal error")
                logger.error(f"Zarinpal payment request failed for order {order_id}. Code: {error_code}, Message: {error_message}, Response: {response_data}")
                raise ZarinpalAPIError(error_code, error_message)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error requesting Zarinpal payment for order {order_id}: {e}", exc_info=True)
            raise ZarinpalAPIError(-500, f"Network error communicating with Zarinpal: {e}")
        except Exception as e:
            logger.error(f"Unexpected error requesting Zarinpal payment for order {order_id}: {e}", exc_info=True)
            raise ZarinpalAPIError(-500, f"An unexpected error occurred: {e}")

    def verify_payment(self, amount: Decimal, authority: str) -> Dict[str, Any]:
        """
        Verify a payment transaction with Zarinpal.

        Args:
            amount: The amount that was supposed to be paid (in Toman).
            authority: The authority token received from the request payment step.

        Returns:
            Dictionary containing verification details (including 'ref_id').

        Raises:
            ZarinpalAPIError: If the verification fails or Zarinpal is disabled.
        """
        if not self.enabled:
            raise ZarinpalAPIError(-1, "Zarinpal payment gateway is disabled in settings.")

        payload = {
            "merchant_id": self.merchant_id,
            "amount": int(amount), # Zarinpal expects integer amount (Toman)
            "authority": authority,
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            logger.info(f"Verifying Zarinpal payment with authority: {authority}, amount: {amount}")
            response = requests.post(self.verify_url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            
            response_data = response.json()
            
            # Successful verification
            if response_data.get("data") and response_data["data"].get("code") in [100, 101]:
                 verification_data = response_data["data"]
                 if verification_data["code"] == 101:
                     logger.warning(f"Zarinpal payment verification indicates already verified. Authority: {authority}, Ref ID: {verification_data.get('ref_id')}")
                 else:
                    logger.info(f"Zarinpal payment verified successfully. Authority: {authority}, Ref ID: {verification_data.get('ref_id')}")
                 return verification_data # Contains code, message, card_hash, card_pan, ref_id, fee_type, fee
            else:
                # Handle Zarinpal specific errors
                error_code = response_data.get("errors", {}).get("code", -1)
                error_message = response_data.get("errors", {}).get("message", "Unknown Zarinpal verification error")
                logger.error(f"Zarinpal payment verification failed. Authority: {authority}, Code: {error_code}, Message: {error_message}, Response: {response_data}")
                raise ZarinpalAPIError(error_code, error_message, authority=authority)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error verifying Zarinpal payment. Authority: {authority}, Error: {e}", exc_info=True)
            raise ZarinpalAPIError(-500, f"Network error communicating with Zarinpal: {e}", authority=authority)
        except Exception as e:
            logger.error(f"Unexpected error verifying Zarinpal payment. Authority: {authority}, Error: {e}", exc_info=True)
            raise ZarinpalAPIError(-500, f"An unexpected error occurred: {e}", authority=authority)


# Create a singleton instance of the service
zarinpal_service = ZarinpalService() 