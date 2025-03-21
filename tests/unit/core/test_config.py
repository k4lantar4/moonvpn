"""Unit tests for configuration settings."""

import pytest
from app.core.config import settings

class TestSettings:
    """Test application settings."""
    
    def test_database_settings(self):
        """Test database configuration."""
        assert settings.DATABASE_URL is not None
        assert isinstance(settings.DATABASE_URL, str)
        assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
    
    def test_security_settings(self):
        """Test security configuration."""
        assert settings.SECRET_KEY is not None
        assert isinstance(settings.SECRET_KEY, str)
        assert len(settings.SECRET_KEY) >= 32
        assert settings.ALGORITHM == "HS256"
        assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    
    def test_vpn_settings(self):
        """Test VPN configuration."""
        assert settings.VPN_SERVER is not None
        assert isinstance(settings.VPN_SERVER, str)
        assert settings.VPN_PORT is not None
        assert isinstance(settings.VPN_PORT, int)
        assert settings.VPN_PORT > 0
        assert settings.VPN_PROTOCOL in ["udp", "tcp"]
        assert settings.VPN_CIPHER is not None
        assert settings.VPN_AUTH is not None
    
    def test_payment_settings(self):
        """Test payment configuration."""
        assert settings.STRIPE_SECRET_KEY is not None
        assert isinstance(settings.STRIPE_SECRET_KEY, str)
        assert settings.STRIPE_WEBHOOK_SECRET is not None
        assert isinstance(settings.STRIPE_WEBHOOK_SECRET, str)
    
    def test_telegram_settings(self):
        """Test Telegram configuration."""
        assert settings.TELEGRAM_BOT_TOKEN is not None
        assert isinstance(settings.TELEGRAM_BOT_TOKEN, str)
        assert settings.TELEGRAM_API_ID is not None
        assert isinstance(settings.TELEGRAM_API_ID, str)
        assert settings.TELEGRAM_API_HASH is not None
        assert isinstance(settings.TELEGRAM_API_HASH, str)
    
    def test_cors_settings(self):
        """Test CORS configuration."""
        assert settings.CORS_ORIGINS is not None
        assert isinstance(settings.CORS_ORIGINS, list)
        assert all(isinstance(origin, str) for origin in settings.CORS_ORIGINS)
    
    def test_rate_limit_settings(self):
        """Test rate limit configuration."""
        assert settings.RATE_LIMIT_PER_MINUTE is not None
        assert isinstance(settings.RATE_LIMIT_PER_MINUTE, int)
        assert settings.RATE_LIMIT_PER_MINUTE > 0
    
    def test_logging_settings(self):
        """Test logging configuration."""
        assert settings.LOG_LEVEL is not None
        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert settings.LOG_FORMAT is not None
        assert isinstance(settings.LOG_FORMAT, str) 