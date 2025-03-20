"""
Base configuration for test settings.
This module provides the base configuration for all test environments.
"""
from typing import Dict, Any
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    """Test environment settings."""
    
    # Database settings
    TEST_DATABASE_URL: str = "sqlite:///./test.db"
    TEST_DATABASE_ECHO: bool = False
    
    # Redis settings
    TEST_REDIS_URL: str = "redis://localhost:6379/1"
    TEST_REDIS_PREFIX: str = "test:"
    
    # JWT settings
    TEST_JWT_SECRET: str = "test_secret_key"
    TEST_JWT_ALGORITHM: str = "HS256"
    TEST_JWT_EXPIRE_MINUTES: int = 30
    
    # Telegram settings
    TEST_TELEGRAM_BOT_TOKEN: str = "test_bot_token"
    TEST_TELEGRAM_WEBHOOK_URL: str = "http://localhost:8000/webhook"
    
    # Payment settings
    TEST_PAYMENT_API_KEY: str = "test_payment_key"
    TEST_PAYMENT_WEBHOOK_URL: str = "http://localhost:8000/payment/webhook"
    
    # 3x-UI Panel settings
    TEST_PANEL_URL: str = "http://localhost:8080"
    TEST_PANEL_USERNAME: str = "test_admin"
    TEST_PANEL_PASSWORD: str = "test_password"
    
    # Test user settings
    TEST_USER_PHONE: str = "+989123456789"
    TEST_USER_PASSWORD: str = "test_password123"
    TEST_USER_EMAIL: str = "test@example.com"
    
    # Test admin settings
    TEST_ADMIN_PHONE: str = "+989123456790"
    TEST_ADMIN_PASSWORD: str = "admin_password123"
    TEST_ADMIN_EMAIL: str = "admin@example.com"
    
    # Test server settings
    TEST_SERVER_HOST: str = "test.vpn.example.com"
    TEST_SERVER_PORT: int = 443
    TEST_SERVER_PROTOCOL: str = "tls"
    
    class Config:
        """Pydantic config."""
        env_file = ".env.test"
        case_sensitive = True

def get_test_settings() -> TestSettings:
    """Get test settings instance."""
    return TestSettings()

def get_test_config() -> Dict[str, Any]:
    """Get test configuration dictionary."""
    settings = get_test_settings()
    return settings.model_dump() 