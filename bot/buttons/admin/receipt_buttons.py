"""
دکمه‌های مدیریت رسیدهای پرداخت برای ادمین
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

# Model import corrected - use receipt_log instead of receipt
from db.models.receipt_log import ReceiptLog

def get_admin_receipts_button() -> InlineKeyboardButton:
    """
    دکمه مدیریت رسیدها برای پنل ادمین
    
    Returns:
        InlineKeyboardButton: دکمه مدیریت رسیدها
    """
    return InlineKeyboardButton(
        text="🧾 رسیدهای در انتظار", 
        callback_data="admin:receipt:pending"
    )

def get_receipt_list_keyboard(receipts: Optional[List[ReceiptLog]] = None, page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد نمایش لیست رسیدها با دکمه‌های مدیریت
    
    Args:
        receipts (List[ReceiptLog], optional): لیست رسیدها
        page (int): شماره صفحه فعلی
        total_pages (int): تعداد کل صفحات
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت رسیدها
    """
    builder = InlineKeyboardBuilder()
    
    # اگر لیست رسیدها ارائه شده است
    if receipts:
        # برای هر رسید یک دکمه مدیریت اضافه می‌کنیم
        for receipt in receipts:
            # نمایش اطلاعات رسید در دکمه
            status_emoji = "✅" if receipt.is_approved else "⏳" if receipt.is_pending else "❌"
            button_text = f"{status_emoji} رسید #{receipt.id} - {receipt.amount:,} تومان"
            
            builder.button(
                text=button_text,
                callback_data=f"admin:receipt:manage:{receipt.id}"
            )
    
    # دکمه‌های پیمایش صفحات
    if total_pages > 1:
        nav_buttons = []
        
        # دکمه صفحه قبل
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ صفحه قبل",
                callback_data=f"admin:receipt:page:{page-1}"
            ))
        
        # نمایش شماره صفحه فعلی
        nav_buttons.append(InlineKeyboardButton(
            text=f"📄 {page} از {total_pages}",
            callback_data="admin:receipt:current_page"
        ))
        
        # دکمه صفحه بعد
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text="▶️ صفحه بعد",
                callback_data=f"admin:receipt:page:{page+1}"
            ))
            
        # اضافه کردن دکمه‌های پیمایش به کیبورد
        for button in nav_buttons:
            builder.add(button)
    
    # دکمه‌های فیلتر
    builder.button(
        text="🟢 رسیدهای تایید شده",
        callback_data="admin:receipt:filter:approved"
    )
    builder.button(
        text="🟡 رسیدهای در انتظار",
        callback_data="admin:receipt:filter:pending"
    )
    builder.button(
        text="🔴 رسیدهای رد شده",
        callback_data="admin:receipt:filter:rejected"
    )
    builder.button(
        text="🔄 همه رسیدها",
        callback_data="admin:receipt:filter:all"
    )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به پنل ادمین",
        callback_data="admin:panel"
    )
    
    # تنظیم چیدمان
    if receipts:
        # یک دکمه در هر ردیف برای رسیدها
        # دو یا سه دکمه در یک ردیف برای دکمه‌های پیمایش
        # دو دکمه در هر ردیف برای فیلترها
        # یک دکمه در ردیف آخر برای بازگشت
        builder.adjust(1, min(3, total_pages*2-1), 2, 2, 1)
    else:
        # بدون رسید، فقط نمایش دکمه‌های فیلتر و بازگشت
        builder.adjust(2, 2, 1)
    
    return builder.as_markup()

def get_receipt_manage_buttons(receipt_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های مدیریت برای یک رسید خاص
    
    Args:
        receipt_id (int): شناسه رسید مورد نظر
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت رسید
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های اصلی مدیریت
    builder.button(
        text="✅ تایید رسید",
        callback_data=f"admin:receipt:approve:{receipt_id}"
    )
    builder.button(
        text="❌ رد رسید",
        callback_data=f"admin:receipt:reject:{receipt_id}"
    )
    builder.button(
        text="👤 اطلاعات کاربر",
        callback_data=f"admin:receipt:user_info:{receipt_id}"
    )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به لیست رسیدها",
        callback_data="admin:receipt:list"
    )
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف، آخرین دکمه در یک ردیف جداگانه
    builder.adjust(2, 1, 1)
    
    return builder.as_markup() 