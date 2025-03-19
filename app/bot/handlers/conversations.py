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
    get_plan_keyboard,
    get_location_keyboard,
    get_payment_keyboard,
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
        message = (
            "👋 به MoonVPN خوش آمدید!\n\n"
            "برای ثبت نام، لطفاً شماره موبایل خود را به فرمت زیر وارد کنید:\n"
            "+98XXXXXXXXXX\n\n"
            "مثال: +989123456789\n\n"
            "نکته: فقط شماره‌های موبایل ایران پذیرفته می‌شوند."
        )
        
        await update.message.reply_text(message)
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
        user = update.effective_user
        phone = update.message.text.strip()
        
        # Validate phone number format
        if not phone.startswith("+98") or not phone[3:].isdigit() or len(phone) != 13:
            await update.message.reply_text(
                "❌ فرمت شماره موبایل نامعتبر است.\n\n"
                "لطفاً یک شماره موبایل معتبر ایرانی که با +98 شروع می‌شود وارد کنید.\n"
                "مثال: +989123456789"
            )
            return RegistrationState.PHONE
        
        # Store phone number in context
        context.user_data["phone"] = phone
        
        # TODO: Send verification code
        message = (
            "✅ شماره موبایل دریافت شد!\n\n"
            "کد تایید به شماره شما ارسال شد.\n"
            "لطفاً کد 6 رقمی را وارد کنید:"
        )
        
        await update.message.reply_text(message)
        logger.info(f"User {user.id} provided phone number: {phone}")
        
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
        user = update.effective_user
        code = update.message.text.strip()
        
        # TODO: Verify code
        # For now, accept any 6-digit code
        if not code.isdigit() or len(code) != 6:
            await update.message.reply_text(
                "❌ کد تایید نامعتبر است.\n\n"
                "لطفاً کد 6 رقمی ارسال شده به موبایل خود را وارد کنید."
            )
            return RegistrationState.VERIFY
        
        # TODO: Create user profile
        message = (
            "🎉 ثبت نام با موفقیت انجام شد!\n\n"
            "حساب کاربری شما ایجاد شد.\n"
            "حالا می‌توانید از تمام امکانات MoonVPN استفاده کنید.\n\n"
            "دستورات موجود:\n"
            "/start - شروع کار\n"
            "/buy - خرید اشتراک\n"
            "/status - وضعیت حساب\n"
            "/settings - تنظیمات"
        )
        
        await update.message.reply_text(message)
        logger.info(f"User {user.id} completed registration")
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_verification: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

async def start_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the purchase process."""
    try:
        user = update.effective_user
        keyboard = get_plan_keyboard()
        
        message = (
            "🛍️ انتخاب پلن VPN\n\n"
            "لطفاً پلن مورد نظر خود را انتخاب کنید:\n\n"
            "💡 نکات مهم:\n"
            "• قیمت‌ها به تومان می‌باشد\n"
            "• پلن‌ها به صورت خودکار تمدید می‌شوند\n"
            "• امکان تغییر پلن در هر زمان وجود دارد"
        )
        
        await update.message.reply_text(message, reply_markup=keyboard)
        logger.info(f"User {user.id} started purchase flow")
        
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
        
        user = update.effective_user
        plan_id = query.data.split(":")[1]
        
        # Store selected plan in context
        context.user_data["plan_id"] = plan_id
        
        # Get available locations
        db = next(get_db())
        locations = await vpn_service.get_available_locations(db)
        
        # Create location keyboard
        keyboard = get_location_keyboard()
        
        message = (
            "🌍 انتخاب سرور\n\n"
            "لطفاً کشور مورد نظر خود را انتخاب کنید:\n\n"
            "💡 نکات مهم:\n"
            "• سرورها به صورت خودکار متعادل می‌شوند\n"
            "• امکان تغییر سرور در هر زمان وجود دارد\n"
            "• سرعت و پایداری سرورها به صورت مداوم بررسی می‌شود"
        )
        
        await query.edit_message_text(message, reply_markup=keyboard)
        logger.info(f"User {user.id} selected plan: {plan_id}")
        
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
        
        user = update.effective_user
        location_id = query.data.split(":")[1]
        
        # Store selected location in context
        context.user_data["location_id"] = location_id
        
        # Get payment keyboard
        keyboard = get_payment_keyboard()
        
        message = (
            "💳 انتخاب روش پرداخت\n\n"
            "لطفاً روش پرداخت مورد نظر خود را انتخاب کنید:\n\n"
            "💡 نکات مهم:\n"
            "• پرداخت از طریق کیف پول: سریع و بدون کارمزد\n"
            "• پرداخت با کارت: امن و سریع\n"
            "• پرداخت با زرین‌پال: امن و مطمئن\n"
            "• پرداخت با واریز مستقیم: بدون کارمزد"
        )
        
        await query.edit_message_text(message, reply_markup=keyboard)
        logger.info(f"User {user.id} selected location: {location_id}")
        
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
        
        user = update.effective_user
        payment_method = query.data.split(":")[1]
        
        # Store payment method in context
        context.user_data["payment_method"] = payment_method
        
        # Get order details from context
        plan_id = context.user_data.get("plan_id")
        location_id = context.user_data.get("location_id")
        
        # Get plan price
        db = next(get_db())
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Create order
        order = Order(
            id=str(uuid.uuid4()),
            user_id=user.id,
            plan_id=plan_id,
            location_id=location_id,
            amount=plan.price,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db.add(order)
        db.commit()
        
        # Process payment
        payment_result = await payment_service.process_payment(
            user_id=user.id,
            amount=plan.price,
            payment_method=payment_method,
            order_id=order.id,
            db=db
        )
        
        # Create confirmation message based on payment method
        if payment_method == "wallet":
            message = (
                "✅ پرداخت موفقیت‌آمیز!\n\n"
                f"مبلغ: {plan.price:,} تومان\n"
                f"شناسه تراکنش: {payment_result['transaction_id']}\n\n"
                "لطفاً سفارش خود را تأیید کنید:"
            )
        elif payment_method == "bank":
            bank_details = payment_result["bank_details"]
            message = (
                "🏦 اطلاعات واریز بانکی\n\n"
                f"بانک: {bank_details['bank_name']}\n"
                f"شماره حساب: {bank_details['account_number']}\n"
                f"صاحب حساب: {bank_details['account_holder']}\n"
                f"توضیحات: {bank_details['description']}\n\n"
                "💡 نکات مهم:\n"
                "• لطفاً مبلغ را به حساب فوق واریز کنید\n"
                "• پس از واریز، سفارش خود را تأیید کنید\n"
                "• تراکنش شما پس از تأیید بررسی خواهد شد"
            )
        elif payment_method == "zarinpal":
            message = (
                "💳 پرداخت با زرین‌پال\n\n"
                f"مبلغ: {plan.price:,} تومان\n"
                f"شناسه تراکنش: {payment_result['transaction_id']}\n\n"
                "لطفاً روی دکمه زیر کلیک کنید تا به درگاه پرداخت هدایت شوید:"
            )
            
            # Create payment button
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💳 پرداخت با زرین‌پال",
                        url=payment_result["payment_url"]
                    )
                ],
                [
                    InlineKeyboardButton("✅ تأیید", callback_data="confirm:yes"),
                    InlineKeyboardButton("❌ انصراف", callback_data="confirm:no")
                ]
            ])
            
            await query.edit_message_text(message, reply_markup=keyboard)
            return PurchaseState.CONFIRM
        else:  # card payment
            message = (
                "💳 پرداخت موفقیت‌آمیز!\n\n"
                f"مبلغ: {plan.price:,} تومان\n"
                f"شناسه تراکنش: {payment_result['transaction_id']}\n\n"
                "لطفاً سفارش خود را تأیید کنید:"
            )
        
        # Create confirmation keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تأیید", callback_data="confirm:yes"),
                InlineKeyboardButton("❌ انصراف", callback_data="confirm:no")
            ]
        ])
        
        await query.edit_message_text(message, reply_markup=keyboard)
        logger.info(f"User {user.id} selected payment method: {payment_method}")
        
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
        
        user = update.effective_user
        confirm = query.data.split(":")[1]
        
        if confirm == "no":
            message = "❌ سفارش لغو شد."
            await query.edit_message_text(message)
            logger.info(f"User {user.id} cancelled order")
            return ConversationHandler.END
        
        # Get order details from context
        plan_id = context.user_data.get("plan_id")
        location_id = context.user_data.get("location_id")
        payment_method = context.user_data.get("payment_method")
        
        # Create VPN account
        db = next(get_db())
        account = await vpn_service.create_account(
            user_id=user.id,
            plan_id=plan_id,
            location_id=location_id,
            db=db
        )
        
        # Get account configuration
        config = await vpn_service.get_account_config(account.id, db)
        
        # Create success message with configuration
        message = (
            "🎉 سفارش شما با موفقیت ثبت شد!\n\n"
            "حساب VPN شما ایجاد شد.\n\n"
            "🔧 اطلاعات اتصال:\n"
            f"سرور: {config['server']}\n"
            f"پورت: {config['port']}\n"
            f"پروتکل: {config['protocol']}\n\n"
            "📧 جزئیات کامل تنظیمات به ایمیل شما ارسال شد.\n\n"
            "💡 نکات مهم:\n"
            "• لطفاً تنظیمات را در دستگاه خود ذخیره کنید\n"
            "• در صورت نیاز به راهنمایی، از دستور /help استفاده کنید\n"
            "• برای مشاهده وضعیت حساب از دستور /status استفاده کنید"
        )
        
        await query.edit_message_text(message)
        logger.info(f"User {user.id} confirmed order and created account {account.id}")
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_confirmation: {str(e)}")
        await query.edit_message_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        return ConversationHandler.END

# Create conversation handlers
registration_handler = ConversationHandler(
    entry_points=[CommandHandler("register", start_registration)],
    states={
        RegistrationState.PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
        ],
        RegistrationState.VERIFY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification)
        ],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
)

purchase_handler = ConversationHandler(
    entry_points=[CommandHandler("buy", start_purchase)],
    states={
        PurchaseState.PLAN: [
            CallbackQueryHandler(handle_plan_selection, pattern="^plan:")
        ],
        PurchaseState.LOCATION: [
            CallbackQueryHandler(handle_location_selection, pattern="^location:")
        ],
        PurchaseState.PAYMENT: [
            CallbackQueryHandler(handle_payment_selection, pattern="^payment:")
        ],
        PurchaseState.CONFIRM: [
            CallbackQueryHandler(handle_confirmation, pattern="^confirm:")
        ],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
) 