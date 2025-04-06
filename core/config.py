from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import json
from typing import List, Optional

class Settings(BaseSettings):
    # --- General / تنظیمات عمومی ---
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "your_very_secret_key_here"
    LOG_LEVEL: str = "INFO"
    DEFAULT_LANGUAGE: str = "fa"
    SUPPORTED_LANGUAGES: str = '["fa", "en"]'  # JSON string

    @property
    def SUPPORTED_LANGUAGES_LIST(self) -> List[str]:
        try:
            return json.loads(self.SUPPORTED_LANGUAGES)
        except json.JSONDecodeError:
            return ["fa", "en"]

    # --- Database (MySQL) / پایگاه داده ---
    MYSQL_HOST: str = "db"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "moonvpn_user"
    MYSQL_PASSWORD: str = "your_strong_db_password"
    MYSQL_DATABASE: str = "moonvpn_db"
    MYSQL_ROOT_PASSWORD: str = "your_strong_root_password"

    @property
    def DATABASE_URL(self) -> str:
        from urllib.parse import quote_plus
        quoted_password = quote_plus(self.MYSQL_PASSWORD)
        return f"mysql+mysqlconnector://{self.MYSQL_USER}:{quoted_password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    # --- Redis Cache / ردیس کش ---
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    REDIS_MAX_CONNECTIONS: int = 10

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        protocol = "rediss" if self.REDIS_SSL else "redis"
        return f"{protocol}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # --- API Server / سرور API ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    WORKERS_COUNT: int = 1
    CORS_ORIGINS: str = '["http://localhost:3000"]'  # JSON string
    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except json.JSONDecodeError:
            return ["http://localhost:3000"]

    # --- Telegram Bot / ربات تلگرام ---
    TELEGRAM_BOT_TOKEN: str = "your_telegram_bot_token_here"
    TELEGRAM_ADMIN_ID: int = 0
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None

    # --- Telegram Channels / کانال‌های تلگرام ---
    ADMIN_CHANNEL_ID: Optional[str] = None
    PAYMENT_CHANNEL_ID: Optional[str] = None
    REPORT_CHANNEL_ID: Optional[str] = None
    LOG_CHANNEL_ID: Optional[str] = None
    ALERT_CHANNEL_ID: Optional[str] = None
    BACKUP_CHANNEL_ID: Optional[str] = None

    # --- 3x-ui Panel / تنظیمات پنل ---
    PANEL1_URL: Optional[str] = None
    PANEL1_USERNAME: Optional[str] = None
    PANEL1_PASSWORD: Optional[str] = None
    PANEL1_LOCATION: Optional[str] = None

    # --- Payment Gateway / درگاه پرداخت ---
    ZARINPAL_MERCHANT_ID: Optional[str] = None
    ZARINPAL_SANDBOX: bool = True

    # --- SMS Service / سرویس پیامک ---
    SMS_API_KEY: Optional[str] = None
    SMS_SENDER: Optional[str] = None
    SMS_TEMPLATE_VERIFICATION: Optional[str] = None

    # --- Docker & Tools / داکر و ابزارها ---
    PHPMYADMIN_PORT: int = 8080
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000

    # --- Security & JWT / امنیت و توکن ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    PASSWORD_SALT: Optional[str] = None

    # --- System Limits / محدودیت‌های سیستم ---
    MAX_CLIENTS_PER_PANEL: int = 500
    MAX_DAILY_TRIALS: int = 50
    DEFAULT_TRAFFIC_LIMIT: int = 100

    # Load settings from .env file
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() == "testing"

    def validate_required_settings(self) -> List[str]:
        """Validates critical settings and returns a list of missing required settings."""
        missing = []
        
        # Critical settings that must be set in production
        if self.is_production():
            required_settings = {
                "SECRET_KEY": self.SECRET_KEY != "your_very_secret_key_here",
                "TELEGRAM_BOT_TOKEN": self.TELEGRAM_BOT_TOKEN != "your_telegram_bot_token_here",
                "TELEGRAM_ADMIN_ID": self.TELEGRAM_ADMIN_ID != 0,
                "MYSQL_PASSWORD": self.MYSQL_PASSWORD != "your_strong_db_password",
                "MYSQL_ROOT_PASSWORD": self.MYSQL_ROOT_PASSWORD != "your_strong_root_password",
                "PASSWORD_SALT": bool(self.PASSWORD_SALT),
            }
            
            missing.extend(
                setting for setting, is_set in required_settings.items()
                if not is_set
            )
            
            # Additional production requirements
            if not self.TELEGRAM_WEBHOOK_URL:
                missing.append("TELEGRAM_WEBHOOK_URL")
            if not self.TELEGRAM_WEBHOOK_SECRET:
                missing.append("TELEGRAM_WEBHOOK_SECRET")
        
        return missing

# Use lru_cache to load settings only once
@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the settings.
    
    The settings are loaded from the .env file and cached for performance.
    In development mode, you might want to reload settings more frequently.
    """
    settings = Settings()
    
    # Validate settings in production
    if settings.is_production():
        missing = settings.validate_required_settings()
        if missing:
            raise ValueError(
                f"Missing required settings in production: {', '.join(missing)}"
            )
    
    return settings

# Instantiate settings for easy import elsewhere if needed, though get_settings is preferred
# settings = get_settings()
