"""
Location handler for MoonVPN Telegram Bot.

This module handles the process of changing VPN account location.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CommandHandler, 
    CallbackQueryHandler, 
    ConversationHandler
)
from telegram.constants import ParseMode

from core.config import settings
from core.database import get_db
from core.models.user import User
from core.models.vpn_account import VPNAccount
from core.models.server import Server
from core.utils.i18n import _
from core.utils.formatting import allowed_group_filter
from core.utils.helpers import require_feature
from core.utils import change_account_server

logger = logging.getLogger(__name__)

# Define states
SELECTING_ACCOUNT = 0
SELECTING_LOCATION = 1
CONFIRMING_CHANGE = 2

async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /location command to start the location change process."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started the location change process")
    
    # Get user's active accounts
    accounts = VPNAccount.get_active_accounts_by_user_id(user_id)
    
    if not accounts:
        # No active accounts
        message = _(
            "❌ **تغییر لوکیشن**\n\n"
            "شما هیچ اکانت فعالی ندارید. برای تغییر لوکیشن ابتدا نیاز است که یک اکانت VPN فعال داشته باشید."
        )
        
        keyboard = [[InlineKeyboardButton(_("🛒 خرید اکانت"), callback_data="buy_account")]]
        keyboard.append([InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
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
        return ConversationHandler.END
    
    # Create message with available accounts
    message = _(
        "🔄 **تغییر لوکیشن**\n\n"
        "لطفاً اکانتی که می‌خواهید لوکیشن آن را تغییر دهید انتخاب کنید:"
    )
    
    # Create buttons for each account
    keyboard = []
    
    for account in accounts:
        server = Server.get_by_id(account.server_id)
        if not server:
            continue
            
        # Get server location and account email (or identifier)
        location = server.location
        email = account.email or f"اکانت #{account.id}"
        
        # Format expiry date
        expiry = account.format_expiry_date()
        
        # Add button for this account
        keyboard.append([
            InlineKeyboardButton(
                f"📍 {location} - {email} - {expiry}",
                callback_data=f"select_account_{account.id}"
            )
        ])
    
    # Add navigation button
    keyboard.append([InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
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
    
    return SELECTING_ACCOUNT

async def account_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle account selection."""
    query = update.callback_query
    await query.answer()
    
    # Get selected account ID
    account_id = int(query.data.split("_")[-1])
    context.user_data["location_change"] = {
        "account_id": account_id
    }
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    if not account:
        await query.edit_message_text(
            _("❌ اطلاعات اکانت نامعتبر است. لطفاً دوباره تلاش کنید."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="change_location")]
            ])
        )
        return SELECTING_ACCOUNT
    
    # Get current server
    current_server = Server.get_by_id(account.server_id)
    if not current_server:
        await query.edit_message_text(
            _("❌ اطلاعات سرور نامعتبر است. لطفاً با پشتیبانی تماس بگیرید."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="change_location")]
            ])
        )
        return SELECTING_ACCOUNT
    
    # Get available servers (different from current)
    servers = Server.get_active_servers()
    available_servers = [s for s in servers if s.id != current_server.id]
    
    if not available_servers:
        await query.edit_message_text(
            _("❌ متأسفانه در حال حاضر هیچ سرور دیگری برای تغییر لوکیشن در دسترس نیست."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="change_location")]
            ])
        )
        return SELECTING_ACCOUNT
    
    # Create message for location selection
    message = _(
        f"🌍 **انتخاب لوکیشن جدید**\n\n"
        f"اکانت انتخابی شما:\n"
        f"• شناسه: {account.email or f'اکانت #{account.id}'}\n"
        f"• لوکیشن فعلی: {current_server.location}\n\n"
        f"لطفاً لوکیشن جدید را انتخاب کنید:"
    )
    
    # Group servers by location
    locations = {}
    for server in available_servers:
        location = server.location
        if location not in locations:
            locations[location] = []
        locations[location].append(server)
    
    # Create buttons for each location
    keyboard = []
    
    for location, servers in locations.items():
        # Use the first server ID for this location
        server_id = servers[0].id
        keyboard.append([
            InlineKeyboardButton(f"📍 {location}", callback_data=f"select_location_{server_id}")
        ])
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton(_("🔙 بازگشت به انتخاب اکانت"), callback_data="change_location")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_LOCATION

async def location_selected_for_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new location selection."""
    query = update.callback_query
    await query.answer()
    
    # Get selected server ID
    new_server_id = int(query.data.split("_")[-1])
    context.user_data["location_change"]["new_server_id"] = new_server_id
    
    # Get account and server details
    account_id = context.user_data["location_change"]["account_id"]
    account = VPNAccount.get_by_id(account_id)
    current_server = Server.get_by_id(account.server_id)
    new_server = Server.get_by_id(new_server_id)
    
    if not account or not current_server or not new_server:
        await query.edit_message_text(
            _("❌ اطلاعات نامعتبر است. لطفاً دوباره تلاش کنید."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="change_location")]
            ])
        )
        return SELECTING_ACCOUNT
    
    # Create confirmation message
    message = _(
        f"✅ **تأیید تغییر لوکیشن**\n\n"
        f"لطفاً جزئیات تغییر لوکیشن را بررسی و تأیید کنید:\n\n"
        f"• اکانت: {account.email or f'اکانت #{account.id}'}\n"
        f"• لوکیشن فعلی: {current_server.location}\n"
        f"• لوکیشن جدید: {new_server.location}\n\n"
        f"توجه: پس از تغییر لوکیشن، نیاز است که کانفیگ جدید را در اپلیکیشن خود وارد کنید."
    )
    
    # Create confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton(_("✅ تأیید و تغییر لوکیشن"), callback_data="confirm_location_change")
        ],
        [
            InlineKeyboardButton(_("🔙 بازگشت به انتخاب لوکیشن"), callback_data="back_to_location_selection")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return CONFIRMING_CHANGE

async def confirm_location_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location change confirmation."""
    query = update.callback_query
    await query.answer()
    
    # Show processing message
    await query.edit_message_text(
        _("🔄 **در حال تغییر لوکیشن...**\n\nلطفاً صبر کنید، این عملیات ممکن است چند لحظه طول بکشد."),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Get location change details
    location_change = context.user_data["location_change"]
    account_id = location_change["account_id"]
    new_server_id = location_change["new_server_id"]
    
    # Get account and servers
    account = VPNAccount.get_by_id(account_id)
    old_server = Server.get_by_id(account.server_id)
    new_server = Server.get_by_id(new_server_id)
    
    if not account or not old_server or not new_server:
        await query.edit_message_text(
            _("❌ خطایی رخ داد. اطلاعات نامعتبر است."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="change_location")]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # Perform the location change
    success, new_config = await change_account_server(account, new_server)
    
    if not success:
        # Failed to change location
        await query.edit_message_text(
            _("❌ **خطا در تغییر لوکیشن**\n\nمتأسفانه تغییر لوکیشن با خطا مواجه شد. لطفاً بعداً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # Update account in database
    old_location = old_server.location
    new_location = new_server.location
    account.server_id = new_server_id
    account.save()
    
    # Send success message with new configuration
    message = _(
        f"✅ **تغییر لوکیشن انجام شد**\n\n"
        f"اکانت شما با موفقیت از {old_location} به {new_location} منتقل شد.\n\n"
        f"برای استفاده از لوکیشن جدید، لطفاً کانفیگ زیر را در اپلیکیشن خود وارد کنید:"
    )
    
    # Send message
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Send configuration in a separate message for easier copying
    config_message = _(f"```\n{new_config}\n```")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=config_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(_("👁️ مشاهده اکانت‌های من"), callback_data="my_accounts")],
            [InlineKeyboardButton(_("🔙 بازگشت به منوی اصلی"), callback_data="main_menu")]
        ])
    )
    
    # Clear location change data
    del context.user_data["location_change"]
    
    return ConversationHandler.END

async def back_to_location_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to location selection."""
    # We'll reuse the account_selected function to show locations again
    return await account_selected(update, context)

@require_feature("change_location")
def get_location_handler():
    """Get the conversation handler for the location change process."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("location", location_command, filters=allowed_group_filter),
            CallbackQueryHandler(location_command, pattern="^change_location$")
        ],
        states={
            SELECTING_ACCOUNT: [
                CallbackQueryHandler(account_selected, pattern=r"^select_account_\d+$"),
                CallbackQueryHandler(location_command, pattern="^change_location$")
            ],
            SELECTING_LOCATION: [
                CallbackQueryHandler(location_selected_for_change, pattern=r"^select_location_\d+$"),
                CallbackQueryHandler(location_command, pattern="^change_location$")
            ],
            CONFIRMING_CHANGE: [
                CallbackQueryHandler(confirm_location_change, pattern="^confirm_location_change$"),
                CallbackQueryHandler(back_to_location_selection, pattern="^back_to_location_selection$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(location_command, pattern="^main_menu$")
        ],
        name="change_location",
        persistent=False
    ) 