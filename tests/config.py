"""Test configuration settings."""

from typing import Dict, Any
from pydantic_settings import BaseSettings
from app.core.config import settings

class TestSettings(BaseSettings):
    """Test-specific settings."""
    
    # Database
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    
    # Security
    TEST_SECRET_KEY: str = "test_secret_key"
    TEST_ALGORITHM: str = "HS256"
    TEST_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # VPN
    TEST_VPN_SERVER: str = "test.vpn.server"
    TEST_VPN_PORT: int = 1194
    TEST_VPN_PROTOCOL: str = "udp"
    TEST_VPN_CIPHER: str = "AES-256-CBC"
    TEST_VPN_AUTH: str = "SHA256"
    
    # Payment
    TEST_STRIPE_SECRET_KEY: str = "test_stripe_secret_key"
    TEST_STRIPE_WEBHOOK_SECRET: str = "test_stripe_webhook_secret"
    
    # Telegram
    TEST_TELEGRAM_BOT_TOKEN: str = "test_telegram_bot_token"
    TEST_TELEGRAM_API_ID: str = "test_telegram_api_id"
    TEST_TELEGRAM_API_HASH: str = "test_telegram_api_hash"
    
    # Test Data
    TEST_USER_EMAIL: str = "test@example.com"
    TEST_USER_PASSWORD: str = "test_password123"
    TEST_USER_USERNAME: str = "test_user"
    
    # Performance Test Settings
    PERFORMANCE_TEST_USERS: int = 100
    PERFORMANCE_TEST_REQUESTS: int = 1000
    PERFORMANCE_TEST_TIMEOUT: int = 30
    
    class Config:
        """Pydantic config."""
        env_file = ".env.test"
        case_sensitive = True

# Create test settings instance
test_settings = TestSettings()

# Test data templates
TEST_VPN_CONFIG_TEMPLATE: Dict[str, Any] = {
    "name": "test_vpn_config",
    "server": test_settings.TEST_VPN_SERVER,
    "port": test_settings.TEST_VPN_PORT,
    "protocol": test_settings.TEST_VPN_PROTOCOL,
    "cipher": test_settings.TEST_VPN_CIPHER,
    "auth": test_settings.TEST_VPN_AUTH,
    "is_active": True
}

TEST_PAYMENT_TEMPLATE: Dict[str, Any] = {
    "amount": 10.0,
    "currency": "USD",
    "payment_method": "credit_card",
    "status": "completed",
    "transaction_id": "test_transaction_id"
}

TEST_TELEGRAM_USER_TEMPLATE: Dict[str, Any] = {
    "telegram_id": 123456789,
    "username": "test_telegram_user",
    "first_name": "Test",
    "last_name": "User",
    "is_active": True
} 