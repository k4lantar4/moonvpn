"""
Decorators for the Telegram bot.

This module provides decorators for common bot functionality.
"""

import logging
import functools
import os
from typing import Callable, Any, Optional, List

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from django.conf import settings

from core.database import get_user
from core.utils.i18n import get_text
from core.utils.helpers import get_user

logger = logging.getLogger(__name__)

# Get admin user IDs from environment variable
ADMIN_USER_IDS = os.getenv("ADMIN_USER_IDS", "[]")
try:
    ADMIN_USER_IDS = eval(ADMIN_USER_IDS)
    if not isinstance(ADMIN_USER_IDS, list):
        ADMIN_USER_IDS = []
except Exception as e:
    logger.error(f"Error parsing ADMIN_USER_IDS: {e}")
    ADMIN_USER_IDS = []

def require_user(func: Callable) -> Callable:
    """
    Decorator to check if the user exists in the database.
    
    This decorator checks if the user exists in the database.
    If not, it sends a message asking the user to register.
    
    Args:
        func: The handler function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user_id = update.effective_user.id
        user = get_user(user_id)
        
        if not user:
            # User not found
            await update.effective_message.reply_text(
                get_text('user_not_found', 'en'),
                parse_mode='HTML'
            )
            return
        
        # User exists, proceed with handler
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def require_login(func: Callable) -> Callable:
    """
    Decorator to require user login before executing a handler.
    
    This decorator checks if the user is logged in.
    If not, it sends a message asking the user to login.
    
    Args:
        func: The handler function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user_id = update.effective_user.id
        user = get_user(user_id)
        
        if not user or not user.get('is_logged_in', False):
            # User not found or not logged in
            await update.effective_message.reply_text(
                get_text('login_required', user_id),
                parse_mode='HTML'
            )
            return
        
        # User is logged in, proceed with handler
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def require_auth(func: Callable) -> Callable:
    """
    Decorator to require user authentication before executing a handler.
    
    This decorator checks if the user exists in the database and is active.
    If not, it sends a message asking the user to register.
    
    Args:
        func: The handler function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user_id = update.effective_user.id
        user = get_user(user_id)
        
        if not user or user.get('status') != 'active':
            # User not found or not active
            await update.effective_message.reply_text(
                get_text('auth.not_registered', user_id),
                parse_mode='HTML'
            )
            return
        
        # User is authenticated, proceed with handler
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin privileges before executing a handler.
    
    This decorator checks if the user is in the list of admin user IDs.
    If not, it sends a message indicating that the command is only available to admins.
    
    Args:
        func: The handler function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_USER_IDS:
            # User is not an admin
            await update.effective_message.reply_text(
                get_text('admin.not_authorized', user_id),
                parse_mode='HTML'
            )
            return
        
        # User is an admin, proceed with handler
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def authenticated_user(func: Callable) -> Callable:
    """
    Decorator to ensure a user is authenticated before accessing a handler.
    Creates the user in the database if they don't exist.
    
    Args:
        func: The handler function to wrap
        
    Returns:
        Wrapped function that checks authentication
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user_id = update.effective_user.id
        
        # Check if user exists in database
        user = get_user(user_id)
        
        if not user:
            # User doesn't exist, prompt to start the bot first
            if update.callback_query:
                await update.callback_query.answer("لطفا ابتدا ربات را استارت کنید: /start", show_alert=True)
                return
            else:
                await update.message.reply_text(
                    "لطفا ابتدا ربات را استارت کنید: /start",
                    parse_mode=ParseMode.HTML
                )
                return
        
        # User exists, proceed with handler
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def admin_only(func: Callable) -> Callable:
    """
    Decorator to ensure only admins can access a handler.
    
    Args:
        func: The handler function to wrap
        
    Returns:
        Wrapped function that checks admin permissions
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user_id = update.effective_user.id
        
        # Get admin IDs from settings
        admin_ids = getattr(settings, 'ADMIN_IDS', [])
        
        # Check if user ID is in admin list
        if str(user_id) in map(str, admin_ids) or user_id in admin_ids:
            # User is admin, proceed with handler
            return await func(update, context, *args, **kwargs)
        else:
            # User is not admin, send error message
            if update.callback_query:
                await update.callback_query.answer("شما دسترسی به این بخش را ندارید.", show_alert=True)
                return
            else:
                await update.message.reply_text(
                    "⚠️ <b>خطای دسترسی</b>\n\n"
                    "شما دسترسی به این بخش را ندارید.",
                    parse_mode=ParseMode.HTML
                )
                return
    
    return wrapper

def staff_only(func: Callable) -> Callable:
    """
    Decorator to ensure only staff members can access a handler.
    Staff includes admins and support team.
    
    Args:
        func: The handler function to wrap
        
    Returns:
        Wrapped function that checks staff permissions
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user_id = update.effective_user.id
        
        # Get admin and staff IDs from settings
        admin_ids = getattr(settings, 'ADMIN_IDS', [])
        staff_ids = getattr(settings, 'STAFF_IDS', [])
        
        # Combine admin and staff IDs
        allowed_ids = list(map(str, admin_ids)) + list(map(str, staff_ids))
        
        # Check if user ID is in allowed list
        if str(user_id) in allowed_ids or user_id in admin_ids or user_id in staff_ids:
            # User is staff, proceed with handler
            return await func(update, context, *args, **kwargs)
        else:
            # User is not staff, send error message
            if update.callback_query:
                await update.callback_query.answer("شما دسترسی به این بخش را ندارید.", show_alert=True)
                return
            else:
                await update.message.reply_text(
                    "⚠️ <b>خطای دسترسی</b>\n\n"
                    "شما دسترسی به این بخش را ندارید.",
                    parse_mode=ParseMode.HTML
                )
                return
    
    return wrapper

def restricted_callback(allowed_patterns: list) -> Callable:
    """
    Decorator to restrict callbacks to specific patterns.
    
    Args:
        allowed_patterns: List of allowed callback data patterns
        
    Returns:
        Decorator function that checks callback patterns
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
            query = update.callback_query
            
            # Check if callback data matches any allowed pattern
            if any(query.data.startswith(pattern) for pattern in allowed_patterns):
                # Callback is allowed, proceed with handler
                return await func(update, context, *args, **kwargs)
            else:
                # Callback is not allowed, ignore
                await query.answer("این دکمه برای شما فعال نیست.", show_alert=True)
                return
        
        return wrapper
    
    return decorator

def management_group_access(required_groups: List[str]) -> Callable:
    """
    Decorator to ensure user has access to specific management functionality.
    
    This decorator checks if the user is in a management group with the specified roles.
    If not, it sends a message indicating that the user doesn't have proper access.
    
    Args:
        required_groups: List of management group types the user must be part of
        
    Returns:
        The decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
            user_id = update.effective_user.id
            
            # Admins always have full access
            admin_ids = getattr(settings, 'ADMIN_IDS', [])
            if str(user_id) in map(str, admin_ids) or user_id in admin_ids:
                return await func(update, context, *args, **kwargs)
            
            # For non-admins, check if they're in the required management groups
            from models.users import User
            from models.groups import BotManagementGroup, BotManagementGroupMember
            
            try:
                # Get user from database
                user = await User.filter(telegram_id=user_id).first()
                if not user:
                    # User not found
                    if update.callback_query:
                        await update.callback_query.answer("شما در سیستم ثبت نشده‌اید.", show_alert=True)
                    else:
                        await update.message.reply_text(
                            "⚠️ <b>خطای دسترسی</b>\n\n"
                            "شما در سیستم ثبت نشده‌اید. لطفا ابتدا ربات را استارت کنید.",
                            parse_mode=ParseMode.HTML
                        )
                    return
                
                # Get user's management group memberships
                memberships = await BotManagementGroupMember.filter(user=user).prefetch_related('group').all()
                
                # Check if user is in any of the required groups
                user_groups = []
                for membership in memberships:
                    group = membership.group
                    if group.is_active and group.notification_types:
                        user_groups.extend(group.notification_types)
                
                # Check if user has access to any of the required groups
                has_access = any(group in user_groups for group in required_groups)
                
                if has_access:
                    # User has proper access, proceed with handler
                    return await func(update, context, *args, **kwargs)
                else:
                    # User doesn't have proper access
                    if update.callback_query:
                        await update.callback_query.answer("شما دسترسی به این بخش را ندارید.", show_alert=True)
                    else:
                        allowed_groups = ", ".join([f"{group}" for group in required_groups])
                        await update.message.reply_text(
                            f"⚠️ <b>خطای دسترسی</b>\n\n"
                            f"شما دسترسی به این بخش را ندارید. برای استفاده از این بخش، باید عضو یکی از گروه‌های مدیریتی زیر باشید:\n"
                            f"{allowed_groups}",
                            parse_mode=ParseMode.HTML
                        )
                    return
                    
            except Exception as e:
                logger.error(f"Error checking management group access: {e}")
                if update.callback_query:
                    await update.callback_query.answer("خطا در بررسی دسترسی. لطفا دوباره تلاش کنید.", show_alert=True)
                else:
                    await update.message.reply_text(
                        "⚠️ <b>خطای سیستمی</b>\n\n"
                        "خطا در بررسی دسترسی. لطفا دوباره تلاش کنید.",
                        parse_mode=ParseMode.HTML
                    )
                return
                
        return wrapper
    return decorator 