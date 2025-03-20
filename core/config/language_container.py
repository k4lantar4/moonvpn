"""
Language selection handler for the Telegram bot.

This module handles language selection for users.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode

import logging
from typing import Dict, Any, List, Optional

from core.utils.i18n import get_text, get_available_languages
from core.database import get_user_language, update_user_language

# Configure logging
logger = logging.getLogger("telegram_bot")

# Conversation states
SELECTING_LANGUAGE = 1


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /language command."""
    user = update.effective_user
    user_id = user.id
    
    # Get user's current language preference
    current_language = get_user_language(user_id)
    
    # Show language selection menu
    await show_language_menu(update, context, current_language)
    
    return SELECTING_LANGUAGE


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle language selection callback."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    # Show language selection menu
    await show_language_menu(update, context, get_user_language(user_id))
    
    return SELECTING_LANGUAGE


async def select_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle language selection."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    # Get selected language from callback data
    # Expected format: "select_language:LANGUAGE_CODE"
    callback_data = query.data
    selected_language = callback_data.split(":")[1]
    
    # Update user's language preference
    update_user_language(user_id, selected_language)
    
    # Log language change
    logger.info(f"User {user_id} ({user.username}) changed language to {selected_language}")
    
    # Get text in the new language
    language_updated_text = get_text("language_updated", selected_language)
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_menu", selected_language),
                callback_data="back:start"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send confirmation message
    await query.edit_message_text(
        language_updated_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ConversationHandler.END


async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, current_language: str) -> None:
    """Show language selection menu."""
    # Get available languages
    available_languages = get_available_languages()
    
    # Create language selection message
    language_selection_text = get_text("select_language", current_language)
    
    # Create keyboard with language options
    keyboard = []
    
    # Add a button for each available language
    for lang_code, lang_name in available_languages.items():
        # Add a checkmark to the current language
        display_name = f"✅ {lang_name}" if lang_code == current_language else lang_name
        keyboard.append([
            InlineKeyboardButton(
                display_name,
                callback_data=f"select_language:{lang_code}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("back", current_language),
            callback_data="back:start"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            language_selection_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            language_selection_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )


def get_language_handler() -> ConversationHandler:
    """Create and return the language selection conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("language", language_command),
            CallbackQueryHandler(language_callback, pattern="^language$"),
        ],
        states={
            SELECTING_LANGUAGE: [
                CallbackQueryHandler(select_language_callback, pattern="^select_language:"),
                CallbackQueryHandler(language_callback, pattern="^language$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(select_language_callback, pattern="^select_language:"),
            CallbackQueryHandler(language_callback, pattern="^language$"),
        ],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END,
        },
    ) 