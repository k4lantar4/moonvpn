"""
Payment configuration for MoonVPN.

This module contains payment-related configuration settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional

class PaymentSettings(BaseSettings):
    """Payment configuration settings."""
    
    # ZarinPal settings
    ZARINPAL_MERCHANT_ID: str
    ZARINPAL_SANDBOX: bool = True
    ZARINPAL_CALLBACK_URL: str
    
    # Bank transfer settings
    BANK_NAME: str
    BANK_ACCOUNT: str
    BANK_HOLDER: str
    
    # Payment form settings
    PAYMENT_FORM_URL: str
    
    # Wallet settings
    MIN_WALLET_BALANCE: float = 0.0
    MAX_WALLET_BALANCE: float = 1000000.0
    
    # Transaction settings
    TRANSACTION_TIMEOUT: int = 3600  # 1 hour in seconds
    MAX_RETRY_ATTEMPTS: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create payment settings instance
payment_settings = PaymentSettings() 