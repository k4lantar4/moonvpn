"""
MoonVPN Telegram Bot - Change Location Handler.

This module handles the user request to change their VPN server location.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, CommandHandler
from telegram.constants import ParseMode

from core.utils.i18n import _
import api
from models.user import User
from models.server import Server
from models.vpn_account import VPNAccount

logger = logging.getLogger(__name__)

# Define states
SELECTING_ACCOUNT = 0
SELECTING_LOCATION = 1
CONFIRMING_CHANGE = 2

# Patterns for callback data
PATTERN_CHANGE_LOCATION = r"^change_location$"
PATTERN_SELECT_ACCOUNT = r"^select_account:(\d+)$"
PATTERN_SELECT_LOCATION = r"^select_location:(\d+)$"
PATTERN_CONFIRM_CHANGE = r"^confirm_change:(\d+):(\d+)$"
PATTERN_CANCEL_CHANGE = r"^cancel_change$"

async def change_location_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /change_location command."""
    user = update.effective_user
    logger.info(f"User {user.id} started the change location process")
    
    # Get user from database
    db_user = User.get_by_telegram_id(user.id)
    if not db_user:
        await update.message.reply_text(
            _("❌ شما ابتدا باید ثبت نام کنید. لطفاً از دستور /start استفاده کنید.")
        )
        return ConversationHandler.END
    
    # Get user's active accounts
    accounts = VPNAccount.get_active_by_user_id(db_user.id)
    
    if not accounts:
        # No active accounts
        message = _(
            "❌ **تغییر مکان سرور**\n\n"
            "شما هیچ اکانت فعالی ندارید. ابتدا باید یک اکانت VPN خریداری کنید."
        )
        keyboard = [[InlineKeyboardButton(_("🛒 خرید اکانت"), callback_data="buy"),
                     InlineKeyboardButton(_("🔙 بازگشت"), callback_data="main_menu")]]
                     
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # Display list of accounts
    message = _(
        "🌍 **تغییر مکان سرور**\n\n"
        "لطفاً اکانتی که می‌خواهید مکان آن را تغییر دهید انتخاب کنید:"
    )
    
    keyboard = []
    for account in accounts:
        server = account.get_server()
        remaining_days = account.days_left()
        
        account_label = _("📡 {server_name} - {days} روز مانده").format(
            server_name=server.name if server else "نامشخص",
            days=remaining_days
        )
        keyboard.append([InlineKeyboardButton(account_label, callback_data=f"select_account:{account.id}")])
    
    keyboard.append([InlineKeyboardButton(_("🔙 بازگشت"), callback_data="main_menu")])
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return SELECTING_ACCOUNT

async def account_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the account selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract account_id from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    
    # Save account_id in context
    context.user_data["change_location"] = {"account_id": account_id}
    
    # Get available locations
    active_servers = Server.get_active()
    
    if not active_servers:
        # No active servers available
        message = _(
            "❌ **تغییر مکان سرور**\n\n"
            "متأسفانه در حال حاضر هیچ سرور فعالی موجود نیست. لطفاً بعداً مجدد تلاش کنید."
        )
        keyboard = [[InlineKeyboardButton(_("🔙 بازگشت"), callback_data="main_menu")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # Get current account's server
    account = VPNAccount.get_by_id(account_id)
    current_server = account.get_server() if account else None
    
    # Display available locations
    message = _(
        "🌍 **تغییر مکان سرور**\n\n"
        "مکان فعلی: **{current_location}**\n\n"
        "لطفاً مکان جدید را انتخاب کنید:"
    ).format(current_location=current_server.name if current_server else "نامشخص")
    
    keyboard = []
    
    # Group servers by location
    locations: Dict[str, List[Server]] = {}
    for server in active_servers:
        if server.location not in locations:
            locations[server.location] = []
        locations[server.location].append(server)
    
    # Add buttons for each location
    for location, servers in locations.items():
        # Skip the current location
        if current_server and location == current_server.location:
            continue
            
        # Count available servers in this location
        count = len(servers)
        server_id = servers[0].id if servers else 0
        
        location_label = _("🌐 {location} ({count} سرور)").format(
            location=location, 
            count=count
        )
        keyboard.append([InlineKeyboardButton(location_label, callback_data=f"select_location:{server_id}")])
    
    keyboard.append([InlineKeyboardButton(_("🔙 بازگشت"), callback_data="main_menu")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return SELECTING_LOCATION

async def location_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the location selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract server_id from callback data
    callback_data = query.data
    server_id = int(callback_data.split(":")[1])
    
    # Save server_id in context
    context.user_data["change_location"]["server_id"] = server_id
    
    # Get account and server details
    account_id = context.user_data["change_location"]["account_id"]
    account = VPNAccount.get_by_id(account_id)
    current_server = account.get_server() if account else None
    new_server = Server.get_by_id(server_id)
    
    if not account or not new_server:
        # Invalid account or server
        message = _(
            "❌ **تغییر مکان سرور**\n\n"
            "خطایی رخ داد. لطفاً بعداً مجدد تلاش کنید."
        )
        keyboard = [[InlineKeyboardButton(_("🔙 بازگشت"), callback_data="main_menu")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # Display confirmation message
    message = _(
        "🌍 **تغییر مکان سرور**\n\n"
        "آیا از تغییر مکان اطمینان دارید؟\n\n"
        "از: **{current_location}**\n"
        "به: **{new_location}**\n\n"
        "⚠️ توجه: پس از تغییر مکان، باید تنظیمات جدید را دانلود و استفاده کنید."
    ).format(
        current_location=current_server.name if current_server else "نامشخص",
        new_location=new_server.name
    )
    
    keyboard = [
        [InlineKeyboardButton(_("✅ تایید"), callback_data=f"confirm_change:{account_id}:{server_id}")],
        [InlineKeyboardButton(_("❌ لغو"), callback_data="cancel_change")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return CONFIRMING_CHANGE

async def confirm_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the confirmation of location change."""
    query = update.callback_query
    await query.answer()
    
    # Extract account_id and server_id from callback data
    callback_data = query.data
    parts = callback_data.split(":")
    account_id = int(parts[1])
    server_id = int(parts[2])
    
    # Get account and server details
    account = VPNAccount.get_by_id(account_id)
    new_server = Server.get_by_id(server_id)
    
    if not account or not new_server:
        # Invalid account or server
        message = _(
            "❌ **تغییر مکان سرور**\n\n"
            "خطایی رخ داد. لطفاً بعداً مجدد تلاش کنید."
        )
        keyboard = [[InlineKeyboardButton(_("🔙 بازگشت"), callback_data="main_menu")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # Change the server
    success = api.change_account_server(account_id, server_id)
    
    if success:
        # Update database
        account.server_id = server_id
        account.update()
        
        # Prepare download buttons for new configuration
        config_buttons = [
            [
                InlineKeyboardButton(_("📥 دانلود تنظیمات"), callback_data=f"download_config:{account_id}"),
                InlineKeyboardButton(_("📱 کیوآر کد"), callback_data=f"show_qrcode:{account_id}")
            ]
        ]
        
        # Success message
        message = _(
            "✅ **تغییر مکان سرور انجام شد**\n\n"
            "تبریک! مکان سرور VPN شما با موفقیت به **{new_location}** تغییر یافت.\n\n"
            "لطفاً تنظیمات جدید را دانلود کرده و در برنامه خود وارد کنید."
        ).format(new_location=new_server.name)
        
        keyboard = config_buttons + [[InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Error message
        message = _(
            "❌ **خطا در تغییر مکان سرور**\n\n"
            "متأسفانه در تغییر مکان سرور خطایی رخ داد. لطفاً بعداً مجدد تلاش کنید."
        )
        
        keyboard = [[InlineKeyboardButton(_("🔙 بازگشت"), callback_data="main_menu")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    return ConversationHandler.END

async def cancel_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the cancellation of location change."""
    query = update.callback_query
    await query.answer()
    
    # Clear user data
    if "change_location" in context.user_data:
        del context.user_data["change_location"]
    
    # Cancellation message
    message = _(
        "❌ **تغییر مکان لغو شد**\n\n"
        "شما تغییر مکان سرور را لغو کردید. سرور شما بدون تغییر باقی می‌ماند."
    )
    
    keyboard = [[InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")]]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ConversationHandler.END

def get_change_location_handler() -> ConversationHandler:
    """Return the conversation handler for change location."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("change_location", change_location_command),
            CallbackQueryHandler(change_location_command, pattern=PATTERN_CHANGE_LOCATION)
        ],
        states={
            SELECTING_ACCOUNT: [
                CallbackQueryHandler(account_selected, pattern=PATTERN_SELECT_ACCOUNT)
            ],
            SELECTING_LOCATION: [
                CallbackQueryHandler(location_selected, pattern=PATTERN_SELECT_LOCATION)
            ],
            CONFIRMING_CHANGE: [
                CallbackQueryHandler(confirm_change, pattern=PATTERN_CONFIRM_CHANGE),
                CallbackQueryHandler(cancel_change, pattern=PATTERN_CANCEL_CHANGE)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_change, pattern=PATTERN_CANCEL_CHANGE),
            CallbackQueryHandler(cancel_change, pattern="main_menu")
        ],
        name="change_location",
        persistent=False
    ) 