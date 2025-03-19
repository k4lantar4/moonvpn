"""
Group management admin commands for MoonVPN Telegram Bot.

This module provides admin commands for managing groups, including:
- Allowed groups where the bot can operate
- Management groups for various admin functions
"""

import logging
from typing import List, Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

from core.utils.helpers import is_admin
from core.utils.formatting import admin_filter
from core.utils.helpers import get_formatted_datetime

logger = logging.getLogger(__name__)

# States
SELECTING_GROUP_TYPE = 0

# Callback data patterns
GROUP_MANAGEMENT = "group_management"
ALLOWED_GROUPS = "goto_allowed_groups"
MANAGEMENT_GROUPS = "goto_management_groups"

async def group_management_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle /group_management command to show group management options.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        Next state
    """
    user_id = update.effective_user.id
    
    # Check if user is admin
    if not await is_admin(user_id):
        await update.message.reply_text("⛔️ شما دسترسی ادمین ندارید.")
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("🏢 مدیریت گروه‌های مجاز", callback_data=ALLOWED_GROUPS)],
        [InlineKeyboardButton("🔔 مدیریت گروه‌های مدیریتی", callback_data=MANAGEMENT_GROUPS)],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "👥 <b>مدیریت گروه‌ها</b>\n\n"
        "از این بخش می‌توانید گروه‌های مرتبط با ربات را مدیریت کنید:\n\n"
        "🏢 <b>گروه‌های مجاز:</b> گروه‌هایی که ربات در آن‌ها فعال است\n"
        "🔔 <b>گروه‌های مدیریتی:</b> گروه‌هایی که برای دریافت اعلان‌ها و مدیریت استفاده می‌شوند\n\n"
        "لطفاً یک گزینه را انتخاب کنید:"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    return SELECTING_GROUP_TYPE

async def handle_group_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle selection of group type to manage.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        Next state
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == ALLOWED_GROUPS:
        # Redirect to allowed groups command
        await query.edit_message_text("در حال انتقال به بخش مدیریت گروه‌های مجاز...")
        # Simulate /allowed_groups command
        context.args = []
        from handlers.admin.allowed_groups import allowed_groups_command
        return await allowed_groups_command(update, context)
    
    elif callback_data == MANAGEMENT_GROUPS:
        # Redirect to management groups command
        await query.edit_message_text("در حال انتقال به بخش مدیریت گروه‌های مدیریتی...")
        # Simulate /management_groups command
        context.args = []
        from handlers.admin.management_groups import management_groups_command
        return await management_groups_command(update, context)
    
    elif callback_data == "back":
        # Go back to admin dashboard
        await query.edit_message_text("بازگشت به منوی اصلی...")
        return ConversationHandler.END
    
    # If we get here, something went wrong
    await query.edit_message_text("❌ خطا در پردازش درخواست.")
    return ConversationHandler.END

def get_group_management_handlers() -> List:
    """
    Get handlers for group management admin commands.
    
    Returns:
        List of handlers
    """
    group_management_handler = ConversationHandler(
        entry_points=[CommandHandler("group_management", group_management_command, filters=admin_filter)],
        states={
            SELECTING_GROUP_TYPE: [
                CallbackQueryHandler(handle_group_type_selection, pattern=f"^({ALLOWED_GROUPS}|{MANAGEMENT_GROUPS}|back)$")
            ],
        },
        fallbacks=[],
        name="group_management_conversation",
        persistent=False
    )
    
    return [group_management_handler] 