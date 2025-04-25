"""
دکمه‌های عمومی و مشترک در ربات
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# شناسه‌های callback برای دکمه‌های عمومی
HELP_MENU_CB = "common:help_menu"
SUPPORT_CHAT_CB = "common:support_chat"
BACK_TO_MAIN_CB = "common:back_main" # Callback for back to main menu button
BACK_TO_PLANS_CB = "common:back_plans" # Callback for back to plans list

# TODO: Add more common buttons like pagination, etc.

def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """کیبرد بازگشت به منوی اصلی"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data=BACK_TO_MAIN_CB))
    return builder.as_markup()

# Add other common keyboards if needed, like back to plans 