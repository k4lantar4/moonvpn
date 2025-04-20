"""
دکمه‌های inline مربوط به پلن‌ها
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.models.plan import Plan


def get_plans_keyboard(plans: List[Plan]) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های انتخاب پلن به صورت InlineKeyboardMarkup
    """
    keyboard = []
    
    for plan in plans:
        text = f"{plan.name} - {plan.traffic} گیگابایت - {plan.duration_days} روز - {plan.price:,} تومان"
        callback_data = f"select_plan:{plan.id}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    
    # دکمه بازگشت در پایین
    keyboard.append([InlineKeyboardButton(text="🔙 بازگشت به منو اصلی", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_plan_details_keyboard(plan_id: int) -> InlineKeyboardMarkup:
    """
    دکمه‌های مرتبط با جزئیات پلن
    """
    keyboard = [
        [InlineKeyboardButton(text="✅ تأیید و ادامه خرید", callback_data=f"confirm_plan:{plan_id}")],
        [InlineKeyboardButton(text="🔙 بازگشت به لیست پلن‌ها", callback_data="back_to_plans")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
