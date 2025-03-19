"""
Traffic reports handler for admin panel.
"""

import logging
from typing import Dict, Any, List
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler
)

from bot.services import vpn_service
from bot.utils import (
    get_traffic_report_message,
    build_navigation_keyboard
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_TRAFFIC_VIEW = 1

async def traffic_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show traffic reports menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="traffic"
    )
    
    # Get daily traffic report by default
    report = await vpn_service.get_traffic_stats(period='daily')
    message = get_traffic_report_message(report)
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_TRAFFIC_VIEW

async def show_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show traffic report for selected period."""
    query = update.callback_query
    await query.answer()
    
    # Get period from callback data
    period = query.data.split('_')[1]
    
    # Get report
    report = await vpn_service.get_traffic_stats(period=period)
    message = get_traffic_report_message(report)
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="traffic"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_TRAFFIC_VIEW

async def show_top_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show top traffic users."""
    query = update.callback_query
    await query.answer()
    
    # Get top users
    users = await vpn_service.get_top_users(metric='traffic', limit=10)
    
    # Format message
    message = "📊 کاربران برتر (مصرف ترافیک)\n\n"
    for i, user in enumerate(users, 1):
        message += (
            f"{i}. {user.get('first_name', 'کاربر')} "
            f"(@{user.get('username', 'بدون نام کاربری')})\n"
            f"📈 مصرف: {format_bytes(user['total_traffic'])}\n"
            f"✅ اشتراک فعال: {user['active_accounts']}\n\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="traffic"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_TRAFFIC_VIEW

async def show_traffic_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show traffic usage alerts."""
    query = update.callback_query
    await query.answer()
    
    # Get alerts
    alerts = await vpn_service.get_traffic_alerts()
    
    # Format message
    message = "⚠️ هشدارهای مصرف ترافیک\n\n"
    for alert in alerts:
        message += (
            f"👤 {alert['user'].get('first_name', 'کاربر')} "
            f"(@{alert['user'].get('username', 'بدون نام کاربری')})\n"
            f"📊 مصرف: {format_traffic_usage(alert['traffic_used'], alert['traffic_limit'])}\n"
            f"📅 انقضا: {format_date(alert['expiry_date'])}\n\n"
        )
    
    if not alerts:
        message += "هیچ هشداری وجود ندارد."
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="traffic"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_TRAFFIC_VIEW

async def show_traffic_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show traffic usage chart."""
    query = update.callback_query
    await query.answer()
    
    # TODO: Implement traffic chart generation
    message = (
        "📊 نمودار مصرف ترافیک\n\n"
        "این قابلیت به زودی اضافه خواهد شد."
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="traffic"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_TRAFFIC_VIEW

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

traffic_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(traffic_menu, pattern="^admin_traffic$")
    ],
    states={
        SELECTING_TRAFFIC_VIEW: [
            CallbackQueryHandler(show_traffic, pattern="^traffic_(daily|weekly|monthly)$"),
            CallbackQueryHandler(show_top_users, pattern="^traffic_top_users$"),
            CallbackQueryHandler(show_traffic_alerts, pattern="^traffic_alerts$"),
            CallbackQueryHandler(show_traffic_chart, pattern="^traffic_chart$"),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
    ],
    map_to_parent={
        ConversationHandler.END: 'SELECTING_ADMIN_ACTION'
    }
) 