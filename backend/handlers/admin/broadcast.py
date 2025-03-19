"""
Broadcast message handler for admin panel.
"""

import logging
from typing import Dict, Any, List
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from bot.services import broadcast_service
from bot.utils import (
    get_broadcast_message,
    get_broadcast_sent_message,
    build_navigation_keyboard
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_BROADCAST_ACTION = 1
ENTERING_MESSAGE = 2
CONFIRMING_BROADCAST = 3

async def broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show broadcast menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="broadcast",
        buttons=[
            ("📝 پیام جدید", "broadcast_new"),
            ("📊 آمار ارسال", "broadcast_stats"),
            ("🔙 بازگشت", "back_to_admin")
        ]
    )
    
    message = (
        "📢 <b>ارسال پیام گروهی</b>\n\n"
        "از این بخش می‌توانید به تمام کاربران پیام ارسال کنید.\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_BROADCAST_ACTION

async def new_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start new broadcast message."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="broadcast",
        buttons=[("🔙 بازگشت", "broadcast_menu")]
    )
    
    message = (
        "📝 <b>پیام جدید</b>\n\n"
        "لطفاً متن پیام خود را وارد کنید.\n"
        "می‌توانید از فرمت HTML استفاده کنید."
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return ENTERING_MESSAGE

async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm broadcast message."""
    message = update.message
    context.user_data['broadcast_message'] = message.text
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="broadcast",
        buttons=[
            ("✅ تأیید و ارسال", "broadcast_send"),
            ("❌ انصراف", "broadcast_menu")
        ]
    )
    
    preview = (
        "📢 <b>پیش‌نمایش پیام</b>\n\n"
        f"{message.text}\n\n"
        "آیا از ارسال این پیام به تمام کاربران اطمینان دارید؟"
    )
    
    await message.reply_text(
        text=preview,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return CONFIRMING_BROADCAST

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send broadcast message to all users."""
    query = update.callback_query
    await query.answer()
    
    message = context.user_data.get('broadcast_message')
    if not message:
        await query.edit_message_text(
            "❌ خطا: پیام یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="broadcast",
                buttons=[("🔙 بازگشت", "broadcast_menu")]
            )
        )
        return SELECTING_BROADCAST_ACTION
    
    # Send broadcast message
    result = await broadcast_service.send_message(message)
    
    # Show results
    stats_message = get_broadcast_sent_message(result)
    
    await query.edit_message_text(
        text=stats_message,
        reply_markup=build_navigation_keyboard(
            current_page=1,
            total_pages=1,
            base_callback="broadcast",
            buttons=[("🔙 بازگشت", "broadcast_menu")]
        ),
        parse_mode='HTML'
    )
    
    # Clear saved message
    context.user_data.pop('broadcast_message', None)
    
    return SELECTING_BROADCAST_ACTION

async def show_broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show broadcast statistics."""
    query = update.callback_query
    await query.answer()
    
    # Get broadcast stats
    stats = await broadcast_service.get_stats()
    
    # Format message
    message = (
        "📊 <b>آمار ارسال پیام‌های گروهی</b>\n\n"
        f"📨 تعداد کل پیام‌ها: {stats['total_messages']}\n"
        f"✅ ارسال موفق: {stats['successful_sends']}\n"
        f"❌ ارسال ناموفق: {stats['failed_sends']}\n"
        f"👥 کاربران فعال: {stats['active_users']}\n"
        f"🚫 کاربران مسدود: {stats['blocked_users']}\n\n"
        "📅 <b>آخرین ارسال‌ها:</b>\n"
    )
    
    for broadcast in stats['recent_broadcasts']:
        message += (
            f"\n🕒 {broadcast['date']}\n"
            f"👥 دریافت‌کنندگان: {broadcast['recipients']}\n"
            f"✅ موفق: {broadcast['successful']}\n"
            f"❌ ناموفق: {broadcast['failed']}\n"
            f"💬 متن: {broadcast['message'][:50]}...\n"
            "➖➖➖➖➖➖➖➖➖➖"
        )
    
    await query.edit_message_text(
        text=message,
        reply_markup=build_navigation_keyboard(
            current_page=1,
            total_pages=1,
            base_callback="broadcast",
            buttons=[("🔙 بازگشت", "broadcast_menu")]
        ),
        parse_mode='HTML'
    )
    
    return SELECTING_BROADCAST_ACTION

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

broadcast_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(broadcast_menu, pattern="^admin_broadcast$")
    ],
    states={
        SELECTING_BROADCAST_ACTION: [
            CallbackQueryHandler(new_broadcast, pattern="^broadcast_new$"),
            CallbackQueryHandler(show_broadcast_stats, pattern="^broadcast_stats$"),
            CallbackQueryHandler(broadcast_menu, pattern="^broadcast_menu$"),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
        ],
        ENTERING_MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_broadcast),
            CallbackQueryHandler(broadcast_menu, pattern="^broadcast_menu$")
        ],
        CONFIRMING_BROADCAST: [
            CallbackQueryHandler(send_broadcast, pattern="^broadcast_send$"),
            CallbackQueryHandler(broadcast_menu, pattern="^broadcast_menu$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
    ],
    map_to_parent={
        ConversationHandler.END: 'SELECTING_ADMIN_ACTION'
    }
) 