"""
هندلرهای callback مربوط به کیف پول و تراکنش‌ها
"""

from decimal import Decimal
from datetime import datetime
from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.buttons.wallet_buttons import TOPUP_CB, CANCEL_CB, CONFIRM_AMOUNT_PREFIX, get_cancel_keyboard
from core.services.payment_service import PaymentService
from core.services.user_service import UserService
from db.models.transaction import TransactionType, TransactionStatus


# تعریف وضعیت‌های مربوط به کیف پول
class WalletStates(StatesGroup):
    """حالت‌های مربوط به کیف پول"""
    waiting_for_amount = State()


# متغیر سراسری برای دسترسی به session_maker
_session_maker = None


async def handle_topup_button(callback: CallbackQuery, state: FSMContext):
    """
    پردازش دکمه افزایش موجودی
    """
    await callback.answer()
    
    # ارسال پیام درخواست مبلغ
    await callback.message.answer(
        "💰 لطفاً مبلغ مورد نظر برای شارژ کیف پول را وارد کنید (به تومان):",
        reply_markup=get_cancel_keyboard()
    )
    
    # تنظیم وضعیت به حالت انتظار برای ورود مبلغ
    await state.set_state(WalletStates.waiting_for_amount)


async def handle_cancel_button(callback: CallbackQuery, state: FSMContext):
    """
    پردازش دکمه انصراف
    """
    await callback.answer()
    
    # خروج از وضعیت فعلی
    await state.clear()
    
    # ارسال پیام انصراف
    await callback.message.answer("عملیات افزایش موجودی لغو شد.")


async def handle_confirm_amount_button(callback: CallbackQuery, state: FSMContext):
    """
    پردازش دکمه تایید مبلغ
    """
    await callback.answer()
    
    # استخراج مبلغ از callback data
    amount_str = callback.data.replace(CONFIRM_AMOUNT_PREFIX, "")
    try:
        amount = Decimal(amount_str)
    except (ValueError, TypeError):
        await callback.message.answer("مبلغ وارد شده معتبر نیست. لطفاً دوباره تلاش کنید.")
        return
    
    # ایجاد سشن دیتابیس
    async with _session_maker() as session:
        try:
            # دریافت اطلاعات کاربر
            user_service = UserService(session)
            payment_service = PaymentService(session)
            
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.message.answer("خطا در شناسایی کاربر. لطفاً دوباره تلاش کنید.")
                return
            
            # ایجاد تراکنش با وضعیت در انتظار و تاریخ فعلی
            try:
                transaction = await payment_service.create_transaction(
                    user_id=user.id,
                    amount=amount,
                    transaction_type=TransactionType.PAYMENT,
                    status=TransactionStatus.PENDING
                )
                
                # ارسال دستورالعمل پرداخت
                instructions = await payment_service.get_payment_instructions()
                
                await callback.message.answer(
                    f"✅ تراکنش با شناسه {transaction.id} ایجاد شد.\n\n"
                    f"🔰 مبلغ: {amount:,} تومان\n\n"
                    f"{instructions}\n\n"
                    f"شناسه تراکنش شما: {transaction.id}"
                )
            except Exception as e:
                await callback.message.answer(f"خطا در ایجاد تراکنش: {str(e)}")
                print(f"Error creating transaction: {str(e)}")
                # بررسی دقیق خطا و لاگ آن
                import traceback
                print(traceback.format_exc())
            
            # پاک کردن وضعیت
            await state.clear()
            
        except Exception as e:
            await callback.message.answer(f"خطایی رخ داد: {str(e)}")
            print(f"General error in handle_confirm_amount_button: {str(e)}")


def register_wallet_callbacks(router: Router, session_maker: async_sessionmaker[AsyncSession]):
    """
    ثبت هندلرهای callback مربوط به کیف پول در روتر ربات
    """
    global _session_maker
    _session_maker = session_maker
    
    # دکمه افزایش موجودی
    router.callback_query.register(
        handle_topup_button,
        F.data == TOPUP_CB
    )
    
    # دکمه انصراف
    router.callback_query.register(
        handle_cancel_button,
        F.data == CANCEL_CB
    )
    
    # دکمه تایید مبلغ
    router.callback_query.register(
        handle_confirm_amount_button,
        F.data.startswith(CONFIRM_AMOUNT_PREFIX)
    ) 