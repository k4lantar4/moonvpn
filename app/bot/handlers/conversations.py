"""
Conversation handlers for MoonVPN Telegram Bot.

This module implements conversation flows for user registration,
purchase process, and other multi-step interactions.
"""

from enum import Enum
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from app.bot.utils.logger import setup_logger
from app.bot.keyboards import (
    get_plan_selection_keyboard,
    get_location_selection_keyboard,
    get_payment_method_keyboard,
    get_confirmation_keyboard,
)
from app.bot.services.vpn_service import VPNService
from app.bot.services.payment_service import PaymentService
from app.core.database.session import get_db

# Initialize logger and services
logger = setup_logger(__name__)
vpn_service = VPNService()
payment_service = PaymentService()

# Conversation states
class RegistrationState(Enum):
    """States for user registration flow."""
    PHONE = 1
    VERIFY = 2
    COMPLETE = 3

class PurchaseState(Enum):
    """States for purchase flow."""
    PLAN = 1
    LOCATION = 2
    PAYMENT = 3
    CONFIRM = 4

# Conversation handlers
async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration process."""
    try:
        user = update.effective_user
        welcome_message = (
            "👋 *به MoonVPN خوش آمدید*\n\n"
            "لطفاً شماره موبایل خود را به فرمت زیر وارد کنید:\n"
            "+98XXXXXXXXXX\n\n"
            "مثال: +989123456789"
        )
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )
        logger.info(f"User {user.id} started registration")
        return RegistrationState.PHONE
        
    except Exception as e:
        logger.error(f"Error in start_registration: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle phone number input."""
    try:
        phone = update.message.text.strip()
        if not phone.startswith('+98') or len(phone) != 13:
            await update.message.reply_text(
                "❌ فرمت شماره موبایل نامعتبر است.\n"
                "لطفاً یک شماره موبایل معتبر ایرانی که با +98 شروع می‌شود وارد کنید."
            )
            return RegistrationState.PHONE
            
        context.user_data['phone'] = phone
        # TODO: Implement SMS verification
        verification_message = (
            "✅ شماره موبایل دریافت شد!\n\n"
            "لطفاً کد تأیید ارسال شده به موبایل خود را وارد کنید:"
        )
        
        await update.message.reply_text(verification_message)
        return RegistrationState.VERIFY
        
    except Exception as e:
        logger.error(f"Error in handle_phone: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle verification code input."""
    try:
        code = update.message.text.strip()
        # TODO: Verify the code
        if code != "123456":  # Placeholder verification
            await update.message.reply_text(
                "❌ کد تأیید نامعتبر است.\n"
                "لطفاً دوباره تلاش کنید:"
            )
            return RegistrationState.VERIFY
            
        # TODO: Create user account
        success_message = (
            "✅ ثبت نام با موفقیت انجام شد!\n\n"
            "حالا می‌توانید یک اشتراک VPN خریداری کنید."
        )
        
        await update.message.reply_text(success_message)
        return RegistrationState.COMPLETE
        
    except Exception as e:
        logger.error(f"Error in handle_verification: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

async def start_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the purchase process."""
    try:
        # TODO: Fetch available plans from database
        plans = [
            {"id": 1, "name": "۱ ماهه", "price": 99000},
            {"id": 2, "name": "۳ ماهه", "price": 249000},
            {"id": 3, "name": "۶ ماهه", "price": 449000},
            {"id": 4, "name": "۱ ساله", "price": 799000},
        ]
        
        plan_message = (
            "🛍️ *انتخاب پلن VPN*\n\n"
            "لطفاً پلن مورد نظر خود را انتخاب کنید:"
        )
        
        await update.message.reply_text(
            plan_message,
            parse_mode='Markdown',
            reply_markup=get_plan_selection_keyboard(plans)
        )
        return PurchaseState.PLAN
        
    except Exception as e:
        logger.error(f"Error in start_purchase: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan selection."""
    try:
        query = update.callback_query
        await query.answer()
        
        plan_id = int(query.data.split('_')[1])
        context.user_data['plan_id'] = plan_id
        
        # TODO: Fetch available locations from database
        locations = [
            {"id": 1, "name": "آمریکا", "flag": "🇺🇸"},
            {"id": 2, "name": "انگلیس", "flag": "🇬🇧"},
            {"id": 3, "name": "آلمان", "flag": "🇩🇪"},
            {"id": 4, "name": "فرانسه", "flag": "🇫🇷"},
        ]
        
        location_message = (
            "🌍 *انتخاب سرور*\n\n"
            "لطفاً سرور مورد نظر خود را انتخاب کنید:"
        )
        
        await query.edit_message_text(
            location_message,
            parse_mode='Markdown',
            reply_markup=get_location_selection_keyboard(locations)
        )
        return PurchaseState.LOCATION
        
    except Exception as e:
        logger.error(f"Error in handle_plan_selection: {str(e)}")
        await query.edit_message_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

async def handle_location_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location selection."""
    try:
        query = update.callback_query
        await query.answer()
        
        location_id = int(query.data.split('_')[1])
        context.user_data['location_id'] = location_id
        
        payment_message = (
            "💳 *انتخاب روش پرداخت*\n\n"
            "لطفاً روش پرداخت مورد نظر خود را انتخاب کنید:"
        )
        
        await query.edit_message_text(
            payment_message,
            parse_mode='Markdown',
            reply_markup=get_payment_method_keyboard()
        )
        return PurchaseState.PAYMENT
        
    except Exception as e:
        logger.error(f"Error in handle_location_selection: {str(e)}")
        await query.edit_message_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

async def handle_payment_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method selection."""
    try:
        query = update.callback_query
        await query.answer()
        
        payment_method = query.data.split('_')[1]
        context.user_data['payment_method'] = payment_method
        
        # TODO: Calculate total price
        total_price = 99000  # Placeholder
        
        confirmation_message = (
            "📝 *خلاصه سفارش*\n\n"
            f"پلن: {context.user_data.get('plan_id')}\n"
            f"سرور: {context.user_data.get('location_id')}\n"
            f"روش پرداخت: {payment_method}\n"
            f"مبلغ کل: {total_price} تومان\n\n"
            "لطفاً سفارش خود را تأیید کنید:"
        )
        
        await query.edit_message_text(
            confirmation_message,
            parse_mode='Markdown',
            reply_markup=get_confirmation_keyboard()
        )
        return PurchaseState.CONFIRM
        
    except Exception as e:
        logger.error(f"Error in handle_payment_selection: {str(e)}")
        await query.edit_message_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle order confirmation."""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text(
                "❌ سفارش لغو شد.\n"
                "برای شروع سفارش جدید از دستور /buy استفاده کنید."
            )
            return ConversationHandler.END
            
        # TODO: Process payment and create VPN account
        success_message = (
            "✅ *سفارش تأیید شد!*\n\n"
            "حساب VPN شما به زودی ایجاد خواهد شد.\n"
            "برای بررسی وضعیت حساب از دستور /status استفاده کنید."
        )
        
        await query.edit_message_text(
            success_message,
            parse_mode='Markdown'
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_confirmation: {str(e)}")
        await query.edit_message_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    try:
        await update.message.reply_text(
            "❌ عملیات لغو شد.\n"
            "برای شروع مجدد از دستور /start استفاده کنید."
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in cancel: {str(e)}")
        return ConversationHandler.END

# Create conversation handlers
registration_handler = ConversationHandler(
    entry_points=[CommandHandler('register', start_registration)],
    states={
        RegistrationState.PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
        RegistrationState.VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

purchase_handler = ConversationHandler(
    entry_points=[CommandHandler('buy', start_purchase)],
    states={
        PurchaseState.PLAN: [CallbackQueryHandler(handle_plan_selection, pattern='^plan_')],
        PurchaseState.LOCATION: [CallbackQueryHandler(handle_location_selection, pattern='^location_')],
        PurchaseState.PAYMENT: [CallbackQueryHandler(handle_payment_selection, pattern='^payment_')],
        PurchaseState.CONFIRM: [CallbackQueryHandler(handle_confirmation, pattern='^(confirm|cancel)$')],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
) 