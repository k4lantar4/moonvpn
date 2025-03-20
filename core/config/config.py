"""
Configuration settings for MoonVPN application.

This module contains all configuration settings for the application,
including bot settings, database configuration, and API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, validator
import logging
import secrets

# Setup logging
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "MoonVPN"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Bot Settings
    TELEGRAM_BOT_TOKEN: SecretStr
    TELEGRAM_BOT_SECRET_TOKEN: Optional[SecretStr] = None
    TELEGRAM_BOT_USERNAME: Optional[str] = None
    TELEGRAM_BOT_NAME: Optional[str] = None
    TELEGRAM_BOT_DESCRIPTION: Optional[str] = None
    TELEGRAM_BOT_COMMANDS: List[dict] = []
    TELEGRAM_BOT_ADMIN_IDS: List[int] = []
    TELEGRAM_BOT_SUPPORT_GROUP_ID: Optional[int] = None
    TELEGRAM_BOT_LOGS_GROUP_ID: Optional[int] = None
    TELEGRAM_BOT_BROADCAST_GROUP_ID: Optional[int] = None
    WEBHOOK_BASE_URL: str
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_ALLOWED_UPDATES: List[str] = [
        "message",
        "callback_query",
        "edited_message",
        "channel_post",
        "edited_channel_post",
        "inline_query",
        "chosen_inline_result",
        "shipping_query",
        "pre_checkout_query",
        "poll",
        "poll_answer",
        "my_chat_member",
        "chat_member",
        "chat_join_request"
    ]
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[SecretStr] = None
    
    # Security
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # 3x-UI Panel
    PANEL_BASE_URL: str
    PANEL_USERNAME: str
    PANEL_PASSWORD: SecretStr
    PANEL_API_URL: str
    PANEL_API_USERNAME: str
    PANEL_API_PASSWORD: SecretStr
    
    # Payment
    ZARINPAL_MERCHANT: Optional[SecretStr] = None
    ZARINPAL_SANDBOX: bool = True
    ZARINPAL_CALLBACK_URL: str
    ZARINPAL_DESCRIPTION: str = "MoonVPN Subscription"
    
    # Payment Gateway URLs
    PAYMENT_FORM_URL: str = "https://payment.moonvpn.com"
    PAYMENT_SUCCESS_URL: str = "https://moonvpn.com/payment/success"
    PAYMENT_FAIL_URL: str = "https://moonvpn.com/payment/fail"
    
    # Bank Transfer Settings
    BANK_NAME: str
    BANK_ACCOUNT: str
    BANK_HOLDER: str
    BANK_IBAN: Optional[str] = None
    
    # Wallet Settings
    MAX_WALLET_BALANCE: float = 1000.0
    MIN_WALLET_BALANCE: float = 0.0
    DEFAULT_CURRENCY: str = "USD"
    
    # Payment Retry Settings
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 5
    
    # Payment Webhook Settings
    WEBHOOK_SECRET: str = secrets.token_urlsafe(32)
    WEBHOOK_TIMEOUT: int = 30
    
    # Payment Logging
    PAYMENT_LOG_LEVEL: str = "INFO"
    PAYMENT_LOG_FILE: str = "payment.log"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
        
    def __init__(self, **kwargs):
        """Initialize settings and compute derived values."""
        super().__init__(**kwargs)
        
        # Compute database URI
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
                f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            )

# Create settings instance
settings = Settings() 

# Generate Telegram bot secret token if not set
if not settings.TELEGRAM_BOT_SECRET_TOKEN:
    from app.core.security import generate_telegram_secret_token
    settings.TELEGRAM_BOT_SECRET_TOKEN = SecretStr(generate_telegram_secret_token())
    logger.info("Generated new Telegram bot secret token") 