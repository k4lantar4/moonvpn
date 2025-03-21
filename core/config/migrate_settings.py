#!/usr/bin/env python3
"""
Script to migrate settings from .env.example to database.

This script handles:
1. Loading settings from .env.example
2. Validating settings format and types
3. Migrating settings to the database with proper categorization
4. Handling environment-specific settings
"""

import os
import json
import logging
import psycopg2
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setting categories
CATEGORY_GENERAL = 'general'
CATEGORY_PAYMENT = 'payment'
CATEGORY_TELEGRAM = 'telegram'
CATEGORY_VPN = 'vpn'
CATEGORY_NOTIFICATION = 'notification'
CATEGORY_SECURITY = 'security'

# Setting data types
TYPE_STRING = 'string'
TYPE_INTEGER = 'integer'
TYPE_FLOAT = 'float'
TYPE_BOOLEAN = 'boolean'
TYPE_JSON = 'json'
TYPE_DATETIME = 'datetime'

# Setting descriptions
SETTING_DESCRIPTIONS = {
    'APP_NAME': 'Name of the application',
    'DEBUG': 'Enable debug mode',
    'API_V1_PREFIX': 'API version 1 prefix',
    'SECRET_KEY': 'Application secret key',
    'ALGORITHM': 'JWT algorithm',
    'ACCESS_TOKEN_EXPIRE_MINUTES': 'JWT access token expiration time',
    'REFRESH_TOKEN_EXPIRE_MINUTES': 'JWT refresh token expiration time',
    'ALLOWED_HOSTS': 'List of allowed hosts',
    'CORS_ORIGINS': 'CORS allowed origins',
    'CORS_ALLOW_CREDENTIALS': 'Allow CORS credentials',
    'CORS_ALLOW_METHODS': 'CORS allowed methods',
    'CORS_ALLOW_HEADERS': 'CORS allowed headers',
    'MAX_LOGIN_ATTEMPTS': 'Maximum login attempts',
    'LOGIN_ATTEMPT_WINDOW': 'Login attempt window in seconds',
    'IP_BLOCK_DURATION': 'IP block duration in seconds',
    'GEOLOCATION_CHECK_ENABLED': 'Enable geolocation check',
    'MAX_LOGIN_DISTANCE_KM': 'Maximum login distance in kilometers',
    'DB_HOST': 'Database host',
    'DB_PORT': 'Database port',
    'DB_NAME': 'Database name',
    'DB_USER': 'Database user',
    'DB_PASSWORD': 'Database password',
    'REDIS_HOST': 'Redis host',
    'REDIS_PORT': 'Redis port',
    'REDIS_PASSWORD': 'Redis password',
    'REDIS_DB': 'Redis database number',
    'PANEL_HOST': '3x-UI panel host',
    'PANEL_PORT': '3x-UI panel port',
    'PANEL_USERNAME': '3x-UI panel username',
    'PANEL_PASSWORD': '3x-UI panel password',
    'PANEL_BASE_PATH': '3x-UI panel base path',
    'ZARINPAL_MERCHANT_ID': 'Zarinpal merchant ID',
    'ZARINPAL_SANDBOX': 'Enable Zarinpal sandbox mode',
    'CARD_NUMBER': 'Card number for payments',
    'CARD_HOLDER': 'Card holder name',
    'CARD_BANK': 'Card bank name',
    'PAYMENT_VERIFICATION_TIMEOUT': 'Payment verification timeout in minutes',
    'VPN_DEFAULT_PROTOCOL': 'Default VPN protocol',
    'VPN_DEFAULT_TRAFFIC_LIMIT_GB': 'Default VPN traffic limit in GB',
    'VPN_DEFAULT_EXPIRE_DAYS': 'Default VPN expiration in days',
    'TRAFFIC_CHECK_INTERVAL': 'Traffic check interval in seconds',
    'TRAFFIC_WARNING_THRESHOLDS': 'Traffic warning thresholds',
    'BANDWIDTH_WARNING_THRESHOLDS': 'Bandwidth warning thresholds',
    'BACKUP_ENABLED': 'Enable automatic backups',
    'BACKUP_INTERVAL': 'Backup interval in seconds',
    'BACKUP_RETENTION_DAYS': 'Backup retention period in days',
    'BACKUP_TYPES': 'Types of backups to perform',
    'ANALYTICS_ENABLED': 'Enable analytics',
    'ANALYTICS_UPDATE_INTERVAL': 'Analytics update interval in seconds',
    'ANALYTICS_RETENTION_DAYS': 'Analytics retention period in days',
    'ADMIN_NOTIFICATIONS': 'Admin notification settings',
    'USER_NOTIFICATIONS': 'User notification settings',
    'CACHE_TTL': 'Cache time-to-live settings',
    'POINTS_PER_PURCHASE': 'Points awarded per purchase',
    'POINTS_PER_REFERRAL': 'Points awarded per referral',
    'POINTS_EXPIRY_DAYS': 'Points expiration in days',
    'DEFAULT_LANGUAGE': 'Default application language',
    'SUPPORTED_LANGUAGES': 'Supported languages',
    'BOT_TOKEN': 'Telegram bot token',
    'ADMIN_ID': 'Admin user ID',
    'ADMIN_IDS': 'Admin user IDs',
    'MANAGER_IDS': 'Manager user IDs',
    'SUPPORT_IDS': 'Support user IDs',
    'WEBHOOK_MODE': 'Enable webhook mode',
    'WEBHOOK_URL': 'Webhook URL',
    'WEBHOOK_PATH': 'Webhook path',
    'WEBHOOK_PORT': 'Webhook port',
    'UPLOAD_DIR': 'Upload directory path',
    'RECEIPTS_DIR': 'Receipts directory path',
    'STATIC_DIR': 'Static files directory path',
    'TEMPLATES_DIR': 'Templates directory path'
}

@contextmanager
def get_db_connection():
    """Get a database connection with proper error handling."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'moonvpn'),
            user=os.getenv('DB_USER', 'moonvpn'),
            password=os.getenv('DB_PASSWORD', 'moonvpn')
        )
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def validate_setting(key: str, value: Any) -> Tuple[bool, str]:
    """Validate a setting value."""
    try:
        # Required settings
        required_settings = ['APP_NAME', 'SECRET_KEY', 'DB_HOST', 'DB_NAME']
        if key in required_settings and not value:
            return False, f"Required setting {key} cannot be empty"
        
        # Validate specific settings
        if key == 'DB_PORT' and not isinstance(value, int):
            return False, f"DB_PORT must be an integer"
        elif key == 'DEBUG' and not isinstance(value, bool):
            return False, f"DEBUG must be a boolean"
        elif key == 'ALLOWED_HOSTS' and not isinstance(value, list):
            return False, f"ALLOWED_HOSTS must be a list"
        elif key == 'CORS_ORIGINS' and not isinstance(value, list):
            return False, f"CORS_ORIGINS must be a list"
        elif key == 'CORS_ALLOW_METHODS' and not isinstance(value, list):
            return False, f"CORS_ALLOW_METHODS must be a list"
        elif key == 'CORS_ALLOW_HEADERS' and not isinstance(value, list):
            return False, f"CORS_ALLOW_HEADERS must be a list"
        
        return True, "Valid"
    except Exception as e:
        return False, str(e)

def get_setting_category(key: str) -> str:
    """Determine the category for a setting."""
    categories = {
        'APP_': CATEGORY_GENERAL,
        'DB_': CATEGORY_GENERAL,
        'REDIS_': CATEGORY_GENERAL,
        'SECRET_': CATEGORY_SECURITY,
        'JWT_': CATEGORY_SECURITY,
        'CORS_': CATEGORY_SECURITY,
        'PAYMENT_': CATEGORY_PAYMENT,
        'VPN_': CATEGORY_VPN,
        'BACKUP_': CATEGORY_GENERAL,
        'ANALYTICS_': CATEGORY_GENERAL,
        'NOTIFICATION_': CATEGORY_NOTIFICATION,
        'CACHE_': CATEGORY_GENERAL,
        'POINTS_': CATEGORY_GENERAL,
        'LANGUAGE_': CATEGORY_GENERAL,
        'TELEGRAM_': CATEGORY_TELEGRAM,
        'STORAGE_': CATEGORY_GENERAL
    }
    
    for prefix, category in categories.items():
        if key.startswith(prefix):
            return category
    return CATEGORY_GENERAL

def get_setting_data_type(value: Any) -> str:
    """Determine the data type for a setting value."""
    if isinstance(value, bool):
        return TYPE_BOOLEAN
    elif isinstance(value, int):
        return TYPE_INTEGER
    elif isinstance(value, float):
        return TYPE_FLOAT
    elif isinstance(value, (list, dict)):
        return TYPE_JSON
    else:
        return TYPE_STRING

def load_env_example() -> Dict[str, Any]:
    """Load settings from .env.example file with validation."""
    env_path = Path(__file__).parent.parent.parent.parent / '.env.example'
    settings = {}
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Handle different data types
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif value.startswith('[') or value.startswith('{'):
                            try:
                                value = json.loads(value)
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON value for {key}: {value}")
                        
                        # Validate setting
                        is_valid, message = validate_setting(key, value)
                        if not is_valid:
                            logger.warning(f"Invalid setting {key}: {message}")
                            continue
                        
                        settings[key] = value
                    except ValueError as e:
                        logger.warning(f"Error parsing line: {line}, Error: {e}")
                        continue
    except FileNotFoundError:
        logger.error(f"Could not find .env.example file at {env_path}")
        raise
    except Exception as e:
        logger.error(f"Error parsing .env.example file: {str(e)}")
        raise
    
    return settings

def migrate_settings() -> None:
    """Migrate settings from .env.example to database."""
    try:
        # Load settings from .env.example
        settings = load_env_example()
        
        # Migrate each setting
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create settings table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(255) UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        data_type VARCHAR(50) NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                conn.commit()
                
                for key, value in settings.items():
                    # Determine category and data type
                    category = get_setting_category(key)
                    data_type = get_setting_data_type(value)
                    description = SETTING_DESCRIPTIONS.get(key, f"Setting from .env.example: {key}")
                    
                    # Convert value to string
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    else:
                        value = str(value)
                    
                    # Check if setting exists
                    cur.execute("SELECT id FROM settings WHERE key = %s", (key,))
                    result = cur.fetchone()
                    
                    if result:
                        # Update existing setting
                        cur.execute("""
                            UPDATE settings 
                            SET value = %s, data_type = %s, category = %s, 
                                description = %s, updated_at = NOW() 
                            WHERE key = %s
                        """, (value, data_type, category, description, key))
                        logger.info(f"Updated setting: {key}")
                    else:
                        # Create new setting
                        cur.execute("""
                            INSERT INTO settings 
                            (key, value, data_type, category, description, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                        """, (key, value, data_type, category, description))
                        logger.info(f"Created setting: {key}")
                
                conn.commit()
        
        logger.info("Settings migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during settings migration: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_settings() 