"""
MoonVPN Telegram Bot - Filter Utilities.

This module provides filter utilities for the MoonVPN Telegram bot.
"""

import logging
from typing import Callable, Any

from telegram import Update
from telegram.ext import ContextTypes

from core.config import get_config_value

# Configure logging
logger = logging.getLogger(__name__)

async def allowed_group_filter(update: Update) -> bool:
    """
    Filter for allowed groups.
    
    Args:
        update: The update to check.
        
    Returns:
        True if the update is from an allowed group or private chat, False otherwise.
    """
    if not update.effective_chat:
        return False
    
    # Always allow private chats
    if update.effective_chat.type == "private":
        return True
    
    # For now, only allow private chats
    return False

async def admin_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Filter for admin users.
    
    Args:
        update: The update to check.
        context: The context object.
        
    Returns:
        True if the user is an admin, False otherwise.
    """
    if not update.effective_user:
        return False
    
    # Get admin IDs from config
    admin_ids = get_config_value("admin_ids", [])
    
    # Check if the user is an admin
    return update.effective_user.id in admin_ids

async def maintenance_mode_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if maintenance mode is enabled.
    
    Args:
        update: The update to check.
        context: The context object.
        
    Returns:
        True if maintenance mode is disabled or the user is an admin, False otherwise.
    """
    # Get maintenance mode status from config
    maintenance_mode = get_config_value("maintenance_mode", False)
    
    # If maintenance mode is disabled, allow all users
    if not maintenance_mode:
        return True
    
    # If maintenance mode is enabled, only allow admin users
    return await admin_filter(update, context) 