"""
User management handlers for the V2Ray Telegram bot.

This module implements handlers for user management operations including:
- User registration
- Profile management
- Account settings
- Traffic usage monitoring
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from core.utils.i18n import get_text, format_number, format_date, get_available_languages
from core.database import (
    get_user,
    create_user,
    update_user,
    get_user_accounts,
    get_user_traffic,
)
from core.utils.helpers import require_auth
from handlers.language import LANGUAGE_CB
from handlers.notifications import NOTIFICATIONS_CB

logger = logging.getLogger(__name__)

# Conversation states
(
    SELECTING_ACTION,
    ENTERING_NAME,
    ENTERING_EMAIL,
    ENTERING_PHONE,
    CONFIRMING_DETAILS,
) = range(5)

# Callback data patterns
PROFILE_CB = "profile"
EDIT_NAME = f"{PROFILE_CB}_name"
EDIT_EMAIL = f"{PROFILE_CB}_email"
EDIT_PHONE = f"{PROFILE_CB}_phone"
VIEW_TRAFFIC = f"{PROFILE_CB}_traffic"
VIEW_SETTINGS = f"{PROFILE_CB}_settings"

@require_auth
async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the user profile menu."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user profile
    user = get_user(user_id)
    if not user:
        # Create new user if not exists
        user = create_user({
            "id": user_id,
            "username": update.effective_user.username,
            "language": language_code,
            "created_at": datetime.now().isoformat()
        })
    
    # Format profile text
    text = get_text("profile_details", language_code).format(
        name=user.get("name", get_text("not_set", language_code)),
        email=user.get("email", get_text("not_set", language_code)),
        phone=user.get("phone", get_text("not_set", language_code)),
        created_at=format_date(user["created_at"], language_code)
    )
    
    # Get account statistics
    accounts = get_user_accounts(user_id)
    if accounts:
        text += "\n\n" + get_text("account_stats", language_code).format(
            total_accounts=len(accounts),
            active_accounts=sum(1 for a in accounts if a["status"] == "active")
        )
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("edit_name", language_code),
                callback_data=EDIT_NAME
            ),
            InlineKeyboardButton(
                get_text("edit_email", language_code),
                callback_data=EDIT_EMAIL
            )
        ],
        [
            InlineKeyboardButton(
                get_text("edit_phone", language_code),
                callback_data=EDIT_PHONE
            ),
            InlineKeyboardButton(
                get_text("view_traffic", language_code),
                callback_data=VIEW_TRAFFIC
            )
        ],
        [
            InlineKeyboardButton(
                get_text("account_settings", language_code),
                callback_data=VIEW_SETTINGS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_menu", language_code),
                callback_data="menu"
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_auth
async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing user's name."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    text = get_text("enter_name", language_code)
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("cancel", language_code),
                callback_data=PROFILE_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return ENTERING_NAME

@require_auth
async def edit_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing user's email."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    text = get_text("enter_email", language_code)
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("cancel", language_code),
                callback_data=PROFILE_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return ENTERING_EMAIL

@require_auth
async def edit_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing user's phone number."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    text = get_text("enter_phone", language_code)
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("cancel", language_code),
                callback_data=PROFILE_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return ENTERING_PHONE

@require_auth
async def save_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save user's name."""
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    name = update.message.text
    
    try:
        # Update user's name
        update_user(user_id, {"name": name})
        text = get_text("name_updated", language_code)
    except Exception as e:
        logger.error(f"Error updating name for user {user_id}: {e}")
        text = get_text("error_general", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_profile", language_code),
                callback_data=PROFILE_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_auth
async def save_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save user's email."""
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    email = update.message.text
    
    # Basic email validation
    if "@" not in email or "." not in email:
        text = get_text("invalid_email", language_code)
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("try_again", language_code),
                    callback_data=EDIT_EMAIL
                )
            ],
            [
                InlineKeyboardButton(
                    get_text("back_to_profile", language_code),
                    callback_data=PROFILE_CB
                )
            ],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text=text, reply_markup=reply_markup)
        return SELECTING_ACTION
    
    try:
        # Update user's email
        update_user(user_id, {"email": email})
        text = get_text("email_updated", language_code)
    except Exception as e:
        logger.error(f"Error updating email for user {user_id}: {e}")
        text = get_text("error_general", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_profile", language_code),
                callback_data=PROFILE_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_auth
async def save_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save user's phone number."""
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    phone = update.message.text
    
    # Basic phone validation (allow only digits and +)
    if not all(c.isdigit() or c == "+" for c in phone):
        text = get_text("invalid_phone", language_code)
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("try_again", language_code),
                    callback_data=EDIT_PHONE
                )
            ],
            [
                InlineKeyboardButton(
                    get_text("back_to_profile", language_code),
                    callback_data=PROFILE_CB
                )
            ],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text=text, reply_markup=reply_markup)
        return SELECTING_ACTION
    
    try:
        # Update user's phone
        update_user(user_id, {"phone": phone})
        text = get_text("phone_updated", language_code)
    except Exception as e:
        logger.error(f"Error updating phone for user {user_id}: {e}")
        text = get_text("error_general", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_profile", language_code),
                callback_data=PROFILE_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_auth
async def view_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user's traffic usage."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user's traffic usage
    traffic = get_user_traffic(user_id)
    
    if not traffic:
        text = get_text("no_traffic_data", language_code)
    else:
        text = get_text("traffic_usage", language_code).format(
            total_used=format_number(traffic["total_used"], language_code),
            total_limit=format_number(traffic["total_limit"], language_code),
            percent=format_number(traffic["usage_percent"], language_code)
        )
        
        # Add per-account breakdown
        text += "\n\n" + get_text("account_breakdown", language_code)
        for account in traffic["accounts"]:
            text += "\n" + get_text("account_traffic_item", language_code).format(
                id=account["id"],
                used=format_number(account["used"], language_code),
                limit=format_number(account["limit"], language_code),
                percent=format_number(account["percent"], language_code)
            )
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_profile", language_code),
                callback_data=PROFILE_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_auth
async def view_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user's account settings."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user settings
    user = get_user(user_id)
    available_languages = get_available_languages()
    
    text = get_text("account_settings_info", language_code).format(
        language=available_languages.get(user["language"], "English"),
        notifications="✓" if user.get("notifications_enabled", True) else "✗",
        auto_renew="✓" if user.get("auto_renew", False) else "✗"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("change_language", language_code),
                callback_data=LANGUAGE_CB
            )
        ],
        [
            InlineKeyboardButton(
                get_text("notification_settings", language_code),
                callback_data=NOTIFICATIONS_CB
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_profile", language_code),
                callback_data=PROFILE_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

def get_user_handler() -> ConversationHandler:
    """Create and return the user management conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("profile", profile_menu),
            CallbackQueryHandler(profile_menu, pattern=f"^{PROFILE_CB}$"),
        ],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(edit_name, pattern=f"^{EDIT_NAME}$"),
                CallbackQueryHandler(edit_email, pattern=f"^{EDIT_EMAIL}$"),
                CallbackQueryHandler(edit_phone, pattern=f"^{EDIT_PHONE}$"),
                CallbackQueryHandler(view_traffic, pattern=f"^{VIEW_TRAFFIC}$"),
                CallbackQueryHandler(view_settings, pattern=f"^{VIEW_SETTINGS}$"),
            ],
            ENTERING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_name),
                CallbackQueryHandler(profile_menu, pattern=f"^{PROFILE_CB}$"),
            ],
            ENTERING_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_email),
                CallbackQueryHandler(profile_menu, pattern=f"^{PROFILE_CB}$"),
            ],
            ENTERING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_phone),
                CallbackQueryHandler(profile_menu, pattern=f"^{PROFILE_CB}$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(profile_menu, pattern="^menu$"),
            CommandHandler("cancel", profile_menu),
        ],
        name="users",
        persistent=False,
        per_message=False
    ) 