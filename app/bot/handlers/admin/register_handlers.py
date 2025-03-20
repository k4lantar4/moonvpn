"""
Handler registration for admin group commands.

This module registers all admin group-specific command handlers
with the bot application.
"""

from typing import List, Dict, Any
from telegram.ext import CommandHandler, Application

from app.bot.handlers.admin.group_commands import GroupCommandHandler
from app.bot.services.admin_service import AdminService
from app.bot.services.admin_analytics_service import AdminAnalyticsService
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

def register_admin_handlers(application: Application) -> None:
    """Register admin group command handlers.
    
    Args:
        application: Telegram bot application instance
    """
    try:
        # Initialize services
        admin_service = AdminService()
        analytics_service = AdminAnalyticsService()
        
        # Initialize command handler
        group_handler = GroupCommandHandler(admin_service, analytics_service)
        
        # Get handlers for registration
        handlers = group_handler.get_handlers()
        
        # Register each handler
        for handler in handlers:
            command = handler["command"]
            callback = handler["callback"]
            group_type = handler["group_type"]
            
            # Create command handler with group type check
            command_handler = CommandHandler(
                command,
                callback,
                filters=group_type
            )
            
            # Add handler to application
            application.add_handler(command_handler)
            logger.info(f"Registered admin command handler: /{command}")
        
        logger.info("Successfully registered all admin command handlers")
        
    except Exception as e:
        logger.error(f"Error registering admin handlers: {str(e)}")
        raise 