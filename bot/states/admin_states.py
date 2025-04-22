"""
وضعیت‌های مربوط به عملیات مدیریتی
"""

from aiogram.fsm.state import State, StatesGroup


class AddPanel(StatesGroup):
    """
    وضعیت‌های مربوط به اضافه کردن پنل جدید
    """
    name = State()                # وارد کردن نام پنل
    location = State()            # وارد کردن موقعیت پنل
    flag_emoji = State()          # وارد کردن ایموجی پرچم کشور
    url = State()                 # وارد کردن آدرس پنل
    username = State()            # وارد کردن نام کاربری
    password = State()            # وارد کردن رمز عبور
    default_label = State()       # وارد کردن پیشوند نام اکانت پیش‌فرض
    confirmation = State()        # تایید نهایی


class AddInbound(StatesGroup):
    """
    وضعیت‌های مربوط به اضافه کردن اینباند جدید
    """
    select_panel = State()         # انتخاب پنل
    enter_protocol = State()       # انتخاب پروتکل
    enter_port = State()          # وارد کردن پورت
    enter_max_clients = State()    # وارد کردن حداکثر تعداد کاربر
    confirm = State()             # تایید نهایی 