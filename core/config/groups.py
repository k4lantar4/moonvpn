"""
Management group models for MoonVPN Telegram Bot.

This module defines the models for management groups and their members.
"""

from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from tortoise import fields
from tortoise.models import Model

from core.handlers.bot.admin.constants import NOTIFICATION_TYPES

class BotManagementGroup(Model):
    """
    Model for management groups that receive notifications.
    """
    id = fields.IntField(pk=True)
    chat_id = fields.BigIntField(unique=True, description="Telegram chat ID")
    title = fields.CharField(max_length=255, description="Group title")
    description = fields.TextField(null=True, description="Group description")
    icon = fields.CharField(max_length=10, default="🤖", description="Group icon emoji")
    notification_types = fields.JSONField(default=list, description="Types of notifications this group receives")
    added_by = fields.JSONField(null=True, description="User who added this group")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_active = fields.BooleanField(default=True, description="Whether this group is active")
    
    class Meta:
        table = "management_groups"
    
    def __str__(self) -> str:
        return f"{self.icon} {self.title} ({self.chat_id})"
    
    def get_notification_types_display(self) -> List[str]:
        """Get human-readable notification types."""
        result = []
        if not self.notification_types:
            return result
            
        for n_type in self.notification_types:
            if n_type in NOTIFICATION_TYPES:
                result.append(f"{NOTIFICATION_TYPES[n_type]['icon']} {NOTIFICATION_TYPES[n_type]['name']}")
            else:
                result.append(n_type)
                
        return result

class BotManagementGroupMember(Model):
    """
    Model for members of management groups.
    """
    id = fields.IntField(pk=True)
    group = fields.ForeignKeyField('models.BotManagementGroup', related_name='members')
    user = fields.ForeignKeyField('models.User', related_name='management_groups')
    role = fields.CharField(max_length=50, default="member", description="Role in the group (admin, moderator, member)")
    added_by = fields.JSONField(null=True, description="User who added this member")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_active = fields.BooleanField(default=True, description="Whether this membership is active")
    
    class Meta:
        table = "management_group_members"
        unique_together = (("group", "user"),)
    
    def __str__(self) -> str:
        return f"{self.user} in {self.group} as {self.role}" 