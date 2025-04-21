"""
کیبوردهای مربوط به دستور /start
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.models.user import UserRole

def get_start_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    """ایجاد کیبورد شروع بر اساس نقش کاربر"""
    
    # دکمه‌های مشترک برای همه کاربران
    buttons = [
        [
            InlineKeyboardButton(text="🛒 خرید اشتراک", callback_data="buy"),
            InlineKeyboardButton(text="💰 کیف پول", callback_data="wallet")
        ],
        [
            InlineKeyboardButton(text="📱 اکانت‌های من", callback_data="my_accounts"),
            InlineKeyboardButton(text="❓ راهنما", callback_data="help")
        ]
    ]
    
    # دکمه‌های مخصوص ادمین
    if role == UserRole.ADMIN:
        admin_buttons = [
            [
                InlineKeyboardButton(text="👥 مدیریت کاربران", callback_data="admin_users"),
                InlineKeyboardButton(text="📊 آمار", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text="⚙️ تنظیمات", callback_data="admin_settings"),
                InlineKeyboardButton(text="🔄 همگام‌سازی", callback_data="admin_sync")
            ]
        ]
        buttons.extend(admin_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 