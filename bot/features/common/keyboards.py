"""
کیبوردهای مشترک ربات (مانند منوی استارت، راهنما و ...)
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from db.models.enums import UserRole

# Callback data constants (میتواند در یک فایل جداگانه constants.py تعریف شود)
HЕLP_CB = "common_help"
SUPPORT_CB = "common_support"
ADMIN_PANEL_CB = "admin_panel"

def get_start_inline_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    """
    ایجاد کیبورد inline شروع بر اساس نقش کاربر
    """
    buttons = [
        [
            InlineKeyboardButton(text="🛒 خرید اشتراک", callback_data="buy_start"), # اصلاح callback_data برای وضوح
            InlineKeyboardButton(text="💰 کیف پول", callback_data="wallet_menu") # اصلاح callback_data برای وضوح
        ],
        [
            InlineKeyboardButton(text="📱 اکانت‌های من", callback_data="my_accounts_list") # اصلاح callback_data برای وضوح
        ],
        [
            InlineKeyboardButton(text="👤 پروفایل من", callback_data="profile_show"), # اضافه کردن دکمه پروفایل
        ],
        [
            InlineKeyboardButton(text="❓ راهنما", callback_data=HЕLP_CB),
            InlineKeyboardButton(text="🆘 پشتیبانی", callback_data=SUPPORT_CB)
        ]
    ]

    # افزودن دکمه پنل ادمین اگر کاربر ادمین است
    if role in [UserRole.ADMIN, UserRole.SUPERADMIN]: # بررسی نقش‌های ادمین
        buttons.append([
            InlineKeyboardButton(text="👑 پنل مدیریت", callback_data=ADMIN_PANEL_CB)
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_reply_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    """
    ایجاد کیبورد reply اصلی بر اساس نقش کاربر
    """
    keyboard = [
        [KeyboardButton(text="🛒 خرید اشتراک"), KeyboardButton(text="💰 کیف پول")],
        [KeyboardButton(text="📱 اکانت‌های من"), KeyboardButton(text="👤 پروفایل من")],
        [KeyboardButton(text="❓ راهنما"), KeyboardButton(text="🆘 پشتیبانی")],
    ]
    
    # افزودن دکمه پنل ادمین اگر کاربر ادمین است
    if role in [UserRole.ADMIN, UserRole.SUPERADMIN]:
         keyboard.insert(0, [KeyboardButton(text="👑 پنل مدیریت")]) # اضافه کردن در ردیف اول
         
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# TODO: پیاده‌سازی کیبوردهای دیگر مربوط به بخش common (مثل راهنما، پشتیبانی) 