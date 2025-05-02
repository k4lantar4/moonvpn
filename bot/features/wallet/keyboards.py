"""
کیبوردهای مربوط به بخش کیف پول
"""

import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)

# Callback data constants for Wallet feature
WALLET_MENU_CB = "wallet:menu"
WALLET_TOPUP_CB = "wallet:topup"
WALLET_HISTORY_CB = "wallet:history"
WALLET_CONFIRM_AMOUNT_PREFIX = "wallet:confirm_amount:"
WALLET_CANCEL_TOPUP_CB = "wallet:cancel_topup"
WALLET_BACK_TO_MAIN_CB = "start" # یا هر callback دیگری برای بازگشت به منوی اصلی

PAYMENT_ONLINE_PREFIX = "pay:online:"
PAYMENT_CARD_PREFIX = "pay:card:"

def get_wallet_menu_keyboard() -> InlineKeyboardMarkup:
    """ایجاد کیبورد منوی اصلی کیف پول."""
    builder = InlineKeyboardBuilder()
    logger.debug("Building main wallet menu keyboard")
    builder.button(text="💰 افزایش موجودی", callback_data=WALLET_TOPUP_CB)
    builder.button(text="📊 تاریخچه تراکنش‌ها", callback_data=WALLET_HISTORY_CB)
    builder.button(text="🏠 بازگشت به منوی اصلی", callback_data=WALLET_BACK_TO_MAIN_CB)
    builder.adjust(1)
    return builder.as_markup()

def get_cancel_topup_keyboard() -> InlineKeyboardMarkup:
    """ایجاد کیبورد انصراف از فرآیند شارژ."""
    builder = InlineKeyboardBuilder()
    logger.debug("Building cancel topup keyboard")
    builder.button(text="🔙 انصراف و بازگشت به کیف پول", callback_data=WALLET_MENU_CB)
    return builder.as_markup()

def get_confirm_amount_keyboard(amount: int) -> InlineKeyboardMarkup:
    """
    ایجاد کیبورد تایید مبلغ شارژ.
    Args:
        amount: مبلغ شارژ به تومان.
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"Building confirm amount keyboard for {amount:,} Toman")
    builder.button(
        text=f"✅ تایید مبلغ {amount:,} تومان", 
        callback_data=f"{WALLET_CONFIRM_AMOUNT_PREFIX}{amount}"
    )
    # استفاده از callback انصراف که به منوی کیف پول برمی‌گردد
    builder.button(text="🔙 انصراف و بازگشت به کیف پول", callback_data=WALLET_MENU_CB) 
    builder.adjust(1)
    return builder.as_markup()

def get_payment_methods_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    """
    ایجاد کیبورد انتخاب روش پرداخت برای یک تراکنش.
    Args:
        transaction_id: شناسه تراکنش.
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"Building payment methods keyboard for transaction {transaction_id}")
    builder.button(text="💳 پرداخت آنلاین", callback_data=f"{PAYMENT_ONLINE_PREFIX}{transaction_id}")
    builder.button(text="💸 کارت به کارت / رسید", callback_data=f"{PAYMENT_CARD_PREFIX}{transaction_id}")
    # TODO: افزودن دکمه انصراف که شاید تراکنش را کنسل کند؟ یا فقط به منوی کیف پول برگردد؟
    builder.button(text="🔙 بازگشت به کیف پول", callback_data=WALLET_MENU_CB)
    builder.adjust(1)
    return builder.as_markup()

# Note: Functions like get_withdrawal_keyboard from the old wallet_keyboard.py 
# seem unused based on the callbacks and commands files read so far.
# They can be added later if needed. 