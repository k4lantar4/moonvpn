"""User wallet management handlers."""

import logging
from decimal import Decimal
from typing import Optional, List, Dict, Any

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

# Import WalletService and related models/schemas
from bot.services.wallet_service import WalletService
from bot.services.payment_service import PaymentService
from bot.services.user_service import UserService
from core.schemas.wallet import Wallet
from core.schemas.transaction import Transaction, TransactionType
from core.database.repositories.bank_card_repository import BankCardRepository

# Import keyboards for wallet operations
from bot.keyboards.inline.wallet_keyboards import (
    get_wallet_keyboard,
    get_deposit_amounts_keyboard
)
from bot.keyboards.inline.payment_keyboards import get_card_selection_keyboard
from bot.keyboards.inline.common_keyboards import get_back_button

# Setup logger for this handler
logger = logging.getLogger(__name__)

# Define wallet router
wallet_router = Router(name="user-wallet")

# --- Wallet Command Handler ---
@wallet_router.message(Command("wallet"))
async def cmd_wallet(message: Message, session: AsyncSession):
    """Handle the /wallet command to show wallet balance and options."""
    user = message.from_user
    if not user:
        logger.warning("Received /wallet from a user with no user data.")
        return
    
    user_id = user.id
    logger.info(f"Received /wallet command from user_id={user_id}")
    
    try:
        wallet_service = WalletService()
        wallet = await wallet_service.get_user_wallet(session, user_id=user_id)
        
        await message.answer(
            f"💰 <b>کیف پول شما</b>\n\n"
            f"موجودی فعلی: <b>{wallet.balance:,.0f} تومان</b>\n\n"
            f"از طریق دکمه‌های زیر می‌توانید کیف پول خود را شارژ کنید یا تاریخچه تراکنش‌ها را مشاهده کنید.",
            reply_markup=get_wallet_keyboard(float(wallet.balance))
        )
    except Exception as e:
        logger.error(f"Error displaying wallet for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "⚠️ متاسفانه در نمایش اطلاعات کیف پول مشکلی پیش آمد. لطفاً بعداً دوباره تلاش کنید."
        )

# --- Wallet Callback Handlers ---
@wallet_router.callback_query(F.data == "wallet")
async def show_wallet(callback: CallbackQuery, session: AsyncSession):
    """Show wallet balance and options."""
    if not callback.from_user:
        logger.warning("Received wallet callback from a user with no user data.")
        return
    
    user_id = callback.from_user.id
    logger.info(f"Received wallet callback from user_id={user_id}")
    
    try:
        wallet_service = WalletService()
        wallet = await wallet_service.get_user_wallet(session, user_id=user_id)
        
        await callback.message.edit_text(
            f"💰 <b>کیف پول شما</b>\n\n"
            f"موجودی فعلی: <b>{wallet.balance:,.0f} تومان</b>\n\n"
            f"از طریق دکمه‌های زیر می‌توانید کیف پول خود را شارژ کنید یا تاریخچه تراکنش‌ها را مشاهده کنید.",
            reply_markup=get_wallet_keyboard(float(wallet.balance))
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error displaying wallet for user {user_id}: {e}", exc_info=True)
        await callback.answer("مشکلی در نمایش اطلاعات کیف پول پیش آمد.", show_alert=True)

# --- Deposit Methods ---
@wallet_router.callback_query(F.data == "deposit_card")
async def deposit_card(callback: CallbackQuery, session: AsyncSession):
    """Handle card deposit option selection."""
    if not callback.from_user:
        return
    
    user_id = callback.from_user.id
    logger.info(f"User {user_id} selected card deposit")
    
    try:
        # Predefined deposit amounts
        amounts = [50000, 100000, 200000, 500000, 1000000]
        
        await callback.message.edit_text(
            "💳 <b>افزایش موجودی با کارت به کارت</b>\n\n"
            "لطفاً مبلغ مورد نظر برای شارژ کیف پول را انتخاب کنید:",
            reply_markup=get_deposit_amounts_keyboard(amounts, "wallet")
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing deposit amounts for user {user_id}: {e}", exc_info=True)
        await callback.answer("مشکلی در نمایش گزینه‌های شارژ پیش آمد.", show_alert=True)

@wallet_router.callback_query(F.data.startswith("deposit_amount_"))
async def select_deposit_amount(callback: CallbackQuery, session: AsyncSession):
    """Handle selection of a predefined deposit amount."""
    if not callback.from_user:
        return
    
    user_id = callback.from_user.id
    try:
        # Extract amount from callback data
        amount = int(callback.data.split("_")[-1])
        logger.info(f"User {user_id} selected deposit amount: {amount}")
        
        # Get available bank cards
        card_repo = BankCardRepository()
        bank_cards = await card_repo.get_active_cards(session)
        
        if not bank_cards:
            await callback.message.edit_text(
                "⚠️ در حال حاضر هیچ کارت بانکی فعالی برای پرداخت وجود ندارد. لطفاً بعداً دوباره تلاش کنید.",
                reply_markup=get_back_button(callback_data="wallet")
            )
            await callback.answer()
            return
        
        # Store user's selected amount in session or context
        # For now, include it in the next callback data
        
        card_list = [{"id": card.id, "bank_name": card.bank_name, "card_number": card.card_number} for card in bank_cards]
        
        await callback.message.edit_text(
            f"💳 <b>افزایش موجودی به مبلغ {amount:,} تومان</b>\n\n"
            "لطفاً کارت بانکی مقصد را انتخاب کنید:",
            reply_markup=get_card_selection_keyboard(card_list, f"deposit_amount_{amount}")
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error processing deposit amount selection for user {user_id}: {e}", exc_info=True)
        await callback.answer("مشکلی در پردازش انتخاب مبلغ پیش آمد.", show_alert=True)

@wallet_router.callback_query(F.data.startswith("select_card_"))
async def select_card_for_deposit(callback: CallbackQuery, session: AsyncSession):
    """Handle bank card selection for deposit."""
    if not callback.from_user or not callback.message:
        return
    
    user_id = callback.from_user.id
    message = callback.message
    
    try:
        card_id = int(callback.data.split("_")[-1])
        
        # Need to extract amount from previous context
        # For now, let's check message text for amount
        amount_text = message.text
        amount = 0
        import re
        
        # Extract amount from text like "💳 افزایش موجودی به مبلغ 100,000 تومان"
        amount_match = re.search(r'مبلغ (\d{1,3}(?:,\d{3})*) تومان', amount_text)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            amount = int(amount_str)
        
        if amount <= 0:
            await callback.answer("مبلغ شارژ نامعتبر است.", show_alert=True)
            return
        
        # Get card details
        card_repo = BankCardRepository()
        card = await card_repo.get(session, id=card_id)
        
        if not card:
            await callback.answer("کارت انتخاب شده در سیستم یافت نشد.", show_alert=True)
            return
        
        # Create payment request
        payment_service = PaymentService()
        payment = await payment_service.create_wallet_charge_request(
            session,
            user_id=user_id,
            amount=Decimal(amount),
            bank_card_id=card_id
        )
        
        # Commit session to save payment
        await session.commit()
        
        # Masked card number for display
        card_number = card.card_number
        masked_card = f"{card_number[:4]}...{card_number[-4:]}" if len(card_number) >= 8 else card_number
        
        await message.edit_text(
            f"🏦 <b>درخواست شارژ کیف پول</b>\n\n"
            f"مبلغ: <b>{amount:,} تومان</b>\n"
            f"شماره کارت: <b>{masked_card}</b>\n"
            f"بانک: <b>{card.bank_name}</b>\n"
            f"به نام: <b>{card.owner_name}</b>\n\n"
            f"📝 <b>مراحل بعدی:</b>\n"
            f"1. لطفاً مبلغ {amount:,} تومان را به کارت بالا واریز کنید.\n"
            f"2. عکس رسید پرداخت را در چت ارسال کنید.\n"
            f"3. پس از تایید ادمین، مبلغ به کیف پول شما افزوده خواهد شد.\n\n"
            f"شناسه پرداخت: <code>{payment.id}</code>\n"
            f"لطفاً در صورت نیاز، این شناسه را به ادمین اطلاع دهید.",
            reply_markup=get_back_button(callback_data="wallet")
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error processing card selection for user {user_id}: {e}", exc_info=True)
        await callback.answer("مشکلی در پردازش انتخاب کارت پیش آمد.", show_alert=True)
        try:
            await session.rollback()
        except Exception:
            pass

@wallet_router.callback_query(F.data == "wallet_history_soon")
async def wallet_history_soon(callback: CallbackQuery):
    """Handle wallet history (coming soon)."""
    await callback.answer("این قابلیت به زودی فعال خواهد شد. 🔜", show_alert=True)

# Register all handlers
def register_wallet_handlers(dp):
    """Register all wallet handlers."""
    dp.include_router(wallet_router)
    logger.info("Wallet handlers registered.") 