"""
User management handlers.

This module contains handlers for managing users.
"""

from typing import Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler

from utils import get_text, format_number, format_date
from decorators import require_admin
from api_client import (
    get_users,
    get_user,
    update_user,
    delete_user,
)
from .constants import SELECTING_USER, ADMIN_MENU, USER_MANAGEMENT

@require_admin
async def user_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of users."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Get all users
    users = get_users()
    
    if not users:
        message = get_text("no_users", language_code)
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("back_to_admin", language_code),
                    callback_data=ADMIN_MENU
                )
            ]
        ]
    else:
        message = "👥 لیست کاربران\n\n"
        keyboard = []
        
        for user in users:
            # Format user status
            status_emoji = "🟢" if user.get("is_active", True) else "🔴"
            username = user.get("username", "")
            user_id = user.get("id", "")
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{status_emoji} {username} ({user_id})",
                    callback_data=f"{USER_MANAGEMENT}:{user_id}"
                )
            ])
    
        # Add back button
        keyboard.append([
            InlineKeyboardButton(
                "🔙 بازگشت به پنل مدیریت",
                callback_data=ADMIN_MENU
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_USER

@require_admin
async def user_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user details."""
    query = update.callback_query
    await query.answer()
    
    # Extract user ID from callback data
    user_id = query.data.split(":")[-1]
    
    # Get user details
    user = get_user(user_id)
    
    if not user:
        await query.edit_message_text(
            "❌ کاربر مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست کاربران", callback_data=USER_MANAGEMENT)]
            ])
        )
        return SELECTING_USER
    
    # Format user details
    username = user.get("username", "تنظیم نشده")
    first_name = user.get("first_name", "")
    last_name = user.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    phone = user.get("phone_number", "تنظیم نشده")
    is_active = "فعال ✅" if user.get("is_active", True) else "غیرفعال ❌"
    is_admin = "بله ⭐️" if user.get("is_admin", False) else "خیر"
    joined_date = format_date(user.get("created_at", ""))
    
    # Get user statistics
    accounts_count = user.get("accounts_count", 0)
    active_accounts = user.get("active_accounts_count", 0)
    total_spent = format_number(user.get("total_spent", 0))
    
    # Create message
    message = (
        f"👤 *اطلاعات کاربر*\n\n"
        f"🆔 شناسه: `{user_id}`\n"
        f"👤 نام کاربری: @{username}\n"
        f"📝 نام: {full_name}\n"
        f"📱 تلفن: {phone}\n"
        f"🚦 وضعیت: {is_active}\n"
        f"👑 ادمین: {is_admin}\n"
        f"📅 تاریخ عضویت: {joined_date}\n\n"
        f"📊 *آمار کاربر*\n\n"
        f"🔑 تعداد اکانت‌ها: {accounts_count}\n"
        f"✅ اکانت‌های فعال: {active_accounts}\n"
        f"💰 مجموع خرید: {total_spent} تومان"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 تغییر وضعیت", 
                callback_data=f"user_toggle:{user_id}"
            ),
            InlineKeyboardButton(
                "🔑 اکانت‌ها", 
                callback_data=f"user_accounts:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 افزایش موجودی", 
                callback_data=f"user_add_balance:{user_id}"
            ),
            InlineKeyboardButton(
                "📝 ریست رمز عبور", 
                callback_data=f"user_reset_password:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ حذف کاربر", 
                callback_data=f"user_delete:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به لیست کاربران", 
                callback_data=USER_MANAGEMENT
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_USER

# Placeholder for other user management functions
# These would be implemented similar to the account and payment handlers

# Define handlers list to be imported in __init__.py
handlers = [
    CallbackQueryHandler(user_details, pattern=f"^{USER_MANAGEMENT}:"),
    CallbackQueryHandler(user_list, pattern=f"^{USER_MANAGEMENT}$"),
]

# Create a class to hold the handlers for easier import
class user_handlers:
    handlers = handlers
    user_list = user_list 