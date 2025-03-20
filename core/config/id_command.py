"""
ID Command handler for the Telegram bot.

This module implements a simple handler to show users their IDs and chat IDs.
"""

import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ParseMode

# Import filters
from core.utils.formatting import allowed_group_filter

# Setup logging
logger = logging.getLogger("telegram_bot")

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user their ID and chat ID."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Format message with user and chat info
    message = "📋 *شناسه‌های تلگرام*\n\n"
    
    # User info
    message += f"👤 *شناسه شما:* `{user.id}`\n"
    if user.username:
        message += f"🔹 نام کاربری: @{user.username}\n"
    message += f"🔹 نام: {user.first_name}"
    if user.last_name:
        message += f" {user.last_name}"
    message += "\n\n"
    
    # Chat info
    message += f"💬 *شناسه این چت:* `{chat.id}`\n"
    
    if chat.type != "private":
        message += f"🔹 نوع چت: {chat.type}\n"
        message += f"🔹 عنوان: {chat.title}\n"
        if chat.username:
            message += f"🔹 نام کاربری: @{chat.username}\n"
    else:
        message += "🔹 نوع چت: خصوصی\n"
    
    # Add note for groups
    if chat.type in ["group", "supergroup"]:
        message += "\n🔸 *نکته:* برای استفاده از ربات در گروه‌ها، لازم است گروه توسط ادمین ربات تأیید شود."

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

def get_id_handler():
    """Return the ID command handler."""
    return CommandHandler("id", id_command, filters=allowed_group_filter) 