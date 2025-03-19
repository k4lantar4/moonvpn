import os
from dotenv import load_dotenv
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, RedisDsn

# Load environment variables
load_dotenv()

# Database settings
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'moonvpn')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Construct database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Database pool settings
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '1800'))

# Database connection settings
DB_ECHO = os.getenv('DB_ECHO', 'false').lower() == 'true'
DB_POOL_PRE_PING = os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true'

# Redis settings (for caching)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
REDIS_SSL = os.getenv('REDIS_SSL', 'false').lower() == 'true'

# Cache settings
CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes default
CACHE_PREFIX = os.getenv('CACHE_PREFIX', 'moonvpn:')

# Database migration settings
MIGRATION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
ALEMBIC_INI = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'alembic.ini')

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG_FILE = os.getenv('LOG_FILE', 'moonvpn.log')

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # PostgreSQL settings
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    # Redis settings
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> PostgresDsn:
        """Get the SQLAlchemy database URL."""
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
        )
    
    @property
    def REDIS_URL(self) -> RedisDsn:
        """Get the Redis URL."""
        return RedisDsn.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            path=str(self.REDIS_DB),
            password=self.REDIS_PASSWORD,
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
db_settings = DatabaseSettings()

# Database configuration
DATABASE_CONFIG = {
    "url": str(db_settings.SQLALCHEMY_DATABASE_URL),
    "echo": False,
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 1800,
}

# Redis configuration
REDIS_CONFIG = {
    "url": str(db_settings.REDIS_URL),
    "encoding": "utf-8",
    "decode_responses": True,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "retry_on_timeout": True,
} 