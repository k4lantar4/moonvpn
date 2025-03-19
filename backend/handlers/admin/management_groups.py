"""
Management groups handlers for MoonVPN Telegram Bot.

This module handles adding, editing, and configuring management groups
for the bot to send various notifications.
"""

import logging
import datetime
from typing import List, Dict, Any, Optional, Union, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

from models.groups import BotManagementGroup
from core.utils.helpers import is_admin
from core.utils.helpers import extract_user_data
from services.notification_service import notification_service
from core.utils.helpers import management_group_access
from core.handlers.bot.admin.constants import NOTIFICATION_TYPES

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_ACTION = 0
ADDING_GROUP = 1
ADDING_DESCRIPTION = 2
ADDING_ICON = 3
SELECTING_NOTIFICATIONS = 4
SELECTING_GROUP_TO_EDIT = 5
EDITING_GROUP = 6
EDITING_ICON = 7
EDITING_DESCRIPTION = 8
REMOVING_GROUP = 9
CONFIRMING_REMOVE = 10

# Callback data patterns
ACTION_ADD = "management_group_add"
ACTION_LIST = "management_group_list"
ACTION_EDIT = "management_group_edit"
ACTION_REMOVE = "management_group_remove"
ACTION_TEST = "management_group_test"
ACTION_CANCEL = "management_group_cancel"
SELECT_GROUP = "select_group"
EDIT_GROUP = "edit_group"
EDIT_ICON = "edit_icon"
EDIT_DESC = "edit_desc"
TOGGLE_ACTIVE = "toggle_active"
REMOVE_GROUP = "remove_group"
CONFIRM_REMOVE = "confirm_remove"
CANCEL_REMOVE = "cancel_remove"
NOTIFICATION_TOGGLE = "notification_toggle"

@management_group_access(["ACCESS_MANAGEMENT"])
async def management_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Command handler for /management_groups
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    user = update.effective_user
    
    # Check if user is admin
    if not await is_admin(user.id):
        await update.message.reply_text(
            "⛔️ شما دسترسی به این بخش را ندارید."
        )
        return ConversationHandler.END
        
    # Show main menu
    await show_main_menu(update, context)
    return SELECTING_ACTION

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main menu for management groups.
    
    Args:
        update: The update object.
        context: The context object.
    """
    keyboard = [
        [
            InlineKeyboardButton("➕ افزودن گروه جدید", callback_data=ACTION_ADD),
            InlineKeyboardButton("📋 لیست گروه‌ها", callback_data=ACTION_LIST)
        ],
        [
            InlineKeyboardButton("✏️ ویرایش گروه", callback_data=ACTION_EDIT),
            InlineKeyboardButton("❌ حذف گروه", callback_data=ACTION_REMOVE)
        ],
        [
            InlineKeyboardButton("🧪 ارسال پیام تست", callback_data=ACTION_TEST),
            InlineKeyboardButton("🚫 انصراف", callback_data=ACTION_CANCEL)
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = (
        "🔔 <b>مدیریت گروه‌های اطلاع‌رسانی</b>\n\n"
        "از این بخش می‌توانید گروه‌های مختلف برای دریافت اعلان‌های مختلف "
        "سیستم را تنظیم کنید.\n\n"
        "یک گزینه را انتخاب کنید:"
    )
    
    # Check if this is from a callback or message
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            text=message_text, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle selection from the main menu.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == ACTION_ADD:
        return await start_add_group(update, context)
    elif action == ACTION_LIST:
        return await list_groups(update, context)
    elif action == ACTION_EDIT:
        return await edit_group_start(update, context)
    elif action == ACTION_REMOVE:
        return await remove_group_start(update, context)
    elif action == ACTION_TEST:
        return await start_test_message(update, context)
    elif action == ACTION_CANCEL:
        await query.edit_message_text("❌ عملیات مدیریت گروه‌ها لغو شد.")
        return ConversationHandler.END
        
    return SELECTING_ACTION

async def start_add_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process of adding a new management group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    
    await query.edit_message_text(
        "➕ <b>افزودن گروه جدید</b>\n\n"
        "لطفاً ربات را به گروه مورد نظر اضافه کرده و سپس یک پیام از آن گروه را به اینجا فوروارد کنید.\n\n"
        "برای انصراف، /cancel را ارسال کنید.",
        parse_mode=ParseMode.HTML
    )
    
    return ADDING_GROUP

async def add_group_from_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process a forwarded message to add a new management group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    message = update.message
    user = update.effective_user
    
    # Check if the message is forwarded
    if not message.forward_from_chat:
        await message.reply_text(
            "❌ پیام باید از یک گروه فوروارد شده باشد. لطفاً دوباره امتحان کنید یا /cancel را ارسال کنید."
        )
        return ADDING_GROUP
        
    # Get chat information
    chat = message.forward_from_chat
    
    # Check if chat is a group or channel
    if chat.type not in ["group", "supergroup", "channel"]:
        await message.reply_text(
            "❌ پیام باید از یک گروه یا کانال فوروارد شده باشد. لطفاً دوباره امتحان کنید یا /cancel را ارسال کنید."
        )
        return ADDING_GROUP
        
    # Check if group already exists
    existing_group = await BotManagementGroup.filter(chat_id=chat.id).first()
    if existing_group:
        await message.reply_text(
            f"❌ این گروه قبلاً به عنوان گروه مدیریتی اضافه شده است.\n\n"
            f"نام گروه: {existing_group.title}\n"
            f"وضعیت: {'فعال' if existing_group.is_active else 'غیرفعال'}"
        )
        return ADDING_GROUP
        
    # Store chat information in user data
    context.user_data["new_group"] = {
        "chat_id": chat.id,
        "title": chat.title,
        "username": chat.username,
        "link": chat.invite_link,
        "type": chat.type,
        "notification_types": []
    }
    
    # Ask for description
    await message.reply_text(
        "✅ گروه شناسایی شد:\n\n"
        f"نام: {chat.title}\n"
        f"نوع: {chat.type}\n\n"
        "لطفاً یک توضیح کوتاه برای این گروه وارد کنید (مثلاً: گروه اطلاع‌رسانی پرداخت‌ها).\n\n"
        "برای انصراف، /cancel را ارسال کنید."
    )
    
    return ADDING_DESCRIPTION

async def add_group_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the description for a new management group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    description = update.message.text
    
    if "new_group" not in context.user_data:
        await update.message.reply_text("❌ خطا در فرآیند افزودن گروه. لطفاً دوباره شروع کنید.")
        return ConversationHandler.END
        
    # Store description in user data
    context.user_data["new_group"]["description"] = description
    
    # Ask for icon
    await update.message.reply_text(
        "✅ توضیحات ذخیره شد.\n\n"
        "لطفاً یک ایموجی به عنوان آیکون گروه ارسال کنید. این ایموجی قبل از هر پیام ارسالی به گروه نمایش داده می‌شود.\n\n"
        "مثال: 💰 یا 📊 یا 🔔\n\n"
        "برای انصراف، /cancel را ارسال کنید."
    )
    
    return ADDING_ICON

async def add_group_icon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the icon for a new management group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    icon = update.message.text.strip()
    
    if len(icon) > 2:
        await update.message.reply_text(
            "❌ آیکون باید فقط یک ایموجی باشد. لطفاً دوباره امتحان کنید."
        )
        return ADDING_ICON
        
    if "new_group" not in context.user_data:
        await update.message.reply_text("❌ خطا در فرآیند افزودن گروه. لطفاً دوباره شروع کنید.")
        return ConversationHandler.END
        
    # Store icon in user data
    context.user_data["new_group"]["icon"] = icon
    
    # Ask for notification types
    await show_notification_types(update, context)
    
    return SELECTING_NOTIFICATIONS

async def show_notification_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show notification type selection options.
    
    Args:
        update: The update object.
        context: The context object.
    """
    # Get selected notification types
    selected_types = context.user_data["new_group"].get("notification_types", [])
    
    # Create keyboard with notification types
    keyboard = []
    for notification_type, notification_info in NOTIFICATION_TYPES.items():
        # Check if this type is selected
        is_selected = notification_type in selected_types
        status = "✅" if is_selected else "❌"
        
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {notification_info['icon']} {notification_info['name']}", 
                callback_data=f"{NOTIFICATION_TOGGLE}_{notification_type}"
            )
        ])
        
    # Add save button
    keyboard.append([
        InlineKeyboardButton("💾 ذخیره و ادامه", callback_data="save_notifications")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # If this is an update to an existing message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🔔 لطفاً انواع اعلان‌هایی که می‌خواهید به این گروه ارسال شود را انتخاب کنید:\n\n"
            "برای افزودن یا حذف هر نوع اعلان، روی آن کلیک کنید. سپس 'ذخیره و ادامه' را بزنید.\n\n"
            "<i>توضیح: گروه‌های مدیریتی می‌توانند انواع مختلفی از اعلان‌ها را دریافت کنند.</i>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        # Send as a new message
        await update.message.reply_text(
            "🔔 لطفاً انواع اعلان‌هایی که می‌خواهید به این گروه ارسال شود را انتخاب کنید:\n\n"
            "برای افزودن یا حذف هر نوع اعلان، روی آن کلیک کنید. سپس 'ذخیره و ادامه' را بزنید.\n\n"
            "<i>توضیح: گروه‌های مدیریتی می‌توانند انواع مختلفی از اعلان‌ها را دریافت کنند.</i>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def toggle_notification_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle selection of a notification type.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    # Check if data includes notification toggle
    if not query.data.startswith(f"{NOTIFICATION_TOGGLE}_"):
        return SELECTING_NOTIFICATIONS
        
    notification_type = query.data.split("_")[-1]
    
    # Toggle this notification type
    if "new_group" not in context.user_data:
        context.user_data["new_group"] = {"notification_types": []}
        
    if "notification_types" not in context.user_data["new_group"]:
        context.user_data["new_group"]["notification_types"] = []
        
    selected_types = context.user_data["new_group"]["notification_types"]
    
    if notification_type in selected_types:
        selected_types.remove(notification_type)
    else:
        selected_types.append(notification_type)
        
    # Update display
    await show_notification_types(update, context)
    
    return SELECTING_NOTIFICATIONS

async def save_management_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the new management group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    if "new_group" not in context.user_data:
        await query.edit_message_text(
            "❌ خطا در فرآیند افزودن گروه. لطفاً دوباره شروع کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 شروع مجدد", callback_data="back_to_main")]
            ])
        )
        return ConversationHandler.END
        
    new_group_data = context.user_data["new_group"]
    
    # Check required fields
    required_fields = ["chat_id", "title", "icon", "description"]
    missing_fields = [field for field in required_fields if field not in new_group_data]
    
    if missing_fields:
        missing_str = ", ".join(missing_fields)
        await query.edit_message_text(
            f"❌ اطلاعات ناقص است. فیلدهای زیر الزامی هستند:\n{missing_str}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 شروع مجدد", callback_data="back_to_main")]
            ])
        )
        return ConversationHandler.END
    
    # Ensure notification types exists (default to empty list)
    if "notification_types" not in new_group_data:
        new_group_data["notification_types"] = []
    
    try:
        # Create a new group
        new_group = BotManagementGroup(
            chat_id=new_group_data["chat_id"],
            title=new_group_data["title"],
            description=new_group_data["description"],
            icon=new_group_data["icon"],
            added_by=extract_user_data(update.effective_user),
            notification_types=new_group_data["notification_types"],
            is_active=True
        )
        
        # Save to database
        await new_group.save()
        
        # Format notification types for display
        notification_types_str = "هیچ"
        if new_group_data["notification_types"]:
            notification_types = []
            for n_type in new_group_data["notification_types"]:
                if n_type in NOTIFICATION_TYPES:
                    notification_types.append(f"{NOTIFICATION_TYPES[n_type]['icon']} {NOTIFICATION_TYPES[n_type]['name']}")
            
            if notification_types:
                notification_types_str = "\n• " + "\n• ".join(notification_types)
        
        # Send success message
        await query.edit_message_text(
            f"✅ گروه مدیریتی با موفقیت اضافه شد:\n\n"
            f"• عنوان: {new_group_data['title']}\n"
            f"• شناسه: {new_group_data['chat_id']}\n"
            f"• آیکون: {new_group_data['icon']}\n"
            f"• توضیحات: {new_group_data['description']}\n"
            f"• اعلان‌ها: {notification_types_str}\n\n"
            f"این گروه اکنون اعلان‌های انتخاب شده را دریافت خواهد کرد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ]),
            parse_mode=ParseMode.HTML
        )
        
        # Clean up user data
        if "new_group" in context.user_data:
            del context.user_data["new_group"]
            
        # Send a welcome message to the group
        try:
            bot = context.bot
            group_id = new_group_data["chat_id"]
            
            welcome_message = (
                f"{new_group_data['icon']} <b>گروه مدیریتی MoonVPN</b>\n\n"
                f"این گروه به عنوان یک گروه مدیریتی در ربات MoonVPN ثبت شد.\n\n"
                f"<b>عنوان:</b> {new_group_data['title']}\n"
                f"<b>توضیحات:</b> {new_group_data['description']}\n\n"
                f"<b>اعلان‌های فعال:</b>\n"
            )
            
            if new_group_data["notification_types"]:
                for n_type in new_group_data["notification_types"]:
                    if n_type in NOTIFICATION_TYPES:
                        welcome_message += f"• {NOTIFICATION_TYPES[n_type]['icon']} {NOTIFICATION_TYPES[n_type]['name']}: {NOTIFICATION_TYPES[n_type]['desc']}\n"
            else:
                welcome_message += "• هیچ اعلانی فعال نیست.\n"
                
            welcome_message += "\n✅ از این پس، اعلان‌های انتخاب شده به این گروه ارسال خواهند شد."
            
            await bot.send_message(
                chat_id=group_id,
                text=welcome_message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error sending welcome message to group {group_id}: {e}")
            # This is not a critical error, so we continue
        
        return SELECTING_ACTION
        
    except Exception as e:
        logger.error(f"Error saving management group: {e}")
        await query.edit_message_text(
            f"❌ خطا در ذخیره گروه مدیریتی: {str(e)}\n\n"
            f"لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ])
        )
        return SELECTING_ACTION

async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """List all management groups.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    try:
        # Get all groups
        groups = await BotManagementGroup.all()
        
        if not groups:
            await query.edit_message_text(
                "❌ هیچ گروه مدیریتی یافت نشد. ابتدا باید حداقل یک گروه اضافه کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ افزودن گروه جدید", callback_data=ACTION_ADD)],
                    [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                ])
            )
            return SELECTING_ACTION
            
        # Build message with group list
        message_text = "📋 <b>لیست گروه‌های مدیریتی</b>\n\n"
        
        for group in groups:
            # Format notification types
            notification_types = []
            if group.notification_types:
                for n_type in group.notification_types:
                    if n_type in NOTIFICATION_TYPES:
                        notification_types.append(f"{NOTIFICATION_TYPES[n_type]['icon']} {NOTIFICATION_TYPES[n_type]['name']}")
            
            notification_types_str = "هیچ" if not notification_types else ", ".join(notification_types)
            
            # Format status
            status = "✅ فعال" if group.is_active else "❌ غیرفعال"
            
            message_text += (
                f"<b>{group.icon} {group.title}</b> (ID: <code>{group.chat_id}</code>)\n"
                f"   وضعیت: {status}\n"
                f"   توضیحات: {group.description or '-'}\n"
                f"   اعلان‌ها: {notification_types_str}\n\n"
            )
            
        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
        return SELECTING_ACTION
    except Exception as e:
        logger.error(f"Error listing management groups: {e}")
        await query.edit_message_text(
            f"❌ خطا در دریافت لیست گروه‌های مدیریتی: {str(e)}\n\n"
            f"لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ])
        )
        return SELECTING_ACTION

async def start_test_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process of sending a test message to management groups.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    
    # Get all active management groups
    try:
        groups = await BotManagementGroup.filter(is_active=True).all()
        
        if not groups:
            await query.edit_message_text(
                "❌ هیچ گروه مدیریتی فعالی یافت نشد. ابتدا باید حداقل یک گروه فعال اضافه کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                ])
            )
            return SELECTING_ACTION
            
        # Create keyboard with group list
        keyboard = []
        for group in groups:
            keyboard.append([
                InlineKeyboardButton(
                    f"{group.icon} {group.title}", 
                    callback_data=f"{SELECT_GROUP}_{group.id}"
                )
            ])
            
        # Add all groups option and back button
        keyboard.append([InlineKeyboardButton("🔔 ارسال به همه گروه‌ها", callback_data=f"{SELECT_GROUP}_all")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🧪 <b>ارسال پیام تست</b>\n\n"
            "لطفاً گروه مورد نظر برای ارسال پیام تست را انتخاب کنید:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return SELECTING_ACTION
    except Exception as e:
        logger.error(f"Error getting management groups for test message: {e}")
        await query.edit_message_text(
            f"❌ خطا در دریافت لیست گروه‌های مدیریتی: {str(e)}\n\n"
            f"لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ])
        )
        return SELECTING_ACTION

async def send_test_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a test message to the selected group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    # Get group ID from callback data
    callback_data = query.data
    
    if not callback_data.startswith(f"{SELECT_GROUP}_"):
        return SELECTING_ACTION
        
    group_id = callback_data.split("_")[-1]
    
    try:
        if group_id == "all":
            # Send to all active groups
            groups = await BotManagementGroup.filter(is_active=True).all()
            
            if not groups:
                await query.edit_message_text(
                    "❌ هیچ گروه مدیریتی فعالی یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                    ])
                )
                return SELECTING_ACTION
                
            # Send test message to each group
            success_count = 0
            error_count = 0
            
            for group in groups:
                try:
                    test_message = (
                        f"{group.icon} <b>پیام تست</b>\n\n"
                        f"این یک پیام تست از ربات MoonVPN است.\n\n"
                        f"اطلاعات گروه:\n"
                        f"🏷 نام: {group.title}\n"
                        f"🆔 شناسه: <code>{group.chat_id}</code>\n"
                        f"⏱ زمان: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    
                    success = await notification_service._send_message_to_chat(
                        chat_id=group.chat_id,
                        message=test_message,
                        parse_mode=ParseMode.HTML
                    )
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"Error sending test message to group {group.title}: {e}")
                    error_count += 1
                    
            # Show result
            await query.edit_message_text(
                f"✅ نتیجه ارسال پیام تست به همه گروه‌ها:\n\n"
                f"✓ موفق: {success_count}\n"
                f"✗ ناموفق: {error_count}\n\n"
                f"تعداد کل گروه‌ها: {len(groups)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                ])
            )
                
        else:
            # Send to specific group
            group = await BotManagementGroup.get(id=int(group_id))
            
            test_message = (
                f"{group.icon} <b>پیام تست</b>\n\n"
                f"این یک پیام تست از ربات MoonVPN است.\n\n"
                f"اطلاعات گروه:\n"
                f"🏷 نام: {group.title}\n"
                f"🆔 شناسه: <code>{group.chat_id}</code>\n"
                f"📝 توضیحات: {group.description or '-'}\n"
                f"🔔 انواع اعلان‌ها: {', '.join(group.notification_types) or 'هیچ‌کدام'}\n"
                f"⏱ زمان: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            success = await notification_service._send_message_to_chat(
                chat_id=group.chat_id,
                message=test_message,
                parse_mode=ParseMode.HTML
            )
            
            if success:
                await query.edit_message_text(
                    f"✅ پیام تست با موفقیت به گروه «{group.title}» ارسال شد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                    ])
                )
            else:
                await query.edit_message_text(
                    f"❌ خطا در ارسال پیام تست به گروه «{group.title}».\n\n"
                    f"لطفاً بررسی کنید که ربات در گروه حضور داشته باشد و دسترسی ارسال پیام داشته باشد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                    ])
                )
                
    except Exception as e:
        logger.error(f"Error sending test message: {e}")
        await query.edit_message_text(
            f"❌ خطا در ارسال پیام تست: {str(e)}\n\n"
            f"لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ])
        )
        
    return SELECTING_ACTION

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command to exit conversation.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    # Clear any stored data
    if "new_group" in context.user_data:
        del context.user_data["new_group"]
        
    await update.message.reply_text(
        "❌ عملیات لغو شد. می‌توانید با دستور /management_groups دوباره شروع کنید."
    )
    
    return ConversationHandler.END

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to the main menu.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    await show_main_menu(update, context)
    return SELECTING_ACTION

async def toggle_active_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle active status of a management group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    # Get group ID from callback data
    callback_data = query.data
    
    if not callback_data.startswith(f"{TOGGLE_ACTIVE}_"):
        return EDITING_GROUP
        
    group_id = int(callback_data.split("_")[-1])
    
    try:
        # Get the management group
        group = await BotManagementGroup.get(id=group_id)
        
        # Toggle active status
        group.is_active = not group.is_active
        await group.save()
        
        # Get notification types as string
        notification_types_str = ", ".join(
            NOTIFICATION_TYPES.get(nt, nt) for nt in group.notification_types
        ) or "هیچ‌کدام"
        
        # Create keyboard with edit options
        keyboard = [
            [InlineKeyboardButton(f"✏️ ویرایش آیکون ({group.icon})", callback_data=f"{EDIT_ICON}_{group_id}")],
            [InlineKeyboardButton("✏️ ویرایش توضیحات", callback_data=f"{EDIT_DESC}_{group_id}")],
            [InlineKeyboardButton(
                "🔄 " + ("غیرفعال‌سازی" if group.is_active else "فعال‌سازی"), 
                callback_data=f"{TOGGLE_ACTIVE}_{group_id}"
            )],
            [InlineKeyboardButton("❌ حذف گروه", callback_data=f"{REMOVE_GROUP}_{group_id}")],
            [InlineKeyboardButton("🧪 ارسال پیام تست", callback_data=f"{SELECT_GROUP}_{group_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=ACTION_EDIT)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ وضعیت گروه «{group.title}» با موفقیت {'فعال' if group.is_active else 'غیرفعال'} شد.\n\n"
            f"🆔 شناسه: <code>{group.chat_id}</code>\n"
            f"{group.icon} آیکون: {group.icon}\n"
            f"📝 توضیحات: {group.description or '-'}\n"
            f"🔔 انواع اعلان‌ها: {notification_types_str}\n"
            f"⚙️ وضعیت: {'✅ فعال' if group.is_active else '❌ غیرفعال'}\n\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return EDITING_GROUP
    except Exception as e:
        logger.error(f"Error toggling group status: {e}")
        await query.edit_message_text(
            f"❌ خطا در تغییر وضعیت گروه: {str(e)}\n\n"
            f"لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=ACTION_EDIT)]
            ])
        )
        return SELECTING_ACTION

async def remove_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process of removing a management group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    # Check if this is from main menu or from editing group
    callback_data = query.data
    
    if callback_data == ACTION_REMOVE:
        # From main menu, show all groups
        try:
            groups = await BotManagementGroup.all()
            
            if not groups:
                await query.edit_message_text(
                    "📋 <b>حذف گروه مدیریتی</b>\n\n"
                    "هیچ گروه مدیریتی ثبت نشده است. برای افزودن گروه جدید، از گزینه «افزودن گروه جدید» استفاده کنید.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                    ])
                )
                return SELECTING_ACTION
                
            # Create keyboard with group list
            keyboard = []
            for group in groups:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{group.icon} {group.title} {'✅' if group.is_active else '❌'}", 
                        callback_data=f"{REMOVE_GROUP}_{group.id}"
                    )
                ])
                
            # Add back button
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ <b>حذف گروه مدیریتی</b>\n\n"
                "⚠️ هشدار: حذف گروه مدیریتی باعث توقف ارسال اعلان‌ها به آن گروه خواهد شد.\n\n"
                "لطفاً گروه مورد نظر برای حذف را انتخاب کنید:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            return REMOVING_GROUP
        except Exception as e:
            logger.error(f"Error getting groups for removal: {e}")
            await query.edit_message_text(
                f"❌ خطا در دریافت لیست گروه‌های مدیریتی: {str(e)}\n\n"
                f"لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                ])
            )
            return SELECTING_ACTION
    else:
        # From editing group, get group ID
        if not callback_data.startswith(f"{REMOVE_GROUP}_"):
            return EDITING_GROUP
            
        group_id = int(callback_data.split("_")[-1])
        
        try:
            # Get the management group
            group = await BotManagementGroup.get(id=group_id)
            
            # Store group ID in user data for later use
            context.user_data["removing_group_id"] = group_id
            
            # Show confirmation
            keyboard = [
                [InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"{CONFIRM_REMOVE}_{group_id}")],
                [InlineKeyboardButton("❌ خیر، انصراف", callback_data=f"{CANCEL_REMOVE}")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ <b>حذف گروه مدیریتی: {group.title}</b>\n\n"
                f"آیا مطمئن هستید که می‌خواهید این گروه را حذف کنید؟\n\n"
                f"🆔 شناسه: <code>{group.chat_id}</code>\n"
                f"{group.icon} آیکون: {group.icon}\n"
                f"📝 توضیحات: {group.description or '-'}\n\n"
                f"⚠️ این عملیات قابل بازگشت نیست و باعث توقف ارسال اعلان‌ها به این گروه خواهد شد.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            return CONFIRMING_REMOVE
        except Exception as e:
            logger.error(f"Error getting group for removal: {e}")
            await query.edit_message_text(
                f"❌ خطا در دریافت اطلاعات گروه: {str(e)}\n\n"
                f"لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=ACTION_EDIT)]
                ])
            )
            return SELECTING_ACTION

async def confirm_remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm removal of a management group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    # Get group ID from callback data
    callback_data = query.data
    
    if not callback_data.startswith(f"{REMOVE_GROUP}_"):
        return REMOVING_GROUP
        
    group_id = int(callback_data.split("_")[-1])
    
    try:
        # Get the management group
        group = await BotManagementGroup.get(id=group_id)
        
        # Store group ID in user data for later use
        context.user_data["removing_group_id"] = group_id
        
        # Show confirmation
        keyboard = [
            [InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"{CONFIRM_REMOVE}_{group_id}")],
            [InlineKeyboardButton("❌ خیر، انصراف", callback_data=f"{CANCEL_REMOVE}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ <b>حذف گروه مدیریتی: {group.title}</b>\n\n"
            f"آیا مطمئن هستید که می‌خواهید این گروه را حذف کنید؟\n\n"
            f"🆔 شناسه: <code>{group.chat_id}</code>\n"
            f"{group.icon} آیکون: {group.icon}\n"
            f"📝 توضیحات: {group.description or '-'}\n\n"
            f"⚠️ این عملیات قابل بازگشت نیست و باعث توقف ارسال اعلان‌ها به این گروه خواهد شد.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return CONFIRMING_REMOVE
    except Exception as e:
        logger.error(f"Error getting group for removal confirmation: {e}")
        await query.edit_message_text(
            f"❌ خطا در دریافت اطلاعات گروه: {str(e)}\n\n"
            f"لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ])
        )
        return SELECTING_ACTION

async def final_remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finally remove the management group.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    # Get group ID from callback data
    callback_data = query.data
    
    if not callback_data.startswith(f"{CONFIRM_REMOVE}_"):
        return CONFIRMING_REMOVE
        
    group_id = int(callback_data.split("_")[-1])
    
    try:
        # Get the management group
        group = await BotManagementGroup.get(id=group_id)
        
        # Store group info before deletion
        group_title = group.title
        group_icon = group.icon
        
        # Delete the group
        await group.delete()
        
        # Clear user data
        if "removing_group_id" in context.user_data:
            del context.user_data["removing_group_id"]
            
        # Show confirmation
        await query.edit_message_text(
            f"✅ گروه مدیریتی «{group_title}» با موفقیت حذف شد.\n\n"
            "می‌توانید با دستور /management_groups به منوی مدیریت گروه‌ها بازگردید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ])
        )
        
        return SELECTING_ACTION
    except Exception as e:
        logger.error(f"Error removing group: {e}")
        await query.edit_message_text(
            f"❌ خطا در حذف گروه: {str(e)}\n\n"
            f"لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ])
        )
        return SELECTING_ACTION

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current operation.
    
    Args:
        update: The update object.
        context: The context object.
        
    Returns:
        The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    
    # Clear user data
    if "editing_group_id" in context.user_data:
        del context.user_data["editing_group_id"]
    if "removing_group_id" in context.user_data:
        del context.user_data["removing_group_id"]
        
    # Show confirmation
    await query.edit_message_text(
        "❌ عملیات لغو شد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ])
    )
    
    return SELECTING_ACTION

def get_management_groups_handlers() -> List:
    """Get all handlers related to management groups.
    
    Returns:
        List of handlers.
    """
    management_groups_handler = ConversationHandler(
        entry_points=[CommandHandler("management_groups", management_groups_command)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(handle_menu_selection, pattern=f"^{ACTION_ADD}$|^{ACTION_LIST}$|^{ACTION_EDIT}$|^{ACTION_REMOVE}$|^{ACTION_TEST}$|^{ACTION_CANCEL}$"),
                CallbackQueryHandler(back_to_main_menu, pattern="^back_to_main$"),
                CallbackQueryHandler(send_test_message, pattern=f"^{SELECT_GROUP}_"),
            ],
            ADDING_GROUP: [
                MessageHandler(filters.FORWARDED, add_group_from_forward),
            ],
            ADDING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_group_description),
            ],
            ADDING_ICON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_group_icon),
            ],
            SELECTING_NOTIFICATIONS: [
                CallbackQueryHandler(toggle_notification_type, pattern=f"^{NOTIFICATION_TOGGLE}_"),
                CallbackQueryHandler(save_management_group, pattern="^save_notifications$"),
            ],
            SELECTING_GROUP_TO_EDIT: [
                CallbackQueryHandler(edit_management_group, pattern=f"^{EDIT_GROUP}_"),
                CallbackQueryHandler(back_to_main_menu, pattern="^back_to_main$"),
            ],
            EDITING_GROUP: [
                CallbackQueryHandler(edit_icon_start, pattern=f"^{EDIT_ICON}_"),
                CallbackQueryHandler(edit_description_start, pattern=f"^{EDIT_DESC}_"),
                CallbackQueryHandler(toggle_active_status, pattern=f"^{TOGGLE_ACTIVE}_"),
                CallbackQueryHandler(remove_group_start, pattern=f"^{REMOVE_GROUP}_"),
                CallbackQueryHandler(send_test_message, pattern=f"^{SELECT_GROUP}_"),
                CallbackQueryHandler(edit_group_start, pattern=f"^{ACTION_EDIT}$"),
            ],
            EDITING_ICON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_icon_process),
            ],
            EDITING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_description_process),
            ],
            REMOVING_GROUP: [
                CallbackQueryHandler(confirm_remove_group, pattern=f"^{REMOVE_GROUP}_"),
                CallbackQueryHandler(back_to_main_menu, pattern="^back_to_main$"),
            ],
            CONFIRMING_REMOVE: [
                CallbackQueryHandler(final_remove_group, pattern=f"^{CONFIRM_REMOVE}_"),
                CallbackQueryHandler(cancel_operation, pattern=f"^{CANCEL_REMOVE}$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(cancel_command, pattern=f"^{ACTION_CANCEL}$"),
        ],
        name="management_groups",
        persistent=False,
    )
    
    return [management_groups_handler] 