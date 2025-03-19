"""
Server management handlers.

This module contains handlers for managing VPN servers.
"""

import logging
from typing import Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler

from utils import get_text, format_number, format_date
from decorators import require_admin
from api_client import (
    get_servers,
    get_server,
    update_server,
    delete_server,
    test_server_connection,
)
from .constants import SELECTING_SERVER, ADMIN_MENU, SERVER_MANAGEMENT
from .notification_hooks import hook_server_status_change

logger = logging.getLogger(__name__)

# Mock API functions - replace with actual API calls
async def get_servers() -> List[Dict[str, Any]]:
    """Get all servers."""
    return [
        {"id": 1, "name": "آلمان ۱", "host": "de1.moonvpn.ir", "status": "online", "location": "آلمان", "users": 120},
        {"id": 2, "name": "هلند ۱", "host": "nl1.moonvpn.ir", "status": "online", "location": "هلند", "users": 85},
        {"id": 3, "name": "فرانسه ۱", "host": "fr1.moonvpn.ir", "status": "offline", "location": "فرانسه", "users": 0},
    ]

async def get_server(server_id: int) -> Dict[str, Any]:
    """Get server by ID."""
    servers = await get_servers()
    for server in servers:
        if server["id"] == server_id:
            return server
    return None

async def toggle_server_status(server_id: int) -> Dict[str, Any]:
    """Toggle server status between online and offline."""
    server = await get_server(server_id)
    if not server:
        return {"success": False, "message": "سرور یافت نشد"}
    
    # Toggle status
    new_status = "offline" if server["status"] == "online" else "online"
    
    # In a real implementation, you would call an API to change the status
    # Here we just return the new status
    return {"success": True, "status": new_status}

@require_admin
async def server_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the list of servers."""
    query = update.callback_query
    if query:
        await query.answer()
    
    # Get all servers
    servers = await get_servers()
    
    message = "🖥️ *مدیریت سرورها*\n\n"
    
    if not servers:
        message += "هیچ سروری ثبت نشده است."
    else:
        for server in servers:
            status_emoji = "🟢" if server["status"] == "online" else "🔴"
            users_count = server.get("users", 0)
            message += (
                f"{status_emoji} *{server['name']}*\n"
                f"• هاست: `{server['host']}`\n"
                f"• موقعیت: {server['location']}\n"
                f"• کاربران: {users_count}\n\n"
            )
    
    # Create keyboard
    keyboard = []
    
    # Add button for each server
    for server in servers:
        status_emoji = "🟢" if server["status"] == "online" else "🔴"
        keyboard.append([
            InlineKeyboardButton(
                f"{status_emoji} {server['name']}",
                callback_data=f"server_details:{server['id']}"
            )
        ])
    
    # Add server management buttons
    keyboard.append([
        InlineKeyboardButton("➕ افزودن سرور", callback_data="add_server"),
        InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_servers")
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به منوی مدیریت", callback_data=ADMIN_MENU)
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
    
    return SELECTING_SERVER

@require_admin
async def server_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display server details."""
    query = update.callback_query
    await query.answer()
    
    # Extract server ID from callback data
    server_id = int(query.data.split(":")[1])
    
    # Get server details
    server = await get_server(server_id)
    
    if not server:
        await query.edit_message_text(
            "❌ سرور مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست سرورها", callback_data="server_list")]
            ])
        )
        return SELECTING_SERVER
    
    # Prepare message
    status_emoji = "🟢" if server["status"] == "online" else "🔴"
    status_text = "آنلاین" if server["status"] == "online" else "آفلاین"
    users_count = server.get("users", 0)
    
    message = (
        f"{status_emoji} *جزئیات سرور {server['name']}*\n\n"
        f"• شناسه: `{server['id']}`\n"
        f"• هاست: `{server['host']}`\n"
        f"• موقعیت: {server['location']}\n"
        f"• وضعیت: {status_text}\n"
        f"• تعداد کاربران: {users_count}\n"
    )
    
    # Add more details if available
    if "ip" in server:
        message += f"• آدرس IP: `{server['ip']}`\n"
    if "port" in server:
        message += f"• پورت: `{server['port']}`\n"
    if "protocol" in server:
        message += f"• پروتکل: {server['protocol']}\n"
    if "capacity" in server:
        message += f"• ظرفیت: {server['capacity']}\n"
    
    # Create keyboard
    toggle_text = "🔴 غیرفعال کردن" if server["status"] == "online" else "🟢 فعال کردن"
    
    keyboard = [
        [
            InlineKeyboardButton(toggle_text, callback_data=f"toggle_server:{server['id']}"),
            InlineKeyboardButton("🔄 همگام‌سازی", callback_data=f"sync_server:{server['id']}")
        ],
        [
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_server:{server['id']}"),
            InlineKeyboardButton("❌ حذف", callback_data=f"delete_server:{server['id']}")
        ],
        [
            InlineKeyboardButton("👥 مشاهده کاربران", callback_data=f"server_users:{server['id']}")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به لیست سرورها", callback_data="server_list")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_SERVER

@require_admin
async def toggle_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle server status between online and offline."""
    query = update.callback_query
    await query.answer()
    
    # Extract server ID from callback data
    server_id = int(query.data.split(":")[1])
    
    # Get current server details for notification
    server_before = await get_server(server_id)
    if not server_before:
        await query.edit_message_text(
            "❌ سرور مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست سرورها", callback_data="server_list")]
            ])
        )
        return SELECTING_SERVER
    
    # Change status
    result = await toggle_server_status(server_id)
    
    if result.get("success", False):
        # Get updated server details with timestamp for notification
        server_after = await get_server(server_id)
        
        # Add timestamp for notification
        import datetime
        server_after['updated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add IP if not present (for notification)
        if 'ip' not in server_after:
            server_after['ip'] = server_after.get('host', 'نامشخص')
        
        # Prepare status information
        new_status = result.get("status", "unknown")
        is_online = new_status == "online"
        
        # Send notification
        try:
            notification_sent = await hook_server_status_change(context.bot, server_after, is_online)
            if not notification_sent:
                logger.warning(f"Notification was not sent for server status change: {server_id}")
        except Exception as e:
            logger.error(f"Failed to send server status notification: {str(e)}")
        
        # Success message
        status_emoji = "🟢" if is_online else "🔴"
        status_text = "آنلاین" if is_online else "آفلاین"
        
        await query.edit_message_text(
            f"{status_emoji} *تغییر وضعیت سرور*\n\n"
            f"وضعیت سرور *{server_before['name']}* با موفقیت به {status_text} تغییر کرد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 مشاهده جزئیات", callback_data=f"server_details:{server_id}")],
                [InlineKeyboardButton("🔙 بازگشت به لیست سرورها", callback_data="server_list")]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Error message
        error_message = result.get("message", "خطای نامشخص")
        await query.edit_message_text(
            f"❌ *خطا در تغییر وضعیت سرور*\n\n{error_message}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات سرور", callback_data=f"server_details:{server_id}")]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    return SELECTING_SERVER

@require_admin
async def server_test_connection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Test connection to a server."""
    query = update.callback_query
    await query.answer(text="در حال تست اتصال...")
    
    # Get server ID from callback data
    server_id = int(query.data.split(":")[-1])
    
    # Get server details first
    server = get_server(server_id)
    if not server:
        await query.edit_message_text(
            "❌ سرور مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست سرورها", callback_data=SERVER_MANAGEMENT)]
            ])
        )
        return SELECTING_SERVER
    
    server_name = server.get("name", "")
    
    # Test connection
    result = test_server_connection(server_id)
    
    success = result.get("success", False)
    message = result.get("message", "")
    
    # Format response message
    if success:
        status_message = (
            f"✅ *اتصال موفق*\n\n"
            f"سرور *{server_name}* به درستی پاسخ داد.\n\n"
            f"پیام: {message}"
        )
    else:
        status_message = (
            f"❌ *خطا در اتصال*\n\n"
            f"اتصال به سرور *{server_name}* با مشکل مواجه شد.\n\n"
            f"خطا: {message}"
        )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 بازگشت به جزئیات سرور", 
                callback_data=f"server_details:{server_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به لیست سرورها", 
                callback_data=SERVER_MANAGEMENT
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        status_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_SERVER

# Placeholder for other server management functions
# These would be implemented similar to the account and payment handlers

# Define handlers list to be imported in __init__.py
handlers = [
    CallbackQueryHandler(server_list, pattern="^server_menu$"),
    CallbackQueryHandler(server_list, pattern="^server_list$"),
    CallbackQueryHandler(server_list, pattern="^refresh_servers$"),
    CallbackQueryHandler(server_details, pattern="^server_details:"),
    CallbackQueryHandler(toggle_server, pattern="^toggle_server:"),
    CallbackQueryHandler(server_test_connection, pattern="^server_test:"),
]

# Create a class to hold the handlers for easier import
class server_handlers:
    """Container for server handlers."""
    
    handlers = handlers
    
    # Export the menu function for use in __init__.py
    server_list = server_list 