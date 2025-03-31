import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file at the project root (moonvpn/.env)
# Adjust path if your .env is elsewhere
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    PROJECT_NAME: str = "MoonVPN Core API"
    API_V1_STR: str = "/api/v1"

    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER", "moonvpn_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "your_strong_password")
    DB_NAME: str = os.getenv("DB_NAME", "moonvpn_db")

    # Construct SQLAlchemy Database URL
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Construct the database URI for SQLAlchemy."""
        # Using pymysql driver
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Security Settings (Example - To be used later)
    # SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_change_this")
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days
    # ALGORITHM: str = "HS256"

    class Config:
        case_sensitive = True
        # env_file = ".env" # Already handled by load_dotenv


settings = Settings()
