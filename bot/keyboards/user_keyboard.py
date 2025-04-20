"""
کیبوردهای مختص کاربران در ربات
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد اصلی برای منوی ربات"""
    
    # دکمه‌های ردیف اول
    btn_plans = KeyboardButton(text="📱 پلن‌های VPN")
    btn_profile = KeyboardButton(text="👤 حساب کاربری")
    
    # دکمه‌های ردیف دوم
    btn_accounts = KeyboardButton(text="🔑 سرویس‌های من")
    btn_wallet = KeyboardButton(text="💰 کیف پول")
    
    # دکمه‌های ردیف سوم
    btn_help = KeyboardButton(text="🆘 راهنما")
    btn_contact = KeyboardButton(text="📞 پشتیبانی")
    
    # ایجاد کیبورد با استفاده از ساختار صحیح برای aiogram v3
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [btn_plans, btn_profile],
            [btn_accounts, btn_wallet],
            [btn_help, btn_contact]
        ],
        resize_keyboard=True,
        type="reply"
    )
    
    return keyboard
