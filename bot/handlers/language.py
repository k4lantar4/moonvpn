"""
Language selection handlers for the Telegram bot.

This module provides handlers for managing user language preferences.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, filters

from core.config import get_settings
from core.database import get_db_session
from api.models import User
from core.i18n import get_text

logger = logging.getLogger(__name__)
settings = get_settings()

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /language command."""
    user_id = update.effective_user.id
    logger.info(f"Language command from user {user_id}")
    
    # Create language selection keyboard
    keyboard = []
    for lang in settings.SUPPORTED_LANGUAGES:
        emoji = "🇮🇷" if lang == "fa" else "🇬🇧"
        text = "فارسی" if lang == "fa" else "English"
        keyboard.append([InlineKeyboardButton(f"{emoji} {text}", callback_data=f"lang_{lang}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌐 Please select your language:\n\n"
        "🗣 لطفاً زبان خود را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection callback."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get the selected language from callback data
    lang = query.data.split("_")[1]
    logger.info(f"User {user_id} selected language: {lang}")
    
    await query.answer()
    
    # Update user's language preference in database
    try:
        db_session = await get_db_session()
        user = db_session.query(User).filter(User.telegram_id == user_id).first()
        
        if user:
            user.lang = lang
            db_session.commit()
            logger.info(f"Updated language preference for user {user_id} to {lang}")
        else:
            logger.warning(f"User {user_id} not found in database")
        
        db_session.close()
        
        # Send confirmation message
        if lang == "fa":
            message = "✅ زبان شما به فارسی تغییر کرد."
        else:
            message = "✅ Your language has been set to English."
        
        await query.edit_message_text(text=message)
        
    except Exception as e:
        logger.error(f"Error updating language preference: {str(e)}")
        await query.edit_message_text(text="❌ Error setting language preference. Please try again.")

def setup_handlers(application):
    """Set up language-related handlers."""
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    
    logger.info("Language handlers registered") 