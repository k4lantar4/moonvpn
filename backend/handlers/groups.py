"""
Group management handlers for the Telegram bot.

This module implements handlers for:
- Group join/leave events
- Group info updates
- Group messages filtering
- Group information commands for users
"""

import logging
from typing import Dict, Any, Optional, List

from telegram import Update, Chat, ChatMember, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ChatMemberHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

# Import models
try:
    from main.models import AllowedGroup, User
    from django.utils import timezone
except ImportError:
    logging.warning("Django models import failed in groups.py. Using mock objects.")
    # Define mock classes for testing without Django
    class AllowedGroup:
        objects = type('', (), {
            'filter': lambda **kwargs: type('', (), {'exists': lambda: False, 'first': lambda: None})(),
            'get': lambda **kwargs: type('', (), {
                'group_id': 123, 
                'title': 'Test Group', 
                'is_active': True,
                'save': lambda: None
            }),
            'create': lambda **kwargs: type('', (), kwargs),
        })()

    class User:
        objects = type('', (), {
            'filter': lambda **kwargs: [],
            'get': lambda **kwargs: type('', (), {'id': 1, 'is_admin': True}),
        })()
        
    timezone = type('', (), {'now': lambda: None})

# Import filters
from core.utils.formatting import allowed_group_filter, admin_filter, maintenance_mode_filter
from core.utils.helpers import get_formatted_datetime

# Setup logging
logger = logging.getLogger("telegram_bot")

# Callback patterns
GROUP_INFO = "group_info"
GROUP_RULES = "show_group_rules"
GROUP_ADMINS = "show_group_admins"

async def extract_chat_info(chat: Chat) -> Dict[str, Any]:
    """
    Extract relevant information from a chat object.
    
    Args:
        chat: The Telegram chat object
        
    Returns:
        Dict[str, Any]: Dictionary with chat information
    """
    return {
        'group_id': chat.id,
        'title': chat.title or f"Chat {chat.id}",
        'username': chat.username,
        'invite_link': chat.invite_link,
        'members_count': chat.get_member_count() if hasattr(chat, 'get_member_count') else 0
    }

async def process_new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process new chat when the bot is added to a group.
    Updates AllowedGroup model with chat info.
    
    Args:
        update: The update object
        context: The context object
    """
    # Get chat information
    chat = update.effective_chat
    chat_info = await extract_chat_info(chat)
    
    try:
        # Check if this group is already in the allowed list
        group_exists = AllowedGroup.objects.filter(group_id=chat.id).exists()
        
        if group_exists:
            # Update existing group info
            group = AllowedGroup.objects.get(group_id=chat.id)
            
            # Update fields
            group.title = chat_info['title']
            group.username = chat_info['username']
            group.invite_link = chat_info['invite_link']
            group.members_count = chat_info['members_count']
            
            # Reactivate if it was inactive
            if not group.is_active:
                group.is_active = True
            
            group.updated_at = timezone.now()
            group.save()
            
            logger.info(f"Updated existing group info: {chat.id} ({chat.title})")
        else:
            # This group is not in the allowed list yet
            # By default, we don't auto-add groups - admin must explicitly allow
            added_by = update.effective_user.id if update.effective_user else 0
            
            # Check if it's a known admin adding the bot
            is_admin_adding = False
            if update.effective_user:
                try:
                    user = User.objects.get(telegram_id=update.effective_user.id)
                    is_admin_adding = user.is_admin
                except:
                    pass
            
            # Create new group entry as inactive by default unless added by admin
            AllowedGroup.objects.create(
                group_id=chat.id,
                title=chat_info['title'],
                username=chat_info['username'],
                invite_link=chat_info['invite_link'],
                members_count=chat_info['members_count'],
                added_by=added_by,
                is_active=is_admin_adding
            )
            
            logger.info(f"Added new group: {chat.id} ({chat.title}), activated: {is_admin_adding}")
            
            # Notify admins if enabled
            # Send welcome message based on whether group is activated
            if is_admin_adding:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="🌙 *Moon VPN*\n\n"
                         "ربات با موفقیت به گروه اضافه شد و فعال است.\n"
                         "برای شروع می‌توانید از دستورات زیر استفاده کنید:\n"
                         "/start - شروع کار با ربات\n"
                         "/help - راهنمای استفاده از ربات",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="🌙 *Moon VPN*\n\n"
                         "ربات به گروه اضافه شد، اما هنوز فعال نشده است.\n"
                         "لطفاً صبر کنید تا ادمین ربات، گروه را تأیید کند.",
                    parse_mode=ParseMode.MARKDOWN
                )
            
    except Exception as e:
        logger.error(f"Error processing new chat: {e}")

async def process_left_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process chat when the bot leaves a group or is removed from a group.
    Sets the AllowedGroup entry to inactive.
    
    Args:
        update: The update object
        context: The context object
    """
    # Get chat information
    chat = update.effective_chat
    
    try:
        # Check if this group is in the database
        group_exists = AllowedGroup.objects.filter(group_id=chat.id).exists()
        
        if group_exists:
            # Update group status to inactive
            group = AllowedGroup.objects.get(group_id=chat.id)
            group.is_active = False
            group.updated_at = timezone.now()
            group.save()
            
            logger.info(f"Set group to inactive: {chat.id} ({chat.title})")
    
    except Exception as e:
        logger.error(f"Error processing left chat: {e}")

def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> Optional[tuple[bool, bool]]:
    """
    Takes a ChatMemberUpdated instance and extracts whether the bot was added or removed.
    
    Returns:
        tuple[bool, bool]: (was_added, was_removed)
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_added = (
        (old_status != ChatMember.MEMBER and new_status == ChatMember.MEMBER)
        or (old_is_member is False and new_is_member is True)
    )
    was_removed = (
        (old_status == ChatMember.MEMBER and new_status != ChatMember.MEMBER)
        or (old_is_member is True and new_is_member is False)
    )
    
    return was_added, was_removed

async def track_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Track when the bot is added to or removed from a chat.
    
    Args:
        update: The update object
        context: The context object
    """
    chat_member = update.chat_member or update.my_chat_member
    
    if not chat_member:
        return
    
    # Extract the status change info
    result = extract_status_change(chat_member)
    if result is None:
        return
    
    was_added, was_removed = result
    
    # Bot was added to a group chat
    if was_added and chat_member.chat.type != Chat.PRIVATE:
        await process_new_chat(update, context)
        
    # Bot was removed from a group chat
    elif was_removed and chat_member.chat.type != Chat.PRIVATE:
        await process_left_chat(update, context)

async def update_group_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Update group information when a message is received from a group.
    
    Args:
        update: The update object
        context: The context object
    """
    # Skip if not a group message
    if update.effective_chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        return
    
    chat = update.effective_chat
    
    try:
        # Check if this group is in the database and active
        group_query = AllowedGroup.objects.filter(group_id=chat.id, is_active=True)
        
        if group_query.exists():
            group = group_query.first()
            
            # Check if any information has changed
            info_changed = (
                group.title != chat.title
                or group.username != chat.username
                or group.invite_link != chat.invite_link
            )
            
            if info_changed:
                # Update information
                group.title = chat.title or group.title
                group.username = chat.username
                group.invite_link = chat.invite_link
                group.updated_at = timezone.now()
                group.save()
                
                logger.info(f"Updated group info: {chat.id} ({chat.title})")
    
    except Exception as e:
        logger.error(f"Error updating group info: {e}")

async def group_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /groupinfo command to show information about the current group.
    
    Args:
        update: The update object
        context: The context object
    """
    # Check if command is used in a group
    if update.effective_chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        await update.message.reply_text(
            "⚠️ این دستور فقط در گروه‌ها قابل استفاده است."
        )
        return
    
    chat_id = update.effective_chat.id
    
    # Get group from database
    try:
        group = AllowedGroup.objects.filter(group_id=chat_id, is_active=True).first()
        
        if not group:
            await update.message.reply_text(
                "⚠️ این گروه در لیست گروه‌های مجاز ربات نیست."
            )
            return
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("📜 قوانین گروه", callback_data=GROUP_RULES)],
            [InlineKeyboardButton("👥 مدیران گروه", callback_data=GROUP_ADMINS)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format group info message
        member_count = update.effective_chat.get_member_count() if hasattr(update.effective_chat, "get_member_count") else "نامشخص"
        username = f"@{update.effective_chat.username}" if update.effective_chat.username else "ندارد"
        
        message = (
            f"ℹ️ <b>اطلاعات گروه</b>\n\n"
            f"🔹 <b>نام:</b> {update.effective_chat.title}\n"
            f"🔹 <b>یوزرنیم:</b> {username}\n"
            f"🔹 <b>شناسه:</b> <code>{chat_id}</code>\n"
            f"🔹 <b>تعداد اعضا:</b> {member_count}\n"
        )
        
        if group.description:
            message += f"🔹 <b>توضیحات:</b> {group.description}\n"
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error in group_info_command: {e}")
        await update.message.reply_text(
            "❌ خطایی در دریافت اطلاعات گروه رخ داد. لطفاً بعداً تلاش کنید."
        )

async def handle_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callbacks for group info buttons.
    
    Args:
        update: The update object
        context: The context object
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    chat_id = update.effective_chat.id
    
    if callback_data == GROUP_RULES:
        # Show group rules
        try:
            # Try to get rules from Telegram API first
            chat = await context.bot.get_chat(chat_id)
            rules = chat.description
            
            if rules:
                await query.edit_message_text(
                    f"📜 <b>قوانین گروه</b>\n\n{rules}",
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text(
                    "📜 <b>قوانین گروه</b>\n\n"
                    "هیچ قوانینی برای این گروه تنظیم نشده است.",
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            logger.error(f"Error getting group rules: {e}")
            await query.edit_message_text(
                "⚠️ خطا در دریافت قوانین گروه.",
                parse_mode=ParseMode.HTML
            )
    
    elif callback_data == GROUP_ADMINS:
        # Show group admins
        try:
            # Get group admins from Telegram API
            admins = await context.bot.get_chat_administrators(chat_id)
            
            if admins:
                message = "👥 <b>مدیران گروه</b>\n\n"
                
                for i, admin in enumerate(admins, 1):
                    user = admin.user
                    status = "👑 مالک" if admin.status == "creator" else "👮‍♂️ ادمین"
                    name = user.full_name
                    username = f" (@{user.username})" if user.username else ""
                    
                    message += f"{i}. {status}: {name}{username}\n"
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text(
                    "⚠️ اطلاعات مدیران در دسترس نیست.",
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            logger.error(f"Error getting group admins: {e}")
            await query.edit_message_text(
                "⚠️ خطا در دریافت لیست مدیران گروه.",
                parse_mode=ParseMode.HTML
            )
    
    else:
        await query.edit_message_text(
            "⚠️ درخواست نامعتبر."
        )

def get_group_handlers():
    """
    Return handlers related to group management.
    
    Returns:
        list: List of handlers
    """
    # Track when bot is added to or removed from chats
    chat_member_handler = ChatMemberHandler(track_chat_member)
    
    # Update group info on regular messages
    group_info_handler = MessageHandler(
        filters.ChatType.GROUPS & allowed_group_filter,
        update_group_info
    )
    
    # User commands for group information
    group_info_command_handler = CommandHandler(
        "groupinfo", 
        group_info_command, 
        filters=allowed_group_filter & maintenance_mode_filter
    )
    
    # Callback handler for group info buttons
    group_callback_handler = CallbackQueryHandler(
        handle_group_callback, 
        pattern=f"^({GROUP_INFO}|{GROUP_RULES}|{GROUP_ADMINS})$"
    )
    
    return [
        chat_member_handler,
        group_info_handler,
        group_info_command_handler,
        group_callback_handler
    ] 