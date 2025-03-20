"""
Allowed Groups Management for MoonVPN Telegram Bot.

This module handles the administration of allowed groups where the bot can operate,
providing functionality to add, edit, and remove groups from the allowed list.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

from models.groups import AllowedGroup
from models.users import User
from core.utils.helpers import get_formatted_datetime, chunked_list
from core.utils.helpers import is_admin
from core.utils.i18n import get_text

# Setup logging
logger = logging.getLogger(__name__)

# Conversation states
(
    MAIN_MENU, 
    LIST_GROUPS, 
    ADD_GROUP_START, 
    ADD_GROUP_FROM_FORWARD,
    ADD_GROUP_DESCRIPTION,
    EDIT_GROUP_START,
    EDIT_GROUP_MENU,
    EDIT_DESCRIPTION_START,
    EDIT_DESCRIPTION_SUBMIT,
    REMOVE_GROUP_START,
    CONFIRM_REMOVE_GROUP,
) = range(11)

# Callback data patterns
ALLOWED_GROUP_MENU = "allowed_group_menu"
LIST_ALLOWED_GROUPS = "list_allowed_groups"
ADD_ALLOWED_GROUP = "add_allowed_group"
EDIT_ALLOWED_GROUP = "edit_allowed_group"
TOGGLE_ALLOWED_GROUP = "toggle_allowed_group"
REMOVE_ALLOWED_GROUP = "remove_allowed_group"
CANCEL_OPERATION = "cancel_allowed_group_op"
BACK_TO_MENU = "back_to_allowed_menu"
SELECT_GROUP_TO_EDIT = "select_group_to_edit"
SELECT_GROUP_TO_REMOVE = "select_group_to_remove"
EDIT_GROUP_DESCRIPTION = "edit_group_description"
CONFIRM_GROUP_REMOVE = "confirm_group_remove"
FINAL_GROUP_REMOVE = "final_group_remove"

async def allowed_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler for /allowed_groups command.
    Shows the main menu for allowed groups management.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    user_id = update.effective_user.id
    
    # Check if user is admin
    if not await is_admin(user_id):
        await update.message.reply_text("⛔️ شما دسترسی ادمین ندارید.")
        return ConversationHandler.END
    
    await show_main_menu(update, context)
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show the main menu for allowed groups management.
    
    Args:
        update: The update object
        context: The context object
    """
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("📋 لیست گروه‌های مجاز", callback_data=LIST_ALLOWED_GROUPS)],
        [InlineKeyboardButton("➕ افزودن گروه جدید", callback_data=ADD_ALLOWED_GROUP)],
        [InlineKeyboardButton("✏️ ویرایش گروه‌ها", callback_data=EDIT_ALLOWED_GROUP)],
        [InlineKeyboardButton("🗑 حذف گروه", callback_data=REMOVE_ALLOWED_GROUP)],
        [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message
    text = (
        "🔍 <b>مدیریت گروه‌های مجاز</b>\n\n"
        "از این بخش می‌توانید گروه‌هایی که ربات در آن‌ها فعال است را مدیریت کنید.\n\n"
        "لطفاً یک گزینه را انتخاب کنید:"
    )
    
    # Handle message vs callback query
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle selection from the main menu.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == LIST_ALLOWED_GROUPS:
        return await list_groups(update, context)
    elif callback_data == ADD_ALLOWED_GROUP:
        return await start_add_group(update, context)
    elif callback_data == EDIT_ALLOWED_GROUP:
        return await edit_group_start(update, context)
    elif callback_data == REMOVE_ALLOWED_GROUP:
        return await remove_group_start(update, context)
    elif callback_data == "main_menu":
        await query.edit_message_text("بازگشت به منوی اصلی...")
        return ConversationHandler.END
    
    return MAIN_MENU

async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    List all allowed groups.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    # Get all allowed groups
    allowed_groups = await AllowedGroup.all().order_by("-is_active", "title")
    
    if not allowed_groups:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ هیچ گروه مجازی یافت نشد.\n\n"
            "برای افزودن گروه، از گزینه «افزودن گروه جدید» استفاده کنید.",
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    # Format the message
    message = "📋 <b>لیست گروه‌های مجاز:</b>\n\n"
    
    for i, group in enumerate(allowed_groups, 1):
        status = "✅ فعال" if group.is_active else "❌ غیرفعال"
        message += f"{i}. <b>{group.title}</b>\n"
        message += f"   ID: <code>{group.chat_id}</code>\n"
        message += f"   وضعیت: {status}\n"
        if group.description:
            message += f"   توضیحات: {group.description}\n"
        message += "\n"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return MAIN_MENU

async def start_add_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start process of adding a new allowed group.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    # Clear any previous data
    if 'new_group' in context.user_data:
        del context.user_data['new_group']
    
    context.user_data['new_group'] = {}
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data=CANCEL_OPERATION)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "➕ <b>افزودن گروه جدید</b>\n\n"
        "لطفاً یک پیام از گروه مورد نظر را برای من فوروارد کنید "
        "یا اگر ربات عضو گروه است، لینک گروه را ارسال کنید.\n\n"
        "<i>توجه: برای اینکه ربات در گروه کار کند، ابتدا باید ربات را به گروه اضافه کرده باشید.</i>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return ADD_GROUP_FROM_FORWARD

async def add_group_from_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process forwarded message to add a new group.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    # Cancel if callback query (cancel button)
    if update.callback_query:
        query = update.callback_query
        if query.data == CANCEL_OPERATION:
            await query.answer("عملیات لغو شد.")
            await show_main_menu(update, context)
            return MAIN_MENU
    
    # Get the chat ID from the forwarded message
    message = update.message
    
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
        chat_title = message.forward_from_chat.title
        chat_username = message.forward_from_chat.username
        
        context.user_data['new_group']['chat_id'] = chat_id
        context.user_data['new_group']['title'] = chat_title
        context.user_data['new_group']['username'] = chat_username
        
        # Check if this group is already in allowed groups
        existing_group = await AllowedGroup.filter(chat_id=chat_id).first()
        
        if existing_group:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            status = "فعال" if existing_group.is_active else "غیرفعال"
            
            await message.reply_text(
                f"⚠️ این گروه قبلاً در لیست گروه‌های مجاز وجود دارد!\n\n"
                f"عنوان: {existing_group.title}\n"
                f"وضعیت: {status}\n",
                reply_markup=reply_markup
            )
            return MAIN_MENU
        
        # Ask for description
        keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data=CANCEL_OPERATION)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            f"✅ اطلاعات گروه دریافت شد:\n\n"
            f"عنوان: {chat_title}\n"
            f"آیدی: {chat_id}\n\n"
            f"لطفاً یک توضیح مختصر برای این گروه وارد کنید (اختیاری):",
            reply_markup=reply_markup
        )
        
        return ADD_GROUP_DESCRIPTION
    
    # Handle link or text that might contain group information
    elif message.text:
        # This is a placeholder - in a real implementation, you would
        # need to handle joining via invite link or extracting group info
        # from a link, which requires additional bot API calls
        
        await message.reply_text(
            "⚠️ لطفاً یک پیام از گروه مورد نظر را فوروارد کنید.\n\n"
            "در حال حاضر، افزودن گروه از طریق لینک پشتیبانی نمی‌شود."
        )
        return ADD_GROUP_FROM_FORWARD
    
    # If neither forward nor text
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data=CANCEL_OPERATION)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        "❌ پیام دریافتی قابل پردازش نیست.\n\n"
        "لطفاً یک پیام از گروه مورد نظر را فوروارد کنید.",
        reply_markup=reply_markup
    )
    
    return ADD_GROUP_FROM_FORWARD

async def add_group_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Add description to the new group and save it.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    # Cancel if callback query (cancel button)
    if update.callback_query:
        query = update.callback_query
        if query.data == CANCEL_OPERATION:
            await query.answer("عملیات لغو شد.")
            await show_main_menu(update, context)
            return MAIN_MENU
    
    # Get the description
    message = update.message
    description = message.text
    
    # Save description
    context.user_data['new_group']['description'] = description
    
    # Create the allowed group
    try:
        group_data = context.user_data['new_group']
        
        # Get user
        user = await User.filter(telegram_id=update.effective_user.id).first()
        
        new_group = await AllowedGroup.create(
            chat_id=group_data['chat_id'],
            title=group_data['title'],
            username=group_data.get('username'),
            description=group_data.get('description'),
            is_active=True,
            added_by=user if user else None
        )
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            f"✅ گروه «{new_group.title}» با موفقیت به لیست گروه‌های مجاز اضافه شد.",
            reply_markup=reply_markup
        )
        
        # Log the action
        logger.info(f"User {update.effective_user.id} added group {new_group.chat_id} to allowed groups")
        
        # Clear the temp data
        if 'new_group' in context.user_data:
            del context.user_data['new_group']
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"Error adding allowed group: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            f"❌ خطا در افزودن گروه: {str(e)}",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU

async def edit_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the process of editing an allowed group.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    # Get all allowed groups
    allowed_groups = await AllowedGroup.all().order_by("-is_active", "title")
    
    if not allowed_groups:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ هیچ گروه مجازی یافت نشد.\n\n"
            "برای افزودن گروه، از گزینه «افزودن گروه جدید» استفاده کنید.",
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    # Create keyboard with groups
    keyboard = []
    for group in allowed_groups:
        status = "✅" if group.is_active else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {group.title}", 
                callback_data=f"{SELECT_GROUP_TO_EDIT}_{group.id}"
            )
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✏️ <b>ویرایش گروه مجاز</b>\n\n"
        "لطفاً گروهی که می‌خواهید ویرایش کنید را انتخاب نمایید:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return EDIT_GROUP_MENU

async def edit_allowed_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Show edit options for a selected allowed group.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    # Get the group ID from callback data
    callback_data = query.data
    if not callback_data.startswith(f"{SELECT_GROUP_TO_EDIT}_"):
        await query.edit_message_text("❌ داده نامعتبر.")
        return ConversationHandler.END
    
    group_id = int(callback_data.split("_")[-1])
    
    # Get the group
    group = await AllowedGroup.filter(id=group_id).first()
    
    if not group:
        await query.edit_message_text(
            "❌ گروه مورد نظر یافت نشد."
        )
        return MAIN_MENU
    
    # Save the group ID in context
    context.user_data['edit_group_id'] = group_id
    
    # Create keyboard with edit options
    keyboard = [
        [InlineKeyboardButton(
            "✏️ ویرایش توضیحات", 
            callback_data=f"{EDIT_GROUP_DESCRIPTION}_{group_id}"
        )],
        [InlineKeyboardButton(
            "🔄 تغییر وضعیت" if group.is_active else "🔄 فعال‌سازی",
            callback_data=f"{TOGGLE_ALLOWED_GROUP}_{group_id}"
        )],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Current status text
    status = "✅ فعال" if group.is_active else "❌ غیرفعال"
    
    await query.edit_message_text(
        f"✏️ <b>ویرایش گروه: {group.title}</b>\n\n"
        f"🆔 شناسه: <code>{group.chat_id}</code>\n"
        f"🔹 وضعیت: {status}\n"
        f"🔹 توضیحات: {group.description or '-'}\n\n"
        f"لطفاً عملیات مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return EDIT_GROUP_MENU

async def edit_description_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the process of editing a group's description.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    # Get the group ID from callback data
    callback_data = query.data
    if not callback_data.startswith(f"{EDIT_GROUP_DESCRIPTION}_"):
        await query.edit_message_text("❌ داده نامعتبر.")
        return ConversationHandler.END
    
    group_id = int(callback_data.split("_")[-1])
    
    # Get the group
    group = await AllowedGroup.filter(id=group_id).first()
    
    if not group:
        await query.edit_message_text(
            "❌ گروه مورد نظر یافت نشد."
        )
        return MAIN_MENU
    
    # Save the group ID in context
    context.user_data['edit_group_id'] = group_id
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data=CANCEL_OPERATION)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✏️ <b>ویرایش توضیحات گروه: {group.title}</b>\n\n"
        f"توضیحات فعلی: {group.description or '-'}\n\n"
        f"لطفاً توضیحات جدید را وارد کنید:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return EDIT_DESCRIPTION_SUBMIT

async def edit_description_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process the new description for a group.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    # Cancel if callback query (cancel button)
    if update.callback_query:
        query = update.callback_query
        if query.data == CANCEL_OPERATION:
            await query.answer("عملیات لغو شد.")
            await show_main_menu(update, context)
            return MAIN_MENU
    
    # Get the group ID from context
    group_id = context.user_data.get('edit_group_id')
    
    if not group_id:
        await update.message.reply_text(
            "❌ خطا: اطلاعات گروه یافت نشد."
        )
        return MAIN_MENU
    
    # Get the group
    group = await AllowedGroup.filter(id=group_id).first()
    
    if not group:
        await update.message.reply_text(
            "❌ گروه مورد نظر یافت نشد."
        )
        return MAIN_MENU
    
    # Get the new description
    new_description = update.message.text
    
    # Update the group
    try:
        old_description = group.description
        group.description = new_description
        await group.save()
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ توضیحات گروه «{group.title}» با موفقیت به‌روزرسانی شد.\n\n"
            f"توضیحات قبلی: {old_description or '-'}\n"
            f"توضیحات جدید: {new_description}",
            reply_markup=reply_markup
        )
        
        # Log the action
        logger.info(
            f"User {update.effective_user.id} updated description of group {group.chat_id} "
            f"from '{old_description}' to '{new_description}'"
        )
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"Error updating group description: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ خطا در به‌روزرسانی توضیحات گروه: {str(e)}",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU

async def toggle_active_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Toggle active status of an allowed group.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    # Get the group ID from callback data
    callback_data = query.data
    if not callback_data.startswith(f"{TOGGLE_ALLOWED_GROUP}_"):
        await query.edit_message_text("❌ داده نامعتبر.")
        return ConversationHandler.END
    
    group_id = int(callback_data.split("_")[-1])
    
    # Get the group
    group = await AllowedGroup.filter(id=group_id).first()
    
    if not group:
        await query.edit_message_text(
            "❌ گروه مورد نظر یافت نشد."
        )
        return MAIN_MENU
    
    # Toggle status
    try:
        old_status = group.is_active
        group.is_active = not old_status
        await group.save()
        
        # Create keyboard for next steps
        keyboard = [
            [InlineKeyboardButton(
                "✏️ ویرایش توضیحات", 
                callback_data=f"{EDIT_GROUP_DESCRIPTION}_{group_id}"
            )],
            [InlineKeyboardButton(
                "🔄 غیرفعال کردن" if group.is_active else "🔄 فعال‌سازی",
                callback_data=f"{TOGGLE_ALLOWED_GROUP}_{group_id}"
            )],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get status text
        new_status_text = "✅ فعال" if group.is_active else "❌ غیرفعال"
        old_status_text = "✅ فعال" if old_status else "❌ غیرفعال"
        
        await query.edit_message_text(
            f"✅ وضعیت گروه «{group.title}» با موفقیت تغییر کرد.\n\n"
            f"وضعیت قبلی: {old_status_text}\n"
            f"وضعیت جدید: {new_status_text}\n\n"
            f"لطفاً عملیات مورد نظر را انتخاب کنید:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        # Log the action
        logger.info(
            f"User {update.effective_user.id} changed status of group {group.chat_id} "
            f"from '{old_status}' to '{group.is_active}'"
        )
        
        return EDIT_GROUP_MENU
        
    except Exception as e:
        logger.error(f"Error toggling group status: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ خطا در تغییر وضعیت گروه: {str(e)}",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU

async def remove_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the process of removing an allowed group.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    # Get all allowed groups
    allowed_groups = await AllowedGroup.all().order_by("-is_active", "title")
    
    if not allowed_groups:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ هیچ گروه مجازی یافت نشد.\n\n"
            "برای افزودن گروه، از گزینه «افزودن گروه جدید» استفاده کنید.",
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    # Create keyboard with groups
    keyboard = []
    for group in allowed_groups:
        status = "✅" if group.is_active else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {group.title}", 
                callback_data=f"{SELECT_GROUP_TO_REMOVE}_{group.id}"
            )
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🗑 <b>حذف گروه مجاز</b>\n\n"
        "لطفاً گروهی که می‌خواهید حذف کنید را انتخاب نمایید:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return REMOVE_GROUP_START

async def confirm_remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Confirm removing an allowed group.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    # Get the group ID from callback data
    callback_data = query.data
    if not callback_data.startswith(f"{SELECT_GROUP_TO_REMOVE}_"):
        await query.edit_message_text("❌ داده نامعتبر.")
        return ConversationHandler.END
    
    group_id = int(callback_data.split("_")[-1])
    
    # Get the group
    group = await AllowedGroup.filter(id=group_id).first()
    
    if not group:
        await query.edit_message_text(
            "❌ گروه مورد نظر یافت نشد."
        )
        return MAIN_MENU
    
    # Save the group ID in context
    context.user_data['remove_group_id'] = group_id
    
    # Create keyboard for confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"{FINAL_GROUP_REMOVE}_{group_id}"),
            InlineKeyboardButton("❌ خیر، لغو عملیات", callback_data=CANCEL_OPERATION)
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get status text
    status = "✅ فعال" if group.is_active else "❌ غیرفعال"
    
    await query.edit_message_text(
        f"⚠️ <b>تأیید حذف گروه</b>\n\n"
        f"آیا مطمئن هستید که می‌خواهید گروه زیر را حذف کنید؟\n\n"
        f"🔹 <b>عنوان:</b> {group.title}\n"
        f"🔹 <b>شناسه:</b> <code>{group.chat_id}</code>\n"
        f"🔹 <b>وضعیت:</b> {status}\n"
        f"🔹 <b>توضیحات:</b> {group.description or '-'}\n\n"
        f"⚠️ این عملیات قابل بازگشت نیست.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return CONFIRM_REMOVE_GROUP

async def final_remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Finally remove the allowed group.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    # Get the group ID from callback data
    callback_data = query.data
    if not callback_data.startswith(f"{FINAL_GROUP_REMOVE}_"):
        await query.edit_message_text("❌ داده نامعتبر.")
        return ConversationHandler.END
    
    group_id = int(callback_data.split("_")[-1])
    
    # Get the group
    group = await AllowedGroup.filter(id=group_id).first()
    
    if not group:
        await query.edit_message_text(
            "❌ گروه مورد نظر یافت نشد."
        )
        return MAIN_MENU
    
    # Save group info for the confirmation message
    group_title = group.title
    group_chat_id = group.chat_id
    
    # Delete the group
    try:
        await group.delete()
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ گروه «{group_title}» با موفقیت از لیست گروه‌های مجاز حذف شد.",
            reply_markup=reply_markup
        )
        
        # Log the action
        logger.info(f"User {update.effective_user.id} removed group {group_chat_id} from allowed groups")
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"Error removing group: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ خطا در حذف گروه: {str(e)}",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel current operation and return to main menu.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer("عملیات لغو شد.")
    
    # Clear any temporary data
    if 'new_group' in context.user_data:
        del context.user_data['new_group']
    if 'edit_group_id' in context.user_data:
        del context.user_data['edit_group_id']
    if 'remove_group_id' in context.user_data:
        del context.user_data['remove_group_id']
    
    await show_main_menu(update, context)
    return MAIN_MENU

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Return to main menu.
    
    Args:
        update: The update object
        context: The context object
        
    Returns:
        int: The next state
    """
    query = update.callback_query
    await query.answer()
    
    await show_main_menu(update, context)
    return MAIN_MENU

def get_allowed_groups_handlers() -> List:
    """
    Get the handlers for allowed groups management.
    
    Returns:
        List of handlers
    """
    allowed_groups_handler = ConversationHandler(
        entry_points=[CommandHandler('allowed_groups', allowed_groups_command)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(handle_menu_selection, pattern=f"^({LIST_ALLOWED_GROUPS}|{ADD_ALLOWED_GROUP}|{EDIT_ALLOWED_GROUP}|{REMOVE_ALLOWED_GROUP}|main_menu)$")
            ],
            LIST_GROUPS: [
                CallbackQueryHandler(back_to_main_menu, pattern=f"^{BACK_TO_MENU}$")
            ],
            ADD_GROUP_START: [
                CallbackQueryHandler(cancel_operation, pattern=f"^{CANCEL_OPERATION}$")
            ],
            ADD_GROUP_FROM_FORWARD: [
                CallbackQueryHandler(cancel_operation, pattern=f"^{CANCEL_OPERATION}$"),
                MessageHandler(filters.FORWARDED | filters.TEXT, add_group_from_forward)
            ],
            ADD_GROUP_DESCRIPTION: [
                CallbackQueryHandler(cancel_operation, pattern=f"^{CANCEL_OPERATION}$"),
                MessageHandler(filters.TEXT, add_group_description)
            ],
            EDIT_GROUP_START: [
                CallbackQueryHandler(back_to_main_menu, pattern=f"^{BACK_TO_MENU}$")
            ],
            EDIT_GROUP_MENU: [
                CallbackQueryHandler(edit_allowed_group, pattern=f"^{SELECT_GROUP_TO_EDIT}_[0-9]+$"),
                CallbackQueryHandler(edit_description_start, pattern=f"^{EDIT_GROUP_DESCRIPTION}_[0-9]+$"),
                CallbackQueryHandler(toggle_active_status, pattern=f"^{TOGGLE_ALLOWED_GROUP}_[0-9]+$"),
                CallbackQueryHandler(back_to_main_menu, pattern=f"^{BACK_TO_MENU}$")
            ],
            EDIT_DESCRIPTION_START: [
                CallbackQueryHandler(cancel_operation, pattern=f"^{CANCEL_OPERATION}$")
            ],
            EDIT_DESCRIPTION_SUBMIT: [
                CallbackQueryHandler(cancel_operation, pattern=f"^{CANCEL_OPERATION}$"),
                MessageHandler(filters.TEXT, edit_description_process)
            ],
            REMOVE_GROUP_START: [
                CallbackQueryHandler(confirm_remove_group, pattern=f"^{SELECT_GROUP_TO_REMOVE}_[0-9]+$"),
                CallbackQueryHandler(back_to_main_menu, pattern=f"^{BACK_TO_MENU}$")
            ],
            CONFIRM_REMOVE_GROUP: [
                CallbackQueryHandler(final_remove_group, pattern=f"^{FINAL_GROUP_REMOVE}_[0-9]+$"),
                CallbackQueryHandler(cancel_operation, pattern=f"^{CANCEL_OPERATION}$")
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_operation),
            CallbackQueryHandler(back_to_main_menu, pattern=f"^{BACK_TO_MENU}$"),
            CallbackQueryHandler(cancel_operation, pattern=f"^{CANCEL_OPERATION}$")
        ],
        name="allowed_groups_conversation",
        persistent=False
    )
    
    return [allowed_groups_handler] 