"""
MoonVPN FastAPI - Constants Module

This module contains constants used throughout the application, including API endpoints,
response codes, and Telegram bot functionality.
"""

# API Constants
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Response Status Codes
class StatusCodes:
    """HTTP status codes used in API responses."""
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503

# API Response Messages
class Messages:
    """Standard API response messages."""
    SUCCESS = "Operation completed successfully"
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"
    NOT_FOUND = "Resource not found"
    UNAUTHORIZED = "Unauthorized access"
    FORBIDDEN = "Access forbidden"
    VALIDATION_ERROR = "Validation error"
    INTERNAL_ERROR = "Internal server error"
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"

# API Error Codes
class ErrorCodes:
    """Standard error codes for API responses."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND_ERROR = "NOT_FOUND_ERROR"
    CONFLICT_ERROR = "CONFLICT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

# API Rate Limiting
class RateLimits:
    """Rate limiting constants."""
    DEFAULT_LIMIT = 100
    DEFAULT_PERIOD = 60  # seconds
    LOGIN_LIMIT = 5
    LOGIN_PERIOD = 300  # 5 minutes
    PAYMENT_LIMIT = 10
    PAYMENT_PERIOD = 3600  # 1 hour

# API Cache Keys
class CacheKeys:
    """Cache key patterns."""
    USER = "user:{user_id}"
    ACCOUNT = "account:{account_id}"
    SERVER = "server:{server_id}"
    PLAN = "plan:{plan_id}"
    TICKET = "ticket:{ticket_id}"
    PAYMENT = "payment:{payment_id}"
    CONFIG = "config:{key}"

# API Pagination
class Pagination:
    """Pagination constants."""
    DEFAULT_PAGE = 1
    DEFAULT_SIZE = 20
    MAX_SIZE = 100

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