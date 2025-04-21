"""
دکمه‌های مربوط به انتخاب inbound در فرایند خرید
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.models.panel import Panel
from db.models.inbound import Inbound


def get_panel_locations_keyboard(panels: List[Panel]) -> InlineKeyboardMarkup:
    """
    ایجاد کیبورد برای انتخاب لوکیشن پنل‌ها
    
    Args:
        panels: لیست پنل‌های فعال
        
    Returns:
        کیبورد اینلاین با دکمه‌های لوکیشن
    """
    buttons = []
    
    # ایجاد دکمه برای هر پنل
    for panel in panels:
        buttons.append([
            InlineKeyboardButton(
                text=f"{panel.flag_emoji} {panel.location}",
                callback_data=f"select_location:{panel.id}"
            )
        ])
    
    # دکمه بازگشت
    buttons.append([
        InlineKeyboardButton(
            text="🔙 بازگشت به لیست پلن‌ها",
            callback_data="back_to_plans"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_inbounds_keyboard(inbounds: List[Inbound], panel_id: int, plan_id: int) -> InlineKeyboardMarkup:
    """
    ایجاد کیبورد برای انتخاب inbound
    
    Args:
        inbounds: لیست inbound‌های فعال
        panel_id: شناسه پنل انتخاب شده
        plan_id: شناسه پلن انتخاب شده
        
    Returns:
        کیبورد اینلاین با دکمه‌های inbound
    """
    buttons = []
    
    # ایجاد دکمه برای هر inbound
    for inbound in inbounds:
        # نمایش پروتکل و پورت
        button_text = f"🔌 {inbound.protocol.upper()} - پورت {inbound.port}"
        
        # اضافه کردن تعداد کلاینت‌ها اگر محدودیت وجود دارد
        if inbound.max_clients > 0:
            button_text += f" ({len(inbound.client_accounts)}/{inbound.max_clients})"
            
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"select_inbound:{plan_id}:{panel_id}:{inbound.id}"
            )
        ])
    
    # دکمه بازگشت
    buttons.append([
        InlineKeyboardButton(
            text="🔙 بازگشت به انتخاب لوکیشن",
            callback_data=f"back_to_locations:{plan_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 