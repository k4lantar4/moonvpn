"""
Email configuration for MoonVPN.

This module contains all email-related configuration settings.
"""

from typing import Dict, Any
from pydantic import BaseSettings, EmailStr, SecretStr, validator
import os

class EmailConfig(BaseSettings):
    """Email configuration settings."""
    
    # SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: EmailStr
    SMTP_PASSWORD: SecretStr
    FROM_EMAIL: EmailStr
    REPLY_TO_EMAIL: EmailStr = None
    
    # Email Verification Settings
    VERIFICATION_TOKEN_EXPIRY: int = 24 * 60 * 60  # 24 hours in seconds
    VERIFICATION_URL_BASE: str = "https://moonvpn.org/verify"
    
    # Password Reset Settings
    RESET_TOKEN_EXPIRY: int = 60 * 60  # 1 hour in seconds
    RESET_URL_BASE: str = "https://moonvpn.org/reset-password"
    
    # Alert Settings
    ALERT_RECIPIENTS: list[EmailStr] = []
    ALERT_SEVERITY_LEVELS: list[str] = ["INFO", "WARNING", "ERROR", "CRITICAL"]
    
    # Rate Limiting
    MAX_EMAILS_PER_HOUR: int = 100
    MAX_EMAILS_PER_DAY: int = 1000
    
    # Template Settings
    TEMPLATE_DIR: str = "app/templates/email"
    LOGO_URL: str = "https://moonvpn.org/static/images/logo.png"
    CONTACT_URL: str = "https://moonvpn.org/contact"
    
    @validator("REPLY_TO_EMAIL", pre=True)
    def set_reply_to_email(cls, v, values):
        """Set reply-to email to FROM_EMAIL if not provided."""
        if v is None:
            return values.get("FROM_EMAIL")
        return v
    
    class Config:
        """Pydantic config class."""
        env_prefix = "EMAIL_"
        case_sensitive = True

# Initialize email config
email_config = EmailConfig(
    SMTP_USER=os.getenv("EMAIL_SMTP_USER", "noreply@moonvpn.org"),
    SMTP_PASSWORD=SecretStr(os.getenv("EMAIL_SMTP_PASSWORD", "")),
    FROM_EMAIL=os.getenv("EMAIL_FROM_EMAIL", "noreply@moonvpn.org"),
    ALERT_RECIPIENTS=[
        EmailStr("admin@moonvpn.org"),
        EmailStr("security@moonvpn.org")
    ]
)

def get_email_config() -> Dict[str, Any]:
    """Get email configuration dictionary."""
    return {
        "smtp_host": email_config.SMTP_HOST,
        "smtp_port": email_config.SMTP_PORT,
        "smtp_user": email_config.SMTP_USER,
        "smtp_password": email_config.SMTP_PASSWORD.get_secret_value(),
        "from_email": email_config.FROM_EMAIL,
        "reply_to_email": email_config.REPLY_TO_EMAIL,
        "verification_token_expiry": email_config.VERIFICATION_TOKEN_EXPIRY,
        "verification_url_base": email_config.VERIFICATION_URL_BASE,
        "reset_token_expiry": email_config.RESET_TOKEN_EXPIRY,
        "reset_url_base": email_config.RESET_URL_BASE,
        "alert_recipients": email_config.ALERT_RECIPIENTS,
        "alert_severity_levels": email_config.ALERT_SEVERITY_LEVELS,
        "max_emails_per_hour": email_config.MAX_EMAILS_PER_HOUR,
        "max_emails_per_day": email_config.MAX_EMAILS_PER_DAY,
        "template_dir": email_config.TEMPLATE_DIR,
        "logo_url": email_config.LOGO_URL,
        "contact_url": email_config.CONTACT_URL
    } 