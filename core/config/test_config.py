import pytest
from app.core.config import settings

class TestSettings:
    def test_database_url(self):
        """Test database URL configuration"""
        assert settings.DATABASE_URL is not None
        assert isinstance(settings.DATABASE_URL, str)
        assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")

    def test_secret_key(self):
        """Test secret key configuration"""
        assert settings.SECRET_KEY is not None
        assert isinstance(settings.SECRET_KEY, str)
        assert len(settings.SECRET_KEY) >= 32

    def test_algorithm(self):
        """Test JWT algorithm configuration"""
        assert settings.ALGORITHM == "HS256"

    def test_access_token_expire_minutes(self):
        """Test access token expiration configuration"""
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)

    def test_refresh_token_expire_days(self):
        """Test refresh token expiration configuration"""
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0
        assert isinstance(settings.REFRESH_TOKEN_EXPIRE_DAYS, int)

    def test_telegram_bot_token(self):
        """Test Telegram bot token configuration"""
        assert settings.TELEGRAM_BOT_TOKEN is not None
        assert isinstance(settings.TELEGRAM_BOT_TOKEN, str)

    def test_telegram_webhook_url(self):
        """Test Telegram webhook URL configuration"""
        assert settings.TELEGRAM_WEBHOOK_URL is not None
        assert isinstance(settings.TELEGRAM_WEBHOOK_URL, str)
        assert settings.TELEGRAM_WEBHOOK_URL.startswith("https://")

    def test_telegram_admin_ids(self):
        """Test Telegram admin IDs configuration"""
        assert settings.TELEGRAM_ADMIN_IDS is not None
        assert isinstance(settings.TELEGRAM_ADMIN_IDS, list)
        assert all(isinstance(id, int) for id in settings.TELEGRAM_ADMIN_IDS)

    def test_telegram_commands(self):
        """Test Telegram commands configuration"""
        assert settings.TELEGRAM_COMMANDS is not None
        assert isinstance(settings.TELEGRAM_COMMANDS, list)
        assert all(isinstance(cmd, dict) for cmd in settings.TELEGRAM_COMMANDS)
        assert all("command" in cmd and "description" in cmd for cmd in settings.TELEGRAM_COMMANDS)

    def test_vpn_config(self):
        """Test VPN configuration"""
        assert settings.VPN_CONFIG is not None
        assert isinstance(settings.VPN_CONFIG, dict)
        assert "server_address" in settings.VPN_CONFIG
        assert "server_port" in settings.VPN_CONFIG
        assert "protocol" in settings.VPN_CONFIG

    def test_payment_config(self):
        """Test payment configuration"""
        assert settings.PAYMENT_CONFIG is not None
        assert isinstance(settings.PAYMENT_CONFIG, dict)
        assert "merchant_id" in settings.PAYMENT_CONFIG
        assert "merchant_key" in settings.PAYMENT_CONFIG
        assert "merchant_salt" in settings.PAYMENT_CONFIG

    def test_environment(self):
        """Test environment configuration"""
        assert settings.ENVIRONMENT in ["development", "production", "testing"]
        assert isinstance(settings.ENVIRONMENT, str)

    def test_debug_mode(self):
        """Test debug mode configuration"""
        assert isinstance(settings.DEBUG_MODE, bool)
        if settings.ENVIRONMENT == "production":
            assert not settings.DEBUG_MODE

    def test_cors_origins(self):
        """Test CORS origins configuration"""
        assert settings.CORS_ORIGINS is not None
        assert isinstance(settings.CORS_ORIGINS, list)
        assert all(isinstance(origin, str) for origin in settings.CORS_ORIGINS)

    def test_api_prefix(self):
        """Test API prefix configuration"""
        assert settings.API_PREFIX == "/api/v1"
        assert isinstance(settings.API_PREFIX, str)

    def test_project_name(self):
        """Test project name configuration"""
        assert settings.PROJECT_NAME == "MoonVPN"
        assert isinstance(settings.PROJECT_NAME, str)

    def test_version(self):
        """Test version configuration"""
        assert settings.VERSION == "1.0.0"
        assert isinstance(settings.VERSION, str)

    def test_description(self):
        """Test description configuration"""
        assert settings.DESCRIPTION is not None
        assert isinstance(settings.DESCRIPTION, str)
        assert len(settings.DESCRIPTION) > 0 