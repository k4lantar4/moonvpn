"""
Internationalization (i18n) module for handling translations in MoonVPN.

This module provides functionality for loading and managing translations from JSON files,
with support for multiple languages and fallback mechanisms.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from functools import lru_cache

from core.config import settings

logger = logging.getLogger(__name__)

class I18n:
    """
    Internationalization class for managing translations.
    
    Attributes:
        default_language (str): The default language to use when a translation is not found
        current_language (str): The currently active language
        translations (Dict): Dictionary containing all loaded translations
    """
    
    def __init__(self, default_language: str = "fa"):
        """
        Initialize the I18n instance.
        
        Args:
            default_language (str): The default language to use. Defaults to "fa".
        """
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, Any]] = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load all translation files from the locales directory."""
        base_path = Path("locales")
        if not base_path.exists():
            logger.error("Locales directory not found!")
            return
        
        for lang_dir in base_path.iterdir():
            if not lang_dir.is_dir():
                continue
                
            lang_code = lang_dir.name
            messages_file = lang_dir / "messages.json"
            
            if not messages_file.exists():
                logger.warning(f"No messages.json found for language {lang_code}")
                continue
                
            try:
                with messages_file.open("r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(f"Loaded translations for {lang_code}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse messages.json for language {lang_code}")
            except Exception as e:
                logger.error(f"Error loading translations for {lang_code}: {e}")
    
    def set_language(self, language: str) -> None:
        """
        Set the current language.
        
        Args:
            language (str): The language code to set as current
        """
        if language in self.translations:
            self.current_language = language
            logger.info(f"Language set to {language}")
        else:
            logger.warning(f"Language {language} not found, using default")
            self.current_language = self.default_language
    
    def get(self, key: str, language: Optional[str] = None) -> str:
        """
        Get a translated message for the given key.
        
        Args:
            key (str): The translation key (e.g., "welcome" or "error.general")
            language (Optional[str]): Override the current language
        
        Returns:
            str: The translated message or the key itself if not found
        """
        lang = language or self.current_language
        
        # Try to get translation in requested language
        try:
            return self._get_nested_value(self.translations[lang], key)["message"]
        except (KeyError, TypeError):
            # If not found, try default language
            if lang != self.default_language:
                try:
                    return self._get_nested_value(
                        self.translations[self.default_language], 
                        key
                    )["message"]
                except (KeyError, TypeError):
                    pass
            
            # If still not found, return the key
            logger.warning(f"Translation not found for key: {key}")
            return key
    
    @staticmethod
    def _get_nested_value(data: Dict[str, Any], key: str) -> Any:
        """
        Get a nested dictionary value using dot notation.
        
        Args:
            data (Dict[str, Any]): The dictionary to search in
            key (str): The key in dot notation (e.g., "error.general")
        
        Returns:
            Any: The value if found
            
        Raises:
            KeyError: If the key is not found
        """
        keys = key.split(".")
        value = data
        
        for k in keys:
            value = value[k]
        
        return value

@lru_cache()
def get_i18n() -> I18n:
    """
    Get or create a singleton instance of I18n.
    
    Returns:
        I18n: The I18n instance
    """
    return I18n(default_language=settings.DEFAULT_LANGUAGE) 