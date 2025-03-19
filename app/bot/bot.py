"""
MoonVPN Telegram Bot Application

This module implements the core Telegram bot functionality for MoonVPN,
handling user interactions, commands, and service integration.
"""

from typing import Optional
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from app.core.config import settings
from app.bot.handlers import (
    start_handler,
    help_handler,
    status_handler,
    settings_handler,
)
from app.bot.handlers.conversations import (
    registration_handler,
    purchase_handler,
)
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class MoonVPNBot:
    """Main bot class for handling Telegram interactions."""
    
    def __init__(self, app: FastAPI):
        """Initialize the bot with FastAPI application."""
        self.app = app
        self.application: Optional[Application] = None
        
    async def setup(self):
        """Setup the bot application with handlers and webhook."""
        try:
            # Initialize bot application
            self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", start_handler))
            self.application.add_handler(CommandHandler("help", help_handler))
            self.application.add_handler(CommandHandler("status", status_handler))
            self.application.add_handler(CommandHandler("settings", settings_handler))
            
            # Add conversation handlers
            self.application.add_handler(registration_handler)
            self.application.add_handler(purchase_handler)
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            # Setup webhook
            await self.application.bot.set_webhook(
                url=f"{settings.WEBHOOK_BASE_URL}/webhook",
                allowed_updates=Update.ALL_TYPES
            )
            
            logger.info("Bot setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during bot setup: {str(e)}")
            raise
    
    async def start(self):
        """Start the bot application."""
        if not self.application:
            raise RuntimeError("Bot application not initialized")
            
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the bot application."""
        if not self.application:
            return
            
        try:
            await self.application.stop()
            await self.application.shutdown()
            
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
            raise
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot application."""
        logger.error(f"Update {update} caused error: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

# Create bot instance
bot = MoonVPNBot(None)  # Will be initialized with FastAPI app 