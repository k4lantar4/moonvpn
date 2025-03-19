"""
Navigation handler for the Telegram bot.

This module handles navigation between different sections of the bot.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

import logging
from typing import Dict, Any, List, Optional

from core.utils.i18n import get_text
from core.database import get_user_language

# Replace the User import with proper model import
from models import User

# Import handlers
from handlers import start

# Configure logging
logger = logging.getLogger("telegram_bot")

MENU_CALLBACKS = {
    "accounts": "accounts",
    "profile": "profile",
    "support": "support",
    "language": "language",
    "admin": "admin",
    "payments": "payments",
    "servers": "servers",
    "monitoring": "monitoring",
    "settings": "settings",
    "referrals": "referrals",
    "notifications": "notifications",
    "points": "points",
    "back_to_main": "back_to_main",
}

async def back_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle back button presses."""
    query = update.callback_query
    await query.answer()
    
    # Get the callback data
    callback_data = query.data
    
    # If it's a back to main menu callback
    if callback_data == "back_to_main":
        return await main_menu_handler(update, context)
    
    # If it's a navigation callback
    if callback_data.startswith("back:"):
        await handle_navigation(update, context)
        return 0  # Return to main menu state
    
    return -1  # Continue with other handlers


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu navigation."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    # Get user's language preference
    language_code = get_user_language(user_id)
    
    # Create welcome message
    welcome_message = get_text("welcome_back", language_code).format(user.first_name)
    
    # Create keyboard
    keyboard = build_main_menu_keyboard(user_id, language_code)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message if it's a callback query
    if query:
        await query.edit_message_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Send a new message if it's not a callback query
        if update.message:
            await update.message.reply_text(
                welcome_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    return 0  # Return to main menu state


async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle navigation between different sections of the bot."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Extract callback data
    callback_data = query.data
    
    # Handle navigation actions
    if callback_data == "back_to_main":
        await show_main_menu(update, context)
    elif callback_data == "accounts":
        # Redirect to accounts menu
        await query.edit_message_text(
            get_text("redirect", language_code),
            reply_markup=None
        )
        return await context.application.handlers.callback_queries[-1].callback(update, context)
    elif callback_data == "payments":
        # Redirect to payments menu
        await query.edit_message_text(
            get_text("redirect", language_code),
            reply_markup=None
        )
        return await context.application.handlers.callback_queries[-1].callback(update, context)
    elif callback_data == "subscription_plans":
        # Redirect to subscription plans menu
        await query.edit_message_text(
            get_text("redirect", language_code),
            reply_markup=None
        )
        return await context.application.handlers.callback_queries[-1].callback(update, context)
    elif callback_data == "profile":
        # Redirect to profile menu
        await query.edit_message_text(
            get_text("redirect", language_code),
            reply_markup=None
        )
        return await context.application.handlers.callback_queries[-1].callback(update, context)
    elif callback_data == "support":
        # Redirect to support menu
        await query.edit_message_text(
            get_text("redirect", language_code),
            reply_markup=None
        )
        return await context.application.handlers.callback_queries[-1].callback(update, context)
    elif callback_data == "language":
        # Navigate to language selection
        from .language import language_callback
        await language_callback(update, context)
        
    elif callback_data == "admin":
        # Check if user is admin
        db_user = User.get_by_id(user_id)
        if db_user and db_user.is_admin:
            # Navigate to admin menu
            from .admin import admin_menu
            await admin_menu(update, context)
        else:
            # User is not an admin
            await query.edit_message_text(
                get_text("error_unauthorized", language_code),
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif callback_data == "monitoring":
        # Navigate to monitoring menu
        from .monitoring import monitoring_menu
        await monitoring_menu(update, context)
        
    elif callback_data == "servers":
        # Navigate to servers menu
        from .admin import server_list
        await server_list(update, context)
        
    elif callback_data == "notifications":
        # Navigate to notifications menu
        from .notifications import notifications_menu
        await notifications_menu(update, context)
        
    elif callback_data == "referrals":
        # Navigate to referrals menu
        from .referrals import referrals_menu
        await referrals_menu(update, context)
        
    elif callback_data == "points":
        # Navigate to points menu
        from .points import points_menu
        await points_menu(update, context)
    
    elif callback_data.startswith("back:"):
        # Handle back navigation to specific menus
        destination = callback_data.split(":")[1]
        
        if destination == "accounts":
            from .accounts import accounts_menu
            await accounts_menu(update, context)
        elif destination == "profile":
            from .profile import profile_menu
            await profile_menu(update, context)
        elif destination == "support":
            from .support import support_menu
            await support_menu(update, context)
        elif destination == "admin":
            from .admin import admin_menu
            await admin_menu(update, context)
        elif destination == "payments":
            from .payments import payments_menu
            await payments_menu(update, context)
        elif destination == "monitoring":
            from .monitoring import monitoring_menu
            await monitoring_menu(update, context)
        elif destination == "notifications":
            from .notifications import notifications_menu
            await notifications_menu(update, context)
        elif destination == "referrals":
            from .referrals import referrals_menu
            await referrals_menu(update, context)
        elif destination == "points":
            from .points import points_menu
            await points_menu(update, context)
        else:
            # Default to main menu
            await back_to_main(update, context)
    
    # If callback data not recognized, do nothing
    else:
        logger.warning(f"Unhandled navigation callback: {callback_data}")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to the main menu."""
    query = update.callback_query
    user = update.effective_user
    user_id = user.id
    
    # Get user's language preference
    language_code = context.user_data.get("language", "en")
    
    # Create welcome message
    welcome_message = get_text("welcome_back", language_code).format(user.first_name)
    
    # Create keyboard
    keyboard = build_main_menu_keyboard(user_id, language_code)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Update message
    await query.edit_message_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def build_main_menu_keyboard(user_id: int, language_code: str) -> List[List[InlineKeyboardButton]]:
    """Build the main menu keyboard based on user permissions."""
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"🚀 {get_text('accounts', language_code)}",
                callback_data="accounts"
            ),
            InlineKeyboardButton(
                f"👤 {get_text('profile', language_code)}",
                callback_data="profile"
            )
        ],
        [
            InlineKeyboardButton(
                f"💰 {get_text('payments', language_code)}",
                callback_data="payments"
            ),
            InlineKeyboardButton(
                f"👥 {get_text('referrals', language_code)}",
                callback_data="referrals"
            )
        ],
        [
            InlineKeyboardButton(
                f"🔔 {get_text('notifications', language_code)}",
                callback_data="notifications"
            ),
            InlineKeyboardButton(
                f"📊 {get_text('monitoring', language_code)}",
                callback_data="monitoring"
            )
        ],
        [
            InlineKeyboardButton(
                f"💬 {get_text('support', language_code)}",
                callback_data="support"
            ),
            InlineKeyboardButton(
                f"🌐 {get_text('language', language_code)}",
                callback_data="language"
            )
        ]
    ]
    
    # Add admin button if user is admin
    db_user = User.get_by_id(user_id)
    if db_user and db_user.is_admin:
        keyboard.append([
            InlineKeyboardButton(
                f"⚙️ {get_text('admin_panel', language_code)}",
                callback_data="admin"
            )
        ])
    
    return keyboard 

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main menu."""
    query = update.callback_query
    user = update.effective_user
    user_id = user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user information
    db_user = get_user(user_id)
    is_admin = db_user.get("is_admin", False) if db_user else False
    
    # Set welcome message
    if "seen_welcome" in context.user_data:
        message = get_text("welcome_back", language_code).format(user.first_name)
    else:
        message = get_text("welcome", language_code).format(user.first_name)
        context.user_data["seen_welcome"] = True
    
    # Build keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔑 {get_text('accounts', language_code)}",
                callback_data="accounts"
            ),
            InlineKeyboardButton(
                f"💰 {get_text('payments', language_code)}",
                callback_data="payments"
            )
        ],
        [
            InlineKeyboardButton(
                f"🏷️ {get_text('subscription_plans', language_code)}",
                callback_data="subscription_plans"
            ),
            InlineKeyboardButton(
                f"👤 {get_text('profile', language_code)}",
                callback_data="profile"
            )
        ],
        [
            InlineKeyboardButton(
                f"🌐 {get_text('language', language_code)}",
                callback_data="language"
            ),
            InlineKeyboardButton(
                f"❓ {get_text('support', language_code)}",
                callback_data="support"
            )
        ]
    ]
    
    # Add admin panel button if user is admin
    if is_admin:
        keyboard.append([
            InlineKeyboardButton(
                f"⚙️ {get_text('admin_panel', language_code)}",
                callback_data="admin"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        ) 

def navigation_handler():
    """Return the handlers for navigation."""
    return [
        CallbackQueryHandler(back_button_handler, pattern=r"^back:"),
        CallbackQueryHandler(back_button_handler, pattern=r"^back_to_main$"),
        CallbackQueryHandler(handle_navigation, pattern=r"^(accounts|profile|support|language|admin|payments|servers|monitoring|settings|referrals|notifications|points)$"),
    ] 