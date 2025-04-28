"""
bot/buttons/receipt_buttons.py

دکمه‌های مربوط به مدیریت رسیدهای پرداخت
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_receipts_button() -> InlineKeyboardButton:
    """
    دکمه مدیریت رسیدها برای پنل ادمین
    
    Returns:
        InlineKeyboardButton: دکمه مدیریت رسیدها
    """
    return InlineKeyboardButton(
        text="🧾 رسیدهای در انتظار", 
        callback_data="admin_pending_receipts"
    ) 