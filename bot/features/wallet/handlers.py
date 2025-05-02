"""
هندلرهای مربوط به ویژگی کیف پول (Wallet Feature)
"""

import logging
from decimal import Decimal
from typing import Union

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

# مدل‌ها و سرویس‌های مورد نیاز
from db.models.user import User
from db.models.transaction import TransactionType, TransactionStatus
from core.services.payment_service import PaymentService
# from core.services.user_service import UserService # دیگر نیازی نیست چون user از میدلور میاد

# کیبوردها و وضعیت‌های مربوط به کیف پول
from .keyboards import (
    get_wallet_menu_keyboard,
    get_cancel_topup_keyboard,
    get_confirm_amount_keyboard,
    get_payment_methods_keyboard, # اگرچه هنوز استفاده نشده
    WALLET_MENU_CB,
    WALLET_TOPUP_CB,
    WALLET_HISTORY_CB,
    WALLET_CONFIRM_AMOUNT_PREFIX,
    WALLET_CANCEL_TOPUP_CB # Note: WALLET_CANCEL_TOPUP_CB might be the same as WALLET_MENU_CB now
)
from .states import WalletStates

logger = logging.getLogger(__name__)
router = Router(name="wallet")


async def show_wallet_menu(target: Union[Message, CallbackQuery], user: User, session: AsyncSession):
    """نمایش منوی اصلی کیف پول و موجودی کاربر."""
    message = target if isinstance(target, Message) else target.message
    try:
        payment_service = PaymentService(session)
        balance = await payment_service.get_user_balance(user.id)
        
        wallet_message = (
            f"💰 **کیف پول شما**\n\n"
            f"👤 کاربر: {user.username or user.first_name or 'کاربر'}\n"
            f"💲 موجودی فعلی: **{balance:,.0f} تومان**\n"
        )
        
        if isinstance(target, CallbackQuery):
            try:
                await message.edit_text(wallet_message, reply_markup=get_wallet_menu_keyboard())
            except Exception:
                 # If edit fails (e.g., same text), send a new message or just answer callback
                 await target.answer() # Acknowledge callback
                 # Optionally send a new message if edit fails
                 # await message.answer(wallet_message, reply_markup=get_wallet_menu_keyboard())
            await target.answer() # Ensure callback is always answered
        else:
            await message.answer(wallet_message, reply_markup=get_wallet_menu_keyboard())
            
    except Exception as e:
        logger.exception(f"Error displaying wallet info for user {user.id}: {e}")
        error_message = "앗! مشکلی در نمایش اطلاعات کیف پول پیش آمد. 😥 لطفا دوباره تلاش کنید."
        if isinstance(target, CallbackQuery):
            await target.answer("خطا در نمایش کیف پول", show_alert=True)
            try: # Try to edit message to show error
                await message.edit_text(error_message)
            except Exception:
                await message.answer(error_message) # Fallback to sending new message
        else:
            await message.answer(error_message)

# --- Command Handler --- 

@router.message(Command("wallet"))
@router.message(F.text == "💰 کیف پول") # Handle text button from main keyboard
async def handle_wallet_command(message: Message, user: User, session: AsyncSession):
    """هندلر دستور /wallet و دکمه متنی کیف پول."""
    await show_wallet_menu(message, user, session)

# --- Callback Query Handlers --- 

@router.callback_query(F.data == WALLET_MENU_CB)
async def handle_wallet_menu_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """هندلر دکمه بازگشت به منوی کیف پول."""
    await show_wallet_menu(callback, user, session)

@router.callback_query(F.data == WALLET_TOPUP_CB)
async def handle_topup_button(callback: CallbackQuery, state: FSMContext):
    """هندلر دکمه افزایش موجودی."""
    await callback.answer()
    await callback.message.edit_text( # Edit previous message
        "لطفاً مبلغ مورد نظر برای شارژ کیف پول را وارد کنید (به تومان، حداقل ۱۰,۰۰۰ تومان):",
        reply_markup=get_cancel_topup_keyboard() # Keyboard with cancel button
    )
    await state.set_state(WalletStates.waiting_for_amount)

# Note: Merged cancel functionality into WALLET_MENU_CB
# @router.callback_query(F.data == WALLET_CANCEL_TOPUP_CB)
# async def handle_cancel_button(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
#     """Handler for the cancel button during top-up."""
#     current_state = await state.get_state()
#     if current_state is None:
#         await callback.answer()
#         return
#     logger.info(f"Cancelling state {current_state} for user {user.id}")
#     await state.clear()
#     await callback.answer("عملیات لغو شد")
#     # Show wallet menu again after cancellation
#     await show_wallet_menu(callback, user, session)

@router.callback_query(F.data.startswith(WALLET_CONFIRM_AMOUNT_PREFIX))
async def handle_confirm_amount_button(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    """هندلر دکمه تایید مبلغ شارژ."""
    amount_str = callback.data.split(":")[-1]
    try:
        amount = Decimal(amount_str)
        if amount < 10000:
             await callback.answer("مبلغ نامعتبر است", show_alert=True)
             return
             
    except (ValueError, IndexError):
        logger.warning(f"Invalid amount format in callback data: {callback.data}")
        await callback.answer("خطا در پردازش مبلغ", show_alert=True)
        return

    await callback.answer(f"در حال ثبت تراکنش {amount:,.0f} تومان...")
    try:
        payment_service = PaymentService(session)
        transaction = await payment_service.create_transaction(
            user_id=user.id,
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING
        )
        
        # Get payment instructions (e.g., bank card info)
        # Assuming payment_service has a method for this
        instructions = "**دستورالعمل پرداخت:**\n" \
                       "لطفا مبلغ را به شماره کارت زیر واریز کرده و سپس رسید را ارسال کنید:\n" \
                       "`1234-5678-9012-3456`\n" \
                       "نام صاحب حساب: شرکت مهتاب وی پی ان"
        # TODO: Get actual payment instructions dynamically

        await callback.message.edit_text( # Edit the message
            f"✅ درخواست شارژ شما ثبت شد.\n\n"
            f"شناسه تراکنش: `{transaction.id}`\n"
            f"مبلغ: **{amount:,.0f} تومان**\n\n"
            f"{instructions}\n\n"
            f"❗️ پس از واریز، حتماً از طریق دکمه 'ثبت رسید' در منوی اصلی، رسید خود را ارسال کنید."
            # TODO: Add keyboard to go back or confirm receipt submission later?
            # reply_markup=get_after_payment_keyboard() 
        )
        await state.clear() # Clear state after successful initiation

    except Exception as e:
        logger.exception(f"Error creating deposit transaction for user {user.id}, amount {amount}: {e}")
        await callback.answer("خطا در ثبت تراکنش", show_alert=True)
        await callback.message.edit_text("앗! مشکلی در ثبت درخواست شارژ پیش آمد. 😥 لطفا دوباره تلاش کنید.")
        await state.clear() # Clear state even on error

# --- Message Handler for Amount Input --- 

@router.message(WalletStates.waiting_for_amount)
async def handle_amount_message(message: Message, state: FSMContext, user: User, session: AsyncSession):
    """پردازش مبلغ وارد شده توسط کاربر برای شارژ."""
    amount_text = message.text.strip()
    try:
        # Allow for commas in input
        amount = int(amount_text.replace(",", ""))
        
        if amount < 10000:
            await message.reply("مبلغ وارد شده باید حداقل ۱۰,۰۰۰ تومان باشد. لطفاً مبلغ معتبر دیگری وارد کنید یا انصراف دهید:", reply_markup=get_cancel_topup_keyboard())
            return
            
        if amount > 10000000: # Example limit
            await message.reply("مبلغ وارد شده بیش از حد مجاز (۱۰ میلیون تومان) است. لطفاً مبلغ معتبر دیگری وارد کنید یا انصراف دهید:", reply_markup=get_cancel_topup_keyboard())
            return
        
        # Show confirmation keyboard
        await message.reply(
            f"شما مبلغ **{amount:,} تومان** را وارد کردید.\nلطفاً مبلغ را تایید کنید:",
            reply_markup=get_confirm_amount_keyboard(amount)
        )
        # Don't clear state here, wait for confirmation callback
        
    except ValueError:
        await message.reply("لطفاً یک مبلغ عددی معتبر وارد کنید (مثال: ۵۰۰۰۰) یا انصراف دهید:", reply_markup=get_cancel_topup_keyboard())

# TODO: Implement handler for WALLET_HISTORY_CB
# TODO: Implement handlers for payment callbacks (PAYMENT_ONLINE_PREFIX, PAYMENT_CARD_PREFIX) 