"""
Keyboard layouts for the MoonVPN Telegram bot.

This module implements various keyboard layouts for different bot interactions
including main menu, help menu, settings, and purchase flows.
"""

from typing import List, Optional, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Create the main menu keyboard."""
    keyboard = [
        [
            KeyboardButton("🛍️ خرید VPN"),
            KeyboardButton("🔍 وضعیت حساب")
        ],
        [
            KeyboardButton("⚙️ تنظیمات"),
            KeyboardButton("❓ راهنما")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_help_keyboard() -> InlineKeyboardMarkup:
    """Create the help menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📱 نحوه اتصال", callback_data="help_connect"),
            InlineKeyboardButton("💳 راهنمای پرداخت", callback_data="help_payment")
        ],
        [
            InlineKeyboardButton("🌍 سرورها", callback_data="help_locations"),
            InlineKeyboardButton("🔒 نکات امنیتی", callback_data="help_security")
        ],
        [
            InlineKeyboardButton("📞 پشتیبانی", callback_data="help_support")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Create the settings menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("👤 پروفایل", callback_data="settings_profile"),
            InlineKeyboardButton("🔔 اعلان‌ها", callback_data="settings_notifications")
        ],
        [
            InlineKeyboardButton("🌐 زبان", callback_data="settings_language"),
            InlineKeyboardButton("🔄 تمدید خودکار", callback_data="settings_renewal")
        ],
        [
            InlineKeyboardButton("🔒 امنیت", callback_data="settings_security"),
            InlineKeyboardButton("📱 دستگاه‌ها", callback_data="settings_devices")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_plan_selection_keyboard(plans: List[dict]) -> InlineKeyboardMarkup:
    """Create the VPN plan selection keyboard."""
    keyboard = []
    for plan in plans:
        keyboard.append([
            InlineKeyboardButton(
                f"{plan['name']} - {plan['price']} تومان",
                callback_data=f"plan_{plan['id']}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("❌ انصراف", callback_data="cancel")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_location_selection_keyboard(locations: List[dict]) -> InlineKeyboardMarkup:
    """Create the server location selection keyboard."""
    keyboard = []
    for location in locations:
        keyboard.append([
            InlineKeyboardButton(
                f"{location['flag']} {location['name']}",
                callback_data=f"location_{location['id']}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("❌ انصراف", callback_data="cancel")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_payment_method_keyboard() -> InlineKeyboardMarkup:
    """Create the payment method selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("💳 کارت به کارت", callback_data="payment_card"),
            InlineKeyboardButton("🏦 واریز مستقیم", callback_data="payment_bank")
        ],
        [
            InlineKeyboardButton("💵 زرین‌پال", callback_data="payment_zarinpal"),
            InlineKeyboardButton("👛 کیف پول", callback_data="payment_wallet")
        ],
        [
            InlineKeyboardButton("❌ انصراف", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Create the confirmation keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data="confirm"),
            InlineKeyboardButton("❌ انصراف", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Create the admin control keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
            InlineKeyboardButton("👥 کاربران", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("🖥️ سرورها", callback_data="admin_servers"),
            InlineKeyboardButton("💰 تراکنش‌ها", callback_data="admin_transactions")
        ],
        [
            InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_status_keyboard(status_info: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Create keyboard layout for status display based on account status.
    
    Args:
        status_info: Dictionary containing account status information
        
    Returns:
        InlineKeyboardMarkup with appropriate buttons
    """
    buttons: List[List[InlineKeyboardButton]] = []
    
    if not status_info["has_account"]:
        # No active account
        buttons.append([
            InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy")
        ])
    elif status_info["status"] == "active":
        # Active account
        buttons.extend([
            [
                InlineKeyboardButton("📥 دریافت کانفیگ", callback_data="get_config"),
                InlineKeyboardButton("🔄 تمدید اشتراک", callback_data="renew")
            ],
            [
                InlineKeyboardButton("🌍 تغییر سرور", callback_data="change_server"),
                InlineKeyboardButton("📊 جزئیات مصرف", callback_data="usage_details")
            ]
        ])
    elif status_info["status"] == "expired":
        # Expired account
        buttons.append([
            InlineKeyboardButton("🔄 تمدید اشتراک", callback_data="renew")
        ])
    elif status_info["status"] == "error":
        # Error state
        buttons.append([
            InlineKeyboardButton("💬 پشتیبانی", callback_data="support")
        ])
    
    # Add back button
    buttons.append([
        InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(buttons)

def get_renewal_keyboard(plans: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Create keyboard layout for subscription renewal.
    
    Args:
        plans: List of available renewal plans
        
    Returns:
        InlineKeyboardMarkup with plan selection buttons
    """
    buttons: List[List[InlineKeyboardButton]] = []
    
    for plan in plans:
        buttons.append([
            InlineKeyboardButton(
                f"{plan['name']} - {plan['price']} تومان",
                callback_data=f"renew_plan_{plan['id']}"
            )
        ])
    
    # Add back button
    buttons.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_status")
    ])
    
    return InlineKeyboardMarkup(buttons)

def get_server_selection_keyboard(locations: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Create keyboard layout for server selection.
    
    Args:
        locations: List of available server locations
        
    Returns:
        InlineKeyboardMarkup with location selection buttons
    """
    buttons: List[List[InlineKeyboardButton]] = []
    
    for location in locations:
        buttons.append([
            InlineKeyboardButton(
                f"🌍 {location['name']} ({location['server_count']} سرور)",
                callback_data=f"select_server_{location['id']}"
            )
        ])
    
    # Add back button
    buttons.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_status")
    ])
    
    return InlineKeyboardMarkup(buttons)

def get_usage_history_keyboard(
    current_page: int,
    total_pages: int,
    days: int = 7
) -> InlineKeyboardMarkup:
    """
    Create keyboard layout for usage history navigation.
    
    Args:
        current_page: Current page number
        total_pages: Total number of pages
        days: Number of days to show per page
        
    Returns:
        InlineKeyboardMarkup with navigation buttons
    """
    buttons: List[List[InlineKeyboardButton]] = []
    
    # Navigation buttons
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                "⬅️ قبلی",
                callback_data=f"history_page_{current_page - 1}"
            )
        )
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                "➡️ بعدی",
                callback_data=f"history_page_{current_page + 1}"
            )
        )
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Time range buttons
    buttons.append([
        InlineKeyboardButton(
            "📅 7 روز",
            callback_data="history_days_7"
        ),
        InlineKeyboardButton(
            "📅 30 روز",
            callback_data="history_days_30"
        ),
        InlineKeyboardButton(
            "📅 90 روز",
            callback_data="history_days_90"
        )
    ])
    
    # Back button
    buttons.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_status")
    ])
    
    return InlineKeyboardMarkup(buttons)

def get_usage_export_keyboard() -> InlineKeyboardMarkup:
    """
    Create keyboard layout for usage analytics export options.
    
    Returns:
        InlineKeyboardMarkup with export format options and back button
    """
    buttons: List[List[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                "📊 PDF گزارش",
                callback_data="export_pdf"
            ),
            InlineKeyboardButton(
                "📈 نمودار",
                callback_data="export_chart"
            )
        ],
        [
            InlineKeyboardButton(
                "📝 متن",
                callback_data="export_text"
            ),
            InlineKeyboardButton(
                "📋 CSV",
                callback_data="export_csv"
            )
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_status")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_analytics_dashboard_keyboard() -> InlineKeyboardMarkup:
    """
    Create keyboard layout for the analytics dashboard.
    
    Returns:
        InlineKeyboardMarkup with analytics options and navigation buttons
    """
    buttons: List[List[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                "📊 نمودار مصرف",
                callback_data="analytics_chart"
            ),
            InlineKeyboardButton(
                "📈 آمار کلی",
                callback_data="analytics_stats"
            )
        ],
        [
            InlineKeyboardButton(
                "🌍 سرورها",
                callback_data="analytics_servers"
            ),
            InlineKeyboardButton(
                "⏱️ زمان‌بندی",
                callback_data="analytics_timing"
            )
        ],
        [
            InlineKeyboardButton(
                "📥 دریافت گزارش",
                callback_data="export_analytics"
            )
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_status")
        ]
    ]
    return InlineKeyboardMarkup(buttons) 