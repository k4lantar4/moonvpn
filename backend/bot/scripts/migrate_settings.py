#!/usr/bin/env python3
"""
Script to migrate settings from .env.example to database.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from core.config import Settings
from core.database.models.settings import Setting
from core.database.session import SessionLocal

def load_env_example() -> Dict[str, Any]:
    """Load settings from .env.example file."""
    env_path = Path(__file__).parent.parent.parent.parent / '.env.example'
    settings = {}
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
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
                            pass
                    
                    settings[key] = value
    except FileNotFoundError:
        logging.error(f"Could not find .env.example file at {env_path}")
        raise
    except Exception as e:
        logging.error(f"Error parsing .env.example file: {str(e)}")
        raise
    
    return settings

def migrate_settings() -> None:
    """Migrate settings from .env.example to database."""
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    
    try:
        # Load settings from .env.example
        settings = load_env_example()
        
        # Define categories for settings
        categories = {
            'APP_': 'general',
            'DB_': 'database',
            'REDIS_': 'cache',
            'SECRET_': 'security',
            'JWT_': 'security',
            'CORS_': 'security',
            'PAYMENT_': 'payment',
            'VPN_': 'vpn',
            'BACKUP_': 'backup',
            'ANALYTICS_': 'analytics',
            'NOTIFICATION_': 'notification',
            'CACHE_': 'cache',
            'POINTS_': 'points',
            'LANGUAGE_': 'language',
            'TELEGRAM_': 'telegram',
            'STORAGE_': 'storage'
        }
        
        # Migrate each setting
        for key, value in settings.items():
            # Determine category
            category = 'general'
            for prefix, cat in categories.items():
                if key.startswith(prefix):
                    category = cat
                    break
            
            # Determine data type
            if isinstance(value, bool):
                data_type = 'boolean'
            elif isinstance(value, int):
                data_type = 'integer'
            elif isinstance(value, (list, dict)):
                data_type = 'json'
            else:
                data_type = 'string'
            
            # Create or update setting
            setting = Setting.get_by_key(db, key)
            if setting:
                setting.value = str(value)
                setting.data_type = data_type
                setting.category = category
                db.commit()
                logger.info(f"Updated setting: {key}")
            else:
                Setting.create(
                    db,
                    key=key,
                    value=str(value),
                    data_type=data_type,
                    category=category
                )
                logger.info(f"Created setting: {key}")
        
        logger.info("Settings migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during settings migration: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_settings() 