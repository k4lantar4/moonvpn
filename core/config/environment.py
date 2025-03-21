"""
Environment Configuration for MoonVPN

This module provides a centralized configuration for all environment variables used in the application.
Each variable is documented with its purpose, default value, and any validation rules.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Environment:
    """Environment configuration manager for MoonVPN."""
    
    # Database Configuration
    DB_HOST: str = os.getenv('MOONVPN_DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('MOONVPN_DB_PORT', '5432'))
    DB_NAME: str = os.getenv('MOONVPN_DB_NAME', 'moonvpn')
    DB_USER: str = os.getenv('MOONVPN_DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('MOONVPN_DB_PASSWORD', 'postgres')
    DB_MAX_CONNECTIONS: int = int(os.getenv('MOONVPN_DB_MAX_CONNECTIONS', '100'))
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv('MOONVPN_REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('MOONVPN_REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('MOONVPN_REDIS_DB', '0'))
    
    # Panel Configuration
    PANEL_TYPE: str = os.getenv('MOONVPN_PANEL_TYPE', 'xui')  # xui or v2ray
    PANEL_DOMAIN: str = os.getenv('MOONVPN_PANEL_DOMAIN', 'vpn-panel.example.com')
    PANEL_PORT: int = int(os.getenv('MOONVPN_PANEL_PORT', '2096'))
    PANEL_USERNAME: str = os.getenv('MOONVPN_PANEL_USERNAME', 'admin')
    PANEL_PASSWORD: str = os.getenv('MOONVPN_PANEL_PASSWORD', 'admin')
    PANEL_API_PATH: str = os.getenv('MOONVPN_PANEL_API_PATH', '/panel/api')
    PANEL_SSL: bool = os.getenv('MOONVPN_PANEL_SSL', 'false').lower() == 'true'
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv('MOONVPN_BOT_TOKEN', '')
    ADMIN_ID: int = int(os.getenv('MOONVPN_ADMIN_ID', '0'))
    ADMIN_USERNAME: str = os.getenv('MOONVPN_ADMIN_USERNAME', 'admin')
    
    # Payment Configuration
    CARD_NUMBER: str = os.getenv('MOONVPN_CARD_NUMBER', '')
    CARD_HOLDER: str = os.getenv('MOONVPN_CARD_HOLDER', '')
    CARD_BANK: str = os.getenv('MOONVPN_CARD_BANK', '')
    
    # Feature Flags
    FEATURE_PAYMENTS: bool = os.getenv('MOONVPN_FEATURE_PAYMENTS', 'true').lower() == 'true'
    FEATURE_ACCOUNT_CREATION: bool = os.getenv('MOONVPN_FEATURE_ACCOUNT_CREATION', 'true').lower() == 'true'
    FEATURE_CHANGE_LOCATION: bool = os.getenv('MOONVPN_FEATURE_CHANGE_LOCATION', 'true').lower() == 'true'
    FEATURE_TRAFFIC_QUERY: bool = os.getenv('MOONVPN_FEATURE_TRAFFIC_QUERY', 'true').lower() == 'true'
    
    # Application Settings
    DEBUG: bool = os.getenv('MOONVPN_DEBUG', 'false').lower() == 'true'
    DEFAULT_LANGUAGE: str = os.getenv('MOONVPN_DEFAULT_LANGUAGE', 'fa')
    SECRET_KEY: str = os.getenv('MOONVPN_SECRET_KEY', 'your-secret-key-here')
    ALLOWED_HOSTS: list = os.getenv('MOONVPN_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    
    # Backup Configuration
    BACKUP_STORAGE_PATH: str = os.getenv('MOONVPN_BACKUP_STORAGE_PATH', '/backups')
    BACKUP_RETENTION_DAYS: int = int(os.getenv('MOONVPN_BACKUP_RETENTION_DAYS', '30'))
    BACKUP_ENCRYPTION_KEY: Optional[str] = os.getenv('MOONVPN_BACKUP_ENCRYPTION_KEY')
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get the database URL for SQLAlchemy."""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def get_panel_url(cls) -> str:
        """Get the panel URL with proper protocol."""
        protocol = 'https' if cls.PANEL_SSL else 'http'
        return f"{protocol}://{cls.PANEL_DOMAIN}:{cls.PANEL_PORT}"
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """
        Validate required environment variables and return any validation errors.
        
        Returns:
            Dict[str, Any]: Dictionary of validation errors, empty if all valid
        """
        errors = {}
        
        # Validate required variables
        if not cls.BOT_TOKEN:
            errors['BOT_TOKEN'] = 'Bot token is required'
            
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'your-secret-key-here':
            errors['SECRET_KEY'] = 'A secure secret key is required'
            
        if cls.ADMIN_ID == 0:
            errors['ADMIN_ID'] = 'Admin ID is required'
            
        # Validate panel configuration
        if cls.PANEL_TYPE not in ['xui', 'v2ray']:
            errors['PANEL_TYPE'] = 'Panel type must be either "xui" or "v2ray"'
            
        return errors

# Initialize and validate environment
env = Environment()
validation_errors = env.validate()

if validation_errors:
    raise ValueError(f"Environment validation failed: {validation_errors}") 