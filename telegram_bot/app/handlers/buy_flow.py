import logging
from datetime import datetime
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

from app.core.config import MANAGE_GROUP_ID
from app.utils.api_client import get_user_by_telegram_id
from app.api import api_client
from app.keyboards.payment import generate_payment_method_keyboard
from app.api.api_client import payments_client, order_client, user_client, plan_client
from app.models.order import PaymentMethod

# Define conversation states
SELECTING_PAYMENT_METHOD = 1
WAITING_FOR_PAYMENT_PROOF = 2
CONFIRMING_PAYMENT = 3
PROCESSING_ZARINPAL = 4

# Callback data patterns
PLAN_CALLBACK_PREFIX = "buy_plan_"
PAYMENT_METHOD_CALLBACK_PREFIX = "payment_method_"
CANCEL_ORDER_CALLBACK = "cancel_order"
CONFIRM_PAYMENT_CALLBACK_PREFIX = "confirm_payment_"
REJECT_PAYMENT_CALLBACK_PREFIX = "reject_payment_"

# Get logger
logger = logging.getLogger(__name__)

# Store user orders in memory (temporary solution - in production, use a database)
# Structure: {user_id: {"order_id": order_id, "payment_method": method, "message_id": msg_id}}
active_orders = {}

# Import the Zarinpal handler
from app.handlers.zarinpal_handler import zarinpal_conversation

async def handle_buy_plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callback when user selects a plan to purchase."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not user:
        logger.error("User not found in buy plan callback")
        return ConversationHandler.END
        
    # Extract plan_id from callback data (format: "buy_plan_123")
    callback_data = query.data
    if not callback_data.startswith(PLAN_CALLBACK_PREFIX):
        logger.error(f"Invalid callback data in buy plan: {callback_data}")
        return ConversationHandler.END
        
    try:
        plan_id = int(callback_data[len(PLAN_CALLBACK_PREFIX):])
    except ValueError:
        logger.error(f"Invalid plan ID in callback: {callback_data}")
        await query.edit_message_text("❌ خطایی رخ داد، لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END
    
    # Store plan_id in context
    context.user_data["selected_plan_id"] = plan_id
    
    # Get user info to get the user ID
    try:
        # Use the user_client
        user_info = await user_client.get_user_by_telegram_id(user.id)
        if not user_info or "id" not in user_info:
            logger.error(f"Could not get user info for user {user.id}")
            await query.edit_message_text("❌ اطلاعات کاربری شما یافت نشد. لطفاً با پشتیبانی تماس بگیرید.")
            return ConversationHandler.END
        context.user_data["user_id"] = user_info["id"]
    except Exception as e:
        logger.error(f"API Error getting user info for {user.id}: {e}")
        await query.edit_message_text(f"❌ خطای ارتباط با سرور: {str(e)}")
        return ConversationHandler.END
    
    # Get available payment methods using the payments_client
    try:
        # Use the new get_available_payment_methods function
        payment_methods = await payments_client.get_available_payment_methods()
        if not payment_methods:
            logger.error("No payment methods returned from API")
            await query.edit_message_text("❌ در حال حاضر امکان پرداخت فراهم نیست. لطفاً بعداً مجدد تلاش کنید.")
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        # Fallback to card-to-card only if API call fails
        payment_methods = [PaymentMethod.CARD_TO_CARD]
        # Don't terminate the flow, just show available methods
    
    # Show payment method selection
    keyboard = generate_payment_method_keyboard(payment_methods)
    
    # Add cancel button
    keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data=CANCEL_ORDER_CALLBACK)])
    
    await query.edit_message_text(
        "💳 *لطفاً روش پرداخت را انتخاب کنید:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return SELECTING_PAYMENT_METHOD

async def handle_payment_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle selected payment method (excluding Zarinpal, handled separately)."""
    query = update.callback_query
    user = update.effective_user
    await query.answer()
    
    if query.data == CANCEL_ORDER_CALLBACK:
        return await cancel_order(update, context)
        
    # Extract payment method
    if not query.data.startswith(PAYMENT_METHOD_CALLBACK_PREFIX):
        logger.warning(f"Invalid payment method callback data: {query.data}")
        return SELECTING_PAYMENT_METHOD # Stay in the same state
        
    payment_method_value = query.data[len(PAYMENT_METHOD_CALLBACK_PREFIX):]
    
    # --- IMPORTANT: Skip Zarinpal here, it will have its own handler --- 
    if payment_method_value == PaymentMethod.ZARINPAL.value:
        # This case should be handled by handle_zarinpal_payment
        logger.warning("Zarinpal callback received in general payment handler. Ignoring.")
        return SELECTING_PAYMENT_METHOD # Or perhaps ConversationHandler.END?

    # Get plan_id from context
    plan_id = context.user_data.get('selected_plan_id')
    if not plan_id:
        logger.error(f"No selected plan found for user {user.id}")
        await query.edit_message_text(
            "❌ اطلاعات پلن یافت نشد. لطفاً دوباره از منوی خرید اقدام کنید.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Get user_id from context
    user_id = context.user_data.get('user_id')
    if not user_id:
        logger.error(f"User ID not found in context for user {user.id}")
        await query.edit_message_text(
            "❌ اطلاعات کاربری شما یافت نشد. لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Create order (or maybe update payment method if order already created?)
    # Let's assume we create the order *after* method selection for non-instant payments
    try:
        order = await order_client.create_order(
            user_id=user_id,
            plan_id=plan_id,
            payment_method=payment_method_value
        )
        if not order:
            logger.error(f"Failed to create order for user {user_id}, plan {plan_id}")
            await query.edit_message_text(
                "❌ خطا در ایجاد سفارش. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                reply_markup=None
            )
            return ConversationHandler.END
            
        logger.info(f"Order {order['id']} created for user {user_id} with method {payment_method_value}")
        context.user_data["order_id"] = order["id"]
        context.user_data["amount"] = order.get("final_amount", 0) # Use final_amount

        # Handle different payment methods (excluding Zarinpal)
        if payment_method_value == PaymentMethod.CARD_TO_CARD.value:
            from app.handlers.payment_proof_handlers import start_card_payment
            # Pass order details needed for card payment
            return await start_card_payment(update, context)
            
        # elif payment_method_value == PaymentMethod.WALLET.value:
            # Handle wallet payment
        
        # elif payment_method_value == PaymentMethod.CRYPTO.value:
            # Handle crypto
            # ... (show message as before) ...
            # return ConversationHandler.END
            
        else:
            logger.warning(f"Unhandled payment method in callback: {payment_method_value}")
            await query.edit_message_text("❌ روش پرداخت انتخاب شده در حال حاضر قابل پردازش نیست.")
            return ConversationHandler.END

    except APIError as e:
        logger.error(f"API Error creating order or handling payment method {payment_method_value}: {e}")
        await query.edit_message_text(f"❌ خطای سرور: {e.message}")
        return ConversationHandler.END
    except Exception as e:
        logger.exception(f"Unexpected error handling payment method {payment_method_value}")
        await query.edit_message_text("❌ خطای پیش‌بینی نشده رخ داد.")
        return ConversationHandler.END

# --- Add New Handler for Zarinpal (keep existing code if any) --- 
async def handle_zarinpal_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the selection of Zarinpal payment method."""
    # This is now handled by zarinpal_handler.py's implementation
    # This stub is left for backward compatibility
    from app.handlers.zarinpal_handler import initiate_zarinpal_payment
    return await initiate_zarinpal_payment(update, context)

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle when user sends payment proof (image)."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not user:
        logger.error("User not found in payment proof handler")
        return ConversationHandler.END
    
    # Check if user has an active order
    if user.id not in active_orders:
        await update.message.reply_text("❌ سفارش فعالی یافت نشد. لطفاً ابتدا سفارش جدید ثبت کنید.")
        return ConversationHandler.END
    
    order_info = active_orders[user.id]
    order_id = order_info["order_id"]
    
    # Check if user sent a photo
    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ لطفاً تصویر رسید پرداخت را ارسال کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ انصراف از خرید", callback_data=CANCEL_ORDER_CALLBACK)
            ]])
        )
        return WAITING_FOR_PAYMENT_PROOF
    
    # Get the largest photo (best quality)
    photo = update.message.photo[-1]
    
    # Send confirmation message to user
    await update.message.reply_text(
        "✅ تصویر رسید پرداخت دریافت شد و در حال بررسی است.\n\n"
        "پس از تایید، اشتراک شما فعال خواهد شد.",
        reply_markup=InlineKeyboardMarkup([])
    )
    
    # In a real implementation, we would:
    # 1. Upload the image to the API
    # 2. Update the order with the payment proof
    
    # For this demo, we'll simulate forwarding to an admin group
    # and providing approve/reject buttons
    
    # This is where we would normally forward to MANAGE_GROUP_ID
    # For demo purposes, we'll just send to the same chat
    admin_message = await context.bot.send_photo(
        chat_id=chat_id,  # In production: MANAGE_GROUP_ID
        photo=photo.file_id,
        caption=(
            f"🧾 *تصویر پرداخت جدید*\n\n"
            f"📌 شماره سفارش: `{order_id}`\n"
            f"👤 کاربر: [{user.first_name}](tg://user?id={user.id})\n"
            f"⏱ زمان: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"👇 *لطفاً وضعیت پرداخت را مشخص کنید:*"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"{CONFIRM_PAYMENT_CALLBACK_PREFIX}{order_id}_{user.id}"),
                InlineKeyboardButton("❌ رد پرداخت", callback_data=f"{REJECT_PAYMENT_CALLBACK_PREFIX}{order_id}_{user.id}")
            ]
        ])
    )
    
    # Save the admin message ID for later reference
    active_orders[user.id]["admin_message_id"] = admin_message.message_id
    
    return CONFIRMING_PAYMENT

async def handle_admin_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin's confirmation or rejection of payment."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    admin = update.effective_user
    
    # Extract action and IDs
    if callback_data.startswith(CONFIRM_PAYMENT_CALLBACK_PREFIX):
        action = "confirm"
        data = callback_data[len(CONFIRM_PAYMENT_CALLBACK_PREFIX):]
    elif callback_data.startswith(REJECT_PAYMENT_CALLBACK_PREFIX):
        action = "reject"
        data = callback_data[len(REJECT_PAYMENT_CALLBACK_PREFIX):]
    else:
        logger.error(f"Invalid admin payment callback: {callback_data}")
        return
    
    # Parse order_id and user_id
    try:
        order_id, user_id = map(int, data.split("_"))
    except ValueError:
        logger.error(f"Invalid data format in admin payment callback: {data}")
        return
    
    # Update the admin message to show who processed it
    await query.edit_message_caption(
        caption=f"{query.message.caption}\n\n"
               f"🔄 {action.title()}ed by {admin.first_name}",
        parse_mode="Markdown",
        reply_markup=None
    )
    
    # Check if user still has an active order
    if int(user_id) not in active_orders:
        logger.warning(f"Order for user {user_id} not found in active_orders")
        # Inform the admin
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ سفارش کاربر دیگر فعال نیست یا قبلاً پردازش شده است."
        )
        return
    
    # Process the payment confirmation or rejection
    if action == "confirm":
        try:
            # Call API to confirm payment and create the client on panel
            admin_note = f"Payment confirmed by admin {admin.first_name} ({admin.id})"
            result = await api_client.confirm_order_payment(
                order_id=order_id,
                admin_id=admin.id,
                admin_note=admin_note
            )
            
            if result:
                # Get subscription details if available
                subscription_id = result.get("subscription_id")
                subscription_details = None
                
                if subscription_id:
                    subscription_details = await api_client.get_subscription_details(subscription_id)
                
                # Create a detailed success message with connection details if available
                success_message = "✅ *پرداخت شما تایید شد!*\n\n"
                
                if subscription_details:
                    # Add subscription details to the message
                    protocol = subscription_details.get("protocol", "نامشخص")
                    location = subscription_details.get("location", "نامشخص")
                    expiry_date = subscription_details.get("expiry_date", "نامشخص")
                    
                    success_message += (
                        f"🔐 *مشخصات اشتراک:*\n"
                        f"🔹 پروتکل: {protocol}\n"
                        f"🔹 لوکیشن: {location}\n"
                        f"🔹 تاریخ انقضا: {expiry_date}\n\n"
                    )
                
                success_message += (
                    "🔰 اشتراک شما با موفقیت فعال شد. برای دریافت اطلاعات اتصال، "
                    "از منوی اصلی گزینه «اشتراک‌های من» را انتخاب کنید."
                )
                
                # Notify the user
                await context.bot.send_message(
                    chat_id=user_id,
                    text=success_message,
                    parse_mode="Markdown"
                )
                
                # Inform the admin
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ اشتراک با موفقیت ایجاد شد و اطلاع‌رسانی به کاربر انجام شد."
                )
            else:
                # Notify admin of API error
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚠️ خطا در تایید پرداخت و ایجاد اشتراک. لطفاً به صورت دستی بررسی کنید."
                )
                
                # Notify the user of processing delay
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "⚠️ *پرداخت شما در حال بررسی است*\n\n"
                        "به دلیل مشکل فنی، پردازش سفارش شما با تأخیر انجام خواهد شد. "
                        "پس از رفع مشکل، اطلاعات اشتراک به شما ارسال خواهد شد.\n\n"
                        "از صبر و شکیبایی شما متشکریم."
                    ),
                    parse_mode="Markdown"
                )
                
                # Don't clean up the order so it can be processed manually
                return
                
        except Exception as e:
            logger.error(f"Error processing payment confirmation for order {order_id}: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ خطا در پردازش تایید پرداخت: {e}"
            )
            return
    else:  # rejection
        try:
            # Call API to reject the order
            rejection_reason = "Rejected by admin"
            result = await api_client.reject_order_payment(
                order_id=order_id,
                admin_id=admin.id,
                rejection_reason=rejection_reason
            )
            
            if result:
                # Notify the user
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "❌ *متأسفانه پرداخت شما تایید نشد*\n\n"
                        "دلایل احتمالی:\n"
                        "- مغایرت در مبلغ واریزی\n"
                        "- خوانا نبودن تصویر رسید\n"
                        "- تأخیر بیش از حد در پرداخت\n\n"
                        "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                    ),
                    parse_mode="Markdown"
                )
                
                # Inform the admin
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ سفارش با موفقیت رد شد و به کاربر اطلاع داده شد."
                )
            else:
                # Notify admin of API error
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚠️ خطا در رد پرداخت. لطفاً به صورت دستی بررسی کنید."
                )
                # Don't clean up the order so it can be processed manually
                return
                
        except Exception as e:
            logger.error(f"Error processing payment rejection for order {order_id}: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ خطا در پردازش رد پرداخت: {e}"
            )
            return
    
    # Clean up the order from memory
    if int(user_id) in active_orders:
        del active_orders[int(user_id)]

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current order process."""
    query = update.callback_query
    user = update.effective_user
    
    if query:
        await query.answer()
        await query.edit_message_text("🚫 فرایند خرید لغو شد.")
    else:
        await update.message.reply_text("🚫 فرایند خرید لغو شد.")
    
    # Clean up
    if user and user.id in active_orders:
        del active_orders[user.id]
    
    return ConversationHandler.END

async def handle_retry_zarinpal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles retrying a Zarinpal payment."""
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if not query.data.startswith("retry_zarinpal_"):
        logger.error(f"Invalid callback data for handle_retry_zarinpal: {query.data}")
        await query.edit_message_text("❌ خطای داخلی. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END

    try:
        order_id = int(query.data.split("retry_zarinpal_")[1])
    except (ValueError, IndexError):
        logger.error(f"Could not parse order ID from: {query.data}")
        await query.edit_message_text("❌ خطای داخلی. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END

    await query.edit_message_text("⏳ در حال دریافت مجدد لینک پرداخت زرین‌پال...")

    try:
        # Request the payment URL from Core API
        payment_url = await payments_client.request_zarinpal_payment(order_id)

        # Show the payment link to the user
        keyboard = [[InlineKeyboardButton("🚀 پرداخت آنلاین", url=payment_url)]]
        
        message = (
            f"✅ لینک پرداخت آنلاین برای سفارش {order_id} دریافت شد.\n\n"
            f"👈 لطفاً برای تکمیل پرداخت روی دکمه زیر کلیک کنید.\n\n"
            f"⚠️ *توجه:* پس از پرداخت موفق در صفحه زرین‌پال، به ربات بازگردید. وضعیت سفارش شما به صورت خودکار بررسی خواهد شد."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # End the conversation here, user proceeds to Zarinpal
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error getting Zarinpal payment URL for order {order_id}: {e}")
        error_message = f"❌ خطای ارتباط با سرور پرداخت: {str(e)}"
        if hasattr(e, 'message') and "Payment gateway error:" in getattr(e, 'message', ''):
            error_message = f"❌ خطای درگاه پرداخت: {e.message.split('Payment gateway error:')[-1].strip()}"
        elif str(e) and "Payment gateway error:" in str(e):
            error_message = f"❌ خطای درگاه پرداخت: {str(e).split('Payment gateway error:')[-1].strip()}"
        await query.edit_message_text(error_message)
        return ConversationHandler.END

# Main conversation handler for the buy flow
buy_flow_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_buy_plan_callback, pattern=f"^{PLAN_CALLBACK_PREFIX}[0-9]+$")],
    states={
        SELECTING_PAYMENT_METHOD: [
            CallbackQueryHandler(
                handle_payment_method_callback, 
                pattern=f"^{PAYMENT_METHOD_CALLBACK_PREFIX}[^{PaymentMethod.ZARINPAL.value}].*$"
            ),
            # Note: Zarinpal is handled by its own conversation handler
            CallbackQueryHandler(cancel_order, pattern=f"^{CANCEL_ORDER_CALLBACK}$"),
        ],
        # Other states go here
    },
    fallbacks=[
        CallbackQueryHandler(cancel_order, pattern=f"^{CANCEL_ORDER_CALLBACK}$"),
        # Add more fallbacks as needed
    ],
    name="buy_flow_conversation",
)

def get_buy_flow_handlers():
    """
    Returns a list of all handlers related to the buy flow, including Zarinpal.
    This should be used in main.py to register all handlers at once.
    """
    return [
        buy_flow_conversation,
        zarinpal_conversation,
        # Add any other related handlers here
    ] 