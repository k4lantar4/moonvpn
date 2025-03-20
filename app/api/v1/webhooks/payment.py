"""
Payment webhook handler for MoonVPN.

This module handles webhook notifications from various payment gateways
including ZarinPal, bank transfers, and other payment methods.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.services.payment_service import PaymentService
from app.core.integrations.zarinpal import zarinpal
from app.core.utils.payment import (
    log_payment_event,
    validate_webhook_signature
)
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/zarinpal")
async def zarinpal_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle ZarinPal webhook notifications."""
    try:
        # Get webhook signature
        signature = request.headers.get("X-ZarinPal-Signature")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature"
            )

        # Get request body
        body = await request.body()

        # Process webhook with ZarinPal integration
        webhook_data = await zarinpal.handle_webhook(body, signature)

        # Get payment service
        payment_service = PaymentService(db)

        # Verify payment
        await payment_service.verify_payment(
            authority=webhook_data["authority"],
            status="OK" if webhook_data["status"] == 100 else "FAILED",
            ref_id=webhook_data["ref_id"]
        )

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing ZarinPal webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.post("/bank-transfer")
async def bank_transfer_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle bank transfer webhook notifications."""
    try:
        # Get webhook signature
        signature = request.headers.get("X-Bank-Signature")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature"
            )

        # Get request body
        body = await request.body()

        # Validate webhook signature
        if not validate_webhook_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        # Parse webhook data
        data = await request.json()

        # Log webhook data
        log_payment_event(
            "bank_transfer_webhook",
            {
                "data": data
            }
        )

        # Verify required fields
        required_fields = ["transaction_id", "status", "amount", "reference"]
        if not all(field in data for field in required_fields):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook data"
            )

        # Get payment service
        payment_service = PaymentService(db)

        # Update transaction status
        if data["status"] == "completed":
            await payment_service.verify_payment(
                authority=data["transaction_id"],
                status="OK",
                ref_id=data["reference"]
            )
        else:
            await payment_service.verify_payment(
                authority=data["transaction_id"],
                status="FAILED",
                ref_id=data["reference"]
            )

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing bank transfer webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.post("/card")
async def card_payment_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle card payment webhook notifications."""
    try:
        # Get webhook signature
        signature = request.headers.get("X-Card-Signature")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature"
            )

        # Get request body
        body = await request.body()

        # Validate webhook signature
        if not validate_webhook_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        # Parse webhook data
        data = await request.json()

        # Log webhook data
        log_payment_event(
            "card_payment_webhook",
            {
                "data": data
            }
        )

        # Verify required fields
        required_fields = ["transaction_id", "status", "amount", "card_last4"]
        if not all(field in data for field in required_fields):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook data"
            )

        # Get payment service
        payment_service = PaymentService(db)

        # Update transaction status
        if data["status"] == "succeeded":
            await payment_service.verify_payment(
                authority=data["transaction_id"],
                status="OK",
                ref_id=data.get("payment_intent_id")
            )
        else:
            await payment_service.verify_payment(
                authority=data["transaction_id"],
                status="FAILED",
                ref_id=data.get("payment_intent_id")
            )

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing card payment webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        ) 