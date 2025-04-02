from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List

from app import models
from app.api import deps
from app.core.config import settings
from app.models.order import PaymentMethod

router = APIRouter()


class PaymentMethodsResponse(BaseModel):
    """Response model for payment method settings"""
    zarinpal_enabled: bool
    wallet_enabled: bool
    crypto_enabled: bool


@router.get("/payment-methods", response_model=PaymentMethodsResponse)
async def get_payment_methods(
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Returns the currently enabled payment methods based on system configuration.
    This endpoint is used by the Telegram bot to determine which payment options to display.
    """
    # Check Zarinpal configuration
    zarinpal_enabled = (
        settings.ZARINPAL_ENABLED and 
        settings.ZARINPAL_MERCHANT_ID is not None and 
        settings.ZARINPAL_CALLBACK_URL_BASE is not None
    )
    
    # For now, we'll assume wallet is always enabled
    # In the future, this could check for wallet-specific configuration
    wallet_enabled = True
    
    # Crypto is not implemented yet
    crypto_enabled = False
    
    return PaymentMethodsResponse(
        zarinpal_enabled=zarinpal_enabled,
        wallet_enabled=wallet_enabled,
        crypto_enabled=crypto_enabled
    )


@router.get("/zarinpal/info")
async def get_zarinpal_info(
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    A simple endpoint to check if Zarinpal is configured and enabled.
    This is used as a fallback by the Telegram bot if the payment-methods endpoint fails.
    """
    return {
        "enabled": settings.ZARINPAL_ENABLED and 
                   settings.ZARINPAL_MERCHANT_ID is not None and 
                   settings.ZARINPAL_CALLBACK_URL_BASE is not None
    } 