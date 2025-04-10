"""
Text utilities for the Telegram bot with multilingual support.

This module provides functions and utilities for managing text messages
in multiple languages, with a focus on Persian and English support.
"""

from typing import Optional
from core.i18n import get_i18n
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

def get_text(key: str, language: Optional[str] = None) -> str:
    """
    Get a translated text message for the given key.
    
    Args:
        key (str): The translation key (e.g., "welcome" or "error.general")
        language (Optional[str]): Override the current language
    
    Returns:
        str: The translated message
    """
    return get_i18n().get(key, language)

def get_welcome_message(language: Optional[str] = None) -> str:
    """Get the welcome message in the specified language."""
    return get_text("welcome", language)

def get_start_message(language: Optional[str] = None) -> str:
    """Get the start command message in the specified language."""
    return get_text("start_command", language)

def get_button_text(key: str, language: Optional[str] = None) -> str:
    """Get button text in the specified language."""
    return get_text(key, language)

def get_error_message(error_type: str = "general", language: Optional[str] = None) -> str:
    """Get an error message in the specified language."""
    return get_text(f"error.{error_type}", language)

def get_language_changed_message(language: Optional[str] = None) -> str:
    """Get the language changed confirmation message."""
    return get_text("language_changed", language)

def format_price(price) -> str:
    """Format a price with commas and تومان.

    Args:
        price: Price value

    Returns:
        str: Formatted price string
    """
    try:
        # Convert to integer if possible to remove decimals like .00
        price_int = int(float(price))
        return f"{price_int:,} تومان"
    except (ValueError, TypeError):
        return f"{price} تومان" # Fallback 