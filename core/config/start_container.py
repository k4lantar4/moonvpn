"""
MoonVPN Telegram Bot - Start Handler.

This module provides handlers for the /start command and welcome messages.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler

from core.database.models.user import User
from bot.constants import CallbackPatterns
from core.handlers.bot.main_menu import send_main_menu
from bot.filters import allowed_group_filter
from core.utils.helpers import is_admin
from core.config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Menu image URL - You can host this on your server or use Telegram file IDs after uploading
MENU_IMAGE = "https://example.com/path/to/vpn_header.jpg"  # Replace with your actual image URL or file_id

# Welcome image URL or file_id - replace with an actual URL or file_id
WELCOME_IMAGE = "https://example.com/path/to/welcome_image.jpg"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    
    This command displays the main menu with glass buttons for all features.
    """
    user = update.effective_user
    message = update.message or update.callback_query.message
    
    # Extract referral code if present
    referral_id = None
    if message and message.text:
        match = re.search(r'start ref_(\d+)', message.text)
        if match:
            referral_id = int(match.group(1))
            logger.info(f"User {user.id} was referred by user {referral_id}")
    
    # Check if user exists in database, create if not
    db_user = User.get_by_telegram_id(user.id)
    
    if not db_user:
        User.create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            referral_id=referral_id,
            created_at=datetime.now()
        )
        logger.info(f"Created new user: {user.id} - @{user.username}")
    else:
        User.update(
            user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            last_seen=datetime.now()
        )
        logger.info(f"Existing user updated: {user.id} (@{user.username})")
    
    # Create a beautiful welcome message with emojis
    welcome_text = (
        f"💫 <b>به MoonVPN خوش آمدید!</b> 🌙\n\n"
        f"سلام {user.first_name}،\n"
        f"به سرویس MoonVPN خوش آمدید. با استفاده از دکمه‌های زیر می‌توانید:\n\n"
        f"• اکانت VPN خریداری کنید\n"
        f"• اکانت‌های خود را مدیریت کنید\n"
        f"• وضعیت سرویس خود را بررسی کنید\n"
        f"• آمار مصرف ترافیک را مشاهده کنید\n"
        f"• سرویس‌های رایگان دریافت کنید\n"
        f"• با دعوت دوستان کسب درآمد کنید\n\n"
        f"لطفاً از منوی زیر گزینه مورد نظر خود را انتخاب کنید:"
    )
    
    # Create a keyboard with glass-style buttons
    keyboard = [
        [
            InlineKeyboardButton("🛒 خرید اکانت", callback_data=CallbackPatterns.BUY_ACCOUNT),
            InlineKeyboardButton("👤 مدیریت اکانت‌ها", callback_data=CallbackPatterns.MANAGE_ACCOUNTS)
        ],
        [
            InlineKeyboardButton("💰 پرداخت", callback_data=CallbackPatterns.PAYMENT),
            InlineKeyboardButton("📊 وضعیت اکانت", callback_data=CallbackPatterns.CHECK_STATUS)
        ],
        [
            InlineKeyboardButton("🌍 تغییر لوکیشن", callback_data=CallbackPatterns.CHANGE_LOCATION),
            InlineKeyboardButton("📈 مصرف ترافیک", callback_data=CallbackPatterns.CHECK_TRAFFIC)
        ],
        [
            InlineKeyboardButton("🎁 سرویس رایگان", callback_data=CallbackPatterns.FREE_SERVICES),
            InlineKeyboardButton("💸 کسب درآمد", callback_data=CallbackPatterns.EARN_MONEY)
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data=CallbackPatterns.SETTINGS),
            InlineKeyboardButton("❓ راهنما", callback_data=CallbackPatterns.HELP)
        ],
        [
            InlineKeyboardButton("🆘 پشتیبانی", callback_data=CallbackPatterns.SUPPORT)
        ]
    ]
    
    # Add admin button if user is admin
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔐 پنل مدیریت", callback_data=CallbackPatterns.ADMIN)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Try to send with image first, fallback to text-only if fails
    try:
        if update.callback_query:
            await update.callback_query.answer()
            if hasattr(update.callback_query.message, 'photo'):
                await update.callback_query.edit_message_caption(
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await update.callback_query.edit_message_text(
                    text=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            try:
                await message.reply_photo(
                    photo=WELCOME_IMAGE,
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending welcome image: {e}")
                # Fallback to text-only
                await message.reply_text(
                    text=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        # Final fallback
        try:
            await message.reply_text(
                text="به MoonVPN خوش آمدید! لطفاً منوی زیر را مشاهده کنید.",
                reply_markup=reply_markup
            )
        except Exception as e2:
            logger.error(f"Failed to send fallback message: {e2}")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the main menu."""
    user = update.effective_user
    
    # Check if user is admin
    db_user = User.get_by_telegram_id(user.id)
    is_admin = db_user.is_admin if db_user else False
    
    # Create main menu keyboard
    keyboard = get_main_menu_keyboard(is_admin)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Menu message
    menu_text = "🌙 <b>منوی اصلی MoonVPN</b>\n\nلطفا گزینه مورد نظر خود را انتخاب کنید:"
    
    # Send message with image
    try:
        # Send with image if available
        await update.message.reply_photo(
            photo=MENU_IMAGE,
            caption=menu_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error sending menu with image: {e}")
        # Fallback to text-only if image fails
        await update.message.reply_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries for the main menu."""
    query = update.callback_query
    user = update.effective_user
    
    await query.answer()
    
    # Create welcome message
    welcome_text = (
        f"💫 <b>منوی اصلی MoonVPN</b> 🌙\n\n"
        f"سلام {user.first_name}،\n"
        f"از منوی زیر گزینه مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("🛒 خرید اکانت", callback_data=CallbackPatterns.BUY_ACCOUNT),
            InlineKeyboardButton("👤 مدیریت اکانت‌ها", callback_data=CallbackPatterns.MANAGE_ACCOUNTS)
        ],
        [
            InlineKeyboardButton("💰 پرداخت", callback_data=CallbackPatterns.PAYMENT),
            InlineKeyboardButton("📊 وضعیت اکانت", callback_data=CallbackPatterns.CHECK_STATUS)
        ],
        [
            InlineKeyboardButton("🌍 تغییر لوکیشن", callback_data=CallbackPatterns.CHANGE_LOCATION),
            InlineKeyboardButton("📈 مصرف ترافیک", callback_data=CallbackPatterns.CHECK_TRAFFIC)
        ],
        [
            InlineKeyboardButton("🎁 سرویس رایگان", callback_data=CallbackPatterns.FREE_SERVICES),
            InlineKeyboardButton("💸 کسب درآمد", callback_data=CallbackPatterns.EARN_MONEY)
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data=CallbackPatterns.SETTINGS),
            InlineKeyboardButton("❓ راهنما", callback_data=CallbackPatterns.HELP)
        ],
        [
            InlineKeyboardButton("🆘 پشتیبانی", callback_data=CallbackPatterns.SUPPORT)
        ]
    ]
    
    # Add admin button if user is admin
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔐 پنل مدیریت", callback_data=CallbackPatterns.ADMIN)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        if hasattr(query.message, 'photo'):
            await query.edit_message_caption(
                caption=welcome_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error updating main menu: {e}")

def get_main_menu_keyboard(is_admin: bool = False) -> List[List[InlineKeyboardButton]]:
    """Create the main menu keyboard."""
    # Create a visually appealing menu with 2 buttons per row
    keyboard = [
        [
            InlineKeyboardButton("🔐 اشتراک های من", callback_data=CallbackPatterns.MY_ACCOUNTS),
            InlineKeyboardButton("🛒 خرید اشتراک جدید", callback_data=CallbackPatterns.BUY_ACCOUNT)
        ],
        [
            InlineKeyboardButton("💰 افزایش موجودی", callback_data=CallbackPatterns.INCREASE_CREDIT),
            InlineKeyboardButton("👤 حساب کاربری", callback_data=CallbackPatterns.USER_SETTINGS)
        ],
        [
            InlineKeyboardButton("🔄 تست رایگان", callback_data=CallbackPatterns.FREE_TEST),
            InlineKeyboardButton("🌐 پروکسی رایگان", callback_data=CallbackPatterns.FREE_PROXY)
        ],
        [
            InlineKeyboardButton("💸 کسب درآمد", callback_data=CallbackPatterns.EARN_MONEY),
            InlineKeyboardButton("🎯 وضعیت سرویس", callback_data=CallbackPatterns.ACCOUNT_STATUS)
        ],
        [
            InlineKeyboardButton("❓ راهنما", callback_data=CallbackPatterns.HELP_COMMAND),
            InlineKeyboardButton("👨‍💻 پشتیبانی", callback_data=CallbackPatterns.SUPPORT)
        ]
    ]
    
    # Add admin button if user is admin
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ پنل مدیریت", callback_data=CallbackPatterns.ADMIN_DASHBOARD)])
    
    return keyboard

def get_start_handlers():
    """Return all handlers related to the start command."""
    return [
        CallbackQueryHandler(main_menu_handler, pattern=f"^{CallbackPatterns.MAIN_MENU}$")
    ]

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    user_id = update.effective_user.id
    
    # Get user's language preference
    db_user = User.get_by_id(user_id)
    if db_user:
        user_pref = db_user.get_preferences()
        language_code = user_pref.get_language() if user_pref else "en"
    else:
        language_code = "en"
    
    # Store language in context for future use
    context.user_data["language"] = language_code
    
    # Send unknown command message
    await update.message.reply_text(
        get_text("unknown_command", language_code),
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the help menu."""
    # This is a placeholder that will redirect to the help module
    from core.handlers.bot.help import help_command as show_help
    await show_help(update, context) 