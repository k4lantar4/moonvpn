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
from app.core.services.sms_service import SMSService
from app.core.database.session import get_db

# Initialize logger and services
logger = setup_logger(__name__)
vpn_service = VPNService()
payment_service = PaymentService()
sms_service = SMSService(next(get_db()))

# Conversation states
class RegistrationState(Enum):
    """States for user registration flow."""
    PHONE = 1
    VERIFY = 2
    COMPLETE = 3

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
        
        # Send verification code
        success, error = await sms_service.send_verification_code(phone)
        
        if not success:
            logger.error(f"Failed to send verification code: {error}")
            await update.message.reply_text(
                "❌ متأسفانه در ارسال کد تأیید مشکلی پیش آمد.\n"
                "لطفاً دوباره تلاش کنید."
            )
            return RegistrationState.PHONE
            
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
        phone = context.user_data.get('phone')
        
        if not phone:
            await update.message.reply_text(
                "❌ شماره موبایل یافت نشد.\n"
                "لطفاً دوباره از ابتدا شروع کنید."
            )
            return ConversationHandler.END
            
        # Verify code
        success, error = await sms_service.verify_code(phone, code)
        
        if not success:
            await update.message.reply_text(
                f"❌ {error}\n"
                "لطفاً دوباره تلاش کنید:"
            )
            return RegistrationState.VERIFY
            
        # Create user account
        db = next(get_db())
        user = User(
            phone=phone,
            is_phone_verified=True,
            language="fa"
        )
        db.add(user)
        db.commit()
        
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

# Register conversation handlers
registration_handler = ConversationHandler(
    entry_points=[CommandHandler("start", handle_phone)],
    states={
        RegistrationState.PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
        RegistrationState.VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    name="registration",
    persistent=True
) 