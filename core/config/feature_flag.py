"""
MoonVPN Telegram Bot - FeatureFlag Model

This module provides the FeatureFlag class for managing feature flags.
"""

import logging
from typing import Dict, Any, Optional, List

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class FeatureFlag:
    """FeatureFlag model for managing feature flags."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize a feature flag object."""
        self.id = data.get('id')
        self.name = data.get('name')
        self.is_enabled = data.get('is_enabled', False)
        self.description = data.get('description', '')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    @staticmethod
    def get_by_id(feature_id: int) -> Optional['FeatureFlag']:
        """Get a feature flag by ID."""
        try:
            query = "SELECT * FROM feature_flags WHERE id = %s"
            result = execute_query(query, (feature_id,), fetch="one")
            
            if result:
                return FeatureFlag(result)
            return None
        except Exception as e:
            logger.error(f"Error getting feature flag by ID {feature_id}: {e}")
            return None
    
    @staticmethod
    def get_by_name(name: str) -> Optional['FeatureFlag']:
        """Get a feature flag by name."""
        try:
            query = "SELECT * FROM feature_flags WHERE name = %s"
            result = execute_query(query, (name,), fetch="one")
            
            if result:
                return FeatureFlag(result)
            return None
        except Exception as e:
            logger.error(f"Error getting feature flag by name {name}: {e}")
            return None
    
    @staticmethod
    def get_all() -> List['FeatureFlag']:
        """Get all feature flags."""
        try:
            query = "SELECT * FROM feature_flags ORDER BY name"
            results = execute_query(query)
            
            return [FeatureFlag(result) for result in results]
        except Exception as e:
            logger.error(f"Error getting all feature flags: {e}")
            return []
    
    @staticmethod
    def create(name: str, is_enabled: bool = False, description: str = '') -> Optional['FeatureFlag']:
        """Create a new feature flag."""
        try:
            query = """
                INSERT INTO feature_flags (name, is_enabled, description)
                VALUES (%s, %s, %s)
                RETURNING id
            """
            feature_id = execute_insert(query, (name, is_enabled, description))
            
            if feature_id:
                return FeatureFlag.get_by_id(feature_id)
            return None
        except Exception as e:
            logger.error(f"Error creating feature flag {name}: {e}")
            return None
    
    def save(self) -> bool:
        """Save changes to the database."""
        try:
            if not self.id:
                return False
            
            query = """
                UPDATE feature_flags
                SET name = %s, is_enabled = %s, description = %s
                WHERE id = %s
            """
            return execute_update(query, (self.name, self.is_enabled, self.description, self.id))
        except Exception as e:
            logger.error(f"Error saving feature flag {self.name}: {e}")
            return False
    
    def delete(self) -> bool:
        """Delete the feature flag."""
        try:
            if not self.id:
                return False
            
            query = "DELETE FROM feature_flags WHERE id = %s"
            return execute_delete(query, (self.id,))
        except Exception as e:
            logger.error(f"Error deleting feature flag {self.name}: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'is_enabled': self.is_enabled,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 