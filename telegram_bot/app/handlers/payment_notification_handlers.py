import logging
from typing import Dict, Optional, Any, List
import re
from datetime import datetime, timedelta

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from api import api_client
from utils.logger import get_logger
from core.config import MANAGE_GROUP_ID, DEBUG_MODE
from handlers.payment_proof_handlers import active_payments
from utils.helpers import format_card_number
from utils.permissions import is_payment_admin

# Set up logging
logger = get_logger(__name__)

# Define callback data patterns for approval/rejection
APPROVE_PAYMENT_PATTERN = r"^approve_payment_(\d+)$"
REJECT_PAYMENT_PATTERN = r"^reject_payment_(\d+)$"
REJECT_REASON_PATTERN = r"^reject_reason_(\d+)$"

# Compile patterns for faster matching
APPROVE_PAYMENT_REGEX = re.compile(APPROVE_PAYMENT_PATTERN)
REJECT_PAYMENT_REGEX = re.compile(REJECT_PAYMENT_PATTERN)
REJECT_REASON_REGEX = re.compile(REJECT_REASON_PATTERN)

# Define callback patterns
PAYMENT_APPROVE_PATTERN = r"^payment_approve_(\d+)$"
PAYMENT_REJECT_PATTERN = r"^payment_reject_(\d+)$"
PAYMENT_REJECT_REASON_PATTERN = r"^payment_reject_reason_(\d+)_(.+)$"
PAYMENT_CUSTOM_REJECT_PATTERN = r"^payment_custom_reject_(\d+)$"

# Common rejection reasons
REJECTION_REASONS = {
    "incorrect_amount": "مبلغ واریزی اشتباه است",
    "fake_receipt": "رسید جعلی است",
    "incomplete_info": "اطلاعات ناقص است",
    "unclear_image": "تصویر رسید واضح نیست",
    "wrong_card": "کارت مقصد اشتباه است",
    "old_receipt": "رسید قدیمی است (تاریخ نامعتبر)",
    "duplicate": "رسید تکراری است"
}

async def send_payment_notification(
    context: ContextTypes.DEFAULT_TYPE,
    order_id: int,
    user_telegram_id: int,
    card_id: Optional[int] = None,
    payment_reference: str = "",
    payment_amount: float = 0,
    payment_proof_img_url: Optional[str] = None,
    payment_proof_file_id: Optional[str] = None
) -> bool:
    """
    Send payment proof notification to the appropriate admin Telegram group.
    
    Args:
        context: Bot context
        order_id: ID of the order
        user_telegram_id: Telegram ID of the user who submitted the payment
        card_id: ID of the bank card used for payment (if available)
        payment_reference: Reference/tracking number provided by the user
        payment_amount: Amount of the payment
        payment_proof_img_url: URL of the uploaded payment proof (if available)
        payment_proof_file_id: Telegram file_id of the payment proof image (if available)
    
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        # If we have a card_id, find the appropriate admin and group
        group_id = MANAGE_GROUP_ID  # Default to main MANAGE group
        admin_info = None
        
        if card_id:
            # Get admin assignment for this card
            admin_assignment = await api_client.get_payment_admin_for_card(card_id)
            
            if admin_assignment and "telegram_group_id" in admin_assignment:
                group_id = admin_assignment["telegram_group_id"]
                admin_info = admin_assignment.get("admin", {})
                logger.info(f"Found admin assignment for card {card_id}: group_id={group_id}")
            else:
                logger.warning(f"No admin assignment found for card {card_id}, using default group")
        
        # Get user information
        user_info = await api_client.get_user_by_telegram_id(user_telegram_id)
        user_name = user_info.get("first_name", "کاربر") if user_info else "کاربر"
        
        # Get order details
        order_details = await api_client.get_order_details(order_id)
        
        # Build message text
        message = (
            f"🧾 *درخواست تأیید پرداخت جدید*\n\n"
            f"📌 شماره سفارش: `{order_id}`\n"
            f"👤 کاربر: {user_name} (ID: `{user_telegram_id}`)\n"
        )
        
        if payment_amount:
            message += f"💰 مبلغ: *{payment_amount:,} تومان*\n"
        
        if payment_reference:
            message += f"📝 شماره پیگیری: `{payment_reference}`\n"
        
        if card_id:
            # Get card details
            card_details = await api_client.get_bank_card_details(card_id)
            if card_details:
                bank_name = card_details.get("bank_name", "نامشخص")
                card_holder = card_details.get("card_holder_name", "نامشخص")
                card_number = card_details.get("card_number", "")
                
                # Mask card number for security
                if card_number:
                    masked_card = card_number[-4:].rjust(len(card_number), '*')
                    message += (
                        f"🏦 *اطلاعات کارت:*\n"
                        f"🔹 بانک: {bank_name}\n"
                        f"🔹 شماره کارت: `{masked_card}`\n"
                        f"🔹 به نام: {card_holder}\n"
                    )
        
        if admin_info:
            admin_name = admin_info.get("first_name", "نامشخص")
            message += f"\n👮 ادمین مسئول: {admin_name}\n"
        
        message += f"\n⏰ زمان ارسال: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Create approve/reject buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"approve_payment_{order_id}"),
                InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_payment_{order_id}")
            ]
        ]
        
        # Send the notification to the admin group
        if payment_proof_file_id:
            # If we have a file_id, send the image with caption
            sent_message = await context.bot.send_photo(
                chat_id=group_id,
                photo=payment_proof_file_id,
                caption=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # If no image available, just send text
            sent_message = await context.bot.send_message(
                chat_id=group_id,
                text=message + "\n⚠️ *تصویر رسید پرداخت موجود نیست*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        # Store message_id for future reference if needed
        if sent_message and sent_message.message_id:
            # Optionally update the order with the message_id for future reference
            await api_client.update_payment_proof_telegram_msg_id(
                order_id=order_id,
                telegram_msg_id=sent_message.message_id,
                telegram_group_id=str(group_id)
            )
            
        logger.info(f"Payment notification sent to group {group_id} for order {order_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending payment notification: {str(e)}")
        
        if DEBUG_MODE:
            # In debug mode, send error to MANAGE_GROUP_ID
            try:
                await context.bot.send_message(
                    chat_id=MANAGE_GROUP_ID,
                    text=f"❌ *خطا در ارسال اطلاعیه پرداخت*\n\n"
                         f"سفارش: {order_id}\n"
                         f"خطا: `{str(e)}`",
                    parse_mode="Markdown"
                )
            except Exception as debug_error:
                logger.error(f"Error sending debug notification: {str(debug_error)}")
        
        return False

async def handle_payment_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin approval of a payment."""
    query = update.callback_query
    await query.answer()
    
    admin = update.effective_user
    if not admin:
        logger.error("Admin not found in payment approval")
        return
    
    # Extract order_id from callback data
    match = APPROVE_PAYMENT_REGEX.match(query.data)
    if not match:
        logger.error(f"Invalid callback data: {query.data}")
        return
    
    order_id = int(match.group(1))
    
    # Check if admin has permission to approve payments
    admin_permissions = await api_client.get_user_permissions(admin.id)
    if not admin_permissions or "approve_payments" not in admin_permissions:
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ شما مجوز تأیید پرداخت را ندارید.",
            reply_to_message_id=query.message.message_id
        )
        return
    
    # Update message to show processing
    await query.edit_message_reply_markup(reply_markup=None)
    processing_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="⏳ در حال پردازش تأیید پرداخت...",
        reply_to_message_id=query.message.message_id
    )
    
    try:
        # Call API to confirm payment
        result = await api_client.confirm_order_payment(
            order_id=order_id,
            admin_id=admin.id,
            admin_note=f"Approved by {admin.full_name} via Telegram"
        )
        
        if result and result.get("success", False):
            # Payment confirmed successfully
            order_data = result.get("data", {})
            subscription_data = order_data.get("subscription", {})
            
            # Get user telegram_id to notify them
            user_id = order_data.get("user_id")
            user_info = await api_client.get_user_by_id(user_id) if user_id else None
            user_telegram_id = user_info.get("telegram_id") if user_info else None
            
            # Update admin group with confirmation
            success_message = (
                f"✅ *پرداخت با موفقیت تأیید شد*\n\n"
                f"📌 شماره سفارش: `{order_id}`\n"
                f"👤 تأیید کننده: {admin.full_name}\n"
                f"⏰ زمان تأیید: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            
            if subscription_data:
                plan_name = subscription_data.get("plan_name", "نامشخص")
                expires_at = subscription_data.get("expires_at", "نامشخص")
                
                success_message += (
                    f"\n📊 *اطلاعات اشتراک:*\n"
                    f"🔹 پلن: {plan_name}\n"
                    f"🔹 تاریخ انقضا: {expires_at}\n"
                )
            
            # Update processing message
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_message.message_id,
                text=success_message,
                parse_mode="Markdown"
            )
            
            # Notify user if we have their telegram_id
            if user_telegram_id:
                user_message = (
                    f"✅ *پرداخت شما تأیید شد*\n\n"
                    f"📌 شماره سفارش: `{order_id}`\n"
                )
                
                if subscription_data:
                    plan_name = subscription_data.get("plan_name", "نامشخص")
                    expires_at = subscription_data.get("expires_at", "نامشخص")
                    
                    user_message += (
                        f"\n📊 *اطلاعات اشتراک:*\n"
                        f"🔹 پلن: {plan_name}\n"
                        f"🔹 تاریخ انقضا: {expires_at}\n"
                        f"\nاشتراک شما فعال شد و می‌توانید از بخش «حساب‌های من» جزئیات اتصال را مشاهده کنید."
                    )
                
                try:
                    await context.bot.send_message(
                        chat_id=user_telegram_id,
                        text=user_message,
                        parse_mode="Markdown"
                    )
                    logger.info(f"User {user_telegram_id} notified about payment approval for order {order_id}")
                except Exception as e:
                    logger.error(f"Error notifying user {user_telegram_id}: {str(e)}")
            
        else:
            # Payment confirmation failed
            error_message = result.get("detail") if result else "خطای نامشخص"
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_message.message_id,
                text=f"❌ *خطا در تأیید پرداخت*\n\n{error_message}",
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error(f"Error processing payment approval: {str(e)}")
        
        # Update processing message with error
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_message.message_id,
            text=f"❌ *خطا در پردازش تأیید پرداخت*\n\n`{str(e)}`",
            parse_mode="Markdown"
        )

async def handle_payment_rejection_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin request to reject a payment (show reason input request)."""
    query = update.callback_query
    await query.answer()
    
    admin = update.effective_user
    if not admin:
        logger.error("Admin not found in payment rejection request")
        return
    
    # Extract order_id from callback data
    match = REJECT_PAYMENT_REGEX.match(query.data)
    if not match:
        logger.error(f"Invalid callback data: {query.data}")
        return
    
    order_id = int(match.group(1))
    
    # Check if admin has permission to reject payments
    admin_permissions = await api_client.get_user_permissions(admin.id)
    if not admin_permissions or "approve_payments" not in admin_permissions:
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ شما مجوز رد پرداخت را ندارید.",
            reply_to_message_id=query.message.message_id
        )
        return
    
    # Store order_id in user_data for the next step
    context.user_data["rejecting_order_id"] = order_id
    context.user_data["rejection_message_id"] = query.message.message_id
    
    # Update message to ask for rejection reason
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("مغایرت مبلغ", callback_data=f"reject_reason_{order_id}_amount")],
            [InlineKeyboardButton("اطلاعات کارت اشتباه", callback_data=f"reject_reason_{order_id}_card")],
            [InlineKeyboardButton("تصویر رسید ناخوانا", callback_data=f"reject_reason_{order_id}_image")],
            [InlineKeyboardButton("تاریخ/زمان نامعتبر", callback_data=f"reject_reason_{order_id}_date")],
            [InlineKeyboardButton("دلیل دیگر (پیام دهید)", callback_data=f"reject_reason_{order_id}_other")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"reject_payment_cancel_{order_id}")]
        ])
    )
    
    # Ask admin to provide rejection reason
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="❓ لطفاً دلیل رد پرداخت را انتخاب کنید یا توضیح دهید:",
        reply_to_message_id=query.message.message_id
    )

async def handle_rejection_reason_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin selection of a predefined rejection reason."""
    query = update.callback_query
    await query.answer()
    
    admin = update.effective_user
    if not admin:
        logger.error("Admin not found in rejection reason selection")
        return
    
    # Extract order_id and reason from callback data
    match = re.match(r"^reject_reason_(\d+)_(.+)$", query.data)
    if not match:
        logger.error(f"Invalid callback data: {query.data}")
        return
    
    order_id = int(match.group(1))
    reason_code = match.group(2)
    
    # Map reason codes to full text
    reason_text = {
        "amount": "مغایرت مبلغ پرداختی با مبلغ سفارش",
        "card": "پرداخت به کارت اشتباه انجام شده است",
        "image": "تصویر رسید ناخوانا یا ناقص است",
        "date": "تاریخ یا زمان پرداخت نامعتبر است",
        "other": "دلیل دیگر (لطفاً پیام دهید)"
    }.get(reason_code, "دلیل نامشخص")
    
    # If reason is "other", wait for admin to type a custom reason
    if reason_code == "other":
        context.user_data["rejecting_order_id"] = order_id
        context.user_data["waiting_for_custom_reason"] = True
        
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📝 لطفاً دلیل رد پرداخت را بنویسید:",
            reply_to_message_id=query.message.message_id
        )
        return
    
    # For predefined reasons, process rejection immediately
    await process_payment_rejection(update, context, order_id, reason_text)

async def handle_custom_rejection_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle custom rejection reason text from admin."""
    # Check if we're waiting for a custom reason
    if not context.user_data.get("waiting_for_custom_reason", False):
        return
    
    order_id = context.user_data.get("rejecting_order_id")
    if not order_id:
        logger.error("No order_id found for custom rejection reason")
        return
    
    # Get custom reason text from message
    custom_reason = update.message.text.strip()
    
    # Process the rejection with custom reason
    await process_payment_rejection(update, context, order_id, custom_reason)
    
    # Clear the waiting flag
    context.user_data["waiting_for_custom_reason"] = False
    context.user_data["rejecting_order_id"] = None

async def process_payment_rejection(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    order_id: int, 
    rejection_reason: str
) -> None:
    """Process payment rejection with the provided reason."""
    admin = update.effective_user
    chat_id = update.effective_chat.id
    
    # Send processing message
    processing_message = await context.bot.send_message(
        chat_id=chat_id,
        text="⏳ در حال پردازش رد پرداخت...",
    )
    
    try:
        # Call API to reject payment
        result = await api_client.reject_order_payment(
            order_id=order_id,
            admin_id=admin.id,
            rejection_reason=rejection_reason
        )
        
        if result and result.get("success", False):
            # Payment rejected successfully
            order_data = result.get("data", {})
            
            # Get user telegram_id to notify them
            user_id = order_data.get("user_id")
            user_info = await api_client.get_user_by_id(user_id) if user_id else None
            user_telegram_id = user_info.get("telegram_id") if user_info else None
            
            # Update admin group with rejection confirmation
            rejection_message = (
                f"❌ *پرداخت رد شد*\n\n"
                f"📌 شماره سفارش: `{order_id}`\n"
                f"👤 رد کننده: {admin.full_name}\n"
                f"📝 دلیل: {rejection_reason}\n"
                f"⏰ زمان رد: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            
            # Update processing message
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_message.message_id,
                text=rejection_message,
                parse_mode="Markdown"
            )
            
            # If we were editing an inline keyboard, update the original message too
            original_message_id = context.user_data.get("rejection_message_id")
            if original_message_id:
                try:
                    await context.bot.edit_message_reply_markup(
                        chat_id=chat_id,
                        message_id=original_message_id,
                        reply_markup=None
                    )
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=rejection_message,
                        reply_to_message_id=original_message_id,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error updating original message: {str(e)}")
            
            # Notify user if we have their telegram_id
            if user_telegram_id:
                user_message = (
                    f"❌ *پرداخت شما رد شد*\n\n"
                    f"📌 شماره سفارش: `{order_id}`\n"
                    f"📝 دلیل: {rejection_reason}\n\n"
                    f"لطفاً مجدداً از طریق منوی اصلی و بخش خرید اقدام نمایید."
                )
                
                try:
                    await context.bot.send_message(
                        chat_id=user_telegram_id,
                        text=user_message,
                        parse_mode="Markdown"
                    )
                    logger.info(f"User {user_telegram_id} notified about payment rejection for order {order_id}")
                except Exception as e:
                    logger.error(f"Error notifying user {user_telegram_id}: {str(e)}")
            
        else:
            # Payment rejection failed
            error_message = result.get("detail") if result else "خطای نامشخص"
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_message.message_id,
                text=f"❌ *خطا در رد پرداخت*\n\n{error_message}",
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error(f"Error processing payment rejection: {str(e)}")
        
        # Update processing message with error
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=processing_message.message_id,
            text=f"❌ *خطا در پردازش رد پرداخت*\n\n`{str(e)}`",
            parse_mode="Markdown"
        )

async def handle_rejection_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancellation of payment rejection."""
    query = update.callback_query
    await query.answer()
    
    # Extract order_id from callback data
    match = re.match(r"^reject_payment_cancel_(\d+)$", query.data)
    if not match:
        logger.error(f"Invalid callback data: {query.data}")
        return
    
    order_id = int(match.group(1))
    
    # Restore original approve/reject buttons
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"approve_payment_{order_id}"),
            InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_payment_{order_id}")
        ]
    ]
    
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Clean up user_data
    if "rejecting_order_id" in context.user_data:
        del context.user_data["rejecting_order_id"]
    if "waiting_for_custom_reason" in context.user_data:
        del context.user_data["waiting_for_custom_reason"]
    if "rejection_message_id" in context.user_data:
        del context.user_data["rejection_message_id"]

def get_payment_notification_handlers():
    """Return a list of handlers for payment notifications."""
    return [
        CallbackQueryHandler(handle_payment_approve, pattern=PAYMENT_APPROVE_PATTERN),
        CallbackQueryHandler(handle_payment_reject, pattern=PAYMENT_REJECT_PATTERN),
        CallbackQueryHandler(handle_payment_reject_reason, pattern=PAYMENT_REJECT_REASON_PATTERN),
        CallbackQueryHandler(handle_custom_reject_reason, pattern=PAYMENT_CUSTOM_REJECT_PATTERN),
        MessageHandler(filters.TEXT & filters.UpdateType.MESSAGE & (~filters.COMMAND) & 
                      filters.PRIVATE, handle_reject_reason_text),
    ]

async def send_payment_notification_to_group(
    context: ContextTypes.DEFAULT_TYPE,
    order_id: int,
    bank_card_id: int,
    payment_proof_img_url: str,
    payment_reference: str,
    user_id: int,
    username: str = None,
    amount: Optional[str] = None
) -> None:
    """
    Send payment notification to the appropriate admin group.
    
    Args:
        context: The context object
        order_id: The order ID
        bank_card_id: The bank card ID
        payment_proof_img_url: URL of the payment proof image
        payment_reference: Payment reference number
        user_id: User ID
        username: Optional username
        amount: Optional payment amount
    """
    try:
        # Get bank card details
        card_data = await api_client.get_bank_card_details(bank_card_id)
        if not card_data:
            logger.error(f"Could not fetch card details for ID {bank_card_id}")
            return
        
        # Get payment admin for this card
        admin_data = await api_client.get_payment_admin_for_card(bank_card_id)
        if not admin_data or not admin_data.get("admin_id") or not admin_data.get("telegram_group_id"):
            logger.error(f"No payment admin assigned for card {bank_card_id}")
            return
        
        admin_id = admin_data.get("admin_id")
        group_id = admin_data.get("telegram_group_id")
        
        # Get order details
        order_details = await api_client.get_order_details(order_id)
        if not order_details:
            logger.error(f"Could not fetch order details for ID {order_id}")
            return
        
        # Get user details
        user_data = await api_client.get_user_by_id(user_id)
        if not user_data:
            logger.error(f"Could not fetch user details for ID {user_id}")
            return
        
        # Format card number for display
        card_number = format_card_number(card_data.get("card_number", ""))
        
        # Create message with all payment details
        message = (
            f"💳 *پرداخت جدید*\n\n"
            f"🆔 شناسه سفارش: `{order_id}`\n"
            f"👤 کاربر: {username or user_data.get('telegram_username') or f'کاربر {user_id}'}\n"
            f"📱 شماره تماس: {user_data.get('phone_number', 'نامشخص')}\n"
            f"💰 مبلغ: {amount or order_details.get('amount', 'نامشخص')} تومان\n"
            f"🏦 بانک: {card_data.get('bank_name', 'نامشخص')}\n"
            f"💳 کارت: {card_number}\n"
            f"👤 به نام: {card_data.get('card_holder_name', 'نامشخص')}\n"
            f"🔢 شماره پیگیری: `{payment_reference}`\n"
            f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"*لطفاً پرداخت را بررسی کنید:*"
        )
        
        # Create inline keyboard with approve/reject buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"payment_approve_{order_id}"),
                InlineKeyboardButton("❌ رد پرداخت", callback_data=f"payment_reject_{order_id}")
            ]
        ]
        
        # Get the full image URL from the core API
        full_image_url = f"{api_client.BASE_URL}{payment_proof_img_url}"
        
        # Send the image with caption and buttons to the group
        try:
            msg = await context.bot.send_photo(
                chat_id=group_id,
                photo=full_image_url,
                caption=message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Update the message ID in the database to track this notification
            await api_client.update_payment_proof_telegram_msg_id(
                order_id=order_id,
                telegram_msg_id=msg.message_id,
                telegram_group_id=str(group_id)
            )
            
            logger.info(f"Payment notification sent to group {group_id} for order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending payment notification to group: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in send_payment_notification_to_group: {str(e)}")
        return False

async def handle_payment_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle payment approval button click."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Extract order_id from callback data
    match = re.match(PAYMENT_APPROVE_PATTERN, query.data)
    if not match:
        return
    
    order_id = int(match.group(1))
    
    # Check if user has permission to approve payments
    if not await is_payment_admin(user.id):
        await query.edit_message_reply_markup(None)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⛔ شما دسترسی لازم برای تایید پرداخت‌ها را ندارید.",
            reply_to_message_id=query.message.message_id
        )
        return
    
    # Show a processing message
    await query.edit_message_reply_markup(None)
    reply_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="⏳ در حال پردازش درخواست تایید پرداخت...",
        reply_to_message_id=query.message.message_id
    )
    
    # Confirm payment via API
    result = await api_client.confirm_order_payment(
        order_id=order_id,
        admin_id=user.id,
        admin_note=f"تایید توسط {user.first_name} (ID: {user.id}) در تلگرام"
    )
    
    # Check result
    if not result:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=reply_message.message_id,
            text="❌ خطا در تایید پرداخت. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
        return
    
    # Get subscription details if created
    subscription_id = result.get("subscription_id")
    subscription_details = None
    
    if subscription_id:
        subscription_details = await api_client.get_subscription_details(subscription_id)
    
    # Format success message
    success_message = (
        f"✅ *پرداخت با موفقیت تایید شد*\n\n"
        f"🆔 شناسه سفارش: `{order_id}`\n"
        f"👤 ادمین تایید‌کننده: {user.first_name}\n"
        f"⏰ زمان تایید: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    
    # Add subscription details if available
    if subscription_details:
        success_message += (
            f"\n*اشتراک ایجاد شده:*\n"
            f"📝 نام: {subscription_details.get('name', 'نامشخص')}\n"
            f"🔌 پروتکل: {subscription_details.get('protocol', 'نامشخص')}\n"
            f"📍 لوکیشن: {subscription_details.get('location', 'نامشخص')}\n"
            f"📅 تاریخ انقضا: {subscription_details.get('expiry_date', 'نامشخص')}\n"
        )
    else:
        success_message += "\n⚠️ اشتراک به صورت خودکار ایجاد نشد. لطفاً به صورت دستی بررسی کنید."
    
    # Update approval message
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=reply_message.message_id,
        text=success_message,
        parse_mode="Markdown"
    )
    
    # Send notification to user
    try:
        # Get the user ID from the order details
        order_details = await api_client.get_order_details(order_id)
        if order_details and "user_id" in order_details:
            user_id = order_details["user_id"]
            
            user_message = (
                f"✅ *پرداخت شما تایید شد*\n\n"
                f"🆔 شناسه سفارش: `{order_id}`\n"
                f"💰 مبلغ: {order_details.get('amount', 'نامشخص')} تومان\n"
                f"⏰ زمان تایید: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            
            if subscription_details:
                user_message += (
                    f"\n*جزئیات اشتراک:*\n"
                    f"📝 نام: {subscription_details.get('name', 'نامشخص')}\n"
                    f"🔌 پروتکل: {subscription_details.get('protocol', 'نامشخص')}\n"
                    f"📍 لوکیشن: {subscription_details.get('location', 'نامشخص')}\n"
                    f"📅 تاریخ انقضا: {subscription_details.get('expiry_date', 'نامشخص')}\n\n"
                    f"می‌توانید از بخش «اشتراک‌های من» جزئیات اتصال و QR کد را دریافت کنید."
                )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=user_message,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error sending notification to user: {str(e)}")

async def handle_payment_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle payment rejection button click."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Extract order_id from callback data
    match = re.match(PAYMENT_REJECT_PATTERN, query.data)
    if not match:
        return
    
    order_id = int(match.group(1))
    
    # Check if user has permission to reject payments
    if not await is_payment_admin(user.id):
        await query.edit_message_reply_markup(None)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⛔ شما دسترسی لازم برای رد پرداخت‌ها را ندارید.",
            reply_to_message_id=query.message.message_id
        )
        return
    
    # Show rejection reason options
    keyboard = []
    # Add predefined rejection reasons
    for reason_key, reason_text in REJECTION_REASONS.items():
        keyboard.append([
            InlineKeyboardButton(
                reason_text, 
                callback_data=f"payment_reject_reason_{order_id}_{reason_key}"
            )
        ])
    
    # Add custom rejection reason option
    keyboard.append([
        InlineKeyboardButton(
            "دلیل دیگر...", 
            callback_data=f"payment_custom_reject_{order_id}"
        )
    ])
    
    # Add cancel button
    keyboard.append([
        InlineKeyboardButton(
            "🔙 انصراف", 
            callback_data=f"payment_approve_{order_id}"
        )
    ])
    
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_payment_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle selection of a predefined rejection reason."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Extract order_id and reason from callback data
    match = re.match(PAYMENT_REJECT_REASON_PATTERN, query.data)
    if not match:
        return
    
    order_id = int(match.group(1))
    reason_key = match.group(2)
    
    # Get the reason text
    reason_text = REJECTION_REASONS.get(reason_key, "دلیل نامشخص")
    
    # Process the rejection
    await process_payment_rejection(
        update=update,
        context=context,
        order_id=order_id,
        reason=reason_text
    )

async def handle_custom_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle custom rejection reason selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract order_id from callback data
    match = re.match(PAYMENT_CUSTOM_REJECT_PATTERN, query.data)
    if not match:
        return
    
    order_id = int(match.group(1))
    
    # Store the order_id in user_data
    context.user_data["rejecting_order_id"] = order_id
    
    # Ask for custom reason
    await query.edit_message_reply_markup(None)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="لطفاً دلیل رد پرداخت را بنویسید:",
        reply_to_message_id=query.message.message_id
    )
    
    # Set the expected state for the next message
    context.user_data["waiting_for_reject_reason"] = True

async def handle_reject_reason_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle custom rejection reason text message."""
    # Check if we're waiting for a rejection reason
    if not context.user_data.get("waiting_for_reject_reason"):
        return
    
    # Get the order_id from user_data
    order_id = context.user_data.get("rejecting_order_id")
    if not order_id:
        return
    
    # Get the reason text from the message
    reason = update.message.text.strip()
    
    # Clear the waiting state
    context.user_data.pop("waiting_for_reject_reason", None)
    context.user_data.pop("rejecting_order_id", None)
    
    # Process the rejection
    await process_payment_rejection(
        update=update,
        context=context,
        order_id=order_id,
        reason=reason
    )

async def process_payment_rejection(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    order_id: int,
    reason: str
) -> None:
    """
    Process payment rejection with the given reason.
    
    Args:
        update: The update object
        context: The context object
        order_id: The order ID to reject
        reason: The rejection reason
    """
    user = update.effective_user
    
    # Show a processing message
    if update.callback_query:
        await update.callback_query.edit_message_reply_markup(None)
        reply_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⏳ در حال پردازش رد پرداخت...",
            reply_to_message_id=update.callback_query.message.message_id
        )
    else:
        reply_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⏳ در حال پردازش رد پرداخت...",
            reply_to_message_id=update.message.message_id
        )
    
    # Reject payment via API
    result = await api_client.reject_order_payment(
        order_id=order_id,
        admin_id=user.id,
        rejection_reason=reason
    )
    
    # Check result
    if not result:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=reply_message.message_id,
            text="❌ خطا در رد پرداخت. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
        return
    
    # Format success message
    success_message = (
        f"❌ *پرداخت رد شد*\n\n"
        f"🆔 شناسه سفارش: `{order_id}`\n"
        f"👤 ادمین: {user.first_name}\n"
        f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📝 دلیل: {reason}\n"
    )
    
    # Update rejection message
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=reply_message.message_id,
        text=success_message,
        parse_mode="Markdown"
    )
    
    # Send notification to user
    try:
        # Get the user ID from the order details
        order_details = await api_client.get_order_details(order_id)
        if order_details and "user_id" in order_details:
            user_id = order_details["user_id"]
            
            user_message = (
                f"❌ *پرداخت شما تایید نشد*\n\n"
                f"🆔 شناسه سفارش: `{order_id}`\n"
                f"💰 مبلغ: {order_details.get('amount', 'نامشخص')} تومان\n"
                f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📝 دلیل: {reason}\n\n"
                f"لطفاً با پشتیبانی تماس بگیرید یا مجدداً اقدام به پرداخت نمایید."
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=user_message,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error sending notification to user: {str(e)}")

def get_payment_notification_handlers():
    """Return a list of handlers for payment notifications."""
    return [
        CallbackQueryHandler(handle_payment_approve, pattern=PAYMENT_APPROVE_PATTERN),
        CallbackQueryHandler(handle_payment_reject, pattern=PAYMENT_REJECT_PATTERN),
        CallbackQueryHandler(handle_payment_reject_reason, pattern=PAYMENT_REJECT_REASON_PATTERN),
        CallbackQueryHandler(handle_custom_reject_reason, pattern=PAYMENT_CUSTOM_REJECT_PATTERN),
        MessageHandler(filters.TEXT & filters.UpdateType.MESSAGE & (~filters.COMMAND) & 
                      filters.PRIVATE, handle_reject_reason_text),
    ] 