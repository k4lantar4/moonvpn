"""
Keyboard layouts for user profile management in MoonVPN Telegram Bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_profile_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main profile menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("👤 اطلاعات پروفایل", callback_data="profile:info"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="profile:settings")
        ],
        [
            InlineKeyboardButton("📊 تاریخچه اشتراک", callback_data="profile:subscriptions"),
            InlineKeyboardButton("💰 تراکنش‌ها", callback_data="profile:transactions")
        ],
        [
            InlineKeyboardButton("🎯 امتیازات", callback_data="profile:points"),
            InlineKeyboardButton("👥 سیستم معرفی", callback_data="profile:referral")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="profile:back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Create settings menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔔 تنظیمات اعلان", callback_data="settings:notifications"),
            InlineKeyboardButton("🌐 زبان", callback_data="settings:language")
        ],
        [
            InlineKeyboardButton("🔄 تمدید خودکار", callback_data="settings:auto_renewal"),
            InlineKeyboardButton("🔒 امنیت", callback_data="settings:security")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="settings:back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_notification_settings_keyboard() -> InlineKeyboardMarkup:
    """Create notification settings keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ اعلان‌های اشتراک", callback_data="notify:subscription"),
            InlineKeyboardButton("✅ اعلان‌های تراکنش", callback_data="notify:transaction")
        ],
        [
            InlineKeyboardButton("✅ اعلان‌های سیستم", callback_data="notify:system"),
            InlineKeyboardButton("✅ اعلان‌های امتیاز", callback_data="notify:points")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="notify:back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Create language selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang:fa"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang:en")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="lang:back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_auto_renewal_keyboard() -> InlineKeyboardMarkup:
    """Create auto-renewal settings keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ فعال", callback_data="renewal:enable"),
            InlineKeyboardButton("❌ غیرفعال", callback_data="renewal:disable")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="renewal:back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_security_settings_keyboard() -> InlineKeyboardButton:
    """Create security settings keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔑 تغییر رمز عبور", callback_data="security:password"),
            InlineKeyboardButton("📱 تغییر شماره موبایل", callback_data="security:phone")
        ],
        [
            InlineKeyboardButton("🔐 احراز هویت دو مرحله‌ای", callback_data="security:2fa"),
            InlineKeyboardButton("📋 دستگاه‌های متصل", callback_data="security:devices")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="security:back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_history_navigation_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Create navigation keyboard for history pages."""
    keyboard = []
    
    # Previous page button
    if page > 1:
        keyboard.append([
            InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"history:prev:{page-1}")
        ])
    
    # Page number
    keyboard.append([
        InlineKeyboardButton(f"📄 صفحه {page} از {total_pages}", callback_data="history:current")
    ])
    
    # Next page button
    if page < total_pages:
        keyboard.append([
            InlineKeyboardButton("➡️ صفحه بعد", callback_data=f"history:next:{page+1}")
        ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data="history:back")
    ])
    
    return InlineKeyboardMarkup(keyboard) 