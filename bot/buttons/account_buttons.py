"""
دکمه‌های مربوط به مدیریت حساب‌ها و اشتراک‌ها
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# شناسه callback برای نمایش اشتراک‌های من
MY_ACCOUNTS_CB = "accounts:my"

# TODO: Add other account related buttons later (e.g., view details, renew) 