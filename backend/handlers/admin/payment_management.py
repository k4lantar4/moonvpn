"""
Payment Management for MoonVPN Telegram Bot Admin Panel.

This module provides the payment management functionality,
allowing administrators to manage payment methods and verify payments.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters
from telegram.constants import ParseMode

from core.utils.i18n import get_text, format_number
from core.utils.helpers import require_admin
from core.config import settings
from core.database import get_db
from core.models.transaction import Transaction
from core.models.system_config import SystemConfig
from core.models.user import User
from django.db.models import Sum, Count, Q

logger = logging.getLogger(__name__)

# Callback data prefixes
ADMIN_PREFIX = "admin"
PAYMENTS = f"{ADMIN_PREFIX}_payments"
PAYMENT_VIEW = f"{PAYMENTS}_view"
PAYMENT_APPROVE = f"{PAYMENTS}_approve"
PAYMENT_REJECT = f"{PAYMENTS}_reject"
PAYMENT_PENDING = f"{PAYMENTS}_pending"
PAYMENT_CARD = f"{PAYMENTS}_card"
PAYMENT_ZARINPAL = f"{PAYMENTS}_zarinpal"
PAYMENT_UPDATE_CARD = f"{PAYMENTS}_update_card"
DASHBOARD = f"{ADMIN_PREFIX}_dashboard"

# Conversation states
(
    WAITING_FOR_INPUT,
    UPDATING_CARD,
    VIEWING_PAYMENT,
) = range(3)

@require_admin
async def payment_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display payment management options and statistics."""
    user = update.effective_user
    user_id = user.id
    language_code = context.user_data.get("language", "en")
    
    logger.info(f"Admin {user_id} ({user.username}) accessed payment management")
    
    # Get system config
    system_config, created = SystemConfig.objects.get_or_create(id=1)
    
    # Get payment statistics
    total_transactions = Transaction.objects.count()
    completed_transactions = Transaction.objects.filter(status='completed').count()
    pending_transactions = Transaction.objects.filter(status='pending_verification').count()
    rejected_transactions = Transaction.objects.filter(status='rejected').count()
    
    # Get revenue statistics
    total_revenue = Transaction.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get today's revenue
    today = datetime.datetime.now().date()
    today_revenue = Transaction.objects.filter(
        status='completed',
        completed_at__date=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get this month's revenue
    first_day_of_month = today.replace(day=1)
    this_month_revenue = Transaction.objects.filter(
        status='completed',
        completed_at__date__gte=first_day_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Create message
    message = f"💰 **{get_text('payment_management', language_code)}**\n\n"
    message += f"📊 **{get_text('payment_statistics', language_code)}**:\n"
    message += f"• {get_text('total_transactions', language_code)}: {total_transactions}\n"
    message += f"• {get_text('completed_transactions', language_code)}: {completed_transactions}\n"
    message += f"• {get_text('pending_transactions', language_code)}: {pending_transactions}\n"
    message += f"• {get_text('rejected_transactions', language_code)}: {rejected_transactions}\n\n"
    
    message += f"💵 **{get_text('revenue_statistics', language_code)}**:\n"
    message += f"• {get_text('total_revenue', language_code)}: {format_number(total_revenue)} {get_text('currency', language_code)}\n"
    message += f"• {get_text('today_revenue', language_code)}: {format_number(today_revenue)} {get_text('currency', language_code)}\n"
    message += f"• {get_text('month_revenue', language_code)}: {format_number(this_month_revenue)} {get_text('currency', language_code)}\n\n"
    
    message += f"⚙️ **{get_text('payment_methods', language_code)}**:\n"
    
    # Card payment
    card_status = get_text("enabled", language_code) if system_config.card_payment_enabled else get_text("disabled", language_code)
    message += f"💳 {get_text('card_payment', language_code)}: {card_status}\n"
    if system_config.card_payment_enabled and system_config.card_number:
        message += f"  • {get_text('card_number', language_code)}: `{system_config.card_number}`\n"
        message += f"  • {get_text('card_holder', language_code)}: {system_config.card_holder or 'N/A'}\n"
    
    # Zarinpal payment
    zarinpal_status = get_text("enabled", language_code) if system_config.zarinpal_enabled else get_text("disabled", language_code)
    message += f"🔵 {get_text('zarinpal_payment', language_code)}: {zarinpal_status}\n\n"
    
    message += f"🔍 {get_text('select_action', language_code)}:"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'❌' if system_config.card_payment_enabled else '✅'} {get_text('toggle_card_payment', language_code)}",
                callback_data=f"{PAYMENT_CARD}_toggle"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'❌' if system_config.zarinpal_enabled else '✅'} {get_text('toggle_zarinpal', language_code)}",
                callback_data=f"{PAYMENT_ZARINPAL}_toggle"
            )
        ]
    ]
    
    # Add update card info button if card payment is enabled
    if system_config.card_payment_enabled:
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ {get_text('update_card_info', language_code)}",
                callback_data=PAYMENT_UPDATE_CARD
            )
        ])
    
    # Add view pending payments button if there are pending payments
    if pending_transactions > 0:
        keyboard.append([
            InlineKeyboardButton(
                f"👁️ {get_text('view_pending_payments', language_code)} ({pending_transactions})",
                callback_data=f"{PAYMENT_PENDING}:1"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            f"🔙 {get_text('back_to_dashboard', language_code)}",
            callback_data=DASHBOARD
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message based on update type
    if update.callback_query:
        await update.callback_query.edit_message_text(
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
    
    return WAITING_FOR_INPUT

async def toggle_card_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle card payment method."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get system config
    system_config, created = SystemConfig.objects.get_or_create(id=1)
    
    # Toggle card payment
    system_config.card_payment_enabled = not system_config.card_payment_enabled
    system_config.save()
    
    # Log action
    logger.info(f"Admin {user.id} ({user.username}) {'enabled' if system_config.card_payment_enabled else 'disabled'} card payment")
    
    # Show success message
    status = get_text("enabled", language_code) if system_config.card_payment_enabled else get_text("disabled", language_code)
    await query.answer(
        f"{get_text('card_payment', language_code)} {status}",
        show_alert=True
    )
    
    # Return to payment management
    return await payment_management(update, context)

async def toggle_zarinpal_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle Zarinpal payment method."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get system config
    system_config, created = SystemConfig.objects.get_or_create(id=1)
    
    # Toggle Zarinpal payment
    system_config.zarinpal_enabled = not system_config.zarinpal_enabled
    system_config.save()
    
    # Log action
    logger.info(f"Admin {user.id} ({user.username}) {'enabled' if system_config.zarinpal_enabled else 'disabled'} Zarinpal payment")
    
    # Show success message
    status = get_text("enabled", language_code) if system_config.zarinpal_enabled else get_text("disabled", language_code)
    await query.answer(
        f"{get_text('zarinpal_payment', language_code)} {status}",
        show_alert=True
    )
    
    # Return to payment management
    return await payment_management(update, context)

async def update_card_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Update card information."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Create message
    message = f"✏️ **{get_text('update_card_info', language_code)}**\n\n"
    message += get_text('update_card_instructions', language_code) + "\n\n"
    message += get_text('card_format_example', language_code) + "\n"
    message += "```\n6037-9912-3456-7890\nJohn Doe\nBank Name\n```"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔙 {get_text('back', language_code)}",
                callback_data=PAYMENTS
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return UPDATING_CARD

async def process_card_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process card information update."""
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get card information
    card_info = update.message.text.strip().split('\n')
    
    if len(card_info) < 2:
        await update.message.reply_text(
            get_text('invalid_card_format', language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        return UPDATING_CARD
    
    try:
        # Get system config
        system_config, created = SystemConfig.objects.get_or_create(id=1)
        
        # Update card information
        system_config.card_number = card_info[0].strip()
        system_config.card_holder = card_info[1].strip()
        
        if len(card_info) > 2:
            system_config.bank_name = card_info[2].strip()
        
        system_config.save()
        
        # Log action
        logger.info(f"Admin {user.id} ({user.username}) updated card information")
        
        # Show success message
        await update.message.reply_text(
            get_text('card_update_success', language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Return to payment management
        return await payment_management(update, context)
    
    except Exception as e:
        logger.error(f"Error updating card information: {e}")
        await update.message.reply_text(
            get_text('error_general', language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        return UPDATING_CARD

async def list_pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """List pending payments with pagination."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get page number from callback data
    callback_data = query.data
    page = int(callback_data.split(":")[-1])
    
    # Payments per page
    payments_per_page = 5
    
    # Get pending payments for current page
    start_idx = (page - 1) * payments_per_page
    end_idx = start_idx + payments_per_page
    
    pending_payments = Transaction.objects.filter(
        status='pending_verification'
    ).order_by('-created_at')[start_idx:end_idx]
    
    # Get total number of pending payments
    total_pending = Transaction.objects.filter(status='pending_verification').count()
    total_pages = (total_pending + payments_per_page - 1) // payments_per_page
    
    # Create message
    message = f"👁️ **{get_text('pending_payments', language_code)}**\n"
    
    if total_pending == 0:
        message += get_text('no_pending_payments', language_code)
    else:
        message += f"{get_text('page', language_code)} {page}/{total_pages}\n\n"
        
        for idx, payment in enumerate(pending_payments, start=1):
            # Get user information
            try:
                payment_user = User.objects.get(id=payment.user_id)
                user_info = f"*{payment_user.first_name or 'User'}* (@{payment_user.username or 'no_username'})"
            except User.DoesNotExist:
                user_info = get_text('unknown_user', language_code)
            
            message += f"💰 **{get_text('payment', language_code)} #{payment.id}**\n"
            message += f"👤 {get_text('user', language_code)}: {user_info}\n"
            message += f"💵 {get_text('amount', language_code)}: {format_number(payment.amount)} {get_text('currency', language_code)}\n"
            message += f"📅 {get_text('date', language_code)}: {payment.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            message += f"🔢 {get_text('transaction_id', language_code)}: `{payment.transaction_id or 'N/A'}`\n"
            message += f"📝 {get_text('description', language_code)}: {payment.description or 'N/A'}\n\n"
            
            # Add view button inline instead of as a URL
            keyboard_row = [
                InlineKeyboardButton(
                    f"👁️ {get_text('view_payment', language_code)}",
                    callback_data=f"{PAYMENT_VIEW}:{payment.id}"
                ),
                InlineKeyboardButton(
                    f"✅ {get_text('approve', language_code)}",
                    callback_data=f"{PAYMENT_APPROVE}:{payment.id}"
                ),
                InlineKeyboardButton(
                    f"❌ {get_text('reject', language_code)}",
                    callback_data=f"{PAYMENT_REJECT}:{payment.id}"
                )
            ]
            
            # Create keyboard with actions for each payment
            if idx == 1:
                keyboard = [keyboard_row]
            else:
                keyboard.append(keyboard_row)
    
    # Create keyboard with pagination
    
    # Add pagination buttons
    if total_pending > 0:
        pagination_row = []
        
        if page > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    "◀️",
                    callback_data=f"{PAYMENT_PENDING}:{page-1}"
                )
            )
        
        if page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    "▶️",
                    callback_data=f"{PAYMENT_PENDING}:{page+1}"
                )
            )
        
        if pagination_row:
            keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            f"🔙 {get_text('back', language_code)}",
            callback_data=PAYMENTS
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return WAITING_FOR_INPUT

async def view_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: Optional[int] = None) -> int:
    """View detailed information about a payment."""
    language_code = context.user_data.get("language", "en")
    
    try:
        # Determine if we're coming from a callback query or direct function call
        if payment_id is None:
            query = update.callback_query
            await query.answer()
            
            # Extract payment ID from callback data
            callback_data = query.data
            payment_id = int(callback_data.split(":")[-1])
        
        # Get payment from database
        payment = Transaction.objects.get(id=payment_id)
        
        # Get user information
        try:
            payment_user = User.objects.get(id=payment.user_id)
            user_info = f"*{payment_user.first_name or 'User'}* (@{payment_user.username or 'no_username'})"
            user_id = payment_user.user_id
        except User.DoesNotExist:
            user_info = get_text('unknown_user', language_code)
            user_id = "N/A"
        
        # Create message
        message = f"💰 **{get_text('payment_details', language_code)}**\n\n"
        
        # Payment information
        message += f"🆔 {get_text('payment_id', language_code)}: `{payment.id}`\n"
        message += f"👤 {get_text('user', language_code)}: {user_info}\n"
        message += f"🆔 {get_text('user_id', language_code)}: `{user_id}`\n"
        message += f"💵 {get_text('amount', language_code)}: {format_number(payment.amount)} {get_text('currency', language_code)}\n"
        message += f"📅 {get_text('created_at', language_code)}: {payment.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        message += f"🔢 {get_text('transaction_id', language_code)}: `{payment.transaction_id or 'N/A'}`\n"
        message += f"📝 {get_text('description', language_code)}: {payment.description or 'N/A'}\n"
        message += f"📊 {get_text('status', language_code)}: {get_text(payment.status, language_code)}\n\n"
        
        if payment.status == 'completed':
            message += f"✅ {get_text('completed_at', language_code)}: {payment.completed_at.strftime('%Y-%m-%d %H:%M')}\n"
        elif payment.status == 'rejected':
            message += f"❌ {get_text('rejected_at', language_code)}: {payment.rejected_at.strftime('%Y-%m-%d %H:%M')}\n"
            message += f"❌ {get_text('rejection_reason', language_code)}: {payment.rejection_reason or 'N/A'}\n"
        
        # Create keyboard
        keyboard = []
        
        # Add payment management buttons
        if payment.status == 'pending_verification':
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ {get_text('approve_payment', language_code)}",
                    callback_data=f"{PAYMENT_APPROVE}:{payment.id}"
                ),
                InlineKeyboardButton(
                    f"❌ {get_text('reject_payment', language_code)}",
                    callback_data=f"{PAYMENT_REJECT}:{payment.id}"
                )
            ])
        
        # Add back button
        keyboard.append([
            InlineKeyboardButton(
                f"🔙 {get_text('back', language_code)}",
                callback_data=PAYMENTS
            )
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send or edit message based on update type
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
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
        
        return VIEWING_PAYMENT
    
    except Transaction.DoesNotExist:
        # Payment not found
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                get_text('payment_not_found', language_code),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            f"🔙 {get_text('back', language_code)}",
                            callback_data=PAYMENTS
                        )
                    ]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                get_text('payment_not_found', language_code),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_INPUT
    
    except Exception as e:
        logger.error(f"Error viewing payment: {e}")
        
        # Handle error
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                get_text('error_general', language_code),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            f"🔙 {get_text('back', language_code)}",
                            callback_data=PAYMENTS
                        )
                    ]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                get_text('error_general', language_code),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_INPUT

async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Approve a pending payment."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Extract payment ID from callback data
    callback_data = query.data
    payment_id = int(callback_data.split(":")[-1])
    
    try:
        # Get payment from database
        payment = Transaction.objects.get(id=payment_id)
        
        # Check if payment is already processed
        if payment.status != 'pending_verification':
            await query.answer(
                get_text('payment_already_processed', language_code),
                show_alert=True
            )
            return await view_payment(update, context, payment_id)
        
        # Approve payment
        payment.status = 'completed'
        payment.completed_at = datetime.datetime.now()
        payment.save()
        
        # Log action
        logger.info(f"Admin {user.id} ({user.username}) approved payment {payment.id}")
        
        # Show success message
        await query.answer(
            get_text('payment_approved_success', language_code),
            show_alert=True
        )
        
        # TODO: Process subscription or account creation based on payment purpose
        
        # View updated payment
        return await view_payment(update, context, payment_id)
    
    except Transaction.DoesNotExist:
        await query.answer(
            get_text('payment_not_found', language_code),
            show_alert=True
        )
        return WAITING_FOR_INPUT
    
    except Exception as e:
        logger.error(f"Error approving payment: {e}")
        await query.answer(
            get_text('error_general', language_code),
            show_alert=True
        )
        return WAITING_FOR_INPUT

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Reject a pending payment."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Extract payment ID from callback data
    callback_data = query.data
    payment_id = int(callback_data.split(":")[-1])
    
    try:
        # Get payment from database
        payment = Transaction.objects.get(id=payment_id)
        
        # Check if payment is already processed
        if payment.status != 'pending_verification':
            await query.answer(
                get_text('payment_already_processed', language_code),
                show_alert=True
            )
            return await view_payment(update, context, payment_id)
        
        # Reject payment
        payment.status = 'rejected'
        payment.rejected_at = datetime.datetime.now()
        payment.rejection_reason = "Administrative action"
        payment.save()
        
        # Log action
        logger.info(f"Admin {user.id} ({user.username}) rejected payment {payment.id}")
        
        # Show success message
        await query.answer(
            get_text('payment_rejected_success', language_code),
            show_alert=True
        )
        
        # View updated payment
        return await view_payment(update, context, payment_id)
    
    except Transaction.DoesNotExist:
        await query.answer(
            get_text('payment_not_found', language_code),
            show_alert=True
        )
        return WAITING_FOR_INPUT
    
    except Exception as e:
        logger.error(f"Error rejecting payment: {e}")
        await query.answer(
            get_text('error_general', language_code),
            show_alert=True
        )
        return WAITING_FOR_INPUT

def get_payment_management_handlers() -> List:
    """Get handlers for payment management."""
    return [
        CallbackQueryHandler(payment_management, pattern=f"^{PAYMENTS}$"),
        CallbackQueryHandler(toggle_card_payment, pattern=f"^{PAYMENT_CARD}_toggle$"),
        CallbackQueryHandler(toggle_zarinpal_payment, pattern=f"^{PAYMENT_ZARINPAL}_toggle$"),
        CallbackQueryHandler(update_card_info, pattern=f"^{PAYMENT_UPDATE_CARD}$"),
        CallbackQueryHandler(list_pending_payments, pattern=f"^{PAYMENT_PENDING}:"),
        CallbackQueryHandler(view_payment, pattern=f"^{PAYMENT_VIEW}:"),
        CallbackQueryHandler(approve_payment, pattern=f"^{PAYMENT_APPROVE}:"),
        CallbackQueryHandler(reject_payment, pattern=f"^{PAYMENT_REJECT}:"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_update),
    ] 