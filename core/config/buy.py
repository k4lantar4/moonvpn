"""
Buy handler for MoonVPN Telegram Bot.

This module handles the process of purchasing new VPN accounts.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    ConversationHandler,
    filters
)
from telegram.constants import ParseMode
from django.utils import timezone
from django.conf import settings

from core.config import settings
from core.database import get_db
from core.models.user import User
from core.models.server import Server
from core.models.subscription_plan import SubscriptionPlan
from core.utils.i18n import _
from core.database import get_subscription_plans, get_user
from core.utils.formatting import allowed_group_filter
from core.utils.helpers import require_feature
from core.utils.helpers import authenticated_user
from backend.payments.services import PaymentService
from backend.accounts.services import AccountService
from core.utils.helpers import format_number, get_user, human_readable_size
from core.utils.helpers import get_back_button
from core.models.vpn_account import VPNAccount
from core.models.transaction import Transaction
from core.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

# Define conversation states
SELECTING_PLAN, SELECTING_PAYMENT_METHOD, CONFIRMING_PAYMENT, VERIFYING_PAYMENT = range(4)

@authenticated_user
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for /buy command - shows available plans"""
    user = get_user(update.effective_user.id)
    
    try:
        # Get active plans
        plans = PaymentService.get_active_plans()
        
        if not plans:
            await update.message.reply_text(
                "⚠️ در حال حاضر پلنی برای فروش موجود نیست. لطفا بعدا مراجعه کنید.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Show available plans
        buttons = []
        for plan in plans:
            # Format price with discount if available
            if plan.discount_price:
                price_text = f"{format_number(plan.display_price)} تومان (🔥 {plan.discount_percentage}% تخفیف)"
            else:
                price_text = f"{format_number(plan.display_price)} تومان"
            
            plan_text = f"{plan.name}: {plan.traffic_amount} {plan.traffic_unit} - {plan.duration_days} روز - {price_text}"
            buttons.append([InlineKeyboardButton(plan_text, callback_data=f"plan_{plan.id}")])
        
        # Add cancel button
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await update.message.reply_text(
            "🛒 <b>پلن های موجود</b>\n\n"
            "لطفا یکی از پلن های زیر را انتخاب کنید:\n\n"
            "<i>پس از انتخاب پلن، روش پرداخت را انتخاب خواهید کرد.</i>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return SELECTING_PLAN
        
    except Exception as e:
        logger.exception(f"Error in buy command: {str(e)}")
        await update.message.reply_text(
            "⚠️ خطایی رخ داد. لطفا بعدا مراجعه کنید."
        )
        return ConversationHandler.END

async def plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.reply_text("❌ عملیات خرید لغو شد.")
        return ConversationHandler.END
    
    plan_id = int(query.data.split("_")[1])
    user = get_user(query.from_user.id)
    
    try:
        # Get plan details
        all_plans = PaymentService.get_active_plans()
        selected_plan = next((p for p in all_plans if p.id == plan_id), None)
        
        if not selected_plan:
            await query.message.reply_text(
                "⚠️ پلن انتخابی معتبر نیست. لطفا دوباره تلاش کنید.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Store selected plan in conversation data
        context.user_data['selected_plan'] = selected_plan
        
        # Show payment methods
        payment_methods = PaymentService.get_active_payment_methods()
        
        if not payment_methods:
            await query.message.reply_text(
                "⚠️ در حال حاضر روش پرداختی فعال نیست. لطفا بعدا مراجعه کنید.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        buttons = []
        for method in payment_methods:
            method_name = method.get_name_display()
            buttons.append([InlineKeyboardButton(method_name, callback_data=f"payment_{method.name}")])
        
        # Add discount code option and back button
        buttons.append([InlineKeyboardButton("🎁 کد تخفیف دارم", callback_data="discount")])
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_plans")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        # Format price with discount if available
        if selected_plan.discount_price:
            price_text = (
                f"💰 قیمت: <s>{format_number(selected_plan.price)} تومان</s> "
                f"<b>{format_number(selected_plan.display_price)} تومان</b> (🔥 {selected_plan.discount_percentage}% تخفیف)"
            )
        else:
            price_text = f"💰 قیمت: <b>{format_number(selected_plan.display_price)} تومان</b>"
        
        # Apply discount code if one is stored in context
        discount_info = ""
        if 'discount_code' in context.user_data:
            discount = context.user_data['discount_code']
            original_price = selected_plan.display_price
            discounted_price = discount.apply_discount(original_price)
            discount_info = (
                f"\n\n🎁 <b>کد تخفیف:</b> {discount.code} "
                f"({discount.discount_percentage}% تخفیف)\n"
                f"💰 قیمت نهایی: <b>{format_number(discounted_price)} تومان</b>"
            )
        
        await query.message.edit_text(
            f"🛒 <b>خرید {selected_plan.name}</b>\n\n"
            f"✅ حجم: <b>{selected_plan.traffic_amount} {selected_plan.traffic_unit}</b>\n"
            f"⏱ مدت زمان: <b>{selected_plan.duration_days} روز</b>\n"
            f"{price_text}"
            f"{discount_info}\n\n"
            f"لطفا روش پرداخت را انتخاب کنید:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return SELECTING_PAYMENT_METHOD
        
    except Exception as e:
        logger.exception(f"Error in plan selection: {str(e)}")
        await query.message.reply_text(
            "⚠️ خطایی رخ داد. لطفا بعدا مراجعه کنید."
        )
        return ConversationHandler.END

async def discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle discount code entry"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "🎁 <b>کد تخفیف</b>\n\n"
        "لطفا کد تخفیف خود را وارد کنید. برای انصراف روی /cancel کلیک کنید.",
        parse_mode=ParseMode.HTML
    )
    
    return CONFIRMING_PAYMENT

async def apply_discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Apply discount code"""
    discount_code = update.message.text.strip()
    user = get_user(update.effective_user.id)
    selected_plan = context.user_data.get('selected_plan')
    
    if discount_code.startswith('/'):
        if discount_code == '/cancel':
            await update.message.reply_text("❌ عملیات خرید لغو شد.")
            return ConversationHandler.END
        await update.message.reply_text(
            "⚠️ لطفا کد تخفیف معتبر وارد کنید یا برای انصراف روی /cancel کلیک کنید."
        )
        return CONFIRMING_PAYMENT
    
    try:
        # Validate discount code
        is_valid, discount, message = PaymentService.validate_discount_code(discount_code, selected_plan)
        
        if not is_valid:
            await update.message.reply_text(
                f"⚠️ {message}\n\n"
                "لطفا کد تخفیف دیگری وارد کنید یا برای انصراف روی /cancel کلیک کنید.",
                parse_mode=ParseMode.HTML
            )
            return CONFIRMING_PAYMENT
        
        # Store discount code in context
        context.user_data['discount_code'] = discount
        
        # Return to payment method selection with discount applied
        return await plan_selection(update, context)
        
    except Exception as e:
        logger.exception(f"Error applying discount: {str(e)}")
        await update.message.reply_text(
            "⚠️ خطایی در اعمال کد تخفیف رخ داد. لطفا دوباره تلاش کنید."
        )
        return CONFIRMING_PAYMENT

async def payment_method_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_plans":
        # Clear discount code if any
        if 'discount_code' in context.user_data:
            del context.user_data['discount_code']
        
        # Show plans again
        await buy_command(update, context)
        return SELECTING_PLAN
    
    if query.data == "discount":
        # Handle discount code entry separately
        await discount_code(update, context)
        return CONFIRMING_PAYMENT
    
    payment_method = query.data.split("_")[1]
    user = get_user(query.from_user.id)
    selected_plan = context.user_data.get('selected_plan')
    discount_code = context.user_data.get('discount_code')
    
    try:
        # Create payment record
        discount_code_str = discount_code.code if discount_code else None
        payment, error = PaymentService.create_payment(
            user=user,
            plan=selected_plan,
            payment_method_name=payment_method,
            discount_code=discount_code_str
        )
        
        if error or not payment:
            await query.message.reply_text(
                f"⚠️ خطا در ایجاد پرداخت: {error}",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Store payment ID in context
        context.user_data['payment_id'] = str(payment.id)
        
        # Get payment instructions
        payment_instructions = PaymentService.get_payment_instructions(payment)
        
        if "error" in payment_instructions:
            await query.message.reply_text(
                f"⚠️ خطا در دریافت اطلاعات پرداخت: {payment_instructions['error']}",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Handle different payment methods
        if payment_method == "card":
            # Format card number
            card_number = payment_instructions.get("card_number", "")
            if len(card_number) == 16:
                card_number = f"{card_number[:4]}-{card_number[4:8]}-{card_number[8:12]}-{card_number[12:]}"
            
            # Calculate expiration time
            expires_at = payment_instructions.get("expires_at")
            expires_in = payment_instructions.get("expires_in_minutes", 30)
            expiry_text = f"⏱ این پرداخت تا <b>{expires_in} دقیقه</b> دیگر معتبر است."
            
            # Create verification buttons
            buttons = [
                [InlineKeyboardButton("✅ پرداخت را انجام دادم", callback_data="verify_payment")],
                [InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment")]
            ]
            
            reply_markup = InlineKeyboardMarkup(buttons)
            
            await query.message.edit_text(
                f"💳 <b>پرداخت کارت به کارت</b>\n\n"
                f"💰 مبلغ: <b>{format_number(payment_instructions['amount'])} تومان</b>\n"
                f"💳 شماره کارت: <b>{card_number}</b>\n"
                f"👤 به نام: <b>{payment_instructions.get('card_holder', '')}</b>\n"
                f"🏦 بانک: {payment_instructions.get('bank_name', '')}\n\n"
                f"🔑 کد پیگیری: <code>{payment_instructions.get('reference_code', '')}</code>\n\n"
                f"{expiry_text}\n\n"
                f"<b>⚠️ توجه:</b>\n"
                f"• لطفا <b>دقیقا</b> مبلغ فوق را واریز کنید.\n"
                f"• پس از پرداخت، روی دکمه «پرداخت را انجام دادم» کلیک کنید.\n"
                f"• در صورت هرگونه مشکل، با پشتیبانی تماس بگیرید.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            return VERIFYING_PAYMENT
            
        elif payment_method == "zarinpal":
            # For Zarinpal, provide link to payment gateway
            redirect_url = payment_instructions.get("redirect_url")
            
            buttons = [
                [InlineKeyboardButton("💰 پرداخت آنلاین", url=redirect_url)],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_payment_methods")],
                [InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment")]
            ]
            
            reply_markup = InlineKeyboardMarkup(buttons)
            
            await query.message.edit_text(
                f"💳 <b>پرداخت آنلاین (درگاه زرین پال)</b>\n\n"
                f"💰 مبلغ: <b>{format_number(payment_instructions['amount'])} تومان</b>\n\n"
                f"• برای پرداخت روی دکمه «پرداخت آنلاین» کلیک کنید.\n"
                f"• پس از پرداخت موفق، به ربات برگردانده خواهید شد.\n"
                f"• در صورت بروز مشکل، با پشتیبانی تماس بگیرید.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            return VERIFYING_PAYMENT
        
        else:
            await query.message.reply_text(
                "⚠️ روش پرداخت انتخابی پشتیبانی نمی‌شود. لطفا دوباره تلاش کنید.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
    except Exception as e:
        logger.exception(f"Error in payment method selection: {str(e)}")
        await query.message.reply_text(
            "⚠️ خطایی رخ داد. لطفا بعدا مراجعه کنید."
        )
        return ConversationHandler.END

async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment verification"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_payment":
        # Cancel payment
        payment_id = context.user_data.get('payment_id')
        if payment_id:
            # TODO: Mark payment as canceled
            pass
        
        await query.message.edit_text(
            "❌ پرداخت لغو شد. می‌توانید مجددا با دستور /buy اقدام به خرید کنید.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    if query.data == "back_to_payment_methods":
        # Go back to payment method selection
        return await plan_selection(update, context)
    
    if query.data == "verify_payment":
        # Show form for card payment verification
        await query.message.edit_text(
            "✅ <b>تایید پرداخت کارت به کارت</b>\n\n"
            "لطفا اطلاعات زیر را وارد کنید:\n\n"
            "• 4 رقم آخر کارت خود\n"
            "• نام صاحب کارت\n"
            "• زمان تقریبی واریز\n\n"
            "مثال:\n"
            "6104\n"
            "محمد محمدی\n"
            "همین الان\n\n"
            "⚠️ برای انصراف از دستور /cancel استفاده کنید.",
            parse_mode=ParseMode.HTML
        )
        
        context.user_data['awaiting_verification'] = True
        return CONFIRMING_PAYMENT
    
    return VERIFYING_PAYMENT

async def process_verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process card payment verification data"""
    if 'awaiting_verification' not in context.user_data:
        return VERIFYING_PAYMENT
    
    text = update.message.text
    
    if text.startswith('/cancel'):
        await update.message.reply_text(
            "❌ عملیات تایید پرداخت لغو شد.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    payment_id = context.user_data.get('payment_id')
    
    if not payment_id:
        await update.message.reply_text(
            "⚠️ خطا در دریافت اطلاعات پرداخت. لطفا مجددا از دستور /buy استفاده کنید.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    # Parse verification data
    lines = text.strip().split('\n')
    
    if len(lines) < 2:
        await update.message.reply_text(
            "⚠️ اطلاعات ناقص است. لطفا حداقل 4 رقم آخر کارت و نام صاحب کارت را وارد کنید."
            "یا برای انصراف از دستور /cancel استفاده کنید.",
            parse_mode=ParseMode.HTML
        )
        return CONFIRMING_PAYMENT
    
    card_number = lines[0].strip()
    payer_name = lines[1].strip()
    payment_time = timezone.now()
    
    if len(lines) > 2:
        payer_bank = lines[2].strip()
    else:
        payer_bank = ""
    
    try:
        # Verify payment
        success, message = PaymentService.verify_card_payment(
            payment_id=payment_id,
            payer_card=card_number,
            payer_name=payer_name,
            payer_bank=payer_bank,
            payment_time=payment_time
        )
        
        if success:
            # Check if payment is actually completed or just registered for verification
            is_completed = "verified successfully" in message.lower()
            
            if is_completed:
                # Payment is verified and completed, create VPN account
                try:
                    # Create account
                    success, account_data, error = AccountService.create_account_from_payment(
                        PaymentService.get_payment_by_id(payment_id)
                    )
                    
                    if success and account_data:
                        # Show account details
                        subscription_link = account_data.get('subscription_link', '')
                        
                        await update.message.reply_text(
                            f"🎉 <b>خرید شما با موفقیت انجام شد!</b>\n\n"
                            f"✅ اشتراک شما فعال شد.\n\n"
                            f"📲 <b>لینک اتصال شما:</b>\n"
                            f"<code>{subscription_link}</code>\n\n"
                            f"⏱ مدت زمان: <b>{account_data.get('days_left', 0)} روز</b>\n"
                            f"📦 حجم کل: <b>{human_readable_size(account_data.get('traffic_limit_bytes', 0))}</b>\n\n"
                            f"🔍 برای مشاهده وضعیت اشتراک خود، از دستور /status استفاده کنید.",
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await update.message.reply_text(
                            f"✅ <b>پرداخت شما با موفقیت انجام شد!</b>\n\n"
                            f"⚠️ اما اشتراک شما به طور خودکار فعال نشد.\n"
                            f"خطا: {error}\n\n"
                            f"🧰 تیم پشتیبانی در اسرع وقت اشتراک شما را فعال خواهد کرد.",
                            parse_mode=ParseMode.HTML
                        )
                    
                except Exception as e:
                    logger.exception(f"Error creating account: {str(e)}")
                    await update.message.reply_text(
                        f"✅ <b>پرداخت شما با موفقیت انجام شد!</b>\n\n"
                        f"⚠️ اما در ایجاد اشتراک خطایی رخ داد.\n"
                        f"🧰 تیم پشتیبانی در اسرع وقت اشتراک شما را فعال خواهد کرد.",
                        parse_mode=ParseMode.HTML
                    )
            else:
                # Payment is registered but pending admin verification
                await update.message.reply_text(
                    "✅ <b>اطلاعات پرداخت شما ثبت شد.</b>\n\n"
                    "پرداخت شما در انتظار تایید توسط ادمین است.\n"
                    "پس از تایید، اشتراک شما فعال خواهد شد و از طریق پیام به شما اطلاع داده خواهد شد.\n\n"
                    "⏱ زمان تقریبی بررسی: حداکثر 30 دقیقه",
                    parse_mode=ParseMode.HTML
                )
        else:
            await update.message.reply_text(
                f"⚠️ <b>خطا در تایید پرداخت:</b>\n{message}\n\n"
                "لطفا اطلاعات را بررسی کرده و مجددا تلاش کنید یا با پشتیبانی تماس بگیرید.",
                parse_mode=ParseMode.HTML
            )
            return CONFIRMING_PAYMENT
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.exception(f"Error in payment verification: {str(e)}")
        await update.message.reply_text(
            f"⚠️ خطایی در تایید پرداخت رخ داد: {str(e)}\n"
            "لطفا بعدا مجددا تلاش کنید یا با پشتیبانی تماس بگیرید.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    user = update.message.from_user
    logger.info(f"User {user.id} canceled the buy conversation")
    await update.message.reply_text(
        "❌ عملیات خرید لغو شد."
    )
    return ConversationHandler.END

# Create the buy conversation handler
buy_handler = ConversationHandler(
    entry_points=[CommandHandler("buy", buy_command)],
    states={
        SELECTING_PLAN: [
            CallbackQueryHandler(plan_selection, pattern=r"^plan_\d+$|^cancel$")
        ],
        SELECTING_PAYMENT_METHOD: [
            CallbackQueryHandler(
                payment_method_selection, 
                pattern=r"^payment_\w+$|^back_to_plans$|^discount$"
            )
        ],
        CONFIRMING_PAYMENT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, apply_discount),
            MessageHandler(~filters.COMMAND, process_verification)
        ],
        VERIFYING_PAYMENT: [
            CallbackQueryHandler(
                verify_payment, 
                pattern=r"^verify_payment$|^cancel_payment$|^back_to_payment_methods$"
            )
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
) 