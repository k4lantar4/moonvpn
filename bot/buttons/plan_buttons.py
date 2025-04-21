"""
دکمه‌های مربوط به انتخاب پلن
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.plan import Plan

def get_plans_keyboard(plans: list[Plan]) -> InlineKeyboardMarkup:
    """ساخت کیبورد انتخاب پلن"""
    
    builder = InlineKeyboardBuilder()
    
    for plan in plans:
        # نمایش قیمت به تومان
        price_toman = f"{plan.price:,}"
        
        builder.button(
            text=f"📦 {plan.name} - {price_toman} تومان",
            callback_data=f"select_plan:{plan.id}"
        )
    
    # چینش دکمه‌ها به صورت عمودی
    builder.adjust(1)
    
    return builder.as_markup()


def get_plan_details_keyboard(plan_id: int) -> InlineKeyboardMarkup:
    """
    دکمه‌های مرتبط با جزئیات پلن
    """
    keyboard = [
        [InlineKeyboardButton(text="✅ تأیید و ادامه خرید", callback_data=f"confirm_plan:{plan_id}")],
        [InlineKeyboardButton(text="🔙 بازگشت به لیست پلن‌ها", callback_data="back_to_plans")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
