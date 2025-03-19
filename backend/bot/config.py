"""
MoonVPN Telegram Bot - Configuration and Constants

This module loads and manages configuration and constants for the bot.
"""

import os
import sys
import json
import logging
import re
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from pathlib import Path
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Conversation states
(
    SELECTING_FEATURE,
    SELECTING_ACTION,
    SELECTING_LANGUAGE,
    TYPING_NAME,
    TYPING_EMAIL,
    TYPING_PHONE,
    TYPING_PASSWORD,
    TYPING_REPLY,
    ENTERING_DETAILS,
    CONFIRMING_PAYMENT,
    SELECTING_REWARD,
    ACCOUNT_CREATED,
    END,
    SELECTING_USER,
    SELECTING_ACCOUNT,
    SELECTING_SERVER,
    PAYMENT_VERIFICATION,
    SERVER_MANAGEMENT,
    SYSTEM_SETTINGS,
    BROADCAST_MESSAGE,
) = map(chr, range(20))

# Command patterns
class Commands:
    """Bot commands."""
    START = "start"
    BUY = "buy"
    STATUS = "status"
    SERVERS = "servers"
    LOCATIONS = "locations"
    HELP = "help"
    SETTINGS = "settings"
    LANGUAGE = "language"
    SUPPORT = "support"
    TRAFFIC = "traffic"
    CHANGE_LOCATION = "change_location"
    EXTEND = "extend"
    PAYMENT = "payment"
    ADMIN = "admin"
    STATS = "stats"
    FEEDBACK = "feedback"
    REFERRAL = "referral"
    EARNINGS = "earnings"
    FREE = "free"
    BROADCAST = "broadcast"
    GET_ID = "getid"
    ABOUT = "about"
    CONTACT = "contact"
    APPS = "apps"
    PRICES = "prices"
    FAQ = "faq"
    REPORT = "report"
    CANCEL = "cancel"

# Generic callback patterns
class CallbackPatterns:
    """Callback patterns for inline keyboards."""
    
    # Main menu
    MAIN_MENU = "main_menu"
    
    # Purchase-related
    BUY_ACCOUNT = "buy_account"
    BUY_PACKAGE = "buy_package"
    BUY_CONFIRM = "buy_confirm"
    BUY_LOCATION = "buy_location"
    BUY_DURATION = "buy_duration"
    
    # Account-related
    ACCOUNT_STATUS = "account_status"
    ACCOUNT_DETAILS = "account_details"
    ACCOUNT_REFRESH = "account_refresh"
    
    # Location-related
    CHANGE_LOCATION = "change_location"
    LOCATION_SELECT = "location_select"
    
    # Traffic-related
    CHECK_TRAFFIC = "check_traffic"
    TRAFFIC_DETAIL = "traffic_detail"
    TRAFFIC_HISTORY = "traffic_history"
    TRAFFIC_GRAPH = "traffic_graph"
    TRAFFIC_REFRESH = "traffic_refresh"
    
    # Payment-related
    PAYMENT = "payment"
    PAYMENT_HISTORY = "payment_history"
    
    # Support-related
    SUPPORT = "support"
    SUPPORT_TICKET = "support_ticket"
    SUPPORT_FAQ = "support_faq"
    SUPPORT_CONTACT = "support_contact"
    
    # Settings-related
    SETTINGS = "settings"
    LANGUAGE_SELECT = "language_select"
    NOTIFICATIONS = "notifications"
    SETTINGS_THEME = "settings_theme"
    
    # Server management
    SERVER_ACTION = "server_action"
    SERVER_LIST = "server_list"
    SERVER_ADD = "server_add"
    SERVER_EDIT = "server_edit"
    SERVER_DELETE = "server_delete"
    SERVER_TEST = "server_test"
    SERVER_VIEW = "server_view"
    
    # Admin dashboard
    ADMIN_DASHBOARD = "admin_dashboard"
    SERVER_ACTION_LIST = "server_action_list"
    
    # Help-related
    HELP = "help"
    HELP_USAGE = "help_usage"
    HELP_PAYMENT = "help_payment"
    HELP_TECHNICAL = "help_technical"
    HELP_COMMANDS = "help_commands"
    HELP_APPS = "help_apps"
    
    # Earnings-related
    EARN_MONEY = "earn_money"
    EARNINGS = "earn"
    
    # Free services
    FREE_SERVICES = "free_services"
    FREE_VPN_DETAIL = "free_vpn_detail"
    FREE_PROXY_DETAIL = "free_proxy_detail"
    
    # Generic navigation
    BACK = "back"
    NEXT = "next"
    PREV = "prev"
    EXIT = "exit"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    DELETE = "delete"
    REFRESH = "refresh"
    
    # Regular expressions for callback patterns
    @staticmethod
    def back_pattern():
        return r"^back(\:[\w\-]+)?$"
    
    @staticmethod
    def page_pattern():
        return r"^page\:(\d+)$"
    
    @staticmethod
    def language_pattern():
        return r"^language\:([\w\-]+)$"
    
    @staticmethod
    def server_action_pattern():
        return r"^server\:([\w\-]+)\:(\d+)$"
    
    @staticmethod
    def location_select_pattern():
        return r"^location\:(\d+)$"
    
    @staticmethod
    def package_select_pattern():
        return r"^package\:(\d+)$"
    
    @staticmethod
    def duration_select_pattern():
        return r"^duration\:(\d+)$"
    
    @staticmethod
    def payment_method_pattern():
        return r"^payment\:([\w\-]+)$"
    
    @staticmethod
    def account_action_pattern():
        return r"^account\:([\w\-]+)\:(\d+)$"
    
    @staticmethod
    def help_section_pattern():
        return r"^help\:([\w\-]+)$"

# Conversation states enum
class States:
    """Conversation states."""
    
    # Server management
    (
        SERVER_MAIN,
        SERVER_ADDING,
        SERVER_EDITING,
        SERVER_CONFIRMING_DELETE,
        SERVER_VIEWING,
    ) = range(5)
    
    # Admin broadcast
    (
        BROADCAST_COMPOSING,
        BROADCAST_CONFIRMING,
        BROADCAST_SENDING,
    ) = range(5, 8)
    
    # Ticket system
    (
        TICKET_CATEGORY,
        TICKET_DESCRIPTION,
        TICKET_CONFIRMING,
        TICKET_REPLYING,
    ) = range(8, 12)
    
    # Help system
    (
        HELP_MAIN,
        HELP_VIEWING,
    ) = range(12, 14)
    
    # Account status
    (
        SHOWING_STATUS,
        ACCOUNT_DETAILS,
    ) = range(14, 16)
    
    # Buying process
    (
        SELECTING_PACKAGE,
        SELECTING_LOCATION,
        CONFIRMING_PURCHASE,
        PROCESSING_PAYMENT,
    ) = range(16, 20)
    
    # Earnings/Referral
    (
        SHOWING_EARNINGS,
        SHOWING_REFERRALS,
        SHOWING_WITHDRAW,
    ) = range(20, 23)
    
    # Settings
    (
        SETTINGS_MAIN,
        CHANGING_LANGUAGE,
        MANAGING_NOTIFICATIONS,
    ) = range(23, 26)

    # Buy process
    BUY_SELECT_PACKAGE = 0
    BUY_SELECT_LOCATION = 1
    BUY_SELECT_DURATION = 2
    BUY_CONFIRM_ORDER = 3
    BUY_PAYMENT_METHOD = 4
    BUY_PAYMENT_DETAILS = 5
    
    # Payment
    PAYMENT_WAITING = 0
    PAYMENT_VERIFICATION = 1
    PAYMENT_COMPLETE = 2
    
    # Account management
    ACCOUNT_LIST = 0
    ACCOUNT_DETAIL = 1
    ACCOUNT_EXTEND = 2
    ACCOUNT_LOCATION = 3
    
    # Status check
    SHOWING_STATUS = 0
    ACCOUNT_DETAILS = 1
    
    # Traffic stats
    TRAFFIC_MAIN = 0
    TRAFFIC_DETAIL = 1
    TRAFFIC_HISTORY = 2
    
    # Settings
    SETTINGS_MAIN = 0
    SETTINGS_LANGUAGE_SELECT = 1
    SETTINGS_NOTIFICATIONS_CONFIG = 2
    
    # Support
    SUPPORT_MAIN = 0
    SUPPORT_TICKET_CREATE = 1
    SUPPORT_TICKET_DETAIL = 2
    
    # Admin broadcast
    BROADCAST_SELECT_TARGET = 0
    BROADCAST_COMPOSE = 1
    BROADCAST_CONFIRM = 2
    
    # Server management
    SERVER_MAIN = 0
    SERVER_DETAILS = 1
    SERVER_ADDING = 2
    SERVER_EDITING = 3
    SERVER_CONFIRMING_DELETE = 4
    
    # Earnings/Affiliate program
    SHOWING_EARNINGS = 0
    SHOWING_REFERRALS = 1
    SHOWING_WITHDRAW = 2
    
    # Free services
    FREE_SERVICES_MAIN = 0
    FREE_VPN_DETAIL = 1
    FREE_PROXY_DETAIL = 2


# Configuration functions
def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    # Basic bot configuration
    config = {
        "telegram_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "webhook_mode": os.environ.get("WEBHOOK_MODE", "false").lower() == "true",
        "webhook_url": os.environ.get("WEBHOOK_URL", ""),
        "webhook_port": int(os.environ.get("WEBHOOK_PORT", "8443")),
        "webhook_path": os.environ.get("WEBHOOK_PATH", ""),
        "webhook_cert": os.environ.get("WEBHOOK_CERT", ""),
        "webhook_key": os.environ.get("WEBHOOK_KEY", ""),
        
        # Admin settings
        "admin_ids": parse_admin_ids(os.environ.get("ADMIN_IDS", "")),
        "manager_ids": parse_admin_ids(os.environ.get("MANAGER_IDS", "")),
        "support_ids": parse_admin_ids(os.environ.get("SUPPORT_IDS", "")),
        
        # API configuration
        "api_base_url": os.environ.get("API_BASE_URL", "http://backend:8000/api/v1"),
        "api_auth_token": os.environ.get("API_AUTH_TOKEN", ""),
        
        # 3x-UI Panel configuration
        "x_ui_panel_url": os.environ.get("X_UI_PANEL_URL", ""),
        "x_ui_panel_username": os.environ.get("X_UI_PANEL_USERNAME", ""),
        "x_ui_panel_password": os.environ.get("X_UI_PANEL_PASSWORD", ""),
        
        # Redis configuration
        "redis_url": os.environ.get("REDIS_URL", "redis://redis:6379/0"),
        
        # Features configuration
        "features": parse_features(os.environ.get("FEATURES", "")),
        
        # Localization
        "default_language": os.environ.get("DEFAULT_LANGUAGE", "fa"),
        "available_languages": os.environ.get("AVAILABLE_LANGUAGES", "fa,en").split(","),
        
        # Payment configuration
        "payment_methods": os.environ.get("PAYMENT_METHODS", "card").split(","),
        "card_number": os.environ.get("CARD_NUMBER", ""),
        "card_holder": os.environ.get("CARD_HOLDER", ""),
        
        # Logging
        "log_level": os.environ.get("LOG_LEVEL", "INFO"),
        "log_file": os.environ.get("LOG_FILE", "bot.log"),
        
        # Sentry configuration
        "sentry_dsn": os.environ.get("SENTRY_DSN", ""),
        "sentry_environment": os.environ.get("SENTRY_ENVIRONMENT", "production"),
    }
    
    # Validate configuration
    validate_config(config)
    
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the configuration.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
    
    Raises:
        ValueError: If a required configuration value is missing
    """
    required_values = [
        "telegram_token",
    ]
    
    missing_values = []
    for key in required_values:
        if not config.get(key):
            missing_values.append(key)
    
    if missing_values:
        message = "Missing required configuration values: " + ", ".join(missing_values)
        logger.error(message)
        raise ValueError(message)
    
    # Validate webhook configuration if webhook mode is enabled
    if config["webhook_mode"]:
        webhook_required = ["webhook_url", "webhook_path", "webhook_port"]
        missing_webhook = []
        
        for key in webhook_required:
            if not config.get(key):
                missing_webhook.append(key)
        
        if missing_webhook:
            message = "Webhook mode enabled but missing webhook configuration: " + ", ".join(missing_webhook)
            logger.error(message)
            raise ValueError(message)


def parse_admin_ids(admin_ids_str: str) -> List[int]:
    """
    Parse admin IDs from a comma-separated string.
    
    Args:
        admin_ids_str (str): Comma-separated string of admin IDs
    
    Returns:
        List[int]: List of admin IDs
    """
    if not admin_ids_str:
        return []
    
    try:
        admin_ids = []
        for id_str in admin_ids_str.split(","):
            admin_id = int(id_str.strip())
            admin_ids.append(admin_id)
        return admin_ids
    except ValueError:
        logger.error(f"Invalid admin IDs: {admin_ids_str}")
        return []


def parse_features(features_str: str) -> Dict[str, bool]:
    """
    Parse feature flags from a comma-separated string.
    
    Args:
        features_str (str): Comma-separated string of features
    
    Returns:
        Dict[str, bool]: Dictionary of feature flags
    """
    features = {
        "referral_program": False,
        "support_tickets": False,
        "notifications": False,
        "payments": False,
        "server_management": False,
        "free_trial": False,
        "api_access": False,
        "discount_codes": False,
        "traffic_stats": False,
        "auto_renewal": False,
        "multi_language": False,
        "social_auth": False,
        "broadcasts": False,
    }
    
    if not features_str:
        return features
    
    for feature in features_str.split(","):
        feature = feature.strip()
        if feature in features:
            features[feature] = True
    
    return features

# Export admin IDs for easy access
ADMIN_USER_IDS = parse_admin_ids(os.environ.get("ADMIN_USER_IDS", ""))

# Export default language
DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "fa")

# Export debug mode
DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"

# Export enabled features
ENABLED_FEATURES = parse_features(os.environ.get("ENABLE_FEATURES", ""))

# Bot token
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Database settings
DATABASE_URL = f"postgresql://{os.environ.get('DB_USER', 'moonvpn')}:{os.environ.get('DB_PASSWORD', 'moonvpn')}@{os.environ.get('DB_HOST', 'postgres')}:{os.environ.get('DB_PORT', '5432')}/{os.environ.get('DB_NAME', 'moonvpn')}"

# Admin settings
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")

# Path settings
ROOT_DIR = Path(__file__).parent.parent.absolute()
BOT_DIR = Path(__file__).parent.absolute()
LOG_DIR = ROOT_DIR / "logs"
CONFIG_DIR = ROOT_DIR / "config"

# Create necessary directories
LOG_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Payment settings
CARD_NUMBER = os.environ.get("CARD_NUMBER", "6037-9975-9507-8955")
CARD_HOLDER = os.environ.get("CARD_HOLDER", "محمد محمدزاده")
CARD_BANK = os.environ.get("CARD_BANK", "ملی")

# Feature flags
FEATURE_FLAGS = {
    "payments": os.environ.get("FEATURE_PAYMENTS", "true").lower() == "true",
    "account_creation": os.environ.get("FEATURE_ACCOUNT_CREATION", "true").lower() == "true",
    "change_location": os.environ.get("FEATURE_CHANGE_LOCATION", "true").lower() == "true",
    "traffic_query": os.environ.get("FEATURE_TRAFFIC_QUERY", "true").lower() == "true",
}

# VPN Server Configuration
PANEL_TYPE = os.environ.get("PANEL_TYPE", "xui")  # xui or v2ray

# Default server settings
DEFAULT_SERVER = {
    "host": os.environ.get("DEFAULT_SERVER_HOST", "vpn-panel.example.com"),
    "port": int(os.environ.get("DEFAULT_SERVER_PORT", "2053")),
    "username": os.environ.get("DEFAULT_SERVER_USERNAME", "admin"),
    "password": os.environ.get("DEFAULT_SERVER_PASSWORD", "admin"),
    "api_port": int(os.environ.get("DEFAULT_SERVER_API_PORT", "2053")),
    "location": os.environ.get("DEFAULT_SERVER_LOCATION", "Germany"),
    "country": os.environ.get("DEFAULT_SERVER_COUNTRY", "DE"),
}

class Settings(BaseSettings):
    """Application settings."""
    
    # Bot settings
    BOT_TOKEN: str
    ADMIN_ID: int
    ADMIN_IDS: List[int] = []
    MANAGER_IDS: List[int] = []
    SUPPORT_IDS: List[int] = []
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "moonvpn"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    
    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "moonvpnredispassword"
    
    # Panel settings
    PANEL_HOST: str
    PANEL_PORT: int
    PANEL_USERNAME: str
    PANEL_PASSWORD: str
    PANEL_BASE_PATH: str
    
    # Migration settings
    MIGRATIONS_DIR: str = "bot/database/migrations"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra fields

# Create settings instance
settings = Settings() 