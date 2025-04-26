"""
دکمه‌های مربوط به مدیریت حساب‌ها و اشتراک‌ها
"""

import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional
from db.models.client_account import ClientAccount

logger = logging.getLogger(__name__)

# شناسه callback برای نمایش اشتراک‌های من
MY_ACCOUNTS_CB = "accounts:my"

def get_account_details_keyboard(account_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مدیریت جزئیات اکانت
    
    Args:
        account_id (int): شناسه اکانت در دیتابیس
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های اصلی
    builder.button(text="🔄 تمدید اشتراک", callback_data=f"account:renew:{account_id}")
    builder.button(text="📊 آمار مصرف", callback_data=f"account:stats:{account_id}")
    builder.button(text="📝 تغییر نام", callback_data=f"account:rename:{account_id}")
    builder.button(text="🔙 برگشت به لیست اکانت‌ها", callback_data=MY_ACCOUNTS_CB)
    
    # تنظیم چیدمان: 2 دکمه در هر ردیف، دکمه بازگشت در ردیف آخر
    builder.adjust(2, 2, 1)
    
    return builder.as_markup()

def get_accounts_list_keyboard(accounts: List[ClientAccount]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد لیست اکانت‌های کاربر
    
    Args:
        accounts (List[ClientAccount]): لیست آبجکت‌های اکانت‌های کاربر
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد لیست اکانت‌ها. تعداد اکانت‌ها: {len(accounts)}. (Building accounts list keyboard. Number of accounts: {len(accounts)}.)")
    
    # اضافه کردن دکمه برای هر اکانت
    for account in accounts:
        # نمایش نام اکانت یا ایمیل
        display_name = account.email or f"اکانت #{account.id}"
        builder.button(
            text=f"👤 {display_name}",
            callback_data=f"account:details:{account.id}"
        )
    
    # دکمه برگشت به منوی اصلی
    builder.button(text="🏠 منوی اصلی", callback_data="start")
    
    # تنظیم چیدمان: یک دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()

# TODO: Add other account related buttons later (e.g., view details, renew) 