"""
دکمه‌های مربوط به عملیات مدیریت پنل
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_panel_management_keyboard(panel_id: int) -> InlineKeyboardMarkup:
    """ساخت کیبورد عملیات مدیریت پنل"""
    # ردیف اول: لیست اینباندها و تست اتصال
    row1 = [
        InlineKeyboardButton(text="📋 لیست اینباندها", callback_data=f"panel_inbounds:{panel_id}"),
        InlineKeyboardButton(text="📶 تست اتصال", callback_data=f"panel:test_connection:{panel_id}")
    ]
    # ردیف دوم: ویرایش تنظیمات و حذف
    row2 = [
        InlineKeyboardButton(text="⚙️ ویرایش", callback_data=f"panel_edit:{panel_id}"),
        InlineKeyboardButton(text="❌ حذف", callback_data=f"panel_disable:{panel_id}")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2]) 