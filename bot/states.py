"""
کلاس‌های FSM (Finite State Machine) برای مدیریت حالت‌های مختلف ربات
"""

from aiogram.fsm.state import State, StatesGroup


class AddPanel(StatesGroup):
    """مراحل اضافه کردن پنل جدید"""
    name = State()              # نام پنل
    location = State()          # لوکیشن (کشور)
    flag_emoji = State()        # ایموجی پرچم
    url = State()               # آدرس پنل
    username = State()          # نام کاربری پنل
    password = State()          # رمز عبور پنل
    default_label = State()     # پیشوند برچسب پیش‌فرض


class BuyState(StatesGroup):
    """مراحل خرید اشتراک"""
    select_plan = State()       # انتخاب پلن
    select_location = State()   # انتخاب لوکیشن
    select_inbound = State()    # انتخاب اینباند
    confirm_purchase = State()  # تایید نهایی خرید
    payment = State()           # پرداخت (در صورت کمبود موجودی)
    receipt = State()           # رسید پرداخت 