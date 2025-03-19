"""
MoonVPN FastAPI - Settings Module

This module contains application settings and configuration.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Union
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings using Pydantic."""
    
    # Application settings
    APP_NAME: str = "MoonVPN"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    
    # Security settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Enhanced security settings
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_ATTEMPT_WINDOW: int = 900  # 15 minutes
    IP_BLOCK_DURATION: int = 86400  # 24 hours
    RATE_LIMITS: Dict[str, Dict[str, int]] = {
        'login': {'max_requests': 5, 'time_window': 300},  # 5 minutes
        'payment': {'max_requests': 10, 'time_window': 3600},  # 1 hour
        'api': {'max_requests': 100, 'time_window': 60}  # 1 minute
    }
    GEOLOCATION_CHECK_ENABLED: bool = True
    MAX_LOGIN_DISTANCE_KM: int = 1000
    
    # Bot settings
    BOT_TOKEN: str
    ADMIN_ID: int
    ADMIN_IDS: List[int] = []
    MANAGER_IDS: List[int] = []
    SUPPORT_IDS: List[int] = []
    WEBHOOK_MODE: bool = False
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: Optional[str] = None
    WEBHOOK_PORT: int = 8443
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "moonvpn"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    
    @property
    def DATABASE_URL(self) -> str:
        """Get SQLAlchemy database URL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "moonvpnredispassword"
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        """Get Redis URL."""
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Panel settings
    PANEL_HOST: str
    PANEL_PORT: int
    PANEL_USERNAME: str
    PANEL_PASSWORD: str
    PANEL_BASE_PATH: str
    
    @property
    def PANEL_URL(self) -> str:
        """Get panel URL."""
        return f"http://{self.PANEL_HOST}:{self.PANEL_PORT}{self.PANEL_BASE_PATH}"
    
    # Payment settings
    ZARINPAL_MERCHANT_ID: Optional[str] = None
    ZARINPAL_SANDBOX: bool = True
    CARD_NUMBER: Optional[str] = None
    CARD_HOLDER: Optional[str] = None
    CARD_BANK: Optional[str] = None
    PAYMENT_VERIFICATION_TIMEOUT: int = 30  # minutes
    
    # VPN settings
    VPN_DEFAULT_PROTOCOL: str = "vmess"
    VPN_DEFAULT_TRAFFIC_LIMIT_GB: int = 50
    VPN_DEFAULT_EXPIRE_DAYS: int = 30
    
    # Traffic monitoring settings
    TRAFFIC_CHECK_INTERVAL: int = 300  # 5 minutes
    TRAFFIC_WARNING_THRESHOLDS: List[int] = [50, 75, 90, 95]  # Percentage of limit
    BANDWIDTH_WARNING_THRESHOLDS: List[int] = [50, 75, 90, 95]  # Percentage of capacity
    TRAFFIC_EXCEEDED_ACTIONS: Dict[str, bool] = {
        'suspend_service': True,
        'notify_user': True,
        'notify_admin': True
    }
    
    # Backup settings
    BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL: int = 86400  # 24 hours
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_TYPES: List[str] = ['database', 'configurations', 'logs']
    
    # Analytics settings
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_UPDATE_INTERVAL: int = 3600  # 1 hour
    ANALYTICS_METRICS: Dict[str, bool] = {
        'user_metrics': True,
        'server_metrics': True,
        'financial_metrics': True,
        'traffic_metrics': True
    }
    ANALYTICS_RETENTION_DAYS: int = 90
    
    # Notification settings
    ADMIN_NOTIFICATIONS: Dict[str, bool] = {
        'security_alerts': True,
        'traffic_exceeded': True,
        'payment_issues': True,
        'server_issues': True
    }
    USER_NOTIFICATIONS: Dict[str, bool] = {
        'traffic_warnings': True,
        'expiration_reminders': True,
        'payment_confirmations': True,
        'service_updates': True
    }
    
    # Cache settings
    CACHE_TTL: Dict[str, int] = {
        "user": 300,        # 5 minutes
        "account": 300,     # 5 minutes
        "server": 600,      # 10 minutes
        "plan": 1800,       # 30 minutes
        "ticket": 300,      # 5 minutes
        "payment": 300,     # 5 minutes
        "config": 3600      # 1 hour
    }
    
    # Points system settings
    POINTS_PER_PURCHASE: int = 10
    POINTS_PER_REFERRAL: int = 50
    POINTS_EXPIRY_DAYS: int = 365
    
    # File storage settings
    UPLOAD_DIR: Path = PROJECT_ROOT / "uploads"
    RECEIPTS_DIR: Path = UPLOAD_DIR / "receipts"
    STATIC_DIR: Path = PROJECT_ROOT / "static"
    TEMPLATES_DIR: Path = PROJECT_ROOT / "templates"
    
    # Language settings
    DEFAULT_LANGUAGE: str = "fa"
    SUPPORTED_LANGUAGES: Dict[str, str] = {
        "fa": "فارسی",
        "en": "English"
    }
    
    # Ticket settings
    TICKET_STATUS: Dict[str, str] = {
        "open": "باز",
        "closed": "بسته شده",
        "answered": "پاسخ داده شده",
        "pending": "در انتظار"
    }
    TICKET_PRIORITY: Dict[str, str] = {
        "low": "کم",
        "medium": "متوسط",
        "high": "زیاد",
        "urgent": "فوری"
    }
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            """Parse environment variables."""
            if field_name == "ADMIN_IDS":
                return [int(id.strip()) for id in raw_val.split(",") if id.strip()]
            if field_name == "MANAGER_IDS":
                return [int(id.strip()) for id in raw_val.split(",") if id.strip()]
            if field_name == "SUPPORT_IDS":
                return [int(id.strip()) for id in raw_val.split(",") if id.strip()]
            if field_name == "ALLOWED_HOSTS":
                return [host.strip() for host in raw_val.split(",") if host.strip()]
            if field_name == "CORS_ORIGINS":
                return [origin.strip() for origin in raw_val.split(",") if origin.strip()]
            return raw_val

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Create required directories
settings = get_settings()
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.RECEIPTS_DIR.mkdir(exist_ok=True)
settings.STATIC_DIR.mkdir(exist_ok=True)
settings.TEMPLATES_DIR.mkdir(exist_ok=True)
