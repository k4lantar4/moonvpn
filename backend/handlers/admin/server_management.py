"""
Admin handlers for VPN server management.

This module provides handlers for managing VPN servers via the Telegram bot.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

from models import Server
from core.utils.helpers import admin_required
from core.utils.i18n import _
from core.utils.formatting import admin_filter
from services.server_manager import ServerManager

# Configure logging
logger = logging.getLogger(__name__)

# Conversation states
(
    SERVER_LIST,
    ADD_SERVER,
    EDIT_SERVER,
    DELETE_SERVER,
    ENTER_NAME,
    ENTER_HOST,
    ENTER_PORT,
    ENTER_USERNAME,
    ENTER_PASSWORD,
    ENTER_API_PORT,
    ENTER_LOCATION,
    CONFIRM_DELETE,
    TEST_CONNECTION,
    SAVE_SERVER,
) = range(14)

# Callback data patterns
SERVER_CB = r"server_(\w+)_(.+)"
SERVER_ACTION = r"server_action_(\w+)_(.+)"

async def server_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /server command to manage VPN servers."""
    await list_servers(update, context)
    return SERVER_LIST

async def list_servers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """List all servers with management options."""
    servers = Server.get_all()
    
    if not servers:
        keyboard = [
            [InlineKeyboardButton(_("➕ Add New Server"), callback_data="server_action_add_new")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(
            _("🖥️ No servers found. Add your first VPN server."),
            reply_markup=reply_markup
        )
        return SERVER_LIST
    
    # Build server list with buttons
    keyboard = []
    for server in servers:
        status = "🟢" if server.is_active else "🔴"
        server_btn = InlineKeyboardButton(
            f"{status} {server.name} ({server.location})",
            callback_data=f"server_view_{server.id}"
        )
        keyboard.append([server_btn])
    
    # Add button to add new server
    keyboard.append([InlineKeyboardButton(_("➕ Add New Server"), callback_data="server_action_add_new")])
    keyboard.append([InlineKeyboardButton(_("🔙 Back to Admin Panel"), callback_data="admin_dashboard")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        _("🖥️ VPN Server Management\n\nSelect a server to manage or add a new one:"),
        reply_markup=reply_markup
    )
    return SERVER_LIST

async def handle_server_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle server-related callbacks."""
    query = update.callback_query
    await query.answer()
    
    # Extract action and server_id from callback data
    match = re.match(SERVER_CB, query.data)
    if match:
        action, server_id = match.groups()
        
        if action == "view":
            return await view_server_details(update, context, server_id)
        elif action == "edit":
            context.user_data["editing_server_id"] = server_id
            return await edit_server_menu(update, context, server_id)
        elif action == "delete":
            context.user_data["deleting_server_id"] = server_id
            return await confirm_delete_server(update, context, server_id)
        elif action == "test":
            return await test_server_connection(update, context, server_id)
        elif action == "toggle":
            return await toggle_server_active(update, context, server_id)
    
    # Handle server actions
    match = re.match(SERVER_ACTION, query.data)
    if match:
        action, param = match.groups()
        
        if action == "add":
            return await start_add_server(update, context)
    
    # Default fallback
    await list_servers(update, context)
    return SERVER_LIST

async def view_server_details(update: Update, context: ContextTypes.DEFAULT_TYPE, server_id: str) -> int:
    """Show server details with management options."""
    query = update.callback_query
    server = Server.get_by_id(int(server_id))
    
    if not server:
        await query.edit_message_text(_("Server not found. It may have been deleted."))
        await list_servers(update, context)
        return SERVER_LIST
    
    status = "🟢 Active" if server.is_active else "🔴 Inactive"
    
    details = _(f"🖥️ Server Details\n\n"
                f"Name: {server.name}\n"
                f"Host: {server.host}\n"
                f"Port: {server.port}\n"
                f"API Port: {server.api_port}\n"
                f"Location: {server.location}\n"
                f"Status: {status}\n")
    
    keyboard = [
        [
            InlineKeyboardButton(_("✏️ Edit"), callback_data=f"server_edit_{server_id}"),
            InlineKeyboardButton(_("🗑️ Delete"), callback_data=f"server_delete_{server_id}")
        ],
        [
            InlineKeyboardButton(_("🔄 Test Connection"), callback_data=f"server_test_{server_id}"),
            InlineKeyboardButton(
                _("🔴 Deactivate") if server.is_active else _("🟢 Activate"), 
                callback_data=f"server_toggle_{server_id}"
            )
        ],
        [InlineKeyboardButton(_("🔙 Back to Server List"), callback_data="server_action_list")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(details, reply_markup=reply_markup)
    return SERVER_LIST

async def start_add_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process of adding a new server."""
    query = update.callback_query
    
    # Initialize a new server in user_data
    context.user_data["new_server"] = {
        "name": "",
        "host": "",
        "port": 2053,
        "username": "",
        "password": "",
        "api_port": 2053,
        "location": "",
        "is_active": True
    }
    
    await query.edit_message_text(
        _("➕ Adding a new VPN server\n\n"
          "Please enter the server name (e.g., 'Germany Server'):"),
    )
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle entering server name."""
    name = update.message.text.strip()
    
    if context.user_data.get("editing_server_id"):
        # Editing existing server
        server_id = context.user_data["editing_server_id"]
        server = Server.get_by_id(int(server_id))
        server.name = name
    else:
        # Adding new server
        context.user_data["new_server"]["name"] = name
    
    await update.message.reply_text(
        _("Enter the server host (IP address or domain name):")
    )
    return ENTER_HOST

async def enter_host(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle entering server host."""
    host = update.message.text.strip()
    
    if context.user_data.get("editing_server_id"):
        server_id = context.user_data["editing_server_id"]
        server = Server.get_by_id(int(server_id))
        server.host = host
    else:
        context.user_data["new_server"]["host"] = host
    
    await update.message.reply_text(
        _("Enter the panel port (default is 2053):")
    )
    return ENTER_PORT

async def enter_port(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle entering server port."""
    try:
        port = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(_("Invalid port. Please enter a number:"))
        return ENTER_PORT
    
    if context.user_data.get("editing_server_id"):
        server_id = context.user_data["editing_server_id"]
        server = Server.get_by_id(int(server_id))
        server.port = port
    else:
        context.user_data["new_server"]["port"] = port
    
    await update.message.reply_text(
        _("Enter the panel username:")
    )
    return ENTER_USERNAME

async def enter_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle entering server username."""
    username = update.message.text.strip()
    
    if context.user_data.get("editing_server_id"):
        server_id = context.user_data["editing_server_id"]
        server = Server.get_by_id(int(server_id))
        server.username = username
    else:
        context.user_data["new_server"]["username"] = username
    
    await update.message.reply_text(
        _("Enter the panel password:")
    )
    return ENTER_PASSWORD

async def enter_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle entering server password."""
    password = update.message.text.strip()
    
    if context.user_data.get("editing_server_id"):
        server_id = context.user_data["editing_server_id"]
        server = Server.get_by_id(int(server_id))
        server.password = password
    else:
        context.user_data["new_server"]["password"] = password
    
    await update.message.reply_text(
        _("Enter the API port (usually the same as panel port, default 2053):")
    )
    return ENTER_API_PORT

async def enter_api_port(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle entering API port."""
    try:
        api_port = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(_("Invalid port. Please enter a number:"))
        return ENTER_API_PORT
    
    if context.user_data.get("editing_server_id"):
        server_id = context.user_data["editing_server_id"]
        server = Server.get_by_id(int(server_id))
        server.api_port = api_port
    else:
        context.user_data["new_server"]["api_port"] = api_port
    
    await update.message.reply_text(
        _("Enter the server location (e.g., 'Germany', 'France'):")
    )
    return ENTER_LOCATION

async def enter_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle entering server location."""
    location = update.message.text.strip()
    
    if context.user_data.get("editing_server_id"):
        server_id = context.user_data["editing_server_id"]
        server = Server.get_by_id(int(server_id))
        server.location = location
        
        # Show summary of edited server
        keyboard = [
            [
                InlineKeyboardButton(_("🔄 Test Connection"), callback_data=f"server_test_{server_id}"),
                InlineKeyboardButton(_("💾 Save"), callback_data=f"server_save_{server_id}")
            ],
            [InlineKeyboardButton(_("🔙 Cancel"), callback_data="server_action_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            _(f"Server details updated:\n\n"
              f"Name: {server.name}\n"
              f"Host: {server.host}\n"
              f"Port: {server.port}\n"
              f"API Port: {server.api_port}\n"
              f"Location: {server.location}\n\n"
              f"Would you like to test the connection or save changes?"),
            reply_markup=reply_markup
        )
        return SERVER_LIST
    else:
        # New server
        context.user_data["new_server"]["location"] = location
        
        # Create new server object
        new_server = context.user_data["new_server"]
        
        keyboard = [
            [
                InlineKeyboardButton(_("🔄 Test Connection"), callback_data="server_test_new"),
                InlineKeyboardButton(_("💾 Save Server"), callback_data="server_save_new")
            ],
            [InlineKeyboardButton(_("🔙 Cancel"), callback_data="server_action_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            _(f"New server details:\n\n"
              f"Name: {new_server['name']}\n"
              f"Host: {new_server['host']}\n"
              f"Port: {new_server['port']}\n"
              f"API Port: {new_server['api_port']}\n"
              f"Location: {new_server['location']}\n\n"
              f"Would you like to test the connection or save the server?"),
            reply_markup=reply_markup
        )
        return SERVER_LIST

async def test_server_connection(update: Update, context: ContextTypes.DEFAULT_TYPE, server_id: str) -> int:
    """Test connection to the server."""
    query = update.callback_query
    
    await query.edit_message_text(_("🔄 Testing connection to server..."))
    
    try:
        if server_id == "new":
            # Testing new server
            new_server = context.user_data["new_server"]
            host = new_server["host"]
            port = new_server["port"]
            username = new_server["username"]
            password = new_server["password"]
        else:
            # Testing existing server
            server = Server.get_by_id(int(server_id))
            host = server.host
            port = server.port
            username = server.username
            password = server.password
        
        # Perform connection test using ServerManager
        server_manager = ServerManager()
        success, message = await server_manager.test_connection(
            host, port, username, password
        )
        
        if success:
            test_result = _("✅ Connection successful! The panel is accessible and login worked.")
        else:
            test_result = _(f"❌ Connection failed: {message}")
        
        # Create keyboard based on context
        if server_id == "new":
            keyboard = [
                [InlineKeyboardButton(_("💾 Save Server"), callback_data="server_save_new")],
                [InlineKeyboardButton(_("🔙 Cancel"), callback_data="server_action_list")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton(_("💾 Save Changes"), callback_data=f"server_save_{server_id}")],
                [InlineKeyboardButton(_("🔙 Back"), callback_data=f"server_view_{server_id}")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(test_result, reply_markup=reply_markup)
        return SERVER_LIST
    
    except Exception as e:
        logger.error(f"Error testing server connection: {e}")
        await query.edit_message_text(
            _(f"❌ Error testing connection: {str(e)}"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 Back"), callback_data="server_action_list")]
            ])
        )
        return SERVER_LIST

async def save_server(update: Update, context: ContextTypes.DEFAULT_TYPE, server_id: str) -> int:
    """Save server to database."""
    query = update.callback_query
    
    try:
        if server_id == "new":
            # Create new server
            new_server_data = context.user_data["new_server"]
            server = Server(
                name=new_server_data["name"],
                host=new_server_data["host"],
                port=new_server_data["port"],
                username=new_server_data["username"],
                password=new_server_data["password"],
                api_port=new_server_data["api_port"],
                location=new_server_data["location"],
                is_active=True
            )
            server.save()
            success_message = _("✅ New server added successfully!")
        else:
            # Update existing server
            server = Server.get_by_id(int(server_id))
            server.save()
            success_message = _("✅ Server updated successfully!")
        
        # Clear context data
        if "new_server" in context.user_data:
            del context.user_data["new_server"]
        if "editing_server_id" in context.user_data:
            del context.user_data["editing_server_id"]
        
        await query.edit_message_text(
            success_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 Back to Server List"), callback_data="server_action_list")]
            ])
        )
        return SERVER_LIST
    
    except Exception as e:
        logger.error(f"Error saving server: {e}")
        await query.edit_message_text(
            _(f"❌ Error saving server: {str(e)}"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 Back"), callback_data="server_action_list")]
            ])
        )
        return SERVER_LIST

async def edit_server_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, server_id: str) -> int:
    """Show edit menu for server."""
    query = update.callback_query
    server = Server.get_by_id(int(server_id))
    
    if not server:
        await query.edit_message_text(_("Server not found. It may have been deleted."))
        await list_servers(update, context)
        return SERVER_LIST
    
    # Store current server ID in context
    context.user_data["editing_server_id"] = server_id
    
    await query.edit_message_text(
        _(f"✏️ Editing server: {server.name}\n\n"
          f"Please enter the new server name:"),
    )
    return ENTER_NAME

async def confirm_delete_server(update: Update, context: ContextTypes.DEFAULT_TYPE, server_id: str) -> int:
    """Confirm server deletion."""
    query = update.callback_query
    server = Server.get_by_id(int(server_id))
    
    if not server:
        await query.edit_message_text(_("Server not found. It may have been deleted."))
        await list_servers(update, context)
        return SERVER_LIST
    
    keyboard = [
        [
            InlineKeyboardButton(_("✅ Yes, Delete"), callback_data=f"server_confirm_delete_{server_id}"),
            InlineKeyboardButton(_("❌ No, Cancel"), callback_data=f"server_view_{server_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        _(f"🗑️ Are you sure you want to delete server '{server.name}'?\n\n"
          f"⚠️ This action cannot be undone and will remove all associated data."),
        reply_markup=reply_markup
    )
    return CONFIRM_DELETE

async def delete_server(update: Update, context: ContextTypes.DEFAULT_TYPE, server_id: str) -> int:
    """Delete server from database."""
    query = update.callback_query
    server = Server.get_by_id(int(server_id))
    
    if not server:
        await query.edit_message_text(_("Server not found. It may have been deleted."))
        await list_servers(update, context)
        return SERVER_LIST
    
    try:
        # Store server name for confirmation message
        server_name = server.name
        
        # Delete the server
        Server.delete(int(server_id))
        
        await query.edit_message_text(
            _(f"✅ Server '{server_name}' has been deleted."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 Back to Server List"), callback_data="server_action_list")]
            ])
        )
        return SERVER_LIST
    
    except Exception as e:
        logger.error(f"Error deleting server: {e}")
        await query.edit_message_text(
            _(f"❌ Error deleting server: {str(e)}"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 Back"), callback_data=f"server_view_{server_id}")]
            ])
        )
        return SERVER_LIST

async def toggle_server_active(update: Update, context: ContextTypes.DEFAULT_TYPE, server_id: str) -> int:
    """Toggle server active status."""
    query = update.callback_query
    server = Server.get_by_id(int(server_id))
    
    if not server:
        await query.edit_message_text(_("Server not found. It may have been deleted."))
        await list_servers(update, context)
        return SERVER_LIST
    
    try:
        # Toggle active status
        server.is_active = not server.is_active
        server.save()
        
        status = _("activated") if server.is_active else _("deactivated")
        
        await query.edit_message_text(
            _(f"✅ Server '{server.name}' has been {status}."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 Back to Server Details"), callback_data=f"server_view_{server_id}")]
            ])
        )
        return SERVER_LIST
    
    except Exception as e:
        logger.error(f"Error toggling server status: {e}")
        await query.edit_message_text(
            _(f"❌ Error changing server status: {str(e)}"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 Back"), callback_data=f"server_view_{server_id}")]
            ])
        )
        return SERVER_LIST

def get_server_management_handlers():
    """Get the handlers for server management."""
    return [
        ConversationHandler(
            entry_points=[CommandHandler("server", server_command, filters=admin_filter)],
            states={
                SERVER_LIST: [
                    CallbackQueryHandler(handle_server_callback, pattern=r"^server_"),
                ],
                ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
                ENTER_HOST: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_host)],
                ENTER_PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_port)],
                ENTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_username)],
                ENTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_password)],
                ENTER_API_PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_api_port)],
                ENTER_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_location)],
                CONFIRM_DELETE: [
                    CallbackQueryHandler(
                        lambda u, c: delete_server(u, c, u.callback_query.data.split("_")[-1]), 
                        pattern=r"^server_confirm_delete_"
                    ),
                    CallbackQueryHandler(
                        lambda u, c: view_server_details(u, c, u.callback_query.data.split("_")[-1]), 
                        pattern=r"^server_view_"
                    )
                ],
                TEST_CONNECTION: [
                    CallbackQueryHandler(
                        lambda u, c: save_server(u, c, "new"), 
                        pattern=r"^server_save_new$"
                    ),
                    CallbackQueryHandler(
                        lambda u, c: save_server(u, c, u.callback_query.data.split("_")[-1]), 
                        pattern=r"^server_save_\d+$"
                    ),
                ],
                SAVE_SERVER: [
                    CallbackQueryHandler(
                        lambda u, c: list_servers(u, c), 
                        pattern=r"^server_action_list$"
                    ),
                ],
            },
            fallbacks=[CommandHandler("cancel", lambda u, c: list_servers(u, c))],
            name="server_management",
            persistent=False,
        )
    ] 