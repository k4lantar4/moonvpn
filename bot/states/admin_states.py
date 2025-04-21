"""
وضعیت‌های مربوط به عملیات مدیریتی
"""

from aiogram.fsm.state import State, StatesGroup


class AddPanel(StatesGroup):
    """
    وضعیت‌های مربوط به اضافه کردن پنل جدید
    """
    enter_name = State()           # وارد کردن نام پنل
    enter_address = State()        # وارد کردن آدرس پنل
    enter_port = State()           # وارد کردن پورت پنل
    enter_username = State()       # وارد کردن نام کاربری
    enter_password = State()       # وارد کردن رمز عبور
    enter_location = State()       # وارد کردن لوکیشن
    enter_flag = State()          # وارد کردن ایموجی پرچم
    confirm = State()             # تایید نهایی


class AddInbound(StatesGroup):
    """
    وضعیت‌های مربوط به اضافه کردن اینباند جدید
    """
    select_panel = State()         # انتخاب پنل
    enter_protocol = State()       # انتخاب پروتکل
    enter_port = State()          # وارد کردن پورت
    enter_max_clients = State()    # وارد کردن حداکثر تعداد کاربر
    confirm = State()             # تایید نهایی 