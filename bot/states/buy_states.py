"""
وضعیت‌های مربوط به فرایند خرید اشتراک
"""

from aiogram.fsm.state import State, StatesGroup


class BuyState(StatesGroup):
    """
    وضعیت‌های مختلف در فرایند خرید
    """
    select_plan = State()  # انتخاب پلن
    select_location = State()  # انتخاب لوکیشن
    select_inbound = State()  # انتخاب پروتکل
    confirm_purchase = State()  # تایید نهایی خرید
    payment = State()  # پرداخت 