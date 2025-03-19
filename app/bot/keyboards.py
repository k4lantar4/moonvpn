"""
Keyboard layouts for MoonVPN Telegram Bot.

This module provides keyboard layouts for various interactive menus
used in the bot's conversation flows.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_plan_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for VPN plan selection."""
    keyboard = [
        [
            InlineKeyboardButton("1 Month - $9.99", callback_data="plan:1_month"),
            InlineKeyboardButton("3 Months - $24.99", callback_data="plan:3_months")
        ],
        [
            InlineKeyboardButton("6 Months - $44.99", callback_data="plan:6_months"),
            InlineKeyboardButton("1 Year - $79.99", callback_data="plan:1_year")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_location_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for server location selection."""
    keyboard = [
        [
            InlineKeyboardButton("🇺🇸 United States", callback_data="location:us"),
            InlineKeyboardButton("🇬🇧 United Kingdom", callback_data="location:uk")
        ],
        [
            InlineKeyboardButton("🇩🇪 Germany", callback_data="location:de"),
            InlineKeyboardButton("🇫🇷 France", callback_data="location:fr")
        ],
        [
            InlineKeyboardButton("🇳🇱 Netherlands", callback_data="location:nl"),
            InlineKeyboardButton("🇸🇪 Sweden", callback_data="location:se")
        ],
        [
            InlineKeyboardButton("🇸🇬 Singapore", callback_data="location:sg"),
            InlineKeyboardButton("🇯🇵 Japan", callback_data="location:jp")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for payment method selection."""
    keyboard = [
        [
            InlineKeyboardButton("💳 Credit Card", callback_data="payment:card"),
            InlineKeyboardButton("💰 Wallet", callback_data="payment:wallet")
        ],
        [
            InlineKeyboardButton("🏦 Bank Transfer", callback_data="payment:bank"),
            InlineKeyboardButton("💵 ZarinPal", callback_data="payment:zarinpal")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for user settings."""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Language", callback_data="settings:language"),
            InlineKeyboardButton("🔔 Notifications", callback_data="settings:notifications")
        ],
        [
            InlineKeyboardButton("🔄 Auto-renewal", callback_data="settings:auto_renewal"),
            InlineKeyboardButton("🔒 Privacy", callback_data="settings:privacy")
        ],
        [
            InlineKeyboardButton("📱 Device Management", callback_data="settings:devices"),
            InlineKeyboardButton("💳 Payment Methods", callback_data="settings:payments")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for language selection."""
    keyboard = [
        [
            InlineKeyboardButton("🇺🇸 English", callback_data="language:en"),
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="language:fa")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_notification_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for notification settings."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Enable All", callback_data="notifications:all_on"),
            InlineKeyboardButton("❌ Disable All", callback_data="notifications:all_off")
        ],
        [
            InlineKeyboardButton("📊 Usage Alerts", callback_data="notifications:usage"),
            InlineKeyboardButton("⏰ Expiry Reminders", callback_data="notifications:expiry")
        ],
        [
            InlineKeyboardButton("🔔 Service Updates", callback_data="notifications:updates"),
            InlineKeyboardButton("💡 Promotions", callback_data="notifications:promotions")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_auto_renewal_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for auto-renewal settings."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Enable", callback_data="auto_renewal:on"),
            InlineKeyboardButton("❌ Disable", callback_data="auto_renewal:off")
        ],
        [
            InlineKeyboardButton("💰 Payment Method", callback_data="auto_renewal:payment"),
            InlineKeyboardButton("📅 Renewal Date", callback_data="auto_renewal:date")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_privacy_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for privacy settings."""
    keyboard = [
        [
            InlineKeyboardButton("👤 Profile Visibility", callback_data="privacy:profile"),
            InlineKeyboardButton("📱 Device Tracking", callback_data="privacy:devices")
        ],
        [
            InlineKeyboardButton("📊 Usage Statistics", callback_data="privacy:stats"),
            InlineKeyboardButton("🔒 Data Protection", callback_data="privacy:data")
        ]
    ]
    return InlineKeyboardMarkup(keyboard) 