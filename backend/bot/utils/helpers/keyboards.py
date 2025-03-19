"""
Keyboard builders for Telegram bot.
"""

import logging
from typing import List, Dict, Any, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from core.config import settings
from core.utils.helpers import format_price, format_bytes, get_subscription_status

logger = logging.getLogger(__name__)

def build_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Build main menu keyboard."""
    buttons = [
        [KeyboardButton("🛒 خرید اشتراک"), KeyboardButton("👤 حساب کاربری")],
        [KeyboardButton("📊 وضعیت سرویس"), KeyboardButton("🔄 تغییر سرور")],
        [KeyboardButton("💬 پشتیبانی"), KeyboardButton("ℹ️ راهنما")]
    ]
    
    if is_admin:
        buttons.insert(0, [KeyboardButton("🎛 پنل مدیریت")])
    
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True
    )

def build_admin_keyboard() -> InlineKeyboardMarkup:
    """Build admin panel keyboard."""
    buttons = [
        [
            InlineKeyboardButton("📊 گزارش درآمد", callback_data="admin_income"),
            InlineKeyboardButton("🖥 مدیریت سرورها", callback_data="admin_servers")
        ],
        [
            InlineKeyboardButton("📈 آمار ترافیک", callback_data="admin_traffic"),
            InlineKeyboardButton("🎫 کدهای تخفیف", callback_data="admin_discounts")
        ],
        [
            InlineKeyboardButton("👥 کاربران", callback_data="admin_users"),
            InlineKeyboardButton("📨 پیام گروهی", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings"),
            InlineKeyboardButton("❌ خروج", callback_data="admin_exit")
        ]
    ]
    
    return InlineKeyboardMarkup(buttons)

def build_subscription_keyboard() -> InlineKeyboardMarkup:
    """Build subscription plans keyboard."""
    buttons = []
    row = []
    
    for i, plan in enumerate(settings.SUBSCRIPTION_PLANS):
        button = InlineKeyboardButton(
            f"{plan['name']} - {format_price(plan['price'])}",
            callback_data=f"plan_{plan['id']}"
        )
        
        row.append(button)
        if len(row) == 2 or i == len(settings.SUBSCRIPTION_PLANS) - 1:
            buttons.append(row)
            row = []
    
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(buttons)

def build_payment_keyboard(amount: int, order_id: str) -> InlineKeyboardMarkup:
    """Build payment methods keyboard."""
    buttons = [
        [InlineKeyboardButton("💳 کارت به کارت", callback_data=f"card_{order_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_plans")]
    ]
    
    # Add Zarinpal if configured
    if settings.ZARINPAL_MERCHANT_ID:
        buttons.insert(
            0,
            [InlineKeyboardButton(
                "💳 درگاه زرین‌پال",
                callback_data=f"zarinpal_{order_id}"
            )]
        )
    
    return InlineKeyboardMarkup(buttons)

def build_server_keyboard() -> InlineKeyboardMarkup:
    """Build server selection keyboard."""
    buttons = []
    row = []
    
    for i, location in enumerate(settings.SERVER_LOCATIONS):
        button = InlineKeyboardButton(
            location['name'],
            callback_data=f"server_{location['id']}"
        )
        
        row.append(button)
        if len(row) == 2 or i == len(settings.SERVER_LOCATIONS) - 1:
            buttons.append(row)
            row = []
    
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(buttons)

def build_account_keyboard(accounts: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Build user accounts keyboard."""
    buttons = []
    
    for account in accounts:
        status = get_subscription_status(
            account['expiry_date'],
            account['traffic_used'],
            account['traffic_limit']
        )
        
        button_text = (
            f"{status} {account.get('name', 'اشتراک')} - "
            f"{format_bytes(account['traffic_used'])}/{format_bytes(account['traffic_limit'])}"
        )
        
        buttons.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"account_{account['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(buttons)

def build_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Build broadcast options keyboard."""
    buttons = [
        [
            InlineKeyboardButton("👥 همه کاربران", callback_data="broadcast_all"),
            InlineKeyboardButton("✅ کاربران فعال", callback_data="broadcast_active")
        ],
        [
            InlineKeyboardButton("⭐️ کاربران ویژه", callback_data="broadcast_premium"),
            InlineKeyboardButton("❌ کاربران غیرفعال", callback_data="broadcast_inactive")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    
    return InlineKeyboardMarkup(buttons)

def build_discount_keyboard(codes: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Build discount codes keyboard."""
    buttons = []
    
    for code in codes:
        status = "✅" if code['status'] == 'active' else "❌"
        button_text = f"{status} {code['code']} - {code['description']}"
        
        buttons.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"discount_{code['code']}"
            )
        ])
    
    buttons.extend([
        [InlineKeyboardButton("➕ کد جدید", callback_data="new_discount")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ])
    
    return InlineKeyboardMarkup(buttons)

def build_user_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Build user management keyboard."""
    buttons = [
        [
            InlineKeyboardButton("🔄 تمدید اشتراک", callback_data=f"extend_{user_id}"),
            InlineKeyboardButton("❌ مسدودسازی", callback_data=f"block_{user_id}")
        ],
        [
            InlineKeyboardButton("📨 ارسال پیام", callback_data=f"message_{user_id}"),
            InlineKeyboardButton("📊 گزارش", callback_data=f"report_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_users")]
    ]
    
    return InlineKeyboardMarkup(buttons)

def build_settings_keyboard() -> InlineKeyboardMarkup:
    """Build settings keyboard."""
    buttons = [
        [
            InlineKeyboardButton("🏷 پلن‌ها", callback_data="settings_plans"),
            InlineKeyboardButton("🌍 سرورها", callback_data="settings_servers")
        ],
        [
            InlineKeyboardButton("💰 پرداخت", callback_data="settings_payment"),
            InlineKeyboardButton("👥 دسترسی‌ها", callback_data="settings_access")
        ],
        [
            InlineKeyboardButton("📨 پیام‌ها", callback_data="settings_messages"),
            InlineKeyboardButton("⚙️ عمومی", callback_data="settings_general")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    
    return InlineKeyboardMarkup(buttons)

def build_confirmation_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """Build confirmation keyboard."""
    buttons = [
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ انصراف", callback_data=f"cancel_{action}")
        ]
    ]
    
    return InlineKeyboardMarkup(buttons)

def build_navigation_keyboard(
    current_page: int,
    total_pages: int,
    base_callback: str
) -> InlineKeyboardMarkup:
    """Build navigation keyboard."""
    buttons = []
    
    # Add page info
    page_text = f"صفحه {current_page} از {total_pages}"
    buttons.append([InlineKeyboardButton(page_text, callback_data="noop")])
    
    # Add navigation buttons
    nav_buttons = []
    
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                "◀️",
                callback_data=f"{base_callback}_page_{current_page - 1}"
            )
        )
    
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                "▶️",
                callback_data=f"{base_callback}_page_{current_page + 1}"
            )
        )
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Add back button
    buttons.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data=f"back_to_{base_callback}"
        )
    ])
    
    return InlineKeyboardMarkup(buttons) 