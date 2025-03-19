"""
MoonVPN Telegram Bot - Support Handler Implementation.

This module provides handlers for the support feature.
"""

import logging
from typing import Dict, List, Optional, Union, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from models.user import User
from models.ticket import Ticket
from core.config import get_config_value
from core.utils.i18n import get_text
from core.utils.formatting import allowed_group_filter, maintenance_mode_check

# States
SUPPORT_MENU, SUPPORT_MESSAGE, SUPPORT_TICKET = range(3)

# Callback patterns
PATTERN_SUPPORT = "support"
PATTERN_SUPPORT_TICKET = "support_ticket"
PATTERN_SUPPORT_CONTACT = "support_contact"
PATTERN_SUPPORT_HISTORY = "support_history"
PATTERN_SUPPORT_TICKET_VIEW = "support_ticket_view_"

logger = logging.getLogger(__name__)

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /support command.
    
    This command displays the support menu.
    """
    return await support_handler(update, context)

async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the support button callback.
    
    This function displays the support menu.
    """
    user = update.effective_user
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    # Create a beautiful support menu
    text = (
        "🆘 <b>پشتیبانی MoonVPN</b>\n\n"
        "از اینکه MoonVPN را انتخاب کرده‌اید، سپاسگزاریم.\n\n"
        "چگونه می‌توانیم به شما کمک کنیم؟"
    )
    
    # Create keyboard with support options
    keyboard = [
        [InlineKeyboardButton("📝 ارسال تیکت پشتیبانی", callback_data=PATTERN_SUPPORT_TICKET)],
        [InlineKeyboardButton("📋 تیکت‌های قبلی", callback_data=PATTERN_SUPPORT_HISTORY)],
        [InlineKeyboardButton("👤 تماس با پشتیبانی", callback_data=PATTERN_SUPPORT_CONTACT)],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return SUPPORT_MENU

async def support_ticket_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the support ticket button callback.
    
    This function prompts the user to enter a support message.
    """
    query = update.callback_query
    await query.answer()
    
    # Create a beautiful support ticket message
    text = (
        "📝 <b>ارسال تیکت پشتیبانی</b>\n\n"
        "لطفاً مشکل یا سوال خود را به صورت کامل شرح دهید.\n"
        "تیم پشتیبانی در اسرع وقت به شما پاسخ خواهد داد."
    )
    
    # Create keyboard with cancel button
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی پشتیبانی", callback_data=PATTERN_SUPPORT)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return SUPPORT_MESSAGE

async def support_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the support message.
    
    This function processes the user's support message and creates a ticket.
    """
    user = update.effective_user
    message = update.message
    
    # Get the message text
    text = message.text
    
    # Create a ticket
    try:
        # Get or create user
        db_user = User.get_by_telegram_id(user.id)
        if not db_user:
            db_user = User.create(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language=user.language_code
            )
        
        # Create ticket
        ticket = Ticket.create(
            user_id=db_user.id,
            subject="Support Request",
            message=text,
            status="open"
        )
        
        # Store ticket ID in context
        context.user_data['ticket_id'] = ticket.id
        
        # Send confirmation message
        confirmation_text = (
            "✅ <b>تیکت شما با موفقیت ثبت شد</b>\n\n"
            f"شماره تیکت: <code>{ticket.id}</code>\n\n"
            "تیم پشتیبانی در اسرع وقت به شما پاسخ خواهد داد."
        )
        
        # Create keyboard with back button
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی پشتیبانی", callback_data=PATTERN_SUPPORT)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(text=confirmation_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        # Forward message to admin
        admin_ids = get_config_value("admin_ids", [])
        for admin_id in admin_ids:
            try:
                admin_text = (
                    f"📩 <b>تیکت جدید</b> #{ticket.id}\n\n"
                    f"<b>کاربر:</b> {user.first_name} {user.last_name or ''} (@{user.username or 'بدون نام کاربری'})\n"
                    f"<b>شناسه کاربر:</b> <code>{user.id}</code>\n\n"
                    f"<b>پیام:</b>\n{text}"
                )
                
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Error forwarding ticket to admin {admin_id}: {e}")
        
        return SUPPORT_MENU
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        
        # Send error message
        error_text = (
            "❌ <b>خطا در ثبت تیکت</b>\n\n"
            "متأسفانه در ثبت تیکت شما خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
        
        # Create keyboard with back button
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی پشتیبانی", callback_data=PATTERN_SUPPORT)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(text=error_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        return SUPPORT_MENU

async def support_contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the support contact button callback.
    
    This function displays contact information for the support team.
    """
    query = update.callback_query
    await query.answer()
    
    # Get support username from config
    support_username = get_config_value("support_username", "@moonvpn_admin")
    
    # Create a beautiful support contact message
    text = (
        "👤 <b>تماس با پشتیبانی</b>\n\n"
        "شما می‌توانید از طریق یکی از روش‌های زیر با پشتیبانی تماس بگیرید:\n\n"
        f"• تلگرام: {support_username}\n"
        "• ایمیل: support@moonvpn.ir\n\n"
        "ساعات پاسخگویی: 9 صبح تا 9 شب، همه روزه"
    )
    
    # Create keyboard with back button
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی پشتیبانی", callback_data=PATTERN_SUPPORT)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return SUPPORT_MENU

async def support_history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the support history button callback.
    
    This function displays the user's previous support tickets.
    """
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Get user's tickets
    try:
        # Get user
        db_user = User.get_by_telegram_id(user.id)
        if not db_user:
            # No user found, so no tickets
            tickets = []
        else:
            # Get tickets
            tickets = Ticket.get_by_user_id(db_user.id)
    except Exception as e:
        logger.error(f"Error getting tickets: {e}")
        tickets = []
    
    if not tickets:
        # No tickets found
        text = (
            "📋 <b>تیکت‌های قبلی</b>\n\n"
            "شما هنوز هیچ تیکتی ثبت نکرده‌اید."
        )
        
        # Create keyboard with back button
        keyboard = [
            [InlineKeyboardButton("📝 ارسال تیکت جدید", callback_data=PATTERN_SUPPORT_TICKET)],
            [InlineKeyboardButton("🔙 بازگشت به منوی پشتیبانی", callback_data=PATTERN_SUPPORT)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        return SUPPORT_MENU
    
    # Create a beautiful ticket history message
    text = (
        "📋 <b>تیکت‌های قبلی</b>\n\n"
        "لیست تیکت‌های شما:\n\n"
    )
    
    # Create keyboard with ticket buttons
    keyboard = []
    
    # Add tickets to text and keyboard
    for i, ticket in enumerate(tickets[:10], 1):  # Show only the last 10 tickets
        # Format status
        if ticket.status == "open":
            status = "🟢 باز"
        elif ticket.status == "answered":
            status = "🔵 پاسخ داده شده"
        elif ticket.status == "closed":
            status = "🔴 بسته شده"
        else:
            status = "⚪ نامشخص"
        
        # Format date
        created_at = ticket.created_at.strftime("%Y-%m-%d %H:%M")
        
        # Add ticket to text
        text += f"{i}. <b>تیکت #{ticket.id}</b> - {status} - {created_at}\n"
        
        # Add button for this ticket
        keyboard.append([
            InlineKeyboardButton(
                f"تیکت #{ticket.id} - {status}",
                callback_data=f"{PATTERN_SUPPORT_TICKET_VIEW}{ticket.id}"
            )
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی پشتیبانی", callback_data=PATTERN_SUPPORT)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return SUPPORT_TICKET

async def support_ticket_view_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the support ticket view button callback.
    
    This function displays the details of a specific ticket.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract ticket ID from callback data
    ticket_id = int(query.data.replace(PATTERN_SUPPORT_TICKET_VIEW, ""))
    
    # Get ticket
    try:
        ticket = Ticket.get_by_id(ticket_id)
    except Exception as e:
        logger.error(f"Error getting ticket: {e}")
        ticket = None
    
    if not ticket:
        # Ticket not found
        text = (
            "❌ <b>تیکت یافت نشد</b>\n\n"
            "تیکت مورد نظر یافت نشد. لطفاً دوباره تلاش کنید."
        )
        
        # Create keyboard with back button
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به لیست تیکت‌ها", callback_data=PATTERN_SUPPORT_HISTORY)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        return SUPPORT_TICKET
    
    # Format status
    if ticket.status == "open":
        status = "🟢 باز"
    elif ticket.status == "answered":
        status = "🔵 پاسخ داده شده"
    elif ticket.status == "closed":
        status = "🔴 بسته شده"
    else:
        status = "⚪ نامشخص"
    
    # Format dates
    created_at = ticket.created_at.strftime("%Y-%m-%d %H:%M")
    updated_at = ticket.updated_at.strftime("%Y-%m-%d %H:%M") if ticket.updated_at else "N/A"
    
    # Create a beautiful ticket view message
    text = (
        f"🎫 <b>تیکت #{ticket.id}</b>\n\n"
        f"<b>وضعیت:</b> {status}\n"
        f"<b>تاریخ ایجاد:</b> {created_at}\n"
        f"<b>آخرین بروزرسانی:</b> {updated_at}\n\n"
        f"<b>موضوع:</b> {ticket.subject}\n\n"
        f"<b>پیام شما:</b>\n{ticket.message}\n\n"
    )
    
    # Add admin response if available
    if ticket.response:
        text += f"<b>پاسخ پشتیبانی:</b>\n{ticket.response}\n\n"
    
    # Create keyboard with back button
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به لیست تیکت‌ها", callback_data=PATTERN_SUPPORT_HISTORY)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return SUPPORT_TICKET

def get_support_handlers() -> List[Any]:
    """Return all handlers related to the support feature."""
    
    # Create conversation handler for support flow
    support_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("support", support_command),
            CallbackQueryHandler(support_handler, pattern=f"^{PATTERN_SUPPORT}$")
        ],
        states={
            SUPPORT_MENU: [
                CallbackQueryHandler(support_ticket_handler, pattern=f"^{PATTERN_SUPPORT_TICKET}$"),
                CallbackQueryHandler(support_contact_handler, pattern=f"^{PATTERN_SUPPORT_CONTACT}$"),
                CallbackQueryHandler(support_history_handler, pattern=f"^{PATTERN_SUPPORT_HISTORY}$")
            ],
            SUPPORT_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, support_message_handler),
                CallbackQueryHandler(support_handler, pattern=f"^{PATTERN_SUPPORT}$")
            ],
            SUPPORT_TICKET: [
                CallbackQueryHandler(support_ticket_view_handler, pattern=f"^{PATTERN_SUPPORT_TICKET_VIEW}\\d+$"),
                CallbackQueryHandler(support_history_handler, pattern=f"^{PATTERN_SUPPORT_HISTORY}$"),
                CallbackQueryHandler(support_handler, pattern=f"^{PATTERN_SUPPORT}$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(support_handler, pattern=f"^{PATTERN_SUPPORT}$"),
            CommandHandler("cancel", support_handler)
        ],
        name="support_conversation",
        persistent=False
    )
    
    return [support_conv_handler] 