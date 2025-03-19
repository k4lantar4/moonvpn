"""
MoonVPN Telegram Bot - Configuration.

This module contains configuration settings for the MoonVPN Telegram Bot.
"""

import os
from pathlib import Path

# Bot token
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Database settings
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/moonvpn")

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

# Localization
DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "fa")

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