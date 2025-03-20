"""
Security configuration settings for the application.
"""
from typing import Dict, Any
from pydantic import BaseSettings

class SecuritySettings(BaseSettings):
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_WINDOW: int = 60  # seconds
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_BLOCK_DURATION: int = 300  # seconds

    # Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    PASSWORD_SALT_ROUNDS: int = 12

    # Two-Factor Authentication
    TWO_FACTOR_ENABLED: bool = True
    TWO_FACTOR_ISSUER: str = "MoonVPN"
    TWO_FACTOR_ALGORITHM: str = "SHA1"
    TWO_FACTOR_DIGITS: int = 6
    TWO_FACTOR_PERIOD: int = 30

    # Session Management
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_CONCURRENT_SESSIONS: int = 3
    SESSION_CLEANUP_INTERVAL: int = 3600  # seconds

    # Encryption
    ENCRYPTION_KEY_ROTATION_DAYS: int = 30
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"
    ENCRYPTION_KEY_LENGTH: int = 32
    ENCRYPTION_IV_LENGTH: int = 12

    # Security Headers
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }

    # CORS Settings
    CORS_ENABLED: bool = True
    CORS_ALLOWED_ORIGINS: list = ["*"]
    CORS_ALLOWED_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOWED_HEADERS: list = ["*"]
    CORS_EXPOSE_HEADERS: list = ["*"]
    CORS_MAX_AGE: int = 600

    # IP Blocking
    IP_BLOCKING_ENABLED: bool = True
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    IP_BLOCK_DURATION_MINUTES: int = 30
    SUSPICIOUS_IP_THRESHOLD: int = 3

    # Audit Logging
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 90
    AUDIT_LOG_LEVEL: str = "INFO"
    AUDIT_LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Monitoring
    MONITORING_ENABLED: bool = True
    MONITORING_INTERVAL_SECONDS: int = 60
    ALERT_THRESHOLDS: Dict[str, int] = {
        "failed_login": 5,
        "api_errors": 10,
        "suspicious_ip": 3,
        "critical_events": 1
    }

    # Email Configuration
    EMAIL_CONFIG: Dict[str, Any] = {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "from_email": "security@moonvpn.com",
        "to_email": "admin@moonvpn.com"
    }

    # Webhook Configuration
    WEBHOOK_CONFIG: Dict[str, Any] = {
        "url": "",
        "headers": {
            "Content-Type": "application/json"
        }
    }

    # SMS Configuration
    SMS_CONFIG: Dict[str, Any] = {
        "provider": "",
        "api_key": "",
        "api_secret": "",
        "from_number": ""
    }

    # Telegram Configuration
    TELEGRAM_CONFIG: Dict[str, Any] = {
        "bot_token": "",
        "chat_id": "",
        "parse_mode": "HTML"
    }

    # Admin Groups
    ADMIN_GROUPS: Dict[str, Dict[str, Any]] = {
        "SECURITY": {
            "name": "Security Team",
            "email": "security@moonvpn.com",
            "telegram_chat_id": "",
            "webhook_url": ""
        },
        "MANAGE": {
            "name": "Management Team",
            "email": "management@moonvpn.com",
            "telegram_chat_id": "",
            "webhook_url": ""
        }
    }

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
security_settings = SecuritySettings() 