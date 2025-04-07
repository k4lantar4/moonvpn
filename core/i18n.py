"""
Translation and localization utilities for the application.

This module provides functions for handling translations and language settings.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Language cache - load all language files at startup
_translations: Dict[str, Dict[str, str]] = {}

def _parse_languages() -> List[str]:
    """Parse supported languages from settings."""
    try:
        languages_str = settings.SUPPORTED_LANGUAGES
        if isinstance(languages_str, str):
            # Try to parse as JSON
            languages = json.loads(languages_str)
            if isinstance(languages, list):
                return languages
    except Exception as e:
        logger.error(f"Error parsing supported languages: {e}")
    
    # Default fallback
    return ["fa", "en"]

def load_translations() -> None:
    """Load translations from JSON files."""
    global _translations
    
    locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locales')
    logger.info(f"Loading translations from: {locales_dir}")
    
    if not os.path.exists(locales_dir):
        logger.warning(f"Locales directory not found: {locales_dir}")
        return
    
    # Parse languages and log for debugging
    supported_languages = _parse_languages()
    logger.info(f"Supported languages: {supported_languages}")
    
    # Check all files in the locales directory
    for filename in os.listdir(locales_dir):
        logger.info(f"Found file in locales directory: {filename}")
    
    for lang in supported_languages:
        lang_file = os.path.join(locales_dir, f"{lang}.json")
        
        try:
            if os.path.exists(lang_file):
                with open(lang_file, 'r', encoding='utf-8') as f:
                    _translations[lang] = json.load(f)
                logger.info(f"Loaded {len(_translations[lang])} translations for {lang}")
            else:
                logger.warning(f"Translation file not found: {lang_file}")
                _translations[lang] = {}
        except Exception as e:
            logger.error(f"Error loading translations for {lang}: {str(e)}")
            _translations[lang] = {}

def get_text(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Get translated text for a given key.
    
    Args:
        key: The translation key
        lang: Language code (defaults to DEFAULT_LANGUAGE in settings)
        **kwargs: Variables to format the translation with
        
    Returns:
        str: Translated text, or the key itself if not found
    """
    if not _translations:
        load_translations()
    
    # Use default language if none provided
    if not lang:
        lang = settings.DEFAULT_LANGUAGE
    
    # Fall back to default language if requested language not available
    if lang not in _translations:
        logger.warning(f"Language {lang} not available, falling back to {settings.DEFAULT_LANGUAGE}")
        lang = settings.DEFAULT_LANGUAGE
    
    # Get translation or use key as fallback
    text = _translations.get(lang, {}).get(key, key)
    
    # Format with variables if provided
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing key in translation format: {e}")
            return text
        except Exception as e:
            logger.error(f"Error formatting translation: {e}")
            return text
    
    return text

# Load translations at module initialization
load_translations() 