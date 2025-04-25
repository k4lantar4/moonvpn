"""
کیبردهای Inline مربوط به کیف پول کاربران
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# شناسه‌های callback برای دکمه‌های کیف پول
WALLET_MENU_CB = "wallet:menu"
TOPUP_CB = "wallet:topup"
CANCEL_CB = "wallet:cancel"
CONFIRM_AMOUNT_PREFIX = "wallet:confirm_amount:"

def get_wallet_keyboard() -> InlineKeyboardMarkup:
    """
    کیبرد اصلی برای کیف پول
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="💰 افزایش موجودی", callback_data=TOPUP_CB))
    
    return builder.as_markup()

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    کیبرد انصراف
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="🔙 انصراف", callback_data=CANCEL_CB))
    
    return builder.as_markup()

def get_confirm_amount_keyboard(amount: int) -> InlineKeyboardMarkup:
    """
    کیبرد تایید مبلغ شارژ
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text=f"✅ تایید مبلغ {amount:,} تومان", 
        callback_data=f"{CONFIRM_AMOUNT_PREFIX}{amount}"
    ))
    builder.add(InlineKeyboardButton(text="🔙 انصراف", callback_data=CANCEL_CB))
    
    # Grid layout (2x1)
    builder.adjust(1)
    
    return builder.as_markup() 