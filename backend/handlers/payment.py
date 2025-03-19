"""
Payment handler for MoonVPN Telegram Bot.

This module handles the payment process and tracking.
"""

import logging
import datetime
from typing import Dict, List, Optional, Union

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    ConversationHandler,
    filters
)
from telegram.constants import ParseMode

from models import User, Payment
from core.utils.i18n import _
from core.utils.formatting import allowed_group_filter, admin_filter
from core.utils.helpers import require_feature

logger = logging.getLogger(__name__)

# Define states
ADDING_BALANCE = 0
SELECTING_AMOUNT = 1
SELECTING_PAYMENT_METHOD = 2
PROCESSING_PAYMENT = 3
ENTERING_TRACKING_ID = 4

# Predefined amounts
AMOUNTS = [50000, 100000, 200000, 500000]

async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /payment command to show payment options."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} accessed payment menu")
    
    # Get user's payment history
    payments = Payment.get_by_user_id(user_id)
    
    # Create message
    message = _(
        "💰 **مدیریت پرداخت**\n\n"
        "در این بخش می‌توانید به موجودی حساب خود اضافه کنید یا سوابق پرداخت‌های خود را مشاهده نمایید."
    )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton(_("💵 افزایش موجودی"), callback_data="add_balance")],
        [InlineKeyboardButton(_("📋 سوابق پرداخت"), callback_data="payment_history")]
    ]
    
    # Add navigation
    keyboard.append([InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
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
    
    return ADDING_BALANCE

async def payment_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show payment history."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get payment history
    payments = Payment.get_by_user_id(user_id)
    
    if not payments:
        message = _(
            "📋 **سوابق پرداخت**\n\n"
            "شما هنوز هیچ پرداختی انجام نداده‌اید."
        )
        
        keyboard = [[InlineKeyboardButton(_("🔙 بازگشت"), callback_data="payment")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return ADDING_BALANCE
    
    # Create message with payment history
    message = _("📋 **سوابق پرداخت**\n\n")
    
    for i, payment in enumerate(payments):
        status_emoji = "✅" if payment.status == "completed" else "⏳" if payment.status == "pending" else "❌"
        
        payment_date = payment.created_at.strftime("%Y-%m-%d %H:%M")
        
        message += _(
            f"{i+1}. {status_emoji} {payment.amount:,} تومان\n"
            f"   📅 تاریخ: {payment_date}\n"
            f"   🔢 شناسه: {payment.reference_id or 'نامشخص'}\n"
            f"   💳 روش: {payment.method}\n\n"
        )
    
    keyboard = [[InlineKeyboardButton(_("🔙 بازگشت"), callback_data="payment")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ADDING_BALANCE

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process of adding balance."""
    query = update.callback_query
    await query.answer()
    
    # Create message with amount options
    message = _(
        "💰 **افزایش موجودی**\n\n"
        "لطفاً مبلغ مورد نظر خود را انتخاب کنید یا مبلغ دلخواه را وارد نمایید:"
    )
    
    # Create buttons for predefined amounts
    keyboard = []
    row = []
    
    for i, amount in enumerate(AMOUNTS):
        amount_str = f"{amount:,}"
        row.append(InlineKeyboardButton(f"{amount_str} تومان", callback_data=f"amount_{amount}"))
        
        if (i + 1) % 2 == 0 or i == len(AMOUNTS) - 1:
            keyboard.append(row)
            row = []
    
    # Add custom amount button
    keyboard.append([InlineKeyboardButton(_("💬 مبلغ دلخواه"), callback_data="custom_amount")])
    
    # Add navigation
    keyboard.append([InlineKeyboardButton(_("🔙 بازگشت"), callback_data="payment")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_AMOUNT

async def amount_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount selection."""
    query = update.callback_query
    await query.answer()
    
    # Get selected amount
    amount = int(query.data.split("_")[1])
    context.user_data["payment"] = {
        "amount": amount
    }
    
    # Show payment method selection
    return await select_payment_method(update, context)

async def custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom amount selection."""
    query = update.callback_query
    await query.answer()
    
    message = _(
        "💬 **مبلغ دلخواه**\n\n"
        "لطفاً مبلغ مورد نظر خود را به تومان وارد کنید:\n"
        "مثال: 150000"
    )
    
    keyboard = [[InlineKeyboardButton(_("🔙 بازگشت"), callback_data="add_balance")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ENTERING_TRACKING_ID

async def process_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process custom amount input."""
    text = update.message.text.strip()
    
    try:
        # Parse amount
        amount = int(text.replace(",", ""))
        
        if amount < 10000:
            # Amount too small
            await update.message.reply_text(
                _("❌ مبلغ وارد شده باید حداقل 10,000 تومان باشد."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="add_balance")]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
            return SELECTING_AMOUNT
        
        # Store amount
        context.user_data["payment"] = {
            "amount": amount
        }
        
        # Show payment method selection
        message = _(
            f"💰 **انتخاب روش پرداخت**\n\n"
            f"مبلغ انتخابی: {amount:,} تومان\n\n"
            f"لطفاً روش پرداخت را انتخاب کنید:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(_("💳 کارت به کارت"), callback_data="payment_method_card"),
                InlineKeyboardButton(_("💻 درگاه آنلاین"), callback_data="payment_method_online")
            ],
            [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="add_balance")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return SELECTING_PAYMENT_METHOD
        
    except ValueError:
        # Invalid amount
        await update.message.reply_text(
            _("❌ لطفاً یک عدد صحیح وارد کنید. مثال: 150000"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="add_balance")]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return ENTERING_TRACKING_ID

async def select_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show payment method selection."""
    query = update.callback_query
    await query.answer()
    
    amount = context.user_data["payment"]["amount"]
    
    message = _(
        f"💰 **انتخاب روش پرداخت**\n\n"
        f"مبلغ انتخابی: {amount:,} تومان\n\n"
        f"لطفاً روش پرداخت را انتخاب کنید:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(_("💳 کارت به کارت"), callback_data="payment_method_card"),
            InlineKeyboardButton(_("💻 درگاه آنلاین"), callback_data="payment_method_online")
        ],
        [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="add_balance")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PAYMENT_METHOD

async def payment_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method selection."""
    query = update.callback_query
    await query.answer()
    
    # Get selected payment method
    method = query.data.split("_")[-1]
    amount = context.user_data["payment"]["amount"]
    
    context.user_data["payment"]["method"] = method
    
    if method == "card":
        # Show card to card payment instructions
        message = _(
            f"💳 **پرداخت کارت به کارت**\n\n"
            f"مبلغ: {amount:,} تومان\n\n"
            f"لطفاً مبلغ را به کارت زیر واریز کنید و سپس تصویر رسید یا شماره پیگیری را ارسال نمایید:\n\n"
            f"شماره کارت: 6037-9975-9507-8955\n"
            f"به نام: محمد محمدزاده\n"
            f"بانک: ملی"
        )
        
        keyboard = [[InlineKeyboardButton(_("❌ انصراف"), callback_data="cancel_payment")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return PROCESSING_PAYMENT
    else:  # online payment
        # Generate online payment link (this would be from your payment gateway)
        payment_link = "https://pay.example.com/12345"
        
        # Create a new pending payment record in database
        user_id = update.effective_user.id
        reference_id = f"PAY{user_id}{int(datetime.datetime.now().timestamp())}"
        
        payment = Payment(
            user_id=user_id,
            amount=amount,
            method="online",
            status="pending",
            reference_id=reference_id
        )
        payment.save()
        
        message = _(
            f"💻 **پرداخت آنلاین**\n\n"
            f"مبلغ: {amount:,} تومان\n"
            f"شناسه پرداخت: {reference_id}\n\n"
            f"برای پرداخت روی دکمه زیر کلیک کنید تا به درگاه پرداخت هدایت شوید.\n"
            f"پس از تکمیل پرداخت، به صورت خودکار به ربات بازگردانده می‌شوید."
        )
        
        keyboard = [
            [InlineKeyboardButton(_("💳 پرداخت آنلاین"), url=payment_link)],
            [InlineKeyboardButton(_("✅ پرداخت انجام شد"), callback_data=f"payment_completed_{reference_id}")],
            [InlineKeyboardButton(_("❌ انصراف"), callback_data="cancel_payment")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return PROCESSING_PAYMENT

async def process_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the payment receipt."""
    user_id = update.effective_user.id
    
    amount = context.user_data["payment"]["amount"]
    method = context.user_data["payment"]["method"]
    
    # Generate reference ID
    reference_id = f"PAY{user_id}{int(datetime.datetime.now().timestamp())}"
    
    # Check if there's a photo
    if update.message.photo:
        # Get the largest photo
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        payment_data = {"file_id": file_id}
        text_receipt = None
    else:
        # Assume it's a text receipt (tracking number)
        text_receipt = update.message.text
        payment_data = {"text_receipt": text_receipt}
    
    # Create payment record
    payment = Payment(
        user_id=user_id,
        amount=amount,
        method="card",
        status="pending",
        reference_id=reference_id,
        payment_data=payment_data
    )
    payment.save()
    
    # Notify admin about new payment
    # This would be implemented in a real system
    
    # Send confirmation to user
    message = _(
        "✅ **رسید دریافت شد**\n\n"
        "رسید پرداخت شما با موفقیت دریافت شد و در حال بررسی توسط ادمین است.\n"
        "پس از تأیید، موجودی به حساب شما اضافه خواهد شد.\n\n"
        f"مبلغ: {amount:,} تومان\n"
        f"شناسه پرداخت: {reference_id}"
    )
    
    keyboard = [
        [InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Clear payment data
    del context.user_data["payment"]
    
    return ConversationHandler.END

async def payment_completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle online payment completion confirmation."""
    query = update.callback_query
    await query.answer()
    
    # Get reference ID from callback data
    reference_id = query.data.split("_")[-1]
    
    # In real implementation, verify payment with payment gateway
    # For this example, we'll simulate success
    
    # Update payment status to completed
    payment = Payment.get_by_reference_id(reference_id)
    if payment:
        payment.status = "completed"
        payment.save()
    
    # Send success message
    message = _(
        "🎉 **پرداخت موفق**\n\n"
        "پرداخت شما با موفقیت انجام شد و موجودی به حساب شما اضافه شد.\n\n"
        f"مبلغ: {payment.amount:,} تومان\n"
        f"شناسه پرداخت: {reference_id}"
    )
    
    keyboard = [
        [InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Clear payment data if exists
    if "payment" in context.user_data:
        del context.user_data["payment"]
    
    return ConversationHandler.END

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the payment process."""
    query = update.callback_query
    await query.answer()
    
    # Clear payment data
    if "payment" in context.user_data:
        del context.user_data["payment"]
    
    message = _(
        "❌ **پرداخت لغو شد**\n\n"
        "فرآیند پرداخت لغو شد. هر زمان که تمایل داشتید می‌توانید مجدداً اقدام نمایید."
    )
    
    keyboard = [
        [InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ConversationHandler.END

@require_feature("payments")
def get_payment_handler():
    """Get the conversation handler for the payment process."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("payment", payment_command, filters=allowed_group_filter),
            CallbackQueryHandler(payment_command, pattern="^payment$")
        ],
        states={
            ADDING_BALANCE: [
                CallbackQueryHandler(add_balance, pattern="^add_balance$"),
                CallbackQueryHandler(payment_history, pattern="^payment_history$")
            ],
            SELECTING_AMOUNT: [
                CallbackQueryHandler(amount_selected, pattern=r"^amount_\d+$"),
                CallbackQueryHandler(custom_amount, pattern="^custom_amount$"),
                CallbackQueryHandler(payment_command, pattern="^payment$")
            ],
            ENTERING_TRACKING_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_custom_amount),
                CallbackQueryHandler(add_balance, pattern="^add_balance$")
            ],
            SELECTING_PAYMENT_METHOD: [
                CallbackQueryHandler(payment_method_selected, pattern=r"^payment_method_(card|online)$"),
                CallbackQueryHandler(add_balance, pattern="^add_balance$")
            ],
            PROCESSING_PAYMENT: [
                MessageHandler((filters.PHOTO | filters.TEXT) & ~filters.COMMAND, process_receipt),
                CallbackQueryHandler(payment_completed, pattern=r"^payment_completed_"),
                CallbackQueryHandler(cancel_payment, pattern="^cancel_payment$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_payment),
            CallbackQueryHandler(cancel_payment, pattern="^cancel_payment$"),
            CallbackQueryHandler(payment_command, pattern="^main_menu$")
        ],
        name="payment",
        persistent=False
    ) 