"""
Zarinpal payment gateway integration for the V2Ray Telegram bot.

This module provides functions for creating and verifying payments using the Zarinpal API.
"""

import logging
import requests
import os
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ZarinpalClient:
    """Client for interacting with the Zarinpal payment gateway."""
    
    def __init__(self, merchant_id=None, sandbox=True):
        """
        Initialize the Zarinpal client.
        
        Args:
            merchant_id: Zarinpal merchant ID (defaults to env var ZARINPAL_MERCHANT_ID)
            sandbox: Whether to use the sandbox environment
        """
        self.merchant_id = merchant_id or os.getenv("ZARINPAL_MERCHANT_ID", "YOUR-MERCHANT-ID")
        self.sandbox = sandbox
        
        # API endpoints
        if self.sandbox:
            self.create_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
            self.verify_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
            self.payment_url = "https://sandbox.zarinpal.com/pg/StartPay/{}"
        else:
            self.create_url = "https://api.zarinpal.com/pg/v4/payment/request.json"
            self.verify_url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
            self.payment_url = "https://zarinpal.com/pg/StartPay/{}"
        
        self.callback_url = os.getenv("ZARINPAL_CALLBACK_URL", "https://example.com/callback")
    
    def create_payment(self, amount: int, user_id: int, description: str = None) -> Tuple[bool, str]:
        """
        Create a new payment request.
        
        Args:
            amount: Payment amount in Tomans
            user_id: Telegram user ID
            description: Payment description
            
        Returns:
            Tuple of (success, payment_url or error_message)
        """
        try:
            # Convert amount to Rials (Zarinpal uses Rials)
            amount_rials = amount * 10
            
            # Prepare request data
            data = {
                "MerchantID": self.merchant_id,
                "Amount": amount_rials,
                "Description": description or f"V2Ray account payment - User {user_id}",
                "CallbackURL": self.callback_url,
                "Metadata": {
                    "user_id": user_id,
                    "amount": amount
                }
            }
            
            # Send request
            response = requests.post(self.create_url, json=data)
            result = response.json()
            
            if response.status_code == 200 and result.get("Status") == 100:
                # Payment request successful
                authority = result.get("Authority")
                payment_url = self.payment_url.format(authority)
                return True, payment_url
            else:
                # Payment request failed
                error_code = result.get("Status", "Unknown")
                error_message = f"Payment request failed with code {error_code}"
                logger.error(error_message)
                return False, error_message
                
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return False, str(e)
    
    def verify_payment(self, authority: str, amount: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify a payment.
        
        Args:
            authority: Payment authority code
            amount: Payment amount in Tomans
            
        Returns:
            Tuple of (success, result_data)
        """
        try:
            # Convert amount to Rials
            amount_rials = amount * 10
            
            # Prepare request data
            data = {
                "MerchantID": self.merchant_id,
                "Authority": authority,
                "Amount": amount_rials
            }
            
            # Send request
            response = requests.post(self.verify_url, json=data)
            result = response.json()
            
            if response.status_code == 200 and result.get("Status") == 100:
                # Payment verified
                ref_id = result.get("RefID")
                return True, {
                    "ref_id": ref_id,
                    "authority": authority,
                    "amount": amount
                }
            else:
                # Payment verification failed
                error_code = result.get("Status", "Unknown")
                return False, {
                    "error_code": error_code,
                    "error_message": f"Payment verification failed with code {error_code}"
                }
                
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False, {"error_message": str(e)}

# For backward compatibility
def create_payment(amount: int, user_id: int) -> Optional[str]:
    """
    Create a new payment request (legacy function).
    
    Args:
        amount: Payment amount in Tomans
        user_id: Telegram user ID
        
    Returns:
        Payment URL if successful, None otherwise
    """
    client = ZarinpalClient()
    success, result = client.create_payment(amount, user_id)
    return result if success else None

def verify_payment(authority: str, amount: int = 0) -> bool:
    """
    Verify a payment (legacy function).
    
    Args:
        authority: Payment authority code
        amount: Payment amount in Tomans
        
    Returns:
        True if payment is verified, False otherwise
    """
    client = ZarinpalClient()
    success, _ = client.verify_payment(authority, amount)
    return success 