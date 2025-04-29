"""
کیبوردهای مربوط به دستور /start
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.models.enums import UserRole
from bot.buttons.common_buttons import HELP_CB, SUPPORT_CB

def get_start_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    """ایجاد کیبورد شروع بر اساس نقش کاربر"""
    
    # دکمه‌های مشترک برای همه کاربران
    buttons = [
        [
            InlineKeyboardButton(text="🛒 خرید اشتراک", callback_data="buy"),
            InlineKeyboardButton(text="💰 کیف پول", callback_data="wallet")
        ],
        [
            InlineKeyboardButton(text="📱 اکانت‌های من", callback_data="my_accounts")
        ],
        [
            InlineKeyboardButton(text="❓ راهنما", callback_data=HELP_CB),
            InlineKeyboardButton(text="🆘 پشتیبانی", callback_data=SUPPORT_CB)
        ]
    ]
    
    # دکمه‌های مخصوص ادمین
    if role == UserRole.AGENT:
        buttons.append([
            InlineKeyboardButton(text="👥 مدیریت کاربران", callback_data="agent_users"),
            InlineKeyboardButton(text="📊 آمار نماینده", callback_data="agent_stats")
        ])
    if role == UserRole.ADMIN or role == UserRole.AGENT:
        buttons.append([
            InlineKeyboardButton(text="👥 مدیریت کاربران", callback_data="admin_users"),
            InlineKeyboardButton(text="📊 آمار", callback_data="admin_stats")
        ])
        buttons.append([
            InlineKeyboardButton(text="⚙️ تنظیمات", callback_data="admin_settings"),
            InlineKeyboardButton(text="🔄 همگام‌سازی", callback_data="admin_sync")
        ])
    if role == UserRole.SUPERADMIN:
        buttons.append([
            InlineKeyboardButton(text="👑 مدیریت کل سیستم", callback_data="superadmin_panel"),
            InlineKeyboardButton(text="🛡️ مدیریت ادمین‌ها", callback_data="superadmin_admins")
        ])
        buttons.append([
            InlineKeyboardButton(text="📊 آمار کل", callback_data="superadmin_stats"),
            InlineKeyboardButton(text="⚙️ تنظیمات پیشرفته", callback_data="superadmin_settings")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 