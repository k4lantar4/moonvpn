"""
MoonVPN Telegram Bot - SystemConfig Model

This module provides the SystemConfig class for managing system configuration.
"""

import logging
from typing import Dict, Any, Optional, List

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class SystemConfig:
    """SystemConfig model for managing system configuration."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize a system config object."""
        self.id = data.get('id')
        self.key = data.get('key')
        self.value = data.get('value')
        self.description = data.get('description', '')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    @staticmethod
    def get_by_id(config_id: int) -> Optional['SystemConfig']:
        """Get a system config by ID."""
        try:
            query = "SELECT * FROM system_configs WHERE id = %s"
            result = execute_query(query, (config_id,), fetch="one")
            
            if result:
                return SystemConfig(result)
            return None
        except Exception as e:
            logger.error(f"Error getting system config by ID {config_id}: {e}")
            return None
    
    @staticmethod
    def get_by_key(key: str) -> Optional['SystemConfig']:
        """Get a system config by key."""
        try:
            query = "SELECT * FROM system_configs WHERE key = %s"
            result = execute_query(query, (key,), fetch="one")
            
            if result:
                return SystemConfig(result)
            return None
        except Exception as e:
            logger.error(f"Error getting system config by key {key}: {e}")
            return None
    
    @staticmethod
    def get_all() -> List['SystemConfig']:
        """Get all system configs."""
        try:
            query = "SELECT * FROM system_configs ORDER BY key"
            results = execute_query(query)
            
            return [SystemConfig(result) for result in results]
        except Exception as e:
            logger.error(f"Error getting all system configs: {e}")
            return []
    
    @staticmethod
    def create(key: str, value: str, description: str = '') -> Optional['SystemConfig']:
        """Create a new system config."""
        try:
            query = """
                INSERT INTO system_configs (key, value, description)
                VALUES (%s, %s, %s)
                RETURNING id
            """
            config_id = execute_insert(query, (key, value, description))
            
            if config_id:
                return SystemConfig.get_by_id(config_id)
            return None
        except Exception as e:
            logger.error(f"Error creating system config {key}: {e}")
            return None
    
    @staticmethod
    def get_value(key: str, default: str = '') -> str:
        """Get a system config value by key."""
        try:
            config = SystemConfig.get_by_key(key)
            if config:
                return config.value
            return default
        except Exception as e:
            logger.error(f"Error getting system config value {key}: {e}")
            return default
    
    @staticmethod
    def set_value(key: str, value: str) -> bool:
        """Set a system config value by key."""
        try:
            config = SystemConfig.get_by_key(key)
            if config:
                config.value = value
                return config.save()
            else:
                return SystemConfig.create(key, value) is not None
        except Exception as e:
            logger.error(f"Error setting system config value {key}: {e}")
            return False
    
    def save(self) -> bool:
        """Save changes to the database."""
        try:
            if not self.id:
                return False
            
            query = """
                UPDATE system_configs
                SET key = %s, value = %s, description = %s
                WHERE id = %s
            """
            return execute_update(query, (self.key, self.value, self.description, self.id))
        except Exception as e:
            logger.error(f"Error saving system config {self.key}: {e}")
            return False
    
    def delete(self) -> bool:
        """Delete the system config."""
        try:
            if not self.id:
                return False
            
            query = "DELETE FROM system_configs WHERE id = %s"
            return execute_delete(query, (self.id,))
        except Exception as e:
            logger.error(f"Error deleting system config {self.key}: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 