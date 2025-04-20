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
    default_label = State()     # پیشوند نام اکانت پیش‌فرض
    confirmation = State()      # تایید نهایی 