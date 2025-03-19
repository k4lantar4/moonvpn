"""
Payment processing handler for the V2Ray Telegram bot.

This module implements handlers for payment operations including:
- Card-to-card payments
- Zarinpal payments
- Payment verification
- Transaction history
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from core.utils.i18n import get_text
from core.utils.formatting import format_number, format_date
from core.database import (
    get_user,
    get_user_language,
    update_user_language,
    get_db_connection,
)
from core.utils.api import create_payment, verify_payment
from core.utils.helpers import require_auth

logger = logging.getLogger(__name__)

# Conversation states
(
    SELECTING_ACTION,
    SELECTING_METHOD,
    ENTERING_AMOUNT,
    CONFIRMING_PAYMENT,
    ENTERING_RECEIPT,
    VERIFYING_PAYMENT,
) = range(6)

# Callback data patterns
PAYMENTS_CB = "payments"
CARD_PAYMENT = f"{PAYMENTS_CB}_card"
ZARINPAL_PAYMENT = f"{PAYMENTS_CB}_zarinpal"
TRANSACTION_HISTORY = f"{PAYMENTS_CB}_history"
VERIFY_PAYMENT = f"{PAYMENTS_CB}_verify"
CANCEL_PAYMENT = f"{PAYMENTS_CB}_cancel"

# Card payment details
CARD_NUMBER = "6037997599999999"  # Replace with actual card number
CARD_HOLDER = "نام صاحب حساب"  # Replace with actual card holder name
BANK_NAME = "بانک"  # Replace with actual bank name

@require_auth
async def payments_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display payment methods menu."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user's current balance
    user = get_user(user_id)
    balance = user.get("balance", 0) if user else 0
    
    # Get payment history count
    transactions = get_transactions(user_id)
    transaction_count = len(transactions) if transactions else 0
    
    # Create message with payment options
    message = get_text("payment_menu_info", language_code).format(
        balance=format_number(balance, language_code),
        transactions=transaction_count
    )
    
    # Build payment methods keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"💳 {get_text('card_payment', language_code)}",
                callback_data=CARD_PAYMENT
            )
        ]
    ]
    
    # Add Zarinpal payment if enabled in settings
    if get_setting("zarinpal_enabled") == "true":
        keyboard[0].append(
            InlineKeyboardButton(
                f"🛒 {get_text('zarinpal_payment', language_code)}",
                callback_data=ZARINPAL_PAYMENT
            )
        )
    
    # Add other options
    keyboard.append([
        InlineKeyboardButton(
            f"📊 {get_text('payment_history', language_code)}",
            callback_data=TRANSACTION_HISTORY
        ),
        InlineKeyboardButton(
            f"🔍 {get_text('verify_payment', language_code)}",
            callback_data=VERIFY_PAYMENT
        )
    ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("back_to_menu", language_code),
            callback_data="back_to_main"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    if query:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return SELECTING_ACTION

@require_auth
async def card_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle card payment selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Setup payment information in context
    context.user_data["payment_method"] = "card"
    
    # Get card details from settings
    card_number = get_setting("card_number") or CARD_NUMBER
    card_holder = get_setting("card_holder") or CARD_HOLDER
    bank_name = get_setting("bank_name") or BANK_NAME
    
    # Display card payment information
    message = get_text("card_payment_info", language_code).format(
        card_number=card_number,
        card_holder=card_holder,
        bank_name=bank_name
    )
    
    # Get preset amounts or use defaults
    preset_amounts = get_setting("preset_amounts")
    
    if preset_amounts:
        try:
            amounts = [int(amount.strip()) for amount in preset_amounts.split(",")]
        except:
            amounts = [100000, 200000, 500000]
    else:
        amounts = [100000, 200000, 500000]
    
    # Create keyboard with preset amounts
    amount_buttons = []
    for amount in amounts:
        amount_formatted = format_number(amount, language_code)
        amount_buttons.append(
            InlineKeyboardButton(
                f"{amount_formatted} {get_text('currency', language_code)}",
                callback_data=f"{PAYMENTS_CB}_amount:{amount}"
            )
        )
    
    # Split into rows of 2 buttons each
    amount_rows = [amount_buttons[i:i+2] for i in range(0, len(amount_buttons), 2)]
    
    keyboard = [
        *amount_rows,
        [
            InlineKeyboardButton(
                f"✏️ {get_text('custom_amount', language_code)}",
                callback_data=f"{PAYMENTS_CB}_enter_amount"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_payments", language_code),
                callback_data=PAYMENTS_CB
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ENTERING_AMOUNT

@require_auth
async def process_amount_preset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process preset payment amount selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Extract amount from callback data
    amount = int(query.data.split(":")[-1])
    
    # Store amount in context
    context.user_data["payment_amount"] = amount
    
    # Format amount for display
    formatted_amount = format_number(amount, language_code)
    
    # Create confirmation message
    message = get_text("confirm_payment", language_code).format(
        amount=formatted_amount,
        currency=get_text("currency", language_code)
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"✅ {get_text('confirm', language_code)}",
                callback_data=f"{PAYMENTS_CB}_confirm"
            ),
            InlineKeyboardButton(
                f"❌ {get_text('cancel', language_code)}",
                callback_data=CANCEL_PAYMENT
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return CONFIRMING_PAYMENT

@require_auth
async def process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process payment amount input."""
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Check if this is from a button or text input
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # If this is a preset amount, handle it differently
        if query.data.startswith(f"{PAYMENTS_CB}_amount:"):
            return await process_amount_preset(update, context)
        
        # This is the "enter custom amount" button
        message = get_text("enter_amount", language_code)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("back_to_payments", language_code),
                    callback_data=PAYMENTS_CB
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ENTERING_AMOUNT
    
    # This is text input
    try:
        # Parse amount from text
        amount_text = update.message.text.strip()
        
        # Remove commas and convert to integer
        amount = int(amount_text.replace(",", ""))
        
        # Check if amount is valid
        min_amount = int(get_setting("min_payment_amount") or 10000)
        max_amount = int(get_setting("max_payment_amount") or 10000000)
        
        if amount < min_amount:
            await update.message.reply_text(
                get_text("amount_too_small", language_code).format(
                    min_amount=format_number(min_amount, language_code)
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            return ENTERING_AMOUNT
        
        if amount > max_amount:
            await update.message.reply_text(
                get_text("amount_too_large", language_code).format(
                    max_amount=format_number(max_amount, language_code)
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            return ENTERING_AMOUNT
        
        # Store amount in context
        context.user_data["payment_amount"] = amount
        
        # Format amount for display
        formatted_amount = format_number(amount, language_code)
        
        # Create confirmation message
        message = get_text("confirm_payment", language_code).format(
            amount=formatted_amount,
            currency=get_text("currency", language_code)
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"✅ {get_text('confirm', language_code)}",
                    callback_data=f"{PAYMENTS_CB}_confirm"
                ),
                InlineKeyboardButton(
                    f"❌ {get_text('cancel', language_code)}",
                    callback_data=CANCEL_PAYMENT
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return CONFIRMING_PAYMENT
        
    except ValueError:
        # Invalid amount format
        await update.message.reply_text(
            get_text("invalid_amount", language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        return ENTERING_AMOUNT
    except Exception as e:
        logger.error(f"Error processing payment amount: {e}")
        await update.message.reply_text(
            get_text("error_general", language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        return ENTERING_AMOUNT

@require_auth
async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process payment confirmation."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    payment_method = context.user_data.get("payment_method")
    amount = context.user_data.get("payment_amount")
    
    # Process payment based on method
    if payment_method == "card":
        # Create card payment transaction
        transaction_id = create_transaction(
            user_id=user_id,
            amount=amount,
            payment_method="card",
            description="Card payment from Telegram bot"
        )
        
        if not transaction_id:
            await query.edit_message_text(
                get_text("payment_creation_error", language_code),
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END
        
        # Store transaction ID in context
        context.user_data["transaction_id"] = transaction_id
        
        # Get card details from settings
        card_number = get_setting("card_number") or CARD_NUMBER
        card_holder = get_setting("card_holder") or CARD_HOLDER
        bank_name = get_setting("bank_name") or BANK_NAME
        
        # Ask user to upload receipt
        message = get_text("card_payment_instructions", language_code).format(
            amount=format_number(amount, language_code),
            currency=get_text("currency", language_code),
            card_number=card_number,
            card_holder=card_holder,
            bank_name=bank_name
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"❌ {get_text('cancel_payment', language_code)}",
                    callback_data=CANCEL_PAYMENT
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ENTERING_RECEIPT
        
    elif payment_method == "zarinpal":
        # Create Zarinpal payment
        result = create_payment(
            user_id=user_id,
            amount=amount,
            description="Zarinpal payment from Telegram bot"
        )
        
        if not result or not result.get("success"):
            error_message = result.get("error_message", "Unknown error") if result else "Payment creation failed"
            await query.edit_message_text(
                get_text("payment_creation_error", language_code) + f"\n\n{error_message}",
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END
        
        # Get payment link and transaction ID
        payment_url = result.get("payment_url")
        transaction_id = result.get("transaction_id")
        
        # Store transaction ID in context
        context.user_data["transaction_id"] = transaction_id
        
        # Send payment link
        message = get_text("zarinpal_payment_link", language_code).format(
            amount=format_number(amount, language_code),
            currency=get_text("currency", language_code)
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"💳 {get_text('pay_now', language_code)}",
                    url=payment_url
                )
            ],
            [
                InlineKeyboardButton(
                    f"✅ {get_text('verify_payment', language_code)}",
                    callback_data=VERIFY_PAYMENT
                )
            ],
            [
                InlineKeyboardButton(
                    f"❌ {get_text('cancel_payment', language_code)}",
                    callback_data=CANCEL_PAYMENT
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return VERIFYING_PAYMENT
    
    # Unknown payment method
    await query.edit_message_text(
        get_text("error_general", language_code),
        parse_mode=ParseMode.MARKDOWN
    )
    return ConversationHandler.END

@require_auth
async def process_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process payment receipt."""
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    transaction_id = context.user_data.get("transaction_id")
    
    # Get receipt from message
    receipt = update.message.text.strip()
    
    # Update transaction with receipt number
    success = update_transaction(
        transaction_id=transaction_id,
        receipt_number=receipt,
        status="pending_verification"
    )
    
    if not success:
        await update.message.reply_text(
            get_text("error_general", language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # Send confirmation message
    message = get_text("receipt_received", language_code).format(
        transaction_id=transaction_id,
        receipt=receipt
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_menu", language_code),
                callback_data="back_to_main"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Notify admins about new payment
    await notify_admins_about_payment(transaction_id)
    
    return ConversationHandler.END

@require_auth
async def transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show transaction history."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get transactions
    transactions = get_transactions(user_id)
    
    if not transactions:
        message = get_text("no_transactions", language_code)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("back_to_payments", language_code),
                    callback_data=PAYMENTS_CB
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return SELECTING_ACTION
    
    # Create message with transaction list
    message = get_text("transaction_history", language_code) + "\n\n"
    
    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Add transactions to message
    for transaction in transactions[:10]:  # Show only 10 most recent
        status = transaction.get("status", "unknown")
        status_text = get_text(f"status_{status}", language_code)
        
        # Get emoji for status
        status_emoji = "✅" if status == "verified" else "⏳" if status == "pending_verification" else "❌" if status == "rejected" else "❓"
        
        # Format date
        created_at = transaction.get("created_at", "")
        date = format_date(created_at, language_code) if created_at else ""
        
        # Format amount
        amount = transaction.get("amount", 0)
        formatted_amount = format_number(amount, language_code) if amount else "0"
        
        # Add transaction to message
        message += f"{status_emoji} *{formatted_amount}* {get_text('currency', language_code)}\n"
        message += f"📅 {date} | 🔍 {status_text}\n"
        
        # Add reference if exists
        if transaction.get("receipt_number"):
            message += f"🧾 `{transaction.get('receipt_number')}`\n"
            
        message += "\n"
    
    # Add keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_payments", language_code),
                callback_data=PAYMENTS_CB
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_ACTION

@require_auth
async def verify_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verify payment status."""
    query = update.callback_query
    if query:
        await query.answer()
        
        # If it's not the verify payment callback, it's a message
        if query.data != VERIFY_PAYMENT:
            await query.edit_message_text(
                get_text("enter_transaction_id", context.user_data.get("language", "en")),
                parse_mode=ParseMode.MARKDOWN
            )
            return VERIFYING_PAYMENT
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get transaction ID from context or message
    transaction_id = context.user_data.get("transaction_id")
    
    if not transaction_id and update.message:
        transaction_id = update.message.text.strip()
    
    if not transaction_id:
        if update.message:
            await update.message.reply_text(
                get_text("enter_transaction_id", language_code),
                parse_mode=ParseMode.MARKDOWN
            )
        return VERIFYING_PAYMENT
    
    # Get transaction
    transaction = get_transaction(transaction_id)
    
    if not transaction:
        error_message = get_text("transaction_not_found", language_code)
        
        if update.message:
            await update.message.reply_text(
                error_message,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text(
                error_message,
                parse_mode=ParseMode.MARKDOWN
            )
        
        return VERIFYING_PAYMENT
    
    # Check if transaction belongs to user
    if transaction.get("user_id") != user_id:
        error_message = get_text("transaction_not_found", language_code)
        
        if update.message:
            await update.message.reply_text(
                error_message,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text(
                error_message,
                parse_mode=ParseMode.MARKDOWN
            )
        
        return VERIFYING_PAYMENT
    
    # Get status
    status = transaction.get("status", "unknown")
    status_text = get_text(f"status_{status}", language_code)
    
    # Format date
    created_at = transaction.get("created_at", "")
    date = format_date(created_at, language_code) if created_at else ""
    
    # Format amount
    amount = transaction.get("amount", 0)
    formatted_amount = format_number(amount, language_code) if amount else "0"
    
    # Create message
    message = get_text("transaction_details", language_code).format(
        transaction_id=transaction_id,
        amount=formatted_amount,
        currency=get_text("currency", language_code),
        status=status_text,
        date=date,
        payment_method=transaction.get("payment_method", "unknown")
    )
    
    # Add receipt if exists
    if transaction.get("receipt_number"):
        message += get_text("transaction_receipt", language_code).format(
            receipt=transaction.get("receipt_number")
        )
    
    # Add keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_payments", language_code),
                callback_data=PAYMENTS_CB
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return SELECTING_ACTION

@require_auth
async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel payment process."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get transaction ID
    transaction_id = context.user_data.get("transaction_id")
    
    # If transaction ID exists, update status
    if transaction_id:
        update_transaction(
            transaction_id=transaction_id,
            status="cancelled"
        )
    
    # Clear payment data from context
    for key in ["payment_method", "payment_amount", "transaction_id"]:
        if key in context.user_data:
            del context.user_data[key]
    
    # Send cancellation message
    message = get_text("payment_cancelled", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_payments", language_code),
                callback_data=PAYMENTS_CB
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_ACTION

async def notify_admins_about_payment(transaction_id: str) -> None:
    """Notify admins about new payment."""
    # Get transaction
    transaction = get_transaction(transaction_id)
    
    if not transaction:
        return
    
    # Get admin users
    admins = get_all_users(is_admin=True)
    
    if not admins:
        return
    
    # Get user who made the payment
    user_id = transaction.get("user_id")
    user = get_user(user_id)
    
    if not user:
        return
    
    # Format amount
    amount = transaction.get("amount", 0)
    
    # Create notification message
    message = f"🔔 *New Payment Notification*\n\n"
    message += f"User: {user.get('first_name')} (@{user.get('username')})\n"
    message += f"Amount: {format_number(amount)} {get_text('currency', 'en')}\n"
    message += f"Transaction ID: `{transaction_id}`\n"
    message += f"Receipt: `{transaction.get('receipt_number', 'N/A')}`\n\n"
    message += f"Please verify this payment in the admin panel."
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "Verify Payment",
                callback_data=f"admin_verify:{transaction_id}"
            ),
            InlineKeyboardButton(
                "Reject Payment",
                callback_data=f"admin_reject:{transaction_id}"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send notification to all admins
    for admin in admins:
        try:
            admin_id = admin.get("id")
            
            # Skip if admin is the user who made the payment
            if admin_id == user_id:
                continue
                
            # Send message to admin
            from telegram.error import TelegramError
            
            try:
                from telegram.ext import ApplicationBuilder
                application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
                
                await application.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            except TelegramError as e:
                logger.error(f"Error sending payment notification to admin {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Error notifying admin about payment: {e}")

@require_auth
async def zarinpal_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Zarinpal payment method."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = get_user_language(user_id) or "en"
    
    # Check if Zarinpal is enabled
    zarinpal_enabled = os.environ.get("ZARINPAL_ENABLED", "false").lower() == "true"
    
    if not zarinpal_enabled:
        await query.edit_message_text(
            get_text("zarinpal_not_enabled", language_code),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text("back", language_code), callback_data=PAYMENTS_CB)]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_ACTION
    
    # Ask for amount
    await query.edit_message_text(
        get_text("enter_payment_amount", language_code),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text("cancel", language_code), callback_data=PAYMENTS_CB)]
        ]),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Store payment method
    context.user_data["payment_method"] = "zarinpal"
    
    return ENTERING_AMOUNT

def get_payments_handler() -> ConversationHandler:
    """Get the payments conversation handler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(payments_menu, pattern=f"^{PAYMENTS_CB}$")
        ],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(card_payment, pattern=f"^{CARD_PAYMENT}$"),
                CallbackQueryHandler(zarinpal_payment, pattern=f"^{ZARINPAL_PAYMENT}$"),
                CallbackQueryHandler(transaction_history, pattern=f"^{TRANSACTION_HISTORY}$"),
                CallbackQueryHandler(verify_payment_status, pattern=f"^{VERIFY_PAYMENT}$"),
            ],
            SELECTING_METHOD: [
                CallbackQueryHandler(card_payment, pattern=f"^{CARD_PAYMENT}$"),
                CallbackQueryHandler(zarinpal_payment, pattern=f"^{ZARINPAL_PAYMENT}$"),
                CallbackQueryHandler(payments_menu, pattern=f"^{PAYMENTS_CB}$"),
            ],
            ENTERING_AMOUNT: [
                CallbackQueryHandler(process_amount_preset, pattern=f"^{PAYMENTS_CB}_amount:"),
                CallbackQueryHandler(process_amount, pattern=f"^{PAYMENTS_CB}_enter_amount$"),
                CallbackQueryHandler(payments_menu, pattern=f"^{PAYMENTS_CB}$"),
                CallbackQueryHandler(card_payment, pattern=f"^{CARD_PAYMENT}$"),
                CallbackQueryHandler(zarinpal_payment, pattern=f"^{ZARINPAL_PAYMENT}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_amount),
            ],
            CONFIRMING_PAYMENT: [
                CallbackQueryHandler(confirm_payment, pattern=f"^{PAYMENTS_CB}_confirm$"),
                CallbackQueryHandler(cancel_payment, pattern=f"^{CANCEL_PAYMENT}$"),
            ],
            ENTERING_RECEIPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_receipt),
                CallbackQueryHandler(cancel_payment, pattern=f"^{CANCEL_PAYMENT}$"),
            ],
            VERIFYING_PAYMENT: [
                CallbackQueryHandler(verify_payment_status, pattern=f"^{VERIFY_PAYMENT}$"),
                CallbackQueryHandler(cancel_payment, pattern=f"^{CANCEL_PAYMENT}$"),
                CallbackQueryHandler(payments_menu, pattern=f"^{PAYMENTS_CB}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, verify_payment_status),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(payments_menu, pattern=f"^{PAYMENTS_CB}$"),
            CallbackQueryHandler(cancel_payment, pattern=f"^{CANCEL_PAYMENT}$"),
        ],
        per_message=False,
    ) 