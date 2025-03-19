"""
MoonVPN Telegram Bot - Account Handler Implementation.

This module provides handlers for managing VPN accounts.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from models.user import User
from core.database import get_user_accounts, get_active_servers
from core.utils.formatting import format_number, format_currency, format_bytes, format_date
from core.utils.i18n import get_text
from core.utils.formatting import allowed_group_filter, maintenance_mode_check

# States
ACCOUNT_DETAILS, ACCOUNT_STATUS, ACCOUNT_TRAFFIC, ACCOUNT_RENEW, ACCOUNT_CHANGE_SERVER = range(5)

# Callback patterns
PATTERN_ACCOUNT = "account"
PATTERN_ACCOUNT_DETAILS = "account_details_"
PATTERN_ACCOUNT_STATUS = "account_status_"
PATTERN_ACCOUNT_TRAFFIC = "account_traffic_"
PATTERN_ACCOUNT_RENEW = "account_renew_"
PATTERN_ACCOUNT_CHANGE_SERVER = "account_change_server_"
PATTERN_BACK = "back_to_"

logger = logging.getLogger(__name__)

async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /account command.
    
    This command displays the account management menu.
    """
    return await account_handler(update, context)

async def account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the account button callback.
    
    This function displays the user's VPN accounts.
    """
    user = update.effective_user
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    # Get user accounts from database
    accounts = get_user_accounts(user.id)
    
    if not accounts:
        # No accounts available
        text = (
            "⚠️ <b>شما هیچ اکانت VPN فعالی ندارید.</b>\n\n"
            "برای خرید اکانت جدید، از منوی اصلی گزینه «خرید اکانت» را انتخاب کنید."
        )
        
        keyboard = [
            [InlineKeyboardButton("🛒 خرید اکانت", callback_data="buy")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        return ConversationHandler.END
    
    # Create a beautiful message with account options
    text = (
        "👤 <b>مدیریت اکانت‌های VPN</b>\n\n"
        "اکانت‌های VPN شما:\n\n"
    )
    
    # Create keyboard with account options
    keyboard = []
    
    # Add accounts to keyboard
    for i, account in enumerate(accounts, 1):
        account_id = account.get('id')
        server_location = account.get('location', 'نامشخص')
        status = account.get('status', 'inactive')
        expiry_date = account.get('expiry_date')
        
        # Format expiry date
        if expiry_date:
            try:
                expiry_date_str = format_date(expiry_date.isoformat())
            except:
                expiry_date_str = str(expiry_date)
        else:
            expiry_date_str = "نامشخص"
        
        # Format status
        if status == 'active':
            status_str = "🟢 فعال"
        elif status == 'expired':
            status_str = "🔴 منقضی شده"
        elif status == 'disabled':
            status_str = "⚫ غیرفعال"
        else:
            status_str = "⚪ نامشخص"
        
        # Add account details to text
        text += f"{i}. <b>سرور {server_location}</b> - {status_str} - انقضا: {expiry_date_str}\n"
        
        # Add button for this account
        keyboard.append([
            InlineKeyboardButton(
                f"🔑 اکانت {i} - سرور {server_location}",
                callback_data=f"{PATTERN_ACCOUNT_DETAILS}{account_id}"
            )
        ])
    
    # Add a separator
    text += "\n"
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ACCOUNT_DETAILS

async def account_details_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle account details selection.
    
    This function displays detailed information about the selected account.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    account_id = int(query.data.replace(PATTERN_ACCOUNT_DETAILS, ""))
    
    # Store selected account ID in context
    context.user_data['selected_account_id'] = account_id
    
    # Get user accounts from database
    accounts = get_user_accounts(update.effective_user.id)
    
    # Find the selected account
    selected_account = next((account for account in accounts if account.get('id') == account_id), None)
    
    if not selected_account:
        # Account not found
        await query.edit_message_text(
            text="⚠️ اکانت انتخاب شده یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data=PATTERN_ACCOUNT)
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Store selected account details in context
    context.user_data['selected_account'] = selected_account
    
    # Create a beautiful account details message
    server_name = selected_account.get('name', 'بدون نام')
    server_location = selected_account.get('location', 'نامشخص')
    server_host = selected_account.get('host', 'نامشخص')
    server_port = selected_account.get('port', 0)
    
    status = selected_account.get('status', 'inactive')
    expiry_date = selected_account.get('expiry_date')
    traffic_used = selected_account.get('traffic_used', 0)
    traffic_limit = selected_account.get('traffic_limit', 0)
    
    # Format expiry date
    if expiry_date:
        try:
            expiry_date_str = format_date(expiry_date.isoformat())
        except:
            expiry_date_str = str(expiry_date)
    else:
        expiry_date_str = "نامشخص"
    
    # Format status
    if status == 'active':
        status_str = "🟢 فعال"
    elif status == 'expired':
        status_str = "🔴 منقضی شده"
    elif status == 'disabled':
        status_str = "⚫ غیرفعال"
    else:
        status_str = "⚪ نامشخص"
    
    # Format traffic
    traffic_used_str = format_bytes(traffic_used * 1024 * 1024 * 1024)  # Convert GB to bytes
    traffic_limit_str = format_bytes(traffic_limit * 1024 * 1024 * 1024)  # Convert GB to bytes
    
    # Calculate traffic percentage
    if traffic_limit > 0:
        traffic_percentage = min(100, (traffic_used / traffic_limit) * 100)
    else:
        traffic_percentage = 0
    
    # Create traffic progress bar
    progress_bar_length = 10
    filled_length = int(progress_bar_length * traffic_percentage / 100)
    progress_bar = '█' * filled_length + '░' * (progress_bar_length - filled_length)
    
    text = (
        f"🔑 <b>جزئیات اکانت VPN</b>\n\n"
        f"<b>وضعیت:</b> {status_str}\n"
        f"<b>سرور:</b> {server_name} ({server_location})\n"
        f"<b>تاریخ انقضا:</b> {expiry_date_str}\n\n"
        f"<b>مصرف ترافیک:</b>\n"
        f"{progress_bar} {traffic_percentage:.1f}%\n"
        f"{traffic_used_str} از {traffic_limit_str}\n\n"
    )
    
    # Add configuration details if account is active
    if status == 'active':
        text += (
            f"<b>تنظیمات اتصال:</b>\n"
            f"• آدرس سرور: <code>{server_host}</code>\n"
            f"• پورت: <code>{server_port}</code>\n"
        )
    
    # Create keyboard with account management options
    keyboard = [
        [
            InlineKeyboardButton("📊 وضعیت اکانت", callback_data=f"{PATTERN_ACCOUNT_STATUS}{account_id}"),
            InlineKeyboardButton("📈 مصرف ترافیک", callback_data=f"{PATTERN_ACCOUNT_TRAFFIC}{account_id}")
        ],
        [
            InlineKeyboardButton("🔄 تمدید اکانت", callback_data=f"{PATTERN_ACCOUNT_RENEW}{account_id}"),
            InlineKeyboardButton("🌍 تغییر سرور", callback_data=f"{PATTERN_ACCOUNT_CHANGE_SERVER}{account_id}")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data=PATTERN_ACCOUNT)
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ACCOUNT_DETAILS

async def account_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle account status request.
    
    This function displays detailed status information about the selected account.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    account_id = int(query.data.replace(PATTERN_ACCOUNT_STATUS, ""))
    
    # Get user accounts from database
    accounts = get_user_accounts(update.effective_user.id)
    
    # Find the selected account
    selected_account = next((account for account in accounts if account.get('id') == account_id), None)
    
    if not selected_account:
        # Account not found
        await query.edit_message_text(
            text="⚠️ اکانت انتخاب شده یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data=PATTERN_ACCOUNT)
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Create a beautiful account status message
    server_name = selected_account.get('name', 'بدون نام')
    server_location = selected_account.get('location', 'نامشخص')
    
    status = selected_account.get('status', 'inactive')
    created_at = selected_account.get('created_at')
    expiry_date = selected_account.get('expiry_date')
    
    # Format dates
    if created_at:
        try:
            created_at_str = format_date(created_at.isoformat())
        except:
            created_at_str = str(created_at)
    else:
        created_at_str = "نامشخص"
        
    if expiry_date:
        try:
            expiry_date_str = format_date(expiry_date.isoformat())
            
            # Calculate days remaining
            now = datetime.now()
            if isinstance(expiry_date, str):
                expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
            
            days_remaining = (expiry_date - now).days
            
            if days_remaining > 0:
                days_remaining_str = f"{days_remaining} روز"
            elif days_remaining == 0:
                days_remaining_str = "کمتر از یک روز"
            else:
                days_remaining_str = "منقضی شده"
        except:
            expiry_date_str = str(expiry_date)
            days_remaining_str = "نامشخص"
    else:
        expiry_date_str = "نامشخص"
        days_remaining_str = "نامشخص"
    
    # Format status
    if status == 'active':
        status_str = "🟢 فعال"
        status_details = "اکانت شما فعال است و می‌توانید از آن استفاده کنید."
    elif status == 'expired':
        status_str = "🔴 منقضی شده"
        status_details = "اکانت شما منقضی شده است. برای استفاده مجدد، آن را تمدید کنید."
    elif status == 'disabled':
        status_str = "⚫ غیرفعال"
        status_details = "اکانت شما غیرفعال شده است. لطفاً با پشتیبانی تماس بگیرید."
    else:
        status_str = "⚪ نامشخص"
        status_details = "وضعیت اکانت شما نامشخص است. لطفاً با پشتیبانی تماس بگیرید."
    
    text = (
        f"📊 <b>وضعیت اکانت VPN</b>\n\n"
        f"<b>سرور:</b> {server_name} ({server_location})\n"
        f"<b>وضعیت:</b> {status_str}\n"
        f"<b>تاریخ ایجاد:</b> {created_at_str}\n"
        f"<b>تاریخ انقضا:</b> {expiry_date_str}\n"
        f"<b>زمان باقی‌مانده:</b> {days_remaining_str}\n\n"
        f"{status_details}"
    )
    
    # Create keyboard with options
    keyboard = [
        [
            InlineKeyboardButton("🔄 تمدید اکانت", callback_data=f"{PATTERN_ACCOUNT_RENEW}{account_id}")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"{PATTERN_ACCOUNT_DETAILS}{account_id}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ACCOUNT_DETAILS

async def account_traffic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle account traffic request.
    
    This function displays detailed traffic information about the selected account.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    account_id = int(query.data.replace(PATTERN_ACCOUNT_TRAFFIC, ""))
    
    # Get user accounts from database
    accounts = get_user_accounts(update.effective_user.id)
    
    # Find the selected account
    selected_account = next((account for account in accounts if account.get('id') == account_id), None)
    
    if not selected_account:
        # Account not found
        await query.edit_message_text(
            text="⚠️ اکانت انتخاب شده یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data=PATTERN_ACCOUNT)
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Create a beautiful account traffic message
    server_name = selected_account.get('name', 'بدون نام')
    server_location = selected_account.get('location', 'نامشخص')
    
    traffic_used = selected_account.get('traffic_used', 0)
    traffic_limit = selected_account.get('traffic_limit', 0)
    
    # Format traffic
    traffic_used_str = format_bytes(traffic_used * 1024 * 1024 * 1024)  # Convert GB to bytes
    traffic_limit_str = format_bytes(traffic_limit * 1024 * 1024 * 1024)  # Convert GB to bytes
    
    # Calculate traffic percentage
    if traffic_limit > 0:
        traffic_percentage = min(100, (traffic_used / traffic_limit) * 100)
    else:
        traffic_percentage = 0
    
    # Create traffic progress bar
    progress_bar_length = 10
    filled_length = int(progress_bar_length * traffic_percentage / 100)
    progress_bar = '█' * filled_length + '░' * (progress_bar_length - filled_length)
    
    # Calculate remaining traffic
    remaining_traffic = max(0, traffic_limit - traffic_used)
    remaining_traffic_str = format_bytes(remaining_traffic * 1024 * 1024 * 1024)  # Convert GB to bytes
    
    text = (
        f"📈 <b>مصرف ترافیک</b>\n\n"
        f"<b>سرور:</b> {server_name} ({server_location})\n\n"
        f"<b>مصرف ترافیک:</b>\n"
        f"{progress_bar} {traffic_percentage:.1f}%\n"
        f"<b>استفاده شده:</b> {traffic_used_str}\n"
        f"<b>کل ترافیک:</b> {traffic_limit_str}\n"
        f"<b>باقی‌مانده:</b> {remaining_traffic_str}\n\n"
    )
    
    # Add warning if traffic is running low
    if traffic_percentage >= 80:
        text += (
            "⚠️ <b>هشدار:</b> ترافیک شما رو به اتمام است. برای جلوگیری از قطع سرویس، "
            "لطفاً اکانت خود را تمدید کنید یا ترافیک اضافی خریداری نمایید.\n\n"
        )
    
    # Create keyboard with options
    keyboard = [
        [
            InlineKeyboardButton("🔄 خرید ترافیک اضافی", callback_data=f"{PATTERN_ACCOUNT_RENEW}{account_id}")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"{PATTERN_ACCOUNT_DETAILS}{account_id}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ACCOUNT_DETAILS

async def account_renew_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle account renewal request.
    
    This function displays renewal options for the selected account.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    account_id = int(query.data.replace(PATTERN_ACCOUNT_RENEW, ""))
    
    # Get user accounts from database
    accounts = get_user_accounts(update.effective_user.id)
    
    # Find the selected account
    selected_account = next((account for account in accounts if account.get('id') == account_id), None)
    
    if not selected_account:
        # Account not found
        await query.edit_message_text(
            text="⚠️ اکانت انتخاب شده یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data=PATTERN_ACCOUNT)
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Create a beautiful account renewal message
    server_name = selected_account.get('name', 'بدون نام')
    server_location = selected_account.get('location', 'نامشخص')
    
    text = (
        f"🔄 <b>تمدید اکانت VPN</b>\n\n"
        f"<b>سرور:</b> {server_name} ({server_location})\n\n"
        f"لطفاً یکی از گزینه‌های تمدید زیر را انتخاب کنید:\n\n"
    )
    
    # Create keyboard with renewal options
    keyboard = [
        [
            InlineKeyboardButton("🔄 تمدید یک ماهه - 150,000 تومان", callback_data="buy")
        ],
        [
            InlineKeyboardButton("🔄 تمدید سه ماهه - 400,000 تومان", callback_data="buy")
        ],
        [
            InlineKeyboardButton("🔄 تمدید شش ماهه - 750,000 تومان", callback_data="buy")
        ],
        [
            InlineKeyboardButton("🔄 تمدید یک ساله - 1,400,000 تومان", callback_data="buy")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"{PATTERN_ACCOUNT_DETAILS}{account_id}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ACCOUNT_DETAILS

async def account_change_server_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle account server change request.
    
    This function displays server change options for the selected account.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    account_id = int(query.data.replace(PATTERN_ACCOUNT_CHANGE_SERVER, ""))
    
    # Get user accounts from database
    accounts = get_user_accounts(update.effective_user.id)
    
    # Find the selected account
    selected_account = next((account for account in accounts if account.get('id') == account_id), None)
    
    if not selected_account:
        # Account not found
        await query.edit_message_text(
            text="⚠️ اکانت انتخاب شده یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data=PATTERN_ACCOUNT)
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Get active servers
    servers = get_active_servers()
    
    if not servers:
        # No servers available
        await query.edit_message_text(
            text="⚠️ در حال حاضر هیچ سروری در دسترس نیست. لطفاً بعداً مراجعه کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"{PATTERN_ACCOUNT_DETAILS}{account_id}")
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Create a beautiful server change message
    current_server_name = selected_account.get('name', 'بدون نام')
    current_server_location = selected_account.get('location', 'نامشخص')
    
    text = (
        f"🌍 <b>تغییر سرور VPN</b>\n\n"
        f"<b>سرور فعلی:</b> {current_server_name} ({current_server_location})\n\n"
        f"لطفاً سرور جدید خود را انتخاب کنید:\n\n"
    )
    
    # Create keyboard with server options
    keyboard = []
    
    # Group servers by location for better UI
    locations = {}
    for server in servers:
        location = server.get('location', 'نامشخص')
        if location not in locations:
            locations[location] = []
        locations[location].append(server)
    
    # Add servers to keyboard grouped by location
    for location, location_servers in sorted(locations.items()):
        # Skip current server location
        if location == current_server_location:
            continue
            
        # Add a header for this location group
        text += f"🌐 <b>سرورهای {location}:</b>\n"
        
        # Add servers for this location
        for server in location_servers:
            server_id = server.get('id')
            name = server.get('name', 'بدون نام')
            
            # Add server details to text
            text += f"• {name}\n"
            
            # Add button for this server
            keyboard.append([
                InlineKeyboardButton(
                    f"🖥️ {name} ({location})",
                    callback_data=f"buy"  # This would normally link to a server change flow
                )
            ])
        
        # Add a separator between location groups
        text += "\n"
    
    # Add note about server change
    text += (
        "📝 <b>توجه:</b> تغییر سرور ممکن است باعث تغییر در کیفیت اتصال شود. "
        "همچنین، برخی از سرورها ممکن است هزینه‌ی اضافی داشته باشند.\n\n"
    )
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"{PATTERN_ACCOUNT_DETAILS}{account_id}")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ACCOUNT_DETAILS

def get_account_handlers() -> List[Any]:
    """Return all handlers related to the account feature."""
    
    # Create conversation handler for account management flow
    account_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("account", account_command),
            CallbackQueryHandler(account_handler, pattern=f"^{PATTERN_ACCOUNT}$")
        ],
        states={
            ACCOUNT_DETAILS: [
                CallbackQueryHandler(account_details_handler, pattern=f"^{PATTERN_ACCOUNT_DETAILS}\\d+$"),
                CallbackQueryHandler(account_status_handler, pattern=f"^{PATTERN_ACCOUNT_STATUS}\\d+$"),
                CallbackQueryHandler(account_traffic_handler, pattern=f"^{PATTERN_ACCOUNT_TRAFFIC}\\d+$"),
                CallbackQueryHandler(account_renew_handler, pattern=f"^{PATTERN_ACCOUNT_RENEW}\\d+$"),
                CallbackQueryHandler(account_change_server_handler, pattern=f"^{PATTERN_ACCOUNT_CHANGE_SERVER}\\d+$"),
                CallbackQueryHandler(account_handler, pattern=f"^{PATTERN_ACCOUNT}$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(account_handler, pattern=f"^{PATTERN_ACCOUNT}$"),
            CommandHandler("cancel", account_handler)
        ],
        name="account_conversation",
        persistent=False
    )
    
    return [account_conv_handler] 