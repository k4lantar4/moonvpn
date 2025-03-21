"""
Admin group API endpoints for MoonVPN.

This module provides the API routes for managing admin groups and their members.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database.models.admin import AdminGroupType, NotificationLevel
from app.core.database.session import get_db
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
from app.core.services.admin_group_service import AdminGroupService
from app.core.security import get_current_active_user
from app.core.schemas.user import User

router = APIRouter()

@router.post("/groups", response_model=AdminGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_group(
    group_data: AdminGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new admin group.
    
    Args:
        group_data: AdminGroupCreate schema with group information
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created AdminGroupResponse
        
    Raises:
        HTTPException: If creation fails or validation fails
    """
    service = AdminGroupService(db)
    return service.create_group(group_data)

@router.get("/groups/{group_id}", response_model=AdminGroupResponse)
async def get_admin_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get an admin group by ID.
    
    Args:
        group_id: ID of the group to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupResponse with group information
        
    Raises:
        HTTPException: If group is not found
    """
    service = AdminGroupService(db)
    return service.get_group(group_id)

@router.get("/groups/chat/{chat_id}", response_model=AdminGroupResponse)
async def get_admin_group_by_chat_id(
    chat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get an admin group by chat ID.
    
    Args:
        chat_id: Telegram chat ID of the group
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupResponse with group information
        
    Raises:
        HTTPException: If group is not found
    """
    service = AdminGroupService(db)
    return service.get_group_by_chat_id(chat_id)

@router.get("/groups", response_model=AdminGroupListResponse)
async def list_admin_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all admin groups with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupListResponse with list of groups
    """
    service = AdminGroupService(db)
    return service.get_all_groups(skip, limit)

@router.get("/groups/active", response_model=AdminGroupListResponse)
async def list_active_admin_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all active admin groups with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupListResponse with list of active groups
    """
    service = AdminGroupService(db)
    return service.get_active_groups(skip, limit)

@router.get("/groups/type/{group_type}", response_model=AdminGroupListResponse)
async def list_admin_groups_by_type(
    group_type: AdminGroupType,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List admin groups by type with pagination.
    
    Args:
        group_type: Type of groups to retrieve
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupListResponse with list of groups of specified type
    """
    service = AdminGroupService(db)
    return service.get_groups_by_type(group_type, skip, limit)

@router.get("/groups/notification/{notification_type}", response_model=AdminGroupListResponse)
async def list_admin_groups_by_notification_type(
    notification_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List admin groups that receive specific notification type with pagination.
    
    Args:
        notification_type: Type of notification to check for
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupListResponse with list of groups that receive the notification type
    """
    service = AdminGroupService(db)
    return service.get_groups_by_notification_type(notification_type, skip, limit)

@router.put("/groups/{group_id}", response_model=AdminGroupResponse)
async def update_admin_group(
    group_id: int,
    update_data: AdminGroupUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an admin group.
    
    Args:
        group_id: ID of the group to update
        update_data: AdminGroupUpdate schema with update information
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated AdminGroupResponse
        
    Raises:
        HTTPException: If group is not found or update fails
    """
    service = AdminGroupService(db)
    return service.update_group(group_id, update_data)

@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an admin group.
    
    Args:
        group_id: ID of the group to delete
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If group is not found or deletion fails
    """
    service = AdminGroupService(db)
    service.delete_group(group_id)
    return None

@router.post("/groups/{group_id}/members", response_model=AdminGroupMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_group_member(
    group_id: int,
    member_data: AdminGroupMemberCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a member to an admin group.
    
    Args:
        group_id: ID of the group
        member_data: AdminGroupMemberCreate schema with member information
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created AdminGroupMemberResponse
        
    Raises:
        HTTPException: If member addition fails or validation fails
    """
    service = AdminGroupService(db)
    return service.add_member(member_data)

@router.get("/groups/{group_id}/members/{user_id}", response_model=AdminGroupMemberResponse)
async def get_group_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a group member by group ID and user ID.
    
    Args:
        group_id: ID of the group
        user_id: ID of the user
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupMemberResponse with member information
        
    Raises:
        HTTPException: If member is not found
    """
    service = AdminGroupService(db)
    return service.get_member(group_id, user_id)

@router.put("/groups/{group_id}/members/{user_id}", response_model=AdminGroupMemberResponse)
async def update_group_member(
    group_id: int,
    user_id: int,
    update_data: AdminGroupMemberUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a group member.
    
    Args:
        group_id: ID of the group
        user_id: ID of the user
        update_data: AdminGroupMemberUpdate schema with update information
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated AdminGroupMemberResponse
        
    Raises:
        HTTPException: If member is not found or update fails
    """
    service = AdminGroupService(db)
    return service.update_member(group_id, user_id, update_data)

@router.delete("/groups/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove a member from an admin group.
    
    Args:
        group_id: ID of the group
        user_id: ID of the user
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If member is not found or removal fails
    """
    service = AdminGroupService(db)
    service.remove_member(group_id, user_id)
    return None

@router.get("/groups/{group_id}/members", response_model=AdminGroupMemberListResponse)
async def list_group_members(
    group_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all members of an admin group with pagination.
    
    Args:
        group_id: ID of the group
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupMemberListResponse with list of members
        
    Raises:
        HTTPException: If group is not found
    """
    service = AdminGroupService(db)
    return service.get_group_members(group_id, skip, limit)

@router.get("/groups/{group_id}/members/active", response_model=AdminGroupMemberListResponse)
async def list_active_group_members(
    group_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all active members of an admin group with pagination.
    
    Args:
        group_id: ID of the group
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupMemberListResponse with list of active members
        
    Raises:
        HTTPException: If group is not found
    """
    service = AdminGroupService(db)
    return service.get_active_members(group_id, skip, limit)

@router.get("/users/{user_id}/groups", response_model=AdminGroupListResponse)
async def list_user_groups(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all admin groups a user is a member of with pagination.
    
    Args:
        user_id: ID of the user
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupListResponse with list of groups
    """
    service = AdminGroupService(db)
    return service.get_user_groups(user_id, skip, limit)

@router.get("/users/{user_id}/groups/active", response_model=AdminGroupListResponse)
async def list_user_active_groups(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all active admin groups a user is a member of with pagination.
    
    Args:
        user_id: ID of the user
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupListResponse with list of active groups
    """
    service = AdminGroupService(db)
    return service.get_user_active_groups(user_id, skip, limit)

@router.get("/users/{user_id}/groups/type/{group_type}", response_model=AdminGroupListResponse)
async def list_user_groups_by_type(
    user_id: int,
    group_type: AdminGroupType,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List admin groups of a specific type that a user is a member of with pagination.
    
    Args:
        user_id: ID of the user
        group_type: Type of groups to retrieve
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AdminGroupListResponse with list of groups of specified type
    """
    service = AdminGroupService(db)
    return service.get_user_groups_by_type(user_id, group_type, skip, limit) 