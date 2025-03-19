"""
MoonVPN Telegram Bot - Start Command Handler.

This module provides the start command handler for the bot.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from backend.models import User as UserModel

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    
    # Log the command
    logger.info(f"User {user.id} ({user.username}) started the bot")
    
    # Create or update user in the database
    try:
        # Get or create user
        db_user, created = UserModel.objects.get_or_create(
            telegram_id=user.id,
            defaults={
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language": user.language_code or "fa"
            }
        )
        
        # Update user info if not created
        if not created:
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db_user.save(update_fields=["username", "first_name", "last_name"])
            
        logger.info(f"User {'created' if created else 'updated'} in database")
        
    except Exception as e:
        logger.error(f"Error creating/updating user: {e}")
    
    # Create welcome message
    welcome_message = (
        f"👋 سلام {user.first_name}!\n\n"
        "به ربات MoonVPN خوش آمدید.\n"
        "از طریق این ربات می‌توانید اشتراک VPN خود را خریداری و مدیریت کنید.\n\n"
        "📱 از دکمه‌های زیر برای شروع استفاده کنید:"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("📦 خرید اشتراک", callback_data="buy:plans"),
            InlineKeyboardButton("👤 حساب کاربری", callback_data="status:main")
        ],
        [
            InlineKeyboardButton("💰 کیف پول", callback_data="wallet:main"),
            InlineKeyboardButton("🔄 تغییر سرور", callback_data="change_server:main")
        ],
        [
            InlineKeyboardButton("❓ راهنما", callback_data="help:main"),
            InlineKeyboardButton("📞 پشتیبانی", callback_data="support:main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send welcome message with keyboard
    await update.message.reply_text(welcome_message, reply_markup=reply_markup) 