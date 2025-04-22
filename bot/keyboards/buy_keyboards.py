"""
کیبوردهای مربوط به فرآیند خرید اشتراک
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.plan import Plan
from db.models.panel import Panel
from db.models.inbound import Inbound


def get_plans_keyboard(plans: list[Plan]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب پلن
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های پلن‌ها
    for plan in plans:
        builder.button(
            text=f"{plan.name} - {plan.duration} روز - {plan.price:,} تومان",
            callback_data=f"plan:{plan.id}"
        )
    
    # دکمه بروزرسانی
    builder.button(
        text="🔄 بروزرسانی",
        callback_data="refresh_plans"
    )
    
    # چینش دکمه‌ها
    builder.adjust(1)
    
    return builder.as_markup()


def get_locations_keyboard(locations: list[Panel]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب لوکیشن
    """
    builder = InlineKeyboardBuilder()
    # دکمه‌های لوکیشن‌ها بر اساس پنل‌های فعال
    for panel in locations:
        builder.button(
            text=f"{panel.flag_emoji} {panel.location_name}",
            callback_data=f"select_location:{panel.id}"
        )
    # دکمه بازگشت به پلن‌ها
    builder.button(
        text="🔙 بازگشت به پلن‌ها",
        callback_data="back_to_plans"
    )
    # چینش دکمه‌ها
    builder.adjust(1)
    return builder.as_markup()


def get_inbounds_keyboard(inbounds: list[Inbound]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب پروتکل
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های پروتکل‌ها
    for inbound in inbounds:
        builder.button(
            text=f"{inbound.name}",
            callback_data=f"inbound:{inbound.id}"
        )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به لوکیشن‌ها",
        callback_data="back_to_locations"
    )
    
    # چینش دکمه‌ها
    builder.adjust(1)
    
    return builder.as_markup()


def get_confirm_purchase_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد تایید خرید
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="✅ تایید و پرداخت",
        callback_data="confirm_purchase"
    )
    
    builder.button(
        text="❌ انصراف",
        callback_data="cancel_purchase"
    )
    
    # چینش دکمه‌ها
    builder.adjust(1)
    
    return builder.as_markup()


def get_payment_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب روش پرداخت
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="🏦 درگاه بانکی",
        callback_data=f"pay:bank:{order_id}"
    )
    
    builder.button(
        text="💰 کیف پول",
        callback_data=f"pay:wallet:{order_id}"
    )
    
    builder.button(
        text="❌ انصراف",
        callback_data="cancel_purchase"
    )
    
    # چینش دکمه‌ها
    builder.adjust(1)
    
    return builder.as_markup() 