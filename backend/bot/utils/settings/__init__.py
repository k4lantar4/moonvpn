"""
Settings utility module for MoonVPN

This module provides functions for managing system settings
stored in the database for configuration.
"""

import logging
import json
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Define a model for settings if it doesn't already exist
try:
    from django.db import models
    from django.core.serializers.json import DjangoJSONEncoder
    
    class SystemSetting(models.Model):
        """Model for storing system settings"""
        key = models.CharField(max_length=100, unique=True)
        value = models.TextField(null=True, blank=True)
        description = models.TextField(blank=True)
        is_json = models.BooleanField(default=False)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        class Meta:
            verbose_name = 'System Setting'
            verbose_name_plural = 'System Settings'
            ordering = ['key']
            
        def __str__(self):
            return self.key
            
        def get_value(self):
            """Get the value, deserializing JSON if needed"""
            if not self.value:
                return None
                
            if self.is_json:
                try:
                    return json.loads(self.value)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON for setting {self.key}")
                    return None
            return self.value
            
        def set_value(self, value):
            """Set the value, serializing to JSON if needed"""
            if isinstance(value, (dict, list)):
                self.is_json = True
                self.value = json.dumps(value, cls=DjangoJSONEncoder)
            else:
                self.is_json = False
                self.value = str(value) if value is not None else None
except ImportError:
    logger.warning("Django models could not be imported in settings module")
    
def get_system_setting(key: str, default: Any = None) -> Any:
    """
    Get a system setting value
    
    Args:
        key: Setting key
        default: Default value if setting doesn't exist
        
    Returns:
        Any: The setting value, or default if not found
    """
    try:
        from django.apps import apps
        
        # Check if Django is setup
        if not apps.ready:
            logger.warning("Django apps not ready, returning default value")
            return default
            
        # Get SystemSetting model
        SystemSetting = apps.get_model('utils.SystemSetting')
        
        try:
            setting = SystemSetting.objects.get(key=key)
            return setting.get_value()
        except SystemSetting.DoesNotExist:
            return default
        except Exception as e:
            logger.error(f"Error retrieving setting {key}: {str(e)}")
            return default
    except Exception as e:
        logger.error(f"Error in get_system_setting: {str(e)}")
        return default
    
def update_system_setting(key: str, value: Any, description: str = '') -> bool:
    """
    Update or create a system setting
    
    Args:
        key: Setting key
        value: Setting value
        description: Optional description
        
    Returns:
        bool: True if the setting was updated successfully, False otherwise
    """
    try:
        from django.apps import apps
        
        # Check if Django is setup
        if not apps.ready:
            logger.warning("Django apps not ready, cannot update setting")
            return False
            
        # Get SystemSetting model
        SystemSetting = apps.get_model('utils.SystemSetting')
        
        # Get or create the setting
        setting, created = SystemSetting.objects.get_or_create(key=key)
        
        # Update description if provided and setting is new
        if description and created:
            setting.description = description
            
        # Set the value
        setting.set_value(value)
        setting.save()
        
        return True
    except Exception as e:
        logger.error(f"Error updating setting {key}: {str(e)}")
        return False
        
def get_all_settings() -> Dict[str, Any]:
    """
    Get all system settings as a dictionary
    
    Returns:
        Dict: Dictionary of all settings
    """
    try:
        from django.apps import apps
        
        # Check if Django is setup
        if not apps.ready:
            logger.warning("Django apps not ready, returning empty settings")
            return {}
            
        # Get SystemSetting model
        SystemSetting = apps.get_model('utils.SystemSetting')
        
        settings = {}
        for setting in SystemSetting.objects.all():
            settings[setting.key] = setting.get_value()
            
        return settings
    except Exception as e:
        logger.error(f"Error getting all settings: {str(e)}")
        return {} 