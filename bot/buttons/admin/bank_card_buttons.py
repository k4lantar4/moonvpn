"""
دکمه‌های مدیریت کارت‌های بانکی برای ادمین
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

from db.models.bank_card import BankCard, RotationPolicy

def get_bank_cards_keyboard(cards: List[BankCard]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد نمایش لیست کارت‌های بانکی با دکمه‌های مدیریت
    
    Args:
        cards (List[BankCard]): لیست کارت‌های بانکی دریافتی از BankCardService
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت کارت بانکی
    """
    builder = InlineKeyboardBuilder()
    
    # اگر هیچ کارتی وجود نداشت
    if not cards:
        builder.button(
            text="➕ ثبت کارت جدید",
            callback_data="admin:bank_card:add"
        )
        builder.button(
            text="🔙 بازگشت به پنل ادمین",
            callback_data="admin:panel"
        )
        builder.adjust(1)  # یک دکمه در هر ردیف
        return builder.as_markup()
        
    # برای هر کارت بانکی یک دکمه مدیریت اضافه می‌کنیم
    for card in cards:
        # نمایش وضعیت کارت با ایموجی مناسب
        status_emoji = "✅" if card.is_active else "❌"
        
        # متن دکمه شامل اطلاعات مختصر کارت
        # نمایش 4 رقم آخر کارت برای امنیت
        masked_card_number = f"****{card.card_number[-4:]}"
        button_text = f"💳 {card.bank_name} - {masked_card_number} {status_emoji}"
        
        # ساختار callback_data استاندارد
        callback_data = f"admin:bank_card:manage:{card.id}"
        
        builder.button(
            text=button_text,
            callback_data=callback_data
        )
    
    # دکمه‌های اضافی
    builder.button(
        text="➕ ثبت کارت جدید",
        callback_data="admin:bank_card:add"
    )
    builder.button(
        text="🔙 بازگشت به پنل ادمین",
        callback_data="admin:panel"
    )
    
    # تنظیم چیدمان - ۱ دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()

def get_bank_card_manage_buttons(card_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های مدیریت برای یک کارت بانکی خاص
    
    Args:
        card_id (int): شناسه کارت بانکی مورد نظر
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت کارت بانکی
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های اصلی مدیریت
    builder.button(
        text="⚙️ ویرایش اطلاعات",
        callback_data=f"admin:bank_card:edit:{card_id}"
    )
    builder.button(
        text="🔀 تغییر وضعیت فعال/غیرفعال",
        callback_data=f"admin:bank_card:toggle:{card_id}"
    )
    builder.button(
        text="❌ حذف کارت",
        callback_data=f"admin:bank_card:delete:{card_id}"
    )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به لیست کارت‌ها",
        callback_data="admin:bank_card:list"
    )
    
    # تنظیم چیدمان - ۱ دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()

def get_bank_card_rotation_policy_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب سیاست چرخش کارت بانکی
    
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با گزینه‌های سیاست چرخش
    """
    builder = InlineKeyboardBuilder()
    
    for policy in RotationPolicy:
        policy_desc = ""
        if policy == RotationPolicy.MANUAL:
            policy_desc = "دستی"
        elif policy == RotationPolicy.INTERVAL:
            policy_desc = "زمانی (متناوب)"
        elif policy == RotationPolicy.LOAD_BALANCE:
            policy_desc = "توزیع بار"
        
        builder.button(
            text=policy_desc,
            callback_data=f"admin:bank_card:policy:{policy.value}"
        )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 انصراف",
        callback_data="admin:bank_card:add:cancel"
    )
    
    # تنظیم چیدمان - ۱ دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()

def get_confirm_delete_bank_card_keyboard(card_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد تایید حذف کارت بانکی
    
    Args:
        card_id (int): شناسه کارت بانکی
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های تایید/لغو
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="✅ بله، حذف شود",
        callback_data=f"admin:bank_card:delete:confirm:{card_id}"
    )
    builder.button(
        text="❌ خیر، انصراف",
        callback_data=f"admin:bank_card:manage:{card_id}"
    )
    
    # تنظیم چیدمان - ۱ دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup() 