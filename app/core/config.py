"""
Configuration settings for MoonVPN application.

This module contains all configuration settings for the application,
including bot settings, database configuration, and API endpoints.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "MoonVPN"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Bot Settings
    TELEGRAM_BOT_TOKEN: SecretStr
    WEBHOOK_BASE_URL: str
    WEBHOOK_PATH: str = "/webhook"
    
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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 3x-UI Panel
    PANEL_BASE_URL: str
    PANEL_USERNAME: str
    PANEL_PASSWORD: SecretStr
    
    # Payment
    ZARINPAL_MERCHANT: Optional[SecretStr] = None
    
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