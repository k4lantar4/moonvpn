import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
import asyncio

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputMediaPhoto,
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

from app.api import api_client
from app.utils.logger import get_logger
from app.keyboards.payment import generate_payment_method_keyboard, get_cancel_keyboard
from app.handlers.main_menu import show_main_menu
from app.handlers.payment_notification_handlers import send_payment_notification_to_group

# Set up logging
logger = get_logger(__name__)

# Define conversation states
(
    SELECTING_BANK_CARD,
    WAITING_FOR_PAYMENT_PROOF,
    CONFIRMING_DETAILS,
    WAITING_FOR_VERIFICATION,
    PAYMENT_COMPLETED,
) = range(5)

# Define callback data patterns
CARD_SELECTION_PREFIX = "select_card_"
CANCEL_PAYMENT = "cancel_payment"
CONFIRM_PAYMENT = "confirm_payment"
PAYMENT_COMPLETE = "payment_complete"
SUBMIT_ANOTHER = "submit_another"

# Store active payment sessions with expiration time
# Format: {user_id: {"order_id": id, "card_id": id, "expires_at": datetime, "amount": amount}}
active_payments = {}

# Payment timeout in minutes
PAYMENT_TIMEOUT_MINUTES = 15

async def show_bank_cards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available bank cards for payment."""
    query = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Extract order data from context
    order_id = context.user_data.get("order_id")
    order_amount = context.user_data.get("amount")
    
    if not order_id or not order_amount:
        await update.effective_message.reply_text(
            "❌ اطلاعات سفارش کامل نیست. لطفاً دوباره از طریق منوی خرید اقدام کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Check if we have a previously used card stored in bot_data
    last_used_card_id = context.bot_data.get("last_used_card_id")
    
    # Try to get the next card using the rotation logic
    next_card = await api_client.get_next_bank_card_for_payment(last_used_id=last_used_card_id)
    
    # If rotation logic fails or no card is returned, fall back to fetching all cards
    if next_card:
        # Store this card as the last used one for next time
        context.bot_data["last_used_card_id"] = next_card["id"]
        bank_cards = [next_card]
    else:
        # Fetch active bank cards for payment as fallback
        bank_cards = await api_client.get_bank_cards_for_payment()
    
    if not bank_cards or len(bank_cards) == 0:
        await update.effective_message.reply_text(
            "❌ در حال حاضر هیچ کارت فعالی برای پرداخت وجود ندارد.\n"
            "لطفاً بعداً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Create the message with payment instructions
    message = (
        f"💳 *پرداخت کارت به کارت*\n\n"
        f"📌 شماره سفارش: `{order_id}`\n"
        f"💰 مبلغ قابل پرداخت: *{order_amount:,} تومان*\n\n"
        f"⏱️ مهلت پرداخت: {PAYMENT_TIMEOUT_MINUTES} دقیقه\n\n"
    )
    
    # Add card information
    keyboard = []
    
    for card in bank_cards:
        # Format card details for display
        bank_name = card["bank_name"]
        # Get card number and mask it for security
        card_number = card["card_number"]
        masked_card = card_number[-4:].rjust(len(card_number), '*')
        card_holder = card["card_holder_name"]
        
        # Add card details to message
        message += (
            f"🏦 *اطلاعات کارت:*\n"
            f"🔹 بانک: {bank_name}\n"
            f"🔹 شماره کارت: `{card_number}`\n"
            f"🔹 به نام: {card_holder}\n\n"
            f"⚠️ *نکات مهم:*\n"
            f"- لطفاً دقیقاً مبلغ {order_amount:,} تومان واریز کنید.\n"
            f"- پس از پرداخت، تصویر رسید پرداخت را ارسال کنید.\n"
            f"- شماره پیگیری یا شناسه پرداخت را حتما یادداشت کنید.\n\n"
            f"👇 *پس از پرداخت، تصویر رسید را ارسال کنید:*"
        )
        
        # Store card id in user_data for later use
        context.user_data["selected_card_id"] = card["id"]
        
        # Add button to keyboard for confirmation
        keyboard.append([
            InlineKeyboardButton("✅ من پرداخت را انجام داده‌ام", callback_data=f"{CARD_SELECTION_PREFIX}{card['id']}")
        ])
    
    # Add cancel button
    keyboard.append([
        InlineKeyboardButton("❌ انصراف از پرداخت", callback_data=CANCEL_PAYMENT)
    ])
    
    # Record payment start time and set expiration
    active_payments[user.id] = {
        "order_id": order_id,
        "expires_at": datetime.now() + timedelta(minutes=PAYMENT_TIMEOUT_MINUTES),
        "amount": order_amount,
        "card_id": context.user_data.get("selected_card_id")  # Store the selected card ID
    }
    
    # Send message with card selection options
    await update.effective_message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Start expiry checker task
    payment_timer_key = f"payment_timer_{user.id}"
    timer_task = asyncio.create_task(check_payment_expiry(user.id, chat_id, context))
    context.bot_data[payment_timer_key] = timer_task
    
    return WAITING_FOR_PAYMENT_PROOF

async def handle_card_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bank card selection for payment."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Check for cancellation
    if query.data == CANCEL_PAYMENT:
        # Clean up payment session
        if user.id in active_payments:
            del active_payments[user.id]
        
        await query.edit_message_text(
            "❌ پرداخت لغو شد.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Extract card ID from callback data
    if not query.data.startswith(CARD_SELECTION_PREFIX):
        logger.error(f"Invalid callback data: {query.data}")
        return SELECTING_BANK_CARD
    
    card_id = int(query.data[len(CARD_SELECTION_PREFIX):])
    
    # Fetch card details
    card = await api_client.get_bank_card_details(card_id)
    
    if not card:
        await query.edit_message_text(
            "❌ اطلاعات کارت یافت نشد. لطفاً کارت دیگری انتخاب کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="show_bank_cards")
            ]])
        )
        return SELECTING_BANK_CARD
    
    # Store card info in active payment
    if user.id in active_payments:
        active_payments[user.id]["card_id"] = card_id
    else:
        # Payment session expired or invalid
        await query.edit_message_text(
            "❌ نشست پرداخت شما منقضی شده است. لطفاً دوباره از منوی خرید اقدام کنید.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Format card details
    bank_name = card["bank_name"]
    card_number = card["card_number"]
    card_holder = card["card_holder_name"]
    
    # Get payment amount
    amount = active_payments[user.id]["amount"]
    
    # Create detailed payment message
    message = (
        f"🧾 *اطلاعات پرداخت*\n\n"
        f"💰 مبلغ قابل پرداخت: *{amount:,} تومان*\n\n"
        f"🏦 *اطلاعات کارت:*\n"
        f"🔹 بانک: {bank_name}\n"
        f"🔹 شماره کارت: `{card_number}`\n"
        f"🔹 به نام: {card_holder}\n\n"
        f"⚠️ *نکات مهم:*\n"
        f"- لطفاً دقیقاً مبلغ {amount:,} تومان واریز کنید.\n"
        f"- پس از پرداخت، تصویر رسید پرداخت را ارسال کنید.\n"
        f"- شماره پیگیری یا شناسه پرداخت را حتما یادداشت کنید.\n\n"
        f"👇 *پس از پرداخت، تصویر رسید را ارسال کنید:*"
    )
    
    # Update message with card details and instructions
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ انصراف از پرداخت", callback_data=CANCEL_PAYMENT)
        ]]),
        parse_mode="Markdown"
    )
    
    return WAITING_FOR_PAYMENT_PROOF

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle receipt image submission."""
    user = update.effective_user
    
    # Check if user has an active payment session
    if user.id not in active_payments:
        await update.message.reply_text(
            "❌ نشست پرداخت شما منقضی شده است. لطفاً دوباره از منوی خرید اقدام کنید.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Check if the message contains a photo
    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ لطفاً تصویر رسید پرداخت را ارسال کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ انصراف از پرداخت", callback_data=CANCEL_PAYMENT)
            ]])
        )
        return WAITING_FOR_PAYMENT_PROOF
    
    # Get the photo with highest resolution
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    # Store file_id in context for use in confirmation
    context.user_data["payment_proof_file_id"] = file_id
    
    # Ask for payment reference number
    await update.message.reply_text(
        "🔢 لطفاً شماره پیگیری یا شناسه پرداخت را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ انصراف از پرداخت", callback_data=CANCEL_PAYMENT)
        ]])
    )
    
    return CONFIRMING_DETAILS

async def handle_payment_reference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle receipt of payment reference/tracking number."""
    user = update.effective_user
    
    if not update.message or not update.message.text:
        await update.message.reply_text(
            "❌ لطفاً شماره پیگیری را به صورت متن وارد کنید."
        )
        return WAITING_FOR_PAYMENT_REFERENCE
    
    # Get payment reference from user
    payment_reference = update.message.text.strip()
    
    # Validate payment reference - it should be a valid tracking number
    if len(payment_reference) < 5 or len(payment_reference) > 30:
        await update.message.reply_text(
            "❌ شماره پیگیری نامعتبر است. لطفاً یک شماره پیگیری معتبر وارد کنید."
        )
        return WAITING_FOR_PAYMENT_REFERENCE
    
    # Store reference number in user data
    context.user_data['payment_reference'] = payment_reference
    
    # Get order ID and other data from user_data
    order_id = context.user_data.get('order_id')
    selected_card_id = context.user_data.get('selected_card_id')
    payment_proof_file_id = context.user_data.get('payment_proof_file_id')
    
    if not order_id:
        await update.message.reply_text(
            "❌ خطا: اطلاعات سفارش یافت نشد. لطفاً دوباره از منوی اصلی شروع کنید."
        )
        return ConversationHandler.END
    
    # Send "processing" message
    processing_msg = await update.message.reply_text(
        "⏳ در حال ارسال اطلاعات پرداخت شما..."
    )
    
    # Get payment proof from user_data
    payment_proof_bytes = context.user_data.get('payment_proof_bytes')
    
    try:
        # Submit payment proof to API
        result = await api_client.submit_payment_proof(
            order_id=order_id,
            payment_reference=payment_reference,
            payment_proof=payment_proof_bytes,
            payment_method="card_to_card",
            notes=f"پرداخت از طریق ربات تلگرام"
        )
        
        if result and result.get("success", True):
            # Clean up stored payment proof bytes to free memory
            if 'payment_proof_bytes' in context.user_data:
                del context.user_data['payment_proof_bytes']
            
            # Try to get order details for amount
            order_details = await api_client.get_order_details(order_id)
            payment_amount = order_details.get("total_amount", 0) if order_details else 0
            
            # Send notification to admin group
            await send_payment_notification_to_group(
                context=context,
                order_id=order_id,
                user_telegram_id=user.id,
                card_id=selected_card_id,
                payment_reference=payment_reference,
                payment_amount=payment_amount,
                payment_proof_file_id=payment_proof_file_id
            )
            
            # Show success message to user
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text=(
                    "✅ رسید پرداخت شما با موفقیت ثبت شد.\n\n"
                    f"📌 شماره سفارش: {order_id}\n"
                    f"📝 شماره پیگیری: {payment_reference}\n\n"
                    "👨‍💼 اطلاعات پرداخت شما برای ادمین ارسال شد و پس از تایید، "
                    "اشتراک شما فعال خواهد شد. این فرآیند معمولاً کمتر از ۳۰ دقیقه طول می‌کشد."
                )
            )
            
            # Store order_id in active_orders for later reference if needed
            if 'active_orders' not in context.bot_data:
                context.bot_data['active_orders'] = {}
            
            # Add to active orders with status "verification_pending"
            context.bot_data['active_orders'][order_id] = {
                'user_id': user.id,
                'status': 'verification_pending',
                'payment_reference': payment_reference,
                'payment_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Cancel payment timer if it exists
            payment_timer_key = f"payment_timer_{user.id}"
            if payment_timer_key in context.bot_data:
                timer_task = context.bot_data[payment_timer_key]
                if not timer_task.cancelled():
                    timer_task.cancel()
                del context.bot_data[payment_timer_key]
            
            # End conversation
            return await handle_completion(update, context)
        else:
            error_msg = result.get("detail", "خطایی رخ داده است. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.") if result else "خطایی رخ داده است. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text=f"❌ خطا در ثبت رسید پرداخت: {error_msg}"
            )
            
            return WAITING_FOR_PAYMENT_REFERENCE
    
    except Exception as e:
        logger.error(f"Error in handle_payment_reference: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_msg.message_id,
            text="❌ خطایی در ارسال اطلاعات پرداخت رخ داده است. لطفاً دوباره تلاش کنید."
        )
        
        # Still keep the reference number in case they retry
        return WAITING_FOR_PAYMENT_REFERENCE

async def handle_completion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment completion and return to main menu."""
    query = update.callback_query
    
    if query:
        await query.answer()
    
    # Return to main menu
    await show_main_menu(update, context)
    
    return ConversationHandler.END

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the payment process."""
    query = update.callback_query
    user = update.effective_user
    
    if query:
        await query.answer()
    
    # Clean up payment session
    if user.id in active_payments:
        del active_payments[user.id]
    
    # Clean up context data
    if "payment_proof_file_id" in context.user_data:
        del context.user_data["payment_proof_file_id"]
    
    if query:
        await query.edit_message_text(
            "❌ پرداخت لغو شد.",
            reply_markup=None
        )
    else:
        await update.message.reply_text(
            "❌ پرداخت لغو شد.",
            reply_markup=None
        )
    
    # Return to main menu
    await show_main_menu(update, context)
    
    return ConversationHandler.END

async def check_payment_expiry(user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check for expired payment sessions and notify users."""
    # Wait until expiry time
    if user_id not in active_payments:
        return
        
    expiry_time = active_payments[user_id].get("expires_at")
    if not expiry_time:
        return
        
    # Calculate seconds until expiry
    now = datetime.now()
    if now < expiry_time:
        # Wait until expiry time
        seconds_to_wait = (expiry_time - now).total_seconds()
        await asyncio.sleep(seconds_to_wait)
    
    # Check if payment is still active
    if user_id in active_payments:
        # Payment session expired
        del active_payments[user_id]
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⏰ مهلت پرداخت به پایان رسید. لطفاً در صورت تمایل، دوباره از منوی خرید اقدام کنید.",
                reply_markup=None
            )
            
            # Clean up user data for this payment session
            if "selected_card_id" in context.user_data:
                del context.user_data["selected_card_id"]
            if "payment_proof_file_id" in context.user_data:
                del context.user_data["payment_proof_file_id"]
            if "payment_proof_bytes" in context.user_data:
                del context.user_data["payment_proof_bytes"]
                
            # Return to main menu
            await show_main_menu({"effective_chat": {"id": chat_id}, "effective_user": {"id": user_id}}, context)
            
        except Exception as e:
            logger.error(f"Error sending payment expiry notification: {str(e)}")

def get_payment_handlers():
    """Return the payment handlers for use in the main application."""
    return [
        # Add handlers to main application
        CallbackQueryHandler(
            show_bank_cards,
            pattern="^show_bank_cards$"
        ),
        # Payment flow conversation handler
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    show_bank_cards,
                    pattern="^payment_method_card_to_card$"
                ),
            ],
            states={
                SELECTING_BANK_CARD: [
                    CallbackQueryHandler(
                        handle_card_selection,
                        pattern=f"^{CARD_SELECTION_PREFIX}\\d+$|^{CANCEL_PAYMENT}$"
                    ),
                ],
                WAITING_FOR_PAYMENT_PROOF: [
                    MessageHandler(
                        filters.PHOTO,
                        handle_payment_proof
                    ),
                    CallbackQueryHandler(
                        cancel_payment,
                        pattern=f"^{CANCEL_PAYMENT}$"
                    ),
                ],
                CONFIRMING_DETAILS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        handle_payment_reference
                    ),
                    CallbackQueryHandler(
                        cancel_payment,
                        pattern=f"^{CANCEL_PAYMENT}$"
                    ),
                ],
                PAYMENT_COMPLETED: [
                    CallbackQueryHandler(
                        handle_completion,
                        pattern=f"^{PAYMENT_COMPLETE}$"
                    ),
                ],
            },
            fallbacks=[
                CallbackQueryHandler(
                    cancel_payment,
                    pattern=f"^{CANCEL_PAYMENT}$"
                ),
                CommandHandler("cancel", cancel_payment),
            ],
            name="payment_flow",
            persistent=False,
        ),
    ] 