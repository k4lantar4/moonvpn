"""
دکمه‌های عمومی و مشترک در ربات
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# فقط دکمه‌های فعال و پاسخ پیش‌فرض
HELP_CB = "common:help"
SUPPORT_CB = "common:support"
BACK_TO_MAIN_CB = "common:back_main"
BACK_TO_PLANS_CB = "common:back_plans"

# TODO: Add more common buttons like pagination, etc.

def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """کیبورد بازگشت به منوی اصلی"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data=BACK_TO_MAIN_CB))
    return builder.as_markup()

def get_help_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❓ راهنما", callback_data=HELP_CB))
    return builder.as_markup()

def get_support_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🆘 پشتیبانی", callback_data=SUPPORT_CB))
    return builder.as_markup()

# Add other common keyboards if needed, like back to plans 