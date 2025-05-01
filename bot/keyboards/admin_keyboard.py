"""
چینش کیبورد پنل ادمین
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.buttons.receipt_buttons import get_admin_receipts_button

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """ایجاد کیبورد اینلاین برای پنل ادمین"""
    kb = InlineKeyboardBuilder()
    
    # دکمه‌های پنل ادمین
    kb.button(text="📊 آمار", callback_data="admin:stats")
    kb.button(text="🔄 همگام‌سازی پنل‌ها", callback_data="admin:sync_panels")
    kb.button(text="📟 مدیریت پنل‌ها", callback_data="admin:panel:list")
    kb.button(text="👥 کاربران", callback_data="admin:user:list")
    kb.button(text="💰 پلن‌ها", callback_data="admin:plan:list")
    kb.button(text="💸 تراکنش‌ها", callback_data="admin:order:list")
    kb.add(get_admin_receipts_button())  # دکمه مدیریت رسیدها
    
    # دکمه خرید سرویس - برای سازگاری با تجربه کاربران
    kb.button(text="🛒 خرید سرویس", callback_data="admin:buy")
    
    kb.button(text="💳 مدیریت کارت‌های بانکی", callback_data="admin:bank_card:list")
    kb.button(text="⚙️ تنظیمات", callback_data="admin:settings")
    kb.button(text="📄 گزارش تمدیدها", callback_data="admin:renewal_log")
    kb.button(text="🔙 بازگشت", callback_data="start")
    kb.button(text="➕ ثبت پنل جدید", callback_data="admin:panel:register")
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف
    kb.adjust(2)
    
    return kb.as_markup() 