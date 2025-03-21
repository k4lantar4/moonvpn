"""
MoonVPN Telegram Bot - Payment Methods Handler.

This module provides functionality to display and process various payment methods.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CallbackQueryHandler, 
    CommandHandler, 
    ConversationHandler,
    MessageHandler,
    filters
)

from core.database.models.user import User
from core.database.models.payment import Payment
from bot.constants import CallbackPatterns, States

logger = logging.getLogger(__name__)

# Payment images
PAYMENT_IMAGE = "https://example.com/path/to/payment_image.jpg"  # Replace with actual image URL or file_id
CARD_PAYMENT_IMAGE = "https://example.com/path/to/card_payment.jpg"  # Replace with actual image
ZARINPAL_IMAGE = "https://example.com/path/to/zarinpal.jpg"  # Replace with actual image

# States for the payment conversation
(
    PAYMENT_METHOD_SELECTION,
    CARD_PAYMENT_AMOUNT,
    CARD_PAYMENT_REFERENCE,
    ZARINPAL_PAYMENT_AMOUNT,
    PAYMENT_CONFIRMATION,
    PAYMENT_COMPLETE
) = range(6)

async def payment_methods_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available payment methods."""
    user = update.effective_user
    message = update.message or update.callback_query.message
    
    # Get user from database
    db_user = User.get_by_telegram_id(user.id)
    if not db_user:
        # Create user if not exists
        db_user = User.create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        logger.info(f"Created new user for payment: {user.id} - @{user.username}")
    
    # Payment methods message
    payment_text = (
        f"💳 <b>روش‌های پرداخت</b>\n\n"
        f"کاربر گرامی، شما می‌توانید از طریق یکی از روش‌های زیر حساب خود را شارژ کنید:\n\n"
        f"• <b>کارت به کارت</b>: پرداخت مستقیم به کارت بانکی ما\n"
        f"• <b>درگاه پرداخت زرین‌پال</b>: پرداخت آنلاین و سریع\n\n"
        f"لطفا روش پرداخت مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("💳 کارت به کارت", callback_data=f"{CallbackPatterns.PAYMENT}_card"),
            InlineKeyboardButton("🔄 زرین‌پال", callback_data=f"{CallbackPatterns.PAYMENT}_zarinpal")
        ],
        [
            InlineKeyboardButton("📜 تاریخچه پرداخت‌ها", callback_data=f"{CallbackPatterns.PAYMENT}_history"),
            InlineKeyboardButton("❓ راهنمای پرداخت", callback_data=f"{CallbackPatterns.HELP}_payment")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    try:
        if update.callback_query:
            await update.callback_query.answer()
            
            if hasattr(update.callback_query.message, 'photo'):
                await update.callback_query.edit_message_caption(
                    caption=payment_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await update.callback_query.edit_message_text(
                    text=payment_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            try:
                await message.reply_photo(
                    photo=PAYMENT_IMAGE,
                    caption=payment_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending payment methods with image: {e}")
                await message.reply_text(
                    text=payment_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Error in payment methods command: {e}")
    
    return PAYMENT_METHOD_SELECTION

async def card_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle card payment method."""
    query = update.callback_query
    await query.answer()
    
    # Get bank account details for card to card payment
    # In real implementation, get from database
    bank_details = {
        "bank_name": "بانک ملت",
        "card_number": "6104 3377 7711 2244",
        "account_number": "1234567890",
        "sheba": "IR123456789012345678901234",
        "owner_name": "شرکت مون وی پی ان"
    }
    
    # Create message with bank details
    card_text = (
        f"💳 <b>پرداخت کارت به کارت</b>\n\n"
        f"لطفا مبلغ مورد نظر خود را به کارت زیر واریز نمایید:\n\n"
        f"🏦 بانک: {bank_details['bank_name']}\n"
        f"💳 شماره کارت: <code>{bank_details['card_number']}</code>\n"
        f"👤 به نام: {bank_details['owner_name']}\n\n"
        f"<b>مراحل پرداخت:</b>\n"
        f"1️⃣ مبلغ مورد نظر را وارد کنید\n"
        f"2️⃣ به یکی از کارت‌های بالا واریز کنید\n"
        f"3️⃣ پس از واریز، کد پیگیری یا ۴ رقم آخر کارت خود را ارسال کنید\n"
        f"4️⃣ پس از تایید، حساب شما شارژ خواهد شد\n\n"
        f"لطفا مبلغ مورد نظر خود را به <b>تومان</b> وارد کنید:"
    )
    
    # Create keyboard for navigation
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به روش‌های پرداخت", callback_data=f"{CallbackPatterns.PAYMENT}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        await query.edit_message_text(
            text=card_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing card payment: {e}")
        await query.message.reply_text(
            text=card_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    return CARD_PAYMENT_AMOUNT

async def process_card_payment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the entered payment amount for card payment."""
    user = update.effective_user
    message_text = update.message.text
    
    # Validate amount
    try:
        amount = int(message_text.replace(",", ""))
        if amount < 50000:  # Minimum amount is 50,000 Tomans
            await update.message.reply_text(
                "❌ حداقل مبلغ قابل پرداخت ۵۰,۰۰۰ تومان می‌باشد. لطفا مبلغ بیشتری وارد کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.PAYMENT}_card")
                ]])
            )
            return CARD_PAYMENT_AMOUNT
    except ValueError:
        await update.message.reply_text(
            "❌ لطفا یک عدد معتبر وارد کنید (مثلا: 100000).",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.PAYMENT}_card")
            ]])
        )
        return CARD_PAYMENT_AMOUNT
    
    # Store amount in context
    context.user_data['payment_amount'] = amount
    
    # Get bank details - in real implementation, get from database
    bank_details = {
        "bank_name": "بانک ملت",
        "card_number": "6104 3377 7711 2244",
        "account_number": "1234567890",
        "sheba": "IR123456789012345678901234",
        "owner_name": "شرکت مون وی پی ان"
    }
    
    # Create confirmation message
    confirmation_text = (
        f"💰 <b>مبلغ انتخابی شما: {amount:,} تومان</b>\n\n"
        f"لطفا این مبلغ را به کارت زیر واریز کنید:\n\n"
        f"🏦 بانک: {bank_details['bank_name']}\n"
        f"💳 شماره کارت: <code>{bank_details['card_number']}</code>\n"
        f"👤 به نام: {bank_details['owner_name']}\n\n"
        f"<b>پس از واریز:</b>\n"
        f"شماره پیگیری یا ۴ رقم آخر کارت خود را وارد کنید:"
    )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.PAYMENT}_card")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message
    await update.message.reply_text(
        text=confirmation_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return CARD_PAYMENT_REFERENCE

async def process_card_payment_reference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the reference number for card payment."""
    user = update.effective_user
    message_text = update.message.text
    
    # Validate reference number
    if len(message_text) < 4 or len(message_text) > 30:
        await update.message.reply_text(
            "❌ شماره پیگیری نامعتبر است. لطفا شماره پیگیری یا ۴ رقم آخر کارت خود را وارد کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.PAYMENT}_card")
            ]])
        )
        return CARD_PAYMENT_REFERENCE
    
    # Store reference in context
    context.user_data['payment_reference'] = message_text
    amount = context.user_data.get('payment_amount', 0)
    
    # Generate a unique payment ID
    payment_id = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user.id}"
    context.user_data['payment_id'] = payment_id
    
    # In a real implementation, save the payment to database
    # Payment.create(
    #     user_id=user.id,
    #     amount=amount,
    #     reference=message_text,
    #     payment_id=payment_id,
    #     method="card",
    #     status="pending"
    # )
    
    # Create confirmation message
    confirmation_text = (
        f"✅ <b>درخواست پرداخت شما ثبت شد</b>\n\n"
        f"🔢 شماره پیگیری: <code>{payment_id}</code>\n"
        f"💰 مبلغ: {amount:,} تومان\n"
        f"🔄 وضعیت: در انتظار تایید\n\n"
        f"پرداخت شما در حال بررسی است و پس از تایید، حساب شما شارژ خواهد شد.\n"
        f"این فرآیند معمولاً بین ۱ تا ۳۰ دقیقه زمان می‌برد."
    )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message
    await update.message.reply_text(
        text=confirmation_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    # Notify admin about the payment (in a real implementation)
    # await notify_admin_about_payment(context, user, amount, message_text, payment_id)
    
    return PAYMENT_COMPLETE

async def zarinpal_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Zarinpal payment method."""
    query = update.callback_query
    await query.answer()
    
    # Create message for Zarinpal payment
    zarinpal_text = (
        f"🔄 <b>پرداخت با درگاه زرین‌پال</b>\n\n"
        f"با استفاده از درگاه پرداخت زرین‌پال، می‌توانید به صورت آنلاین و سریع حساب خود را شارژ کنید.\n\n"
        f"<b>مزایای پرداخت با زرین‌پال:</b>\n"
        f"• پرداخت سریع و آنلاین\n"
        f"• پشتیبانی از تمام کارت‌های شتاب\n"
        f"• شارژ آنی حساب پس از پرداخت\n"
        f"• امنیت بالا\n\n"
        f"لطفا مبلغ مورد نظر خود را به <b>تومان</b> وارد کنید:"
    )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به روش‌های پرداخت", callback_data=f"{CallbackPatterns.PAYMENT}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        await query.edit_message_text(
            text=zarinpal_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing Zarinpal payment: {e}")
        await query.message.reply_text(
            text=zarinpal_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    return ZARINPAL_PAYMENT_AMOUNT

async def process_zarinpal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the entered amount for Zarinpal payment."""
    user = update.effective_user
    message_text = update.message.text
    
    # Validate amount
    try:
        amount = int(message_text.replace(",", ""))
        if amount < 10000:  # Minimum amount is 10,000 Tomans
            await update.message.reply_text(
                "❌ حداقل مبلغ قابل پرداخت ۱۰,۰۰۰ تومان می‌باشد. لطفا مبلغ بیشتری وارد کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.PAYMENT}_zarinpal")
                ]])
            )
            return ZARINPAL_PAYMENT_AMOUNT
    except ValueError:
        await update.message.reply_text(
            "❌ لطفا یک عدد معتبر وارد کنید (مثلا: 100000).",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.PAYMENT}_zarinpal")
            ]])
        )
        return ZARINPAL_PAYMENT_AMOUNT
    
    # Store amount in context
    context.user_data['payment_amount'] = amount
    
    # Generate a unique payment ID
    payment_id = f"ZP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user.id}"
    context.user_data['payment_id'] = payment_id
    
    # In a real implementation, create a Zarinpal payment request
    # and get the payment URL
    zarinpal_url = f"https://example.com/zarinpal/pay/{payment_id}?amount={amount}"
    
    # Create confirmation message
    confirmation_text = (
        f"💰 <b>مبلغ انتخابی شما: {amount:,} تومان</b>\n\n"
        f"برای پرداخت، لطفا روی دکمه «پرداخت آنلاین» کلیک کنید.\n"
        f"پس از پرداخت موفق، به صورت خودکار به ربات بازگردانده می‌شوید و حساب شما شارژ خواهد شد."
    )
    
    # Create keyboard with payment link
    keyboard = [
        [InlineKeyboardButton("💳 پرداخت آنلاین", url=zarinpal_url)],
        [InlineKeyboardButton("🔙 انصراف", callback_data=f"{CallbackPatterns.PAYMENT}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message
    await update.message.reply_text(
        text=confirmation_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    # In a real implementation, save the payment to database
    # Payment.create(
    #     user_id=user.id,
    #     amount=amount,
    #     payment_id=payment_id,
    #     method="zarinpal",
    #     status="pending"
    # )
    
    return PAYMENT_COMPLETE

async def payment_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show payment history."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    
    # Get payments from database
    # In a real implementation, fetch from database
    # For demo purposes, using hardcoded data
    payments = [
        {
            "id": "PAY-20230715123456-123456789",
            "date": "2023-07-15 12:34:56",
            "amount": 100000,
            "method": "card",
            "status": "completed"
        },
        {
            "id": "ZP-20230710154321-123456789",
            "date": "2023-07-10 15:43:21",
            "amount": 50000,
            "method": "zarinpal",
            "status": "completed"
        },
        {
            "id": "PAY-20230705103025-123456789",
            "date": "2023-07-05 10:30:25",
            "amount": 80000,
            "method": "card",
            "status": "failed"
        }
    ]
    
    if not payments:
        history_text = (
            "📜 <b>تاریخچه پرداخت‌ها</b>\n\n"
            "شما هنوز هیچ پرداختی انجام نداده‌اید."
        )
    else:
        history_text = "📜 <b>تاریخچه پرداخت‌ها</b>\n\n"
        
        for payment in payments:
            # Get status emoji
            status_emoji = "✅" if payment["status"] == "completed" else "❌"
            
            # Get method name
            method_name = "کارت به کارت" if payment["method"] == "card" else "زرین‌پال"
            
            # Add payment to history
            history_text += (
                f"🔢 شناسه: <code>{payment['id']}</code>\n"
                f"📅 تاریخ: {payment['date']}\n"
                f"💰 مبلغ: {payment['amount']:,} تومان\n"
                f"🔄 روش: {method_name}\n"
                f"🔄 وضعیت: {status_emoji}\n"
                f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
            )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به روش‌های پرداخت", callback_data=f"{CallbackPatterns.PAYMENT}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        await query.edit_message_text(
            text=history_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing payment history: {e}")
        await query.message.reply_text(
            text=history_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    return PAYMENT_METHOD_SELECTION

async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callbacks from payment methods."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    action = callback_data.split("_")[1] if "_" in callback_data else ""
    
    if action == "card":
        # Handle card payment
        return await card_payment(update, context)
    elif action == "zarinpal":
        # Handle Zarinpal payment
        return await zarinpal_payment(update, context)
    elif action == "history":
        # Show payment history
        return await payment_history(update, context)
    else:
        # Default - show payment methods
        return await payment_methods_command(update, context)

def get_payment_methods_handlers() -> List:
    """Return all handlers related to payment methods."""
    
    payment_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("payment", payment_methods_command),
            CallbackQueryHandler(payment_callback, pattern=f"^{CallbackPatterns.PAYMENT}$"),
            CallbackQueryHandler(payment_callback, pattern=f"^{CallbackPatterns.INCREASE_CREDIT}$")
        ],
        states={
            PAYMENT_METHOD_SELECTION: [
                CallbackQueryHandler(payment_callback, pattern=f"^{CallbackPatterns.PAYMENT}"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$")
            ],
            CARD_PAYMENT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_payment_amount),
                CallbackQueryHandler(payment_callback, pattern=f"^{CallbackPatterns.PAYMENT}")
            ],
            CARD_PAYMENT_REFERENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_card_payment_reference),
                CallbackQueryHandler(payment_callback, pattern=f"^{CallbackPatterns.PAYMENT}")
            ],
            ZARINPAL_PAYMENT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_zarinpal_amount),
                CallbackQueryHandler(payment_callback, pattern=f"^{CallbackPatterns.PAYMENT}")
            ],
            PAYMENT_COMPLETE: [
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
                CommandHandler("start", lambda u, c: ConversationHandler.END)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END)
        ],
        name="payment_conversation",
        persistent=False
    )
    
    return [payment_conversation] 