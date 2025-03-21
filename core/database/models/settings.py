"""
MoonVPN Telegram Bot - Settings Model

This module provides the Setting model for managing system configurations.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class Setting:
    """Settings model for managing system configurations."""
    
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
    
    def __init__(self, setting_data: Dict[str, Any]):
        """
        Initialize a setting object.
        
        Args:
            setting_data (Dict[str, Any]): Setting data from database
        """
        self.id = setting_data.get('id')
        self.key = setting_data.get('key')
        self.value = setting_data.get('value')
        self.data_type = setting_data.get('data_type', self.TYPE_STRING)
        self.category = setting_data.get('category', self.CATEGORY_GENERAL)
        self.description = setting_data.get('description')
        self.is_public = setting_data.get('is_public', False)
        self.created_at = setting_data.get('created_at')
        self.updated_at = setting_data.get('updated_at')
        self.updated_by = setting_data.get('updated_by')
        
        # Additional data from joins
        self.admin_username = setting_data.get('admin_username')
        
    @staticmethod
    def get_by_id(setting_id: int) -> Optional['Setting']:
        """
        Get a setting by ID.
        
        Args:
            setting_id (int): Setting ID
            
        Returns:
            Optional[Setting]: Setting object or None if not found
        """
        query = """
            SELECT s.*, u.username as admin_username
            FROM settings s
            LEFT JOIN users u ON s.updated_by = u.id
            WHERE s.id = %s
        """
        result = execute_query(query, (setting_id,), fetch="one")
        
        if result:
            return Setting(result)
            
        return None
        
    @staticmethod
    def get_by_key(key: str, typed: bool = True) -> Any:
        """
        Get a setting value by key.
        
        Args:
            key (str): Setting key
            typed (bool, optional): Whether to return the value with the correct type. Defaults to True.
            
        Returns:
            Any: Setting value or None if not found
        """
        # Try to get from cache first
        cached_setting = cache_get(f"setting:{key}")
        if cached_setting:
            if typed:
                return Setting._convert_value(cached_setting.get('value'), cached_setting.get('data_type'))
            return cached_setting.get('value')
        
        # Get from database
        query = "SELECT * FROM settings WHERE key = %s"
        result = execute_query(query, (key,), fetch="one")
        
        if result:
            # Cache setting data
            cache_set(f"setting:{key}", dict(result), 3600)  # Cache for 1 hour
            
            if typed:
                return Setting._convert_value(result.get('value'), result.get('data_type'))
            return result.get('value')
            
        return None
        
    @staticmethod
    def get_by_category(category: str) -> List['Setting']:
        """
        Get settings by category.
        
        Args:
            category (str): Setting category
            
        Returns:
            List[Setting]: List of setting objects
        """
        query = """
            SELECT s.*, u.username as admin_username
            FROM settings s
            LEFT JOIN users u ON s.updated_by = u.id
            WHERE s.category = %s
            ORDER BY s.key
        """
        results = execute_query(query, (category,))
        
        return [Setting(result) for result in results]
        
    @staticmethod
    def get_all() -> List['Setting']:
        """
        Get all settings.
        
        Returns:
            List[Setting]: List of setting objects
        """
        query = """
            SELECT s.*, u.username as admin_username
            FROM settings s
            LEFT JOIN users u ON s.updated_by = u.id
            ORDER BY s.category, s.key
        """
        results = execute_query(query)
        
        return [Setting(result) for result in results]
        
    @staticmethod
    def get_public() -> List['Setting']:
        """
        Get all public settings.
        
        Returns:
            List[Setting]: List of public setting objects
        """
        query = """
            SELECT s.*, u.username as admin_username
            FROM settings s
            LEFT JOIN users u ON s.updated_by = u.id
            WHERE s.is_public = TRUE
            ORDER BY s.category, s.key
        """
        results = execute_query(query)
        
        return [Setting(result) for result in results]
        
    @staticmethod
    def create(key: str, value: Any, data_type: str = TYPE_STRING, 
              category: str = CATEGORY_GENERAL, description: str = '',
              is_public: bool = False, updated_by: Optional[int] = None) -> Optional['Setting']:
        """
        Create a new setting.
        
        Args:
            key (str): Setting key
            value (Any): Setting value
            data_type (str, optional): Data type. Defaults to TYPE_STRING.
            category (str, optional): Category. Defaults to CATEGORY_GENERAL.
            description (str, optional): Description. Defaults to ''.
            is_public (bool, optional): Public status. Defaults to False.
            updated_by (Optional[int], optional): Admin user ID. Defaults to None.
            
        Returns:
            Optional[Setting]: Setting object or None if creation failed
        """
        # Check if key already exists
        existing = Setting.get_by_key(key, typed=False)
        if existing is not None:
            logger.error(f"Setting key '{key}' already exists")
            return None
            
        # Insert into database
        query = """
            INSERT INTO settings (
                key, value, data_type, category, description, is_public, updated_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        # Convert value to string based on data_type
        value_str = Setting._value_to_string(value, data_type)
        
        setting_id = execute_insert(query, (
            key, value_str, data_type, category, description, is_public, updated_by
        ))
        
        if setting_id:
            # Clear cache
            cache_delete(f"setting:{key}")
            
            # Return the created setting
            return Setting.get_by_id(setting_id)
            
        return None
        
    @staticmethod
    def set(key: str, value: Any, updated_by: Optional[int] = None) -> bool:
        """
        Set a setting value. Creates the setting if it doesn't exist.
        
        Args:
            key (str): Setting key
            value (Any): Setting value
            updated_by (Optional[int], optional): Admin user ID. Defaults to None.
            
        Returns:
            bool: True if setting was updated or created, False otherwise
        """
        query = "SELECT * FROM settings WHERE key = %s"
        result = execute_query(query, (key,), fetch="one")
        
        if result:
            # Existing setting
            setting = Setting(result)
            setting.value = value
            setting.updated_by = updated_by
            return setting.save()
        else:
            # New setting
            data_type = Setting._get_type(value)
            setting = Setting.create(key, value, data_type, updated_by=updated_by)
            return setting is not None
        
    def save(self) -> bool:
        """
        Save setting changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
            
        query = """
            UPDATE settings SET
                key = %s,
                value = %s,
                data_type = %s,
                category = %s,
                description = %s,
                is_public = %s,
                updated_by = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        # Convert value to string based on data_type
        value_str = Setting._value_to_string(self.value, self.data_type)
        
        success = execute_update(query, (
            self.key,
            value_str,
            self.data_type,
            self.category,
            self.description,
            self.is_public,
            self.updated_by,
            self.id
        ))
        
        if success:
            # Clear cache
            cache_delete(f"setting:{self.key}")
            
        return success
        
    def delete(self) -> bool:
        """
        Delete setting from database.
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Delete from database
        query = "DELETE FROM settings WHERE id = %s"
        success = execute_delete(query, (self.id,))
        
        if success:
            # Clear cache
            cache_delete(f"setting:{self.key}")
            
        return success
        
    def get_typed_value(self) -> Any:
        """
        Get the value with the correct type.
        
        Returns:
            Any: Setting value with the correct type
        """
        return Setting._convert_value(self.value, self.data_type)
        
    @staticmethod
    def _convert_value(value: Any, data_type: str) -> Any:
        """
        Convert a value to the correct type.
        
        Args:
            value (Any): Value to convert
            data_type (str): Data type
            
        Returns:
            Any: Converted value
        """
        if value is None:
            return None
            
        try:
            if data_type == Setting.TYPE_STRING:
                return str(value)
            elif data_type == Setting.TYPE_INTEGER:
                return int(value)
            elif data_type == Setting.TYPE_FLOAT:
                return float(value)
            elif data_type == Setting.TYPE_BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', 'yes', '1', 'y')
                return bool(value)
            elif data_type == Setting.TYPE_JSON:
                if isinstance(value, str):
                    return json.loads(value)
                return value
            elif data_type == Setting.TYPE_DATETIME:
                if isinstance(value, str):
                    return datetime.fromisoformat(value)
                return value
        except Exception as e:
            logger.error(f"Error converting value '{value}' to type '{data_type}': {e}")
            
        return value
        
    @staticmethod
    def _value_to_string(value: Any, data_type: str) -> str:
        """
        Convert a value to a string based on data type.
        
        Args:
            value (Any): Value to convert
            data_type (str): Data type
            
        Returns:
            str: Value as string
        """
        if value is None:
            return None
            
        try:
            if data_type == Setting.TYPE_JSON:
                if not isinstance(value, str):
                    return json.dumps(value)
            elif data_type == Setting.TYPE_DATETIME:
                if isinstance(value, datetime):
                    return value.isoformat()
            elif data_type == Setting.TYPE_BOOLEAN:
                return '1' if value else '0'
        except Exception as e:
            logger.error(f"Error converting value '{value}' to string for type '{data_type}': {e}")
            
        return str(value)
        
    @staticmethod
    def _get_type(value: Any) -> str:
        """
        Get the data type of a value.
        
        Args:
            value (Any): Value to get type for
            
        Returns:
            str: Data type
        """
        if isinstance(value, bool):
            return Setting.TYPE_BOOLEAN
        elif isinstance(value, int):
            return Setting.TYPE_INTEGER
        elif isinstance(value, float):
            return Setting.TYPE_FLOAT
        elif isinstance(value, dict) or isinstance(value, list):
            return Setting.TYPE_JSON
        elif isinstance(value, datetime):
            return Setting.TYPE_DATETIME
        else:
            return Setting.TYPE_STRING
        
    def get_updater(self):
        """
        Get the admin who updated this setting.
        
        Returns:
            Optional[User]: Admin user object or None if not found
        """
        if not self.updated_by:
            return None
            
        from models.user import User
        return User.get_by_id(self.updated_by)
        
    @staticmethod
    def get_app_name() -> str:
        """
        Get the application name.
        
        Returns:
            str: Application name
        """
        return Setting.get_by_key('app_name') or 'MoonVPN'
        
    @staticmethod
    def get_default_language() -> str:
        """
        Get the default language.
        
        Returns:
            str: Default language code
        """
        return Setting.get_by_key('default_language') or 'fa'
        
    @staticmethod
    def get_payment_methods() -> List[str]:
        """
        Get enabled payment methods.
        
        Returns:
            List[str]: List of enabled payment methods
        """
        methods = Setting.get_by_key('payment_methods')
        if methods:
            if isinstance(methods, str):
                return methods.split(',')
            if isinstance(methods, list):
                return methods
        return ['card']
        
    @staticmethod
    def get_referral_reward_amount() -> float:
        """
        Get referral reward amount.
        
        Returns:
            float: Referral reward amount
        """
        return float(Setting.get_by_key('referral_reward_amount') or 0)
        
    @staticmethod
    def is_feature_enabled(feature: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature (str): Feature name
            
        Returns:
            bool: True if feature is enabled, False otherwise
        """
        enabled_features = Setting.get_by_key('enabled_features')
        if enabled_features:
            if isinstance(enabled_features, str):
                return feature in enabled_features.split(',')
            if isinstance(enabled_features, list):
                return feature in enabled_features
        return False
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert setting to dictionary.
        
        Returns:
            Dict[str, Any]: Setting data as dictionary
        """
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_typed_value(),
            'data_type': self.data_type,
            'category': self.category,
            'description': self.description,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by,
            'admin_username': self.admin_username
        } 