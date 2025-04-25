"""
مدیریت کیف پول و پرداخت‌ها
"""

from decimal import Decimal
from typing import Union
from aiogram import types, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.buttons.wallet_buttons import get_wallet_keyboard, get_confirm_amount_keyboard
from bot.callbacks.wallet_callbacks import WalletStates
from core.services.user_service import UserService
from core.services.payment_service import PaymentService
from db.models.transaction import TransactionType, TransactionStatus

# متغیر سراسری برای دسترسی به session_maker
_session_maker: async_sessionmaker[AsyncSession] = None


async def _display_wallet_info(target: Union[Message, CallbackQuery], session: AsyncSession):
    """
    منطق اصلی نمایش اطلاعات کیف پول کاربر
    """
    user_id = target.from_user.id
    message = target if isinstance(target, Message) else target.message

    try:
        # دریافت اطلاعات کاربر
        user_service = UserService(session)
        payment_service = PaymentService(session)
        
        user = await user_service.get_user_by_telegram_id(user_id)
        if not user:
            await message.answer("خطا در شناسایی کاربر. لطفاً ابتدا از دستور /start استفاده کنید.")
            return
        
        # نمایش وضعیت کیف پول
        balance = await payment_service.get_user_balance(user.id)
        
        wallet_message = (
            f"💰 کیف پول شما\n\n"
            f"👤 کاربر: {user.username or 'بدون نام کاربری'}\n"
            f"💲 موجودی فعلی: {balance:,} تومان\n\n"
            f"برای افزایش موجودی، از دکمه زیر استفاده کنید:"
        )
        
        # ارسال پیام با دکمه افزایش موجودی
        if isinstance(target, CallbackQuery):
            await message.edit_text(wallet_message, reply_markup=get_wallet_keyboard())
            await target.answer()
        else:
            await message.answer(wallet_message, reply_markup=get_wallet_keyboard())
        
    except Exception as e:
        # لاگ خطا و ارسال پیام خطا
        print(f"خطا در نمایش اطلاعات کیف پول: {e}")
        error_message = "متأسفانه خطایی در سیستم رخ داده است. لطفاً بعداً تلاش کنید یا با پشتیبانی تماس بگیرید."
        if isinstance(target, CallbackQuery):
            try:
                await message.edit_text(error_message)
            except Exception as edit_err:
                print(f"Could not edit message on wallet error: {edit_err}")
                await message.answer(error_message)
            await target.answer("خطا در نمایش کیف پول")
        else:
            await message.answer(error_message)


async def wallet_command(message: types.Message):
    """
    هندلر دستور /wallet و دکمه متنی "کیف پول"
    """
    async with _session_maker() as session:
        await _display_wallet_info(message, session)


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


def register_wallet_command(router: Router, session_maker: async_sessionmaker[AsyncSession]):
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
    
    # هندلر دکمه متن "کیف پول"
    router.message.register(
        wallet_command, 
        F.text == "💳 کیف پول"
    )
    
    # پردازش مبلغ وارد شده
    router.message.register(
        handle_amount_message,
        WalletStates.waiting_for_amount
    )