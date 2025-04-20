"""
خوشامدگویی و ثبت‌نام اولیه کاربران
"""

from aiogram import types, Dispatcher, F
from aiogram.filters import Command
from sqlalchemy.orm import Session, sessionmaker

from bot.keyboards import get_main_keyboard
from core.services.user_service import UserService

# متغیر سراسری برای دسترسی به session_maker
_session_maker = None

async def start_handler(message: types.Message):
    """
    هندلر دستور /start
    ثبت کاربر در دیتابیس و نمایش کیبورد اصلی
    """
    print(f"start_handler called with message from user {message.from_user.id}")
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # ایجاد سشن دیتابیس
    print("Creating database session")
    session = _session_maker()
    
    try:
        # ثبت کاربر در دیتابیس (یا بازیابی اطلاعات اگر از قبل ثبت شده)
        print("Initializing UserService")
        user_service = UserService(session)
        print(f"Registering user with ID: {user_id}, username: {username}")
        user = user_service.register_user(user_id, username)
        print(f"User registered: {user}")
        
        # پیام خوشامدگویی
        welcome_message = (
            f"سلام {first_name} عزیز! 👋\n\n"
            f"به بات MoonVPN خوش آمدید! 🌙✨\n\n"
            f"این بات به شما کمک می‌کند تا:\n"
            f"- سرویس VPN با کیفیت خریداری کنید 🚀\n"
            f"- سرویس‌های خود را به راحتی مدیریت کنید 🔑\n"
            f"- شارژ حساب و پرداخت امن انجام دهید 💰\n\n"
            f"لطفاً از منوی زیر یک گزینه را انتخاب کنید:"
        )
        
        # ارسال پیام با کیبورد اصلی
        print("Sending welcome message with keyboard")
        await message.answer(welcome_message, reply_markup=get_main_keyboard())
        print("Message sent successfully")
        
    except Exception as e:
        # لاگ خطا و ارسال پیام خطا
        print(f"Error in start command: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        await message.answer("متأسفانه خطایی در سیستم رخ داده است. لطفاً بعداً تلاش کنید یا با پشتیبانی تماس بگیرید.")
    
    finally:
        # بستن سشن دیتابیس در نهایت
        print("Closing database session")
        session.close()


def register_start_command(dp: Dispatcher, session_maker: sessionmaker):
    """
    ثبت هندلر دستور /start در دیسپچر ربات
    """
    global _session_maker
    _session_maker = session_maker
    
    dp.message.register(
        start_handler,
        Command("start")
    )
