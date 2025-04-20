"""
دکمه‌های inline مربوط به خرید و انتخاب سرویس‌ها
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.models.panel import Panel
from db.models.inbound import Inbound


def get_locations_keyboard(panels: List[Panel]) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های انتخاب لوکیشن سرور به صورت InlineKeyboardMarkup
    """
    keyboard = []
    
    for panel in panels:
        text = f"{panel.flag_emoji} {panel.location}"
        callback_data = f"select_location:{panel.id}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    
    # دکمه بازگشت در پایین
    keyboard.append([InlineKeyboardButton(text="🔙 بازگشت به منو قبلی", callback_data="back_to_plans")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_inbounds_keyboard(inbounds: List[Inbound], plan_id: int) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های انتخاب inbound به صورت InlineKeyboardMarkup
    """
    keyboard = []
    
    for inbound in inbounds:
        text = f"{inbound.protocol.upper()} - {inbound.tag}"
        callback_data = f"select_inbound:{plan_id}:{inbound.id}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    
    # دکمه بازگشت در پایین
    keyboard.append([InlineKeyboardButton(text="🔙 بازگشت به لوکیشن‌ها", callback_data="back_to_locations")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_purchase_keyboard(plan_id: int, inbound_id: int) -> InlineKeyboardMarkup:
    """
    دکمه‌های تأیید نهایی خرید
    """
    keyboard = [
        [InlineKeyboardButton(text="✅ تأیید و دریافت کانفیگ", callback_data=f"confirm_purchase:{plan_id}:{inbound_id}")],
        [InlineKeyboardButton(text="🔙 بازگشت به انتخاب پروتکل", callback_data=f"back_to_inbounds:{plan_id}")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 