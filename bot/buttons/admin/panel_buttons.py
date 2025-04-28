"""
دکمه‌های مدیریت پنل‌ها برای ادمین
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

from db.models.panel import Panel, PanelStatus

def get_panel_list_keyboard(panels: List[Panel]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد نمایش لیست پنل‌ها با دکمه‌های مدیریت
    
    Args:
        panels (List[Panel]): لیست پنل‌های دریافتی از PanelService
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت پنل
    """
    builder = InlineKeyboardBuilder()
    
    # اگر هیچ پنلی وجود نداشت
    if not panels:
        builder.button(
            text="➕ ثبت پنل جدید",
            callback_data="admin:panel:register"
        )
        builder.button(
            text="🔙 بازگشت به پنل ادمین",
            callback_data="admin:panel"
        )
        builder.adjust(1)  # یک دکمه در هر ردیف
        return builder.as_markup()
        
    # برای هر پنل یک دکمه مدیریت اضافه می‌کنیم
    for panel in panels:
        # نمایش وضعیت پنل با ایموجی مناسب
        status_emoji = (
            "✅" if panel.status == PanelStatus.ACTIVE 
            else "⚠️" if panel.status == PanelStatus.INACTIVE 
            else "❌"
        )
        
        # متن دکمه شامل اطلاعات مختصر پنل
        button_text = f"📟 {panel.flag_emoji} {panel.location_name} {status_emoji}"
        
        # ساختار callback_data استاندارد
        callback_data = f"admin:panel:manage:{panel.id}"
        
        builder.button(
            text=button_text,
            callback_data=callback_data
        )
    
    # دکمه‌های اضافی
    builder.button(
        text="➕ ثبت پنل جدید",
        callback_data="admin:panel:register"
    )
    builder.button(
        text="🔄 همگام‌سازی همه پنل‌ها",
        callback_data="admin:panel:sync_all"
    )
    builder.button(
        text="🔙 بازگشت به پنل ادمین",
        callback_data="admin:panel"
    )
    
    # تنظیم چیدمان - ۱ دکمه در هر ردیف برای پنل‌ها و دکمه‌های اضافی
    builder.adjust(1)
    
    return builder.as_markup()

def get_panel_manage_buttons(panel_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های مدیریت برای یک پنل خاص
    
    Args:
        panel_id (int): شناسه پنل مورد نظر
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت پنل
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های اصلی مدیریت
    builder.button(
        text="📋 لیست اینباندها",
        callback_data=f"admin:panel:inbounds:{panel_id}"
    )
    builder.button(
        text="📶 تست اتصال",
        callback_data=f"admin:panel:test_connection:{panel_id}"
    )
    builder.button(
        text="⚙️ ویرایش",
        callback_data=f"admin:panel:edit:{panel_id}"
    )
    builder.button(
        text="🔄 همگام‌سازی",
        callback_data=f"admin:panel:sync:{panel_id}"
    )
    builder.button(
        text="🔀 تغییر وضعیت",
        callback_data=f"admin:panel:toggle_status:{panel_id}"
    )
    builder.button(
        text="❌ غیرفعال‌سازی",
        callback_data=f"admin:panel:disable:{panel_id}"
    )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به لیست پنل‌ها",
        callback_data="admin:panel:list"
    )
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف، آخرین دکمه در یک ردیف جداگانه
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup() 