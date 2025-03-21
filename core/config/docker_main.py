#!/usr/bin/env python3
"""
MoonVPN Telegram Bot - Standalone Main Entry Point

This module initializes and runs the Telegram bot without Django dependencies.
Uses a standalone SQLite database for storage.
"""

import logging
import os
import sys
from pathlib import Path
import json
import asyncio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_logs.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables from environment
token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("No TELEGRAM_BOT_TOKEN found in environment. Exiting.")
    sys.exit(1)

# Import necessary modules for the bot
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Simple command handlers for core functionality
async def start_command(update, context):
    """Handle the /start command."""
    user = update.effective_user
    await update.message.reply_html(
        f"سلام {user.mention_html()}! 👋\n\n"
        f"به ربات MoonVPN خوش آمدید.\n"
        f"از این ربات برای خرید، مدیریت و استفاده از سرویس VPN استفاده کنید."
    )

async def help_command(update, context):
    """Handle the /help command."""
    await update.message.reply_text(
        "🔍 راهنمای دستورات:\n\n"
        "/start - شروع کار با ربات\n"
        "/help - نمایش این راهنما\n"
        "/buy - خرید اشتراک جدید\n"
        "/status - وضعیت اشتراک‌های شما\n"
        "/support - ارتباط با پشتیبانی"
    )

async def buy_command(update, context):
    """Handle the /buy command."""
    await update.message.reply_text(
        "🛒 خرید اشتراک جدید\n\n"
        "برای خرید اشتراک VPN، لطفاً یکی از بسته‌های زیر را انتخاب کنید:\n\n"
        "1️⃣ بسته یک ماهه: 175,000 تومان\n"
        "2️⃣ بسته سه ماهه: 450,000 تومان\n"
        "3️⃣ بسته شش ماهه: 850,000 تومان\n\n"
        "برای خرید، لطفاً با پشتیبانی تماس بگیرید."
    )

async def status_command(update, context):
    """Handle the /status command."""
    await update.message.reply_text(
        "📊 وضعیت اشتراک شما\n\n"
        "شما در حال حاضر هیچ اشتراک فعالی ندارید.\n\n"
        "برای خرید اشتراک، از دستور /buy استفاده کنید."
    )

async def support_command(update, context):
    """Handle the /support command."""
    await update.message.reply_text(
        "📞 پشتیبانی\n\n"
        "برای ارتباط با پشتیبانی، لطفاً به آیدی زیر پیام دهید:\n"
        "@MoonVPN_Support"
    )

async def error_handler(update, context):
    """Log errors caused by updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Run bot."""
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("support", support_command))
    
    # Log errors
    application.add_error_handler(error_handler)
    
    # Start the bot
    webhook_url = os.environ.get("WEBHOOK_URL")
    webhook_path = os.environ.get("WEBHOOK_PATH")
    webhook_mode = os.environ.get("WEBHOOK_MODE", "false").lower() == "true"
    
    if webhook_mode and webhook_url and webhook_path:
        # Start webhook
        logger.info(f"Starting webhook on {webhook_url}{webhook_path}")
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("WEBHOOK_PORT", 8443)),
            url_path=webhook_path,
            webhook_url=f"{webhook_url}{webhook_path}"
        )
    else:
        # Start polling
        logger.info("Starting bot in polling mode")
        application.run_polling()

if __name__ == "__main__":
    main() 