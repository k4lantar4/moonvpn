"""
ZarinPal payment integration for MoonVPN.

This module handles all ZarinPal-specific payment operations including
payment request, verification, and webhook handling.
"""

import logging
from typing import Optional, Dict, Any
import aiohttp
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.utils.payment import (
    format_amount,
    log_payment_event,
    validate_webhook_signature
)

logger = logging.getLogger(__name__)

class ZarinPalAPI:
    """ZarinPal payment gateway integration."""

    def __init__(self):
        """Initialize ZarinPal API client."""
        self.merchant = settings.ZARINPAL_MERCHANT
        self.sandbox = settings.ZARINPAL_SANDBOX
        self.callback_url = settings.ZARINPAL_CALLBACK_URL
        self.description = settings.ZARINPAL_DESCRIPTION
        
        # API endpoints
        self.base_url = "https://sandbox.zarinpal.com/pg" if self.sandbox else "https://api.zarinpal.com/pg/v4"
        self.payment_url = "https://sandbox.zarinpal.com/pg/StartPay" if self.sandbox else "https://www.zarinpal.com/pg/StartPay"

    async def request_payment(
        self,
        amount: float,
        description: Optional[str] = None,
        email: Optional[str] = None,
        mobile: Optional[str] = None,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Request a new payment from ZarinPal."""
        try:
            # Prepare request data
            data = {
                "MerchantID": self.merchant,
                "Amount": int(amount),  # ZarinPal expects amount in smallest currency unit
                "Description": description or self.description,
                "CallbackURL": self.callback_url,
                "Email": email,
                "Mobile": mobile,
                "OrderID": order_id
            }

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/PaymentRequest.json",
                    json=data
                ) as response:
                    result = await response.json()

            # Log the request
            log_payment_event(
                "zarinpal_payment_request",
                {
                    "amount": amount,
                    "description": description,
                    "email": email,
                    "mobile": mobile,
                    "order_id": order_id,
                    "response": result
                }
            )

            # Handle response
            if result["Status"] == 100:
                return {
                    "success": True,
                    "authority": result["Authority"],
                    "payment_url": f"{self.payment_url}/{result['Authority']}"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"ZarinPal payment request failed: {result['Message']}"
                )

        except aiohttp.ClientError as e:
            logger.error(f"ZarinPal API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service temporarily unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected error in ZarinPal payment request: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    async def verify_payment(
        self,
        authority: str,
        amount: float
    ) -> Dict[str, Any]:
        """Verify a payment with ZarinPal."""
        try:
            # Prepare request data
            data = {
                "MerchantID": self.merchant,
                "Authority": authority,
                "Amount": int(amount)  # ZarinPal expects amount in smallest currency unit
            }

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/PaymentVerification.json",
                    json=data
                ) as response:
                    result = await response.json()

            # Log the verification
            log_payment_event(
                "zarinpal_payment_verification",
                {
                    "authority": authority,
                    "amount": amount,
                    "response": result
                }
            )

            # Handle response
            if result["Status"] == 100:
                return {
                    "success": True,
                    "ref_id": result["RefID"],
                    "card_pan": result.get("CardPan"),
                    "card_hash": result.get("CardHash"),
                    "fee": result.get("Fee"),
                    "fee_type": result.get("FeeType")
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"ZarinPal payment verification failed: {result['Message']}"
                )

        except aiohttp.ClientError as e:
            logger.error(f"ZarinPal API verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service temporarily unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected error in ZarinPal payment verification: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """Handle ZarinPal webhook."""
        try:
            # Validate webhook signature
            if not validate_webhook_signature(payload, signature):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )

            # Parse webhook data
            data = await payload.json()

            # Log webhook data
            log_payment_event(
                "zarinpal_webhook",
                {
                    "data": data
                }
            )

            # Verify webhook data
            if not all(key in data for key in ["Authority", "Status", "RefID"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid webhook data"
                )

            return {
                "success": True,
                "authority": data["Authority"],
                "status": data["Status"],
                "ref_id": data["RefID"],
                "card_pan": data.get("CardPan"),
                "card_hash": data.get("CardHash"),
                "fee": data.get("Fee"),
                "fee_type": data.get("FeeType")
            }

        except Exception as e:
            logger.error(f"Error handling ZarinPal webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

# Create a singleton instance
zarinpal = ZarinPalAPI() 