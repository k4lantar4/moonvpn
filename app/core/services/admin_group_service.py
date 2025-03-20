"""
Admin group service for MoonVPN.

This module provides the business logic layer for managing admin groups and their members.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.database.models.admin import AdminGroup, AdminGroupMember, AdminGroupType, NotificationLevel
from app.core.repositories.admin_group_repository import AdminGroupRepository
from app.core.schemas.admin_group import (
    AdminGroupCreate,
    AdminGroupUpdate,
    AdminGroupMemberCreate,
    AdminGroupMemberUpdate,
    AdminGroupResponse,
    AdminGroupMemberResponse,
    AdminGroupListResponse,
    AdminGroupMemberListResponse
)

class AdminGroupService:
    """Service for managing admin groups and their members."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AdminGroupRepository(db)
    
    # Group Operations
    
    def create_group(self, group_data: AdminGroupCreate) -> AdminGroupResponse:
        """
        Create a new admin group.
        
        Args:
            group_data: AdminGroupCreate schema with group information
            
        Returns:
            AdminGroupResponse with created group information
            
        Raises:
            HTTPException: If group creation fails or validation fails
        """
        # Validate group name uniqueness
        existing_group = self.repository.get_group_by_chat_id(group_data.chat_id)
        if existing_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A group with this chat ID already exists"
            )
        
        # Create group
        group = self.repository.create_group(group_data)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create admin group"
            )
        
        return AdminGroupResponse.from_orm(group)
    
    def get_group(self, group_id: int) -> AdminGroupResponse:
        """
        Get an admin group by ID.
        
        Args:
            group_id: ID of the group to retrieve
            
        Returns:
            AdminGroupResponse with group information
            
        Raises:
            HTTPException: If group is not found
        """
        group = self.repository.get_group(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin group not found"
            )
        
        return AdminGroupResponse.from_orm(group)
    
    def get_group_by_chat_id(self, chat_id: int) -> AdminGroupResponse:
        """
        Get an admin group by chat ID.
        
        Args:
            chat_id: Telegram chat ID of the group
            
        Returns:
            AdminGroupResponse with group information
            
        Raises:
            HTTPException: If group is not found
        """
        group = self.repository.get_group_by_chat_id(chat_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin group not found"
            )
        
        return AdminGroupResponse.from_orm(group)
    
    def get_all_groups(self, skip: int = 0, limit: int = 100) -> AdminGroupListResponse:
        """
        Get all admin groups with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            AdminGroupListResponse with list of groups
        """
        groups = self.repository.get_all_groups(skip, limit)
        return AdminGroupListResponse(
            groups=[AdminGroupResponse.from_orm(group) for group in groups],
            total=len(groups),
            skip=skip,
            limit=limit
        )
    
    def get_active_groups(self, skip: int = 0, limit: int = 100) -> AdminGroupListResponse:
        """
        Get all active admin groups with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            AdminGroupListResponse with list of active groups
        """
        groups = self.repository.get_active_groups(skip, limit)
        return AdminGroupListResponse(
            groups=[AdminGroupResponse.from_orm(group) for group in groups],
            total=len(groups),
            skip=skip,
            limit=limit
        )
    
    def get_groups_by_type(self, group_type: AdminGroupType, skip: int = 0, limit: int = 100) -> AdminGroupListResponse:
        """
        Get admin groups by type with pagination.
        
        Args:
            group_type: Type of groups to retrieve
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            AdminGroupListResponse with list of groups of specified type
        """
        groups = self.repository.get_groups_by_type(group_type, skip, limit)
        return AdminGroupListResponse(
            groups=[AdminGroupResponse.from_orm(group) for group in groups],
            total=len(groups),
            skip=skip,
            limit=limit
        )
    
    def get_groups_by_notification_type(self, notification_type: str, skip: int = 0, limit: int = 100) -> AdminGroupListResponse:
        """
        Get admin groups that receive specific notification type with pagination.
        
        Args:
            notification_type: Type of notification to check for
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            AdminGroupListResponse with list of groups that receive the notification type
        """
        groups = self.repository.get_groups_by_notification_type(notification_type, skip, limit)
        return AdminGroupListResponse(
            groups=[AdminGroupResponse.from_orm(group) for group in groups],
            total=len(groups),
            skip=skip,
            limit=limit
        )
    
    def update_group(self, group_id: int, update_data: AdminGroupUpdate) -> AdminGroupResponse:
        """
        Update an admin group.
        
        Args:
            group_id: ID of the group to update
            update_data: AdminGroupUpdate schema with update information
            
        Returns:
            AdminGroupResponse with updated group information
            
        Raises:
            HTTPException: If group is not found or update fails
        """
        # Check if group exists
        group = self.repository.get_group(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin group not found"
            )
        
        # Validate chat_id uniqueness if being updated
        if update_data.chat_id and update_data.chat_id != group.chat_id:
            existing_group = self.repository.get_group_by_chat_id(update_data.chat_id)
            if existing_group:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A group with this chat ID already exists"
                )
        
        # Update group
        updated_group = self.repository.update_group(group_id, update_data)
        if not updated_group:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update admin group"
            )
        
        return AdminGroupResponse.from_orm(updated_group)
    
    def delete_group(self, group_id: int) -> bool:
        """
        Delete an admin group.
        
        Args:
            group_id: ID of the group to delete
            
        Returns:
            True if group was deleted, False otherwise
            
        Raises:
            HTTPException: If group is not found or deletion fails
        """
        # Check if group exists
        group = self.repository.get_group(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin group not found"
            )
        
        # Delete group
        if not self.repository.delete_group(group_id):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete admin group"
            )
        
        return True
    
    # Member Operations
    
    def add_member(self, member_data: AdminGroupMemberCreate) -> AdminGroupMemberResponse:
        """
        Add a member to an admin group.
        
        Args:
            member_data: AdminGroupMemberCreate schema with member information
            
        Returns:
            AdminGroupMemberResponse with created member information
            
        Raises:
            HTTPException: If member addition fails or validation fails
        """
        # Validate group exists and is active
        group = self.repository.get_group(member_data.group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin group not found"
            )
        if not group.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add member to inactive group"
            )
        
        # Add member
        member = self.repository.add_member(member_data)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Member already exists in this group"
            )
        
        return AdminGroupMemberResponse.from_orm(member)
    
    def get_member(self, group_id: int, user_id: int) -> AdminGroupMemberResponse:
        """
        Get a group member by group ID and user ID.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user
            
        Returns:
            AdminGroupMemberResponse with member information
            
        Raises:
            HTTPException: If member is not found
        """
        member = self.repository.get_member(group_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group member not found"
            )
        
        return AdminGroupMemberResponse.from_orm(member)
    
    def update_member(self, group_id: int, user_id: int, update_data: AdminGroupMemberUpdate) -> AdminGroupMemberResponse:
        """
        Update a group member.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user
            update_data: AdminGroupMemberUpdate schema with update information
            
        Returns:
            AdminGroupMemberResponse with updated member information
            
        Raises:
            HTTPException: If member is not found or update fails
        """
        # Check if member exists
        member = self.repository.get_member(group_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group member not found"
            )
        
        # Update member
        updated_member = self.repository.update_member(group_id, user_id, update_data)
        if not updated_member:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update group member"
            )
        
        return AdminGroupMemberResponse.from_orm(updated_member)
    
    def remove_member(self, group_id: int, user_id: int) -> bool:
        """
        Remove a member from an admin group.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user
            
        Returns:
            True if member was removed, False otherwise
            
        Raises:
            HTTPException: If member is not found or removal fails
        """
        # Check if member exists
        member = self.repository.get_member(group_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group member not found"
            )
        
        # Remove member
        if not self.repository.remove_member(group_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove group member"
            )
        
        return True
    
    def get_group_members(self, group_id: int, skip: int = 0, limit: int = 100) -> AdminGroupMemberListResponse:
        """
        Get all members of an admin group with pagination.
        
        Args:
            group_id: ID of the group
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            AdminGroupMemberListResponse with list of members
            
        Raises:
            HTTPException: If group is not found
        """
        # Check if group exists
        group = self.repository.get_group(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin group not found"
            )
        
        members = self.repository.get_group_members(group_id, skip, limit)
        return AdminGroupMemberListResponse(
            members=[AdminGroupMemberResponse.from_orm(member) for member in members],
            total=len(members),
            skip=skip,
            limit=limit
        )
    
    def get_active_members(self, group_id: int, skip: int = 0, limit: int = 100) -> AdminGroupMemberListResponse:
        """
        Get all active members of an admin group with pagination.
        
        Args:
            group_id: ID of the group
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            AdminGroupMemberListResponse with list of active members
            
        Raises:
            HTTPException: If group is not found
        """
        # Check if group exists
        group = self.repository.get_group(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin group not found"
            )
        
        members = self.repository.get_active_members(group_id, skip, limit)
        return AdminGroupMemberListResponse(
            members=[AdminGroupMemberResponse.from_orm(member) for member in members],
            total=len(members),
            skip=skip,
            limit=limit
        )
    
    def is_user_member(self, user_id: int, group_id: int) -> bool:
        """
        Check if a user is a member of an admin group.
        
        Args:
            user_id: ID of the user
            group_id: ID of the group
            
        Returns:
            True if user is a member, False otherwise
        """
        return self.repository.is_user_member(user_id, group_id)
    
    def get_user_groups(self, user_id: int, skip: int = 0, limit: int = 100) -> AdminGroupListResponse:
        """
        Get all admin groups a user is a member of with pagination.
        
        Args:
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            AdminGroupListResponse with list of groups
        """
        groups = self.repository.get_user_groups(user_id, skip, limit)
        return AdminGroupListResponse(
            groups=[AdminGroupResponse.from_orm(group) for group in groups],
            total=len(groups),
            skip=skip,
            limit=limit
        )
    
    def get_user_active_groups(self, user_id: int, skip: int = 0, limit: int = 100) -> AdminGroupListResponse:
        """
        Get all active admin groups a user is a member of with pagination.
        
        Args:
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            AdminGroupListResponse with list of active groups
        """
        groups = self.repository.get_user_active_groups(user_id, skip, limit)
        return AdminGroupListResponse(
            groups=[AdminGroupResponse.from_orm(group) for group in groups],
            total=len(groups),
            skip=skip,
            limit=limit
        )
    
    def get_user_groups_by_type(self, user_id: int, group_type: AdminGroupType, skip: int = 0, limit: int = 100) -> AdminGroupListResponse:
        """
        Get admin groups of a specific type that a user is a member of with pagination.
        
        Args:
            user_id: ID of the user
            group_type: Type of groups to retrieve
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            AdminGroupListResponse with list of groups of specified type
        """
        groups = self.repository.get_user_groups_by_type(user_id, group_type, skip, limit)
        return AdminGroupListResponse(
            groups=[AdminGroupResponse.from_orm(group) for group in groups],
            total=len(groups),
            skip=skip,
            limit=limit
        ) 