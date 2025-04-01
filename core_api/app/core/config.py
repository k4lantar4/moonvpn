import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

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
