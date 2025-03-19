"""
Constants used in admin handlers.

This module contains constants used across all admin handlers.
"""

# Main admin menu state
ADMIN_MENU = "admin"

# Admin management states
MANAGING_ADMINS = 1
ADDING_ADMIN = 2
REMOVING_ADMIN = 3

# Server management states
SERVER_MANAGEMENT = "server_menu"
SELECTING_SERVER = 4
ADDING_SERVER = 5
EDITING_SERVER = 6
DELETING_SERVER = 7
TESTING_SERVER = 8

# User management states
USER_MANAGEMENT = "user_menu"
SELECTING_USER = 9
EDITING_USER = 10
ADDING_BALANCE = 11
DELETING_USER = 12

# Account management states
ACCOUNT_MANAGEMENT = "account_menu"
SELECTING_ACCOUNT = 13
CREATING_ACCOUNT = 14
EDITING_ACCOUNT = 15
EXTENDING_ACCOUNT = 16
REVOKING_ACCOUNT = 17

# Payment management states
PAYMENT_MANAGEMENT = "payment_menu"
SELECTING_PAYMENT = 18
APPROVING_PAYMENT = 19
REJECTING_PAYMENT = 20
FILTERING_PAYMENTS = 21
ADDING_PAYMENT_NOTE = 22
ENTERING_PAYMENT_NOTES = 32

# Service plan management states
SERVICE_MANAGEMENT = "service_menu"
SELECTING_SERVICE = 23
ADDING_SERVICE = 24
EDITING_SERVICE = 25
DELETING_SERVICE = 26

# Broadcast management states
BROADCAST_MENU = "broadcast_menu"
COMPOSING_MESSAGE = 27

# Settings management states
SETTINGS_MANAGEMENT = "settings_menu"
SELECTING_SETTING = 28
EDITING_SETTING = 29

# Reports and statistics states
REPORTS_MENU = "reports_menu"
SELECTING_REPORT = 30
GENERATING_REPORT = 31
ENTERING_PAYMENT_NOTES = 32

# Group settings states
SELECTING_GROUP = 33
ENTERING_GROUP_ID = 34

# Admin action constants
ACTION_BACK = "back"
ACTION_CANCEL = "cancel"
ACTION_CONFIRM = "confirm"
ACTION_EDIT = "edit"
ACTION_DELETE = "delete"
ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"
ACTION_REFRESH = "refresh"

# Pagination constants
ITEMS_PER_PAGE = 5

# Filter constants
FILTER_ALL = "all"
FILTER_ACTIVE = "active"
FILTER_INACTIVE = "inactive"
FILTER_PENDING = "pending"
FILTER_APPROVED = "approved"
FILTER_REJECTED = "rejected"
FILTER_REFUNDED = "refunded"

# Callback data patterns
BACK_TO_ADMIN = "admin_menu"
BACK_TO_MAIN = "back_to_main"
USER_MANAGEMENT = "admin_users"
SERVER_MANAGEMENT = "server_menu"
PAYMENT_VERIFICATION = "admin_payments"
ACCOUNT_MANAGEMENT = "admin_accounts"
SYSTEM_SETTINGS = "admin_settings"
ADMIN_BROADCAST = "admin_broadcast"
ADMIN_STATISTICS = "admin_statistics"
ADMIN_BACKUP = "admin_backup"

# Cancel and confirm patterns
CANCEL = "cancel"
CONFIRM = "confirm"

# State definitions for top level conversation
SELECTING_ACTION = 0

# State definitions for second level conversations
SELECTING_LOG_TYPE = 1
SELECTING_LOG_ACTION = 2
SELECTING_ACCOUNT_ACTION = 3
SELECTING_PACKAGE_ACTION = 4
SELECTING_DISCOUNT_ACTION = 5
SELECTING_REPORT_PERIOD = 6
SELECTING_REPORT_ACTION = 7
SELECTING_MASS_MESSAGE_TYPE = 8
ENTERING_MASS_MESSAGE_TEXT = 9
ENTERING_MASS_MESSAGE_PHOTO = 10
ENTERING_MASS_MESSAGE_FILE = 11
ENTERING_MASS_MESSAGE_VIDEO = 12
CONFIRMING_MASS_MESSAGE = 13
SELECTING_MONITORING_ACTION = 14
SELECTING_ACCESS_ACTION = 15
ENTERING_ADMIN_USER_ID = 16
SELECTING_BACKUP_ACTION = 17
CONFIRMING_BACKUP_RESTORE = 18
CONFIRMING_BACKUP_DELETE = 19

# Backup types
BACKUP_TYPE_FULL = "full"
BACKUP_TYPE_INCREMENTAL = "incremental"
BACKUP_TYPE_DIFFERENTIAL = "differential"
BACKUP_TYPE_CONFIG = "config"
BACKUP_TYPE_DATABASE = "database"
BACKUP_TYPE_FILES = "files"
BACKUP_TYPE_LOGS = "logs"

# Backup status
BACKUP_STATUS_PENDING = "pending"
BACKUP_STATUS_PROCESSING = "processing"
BACKUP_STATUS_COMPLETED = "completed"
BACKUP_STATUS_ERROR = "error"

# Notification types
NOTIFICATION_TYPES = {
    "GENERAL_MANAGEMENT": {
        "name": "مدیریت کلی",
        "desc": "اطلاعیه‌های عمومی و مدیریت کلی سیستم",
        "icon": "👨‍💼"
    },
    "LOCATION_MANAGEMENT": {
        "name": "مدیریت مکان‌ها",
        "desc": "افزودن، ویرایش و حذف مکان‌های جغرافیایی",
        "icon": "🌎"
    },
    "SERVER_MANAGEMENT": {
        "name": "مدیریت سرورها",
        "desc": "وضعیت و مدیریت سرورها",
        "icon": "🖥️"
    },
    "SERVICE_MANAGEMENT": {
        "name": "مدیریت خدمات",
        "desc": "سرویس‌ها، قیمت‌ها و ویژگی‌ها",
        "icon": "🛒"
    },
    "USER_MANAGEMENT": {
        "name": "مدیریت کاربران",
        "desc": "اطلاعات، وضعیت و عملکرد کاربران",
        "icon": "👥"
    },
    "DISCOUNT_MARKETING": {
        "name": "تخفیف‌ها و بازاریابی",
        "desc": "مدیریت کدهای تخفیف و کمپین‌های بازاریابی",
        "icon": "🏷️"
    },
    "FINANCIAL_REPORTS": {
        "name": "گزارش‌های مالی",
        "desc": "گزارش‌های درآمد، پرداخت‌ها و تراکنش‌ها",
        "icon": "📊"
    },
    "BULK_MESSAGING": {
        "name": "پیام‌رسانی انبوه",
        "desc": "ارسال پیام به گروه‌های کاربری",
        "icon": "📨"
    },
    "SERVER_MONITORING": {
        "name": "مانیتورینگ سرور",
        "desc": "نظارت بر وضعیت و عملکرد سرورها",
        "icon": "📡"
    },
    "ACCESS_MANAGEMENT": {
        "name": "مدیریت دسترسی",
        "desc": "تنظیم سطوح دسترسی و نقش‌ها",
        "icon": "🔐"
    },
    "SYSTEM_SETTINGS": {
        "name": "تنظیمات سیستم",
        "desc": "پیکربندی و تنظیمات کلی سیستم",
        "icon": "⚙️"
    },
    "BACKUP_RESTORE": {
        "name": "پشتیبان‌گیری و بازیابی",
        "desc": "مدیریت نسخه‌های پشتیبان و بازیابی",
        "icon": "🔄"
    },
    "PAYMENT_NOTIFICATION": {
        "name": "اعلان‌های پرداخت",
        "desc": "اطلاع‌رسانی پرداخت‌های جدید و تاییدشده",
        "icon": "💰"
    },
    "ERROR_ALERTS": {
        "name": "هشدارهای خطا",
        "desc": "هشدار خطاهای سیستمی و مشکلات فنی",
        "icon": "⚠️"
    }
} 