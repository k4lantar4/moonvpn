"""
Income reports handler for admin panel.
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

from bot.services import payment_service
from bot.utils import (
    get_income_report_message,
    build_navigation_keyboard
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_REPORT_PERIOD = 1

async def income_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show income reports menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="income"
    )
    
    # Get daily report by default
    report = await payment_service.get_income_reports(period='daily')
    message = get_income_report_message(report)
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_REPORT_PERIOD

async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show income report for selected period."""
    query = update.callback_query
    await query.answer()
    
    # Get period from callback data
    period = query.data.split('_')[1]
    
    # Get report
    report = await payment_service.get_income_reports(period=period)
    message = get_income_report_message(report)
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="income"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_REPORT_PERIOD

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

income_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(income_menu, pattern="^admin_income$")
    ],
    states={
        SELECTING_REPORT_PERIOD: [
            CallbackQueryHandler(show_report, pattern="^report_(daily|weekly|monthly)$"),
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