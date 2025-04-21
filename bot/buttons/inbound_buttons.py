"""
دکمه‌های مربوط به انتخاب inbound در فرایند خرید
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.models.panel import Panel
from db.models.inbound import Inbound


def get_panel_locations_keyboard(panels: List[Panel]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب لوکیشن پنل‌ها
    """
    keyboard = []
    
    # دکمه‌های انتخاب لوکیشن
    for panel in panels:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{panel.flag_emoji} {panel.location_name}",
                callback_data=f"select_location:{panel.id}"
            )
        ])
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 بازگشت به لیست پلن‌ها",
            callback_data="back_to_plans"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_inbounds_keyboard(inbounds: List[Inbound], panel_id: int, plan_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب inbound
    """
    keyboard = []
    
    # دکمه‌های انتخاب inbound
    for inbound in inbounds:
        # نمایش تعداد کاربران در صورت وجود محدودیت
        client_info = ""
        if inbound.max_clients:
            client_info = f" ({inbound.client_count}/{inbound.max_clients})"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{inbound.protocol.upper()}@{inbound.port}{client_info}",
                callback_data=f"select_inbound:{plan_id}:{panel_id}:{inbound.id}"
            )
        ])
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 بازگشت به لیست لوکیشن‌ها",
            callback_data=f"back_to_locations:{plan_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 