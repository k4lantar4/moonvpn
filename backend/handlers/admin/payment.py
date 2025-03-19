"""
Payment management handlers.

This module contains handlers for managing payments.
"""

from datetime import datetime
from typing import Dict, List, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from utils import get_text, format_number, format_date
from decorators import require_admin
from api_client import (
    get_payments,
    get_payment,
    update_payment,
    delete_payment,
)
from .constants import SELECTING_PAYMENT, ENTERING_PAYMENT_NOTES, ADMIN_MENU
from .notification_hooks import hook_payment_processed

@require_admin
async def payment_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display list of payments for admin verification."""
    query = update.callback_query
    await query.answer()
    
    # Get status filter from context if available, default to "all"
    status_filter = context.user_data.get("payment_status_filter", "all")
    
    # Get list of payments from API
    if status_filter != "all":
        payments = get_payments(status=status_filter)
    else:
        payments = get_payments()
    
    if not payments:
        # No payments matching the filter
        filter_msg = f" با وضعیت {status_filter}" if status_filter != "all" else ""
        
        keyboard = [
            [InlineKeyboardButton("🔍 تغییر فیلتر", callback_data="payment_change_filter")],
            [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"💰 پرداخت‌ها{filter_msg}\n\nهیچ پرداختی یافت نشد.",
            reply_markup=reply_markup
        )
        
        return SELECTING_PAYMENT
    
    # Sort payments by creation date, newest first
    payments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Create message showing current filter
    filter_msg = f"فیلتر فعلی: {status_filter}" if status_filter != "all" else "نمایش همه پرداخت‌ها"
    message = f"💰 مدیریت پرداخت‌ها\n\n{filter_msg}\n\n"
    
    # Show only first 10 payments to avoid message size limits
    display_payments = payments[:10]
    
    # Create keyboard with payment options
    keyboard = []
    
    for payment in display_payments:
        # Format date
        created_at = payment.get('created_at', '')
        payment_date = created_at[:10] if created_at else 'N/A'
        
        # Format amount
        amount = payment.get('amount', 0)
        
        # Get payment status and emoji
        status = payment.get('status', 'unknown')
        status_emoji = {
            'pending': '⏳',
            'completed': '✅',
            'failed': '❌',
            'refunded': '↩️',
            'expired': '⏰'
        }.get(status, '❓')
        
        # Get username
        user = payment.get('user', {})
        username = user.get('username', 'Unknown') if isinstance(user, dict) else 'Unknown'
        
        payment_id = payment.get('id', 0)
        
        keyboard.append([
            InlineKeyboardButton(
                f"{status_emoji} {username} - {amount:,} تومان - {payment_date}",
                callback_data=f"payment_details:{payment_id}"
            )
        ])
    
    # Add pagination if there are more than 10 payments
    if len(payments) > 10:
        keyboard.append([
            InlineKeyboardButton("📄 بعدی", callback_data="payment_list:2")
        ])
    
    # Add filter and management buttons
    keyboard.append([
        InlineKeyboardButton("🔍 تغییر فیلتر", callback_data="payment_change_filter"),
        InlineKeyboardButton("🔄 به‌روزرسانی", callback_data="admin_payments")
    ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup
    )
    
    return SELECTING_PAYMENT

@require_admin
async def payment_list_paginated(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display paginated list of payments."""
    query = update.callback_query
    await query.answer()
    
    # Get page number from callback data
    page = int(query.data.split(":")[1])
    
    # Get status filter from context if available, default to "all"
    status_filter = context.user_data.get("payment_status_filter", "all")
    
    # Get list of payments from API
    if status_filter != "all":
        payments = get_payments(status=status_filter)
    else:
        payments = get_payments()
    
    if not payments:
        # No payments matching the filter
        filter_msg = f" با وضعیت {status_filter}" if status_filter != "all" else ""
        
        keyboard = [
            [InlineKeyboardButton("🔍 تغییر فیلتر", callback_data="payment_change_filter")],
            [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"💰 پرداخت‌ها{filter_msg}\n\nهیچ پرداختی یافت نشد.",
            reply_markup=reply_markup
        )
        
        return SELECTING_PAYMENT
    
    # Sort payments by creation date, newest first
    payments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Calculate pagination
    items_per_page = 10
    total_pages = (len(payments) + items_per_page - 1) // items_per_page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(payments))
    
    # Create keyboard with payment options
    keyboard = []
    
    # Create message showing current filter and page
    filter_msg = f"فیلتر فعلی: {status_filter}" if status_filter != "all" else "نمایش همه پرداخت‌ها"
    message = f"💰 مدیریت پرداخت‌ها (صفحه {page}/{total_pages})\n\n{filter_msg}\n\n"
    
    for payment in payments[start_idx:end_idx]:
        # Format date
        created_at = payment.get('created_at', '')
        payment_date = created_at[:10] if created_at else 'N/A'
        
        # Format amount
        amount = payment.get('amount', 0)
        
        # Get payment status and emoji
        status = payment.get('status', 'unknown')
        status_emoji = {
            'pending': '⏳',
            'completed': '✅',
            'failed': '❌',
            'refunded': '↩️',
            'expired': '⏰'
        }.get(status, '❓')
        
        # Get username
        user = payment.get('user', {})
        username = user.get('username', 'Unknown') if isinstance(user, dict) else 'Unknown'
        
        payment_id = payment.get('id', 0)
        
        keyboard.append([
            InlineKeyboardButton(
                f"{status_emoji} {username} - {amount:,} تومان - {payment_date}",
                callback_data=f"payment_details:{payment_id}"
            )
        ])
    
    # Add pagination buttons if needed
    pagination = []
    if page > 1:
        pagination.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"payment_list:{page-1}"))
    if page < total_pages:
        pagination.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"payment_list:{page+1}"))
    
    if pagination:
        keyboard.append(pagination)
    
    # Add filter and management buttons
    keyboard.append([
        InlineKeyboardButton("🔍 تغییر فیلتر", callback_data="payment_change_filter"),
        InlineKeyboardButton("🔄 به‌روزرسانی", callback_data="admin_payments")
    ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup
    )
    
    return SELECTING_PAYMENT

@require_admin
async def payment_change_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Change the payment status filter."""
    query = update.callback_query
    await query.answer()
    
    # Show filter options
    keyboard = [
        [
            InlineKeyboardButton("🌐 همه", callback_data="payment_set_filter:all"),
            InlineKeyboardButton("⏳ در انتظار", callback_data="payment_set_filter:pending")
        ],
        [
            InlineKeyboardButton("✅ تکمیل شده", callback_data="payment_set_filter:completed"),
            InlineKeyboardButton("❌ ناموفق", callback_data="payment_set_filter:failed")
        ],
        [
            InlineKeyboardButton("↩️ بازگشت داده شده", callback_data="payment_set_filter:refunded"),
            InlineKeyboardButton("⏰ منقضی شده", callback_data="payment_set_filter:expired")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data="admin_payments")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔍 وضعیت پرداخت مورد نظر را برای فیلتر کردن انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return SELECTING_PAYMENT

@require_admin
async def payment_set_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set the payment status filter."""
    query = update.callback_query
    await query.answer()
    
    # Get status from callback data
    status = query.data.split(":")[1]
    
    # Store in context
    context.user_data["payment_status_filter"] = status
    
    # Return to payment list with new filter
    return await payment_list(update, context)

@require_admin
async def payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display payment details."""
    query = update.callback_query
    await query.answer()
    
    # Extract payment ID from callback data
    payment_id = int(query.data.split(":")[1])
    
    # Store in context for later use
    context.user_data["current_payment_id"] = payment_id
    
    # Get payment details from API
    payment = get_payment(payment_id)
    
    if not payment:
        # Payment not found
        await query.edit_message_text(
            "❌ پرداخت مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data="admin_payments")]
            ])
        )
        return SELECTING_PAYMENT
    
    # Format payment details
    created_at = payment.get('created_at', '')
    payment_date = created_at[:19].replace('T', ' ') if created_at else 'N/A'
    updated_at = payment.get('updated_at', '')
    updated_date = updated_at[:19].replace('T', ' ') if updated_at else 'N/A'
    
    # Get payment amount
    amount = payment.get('amount', 0)
    
    # Get payment method
    payment_method = payment.get('payment_method', 'Unknown')
    
    # Get payment status and emoji
    status = payment.get('status', 'unknown')
    status_emoji = {
        'pending': '⏳',
        'completed': '✅',
        'failed': '❌',
        'refunded': '↩️',
        'expired': '⏰'
    }.get(status, '❓')
    
    # Get user info
    user = payment.get('user', {})
    if isinstance(user, dict):
        username = user.get('username', 'Unknown')
        user_id = user.get('id', 'Unknown')
        user_info = f"👤 کاربر: {username} (ID: {user_id})\n"
    else:
        user_info = "👤 کاربر: نامشخص\n"
    
    # Check if payment is associated with a subscription
    subscription_info = ""
    subscription = payment.get('subscription', None)
    if subscription:
        sub_id = subscription.get('id', 'Unknown')
        plan_name = subscription.get('plan', {}).get('name', 'Unknown')
        subscription_info = f"🔄 اشتراک: {plan_name} (ID: {sub_id})\n"
    
    # Get transaction ID if available
    transaction_id = payment.get('transaction_id', 'N/A')
    transaction_info = f"🧾 شناسه تراکنش: {transaction_id}\n" if transaction_id != 'N/A' else ""
    
    # Get payment notes if available
    notes = payment.get('notes', '')
    notes_info = f"📝 یادداشت‌ها: {notes}\n" if notes else ""
    
    # Create detailed message
    message = (
        f"💰 جزئیات پرداخت (ID: {payment_id})\n\n"
        f"{user_info}"
        f"💲 مبلغ: {amount:,} تومان\n"
        f"🏦 روش پرداخت: {payment_method}\n"
        f"🚦 وضعیت: {status_emoji} {status}\n"
        f"{subscription_info}"
        f"{transaction_info}"
        f"{notes_info}"
        f"🕒 تاریخ ایجاد: {payment_date}\n"
        f"🔄 آخرین بروزرسانی: {updated_date}"
    )
    
    # Create keyboard with action buttons based on payment status
    keyboard = []
    
    if status == 'pending':
        keyboard.append([
            InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"payment_approve:{payment_id}"),
            InlineKeyboardButton("❌ رد پرداخت", callback_data=f"payment_reject:{payment_id}")
        ])
    elif status == 'completed':
        keyboard.append([
            InlineKeyboardButton("↩️ بازگشت وجه", callback_data=f"payment_refund:{payment_id}")
        ])
    
    # Add note button
    keyboard.append([
        InlineKeyboardButton("📝 افزودن یادداشت", callback_data=f"payment_add_note:{payment_id}")
    ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data="admin_payments")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return SELECTING_PAYMENT

@require_admin
async def payment_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Approve a payment."""
    query = update.callback_query
    await query.answer()
    
    # Extract payment ID from callback data
    payment_id = query.data.split(":")[-1]
    
    # Get payment details
    payment_details = get_payment(payment_id)
    
    if not payment_details:
        await query.edit_message_text(
            "❌ پرداخت مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data=PAYMENT_MANAGEMENT)]
            ])
        )
        return SELECTING_PAYMENT
    
    message = (
        f"💰 *تایید پرداخت*\n\n"
        f"آیا از تایید این پرداخت اطمینان دارید؟\n\n"
        f"• شناسه پرداخت: `{payment_id}`\n"
        f"• مبلغ: {format_number(payment_details.get('amount', 0))} تومان\n"
        f"• کاربر: {payment_details.get('user_name', 'ناشناس')}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ تایید نهایی", 
                callback_data=f"payment_approve_confirm:{payment_id}"
            ),
            InlineKeyboardButton(
                "❌ انصراف", 
                callback_data=f"payment_details:{payment_id}"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PAYMENT

@require_admin
async def payment_process_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process payment approval."""
    query = update.callback_query
    await query.answer()
    
    # Extract payment ID from callback data
    payment_id = query.data.split(":")[-1]
    
    # Get admin info
    admin_id = query.from_user.id
    admin_username = query.from_user.username or query.from_user.first_name
    
    # Approve payment using API
    approval_result = approve_payment(payment_id, admin_id, admin_username)
    
    if approval_result.get('success', False):
        # Get updated payment details for notification
        payment_details = get_payment(payment_id)
        
        if payment_details:
            # Add admin info to payment details
            payment_details['admin_id'] = admin_id
            payment_details['admin_username'] = admin_username
            
            # Add timestamp for notification
            payment_details['updated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Send notification to management groups
            try:
                notification_sent = await hook_payment_processed(context.bot, payment_details, approved=True)
                if not notification_sent:
                    logger.warning(f"Failed to send payment approval notification for payment: {payment_id}")
            except Exception as e:
                logger.error(f"Failed to send payment approval notification: {str(e)}")
        
        # Success message
        message = (
            f"✅ *پرداخت با موفقیت تایید شد*\n\n"
            f"• شناسه پرداخت: `{payment_id}`\n"
            f"• تایید‌کننده: @{admin_username}\n\n"
            f"اکانت کاربر با موفقیت فعال شد."
        )
    else:
        # Error message
        error = approval_result.get('message', 'خطای نامشخص')
        message = (
            f"❌ *خطا در تایید پرداخت*\n\n"
            f"• شناسه پرداخت: `{payment_id}`\n"
            f"• خطا: {error}"
        )
    
    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 بازگشت به لیست پرداخت‌ها", 
                callback_data=PAYMENT_MANAGEMENT
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PAYMENT

@require_admin
async def payment_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Reject a pending payment."""
    query = update.callback_query
    await query.answer()
    
    # Get payment ID from callback data
    payment_id = int(query.data.split(":")[1])
    
    # Ask for rejection reason
    await query.edit_message_text(
        "❓ لطفاً دلیل رد پرداخت را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data=f"payment_details:{payment_id}")]
        ])
    )
    
    # Store payment ID for later use
    context.user_data["rejecting_payment_id"] = payment_id
    
    # Switch to waiting for text input
    return ENTERING_PAYMENT_NOTES

@require_admin
async def payment_add_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Add a note to a payment."""
    query = update.callback_query
    await query.answer()
    
    # Get payment ID from callback data
    payment_id = int(query.data.split(":")[1])
    
    # Ask for note text
    await query.edit_message_text(
        "📝 لطفاً یادداشت خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data=f"payment_details:{payment_id}")]
        ])
    )
    
    # Store payment ID for later use
    context.user_data["noting_payment_id"] = payment_id
    
    # Switch to waiting for text input
    return ENTERING_PAYMENT_NOTES

@require_admin
async def payment_process_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process adding a note to a payment."""
    # Get message text as note
    note = update.message.text
    
    # Get payment ID from context
    payment_id = context.user_data.get("noting_payment_id")
    
    if not payment_id:
        await update.message.reply_text(
            "❌ خطا: اطلاعات پرداخت یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data="admin_payments")]
            ])
        )
        return SELECTING_PAYMENT
    
    # Get current payment to append note
    payment = get_payment(payment_id)
    if not payment:
        await update.message.reply_text(
            "❌ خطا: پرداخت یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data="admin_payments")]
            ])
        )
        return SELECTING_PAYMENT
    
    # Append new note to existing notes
    current_notes = payment.get("notes", "")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_notes = f"{current_notes}\n[{timestamp}] {note}" if current_notes else f"[{timestamp}] {note}"
    
    # Update payment with new notes
    result = update_payment(payment_id, {
        "notes": new_notes
    })
    
    if result:
        # Send confirmation message
        await update.message.reply_text(
            "✅ یادداشت با موفقیت اضافه شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 مشاهده جزئیات", callback_data=f"payment_details:{payment_id}")],
                [InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data="admin_payments")]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ خطا در افزودن یادداشت. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات پرداخت", callback_data=f"payment_details:{payment_id}")]
            ])
        )
    
    return SELECTING_PAYMENT

@require_admin
async def payment_process_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process payment rejection."""
    query = update.callback_query
    await query.answer()
    
    # Get payment ID and rejection reason
    payment_id = context.user_data.get("rejection_payment_id")
    rejection_reason = context.user_data.get("rejection_reason", "")
    
    if not payment_id:
        await query.edit_message_text(
            "❌ خطا: شناسه پرداخت یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data=PAYMENT_MANAGEMENT)]
            ])
        )
        return SELECTING_PAYMENT
    
    # Get admin info
    admin_id = query.from_user.id
    admin_username = query.from_user.username or query.from_user.first_name
    
    # Reject payment using API
    rejection_result = reject_payment(payment_id, rejection_reason, admin_id, admin_username)
    
    if rejection_result.get('success', False):
        # Get updated payment details for notification
        payment_details = get_payment(payment_id)
        
        if payment_details:
            # Add admin info to payment details
            payment_details['admin_id'] = admin_id
            payment_details['admin_username'] = admin_username
            payment_details['reason'] = rejection_reason
            
            # Add timestamp for notification
            payment_details['updated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Send notification to management groups
            try:
                notification_sent = await hook_payment_processed(context.bot, payment_details, approved=False)
                if not notification_sent:
                    logger.warning(f"Failed to send payment rejection notification for payment: {payment_id}")
            except Exception as e:
                logger.error(f"Failed to send payment rejection notification: {str(e)}")
        
        # Success message
        message = (
            f"❌ *پرداخت رد شد*\n\n"
            f"• شناسه پرداخت: `{payment_id}`\n"
            f"• دلیل: {rejection_reason}\n"
            f"• رد‌کننده: @{admin_username}\n\n"
            f"کاربر از این تغییر مطلع خواهد شد."
        )
    else:
        # Error message
        error = rejection_result.get('message', 'خطای نامشخص')
        message = (
            f"❌ *خطا در رد پرداخت*\n\n"
            f"• شناسه پرداخت: `{payment_id}`\n"
            f"• خطا: {error}"
        )
    
    # Clear context data
    if "rejection_payment_id" in context.user_data:
        del context.user_data["rejection_payment_id"]
    if "rejection_reason" in context.user_data:
        del context.user_data["rejection_reason"]
    
    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 بازگشت به لیست پرداخت‌ها", 
                callback_data=PAYMENT_MANAGEMENT
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PAYMENT

@require_admin
async def payment_refund(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Refund a completed payment."""
    query = update.callback_query
    await query.answer()
    
    # Get payment ID from callback data
    payment_id = int(query.data.split(":")[1])
    
    # Ask for refund reason
    await query.edit_message_text(
        "❓ لطفاً دلیل بازگشت وجه را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data=f"payment_details:{payment_id}")]
        ])
    )
    
    # Store payment ID for later use
    context.user_data["refunding_payment_id"] = payment_id
    
    # Switch to waiting for text input
    return ENTERING_PAYMENT_NOTES

@require_admin
async def payment_process_refund(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process a payment refund with the provided reason."""
    # Get message text as refund reason
    reason = update.message.text
    
    # Get payment ID from context
    payment_id = context.user_data.get("refunding_payment_id")
    
    if not payment_id:
        await update.message.reply_text(
            "❌ خطا: اطلاعات پرداخت یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data="admin_payments")]
            ])
        )
        return SELECTING_PAYMENT
    
    # Update payment with refund reason and change status
    result = update_payment(payment_id, {
        "status": "refunded",
        "notes": f"Refunded: {reason}"
    })
    
    if result:
        # Send confirmation message
        await update.message.reply_text(
            "✅ بازگشت وجه با موفقیت انجام شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 مشاهده جزئیات", callback_data=f"payment_details:{payment_id}")],
                [InlineKeyboardButton("🔙 بازگشت به لیست پرداخت‌ها", callback_data="admin_payments")]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ خطا در بازگشت وجه. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات پرداخت", callback_data=f"payment_details:{payment_id}")]
            ])
        )
    
    return SELECTING_PAYMENT


# Define handlers list to be imported in __init__.py
handlers = [
    CallbackQueryHandler(payment_details, pattern="^payment_details:"),
    CallbackQueryHandler(payment_list_paginated, pattern="^payment_list:"),
    CallbackQueryHandler(payment_change_filter, pattern="^payment_change_filter$"),
    CallbackQueryHandler(payment_set_filter, pattern="^payment_set_filter:"),
    CallbackQueryHandler(payment_approve, pattern="^payment_approve:"),
    CallbackQueryHandler(payment_reject, pattern="^payment_reject:"),
    CallbackQueryHandler(payment_refund, pattern="^payment_refund:"),
    CallbackQueryHandler(payment_add_note, pattern="^payment_add_note:"),
    CallbackQueryHandler(payment_list, pattern="^admin_payments$"),
]

# Handlers for text input (entering notes state)
entering_notes_handlers = [
    MessageHandler(filters.TEXT & ~filters.COMMAND, payment_process_note),
    MessageHandler(filters.TEXT & ~filters.COMMAND, payment_process_rejection),
    MessageHandler(filters.TEXT & ~filters.COMMAND, payment_process_refund),
    CallbackQueryHandler(payment_details, pattern="^payment_details:"),
    CallbackQueryHandler(payment_list, pattern="^admin_payments$"),
]

# Create a class to hold the handlers for easier import
class payment_handlers:
    handlers = handlers
    entering_notes_handlers = entering_notes_handlers
    payment_list = payment_list 