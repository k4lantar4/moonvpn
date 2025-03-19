"""
MoonVPN Telegram Bot - Configuration Utilities.

This module provides configuration utilities for the MoonVPN Telegram bot.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "telegram_token": "6505866524:AAFHYB6cbx0OZ_jCk0oiWg55bysDftGkUAY",
    "admin_ids": [1713374557],
    "support_username": "@moonvpn_admin",
    "payment_methods": ["card", "crypto"],
    "card_number": "6037997123456789",
    "card_holder": "محمد محمدی",
    "maintenance_mode": False,
    "default_language": "fa",
    "welcome_message": "به ربات MoonVPN خوش آمدید!",
    "vpn_panel_url": "https://panel.moonvpn.ir",
    "vpn_panel_api_key": "your_api_key_here"
}

# Configuration file path
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.json"

def load_config() -> Dict[str, Any]:
    """
    Load configuration from file or environment variables.
    
    Returns:
        A dictionary containing the configuration.
    """
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from config file
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                file_config = json.load(f)
                config.update(file_config)
                logger.info(f"Loaded configuration from {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Error loading configuration from file: {e}")
    
    # Override with environment variables
    for key in config.keys():
        env_key = f"MOONVPN_{key.upper()}"
        if env_key in os.environ:
            try:
                # Try to parse as JSON for complex types
                try:
                    value = json.loads(os.environ[env_key])
                except json.JSONDecodeError:
                    # If not valid JSON, use as string
                    value = os.environ[env_key]
                
                config[key] = value
                logger.info(f"Overriding configuration from environment: {key}")
            except Exception as e:
                logger.error(f"Error parsing environment variable {env_key}: {e}")
    
    return config

def save_config(config: Dict[str, Any]) -> bool:
    """
    Save configuration to file.
    
    Args:
        config: The configuration to save.
        
    Returns:
        True if the configuration was saved successfully, False otherwise.
    """
    try:
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        
        # Save configuration to file
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
            
        logger.info(f"Saved configuration to {CONFIG_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration to file: {e}")
        return False

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value.
    
    Args:
        key: The configuration key.
        default: The default value to return if the key is not found.
        
    Returns:
        The configuration value.
    """
    config = load_config()
    return config.get(key, default)

def set_config_value(key: str, value: Any) -> bool:
    """
    Set a configuration value.
    
    Args:
        key: The configuration key.
        value: The configuration value.
        
    Returns:
        True if the configuration was saved successfully, False otherwise.
    """
    config = load_config()
    config[key] = value
    return save_config(config)

def is_admin(user_id: int) -> bool:
    """
    Check if the user is an admin.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if the user is an admin, False otherwise
    """
    try:
        # First, check in the database
        from core.database import get_user
        user = get_user(user_id)
        if user and user.get("is_admin", False):
            return True
        
        # Then, check in the config
        config = load_config()
        return str(user_id) in map(str, config["admin_ids"])
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

def get_card_payment_details() -> Dict[str, Any]:
    """
    Get card payment details.
    
    Returns:
        Dictionary containing card payment details
    """
    config = load_config()
    return config["card_payment"]

def get_zarinpal_details() -> Dict[str, Any]:
    """
    Get Zarinpal payment details.
    
    Returns:
        Dictionary containing Zarinpal payment details
    """
    config = load_config()
    return config["zarinpal"]

def get_threexui_config() -> Dict[str, Any]:
    """
    Get 3X-UI API configuration.
    
    Returns:
        Dictionary containing 3X-UI API configuration
    """
    config = load_config()
    return config["threexui"]

class Config:
    """
    Configuration class for the Telegram bot.
    
    This class provides a convenient interface for accessing configuration settings.
    """
    
    @staticmethod
    def load():
        """
        Load configuration settings.
        
        Returns:
            Dictionary containing configuration settings
        """
        return load_config()
    
    @staticmethod
    def is_admin(user_id: int) -> bool:
        """
        Check if the user is an admin.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if the user is an admin, False otherwise
        """
        return is_admin(user_id)
    
    @staticmethod
    def get_card_payment_details() -> Dict[str, Any]:
        """
        Get card payment details.
        
        Returns:
            Dictionary containing card payment details
        """
        return get_card_payment_details()
    
    @staticmethod
    def get_zarinpal_details() -> Dict[str, Any]:
        """
        Get Zarinpal payment details.
        
        Returns:
            Dictionary containing Zarinpal payment details
        """
        return get_zarinpal_details()
    
    @staticmethod
    def get_threexui_config() -> Dict[str, Any]:
        """
        Get 3X-UI API configuration.
        
        Returns:
            Dictionary containing 3X-UI API configuration
        """
        return get_threexui_config() 