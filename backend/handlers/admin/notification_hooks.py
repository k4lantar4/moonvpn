"""
Notification hooks for important system events.

This module contains hook functions that are called from various parts of the system
to send notifications to the appropriate management groups.
"""

import logging
from typing import Dict, Any, Optional

from telegram import Bot
from .notification_groups import (
    notify_user_registration,
    notify_payment_new,
    notify_payment_processed,
    notify_server_status,
    notify_account_created,
    notify_system_error,
    notify_backup_completed,
    notify_high_system_load,
    notify_seller_activity
)

# Logger
logger = logging.getLogger(__name__)

async def hook_user_registration(bot: Bot, user_data: Dict[str, Any]) -> bool:
    """
    Hook for sending notification when a new user registers.
    
    Args:
        bot: The bot instance
        user_data: Dict with user details
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        return await notify_user_registration(bot, user_data)
    except Exception as e:
        logger.error(f"Failed to send user registration notification: {str(e)}")
        return False

async def hook_payment_received(bot: Bot, payment_data: Dict[str, Any]) -> bool:
    """
    Hook for sending notification when a new payment is received.
    
    Args:
        bot: The bot instance
        payment_data: Dict with payment details
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        return await notify_payment_new(bot, payment_data)
    except Exception as e:
        logger.error(f"Failed to send payment received notification: {str(e)}")
        return False

async def hook_payment_processed(bot: Bot, payment_data: Dict[str, Any], approved: bool) -> bool:
    """
    Hook for sending notification when a payment is processed (approved/rejected).
    
    Args:
        bot: The bot instance
        payment_data: Dict with payment details
        approved: Whether the payment was approved or rejected
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        return await notify_payment_processed(bot, payment_data, approved)
    except Exception as e:
        logger.error(f"Failed to send payment processed notification: {str(e)}")
        return False

async def hook_server_status_change(bot: Bot, server_data: Dict[str, Any], is_online: bool) -> bool:
    """
    Hook for sending notification when a server status changes.
    
    Args:
        bot: The bot instance
        server_data: Dict with server details
        is_online: Whether the server is now online or offline
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        return await notify_server_status(bot, server_data, is_online)
    except Exception as e:
        logger.error(f"Failed to send server status notification: {str(e)}")
        return False

async def hook_account_created(bot: Bot, account_data: Dict[str, Any]) -> bool:
    """
    Hook for sending notification when a new VPN account is created.
    
    Args:
        bot: The bot instance
        account_data: Dict with account details
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        return await notify_account_created(bot, account_data)
    except Exception as e:
        logger.error(f"Failed to send account created notification: {str(e)}")
        return False

async def hook_system_error(bot: Bot, error_data: Dict[str, Any]) -> bool:
    """
    Hook for sending notification when a serious system error occurs.
    
    Args:
        bot: The bot instance
        error_data: Dict with error details
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        return await notify_system_error(bot, error_data)
    except Exception as e:
        logger.error(f"Failed to send system error notification: {str(e)}")
        return False

async def hook_backup_completed(bot: Bot, backup_data: Dict[str, Any]) -> bool:
    """
    Hook for sending notification when a system backup is completed.
    
    Args:
        bot: The bot instance
        backup_data: Dict with backup details
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        return await notify_backup_completed(bot, backup_data)
    except Exception as e:
        logger.error(f"Failed to send backup completed notification: {str(e)}")
        return False

async def hook_high_system_load(bot: Bot, system_data: Dict[str, Any]) -> bool:
    """
    Hook for sending notification when system load is high.
    
    Args:
        bot: The bot instance
        system_data: Dict with system load details
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        return await notify_high_system_load(bot, system_data)
    except Exception as e:
        logger.error(f"Failed to send high system load notification: {str(e)}")
        return False

async def hook_seller_activity(bot: Bot, seller_data: Dict[str, Any]) -> bool:
    """
    Hook for sending notification when there's seller activity.
    
    Args:
        bot: The bot instance
        seller_data: Dict with seller activity details
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        return await notify_seller_activity(bot, seller_data)
    except Exception as e:
        logger.error(f"Failed to send seller activity notification: {str(e)}")
        return False 