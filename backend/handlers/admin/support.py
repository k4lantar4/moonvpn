"""
Support management handler for admin panel.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from bot.services import support_service
from bot.utils import (
    build_navigation_keyboard,
    format_date,
    format_time_ago
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_SUPPORT_ACTION = 1
VIEWING_TICKET = 2
REPLYING_TO_TICKET = 3
CONFIRMING_CLOSE = 4

async def support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show support management menu."""
    query = update.callback_query
    await query.answer()
    
    # Get support stats
    stats = await support_service.get_support_stats()
    
    message = (
        "🎯 <b>مدیریت پشتیبانی</b>\n\n"
        "📊 <b>آمار تیکت‌ها:</b>\n"
        f"• باز: {stats['open_tickets']} تیکت\n"
        f"• در انتظار پاسخ: {stats['pending_tickets']} تیکت\n"
        f"• بسته شده: {stats['closed_tickets']} تیکت\n"
        f"• میانگین زمان پاسخ: {stats['avg_response_time']}\n\n"
        "🔔 <b>اعلان‌های مهم:</b>\n"
        f"• تیکت‌های فوری: {stats['urgent_tickets']}\n"
        f"• تیکت‌های قدیمی: {stats['old_tickets']}\n"
        f"• بدون پاسخ: {stats['unanswered_tickets']}"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="support",
        buttons=[
            ("📨 تیکت‌های باز", "support_open"),
            ("⏳ در انتظار", "support_pending"),
            ("✅ بسته شده", "support_closed"),
            ("📊 آمار", "support_stats"),
            ("🔙 بازگشت", "back_to_admin")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_SUPPORT_ACTION

async def list_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of tickets based on status."""
    query = update.callback_query
    await query.answer()
    
    # Get status from callback data
    status = query.data.split('_')[1]
    
    # Get page from callback data or default to 1
    page = int(query.data.split('_')[-1]) if len(query.data.split('_')) > 2 else 1
    
    # Get tickets for current page
    tickets = await support_service.get_tickets(status=status, page=page)
    total_pages = tickets['total_pages']
    
    message = (
        f"📋 <b>تیکت‌های {tickets['status_text']}</b>\n\n"
        f"📄 صفحه {page} از {total_pages}\n\n"
    )
    
    for ticket in tickets['items']:
        message += (
            f"🎫 <b>#{ticket['id']}</b>\n"
            f"👤 کاربر: {ticket['user_name']}\n"
            f"📝 موضوع: {ticket['subject']}\n"
            f"⏰ {format_time_ago(ticket['created_at'])}\n"
            f"📊 وضعیت: {ticket['status']}\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=page,
        total_pages=total_pages,
        base_callback=f"support_{status}",
        extra_buttons=[("🔙 بازگشت", "support_menu")]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_SUPPORT_ACTION

async def view_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show ticket details and conversation."""
    query = update.callback_query
    await query.answer()
    
    # Get ticket ID from callback data
    ticket_id = query.data.split('_')[-1]
    
    # Get ticket details
    ticket = await support_service.get_ticket(ticket_id)
    
    message = (
        f"🎫 <b>تیکت #{ticket['id']}</b>\n\n"
        f"👤 <b>کاربر:</b> {ticket['user_name']}\n"
        f"📱 آیدی: {ticket['user_id']}\n"
        f"📝 موضوع: {ticket['subject']}\n"
        f"📅 تاریخ: {format_date(ticket['created_at'])}\n"
        f"📊 وضعیت: {ticket['status']}\n\n"
        "💬 <b>گفتگو:</b>\n\n"
    )
    
    for msg in ticket['messages']:
        sender = "👤 کاربر" if msg['is_user'] else "👨‍💼 پشتیبان"
        message += (
            f"{sender}:\n"
            f"{msg['text']}\n"
            f"⏰ {format_time_ago(msg['sent_at'])}\n\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="support",
        buttons=[
            ("💬 پاسخ", f"support_reply_{ticket_id}"),
            ("✅ بستن", f"support_close_{ticket_id}"),
            ("🔙 بازگشت", "support_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return VIEWING_TICKET

async def reply_to_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start replying to a ticket."""
    query = update.callback_query
    await query.answer()
    
    # Get ticket ID from callback data
    ticket_id = query.data.split('_')[-1]
    
    # Store ticket ID in context
    context.user_data['reply_to_ticket'] = ticket_id
    
    message = (
        "💬 <b>ارسال پاسخ</b>\n\n"
        f"در حال پاسخ به تیکت #{ticket_id}\n"
        "لطفاً متن پاسخ خود را ارسال کنید:"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="support",
        buttons=[("❌ انصراف", f"support_view_{ticket_id}")]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return REPLYING_TO_TICKET

async def send_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send reply to ticket."""
    message = update.message
    
    # Get ticket ID from context
    ticket_id = context.user_data.get('reply_to_ticket')
    if not ticket_id:
        await message.reply_text(
            "❌ خطا: شناسه تیکت یافت نشد.\n"
            "لطفاً دوباره تلاش کنید."
        )
        return SELECTING_SUPPORT_ACTION
    
    try:
        # Send reply
        result = await support_service.reply_to_ticket(
            ticket_id=ticket_id,
            text=message.text,
            admin_id=update.effective_user.id
        )
        
        # Clear ticket ID from context
        context.user_data.pop('reply_to_ticket', None)
        
        # Show success message
        await message.reply_text(
            "✅ پاسخ شما با موفقیت ارسال شد."
        )
        
        # Return to ticket view
        return await view_ticket(update, context)
        
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")
        await message.reply_text(
            "❌ خطا در ارسال پاسخ.\n"
            "لطفاً دوباره تلاش کنید."
        )
        return REPLYING_TO_TICKET

async def confirm_close_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for confirmation before closing ticket."""
    query = update.callback_query
    await query.answer()
    
    # Get ticket ID from callback data
    ticket_id = query.data.split('_')[-1]
    
    message = (
        "⚠️ <b>بستن تیکت</b>\n\n"
        f"آیا از بستن تیکت #{ticket_id} اطمینان دارید؟\n"
        "پس از بستن تیکت، کاربر نمی‌تواند پیام جدیدی ارسال کند."
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="support",
        buttons=[
            ("✅ تأیید", f"support_close_confirm_{ticket_id}"),
            ("❌ انصراف", f"support_view_{ticket_id}")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return CONFIRMING_CLOSE

async def close_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Close the ticket after confirmation."""
    query = update.callback_query
    await query.answer()
    
    # Get ticket ID from callback data
    ticket_id = query.data.split('_')[-1]
    
    try:
        # Close ticket
        result = await support_service.close_ticket(
            ticket_id=ticket_id,
            admin_id=update.effective_user.id
        )
        
        message = (
            "✅ <b>تیکت بسته شد</b>\n\n"
            f"تیکت #{ticket_id} با موفقیت بسته شد.\n"
            f"📅 تاریخ: {format_date(datetime.now())}"
        )
        
    except Exception as e:
        logger.error(f"Failed to close ticket: {e}")
        message = (
            "❌ <b>خطا در بستن تیکت</b>\n\n"
            f"علت: {str(e)}"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="support",
        buttons=[("🔙 بازگشت", "support_menu")]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_SUPPORT_ACTION

async def show_support_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show detailed support statistics."""
    query = update.callback_query
    await query.answer()
    
    # Get detailed stats
    stats = await support_service.get_detailed_stats()
    
    message = (
        "📊 <b>آمار پشتیبانی</b>\n\n"
        "🎫 <b>وضعیت تیکت‌ها:</b>\n"
        f"• کل تیکت‌ها: {stats['total_tickets']}\n"
        f"• باز: {stats['open_tickets']}\n"
        f"• در انتظار: {stats['pending_tickets']}\n"
        f"• بسته شده: {stats['closed_tickets']}\n\n"
        "⏱ <b>زمان پاسخگویی:</b>\n"
        f"• میانگین: {stats['avg_response_time']}\n"
        f"• حداقل: {stats['min_response_time']}\n"
        f"• حداکثر: {stats['max_response_time']}\n\n"
        "📈 <b>آمار هفته اخیر:</b>\n"
        f"• تیکت‌های جدید: {stats['new_tickets_week']}\n"
        f"• پاسخ‌های ارسالی: {stats['replies_week']}\n"
        f"• تیکت‌های بسته شده: {stats['closed_tickets_week']}\n\n"
        "👥 <b>عملکرد پشتیبان‌ها:</b>\n"
        f"{stats['admin_performance']}"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="support",
        buttons=[
            ("📥 دانلود گزارش", "support_download_stats"),
            ("🔄 بروزرسانی", "support_stats"),
            ("🔙 بازگشت", "support_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_SUPPORT_ACTION

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

support_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(support_menu, pattern="^admin_support$")
    ],
    states={
        SELECTING_SUPPORT_ACTION: [
            CallbackQueryHandler(list_tickets, pattern="^support_(open|pending|closed)"),
            CallbackQueryHandler(view_ticket, pattern="^support_view_"),
            CallbackQueryHandler(show_support_stats, pattern="^support_stats$"),
            CallbackQueryHandler(support_menu, pattern="^support_menu$"),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
        ],
        VIEWING_TICKET: [
            CallbackQueryHandler(reply_to_ticket, pattern="^support_reply_"),
            CallbackQueryHandler(confirm_close_ticket, pattern="^support_close_"),
            CallbackQueryHandler(support_menu, pattern="^support_menu$")
        ],
        REPLYING_TO_TICKET: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, send_reply),
            CallbackQueryHandler(view_ticket, pattern="^support_view_")
        ],
        CONFIRMING_CLOSE: [
            CallbackQueryHandler(close_ticket, pattern="^support_close_confirm_"),
            CallbackQueryHandler(view_ticket, pattern="^support_view_")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
    ],
    map_to_parent={
        ConversationHandler.END: 'SELECTING_ADMIN_ACTION'
    }
) 