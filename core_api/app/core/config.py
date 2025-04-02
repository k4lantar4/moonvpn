import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Decimal

# No need to manually define .env path if docker-compose env_file is used
# Let BaseSettings read directly from environment variables passed by docker-compose

class Settings(BaseSettings):
    PROJECT_NAME: str = "MoonVPN Core API"
    API_V1_STR: str = "/api/v1"

    # --- Database Configuration --- #
    # BaseSettings will read this from environment variables passed by docker-compose
    # Default is only a fallback if the env var is somehow not set.
    SQLALCHEMY_DATABASE_URI: str = "mysql+pymysql://fallback_user:fallback_pass@localhost/fallback_db?charset=utf8mb4"

    # --- Security Settings --- #
    SECRET_KEY: str = "fallback_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    # --- OTP Settings --- #
    OTP_EXPIRE_SECONDS: int = 3 * 60

    # --- Redis Configuration --- #
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # --- File Storage Settings --- #
    STATIC_FILES_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
    STATIC_FILES_URL_PATH: str = "/static"
    MAX_UPLOAD_SIZE_MB: int = 10  # Default max upload size in MB

    # --- SSH Server Access Settings --- #
    SSH_ENABLED: bool = False  # Enable/disable SSH functionality globally
    SSH_USERNAME: Optional[str] = None  # SSH username for connecting to servers
    SSH_PASSWORD: Optional[str] = None  # SSH password (if using password authentication)
    SSH_KEY_PATH: Optional[str] = None  # Path to SSH private key (if using key-based authentication)
    SSH_KEY_PASSPHRASE: Optional[str] = None  # Passphrase for SSH key (if protected)
    SSH_CONNECTION_TIMEOUT: int = 10  # Seconds to wait for SSH connection

    # --- Zarinpal Payment Gateway Settings --- #
    ZARINPAL_ENABLED: bool = False # Enable/disable Zarinpal globally
    ZARINPAL_MERCHANT_ID: Optional[str] = None
    ZARINPAL_API_URL_REQUEST: str = "https://api.zarinpal.com/pg/v4/payment/request.json" 
    ZARINPAL_API_URL_VERIFY: str = "https://api.zarinpal.com/pg/v4/payment/verify.json"
    ZARINPAL_START_PAY_URL: str = "https://www.zarinpal.com/pg/StartPay/"
    ZARINPAL_CALLBACK_URL_BASE: Optional[str] = None # e.g., "https://vpn.yourdomain.com" - must include scheme
    ZARINPAL_CALLBACK_PATH: str = "api/v1/payments/zarinpal/callback" # Default path within the base URL

    FRONTEND_PAYMENT_RESULT_URL: str = "/payment-result" # Relative or absolute URL on the frontend

    # --- Seller Role Upgrade --- #
    SELLER_UPGRADE_THRESHOLD: Optional[Decimal] = None # e.g., 1000000.00 for 1M Toman
    SELLER_ROLE_NAME: str = 'seller'
    
    # Panel API Settings
    PANEL_API_URL: Optional[str] = None
    
    # Pydantic-Settings configuration
    # Remove env_file, rely on docker-compose to set environment variables
    # For Pydantic V2:
    model_config = SettingsConfigDict(extra='ignore', case_sensitive=True)
    # For Pydantic V1:
    # class Config:
    #     case_sensitive = True


# Create a single instance of the settings
settings = Settings()

# Optional: Print loaded DB URI for debugging
# print(f"Loaded SQLALCHEMY_DATABASE_URI: {settings.SQLALCHEMY_DATABASE_URI}")
