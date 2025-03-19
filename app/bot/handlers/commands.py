"""
Command handlers for MoonVPN Telegram Bot.

This module contains all command handlers for the bot,
including start, help, status, buy, and settings commands.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    try:
        user = update.effective_user
        welcome_message = (
            f"👋 Welcome to MoonVPN, {user.first_name}!\n\n"
            "I'm your personal VPN assistant. Here's what I can help you with:\n"
            "• Purchase VPN accounts\n"
            "• Check account status\n"
            "• Change server location\n"
            "• Manage subscriptions\n"
            "• Get support\n\n"
            "Use /help to see all available commands."
        )
        
        await update.message.reply_text(welcome_message)
        logger.info(f"User {user.id} started the bot")
        
    except Exception as e:
        logger.error(f"Error in start_handler: {str(e)}")
        await update.message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    try:
        help_message = (
            "📚 Available Commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/buy - Purchase a VPN account\n"
            "/status - Check your account status\n"
            "/settings - Manage your settings\n\n"
            "Need more help? Contact our support team!"
        )
        
        await update.message.reply_text(help_message)
        logger.info(f"User {update.effective_user.id} requested help")
        
    except Exception as e:
        logger.error(f"Error in help_handler: {str(e)}")
        await update.message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /status command."""
    try:
        user = update.effective_user
        # TODO: Implement status checking logic
        status_message = (
            "🔍 Account Status:\n\n"
            "No active VPN account found.\n"
            "Use /buy to purchase a new account."
        )
        
        await update.message.reply_text(status_message)
        logger.info(f"User {user.id} checked account status")
        
    except Exception as e:
        logger.error(f"Error in status_handler: {str(e)}")
        await update.message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /buy command."""
    try:
        user = update.effective_user
        # TODO: Implement purchase flow
        buy_message = (
            "🛍️ VPN Plans:\n\n"
            "1. Monthly Plan - $9.99\n"
            "2. 3-Month Plan - $24.99\n"
            "3. 6-Month Plan - $44.99\n"
            "4. Yearly Plan - $79.99\n\n"
            "Select a plan to continue:"
        )
        
        await update.message.reply_text(buy_message)
        logger.info(f"User {user.id} started purchase flow")
        
    except Exception as e:
        logger.error(f"Error in buy_handler: {str(e)}")
        await update.message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /settings command."""
    try:
        user = update.effective_user
        # TODO: Implement settings management
        settings_message = (
            "⚙️ Settings:\n\n"
            "1. Language\n"
            "2. Notifications\n"
            "3. Auto-renewal\n"
            "4. Privacy\n\n"
            "Select an option to configure:"
        )
        
        await update.message.reply_text(settings_message)
        logger.info(f"User {user.id} accessed settings")
        
    except Exception as e:
        logger.error(f"Error in settings_handler: {str(e)}")
        await update.message.reply_text(
            "Sorry, something went wrong. Please try again later."
        ) 