"""
Admin group service for MoonVPN Telegram Bot.

This module provides services for managing admin groups and their members.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_

from app.core.database.models.admin import AdminGroup, AdminGroupMember, AdminGroupType, NotificationLevel
from app.core.exceptions import AdminGroupError
from app.core.schemas.admin_group import (
    AdminGroupCreate,
    AdminGroupUpdate,
    AdminGroupMemberCreate,
    AdminGroupMemberUpdate
)

class AdminGroupService:
    """Service for managing admin groups and their members."""
    
    def __init__(self, db: Session):
        """Initialize the admin group service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_group(self, group_data: AdminGroupCreate) -> AdminGroup:
        """
        Create a new admin group.
        
        Args:
            group_data: AdminGroupCreate schema with group information
            
        Returns:
            Created AdminGroup instance
        """
        group = AdminGroup(**group_data.dict())
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group
    
    def get_group(self, group_id: int) -> Optional[AdminGroup]:
        """
        Get an admin group by ID.
        
        Args:
            group_id: ID of the group to retrieve
            
        Returns:
            AdminGroup instance if found, None otherwise
        """
        return self.db.query(AdminGroup).filter(AdminGroup.id == group_id).first()
    
    def get_group_by_chat_id(self, chat_id: int) -> Optional[AdminGroup]:
        """
        Get an admin group by chat ID.
        
        Args:
            chat_id: Telegram chat ID of the group
            
        Returns:
            AdminGroup instance if found, None otherwise
        """
        return self.db.query(AdminGroup).filter(AdminGroup.chat_id == chat_id).first()
    
    def get_all_groups(self) -> List[AdminGroup]:
        """
        Get all admin groups.
        
        Returns:
            List of all AdminGroup instances
        """
        return self.db.query(AdminGroup).all()
    
    def get_active_groups(self) -> List[AdminGroup]:
        """
        Get all active admin groups.
        
        Returns:
            List of active AdminGroup instances
        """
        return self.db.query(AdminGroup).filter(AdminGroup.is_active == True).all()
    
    def get_groups_by_type(self, group_type: str) -> List[AdminGroup]:
        """
        Get admin groups by type.
        
        Args:
            group_type: Type of groups to retrieve
            
        Returns:
            List of AdminGroup instances of specified type
        """
        return self.db.query(AdminGroup).filter(AdminGroup.type == group_type).all()
    
    def get_groups_by_notification_type(self, notification_type: str) -> List[AdminGroup]:
        """
        Get admin groups that receive specific notification type.
        
        Args:
            notification_type: Type of notification to check for
            
        Returns:
            List of AdminGroup instances that receive the notification type
        """
        return self.db.query(AdminGroup).filter(
            AdminGroup.notification_types.contains([notification_type])
        ).all()
    
    def update_group(self, group_id: int, update_data: AdminGroupUpdate) -> Optional[AdminGroup]:
        """
        Update an admin group.
        
        Args:
            group_id: ID of the group to update
            update_data: AdminGroupUpdate schema with update information
            
        Returns:
            Updated AdminGroup instance if found, None otherwise
        """
        group = self.get_group(group_id)
        if not group:
            return None
        
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(group, field, value)
        
        self.db.commit()
        self.db.refresh(group)
        return group
    
    def delete_group(self, group_id: int) -> bool:
        """
        Delete an admin group.
        
        Args:
            group_id: ID of the group to delete
            
        Returns:
            True if group was deleted, False otherwise
        """
        group = self.get_group(group_id)
        if not group:
            return False
        
        self.db.delete(group)
        self.db.commit()
        return True
    
    def add_member(self, member_data: AdminGroupMemberCreate) -> Optional[AdminGroupMember]:
        """
        Add a member to an admin group.
        
        Args:
            member_data: AdminGroupMemberCreate schema with member information
            
        Returns:
            Created AdminGroupMember instance if successful, None otherwise
        """
        # Check if member already exists
        existing_member = self.get_member(member_data.group_id, member_data.user_id)
        if existing_member:
            return None
        
        member = AdminGroupMember(**member_data.dict())
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def get_member(self, group_id: int, user_id: int) -> Optional[AdminGroupMember]:
        """
        Get a group member by group ID and user ID.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user
            
        Returns:
            AdminGroupMember instance if found, None otherwise
        """
        return self.db.query(AdminGroupMember).filter(
            and_(
                AdminGroupMember.group_id == group_id,
                AdminGroupMember.user_id == user_id
            )
        ).first()
    
    def update_member(self, group_id: int, user_id: int, update_data: AdminGroupMemberUpdate) -> Optional[AdminGroupMember]:
        """
        Update a group member.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user
            update_data: AdminGroupMemberUpdate schema with update information
            
        Returns:
            Updated AdminGroupMember instance if found, None otherwise
        """
        member = self.get_member(group_id, user_id)
        if not member:
            return None
        
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(member, field, value)
        
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def remove_member(self, group_id: int, user_id: int) -> bool:
        """
        Remove a member from an admin group.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user
            
        Returns:
            True if member was removed, False otherwise
        """
        member = self.get_member(group_id, user_id)
        if not member:
            return False
        
        self.db.delete(member)
        self.db.commit()
        return True
    
    def get_group_members(self, group_id: int) -> List[AdminGroupMember]:
        """
        Get all members of an admin group.
        
        Args:
            group_id: ID of the group
            
        Returns:
            List of AdminGroupMember instances
        """
        return self.db.query(AdminGroupMember).filter(
            AdminGroupMember.group_id == group_id
        ).all()
    
    def get_active_members(self, group_id: int) -> List[AdminGroupMember]:
        """
        Get all active members of an admin group.
        
        Args:
            group_id: ID of the group
            
        Returns:
            List of active AdminGroupMember instances
        """
        return self.db.query(AdminGroupMember).filter(
            and_(
                AdminGroupMember.group_id == group_id,
                AdminGroupMember.is_active == True
            )
        ).all()
    
    def is_user_member(self, user_id: int, group_id: int) -> bool:
        """
        Check if a user is a member of an admin group.
        
        Args:
            user_id: ID of the user
            group_id: ID of the group
            
        Returns:
            True if user is a member, False otherwise
        """
        member = self.get_member(group_id, user_id)
        return member is not None and member.is_active
    
    def get_user_groups(self, user_id: int) -> List[AdminGroup]:
        """
        Get all admin groups a user is a member of.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of AdminGroup instances
        """
        return self.db.query(AdminGroup).join(AdminGroupMember).filter(
            and_(
                AdminGroupMember.user_id == user_id,
                AdminGroupMember.is_active == True
            )
        ).all()
    
    def get_user_active_groups(self, user_id: int) -> List[AdminGroup]:
        """
        Get all active admin groups a user is a member of.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of active AdminGroup instances
        """
        return self.db.query(AdminGroup).join(AdminGroupMember).filter(
            and_(
                AdminGroupMember.user_id == user_id,
                AdminGroupMember.is_active == True,
                AdminGroup.is_active == True
            )
        ).all()
    
    def get_user_groups_by_type(self, user_id: int, group_type: str) -> List[AdminGroup]:
        """
        Get admin groups of a specific type that a user is a member of.
        
        Args:
            user_id: ID of the user
            group_type: Type of groups to retrieve
            
        Returns:
            List of AdminGroup instances of specified type
        """
        return self.db.query(AdminGroup).join(AdminGroupMember).filter(
            and_(
                AdminGroupMember.user_id == user_id,
                AdminGroupMember.is_active == True,
                AdminGroup.type == group_type
            )
        ).all() 