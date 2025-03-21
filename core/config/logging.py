"""
MoonVPN Telegram Bot - Constants Module

This module contains constants used throughout the bot.
"""

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

# Callback data patterns for account management
ACCOUNTS_CB = "accounts"
VIEW_ACCOUNTS = "view_accounts"
CREATE_ACCOUNT = "create_account"
VIEW_DETAILS = "view_details"
CONFIRM_PURCHASE = "confirm_purchase"
RENEW_ACCOUNT = "renew_account"
CONFIRM_RENEW = "confirm_renew"
BACK_CB = "back"

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

# Callback patterns
class CallbackPatterns:
    """Callback patterns for inline keyboards."""
    MAIN_MENU = "main_menu"
    BUY = "buy"
    STATUS = "status"
    SETTINGS = "settings"
    SUPPORT = "support"
    HELP = "help"
    ACCOUNT = "account"
    LANGUAGE = "language"
    SERVER = "server"
    PAYMENT = "payment"
    BACK = "back"
    NEXT = "next"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    SELECT = "select"
    REFRESH = "refresh"

# Language constants
DEFAULT_LANGUAGE = "fa"
SUPPORTED_LANGUAGES = {
    "fa": "فارسی",
    "en": "English"
}

# Payment constants
PAYMENT_METHODS = {
    "card": "کارت به کارت",
    "zarinpal": "درگاه پرداخت زرین‌پال"
}

# Server constants
SERVER_TYPES = {
    "vmess": "VMess",
    "vless": "VLESS",
    "trojan": "Trojan",
    "shadowsocks": "Shadowsocks"
}

# Account status
ACCOUNT_STATUS = {
    "active": "فعال",
    "expired": "منقضی شده",
    "disabled": "غیرفعال",
    "error": "خطا"
}

# Ticket status
TICKET_STATUS = {
    "open": "باز",
    "closed": "بسته شده",
    "answered": "پاسخ داده شده",
    "pending": "در انتظار"
}

# Ticket priority
TICKET_PRIORITY = {
    "low": "کم",
    "medium": "متوسط",
    "high": "زیاد",
    "urgent": "فوری"
}

# Cache constants
CACHE_TTL = {
    "user": 300,  # 5 minutes
    "account": 300,
    "server": 600,  # 10 minutes
    "plan": 1800,  # 30 minutes
    "ticket": 300,
    "payment": 300,
    "config": 3600  # 1 hour
} 