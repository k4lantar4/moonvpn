"""
چینش کیبورد پنل ادمین
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """ایجاد کیبورد اینلاین برای پنل ادمین"""
    kb = InlineKeyboardBuilder()
    
    # دکمه‌های پنل ادمین
    kb.button(text="📊 آمار", callback_data="admin_stats")
    kb.button(text="🔄 همگام‌سازی پنل‌ها", callback_data="sync_panels")
    kb.button(text="📟 مدیریت پنل‌ها", callback_data="manage_panels")
    kb.button(text="👥 کاربران", callback_data="admin_users")
    kb.button(text="💰 پلن‌ها", callback_data="admin_plans")
    kb.button(text="⚙️ تنظیمات", callback_data="admin_settings")
    kb.button(text="🔙 بازگشت", callback_data="start") # Assuming 'start' goes to main menu
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف
    kb.adjust(2)
    
    return kb.as_markup() 