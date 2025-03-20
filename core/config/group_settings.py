"""
Notification Group Settings.

This module contains handlers for managing notification group settings.
"""

import logging
from typing import List, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler, CallbackContext

from utils import get_text
from decorators import require_admin
from .constants import ADMIN_MENU, SELECTING_GROUP, ENTERING_GROUP_ID
from .notification_groups import (
    GROUP_MANAGEMENT,
    GROUP_REPORTS,
    GROUP_LOGS,
    GROUP_TRANSACTIONS,
    GROUP_OUTAGES,
    GROUP_SELLERS,
    GROUP_BACKUPS,
)

logger = logging.getLogger(__name__)

# States
ADDING_GROUP = 1
EDITING_GROUP = 2
SELECTING_GROUP_TYPE = 3
CONFIRM_DELETE_GROUP = 4

# Notification group types with proper emoji
GROUP_TYPES = {
    GROUP_MANAGEMENT: "🛡️ مدیریت اصلی",
    GROUP_REPORTS: "📊 گزارشات",
    GROUP_LOGS: "📄 لاگ ربات",
    GROUP_TRANSACTIONS: "💰 تراکنش‌ها",
    GROUP_OUTAGES: "⚠️ اختلالات و قطعی",
    GROUP_SELLERS: "👥 فروشندگان",
    GROUP_BACKUPS: "💾 بک‌آپ‌ها",
}

# Mock API - Replace with actual API calls
async def get_notification_groups() -> List[Dict[str, Any]]:
    """Get all notification groups."""
    # This should be replaced with an actual API call
    return [
        {"id": 1, "type": GROUP_MANAGEMENT, "name": GROUP_TYPES[GROUP_MANAGEMENT], "chat_id": "-100123456789"},
        {"id": 2, "type": GROUP_TRANSACTIONS, "name": GROUP_TYPES[GROUP_TRANSACTIONS], "chat_id": "-100987654321"},
        {"id": 3, "type": GROUP_LOGS, "name": GROUP_TYPES[GROUP_LOGS], "chat_id": "-100123123123"}
    ]

async def add_notification_group(group_type: str, chat_id: str) -> Dict[str, Any]:
    """Add a new notification group."""
    # This should be replaced with an actual API call
    return {"success": True, "id": 4, "type": group_type, "name": GROUP_TYPES.get(group_type, "نامشخص"), "chat_id": chat_id}

async def update_notification_group(group_id: int, group_type: str = None, chat_id: str = None) -> Dict[str, Any]:
    """Update an existing notification group."""
    # This should be replaced with an actual API call
    return {"success": True}

async def delete_notification_group(group_id: int) -> Dict[str, Any]:
    """Delete a notification group."""
    # This should be replaced with an actual API call
    return {"success": True}

@require_admin
async def group_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the notification group settings menu."""
    query = update.callback_query
    
    if query:
        await query.answer()
    
    groups = await get_notification_groups()
    
    message = "👥 *تنظیمات گروه‌های اطلاع‌رسانی*\n\n"
    message += "از این بخش می‌توانید گروه‌های تلگرامی را برای دریافت اعلان‌های مختلف مدیریت کنید.\n\n"
    message += "گروه‌های اطلاع‌رسانی موجود:\n\n"
    
    if not groups:
        message += "هیچ گروهی تنظیم نشده است.\n"
    else:
        for group in groups:
            message += f"• *{group['name']}*: `{group['chat_id']}`\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن گروه جدید", callback_data="add_notification_group")]
    ]
    
    # Add buttons for each group
    for group in groups:
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ {group['name']}", 
                callback_data=f"edit_notification_group:{group['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی مدیریت", callback_data=ADMIN_MENU)])
    
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
    
    return SELECTING_GROUP

@require_admin
async def add_notification_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process of adding a new notification group."""
    query = update.callback_query
    await query.answer()
    
    message = "🔔 *افزودن گروه اطلاع‌رسانی جدید*\n\n"
    message += "لطفاً نوع گروه را انتخاب کنید:"
    
    keyboard = []
    for group_type, name in GROUP_TYPES.items():
        keyboard.append([
            InlineKeyboardButton(name, callback_data=f"select_group_type:{group_type}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="group_settings")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_GROUP_TYPE

@require_admin
async def select_group_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle group type selection."""
    query = update.callback_query
    await query.answer()
    
    group_type = query.data.split(":")[-1]
    group_name = GROUP_TYPES.get(group_type, "نامشخص")
    
    # Store selected group type in context
    context.user_data["selected_group_type"] = group_type
    
    message = f"🔔 *افزودن گروه {group_name}*\n\n"
    message += "ربات باید در گروه موردنظر افزوده شده باشد.\n\n"
    message += "لطفاً شناسه گروه تلگرام را وارد کنید (مثال: -100123456789):\n"
    message += "یا لینک دعوت گروه را ارسال کنید."
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="group_settings")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ENTERING_GROUP_ID

@require_admin
async def enter_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the entered group ID."""
    # Get the group ID from the message
    text = update.message.text.strip()
    
    # Try to extract chat ID from invite link or direct ID input
    chat_id = text
    if "t.me/" in text or "telegram.me/" in text:
        # This is a simplified version - in real implementation, 
        # you would need to handle invite links correctly
        await update.message.reply_text(
            "❌ لینک دعوت مستقیماً قابل استفاده نیست. لطفاً شناسه عددی گروه را وارد کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="group_settings")]
            ])
        )
        return SELECTING_GROUP
    
    # Get the group type from context
    group_type = context.user_data.get("selected_group_type")
    
    if not group_type:
        await update.message.reply_text(
            "❌ خطا: نوع گروه یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="group_settings")]
            ])
        )
        return SELECTING_GROUP
    
    # Add the group to the database
    result = await add_notification_group(group_type, chat_id)
    
    if result.get("success", False):
        # Send a test message to the group to confirm bot has access
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔔 *پیام آزمایشی اطلاع‌رسانی*\n\n"
                     "این پیام برای تأیید دسترسی ربات به گروه اطلاع‌رسانی ارسال شده است.\n\n"
                     f"نوع گروه: {GROUP_TYPES.get(group_type, 'نامشخص')}\n"
                     f"شناسه گروه: `{chat_id}`",
                parse_mode=ParseMode.MARKDOWN
            )
            
            success_message = (
                f"✅ گروه اطلاع‌رسانی *{GROUP_TYPES.get(group_type, 'نامشخص')}* با موفقیت اضافه شد!\n\n"
                f"یک پیام آزمایشی به گروه ارسال شد."
            )
        except Exception as e:
            logger.error(f"Failed to send test message to group {chat_id}: {str(e)}")
            success_message = (
                f"⚠️ گروه اطلاع‌رسانی *{GROUP_TYPES.get(group_type, 'نامشخص')}* اضافه شد، "
                f"اما پیام آزمایشی ارسال نشد. لطفاً مطمئن شوید که ربات در گروه عضو است و دسترسی ارسال پیام دارد."
            )
    else:
        success_message = f"❌ خطا در افزودن گروه اطلاع‌رسانی: {result.get('message', 'خطای نامشخص')}"
    
    # Clear context data
    if "selected_group_type" in context.user_data:
        del context.user_data["selected_group_type"]
    
    await update.message.reply_text(
        success_message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به تنظیمات گروه", callback_data="group_settings")]
        ]),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_GROUP

@require_admin
async def edit_notification_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Edit an existing notification group."""
    query = update.callback_query
    await query.answer()
    
    group_id = int(query.data.split(":")[-1])
    
    # Get all groups
    groups = await get_notification_groups()
    
    # Find the group with the specified ID
    selected_group = None
    for group in groups:
        if group["id"] == group_id:
            selected_group = group
            break
    
    if not selected_group:
        await query.edit_message_text(
            "❌ گروه مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="group_settings")]
            ])
        )
        return SELECTING_GROUP
    
    # Store group ID in context
    context.user_data["editing_group_id"] = group_id
    
    message = (
        f"✏️ *ویرایش گروه {selected_group['name']}*\n\n"
        f"• نوع: {selected_group['name']}\n"
        f"• شناسه گروه: `{selected_group['chat_id']}`\n\n"
        "چه تغییری می‌خواهید اعمال کنید؟"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 تغییر نوع گروه", callback_data="change_group_type")],
        [InlineKeyboardButton("🆔 تغییر شناسه گروه", callback_data="change_group_id")],
        [InlineKeyboardButton("❌ حذف گروه", callback_data=f"delete_notification_group:{group_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="group_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return EDITING_GROUP

@require_admin
async def change_group_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Change the type of an existing notification group."""
    query = update.callback_query
    await query.answer()
    
    group_id = context.user_data.get("editing_group_id")
    
    if not group_id:
        await query.edit_message_text(
            "❌ خطا: اطلاعات گروه یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="group_settings")]
            ])
        )
        return SELECTING_GROUP
    
    message = "🔄 *تغییر نوع گروه*\n\n"
    message += "لطفاً نوع جدید گروه را انتخاب کنید:"
    
    keyboard = []
    for group_type, name in GROUP_TYPES.items():
        keyboard.append([
            InlineKeyboardButton(
                name, 
                callback_data=f"update_group_type:{group_id}:{group_type}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت", 
            callback_data=f"edit_notification_group:{group_id}"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return EDITING_GROUP

@require_admin
async def update_group_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Update the group type in the database."""
    query = update.callback_query
    await query.answer()
    
    # Extract group ID and new type from callback data
    parts = query.data.split(":")
    group_id = int(parts[1])
    new_type = parts[2]
    
    # Update the group in the database
    result = await update_notification_group(group_id, group_type=new_type)
    
    if result.get("success", False):
        message = f"✅ نوع گروه با موفقیت به *{GROUP_TYPES.get(new_type, 'نامشخص')}* تغییر یافت."
    else:
        message = f"❌ خطا در تغییر نوع گروه: {result.get('message', 'خطای نامشخص')}"
    
    keyboard = [
        [InlineKeyboardButton("✏️ ادامه ویرایش", callback_data=f"edit_notification_group:{group_id}")],
        [InlineKeyboardButton("🔙 بازگشت به تنظیمات گروه", callback_data="group_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return EDITING_GROUP

@require_admin
async def delete_notification_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm deletion of a notification group."""
    query = update.callback_query
    await query.answer()
    
    group_id = int(query.data.split(":")[-1])
    
    # Get all groups
    groups = await get_notification_groups()
    
    # Find the group with the specified ID
    selected_group = None
    for group in groups:
        if group["id"] == group_id:
            selected_group = group
            break
    
    if not selected_group:
        await query.edit_message_text(
            "❌ گروه مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="group_settings")]
            ])
        )
        return SELECTING_GROUP
    
    message = (
        f"❌ *حذف گروه {selected_group['name']}*\n\n"
        f"آیا از حذف این گروه اطلاع‌رسانی اطمینان دارید؟\n\n"
        f"• نوع: {selected_group['name']}\n"
        f"• شناسه گروه: `{selected_group['chat_id']}`\n\n"
        "⚠️ این عملیات غیرقابل بازگشت است."
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"confirm_delete_group:{group_id}"),
            InlineKeyboardButton("❌ خیر، انصراف", callback_data=f"edit_notification_group:{group_id}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return CONFIRM_DELETE_GROUP

@require_admin
async def confirm_delete_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the confirmation of group deletion."""
    query = update.callback_query
    await query.answer()
    
    group_id = int(query.data.split(":")[-1])
    
    # Delete the group from the database
    result = await delete_notification_group(group_id)
    
    if result.get("success", False):
        message = "✅ گروه اطلاع‌رسانی با موفقیت حذف شد."
    else:
        message = f"❌ خطا در حذف گروه: {result.get('message', 'خطای نامشخص')}"
    
    # Clear context data
    if "editing_group_id" in context.user_data:
        del context.user_data["editing_group_id"]
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به تنظیمات گروه", callback_data="group_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_GROUP

class group_settings_handlers:
    """Container for group settings handlers."""
    
    handlers = [
        # Main settings menu
        (r"^group_settings$", group_settings_menu),
        
        # Adding new groups
        (r"^add_notification_group$", add_notification_group),
        (r"^select_group_type:(.+)$", select_group_type),
        
        # Editing groups
        (r"^edit_notification_group:(\d+)$", edit_notification_group),
        (r"^change_group_type$", change_group_type),
        (r"^update_group_type:(\d+):(.+)$", update_group_type),
        
        # Deleting groups
        (r"^delete_notification_group:(\d+)$", delete_notification_group),
        (r"^confirm_delete_group:(\d+)$", confirm_delete_group),
    ]
    
    # Export the menu function for use in __init__.py
    group_settings_menu = group_settings_menu 