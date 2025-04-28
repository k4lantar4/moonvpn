"""
دکمه‌های پنل ادمین - نسخه قدیمی

این فایل برای حفظ سازگاری با کد قبلی حفظ شده است.
تمام توابع به فایل‌های جداگانه در دایرکتوری admin/ منتقل شده‌اند.
"""

# Re-export all admin buttons from the admin package
from bot.buttons.admin.main_buttons import get_admin_panel_keyboard
from bot.buttons.admin.panel_buttons import get_panel_list_keyboard, get_panel_manage_buttons
from bot.buttons.admin.bank_card_buttons import (
    get_bank_cards_keyboard, 
    get_bank_card_manage_buttons,
    get_bank_card_rotation_policy_keyboard,
    get_confirm_delete_bank_card_keyboard
)
from bot.buttons.admin.receipt_buttons import get_admin_receipts_button
from bot.buttons.admin.user_buttons import get_user_list_keyboard, get_user_manage_buttons
from bot.buttons.admin.plan_buttons import get_plan_list_keyboard, get_plan_manage_buttons
from bot.buttons.admin.order_buttons import get_order_list_keyboard, get_order_manage_buttons

# Function to get renewal log button (for backward compatibility)
from aiogram.types import InlineKeyboardButton

def get_renewal_log_button() -> InlineKeyboardButton:
    """Returns the button for viewing client renewal logs."""
    return InlineKeyboardButton(
        text="📄 گزارش تمدید کلاینت‌ها",
        callback_data="admin:renewal_log"
    )