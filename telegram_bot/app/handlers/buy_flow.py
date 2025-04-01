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

# Define conversation states
SELECTING_PAYMENT_METHOD = 1
WAITING_FOR_PAYMENT_PROOF = 2
CONFIRMING_PAYMENT = 3

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
    user_info = await get_user_by_telegram_id(user.id)
    if not user_info or "id" not in user_info:
        logger.error(f"Could not get user info for user {user.id}")
        await query.edit_message_text("❌ اطلاعات کاربری شما یافت نشد. لطفاً با پشتیبانی تماس بگیرید.")
        return ConversationHandler.END
    
    # Store user_id in context
    context.user_data["user_id"] = user_info["id"]
    
    # Get available payment methods
    payment_methods = await api_client.get_payment_methods()
    if not payment_methods:
        logger.error("Could not fetch payment methods")
        await query.edit_message_text("❌ در حال حاضر امکان پرداخت فراهم نیست. لطفاً بعداً مجدد تلاش کنید.")
        return ConversationHandler.END
    
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
    """Handle selected payment method"""
    query = update.callback_query
    user = update.effective_user
    
    # Answer callback query to remove the loading state
    await query.answer()
    
    # Check for cancellation
    if query.data == "cancel_payment":
        # Delete active order from memory
        if user.id in active_orders:
            del active_orders[user.id]
        
        await query.edit_message_text(
            "❌ خرید لغو شد.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Extract selected payment method from callback data
    try:
        payment_method = query.data.replace("payment_method_", "")
    except Exception as e:
        logger.error(f"Error extracting payment method: {str(e)}")
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Get plan data from memory
    plan_id = context.user_data.get('selected_plan_id')
    if not plan_id:
        logger.error(f"No selected plan found for user {user.id}")
        await query.edit_message_text(
            "❌ اطلاعات پلن یافت نشد. لطفاً دوباره از منوی خرید اقدام کنید.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Get user data
    user_data = await api_client.get_user_by_telegram_id(user.id)
    if not user_data:
        logger.error(f"User data not found for Telegram ID {user.id}")
        await query.edit_message_text(
            "❌ اطلاعات کاربری شما یافت نشد. لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Create order
    try:
        order = await api_client.create_order(
            user_id=user_data["id"],
            plan_id=plan_id,
            payment_method=payment_method
        )
        
        if not order:
            logger.error(f"Failed to create order for user {user_data['id']}, plan {plan_id}")
            await query.edit_message_text(
                "❌ خطا در ایجاد سفارش. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                reply_markup=None
            )
            return ConversationHandler.END
            
        logger.info(f"Order created: {order}")
        
        # Store order_id and amount in context for the payment proof submission
        context.user_data["order_id"] = order["id"]
        context.user_data["amount"] = order["total_price"]
        
        # Handle different payment methods
        if payment_method == "card_to_card":
            # For card-to-card payment, redirect to payment proof handler
            # Store the active order for reference
            active_orders[user.id] = {
                "order_id": order["id"],
                "plan_id": plan_id,
                "amount": order["total_price"]
            }
            
            # Redirect to card-to-card payment flow
            from app.handlers.payment_proof_handlers import show_bank_cards
            return await show_bank_cards(update, context)
            
        elif payment_method == "crypto":
            # Handle crypto payment method
            message = (
                f"💰 *پرداخت ارز دیجیتال*\n\n"
                f"📌 شماره سفارش: `{order['id']}`\n"
                f"💰 مبلغ قابل پرداخت: *{order['total_price']:,} تومان*\n\n"
                f"لطفاً با پشتیبانی تماس بگیرید تا اطلاعات پرداخت ارز دیجیتال به شما ارائه شود."
            )
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="back_to_main")
                ]]),
                parse_mode="Markdown"
            )
            return ConversationHandler.END
            
        else:
            # Unsupported payment method
            logger.warning(f"Unsupported payment method: {payment_method}")
            await query.edit_message_text(
                "❌ روش پرداخت انتخابی فعلاً پشتیبانی نمی‌شود.",
                reply_markup=None
            )
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Error handling payment method: {str(e)}")
        await query.edit_message_text(
            f"❌ خطایی رخ داد: {str(e)}",
            reply_markup=None
        )
        return ConversationHandler.END

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

def get_buy_flow_handlers():
    """Return the handlers for the buy flow."""
    return [
        # Handle plan selection callbacks
        CallbackQueryHandler(
            handle_buy_plan_callback,
            pattern=f"^{PLAN_CALLBACK_PREFIX}",
        ),
        # Admin payment confirmation/rejection handlers
        CallbackQueryHandler(
            handle_admin_payment_confirmation,
            pattern=f"^{CONFIRM_PAYMENT_CALLBACK_PREFIX}|{REJECT_PAYMENT_CALLBACK_PREFIX}",
        ),
        # Conversation handler for the full purchase flow
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    handle_buy_plan_callback,
                    pattern=f"^{PLAN_CALLBACK_PREFIX}",
                ),
            ],
            states={
                SELECTING_PAYMENT_METHOD: [
                    CallbackQueryHandler(
                        handle_payment_method_callback,
                        pattern=f"^{PAYMENT_METHOD_CALLBACK_PREFIX}|{CANCEL_ORDER_CALLBACK}",
                    ),
                ],
                WAITING_FOR_PAYMENT_PROOF: [
                    MessageHandler(filters.PHOTO, handle_payment_proof),
                    CallbackQueryHandler(cancel_order, pattern=f"^{CANCEL_ORDER_CALLBACK}$"),
                ],
                CONFIRMING_PAYMENT: [
                    # This is handled by the standalone handler for admin confirmation
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_order),
                CallbackQueryHandler(cancel_order, pattern=f"^{CANCEL_ORDER_CALLBACK}$"),
            ],
            name="buy_flow",
            persistent=False,
        ),
    ] 