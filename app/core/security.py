"""
Security utilities for MoonVPN.

This module provides security-related functions for the application,
including Telegram request verification and other security features.
"""

import hmac
import hashlib
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

def verify_telegram_request(
    request_body: bytes,
    secret_token: Optional[str] = None
) -> bool:
    """
    Verify that a request is coming from Telegram.
    
    Args:
        request_body: The raw request body
        secret_token: The secret token from request headers
        
    Returns:
        bool: True if request is valid, False otherwise
    """
    try:
        # Check if secret token matches
        if secret_token != settings.TELEGRAM_BOT_SECRET_TOKEN:
            logger.warning("Invalid secret token in request")
            return False
            
        # Calculate HMAC
        hmac_obj = hmac.new(
            key=settings.TELEGRAM_BOT_TOKEN.encode(),
            msg=request_body,
            digestmod=hashlib.sha256
        )
        calculated_hash = hmac_obj.hexdigest()
        
        # Compare with provided hash
        return calculated_hash == secret_token
        
    except Exception as e:
        logger.error(f"Error verifying Telegram request: {str(e)}")
        return False

def generate_telegram_secret_token() -> str:
    """
    Generate a secret token for Telegram webhook verification.
    
    Returns:
        str: The generated secret token
    """
    try:
        # Generate a random token
        token = hmac.new(
            key=settings.TELEGRAM_BOT_TOKEN.encode(),
            msg=settings.SECRET_KEY.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return token
        
    except Exception as e:
        logger.error(f"Error generating secret token: {str(e)}")
        raise 