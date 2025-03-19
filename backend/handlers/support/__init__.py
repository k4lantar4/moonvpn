"""
Support handlers for the MoonVPN Telegram bot.
"""

from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging
from typing import List, Any

from .support import support_command, support_handler, support_ticket_handler, support_message_handler, support_contact_handler, support_history_handler, support_ticket_view_handler, get_support_handlers

__all__ = ["support_command", "support_handler", "get_support_handlers"]

def get_support_handler():
    """
    Get the support handler.
    
    Returns:
        The support handler.
    """
    return get_support_handlers() 