"""
Decorators for MoonVPN Telegram Bot.

This module provides decorators for command validation and access control.
"""

from functools import wraps
from typing import Callable, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from app.core.database.models.admin import AdminGroupType
from app.bot.services.admin_service import AdminService
from app.core.database.models.admin_group import AdminGroupMember
from app.bot.services.admin_group_service import AdminGroupService

def admin_required(required_role: Optional[str] = None):
    """
    Decorator to check if a user has admin privileges.
    
    Args:
        required_role: Optional specific role required (e.g., 'admin', 'moderator')
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            # Check if we have user information
            if not update.effective_user:
                await update.message.reply_text(
                    "❌ اطلاعات کاربر در دسترس نیست.\n"
                    "User information is not available."
                )
                return
            
            user_id = update.effective_user.id
            
            # Get database session from context
            db = context.bot_data.get('db')
            if not db:
                await update.message.reply_text(
                    "❌ خطا در اتصال به پایگاه داده.\n"
                    "Database connection error."
                )
                return
            
            # Initialize admin group service
            admin_service = AdminGroupService(db)
            
            # Get user's groups
            user_groups = admin_service.get_user_groups(user_id)
            if not user_groups:
                await update.message.reply_text(
                    "❌ شما دسترسی لازم برای استفاده از این دستور را ندارید.\n"
                    "You don't have permission to use this command."
                )
                return
            
            # If specific role is required, check for it
            if required_role:
                has_role = False
                for group in user_groups:
                    member = admin_service.get_member(group.chat_id, user_id)
                    if member and member.role == required_role:
                        has_role = True
                        break
                
                if not has_role:
                    await update.message.reply_text(
                        f"❌ شما نیاز به نقش {required_role} دارید.\n"
                        f"You need the {required_role} role."
                    )
                    return
            
            # User has required permissions, proceed with the command
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator

def group_admin_required(group_type: Optional[str] = None):
    """
    Decorator to check if a user has admin privileges for a specific group type.
    
    Args:
        group_type: Optional specific group type required
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            # Check if we have user information
            if not update.effective_user:
                await update.message.reply_text(
                    "❌ اطلاعات کاربر در دسترس نیست.\n"
                    "User information is not available."
                )
                return
            
            user_id = update.effective_user.id
            
            # Get database session from context
            db = context.bot_data.get('db')
            if not db:
                await update.message.reply_text(
                    "❌ خطا در اتصال به پایگاه داده.\n"
                    "Database connection error."
                )
                return
            
            # Initialize admin group service
            admin_service = AdminGroupService(db)
            
            # Get user's groups
            user_groups = admin_service.get_user_groups(user_id)
            if not user_groups:
                await update.message.reply_text(
                    "❌ شما دسترسی لازم برای استفاده از این دستور را ندارید.\n"
                    "You don't have permission to use this command."
                )
                return
            
            # If specific group type is required, check for it
            if group_type:
                has_group_type = False
                for group in user_groups:
                    if group.type == group_type:
                        has_group_type = True
                        break
                
                if not has_group_type:
                    await update.message.reply_text(
                        f"❌ شما نیاز به دسترسی به گروه‌های نوع {group_type} دارید.\n"
                        f"You need access to {group_type} type groups."
                    )
                    return
            
            # User has required permissions, proceed with the command
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator

def group_type_required(group_type: AdminGroupType) -> Callable:
    """Decorator to check if command is used in correct group type.
    
    Args:
        group_type: Required group type
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
            if not update.effective_chat:
                await update.message.reply_text("❌ Chat information not available.")
                return
            
            admin_service = context.bot_data.get('admin_service')
            if not admin_service:
                await update.message.reply_text("❌ Admin service not initialized.")
                return
            
            if not await admin_service.is_admin_group(update.effective_chat.id):
                await update.message.reply_text("❌ This command can only be used in admin groups.")
                return
            
            group = await admin_service.get_group(update.effective_chat.id)
            if not group or group.type != group_type:
                await update.message.reply_text(
                    f"❌ This command can only be used in {group_type.value} groups."
                )
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator 