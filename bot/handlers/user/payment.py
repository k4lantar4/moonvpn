"""User payment handling."""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

# Import services and models
from bot.services.payment_service import PaymentService
from bot.services.wallet_service import WalletService
from bot.services.plan_service import PlanService
from bot.services.client_service import ClientService
from core.exceptions import BusinessLogicError, NotFoundError, ServiceError

# Import keyboards
from bot.keyboards.inline.payment_keyboards import (
    get_payment_methods_keyboard,
    get_card_selection_keyboard
)
from bot.keyboards.inline.common_keyboards import get_back_button

# Setup logger
logger = logging.getLogger(__name__)

# Define payment router
payment_router = Router(name="user-payment")

# --- Payment Method Selection ---
@payment_router.callback_query(F.data.startswith("purchase_plan_"))
async def select_payment_method(callback: CallbackQuery, session: AsyncSession):
    """Handle payment method selection for plan purchase."""
    if not callback.from_user:
        return
    
    user_id = callback.from_user.id
    try:
        # Extract plan_id from callback data
        plan_id = int(callback.data.split("_")[-1])
        logger.info(f"User {user_id} selecting payment method for plan {plan_id}")
        
        # Get plan details
        plan_service = PlanService()
        plan = await plan_service.get_plan_by_id(session, plan_id)
        
        if not plan:
            await callback.answer("پلن مورد نظر یافت نشد.", show_alert=True)
            return
        
        # Check wallet balance to determine if wallet payment is possible
        wallet_service = WalletService()
        wallet = await wallet_service.get_user_wallet(session, user_id)
        wallet_sufficient = wallet.balance >= plan.price
        
        # Store plan_id in session or context for later use
        # For now, include it in callback_data
        
        await callback.message.edit_text(
            f"💳 <b>انتخاب روش پرداخت</b>\n\n"
            f"پلن: <b>{plan.name}</b>\n"
            f"قیمت: <b>{plan.price:,} تومان</b>\n"
            f"مدت: <b>{plan.duration_days} روز</b>\n"
            f"ترافیک: <b>{plan.traffic_gb} گیگابایت</b>\n\n"
            f"لطفاً روش پرداخت را انتخاب کنید:",
            reply_markup=get_payment_methods_keyboard(
                wallet_sufficient=wallet_sufficient,
                back_callback=f"plan_details_{plan_id}"
            )
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing payment methods for user {user_id}: {e}", exc_info=True)
        await callback.answer("مشکلی در پردازش درخواست پیش آمد.", show_alert=True)

# --- Wallet Payment Handler ---
@payment_router.callback_query(F.data == "pay_wallet")
async def pay_with_wallet(callback: CallbackQuery, session: AsyncSession):
    """Process wallet payment for plan purchase."""
    if not callback.from_user or not callback.message:
        return
    
    user_id = callback.from_user.id
    message = callback.message
    
    try:
        # Extract plan information from message text
        import re
        plan_name = ""
        plan_price = 0
        
        # Extract plan name like "پلن: Basic"
        name_match = re.search(r'پلن: <b>(.*?)<\/b>', message.text, re.DOTALL)
        if name_match:
            plan_name = name_match.group(1)
        
        # Extract price like "قیمت: 100,000 تومان"
        price_match = re.search(r'قیمت: <b>(\d{1,3}(?:,\d{3})*) تومان<\/b>', message.text)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            plan_price = int(price_str)
        
        if not plan_name or plan_price <= 0:
            await callback.answer("اطلاعات پلن نامعتبر است.", show_alert=True)
            return
        
        # Find plan by name
        plan_service = PlanService()
        plans = await plan_service.get_plans_by_name(session, plan_name)
        
        if not plans or len(plans) == 0:
            await callback.answer("پلن مورد نظر یافت نشد.", show_alert=True)
            return
        
        plan = plans[0]  # Assume the first match is the correct one
        
        # Process wallet payment
        payment_service = PaymentService()
        
        # Create and process payment
        payment = await payment_service.process_wallet_payment(
            session,
            user_id=user_id,
            plan_id=plan.id
        )
        
        # Create client account
        client_service = ClientService()
        client_account = await client_service.create_client(
            session,
            user_id=user_id,
            plan_id=plan.id,
            # Assuming default location and protocol
            location_id=1,  # TODO: Allow selection or use default
            protocol="vmess"  # TODO: Allow selection or use default
        )
        
        # Commit changes
        await session.commit()
        
        # Respond to user
        await callback.message.edit_text(
            f"✅ <b>پرداخت موفق</b>\n\n"
            f"پلن: <b>{plan.name}</b>\n"
            f"قیمت: <b>{plan.price:,} تومان</b>\n"
            f"روش پرداخت: <b>کیف پول</b>\n\n"
            f"🎉 اکانت شما با موفقیت ایجاد شد.\n"
            f"می‌توانید از منوی اصلی، بخش «اکانت‌های من» را انتخاب کنید "
            f"تا لینک اتصال را دریافت کنید.",
            reply_markup=get_back_button(callback_data="main_menu")
        )
        await callback.answer("پرداخت با موفقیت انجام شد! ✅", show_alert=True)
        
    except BusinessLogicError as e:
        logger.warning(f"Business logic error during wallet payment for user {user_id}: {e}")
        await callback.answer(f"خطا: {str(e)}", show_alert=True)
        try:
            await session.rollback()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error processing wallet payment for user {user_id}: {e}", exc_info=True)
        await callback.answer("مشکلی در پردازش پرداخت پیش آمد.", show_alert=True)
        try:
            await session.rollback()
        except Exception:
            pass

# --- Card Payment Handler ---
@payment_router.callback_query(F.data == "pay_card")
async def pay_with_card(callback: CallbackQuery, session: AsyncSession):
    """Handle card payment option for plan purchase."""
    if not callback.from_user:
        return
    
    user_id = callback.from_user.id
    
    try:
        # Extract plan information from message text
        import re
        plan_name = ""
        
        # Extract plan name like "پلن: Basic"
        name_match = re.search(r'پلن: <b>(.*?)<\/b>', callback.message.text, re.DOTALL)
        if name_match:
            plan_name = name_match.group(1)
        
        # Find plan by name
        plan_service = PlanService()
        plans = await plan_service.get_plans_by_name(session, plan_name)
        
        if not plans or len(plans) == 0:
            await callback.answer("پلن مورد نظر یافت نشد.", show_alert=True)
            return
        
        plan = plans[0]  # Assume the first match is the correct one
        
        # Get bank cards
        from core.database.repositories.bank_card_repository import BankCardRepository
        card_repo = BankCardRepository()
        bank_cards = await card_repo.get_active_cards(session)
        
        if not bank_cards:
            await callback.message.edit_text(
                "⚠️ در حال حاضر هیچ کارت بانکی فعالی برای پرداخت وجود ندارد. "
                "لطفاً از روش دیگری استفاده کنید یا بعداً دوباره تلاش کنید.",
                reply_markup=get_back_button(callback_data=f"purchase_plan_{plan.id}")
            )
            await callback.answer()
            return
        
        card_list = [{"id": card.id, "bank_name": card.bank_name, "card_number": card.card_number} for card in bank_cards]
        
        await callback.message.edit_text(
            f"💳 <b>پرداخت با کارت برای پلن {plan.name}</b>\n\n"
            f"قیمت: <b>{plan.price:,} تومان</b>\n\n"
            f"لطفاً کارت بانکی مقصد را انتخاب کنید:",
            reply_markup=get_card_selection_keyboard(card_list, f"purchase_plan_{plan.id}")
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing card options for user {user_id}: {e}", exc_info=True)
        await callback.answer("مشکلی در پردازش درخواست پیش آمد.", show_alert=True)

@payment_router.callback_query(F.data.startswith("select_card_") & ~F.data.startswith("select_card_for_"))
async def select_card_for_payment(callback: CallbackQuery, session: AsyncSession):
    """Handle bank card selection for plan payment."""
    if not callback.from_user or not callback.message:
        return
    
    user_id = callback.from_user.id
    message = callback.message
    
    try:
        card_id = int(callback.data.split("_")[-1])
        
        # Extract plan information from message text
        import re
        plan_name = ""
        plan_price = 0
        
        # Extract plan name like "پلن Basic" or "پرداخت با کارت برای پلن Basic"
        name_match = re.search(r'پلن (.*?)(?:<\/b>|$)', message.text, re.DOTALL)
        if name_match:
            plan_name = name_match.group(1).strip()
            if plan_name.startswith("<b>"):
                plan_name = plan_name[3:]
            if plan_name.endswith("</b>"):
                plan_name = plan_name[:-4]
        
        # Extract price like "قیمت: 100,000 تومان"
        price_match = re.search(r'قیمت: <b>(\d{1,3}(?:,\d{3})*) تومان<\/b>', message.text)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            plan_price = int(price_str)
        
        if not plan_name or plan_price <= 0:
            await callback.answer("اطلاعات پلن نامعتبر است.", show_alert=True)
            return
        
        # Find plan by name
        plan_service = PlanService()
        plans = await plan_service.get_plans_by_name(session, plan_name)
        
        if not plans or len(plans) == 0:
            await callback.answer("پلن مورد نظر یافت نشد.", show_alert=True)
            return
        
        plan = plans[0]  # Assume the first match is the correct one
        
        # Get card details
        from core.database.repositories.bank_card_repository import BankCardRepository
        card_repo = BankCardRepository()
        card = await card_repo.get(session, id=card_id)
        
        if not card:
            await callback.answer("کارت انتخاب شده در سیستم یافت نشد.", show_alert=True)
            return
        
        # Create payment request
        payment_service = PaymentService()
        payment = await payment_service.create_card_payment_request(
            session,
            user_id=user_id,
            plan_id=plan.id,
            bank_card_id=card_id
        )
        
        # Commit session to save payment
        await session.commit()
        
        # Masked card number for display
        card_number = card.card_number
        masked_card = f"{card_number[:4]}...{card_number[-4:]}" if len(card_number) >= 8 else card_number
        
        await message.edit_text(
            f"🏦 <b>درخواست پرداخت برای پلن {plan.name}</b>\n\n"
            f"مبلغ: <b>{plan.price:,} تومان</b>\n"
            f"شماره کارت: <b>{masked_card}</b>\n"
            f"بانک: <b>{card.bank_name}</b>\n"
            f"به نام: <b>{card.owner_name}</b>\n\n"
            f"📝 <b>مراحل بعدی:</b>\n"
            f"1. لطفاً مبلغ {plan.price:,} تومان را به کارت بالا واریز کنید.\n"
            f"2. عکس رسید پرداخت را در چت ارسال کنید.\n"
            f"3. پس از تایید ادمین، اکانت شما فعال خواهد شد.\n\n"
            f"شناسه پرداخت: <code>{payment.id}</code>\n"
            f"لطفاً در صورت نیاز، این شناسه را به ادمین اطلاع دهید.",
            reply_markup=get_back_button(callback_data="main_menu")
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error processing card selection for payment by user {user_id}: {e}", exc_info=True)
        await callback.answer("مشکلی در پردازش انتخاب کارت پیش آمد.", show_alert=True)
        try:
            await session.rollback()
        except Exception:
            pass

@payment_router.callback_query(F.data == "pay_wallet_insufficient")
async def wallet_insufficient(callback: CallbackQuery):
    """Handle insufficient wallet balance."""
    await callback.answer(
        "موجودی کیف پول شما کافی نیست. لطفاً ابتدا کیف پول خود را شارژ کنید.", 
        show_alert=True
    )

# Register all handlers
def register_payment_handlers(dp):
    """Register all payment handlers."""
    dp.include_router(payment_router)
    logger.info("Payment handlers registered.") 