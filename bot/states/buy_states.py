"""
کلاس‌های state مربوط به فرآیند خرید اشتراک
"""

from aiogram.fsm.state import State, StatesGroup


class BuyState(StatesGroup):
    """کلاس state برای فرآیند خرید اشتراک"""
    select_plan = State()  # انتخاب پلن
    select_location = State()  # انتخاب لوکیشن
    select_inbound = State()  # انتخاب پروتکل
    confirm_purchase = State()  # تایید نهایی
    payment = State()  # پرداخت 