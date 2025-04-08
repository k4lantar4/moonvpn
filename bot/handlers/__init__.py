"""
Bot handlers package.

This package contains all the handlers for the Telegram bot.
""" 

from bot.handlers.language import setup_handlers as setup_language_handlers
from bot.handlers.user import setup_handlers as setup_user_handlers

__all__ = [
    'setup_language_handlers',
    'setup_user_handlers'
] 