"""
MoonVPN Telegram Bot - Admin Handler Module.

This module provides handlers for the admin feature.
"""

from typing import List

from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    BaseHandler,
    CommandHandler
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from core.utils.helpers import admin_only
from .discount import discount_handler
from .reports import reports_handler
from .traffic import traffic_handler
from .servers import servers_handler

# Import all admin modules
from .user import user_handlers
from .payment import payment_handlers
from .account import account_handlers
from .server import server_handlers
from .service import service_handlers
from .dashboard import get_admin_dashboard_handlers, admin_dashboard
from .broadcast import broadcast_handlers
from .settings import settings_handlers
from .group_settings import group_settings_handlers
from .constants import ADMIN_MENU

# Main admin menu function
from .menu import admin_menu

# Import backup related modules
from .backup import get_backup_handlers
from .constants import (
    SELECTING_ACTION,
    SELECTING_BACKUP_ACTION,
    CONFIRMING_BACKUP_RESTORE,
    CONFIRMING_BACKUP_DELETE,
    ADMIN_BACKUP,
    BACK_TO_MAIN,
    # Backup types
    BACKUP_TYPE_FULL,
    BACKUP_TYPE_INCREMENTAL,
    BACKUP_TYPE_DIFFERENTIAL,
    BACKUP_TYPE_CONFIG,
    BACKUP_TYPE_DATABASE,
    BACKUP_TYPE_FILES,
    BACKUP_TYPE_LOGS,
    # Backup status
    BACKUP_STATUS_PENDING,
    BACKUP_STATUS_PROCESSING,
    BACKUP_STATUS_COMPLETED,
    BACKUP_STATUS_ERROR,
)

# Import new menu handlers and create callback handlers for them
from core.handlers.bot.admin.admin import admin_command
from core.handlers.bot.admin.menu import (
    admin_menu, 
    handle_general_management,
    handle_location_management,
    handle_server_management,
    handle_service_management,
    handle_user_management,
    handle_discount_marketing,
    handle_financial_reports,
    handle_bulk_messaging,
    handle_server_monitoring,
    handle_access_management,
    handle_system_settings,
    handle_backup_restore
)
from core.handlers.bot.admin.dashboard import admin_dashboard
from core.handlers.bot.admin.payment_management import payment_management
from core.handlers.bot.admin.user_management import user_management
from core.handlers.bot.admin.management_groups import get_management_groups_handlers

# Create a combined list of all handlers
def get_handlers() -> List[BaseHandler]:
    """Return all admin handlers."""
    return [
        # Main admin menu handler
        CallbackQueryHandler(admin_menu, pattern=f"^{ADMIN_MENU}$"),
        
        # Management settings redirects to the main settings menu
        CallbackQueryHandler(settings_handlers.settings_menu, pattern="^management_settings$"),
        
        # Include all handlers from each module
        *user_handlers.handlers,
        *payment_handlers.handlers,
        *account_handlers.handlers,
        *server_handlers.handlers,
        *service_handlers.handlers,
        *get_admin_dashboard_handlers(),
        *broadcast_handlers.handlers,
        *settings_handlers.handlers,
        *group_settings_handlers.handlers,
        
        # Include backup handlers
        *get_backup_handlers(),

        # Admin menu handlers
        CallbackQueryHandler(admin_menu, pattern="^admin_menu$"),
        CallbackQueryHandler(handle_general_management, pattern="^admin_general_management$"),
        CallbackQueryHandler(handle_location_management, pattern="^admin_location_management$"),
        CallbackQueryHandler(handle_server_management, pattern="^admin_server_management$"),
        CallbackQueryHandler(handle_service_management, pattern="^admin_service_management$"),
        CallbackQueryHandler(handle_user_management, pattern="^admin_user_management$"),
        CallbackQueryHandler(handle_discount_marketing, pattern="^admin_discount_marketing$"),
        CallbackQueryHandler(handle_financial_reports, pattern="^admin_financial_reports$"),
        CallbackQueryHandler(handle_bulk_messaging, pattern="^admin_bulk_messaging$"),
        CallbackQueryHandler(handle_server_monitoring, pattern="^admin_server_monitoring$"),
        CallbackQueryHandler(handle_access_management, pattern="^admin_access_management$"),
        CallbackQueryHandler(handle_system_settings, pattern="^admin_system_settings$"),
        CallbackQueryHandler(handle_backup_restore, pattern="^admin_backup_restore$"),

        # Get management groups handlers
        *get_management_groups_handlers(),

        # Dashboard handler
        admin_dashboard,

        # Payment management handler
        payment_management,

        # User management handler
        user_management,
    ]

# Function to get admin handler for use in main handlers/__init__.py
def get_admin_handler():
    """Return the admin handler for use in the main handlers/__init__.py."""
    # Create a handler that matches the admin menu pattern
    return CallbackQueryHandler(admin_menu, pattern=f"^{ADMIN_MENU}$")

# Export individual admin management functions
# These can be imported directly when needed
admin_menu = admin_menu
user_list = user_handlers.user_list
payment_list = payment_handlers.payment_list
account_list = account_handlers.account_list
server_list = server_handlers.server_list
service_list = service_handlers.service_list
dashboard = admin_dashboard
broadcast_menu = broadcast_handlers.broadcast_menu
settings_menu = settings_handlers.settings_menu
group_settings_menu = group_settings_handlers.group_settings_menu

# Export backup related constants and functions
__all__ = [
    'get_backup_handlers',
    'SELECTING_ACTION',
    'SELECTING_BACKUP_ACTION',
    'CONFIRMING_BACKUP_RESTORE',
    'CONFIRMING_BACKUP_DELETE',
    'ADMIN_MENU',
    'ADMIN_BACKUP',
    'BACK_TO_MAIN',
    'BACKUP_TYPE_FULL',
    'BACKUP_TYPE_INCREMENTAL',
    'BACKUP_TYPE_DIFFERENTIAL',
    'BACKUP_TYPE_CONFIG',
    'BACKUP_TYPE_DATABASE',
    'BACKUP_TYPE_FILES',
    'BACKUP_TYPE_LOGS',
    'BACKUP_STATUS_PENDING',
    'BACKUP_STATUS_PROCESSING',
    'BACKUP_STATUS_COMPLETED',
    'BACKUP_STATUS_ERROR',
]

from .admin import admin_command, admin_handler, get_admin_handlers

__all__ = ["admin_command", "admin_handler", "get_admin_handlers"]

# Conversation states
SELECTING_ADMIN_ACTION = 0

@admin_only
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show admin panel main menu."""
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    keyboard = [
        [
            InlineKeyboardButton("📊 گزارش درآمد", callback_data="admin_income_reports"),
            InlineKeyboardButton("🖥️ مدیریت سرورها", callback_data="admin_servers")
        ],
        [
            InlineKeyboardButton("📈 آمار مصرف", callback_data="admin_traffic_stats"),
            InlineKeyboardButton("🏷️ کدهای تخفیف", callback_data="admin_discount_codes")
        ],
        [
            InlineKeyboardButton("👥 کاربران", callback_data="admin_users"),
            InlineKeyboardButton("💬 پیام همگانی", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings"),
            InlineKeyboardButton("❌ خروج", callback_data="admin_exit")
        ]
    ]
    
    await message.edit_text(
        "🎛️ <b>پنل مدیریت</b>\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    
    return SELECTING_ADMIN_ACTION

async def admin_exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Exit from admin panel."""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "✅ از پنل مدیریت خارج شدید.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 بازگشت به منو", callback_data="start")
        ]])
    )
    
    return ConversationHandler.END

# Create admin panel conversation handler
admin_handler = ConversationHandler(
    entry_points=[
        CommandHandler("admin", admin_menu),
        CallbackQueryHandler(admin_menu, pattern="^admin_menu$")
    ],
    states={
        SELECTING_ADMIN_ACTION: [
            reports_handler,
            traffic_handler,
            servers_handler,
            discount_handler,
            CallbackQueryHandler(admin_exit, pattern="^admin_exit$")
        ]
    },
    fallbacks=[CommandHandler("cancel", admin_exit)]
)

__all__ = ['admin_handler'] 