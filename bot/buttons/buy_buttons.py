"""
دکمه‌های مربوط به فرآیند خرید اشتراک
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.models import Plan, Panel, Inbound


def get_plans_keyboard() -> InlineKeyboardMarkup:
    """ساخت کیبورد انتخاب پلن"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 بروزرسانی لیست", callback_data="refresh_plans")
    return builder.as_markup()


def get_locations_keyboard(panels: list[Panel]) -> InlineKeyboardMarkup:
    """ساخت کیبورد انتخاب لوکیشن"""
    builder = InlineKeyboardBuilder()
    
    # گروه‌بندی پنل‌ها بر اساس لوکیشن
    locations = {}
    for panel in panels:
        if panel.location not in locations:
            locations[panel.location] = panel.flag_emoji
            
    # اضافه کردن دکمه برای هر لوکیشن
    for location, emoji in locations.items():
        builder.button(
            text=f"{emoji} {location}",
            callback_data=f"select_location:{location}"
        )
    
    # چینش دکمه‌ها در دو ستون
    builder.adjust(2)
    
    # دکمه بازگشت
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت به لیست پلن‌ها",
        callback_data="back_to_plans"
    ))
    
    return builder.as_markup()


def get_inbounds_keyboard(inbounds: list[Inbound], panel_id: int) -> InlineKeyboardMarkup:
    """ساخت کیبورد انتخاب اینباند"""
    builder = InlineKeyboardBuilder()
    
    # اضافه کردن دکمه برای هر اینباند
    for inbound in inbounds:
        builder.button(
            text=f"📡 {inbound.remark}",
            callback_data=f"select_inbound:{panel_id}:{inbound.id}"
        )
    
    # چینش دکمه‌ها در یک ستون
    builder.adjust(1)
    
    # دکمه بازگشت
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت به انتخاب لوکیشن",
        callback_data="back_to_locations"
    ))
    
    return builder.as_markup()


def get_confirm_purchase_keyboard(plan_id: int, panel_id: int, inbound_id: int) -> InlineKeyboardMarkup:
    """ساخت کیبورد تایید نهایی خرید"""
    builder = InlineKeyboardBuilder()
    
    # دکمه تایید
    builder.button(
        text="✅ تایید و پرداخت",
        callback_data=f"confirm_purchase:{plan_id}:{panel_id}:{inbound_id}"
    )
    
    # دکمه بازگشت
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت به انتخاب پروتکل",
        callback_data="back_to_inbounds"
    ))
    
    return builder.as_markup()


def get_payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    """ساخت کیبورد پرداخت"""
    builder = InlineKeyboardBuilder()
    
    # دکمه پرداخت
    builder.button(
        text="💳 پرداخت آنلاین",
        callback_data=f"pay:{payment_id}"
    )
    
    # دکمه کارت به کارت
    builder.button(
        text="💸 کارت به کارت",
        callback_data=f"card_payment:{payment_id}"
    )
    
    # چینش دکمه‌ها در یک ستون
    builder.adjust(1)
    
    # دکمه بازگشت
    builder.row(InlineKeyboardButton(
        text="🔙 انصراف",
        callback_data="cancel_payment"
    ))
    
    return builder.as_markup() 