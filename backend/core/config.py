"""Configuration settings for the application."""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    """Application settings."""
    # Debug settings
    DEBUG: bool = False
    ALLOWED_HOSTS: str

    @validator("ALLOWED_HOSTS")
    def parse_allowed_hosts(cls, v: str) -> List[str]:
        """Parse ALLOWED_HOSTS from comma-separated string to list."""
        return [host.strip() for host in v.split(",")]

    # Database settings
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # Field encryption
    FIELD_ENCRYPTION_KEY: str

    # Redis settings
    REDIS_URL: str

    # Email settings
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USE_TLS: bool
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str
    DEFAULT_FROM_EMAIL: str

    # Telegram settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str
    TELEGRAM_ADMIN_GROUP_ID: str

    # Payment settings
    ZARINPAL_MERCHANT: str
    ZARINPAL_SANDBOX: bool
    ZARINPAL_CALLBACK_URL: str

    # Points system settings
    POINTS_PER_PURCHASE: int
    POINTS_PER_REFERRAL: int
    POINTS_EXPIRY_DAYS: int

    # Live chat settings
    LIVE_CHAT_ENABLED: bool
    MAX_CHAT_SESSIONS: int
    CHAT_TIMEOUT_MINUTES: int

    # Card payment settings
    CARD_PAYMENT_VERIFICATION_TIMEOUT_MINUTES: int
    CARD_PAYMENT_NUMBER: str
    CARD_PAYMENT_HOLDER: str
    CARD_PAYMENT_BANK: str
    ADMIN_NOTIFICATION_ENABLED: bool

    # Security settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # API settings
    API_V1_STR: str
    PROJECT_NAME: str

    # CORS settings
    BACKEND_CORS_ORIGINS: str

    @validator("BACKEND_CORS_ORIGINS")
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse BACKEND_CORS_ORIGINS from JSON string to list."""
        import json
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return [origin.strip() for origin in v.split(",")]

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        db_url = f"postgresql+asyncpg://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}@{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"
        print(f"Database URL: {db_url}")
        return db_url

    class Config:
        """Pydantic config."""
        case_sensitive = True
        env_file = ".env"

settings = Settings()
print(f"Settings loaded with database URL: {settings.SQLALCHEMY_DATABASE_URI}") 