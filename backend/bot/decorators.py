"""
Decorators for the Telegram bot.

This module provides decorators for the Telegram bot handlers.
"""

import os
import json
import logging
import functools
from typing import Callable, List, Any, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes

# Configure logging
logger = logging.getLogger("telegram_bot")

# Get admin user IDs from environment variable
ADMIN_USER_IDS = os.getenv("ADMIN_USER_IDS", "[]")
try:
    ADMIN_USER_IDS = json.loads(ADMIN_USER_IDS)
except json.JSONDecodeError:
    logger.error(f"Invalid ADMIN_USER_IDS format: {ADMIN_USER_IDS}")
    ADMIN_USER_IDS = []

def require_admin(func: Callable) -> Callable:
    """Decorator to require admin privileges for a handler."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        user_id = user.id
        
        # Check if user is admin
        if str(user_id) not in ADMIN_USER_IDS:
            logger.warning(f"User {user_id} ({user.username}) tried to access admin function {func.__name__}")
            await update.message.reply_text("You don't have permission to use this command.")
            return
        
        # User is admin, proceed with the handler
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for a handler."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        user_id = user.id
        
        # Check if user exists in the database
        from core.database import get_user
        user_data = get_user(user_id)
        
        if not user_data:
            logger.warning(f"User {user_id} ({user.username}) tried to access authenticated function {func.__name__} without being registered")
            
            # If it's a callback query, answer it
            if update.callback_query:
                await update.callback_query.answer("Please register first by using /start command.")
                return
            
            # If it's a message, reply to it
            if update.message:
                await update.message.reply_text("Please register first by using /start command.")
                return
            
            return
        
        # User is authenticated, proceed with the handler
        return await func(update, context, *args, **kwargs)
    
    return wrapper 