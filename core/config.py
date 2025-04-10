"""Core settings management using Pydantic."""

from typing import Literal, List, Optional, Any, Dict
# Import SecretStr from pydantic and validator tools
from pydantic import SecretStr, model_validator, field_validator, FieldValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """
    Reads configuration settings from environment variables or a .env file.
    """
    ENVIRONMENT: Literal["dev", "test", "prod"] = "dev"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- Database ---
    DB_HOST: str = "db"
    DB_PORT: str = "3306"
    DB_USER: str = "moonvpn_user"
    DB_PASSWORD: SecretStr
    DB_NAME: str = "moonvpn_db"
    DB_ROOT_PASSWORD: Optional[SecretStr] = None

    # Constructed automatically if not provided explicitly
    DATABASE_URL: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def build_database_url(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(values.get("DATABASE_URL"), str):
            # If DATABASE_URL is provided, use it directly
            return values
        # Build the URL from components
        db_user = values.get("DB_USER")
        db_password_secret = values.get("DB_PASSWORD")
        db_password = db_password_secret.get_secret_value() if isinstance(db_password_secret, SecretStr) else db_password_secret
        db_host = values.get("DB_HOST")
        db_port = values.get("DB_PORT")
        db_name = values.get("DB_NAME")
        if all([db_user, db_password is not None, db_host, db_port, db_name]): # Check password is not None
            values["DATABASE_URL"] = f"mysql+aiomysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        else:
            # Handle case where components might be missing - could raise error or set None
            # Setting None might cause issues later, perhaps raise ConfigurationError?
            # For now, let it be None if components missing, but add a check later?
            pass
        return values

    # --- Telegram Bot ---
    BOT_TOKEN: SecretStr # Require BOT_TOKEN
    # Comma-separated string of admin IDs from .env
    ADMIN_IDS: str 
    # List of integer admin IDs, populated by validator
    ADMIN_USER_IDS: List[int] = []

    @field_validator('ADMIN_USER_IDS', mode='before')
    @classmethod
    def assemble_admin_user_ids(cls, v: Any, info: FieldValidationInfo) -> List[int]:
        admin_ids_str = info.data.get('ADMIN_IDS')
        if isinstance(admin_ids_str, str):
            try:
                ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip()]
                if not ids:
                    raise ValueError("ADMIN_IDS cannot be empty or contain only whitespace.")
                return ids
            except ValueError as e:
                raise ValueError(f"Invalid ADMIN_IDS format in .env: '{admin_ids_str}'. Should be comma-separated integers. Error: {e}")
        # Return existing value (e.g., default empty list) if ADMIN_IDS is not a string
        return v 

    # --- Notification Channels ---
    NOTIFICATION_CHANNEL_ADMIN: Optional[str] = None
    NOTIFICATION_CHANNEL_PAYMENT: Optional[str] = None
    NOTIFICATION_CHANNEL_BACKUP: Optional[str] = None
    NOTIFICATION_CHANNEL_CRITICAL: Optional[str] = None
    NOTIFICATION_CHANNEL_USER_REGISTRATION: Optional[str] = None

    # --- Security ---
    # Require SECRET_KEY, remove default
    SECRET_KEY: SecretStr 

    # --- Redis Cache (Optional - Placeholder) ---
    # Example: redis://localhost:6379/0
    REDIS_URL: str | None = None

    # --- Redis ---
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[SecretStr] = None
    REDIS_MAX_CONNECTIONS: int = 10
    CACHE_KEY_PREFIX: str = "moonvpn_cache"

    # --- Panel Integration ---
    PANEL_API_TIMEOUT: int = 30 # Timeout for requests to panel APIs in seconds

    # Pydantic-Settings configuration
    model_config = SettingsConfigDict(
        env_file='.env',          # Load from .env file
        env_file_encoding='utf-8', # Specify encoding
        extra='ignore'            # Ignore extra fields from env/dotenv
    )

# Create a single instance of the settings to be imported elsewhere
settings = Settings()

# Add a check after initialization to ensure critical settings are present
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL could not be constructed. Check DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME in .env or provide DATABASE_URL explicitly.")
if not settings.ADMIN_USER_IDS:
     raise ValueError("ADMIN_USER_IDS is empty. Check ADMIN_IDS in .env.")
if not settings.SECRET_KEY.get_secret_value():
    raise ValueError("SECRET_KEY is missing or empty in .env.")

# --- Environment Specific Settings ---
# You can add logic here to override settings based on ENVIRONMENT
# For example:
# if settings.ENVIRONMENT == "prod":
#     settings.LOG_LEVEL = "WARNING"
# elif settings.ENVIRONMENT == "test":
#     # Override settings for testing
#     settings.DATABASE_URL = "mysql+aiomysql://test_user:test_pass@localhost:3307/test_db" # Example test DB
