import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    AnyHttpUrl, EmailStr, PostgresDsn, 
    SecretStr, field_validator, model_validator
)
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Settings loaded from environment variables
    """
    # API General Settings
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # production, development, testing
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    PROJECT_NAME: str = "MoonVPN"
    SECRET_KEY: str
    API_SECRET_KEY: Optional[str] = None
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    @field_validator("API_SECRET_KEY")
    def validate_api_secret_key(cls, v, info):
        # If API_SECRET_KEY is not set, use SECRET_KEY
        if not v:
            return info.data.get("SECRET_KEY")
        return v
    
    # Security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_ALGORITHM: str = "HS256"
    
    # Database settings
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    DATABASE_URI: Optional[str] = None
    
    # Cache settings
    CACHE_KEY_PREFIX: str = "moonvpn"
    CACHE_DEFAULT_TTL: int = 3600  # In seconds (1 hour)
    
    # Panel Service settings
    DEFAULT_PANEL_TYPE: str = "3x-ui"
    PANEL_CONNECTION_TIMEOUT: int = 30  # In seconds
    PANEL_API_RETRY_COUNT: int = 3
    PANEL_HEALTH_CHECK_INTERVAL: int = 900  # In seconds (15 minutes)
    PANEL_ENCRYPTION_KEY: Optional[str] = None
    
    # Environment variables that will be loaded
    DEFAULT_LANGUAGE: Optional[str] = None
    SUPPORTED_LANGUAGES: Optional[str] = None
    MYSQL_ROOT_PASSWORD: Optional[str] = None
    REDIS_SSL: Optional[str] = None
    REDIS_MAX_CONNECTIONS: Optional[str] = None
    API_HOST: Optional[str] = None
    WORKERS_COUNT: Optional[str] = None
    CORS_ORIGINS: Optional[str] = None
    RATE_LIMIT_PER_MINUTE: Optional[str] = None
    TELEGRAM_ADMIN_ID: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None
    ADMIN_CHANNEL_ID: Optional[str] = None
    PAYMENT_CHANNEL_ID: Optional[str] = None
    REPORT_CHANNEL_ID: Optional[str] = None
    ALERT_CHANNEL_ID: Optional[str] = None
    BACKUP_CHANNEL_ID: Optional[str] = None
    ZARINPAL_SANDBOX: Optional[str] = None
    PHPMYADMIN_PORT: Optional[str] = None
    PROMETHEUS_PORT: Optional[str] = None
    GRAFANA_PORT: Optional[str] = None
    REFRESH_TOKEN_EXPIRE_DAYS: Optional[str] = None
    ALGORITHM: Optional[str] = None
    PASSWORD_SALT: Optional[str] = None
    MAX_CLIENTS_PER_PANEL: Optional[str] = None
    MAX_DAILY_TRIALS: Optional[str] = None
    DEFAULT_TRAFFIC_LIMIT: Optional[str] = None
    
    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        return f"mysql+aiomysql://{values.get('MYSQL_USER')}:{values.get('MYSQL_PASSWORD')}@{values.get('MYSQL_HOST')}:{values.get('MYSQL_PORT')}/{values.get('MYSQL_DATABASE')}"
    
    @field_validator("PANEL_ENCRYPTION_KEY")
    def validate_panel_encryption_key(cls, v: Optional[str], info):
        # If PANEL_ENCRYPTION_KEY is not set, use a derivative of SECRET_KEY
        if not v:
            secret_key = info.data.get("SECRET_KEY", "")
            # Use a different part of the SECRET_KEY to avoid using the same value
            return secret_key[-32:] if len(secret_key) >= 32 else secret_key
        return v
    
    # Telegram Bot settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_IDS: List[int] = []
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    LOG_CHANNEL_ID: Optional[str] = None
    
    @field_validator("TELEGRAM_ADMIN_IDS", mode="before")
    def parse_admin_ids(cls, v: Union[str, List[int]]) -> List[int]:
        if isinstance(v, str):
            # حذف گیومه‌های احتمالی از ابتدا و انتهای رشته
            v = v.strip('"\'')
            return [int(i.strip()) for i in v.split(",") if i.strip().isdigit()]
        elif isinstance(v, int):
            # اگر یک عدد صحیح باشد، آن را در یک لیست قرار می‌دهیم
            return [v]
        return v
    
    # Redis Cache settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # System settings
    DEFAULT_REMARK_PATTERN: str = "{prefix}-{id}-{custom}"
    MIGRATION_REMARK_PATTERN: str = "{original}-M{count}"
    
    # External Service Integration
    ZARINPAL_MERCHANT_ID: Optional[str] = None
    
    # Helper methods
    def is_development(self) -> bool:
        """Check if the environment is development."""
        return self.ENVIRONMENT.lower() == "development"

    def is_production(self) -> bool:
        """Check if the environment is production."""
        return self.ENVIRONMENT.lower() == "production"

    def is_testing(self) -> bool:
        """Check if the environment is testing."""
        return self.ENVIRONMENT.lower() == "testing"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="allow"  # Allow extra fields that are not defined in the model
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Returns the settings object, cached for better performance.
    """
    return Settings() 