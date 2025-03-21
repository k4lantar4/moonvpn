"""
MoonVPN Telegram Bot - Internationalization Utilities.

This module provides internationalization utilities for the MoonVPN Telegram bot.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from telegram import Update
from telegram.ext import ContextTypes

from core.config import get_config_value

# Configure logging
logger = logging.getLogger(__name__)

# Default language
DEFAULT_LANGUAGE = "fa"

# Translations dictionary
_translations: Dict[str, Dict[str, str]] = {}
_supported_languages: Dict[str, str] = {
    "fa": "فارسی",
    "en": "English",
}
_default_language = DEFAULT_LANGUAGE

def setup_i18n() -> None:
    """Set up internationalization by loading translation files."""
    global _translations, _default_language
    
    # Load translations for each supported language
    locales_dir = Path(__file__).parent.parent / "locales"
    
    if not locales_dir.exists():
        logger.warning(f"Locales directory not found: {locales_dir}")
        return
    
    for lang_code in _supported_languages:
        translations_file = locales_dir / f"{lang_code}.json"
        try:
            if translations_file.exists():
                with open(translations_file, "r", encoding="utf-8") as f:
                    _translations[lang_code] = json.load(f)
                logger.info(f"Loaded {len(_translations[lang_code])} translations for {lang_code}")
            else:
                logger.warning(f"Translation file not found: {translations_file}")
                _translations[lang_code] = {}
        except Exception as e:
            logger.error(f"Error loading translations for {lang_code}: {e}")
            _translations[lang_code] = {}
    
    # Make sure default language is available
    if _default_language not in _translations:
        logger.warning(f"Default language {_default_language} has no translations, using empty dictionary")
        _translations[_default_language] = {}

def _(text: str, lang_code: str = None, **kwargs) -> str:
    """
    Translate a text key into the specified language.
    
    Args:
        text (str): Text key to translate
        lang_code (str, optional): Language code. Defaults to default language.
        **kwargs: Format parameters for the translated string
        
    Returns:
        str: Translated string
    """
    if lang_code is None:
        lang_code = _default_language
    
    # Ensure the language is supported
    if lang_code not in _translations:
        lang_code = _default_language
    
    # Get the translation
    translation = _translations.get(lang_code, {}).get(text, text)
    
    # Apply formatting if kwargs provided
    if kwargs:
        try:
            return translation.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing format parameter in translation: {e}")
            return translation
        except Exception as e:
            logger.error(f"Error formatting translation: {e}")
            return translation
    
    return translation

def get_user_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """
    Get the language for the current user.
    
    Args:
        update (Update): Telegram update
        context (ContextTypes.DEFAULT_TYPE): Context
        
    Returns:
        str: Language code
    """
    # First check if language is stored in user data
    if context.user_data and "language" in context.user_data:
        return context.user_data["language"]
    
    # Then try to get from user's Telegram settings
    user_language = update.effective_user.language_code
    if user_language in _supported_languages:
        return user_language
    
    # Default to Persian
    return _default_language

def set_user_language(context: ContextTypes.DEFAULT_TYPE, lang_code: str) -> bool:
    """
    Set the language for the current user.
    
    Args:
        context (ContextTypes.DEFAULT_TYPE): Context
        lang_code (str): Language code
        
    Returns:
        bool: True if language was set, False otherwise
    """
    if lang_code in _supported_languages:
        context.user_data["language"] = lang_code
        return True
    return False

def get_supported_languages() -> Dict[str, str]:
    """
    Get the supported languages.
    
    Returns:
        Dict[str, str]: Dictionary of language codes to language names
    """
    return _supported_languages.copy()

def format_number(number: float, language: str = None) -> str:
    """
    Format a number according to language conventions.
    
    Args:
        number (float): Number to format
        language (str, optional): Language code. Defaults to default language.
        
    Returns:
        str: Formatted number
    """
    if language is None:
        language = _default_language
    
    # For Persian, use Persian numerals
    if language == "fa":
        # Convert to Persian numerals
        english_to_persian = {
            '0': '۰',
            '1': '۱',
            '2': '۲',
            '3': '۳',
            '4': '۴',
            '5': '۵',
            '6': '۶',
            '7': '۷',
            '8': '۸',
            '9': '۹',
            '.': '.',
        }
        
        # Format number with comma as thousands separator
        formatted = "{:,.2f}".format(number).rstrip('0').rstrip('.') if isinstance(number, float) else "{:,}".format(number)
        
        # Convert to Persian numerals
        persian_formatted = ''.join(english_to_persian.get(c, c) for c in formatted)
        return persian_formatted
    
    # For other languages, use standard formatting
    if isinstance(number, float):
        return "{:,.2f}".format(number).rstrip('0').rstrip('.')
    return "{:,}".format(number)

def format_date(date_obj, language: str = None) -> str:
    """
    Format a date according to language conventions.
    
    Args:
        date_obj: Date object (datetime.date or datetime.datetime)
        language (str, optional): Language code. Defaults to default language.
        
    Returns:
        str: Formatted date
    """
    if language is None:
        language = _default_language
    
    # For Persian, use Jalali calendar
    if language == "fa":
        try:
            import jdatetime
            j_date = jdatetime.date.fromgregorian(date=date_obj)
            return j_date.strftime("%Y/%m/%d")
        except ImportError:
            logger.warning("jdatetime module not installed, using Gregorian calendar for Persian")
            return date_obj.strftime("%Y/%m/%d")
        except Exception as e:
            logger.error(f"Error converting to Jalali date: {e}")
            return date_obj.strftime("%Y/%m/%d")
    
    # For other languages, use Gregorian calendar
    return date_obj.strftime("%Y/%m/%d")

def format_datetime(datetime_obj, language: str = None) -> str:
    """
    Format a datetime according to language conventions.
    
    Args:
        datetime_obj: Datetime object
        language (str, optional): Language code. Defaults to default language.
        
    Returns:
        str: Formatted datetime
    """
    if language is None:
        language = _default_language
    
    # For Persian, use Jalali calendar
    if language == "fa":
        try:
            import jdatetime
            j_datetime = jdatetime.datetime.fromgregorian(datetime=datetime_obj)
            return j_datetime.strftime("%Y/%m/%d %H:%M:%S")
        except ImportError:
            logger.warning("jdatetime module not installed, using Gregorian calendar for Persian")
            return datetime_obj.strftime("%Y/%m/%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error converting to Jalali datetime: {e}")
            return datetime_obj.strftime("%Y/%m/%d %H:%M:%S")
    
    # For other languages, use Gregorian calendar
    return datetime_obj.strftime("%Y/%m/%d %H:%M:%S")

def format_time_delta(seconds: int, language: str = None) -> str:
    """
    Format a time delta in seconds to human-readable format.
    
    Args:
        seconds (int): Time delta in seconds
        language (str, optional): Language code. Defaults to default language.
        
    Returns:
        str: Formatted time delta
    """
    if language is None:
        language = _default_language
    
    # Calculate days, hours, minutes, seconds
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Format components
    components = []
    
    if days > 0:
        components.append(_("{days} days", language, days=format_number(days, language)))
    
    if hours > 0:
        components.append(_("{hours} hours", language, hours=format_number(hours, language)))
    
    if minutes > 0 and days == 0:  # Show minutes only if less than a day
        components.append(_("{minutes} minutes", language, minutes=format_number(minutes, language)))
    
    if seconds > 0 and days == 0 and hours == 0:  # Show seconds only if less than an hour
        components.append(_("{seconds} seconds", language, seconds=format_number(seconds, language)))
    
    if not components:
        return _("0 seconds", language)
    
    return " ".join(components)

def get_text(key: str, language: Optional[str] = None, **kwargs) -> str:
    """
    Get a translated text for the given key.
    
    Args:
        key: The translation key.
        language: The language code. If None, the default language will be used.
        **kwargs: Variables to format the text with.
        
    Returns:
        The translated text.
    """
    if language is None:
        language = get_config_value("default_language", DEFAULT_LANGUAGE)
    
    # Fallback to default language if the specified language is not available
    if language not in _translations:
        language = DEFAULT_LANGUAGE
    
    # Get the translation
    translation = _translations.get(language, {}).get(key)
    
    # Fallback to default language if the key is not found
    if translation is None and language != DEFAULT_LANGUAGE:
        translation = _translations.get(DEFAULT_LANGUAGE, {}).get(key)
    
    # Fallback to the key itself if the translation is not found
    if translation is None:
        translation = key
    
    # Format the translation with the provided variables
    try:
        if kwargs:
            translation = translation.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing format variable in translation: {e}")
    except Exception as e:
        logger.error(f"Error formatting translation: {e}")
    
    return translation

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
    for locale in _translations:
        if locale not in languages:
            languages[locale] = locale
    
    return languages 