"""
Inline keyboard for language selection.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Placeholder for translation - adapt if you have a real system
def _(text):
    return text

# Define supported languages (can be moved to config later)
SUPPORTED_LANGUAGES = {
    "fa": "🇮🇷 فارسی",
    "en": "🇬🇧 English",
}

def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Creates an inline keyboard for selecting the bot language."""
    builder = InlineKeyboardBuilder()
    
    for code, name in SUPPORTED_LANGUAGES.items():
        builder.row(
            InlineKeyboardButton(text=name, callback_data=f"set_lang_{code}")
        )
        
    return builder.as_markup() 