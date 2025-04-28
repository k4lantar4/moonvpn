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


# Added RegisterPanelStates for handling new panel registration
class RegisterPanelStates(StatesGroup):
    waiting_for_panel_url = State()
    waiting_for_username = State()
    waiting_for_password = State()
    waiting_for_location_name = State()


class BankCardStates(StatesGroup):
    """
    وضعیت‌های مربوط به مدیریت کارت‌های بانکی
    """
    # افزودن کارت جدید
    add_card_number = State()        # وارد کردن شماره کارت
    add_holder_name = State()        # وارد کردن نام دارنده کارت
    add_bank_name = State()          # وارد کردن نام بانک
    add_rotation_policy = State()    # انتخاب سیاست چرخش کارت
    add_rotation_interval = State()  # وارد کردن بازه زمانی چرخش (اگر سیاست interval باشد)
    add_confirmation = State()       # تایید نهایی
    
    # ویرایش کارت موجود
    edit_select_field = State()       # انتخاب فیلد برای ویرایش
    edit_card_number = State()        # ویرایش شماره کارت
    edit_holder_name = State()        # ویرایش نام دارنده کارت
    edit_bank_name = State()          # ویرایش نام بانک
    edit_rotation_policy = State()    # ویرایش سیاست چرخش
    edit_rotation_interval = State()  # ویرایش بازه زمانی چرخش