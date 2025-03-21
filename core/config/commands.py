"""
Command handlers for the MoonVPN Telegram bot.

This module implements the command handlers for various bot commands
including start, help, status, settings, and admin commands.
"""

from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import settings
from app.bot.utils.logger import setup_logger
from app.bot.keyboards import (
    get_main_menu_keyboard,
    get_help_keyboard,
    get_settings_keyboard,
    get_status_keyboard,
)
from app.bot.services.vpn_service import VPNService

logger = setup_logger(__name__)
vpn_service = VPNService()

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    try:
        user = update.effective_user
        welcome_message = (
            f"👋 به MoonVPN خوش آمدید، {user.first_name}!\n\n"
            "🔒 سرویس VPN امن شما فقط چند کلیک فاصله دارد.\n"
            "از منوی زیر برای شروع استفاده کنید:"
        )
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"User {user.id} started the bot")
        
    except Exception as e:
        logger.error(f"Error in start_handler: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    try:
        help_message = (
            "📚 *راهنمای MoonVPN*\n\n"
            "*دستورات موجود:*\n"
            "/start - شروع کار با ربات\n"
            "/help - نمایش این راهنما\n"
            "/status - بررسی وضعیت حساب VPN\n"
            "/buy - خرید اشتراک جدید\n"
            "/settings - تنظیمات حساب\n\n"
            "*نیاز به راهنمایی بیشتر؟*\n"
            "برای دریافت کمک با پشتیبانی ما تماس بگیرید."
        )
        
        await update.message.reply_text(
            help_message,
            parse_mode='Markdown',
            reply_markup=get_help_keyboard()
        )
        logger.info(f"User {update.effective_user.id} requested help")
        
    except Exception as e:
        logger.error(f"Error in help_handler: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /status command."""
    try:
        user = update.effective_user
        
        # Get account status
        status_info = await vpn_service.get_account_status(user.id)
        
        # Send status message with appropriate keyboard
        await update.message.reply_text(
            status_info["message"],
            parse_mode='Markdown',
            reply_markup=get_status_keyboard(status_info)
        )
        
        logger.info(f"User {user.id} checked VPN status: {status_info['status']}")
        
    except Exception as e:
        logger.error(f"Error in status_handler: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /settings command."""
    try:
        user = update.effective_user
        settings_message = (
            "⚙️ *تنظیمات حساب*\n\n"
            "مدیریت تنظیمات و ترجیحات حساب شما:"
        )
        
        await update.message.reply_text(
            settings_message,
            parse_mode='Markdown',
            reply_markup=get_settings_keyboard()
        )
        logger.info(f"User {user.id} accessed settings")
        
    except Exception as e:
        logger.error(f"Error in settings_handler: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )

# Admin Commands
async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /admin_stats command (admin only)."""
    try:
        user = update.effective_user
        if user.id not in settings.ADMIN_IDS:
            await update.message.reply_text("⛔️ این دستور فقط برای مدیران سیستم است.")
            return
            
        # TODO: Implement admin statistics
        stats_message = (
            "📊 *آمار سیستم*\n\n"
            "در حال بارگذاری آمار سیستم..."
        )
        
        await update.message.reply_text(
            stats_message,
            parse_mode='Markdown'
        )
        logger.info(f"Admin {user.id} requested statistics")
        
    except Exception as e:
        logger.error(f"Error in admin_stats_handler: {str(e)}")
        await update.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        ) 