"""
Unknown command handler.

This module contains the handler for unknown commands.
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from core.utils.i18n import get_text
from core.database import get_user_language

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    if not update.message:
        return
    
    user_id = update.effective_user.id
    language_code = get_user_language(user_id) or "en"
    
    await update.message.reply_text(
        get_text("unknown_command", language_code),
        parse_mode=ParseMode.MARKDOWN
    ) 