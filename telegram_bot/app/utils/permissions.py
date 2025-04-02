"""
Permissions utilities for checking user roles and permissions.
"""
import logging
from typing import List

from api import api_client
from utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

# Permission constants
ADMIN_PERMISSION = "admin"
PAYMENT_ADMIN_PERMISSION = "payment_admin"
SUPER_ADMIN_PERMISSION = "super_admin"

async def get_user_permissions(user_id: int) -> List[str]:
    """
    Get permissions for a user from the API.
    
    Args:
        user_id: The user ID to check permissions for
        
    Returns:
        List of permission strings
    """
    try:
        permissions = await api_client.get_user_permissions(user_id)
        if permissions is None:
            return []
        return permissions
    except Exception as e:
        logger.error(f"Error getting permissions for user {user_id}: {str(e)}")
        return []

async def is_admin(user_id: int) -> bool:
    """
    Check if a user has admin permissions.
    
    Args:
        user_id: The user ID to check
        
    Returns:
        True if the user is an admin, False otherwise
    """
    permissions = await get_user_permissions(user_id)
    return ADMIN_PERMISSION in permissions or SUPER_ADMIN_PERMISSION in permissions

async def is_payment_admin(user_id: int) -> bool:
    """
    Check if a user has payment admin permissions.
    
    Args:
        user_id: The user ID to check
        
    Returns:
        True if the user is a payment admin, False otherwise
    """
    permissions = await get_user_permissions(user_id)
    return (PAYMENT_ADMIN_PERMISSION in permissions or 
            ADMIN_PERMISSION in permissions or 
            SUPER_ADMIN_PERMISSION in permissions)

async def is_super_admin(user_id: int) -> bool:
    """
    Check if a user has super admin permissions.
    
    Args:
        user_id: The user ID to check
        
    Returns:
        True if the user is a super admin, False otherwise
    """
    permissions = await get_user_permissions(user_id)
    return SUPER_ADMIN_PERMISSION in permissions

def admin_only(func):
    """
    Decorator to restrict handlers to admins only.
    
    Args:
        func: The function to decorate
    
    Returns:
        Decorated function that checks admin permissions
    """
    async def wrapper(update, context):
        user_id = update.effective_user.id
        if not await is_admin(user_id):
            await update.message.reply_text(
                "⛔ شما دسترسی لازم برای استفاده از این قابلیت را ندارید."
            )
            return
        return await func(update, context)
    return wrapper

def payment_admin_only(func):
    """
    Decorator to restrict handlers to payment admins only.
    
    Args:
        func: The function to decorate
    
    Returns:
        Decorated function that checks payment admin permissions
    """
    async def wrapper(update, context):
        user_id = update.effective_user.id
        if not await is_payment_admin(user_id):
            await update.message.reply_text(
                "⛔ شما دسترسی لازم برای استفاده از این قابلیت را ندارید."
            )
            return
        return await func(update, context)
    return wrapper

def super_admin_only(func):
    """
    Decorator to restrict handlers to super admins only.
    
    Args:
        func: The function to decorate
    
    Returns:
        Decorated function that checks super admin permissions
    """
    async def wrapper(update, context):
        user_id = update.effective_user.id
        if not await is_super_admin(user_id):
            await update.message.reply_text(
                "⛔ شما دسترسی لازم برای استفاده از این قابلیت را ندارید."
            )
            return
        return await func(update, context)
    return wrapper 