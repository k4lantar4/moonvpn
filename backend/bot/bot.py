"""
MoonVPN Telegram Bot - Main Entry Point.

This module initializes and runs the Telegram bot with enhanced security and monitoring.
"""

import logging
import os
import sys
from pathlib import Path
import asyncio

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Set up Django using our custom setup function
from core.bot.django_setup import setup_django
setup_django()

# Import necessary models
from core.database.models import (
    User, AdminGroup, Wallet, Transaction, Order, Voucher,
    Server, Location, VPNAccount, SubscriptionPlan, AccountService
)

# Import bot components
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from telegram import Update

# Placeholder for handlers that we'll implement later
async def start_handler(update, context):
    """Handle the /start command."""
    await update.message.reply_text("Welcome to MoonVPN Bot! This is a placeholder message.")

async def buy_handler(update, context):
    """Handle the /buy command and buy: callback queries."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("This is a placeholder for the buy callback handler.")
    else:
        await update.message.reply_text("This is a placeholder for the buy command handler.")

async def status_handler(update, context):
    """Handle the /status command."""
    await update.message.reply_text("This is a placeholder for the status command handler.")

async def status_callback_handler(update, context):
    """Handle status: callback queries."""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("This is a placeholder for the status callback handler.")

async def change_server_handler(update, context):
    """Handle the /change_server command."""
    await update.message.reply_text("This is a placeholder for the change_server command handler.")

async def change_server_callback_handler(update, context):
    """Handle change_server: callback queries."""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("This is a placeholder for the change_server callback handler.")

async def admin_handler(update, context):
    """Handle the /admin command."""
    await update.message.reply_text("This is a placeholder for the admin command handler.")

async def admin_callback_handler(update, context):
    """Handle admin: callback queries."""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("This is a placeholder for the admin callback handler.")

async def support_handler(update, context):
    """Handle the /support command."""
    await update.message.reply_text("This is a placeholder for the support command handler.")

async def wallet_handler(update, context):
    """Handle the /wallet command."""
    await update.message.reply_text("This is a placeholder for the wallet command handler.")

async def wallet_callback_handler(update, context):
    """Handle wallet: callback queries."""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("This is a placeholder for the wallet callback handler.")

async def main():
    """Start the bot with enhanced capabilities."""
    try:
        # Get the bot token from environment variable
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("No bot token provided. Set the TELEGRAM_BOT_TOKEN environment variable.")
            sys.exit(1)
        
        # Initialize bot application
        application = Application.builder().token(bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("help", start_handler))
        
        application.add_handler(CommandHandler("buy", buy_handler))
        application.add_handler(CallbackQueryHandler(buy_handler, pattern="^buy:"))
        
        application.add_handler(CommandHandler("status", status_handler))
        application.add_handler(CallbackQueryHandler(status_callback_handler, pattern="^status:"))
        
        application.add_handler(CommandHandler("change_server", change_server_handler))
        application.add_handler(CallbackQueryHandler(change_server_callback_handler, pattern="^change_server:"))
        
        application.add_handler(CommandHandler("admin", admin_handler))
        application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin:"))
        
        application.add_handler(CommandHandler("support", support_handler))
        
        application.add_handler(CommandHandler("wallet", wallet_handler))
        application.add_handler(CallbackQueryHandler(wallet_callback_handler, pattern="^wallet:"))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("Starting bot...")
        await application.start()
        
        # Run the bot until Ctrl+C is pressed
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)

async def error_handler(update, context):
    """Handle errors in the bot."""
    try:
        logger.error(f"Update {update} caused error {context.error}")
        
        # Get admin group for error reporting
        admin_groups = AdminGroup.objects.filter(type='management', is_active=True)
        if admin_groups.exists():
            admin_group_id = admin_groups.first().telegram_chat_id
            
            # Prepare error message
            error_message = (
                f"⚠️ Bot Error\n\n"
                f"Error: {str(context.error)}\n"
                f"User: {update.effective_user.id if update and update.effective_user else 'Unknown'}\n"
                f"Type: {type(context.error).__name__}"
            )
            
            # Send error message to admin group
            await context.bot.send_message(
                chat_id=admin_group_id,
                text=error_message
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

if __name__ == '__main__':
    asyncio.run(main())
