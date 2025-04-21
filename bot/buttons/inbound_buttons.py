"""
دکمه‌های inline مربوط به انتخاب inbound
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.models.inbound import Inbound
from db.models.panel import Panel


def get_panel_locations_keyboard(panels: List[Panel]) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های انتخاب لوکیشن سرور به صورت InlineKeyboardMarkup
    
    Args:
        panels: لیست پنل‌های فعال
    
    Returns:
        کیبورد اینلاین با دکمه‌های لوکیشن
    """
    keyboard = []
    
    for panel in panels:
        text = f"{panel.flag_emoji} {panel.location}"
        callback_data = f"select_location:{panel.id}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    
    # دکمه بازگشت در پایین
    keyboard.append([InlineKeyboardButton(text="🔙 بازگشت به لیست پلن‌ها", callback_data="back_to_plans")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_inbounds_keyboard(inbounds: List[Inbound], panel_id: int, plan_id: int) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های انتخاب inbound به صورت InlineKeyboardMarkup
    
    Args:
        inbounds: لیست inbound‌های فعال
        panel_id: شناسه پنل انتخاب شده
        plan_id: شناسه پلن انتخاب شده
    
    Returns:
        کیبورد اینلاین با دکمه‌های inbound
    """
    keyboard = []
    
    for inbound in inbounds:
        # نمایش پروتکل و برچسب
        text = f"{inbound.protocol.upper()} - {inbound.tag}"
        callback_data = f"select_inbound:{plan_id}:{panel_id}:{inbound.id}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    
    # دکمه بازگشت در پایین
    keyboard.append([InlineKeyboardButton(text="🔙 بازگشت به لوکیشن‌ها", callback_data=f"back_to_locations:{plan_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 