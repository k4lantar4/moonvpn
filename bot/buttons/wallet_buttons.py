"""
کیبردهای Inline مربوط به کیف پول کاربران
"""

import logging
from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)

# شناسه‌های callback برای دکمه‌های کیف پول
WALLET_MENU_CB = "wallet:menu"
TOPUP_CB = "wallet:topup"
CANCEL_CB = "wallet:cancel"
CONFIRM_AMOUNT_PREFIX = "wallet:confirm_amount:"


def get_wallet_keyboard() -> InlineKeyboardMarkup:
    """
    کیبرد اصلی برای کیف پول
    
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت کیف پول
    """
    builder = InlineKeyboardBuilder()
    logger.debug("ساخت کیبورد اصلی کیف پول (Building main wallet keyboard)")
    
    builder.button(text="💰 افزایش موجودی", callback_data=TOPUP_CB)
    builder.button(text="📊 تاریخچه تراکنش‌ها", callback_data="wallet:history")
    builder.button(text="🏠 بازگشت به منوی اصلی", callback_data="start")
    
    # تنظیم چیدمان: یک دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    کیبرد انصراف
    
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه انصراف
    """
    builder = InlineKeyboardBuilder()
    logger.debug("ساخت کیبورد انصراف (Building cancel keyboard)")
    
    builder.button(text="🔙 انصراف", callback_data=CANCEL_CB)
    
    return builder.as_markup()


def get_confirm_amount_keyboard(amount: int) -> InlineKeyboardMarkup:
    """
    کیبرد تایید مبلغ شارژ
    
    Args:
        amount (int): مبلغ شارژ به تومان
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های تایید و انصراف
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد تایید مبلغ {amount:,} تومان (Building confirm amount keyboard for {amount:,} tomans)")
    
    builder.button(
        text=f"✅ تایید مبلغ {amount:,} تومان", 
        callback_data=f"{CONFIRM_AMOUNT_PREFIX}{amount}"
    )
    builder.button(text="🔙 انصراف", callback_data=CANCEL_CB)
    
    # تنظیم چیدمان: یک دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()


def get_payment_methods_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    """
    کیبورد انتخاب روش پرداخت
    
    Args:
        transaction_id (int): شناسه تراکنش
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های روش‌های پرداخت
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد روش‌های پرداخت برای تراکنش {transaction_id} (Building payment methods keyboard for transaction {transaction_id})")
    
    builder.button(text="💳 پرداخت آنلاین", callback_data=f"pay:online:{transaction_id}")
    builder.button(text="💸 کارت به کارت", callback_data=f"pay:card:{transaction_id}")
    builder.button(text="🔙 انصراف", callback_data=CANCEL_CB)
    
    # تنظیم چیدمان: یک دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup() 