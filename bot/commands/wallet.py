"""
مدیریت کیف پول و پرداخت‌ها
"""

from decimal import Decimal
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session, sessionmaker

from bot.buttons.wallet_buttons import get_wallet_keyboard, get_confirm_amount_keyboard
from bot.callbacks.wallet_callbacks import WalletStates
from core.services.user_service import UserService
from core.services.payment_service import PaymentService
from db.models.transaction import TransactionType, TransactionStatus

# متغیر سراسری برای دسترسی به session_maker
_session_maker = None


async def wallet_command(message: types.Message):
    """
    هندلر دستور /wallet
    نمایش وضعیت کیف پول و دکمه افزایش موجودی
    """
    user_id = message.from_user.id
    
    # ایجاد سشن دیتابیس
    session = _session_maker()
    
    try:
        # دریافت اطلاعات کاربر
        user_service = UserService(session)
        payment_service = PaymentService(session)
        
        user = user_service.get_user_by_telegram_id(user_id)
        if not user:
            await message.answer("خطا در شناسایی کاربر. لطفاً ابتدا از دستور /start استفاده کنید.")
            return
        
        # نمایش وضعیت کیف پول
        balance = payment_service.get_user_balance(user_id)
        
        wallet_message = (
            f"💰 کیف پول شما\n\n"
            f"👤 کاربر: {user.username or 'بدون نام کاربری'}\n"
            f"💲 موجودی فعلی: {balance:,} تومان\n\n"
            f"برای افزایش موجودی، از دکمه زیر استفاده کنید:"
        )
        
        # ارسال پیام با دکمه افزایش موجودی
        await message.answer(wallet_message, reply_markup=get_wallet_keyboard())
        
    except Exception as e:
        # لاگ خطا و ارسال پیام خطا
        print(f"Error in wallet command: {e}")
        await message.answer("متأسفانه خطایی در سیستم رخ داده است. لطفاً بعداً تلاش کنید یا با پشتیبانی تماس بگیرید.")
    
    finally:
        # بستن سشن دیتابیس در نهایت
        session.close()


async def handle_amount_message(message: types.Message, state: FSMContext):
    """
    پردازش مبلغ وارد شده توسط کاربر
    """
    # دریافت متن پیام
    amount_text = message.text.strip()
    
    try:
        # تبدیل مبلغ به عدد
        amount = int(amount_text.replace(",", ""))
        
        # بررسی معتبر بودن مبلغ
        if amount < 10000:
            await message.answer("مبلغ وارد شده باید حداقل ۱۰,۰۰۰ تومان باشد. لطفاً مبلغ دیگری وارد کنید:")
            return
            
        if amount > 10000000:
            await message.answer("مبلغ وارد شده بیشتر از حد مجاز است. لطفاً مبلغ دیگری وارد کنید:")
            return
        
        # نمایش دکمه تایید مبلغ
        await message.answer(
            f"مبلغ: {amount:,} تومان\n"
            f"لطفاً تایید کنید:",
            reply_markup=get_confirm_amount_keyboard(amount)
        )
        
        # پاک کردن وضعیت
        await state.clear()
        
    except ValueError:
        await message.answer("لطفاً یک عدد معتبر وارد کنید (مثال: ۵۰۰۰۰)")


def register_wallet_command(router: Router, session_maker: sessionmaker):
    """
    ثبت هندلر دستور /wallet در روتر ربات
    """
    global _session_maker
    _session_maker = session_maker
    
    # دستور wallet
    router.message.register(
        wallet_command,
        Command("wallet")
    )
    
    # پردازش مبلغ وارد شده
    router.message.register(
        handle_amount_message,
        WalletStates.waiting_for_amount
    )