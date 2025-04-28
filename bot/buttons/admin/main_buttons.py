"""
دکمه‌های اصلی پنل ادمین
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """
    ایجاد کیبورد اینلاین برای پنل اصلی ادمین
    
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های اصلی مدیریت
    """
    kb = InlineKeyboardBuilder()
    
    # دکمه‌های آمار و همگام‌سازی
    kb.button(text="📊 آمار", callback_data="admin:stats")
    kb.button(text="🔄 همگام‌سازی پنل‌ها", callback_data="admin:sync_panels")
    
    # دکمه‌های مدیریت پنل، کاربران و پلن‌ها
    kb.button(text="📟 مدیریت پنل‌ها", callback_data="admin:panel:list")
    kb.button(text="👥 مدیریت کاربران", callback_data="admin:user:list")
    kb.button(text="💰 مدیریت پلن‌ها", callback_data="admin:plan:list")
    
    # دکمه‌های مدیریت تراکنش‌ها و رسیدها
    kb.button(text="💸 تراکنش‌ها", callback_data="admin:order:list")
    kb.button(text="🧾 رسیدهای در انتظار", callback_data="admin:receipt:pending")
    
    # سایر دکمه‌های مدیریتی
    kb.button(text="💳 مدیریت کارت‌های بانکی", callback_data="admin:bank_card:list")
    kb.button(text="⚙️ تنظیمات", callback_data="admin:settings")
    kb.button(text="📄 گزارش تمدیدها", callback_data="admin:renewal_log")
    
    # دکمه‌های کاربردی
    kb.button(text="➕ ثبت پنل جدید", callback_data="admin:panel:register")
    kb.button(text="🔙 بازگشت", callback_data="start")
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف
    kb.adjust(2)
    
    return kb.as_markup() 