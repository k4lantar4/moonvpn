"""
دکمه‌های مربوط به عملیات مدیریت پنل
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_panel_management_keyboard(panel_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد عملیات مدیریت پنل
    
    Args:
        panel_id (int): شناسه پنل مورد نظر
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت پنل
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های اصلی مدیریت
    builder.button(
        text="📋 لیست اینباندها",
        callback_data=f"panel_inbounds:{panel_id}"
    )
    builder.button(
        text="📶 تست اتصال",
        callback_data=f"panel:test_connection:{panel_id}"
    )
    builder.button(
        text="⚙️ ویرایش",
        callback_data=f"panel_edit:{panel_id}"
    )
    builder.button(
        text="🔄 همگام‌سازی",
        callback_data=f"panel:sync:{panel_id}"
    )
    builder.button(
        text="🔀 تغییر وضعیت",
        callback_data=f"panel_toggle_status:{panel_id}"
    )
    builder.button(
        text="❌ غیرفعال‌سازی",
        callback_data=f"panel_disable:{panel_id}"
    )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به لیست پنل‌ها",
        callback_data="manage_panels"
    )
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف، آخرین دکمه در یک ردیف جداگانه
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup() 