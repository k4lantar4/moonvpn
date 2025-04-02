import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    CallbackQuery
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters
)

from app.core.config import settings
from app.utils.api_client import get_user_by_telegram_id
from app.api import api_client
from app.api.api_client import payments_client, order_client, user_client, plan_client, subscription_client
from app.models.order import PaymentMethod, OrderStatus

# Define conversation states
WAITING_FOR_PAYMENT = 1
PAYMENT_COMPLETED = 2

# Callback data patterns
CANCEL_ORDER_CALLBACK = "cancel_order"
CHECK_PAYMENT_STATUS_CALLBACK = "check_zarinpal_payment"

# Get logger
logger = logging.getLogger(__name__)

# Store active Zarinpal payment sessions
# Structure: {user_id: {"order_id": order_id, "check_count": int, "last_check": datetime}}
active_zarinpal_payments = {}

# Constants
MAX_STATUS_CHECKS = 10  # Maximum number of times to check payment status
CHECK_INTERVAL = 30  # Seconds between status checks
PAYMENT_TIMEOUT = 900  # 15 minutes payment timeout

async def initiate_zarinpal_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Initiates a Zarinpal payment for the selected plan.
    This should be called after the user selects Zarinpal as their payment method.
    """
    query = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not query:
        # Handle direct command case (unlikely but possible)
        await update.message.reply_text("⚠️ لطفاً از منوی خرید سرویس استفاده کنید.")
        return ConversationHandler.END
        
    await query.answer()
    
    plan_id = context.user_data.get('selected_plan_id')
    user_id = context.user_data.get('user_id')
    
    if not plan_id or not user_id:
        logger.error(f"Missing plan_id or user_id in Zarinpal handler for user {user.id}")
        await query.edit_message_text("❌ اطلاعات سفارش یافت نشد، لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END
    
    # Show processing message
    await query.edit_message_text("⏳ در حال ایجاد سفارش و دریافت لینک پرداخت زرین‌پال...")
    
    try:
        # 1. Create the order with Zarinpal method
        order = await order_client.create_order(
            user_id=user_id,
            plan_id=plan_id,
            payment_method=PaymentMethod.ZARINPAL.value
        )
        
        if not order or not order.get("id"):
            logger.error(f"Failed to create order for user {user_id}, plan {plan_id}")
            await query.edit_message_text("❌ خطا در ایجاد سفارش. لطفاً دوباره تلاش کنید.")
            return ConversationHandler.END
        
        order_id = order["id"]
        context.user_data["order_id"] = order_id
        final_amount = order.get("final_amount", 0)
        
        logger.info(f"Order {order_id} created for user {user_id} with Zarinpal payment method")
        
        # 2. Request payment URL from API
        try:
            payment_url = await payments_client.request_zarinpal_payment(order_id)
            
            # 3. Store payment session info
            active_zarinpal_payments[user.id] = {
                "order_id": order_id,
                "check_count": 0,
                "last_check": datetime.now(),
                "started_at": datetime.now(),
                "message_id": None  # Will be updated after sending
            }
            
            # 4. Create payment message with buttons
            keyboard = [
                [InlineKeyboardButton("🚀 پرداخت آنلاین", url=payment_url)],
                [InlineKeyboardButton("🔄 بررسی وضعیت پرداخت", callback_data=CHECK_PAYMENT_STATUS_CALLBACK)],
                [InlineKeyboardButton("❌ لغو سفارش", callback_data=CANCEL_ORDER_CALLBACK)]
            ]
            
            message = (
                f"✅ سفارش شما با موفقیت ثبت شد (شماره: `{order_id}`).\n\n"
                f"💰 مبلغ قابل پرداخت: *{final_amount:,} تومان*\n\n"
                f"👈 لطفاً برای تکمیل پرداخت روی دکمه «پرداخت آنلاین» کلیک کنید.\n\n"
                f"⚠️ *توجه:* پس از پرداخت موفق در صفحه زرین‌پال، به ربات بازگردید و دکمه «بررسی وضعیت پرداخت» را بزنید.\n\n"
                f"⏱ مهلت پرداخت: *15 دقیقه*"
            )
            
            sent_message = await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            # Update message_id in active payments
            if user.id in active_zarinpal_payments:
                active_zarinpal_payments[user.id]["message_id"] = sent_message.message_id
            
            # Schedule automatic order cancellation if payment not completed
            context.job_queue.run_once(
                cancel_expired_payment,
                PAYMENT_TIMEOUT,
                data={"user_id": user.id, "chat_id": chat_id, "order_id": order_id}
            )
            
            return WAITING_FOR_PAYMENT
            
        except Exception as e:
            logger.error(f"Error requesting Zarinpal payment URL for order {order_id}: {e}")
            await query.edit_message_text(
                "❌ خطا در دریافت لینک پرداخت. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
                ]])
            )
            return ConversationHandler.END
            
    except Exception as e:
        logger.exception(f"Unexpected error initiating Zarinpal payment for user {user.id}: {e}")
        await query.edit_message_text(
            "❌ خطایی در فرآیند پرداخت رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
            ]])
        )
        return ConversationHandler.END

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Checks the status of a Zarinpal payment when the user clicks the button.
    """
    query = update.callback_query
    user = update.effective_user
    
    await query.answer("درحال بررسی وضعیت پرداخت...")
    
    # Verify we have an active payment session for this user
    if user.id not in active_zarinpal_payments:
        await query.edit_message_text(
            "❌ اطلاعات پرداخت شما یافت نشد. لطفاً دوباره از منوی خرید اقدام کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
            ]])
        )
        return ConversationHandler.END
    
    payment_data = active_zarinpal_payments[user.id]
    order_id = payment_data["order_id"]
    
    # Check if we've exceeded maximum checks
    if payment_data["check_count"] >= MAX_STATUS_CHECKS:
        await query.edit_message_text(
            "⚠️ تعداد دفعات بررسی وضعیت پرداخت به حداکثر رسیده است.\n\n"
            "اگر پرداخت را انجام داده‌اید اما سیستم آن را تشخیص نمی‌دهد، لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
            ]])
        )
        # Clean up the session
        if user.id in active_zarinpal_payments:
            del active_zarinpal_payments[user.id]
        return ConversationHandler.END
    
    # Check if enough time has passed since last check
    time_since_last_check = (datetime.now() - payment_data["last_check"]).total_seconds()
    if time_since_last_check < CHECK_INTERVAL:
        await query.answer(
            f"لطفاً {CHECK_INTERVAL - int(time_since_last_check)} ثانیه صبر کنید و دوباره تلاش کنید.",
            show_alert=True
        )
        return WAITING_FOR_PAYMENT
    
    # Update check count and last check time
    payment_data["check_count"] += 1
    payment_data["last_check"] = datetime.now()
    
    # Display checking message
    await query.edit_message_text(
        f"⏳ درحال بررسی وضعیت پرداخت سفارش #{order_id}...\n\n"
        "لطفاً چند لحظه صبر کنید.",
        reply_markup=None
    )
    
    try:
        # Get current order status from API
        order = await order_client.get_order(order_id)
        
        if not order:
            logger.error(f"Order {order_id} not found during payment status check")
            await query.edit_message_text(
                "❌ اطلاعات سفارش یافت نشد. لطفاً با پشتیبانی تماس بگیرید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
                ]])
            )
            return ConversationHandler.END
        
        order_status = order.get("status")
        
        # Check if payment was successful (order status is PAID or higher)
        if order_status == OrderStatus.PAID.value or order_status == OrderStatus.COMPLETED.value:
            # Payment successful! Get subscription details if available
            subscription_id = order.get("subscription_id")
            subscription_details = None
            
            if subscription_id:
                try:
                    subscription_details = await subscription_client.get_subscription(subscription_id)
                except Exception as sub_error:
                    logger.error(f"Error getting subscription details for order {order_id}: {sub_error}")
            
            # Clean up the session
            if user.id in active_zarinpal_payments:
                del active_zarinpal_payments[user.id]
            
            # Show success message with subscription details if available
            success_message = (
                f"✅ پرداخت شما با موفقیت انجام شد!\n\n"
                f"🛍️ شماره سفارش: `{order_id}`\n"
                f"💰 مبلغ پرداخت شده: *{order.get('final_amount', 0):,} تومان*\n"
                f"🕒 تاریخ پرداخت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            
            if subscription_details:
                # Add subscription details
                success_message += (
                    f"📡 *اطلاعات سرویس شما:*\n"
                    f"🔹 نام سرویس: {subscription_details.get('plan_name', 'نامشخص')}\n"
                    f"🔹 تاریخ انقضا: {subscription_details.get('expiry_date', 'نامشخص')}\n"
                    f"🔹 پروتکل: {subscription_details.get('protocol', 'نامشخص')}\n\n"
                    f"برای مشاهده اطلاعات اتصال و QR کد از منوی «حساب‌های من» اقدام کنید."
                )
            else:
                success_message += (
                    "⏳ سرویس شما در حال آماده‌سازی است و به زودی فعال خواهد شد.\n"
                    "لطفاً چند دقیقه دیگر از طریق منوی «حساب‌های من» سرویس خود را مشاهده نمایید."
                )
            
            await query.edit_message_text(
                success_message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
                ]]),
                parse_mode="Markdown"
            )
            
            return ConversationHandler.END
            
        elif order_status == OrderStatus.FAILED.value:
            # Payment failed
            await query.edit_message_text(
                "❌ متأسفانه پرداخت شما ناموفق بود.\n\n"
                "دلیل: پرداخت در درگاه زرین‌پال تکمیل نشده یا با خطا مواجه شده است.\n\n"
                "می‌توانید مجدداً از منوی خرید سرویس اقدام نمایید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
                ]])
            )
            
            # Clean up the session
            if user.id in active_zarinpal_payments:
                del active_zarinpal_payments[user.id]
                
            return ConversationHandler.END
            
        else:
            # Payment still pending - recreate the original message with payment buttons
            original_message = (
                f"👇 وضعیت پرداخت سفارش #{order_id}:\n\n"
                f"⏳ *در انتظار پرداخت*\n\n"
                f"💰 مبلغ قابل پرداخت: *{order.get('final_amount', 0):,} تومان*\n\n"
                f"بررسی شده در: {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"⚠️ اگر پرداخت را انجام داده‌اید، چند دقیقه صبر کنید و سپس دکمه «بررسی وضعیت پرداخت» را مجدداً بزنید."
            )
            
            # Get the original payment URL to offer payment option again
            try:
                payment_url = await payments_client.request_zarinpal_payment(order_id)
                keyboard = [
                    [InlineKeyboardButton("🚀 پرداخت آنلاین", url=payment_url)],
                    [InlineKeyboardButton("🔄 بررسی وضعیت پرداخت", callback_data=CHECK_PAYMENT_STATUS_CALLBACK)],
                    [InlineKeyboardButton("❌ لغو سفارش", callback_data=CANCEL_ORDER_CALLBACK)]
                ]
            except Exception as e:
                # If we can't get the payment URL again, just show status check button
                logger.error(f"Error re-requesting payment URL: {e}")
                keyboard = [
                    [InlineKeyboardButton("🔄 بررسی وضعیت پرداخت", callback_data=CHECK_PAYMENT_STATUS_CALLBACK)],
                    [InlineKeyboardButton("❌ لغو سفارش", callback_data=CANCEL_ORDER_CALLBACK)]
                ]
            
            await query.edit_message_text(
                original_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            return WAITING_FOR_PAYMENT
            
    except Exception as e:
        logger.exception(f"Error checking payment status for order {order_id}: {e}")
        
        # Show error but allow retrying
        await query.edit_message_text(
            f"❌ خطا در بررسی وضعیت پرداخت: {str(e)}\n\n"
            "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data=CHECK_PAYMENT_STATUS_CALLBACK)],
                [InlineKeyboardButton("❌ لغو سفارش", callback_data=CANCEL_ORDER_CALLBACK)]
            ])
        )
        
        return WAITING_FOR_PAYMENT

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current order and payment process."""
    query = update.callback_query
    user = update.effective_user
    
    await query.answer("در حال لغو سفارش...")
    
    # Clean up the session
    if user.id in active_zarinpal_payments:
        order_id = active_zarinpal_payments[user.id]["order_id"]
        del active_zarinpal_payments[user.id]
        
        # Try to cancel the order on the backend
        try:
            await order_client.cancel_order(order_id)
            logger.info(f"Order {order_id} cancelled by user {user.id}")
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
    
    await query.edit_message_text(
        "❌ سفارش لغو شد.\n\n"
        "می‌توانید مجدداً از منوی خرید سرویس اقدام نمایید.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
        ]])
    )
    
    return ConversationHandler.END

async def cancel_expired_payment(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Automatically cancels an expired payment after the timeout period."""
    job_data = context.job.data
    user_id = job_data.get("user_id")
    chat_id = job_data.get("chat_id")
    order_id = job_data.get("order_id")
    
    if not user_id or not chat_id or not order_id:
        logger.error("Missing required data in cancel_expired_payment job")
        return
    
    # Check if payment is still active
    if user_id not in active_zarinpal_payments or active_zarinpal_payments[user_id]["order_id"] != order_id:
        # Payment already completed or cancelled
        return
    
    # Try to get the message ID to update
    message_id = active_zarinpal_payments[user_id].get("message_id")
    
    # Clean up the session
    del active_zarinpal_payments[user_id]
    
    # Try to cancel the order on the backend
    try:
        await order_client.cancel_order(order_id)
        logger.info(f"Order {order_id} auto-cancelled due to payment timeout")
    except Exception as e:
        logger.error(f"Error auto-cancelling order {order_id}: {e}")
    
    # Try to update the message if we have its ID
    if message_id:
        try:
            await context.bot.edit_message_text(
                "⏱ زمان پرداخت به پایان رسید و سفارش لغو شد.\n\n"
                "می‌توانید مجدداً از منوی خرید سرویس اقدام نمایید.",
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
                ]])
            )
        except Exception as e:
            logger.error(f"Error updating expired payment message: {e}")

# Setup handlers
zarinpal_handler = CallbackQueryHandler(
    initiate_zarinpal_payment,
    pattern=f"^payment_method_{PaymentMethod.ZARINPAL.value}$"
)

zarinpal_conversation = ConversationHandler(
    entry_points=[zarinpal_handler],
    states={
        WAITING_FOR_PAYMENT: [
            CallbackQueryHandler(check_payment_status, pattern=f"^{CHECK_PAYMENT_STATUS_CALLBACK}$"),
            CallbackQueryHandler(cancel_order, pattern=f"^{CANCEL_ORDER_CALLBACK}$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel_order, pattern=f"^{CANCEL_ORDER_CALLBACK}$")]
) 