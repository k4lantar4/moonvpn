"""
MoonVPN Telegram Bot - Internationalization.

This module provides utilities for translating messages in MoonVPN Telegram Bot.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from core.config import BOT_DIR, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)

# Translation dictionaries
TRANSLATIONS = {}

# Load translations from files
LOCALE_DIR = BOT_DIR / "locales"
LOCALE_DIR.mkdir(exist_ok=True)

# Ensure we have at least a basic translation file for the default language
DEFAULT_LOCALE_FILE = LOCALE_DIR / f"{DEFAULT_LANGUAGE}.json"
if not DEFAULT_LOCALE_FILE.exists():
    # Create a basic translation file
    TRANSLATIONS[DEFAULT_LANGUAGE] = {}
    with open(DEFAULT_LOCALE_FILE, "w", encoding="utf-8") as f:
        json.dump(TRANSLATIONS[DEFAULT_LANGUAGE], f, ensure_ascii=False, indent=2)

# Load all available translations
for locale_file in LOCALE_DIR.glob("*.json"):
    locale_name = locale_file.stem
    try:
        with open(locale_file, "r", encoding="utf-8") as f:
            TRANSLATIONS[locale_name] = json.load(f)
        logger.info(f"Loaded translations for {locale_name}")
    except Exception as e:
        logger.error(f"Failed to load translations for {locale_name}: {e}")
        TRANSLATIONS[locale_name] = {}

def _(text: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """
    Translate a message to the specified language.
    
    Args:
        text: The text to translate
        lang: The language code to translate to
        
    Returns:
        The translated text, or the original text if no translation is available
    """
    if lang not in TRANSLATIONS:
        # Fallback to default language
        lang = DEFAULT_LANGUAGE
    
    # Try to find the translation
    translation = TRANSLATIONS.get(lang, {}).get(text)
    if translation:
        return translation
    
    # If not found in the specified language, try default language
    if lang != DEFAULT_LANGUAGE:
        translation = TRANSLATIONS.get(DEFAULT_LANGUAGE, {}).get(text)
        if translation:
            return translation
    
    # If still not found, add it to the translations file for the default language
    if text not in TRANSLATIONS.get(DEFAULT_LANGUAGE, {}):
        TRANSLATIONS.setdefault(DEFAULT_LANGUAGE, {})[text] = text
        
        # Save the updated translations
        with open(DEFAULT_LOCALE_FILE, "w", encoding="utf-8") as f:
            json.dump(TRANSLATIONS[DEFAULT_LANGUAGE], f, ensure_ascii=False, indent=2)
    
    # Return the original text as fallback
    return text

# Alias for backward compatibility
get_text = _

def set_language(user_id: int, lang: str) -> None:
    """
    Set a user's preferred language.
    
    Args:
        user_id: The user's ID
        lang: The language code to set
    """
    # This function would typically update the user's language preference in the database
    # For now, it's a placeholder
    pass

def get_available_languages() -> Dict[str, str]:
    """
    Get a dictionary of available languages.
    
    Returns:
        A dictionary mapping language codes to language names
    """
    languages = {
        "fa": "فارسی",
        "en": "English"
    }
    
    # Add any additional languages found in locale files
    for locale in TRANSLATIONS:
        if locale not in languages:
            languages[locale] = locale
    
    return languages 