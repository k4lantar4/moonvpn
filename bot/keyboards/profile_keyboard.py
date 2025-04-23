"""
چینش کیبوردهای مربوط به دستور پروفایل
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """ایجاد کیبورد اینلاین برای دستور پروفایل"""
    kb = InlineKeyboardBuilder()
    
    # افزودن دکمه‌های مربوط به پروفایل
    kb.button(text="🔄 به‌روزرسانی", callback_data="refresh_profile")
    kb.button(text="⚙️ تنظیمات", callback_data="profile_settings")
    kb.button(text="📊 جزئیات حساب", callback_data="account_details")
    kb.button(text="💳 کیف پول", callback_data="wallet_menu") # Callback data from wallet_buttons
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف
    kb.adjust(2)
    
    return kb.as_markup() 