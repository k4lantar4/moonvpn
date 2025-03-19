"""
Account management handlers.

This module contains handlers for managing VPN accounts.
"""

from datetime import datetime, timedelta
import pytz
import json
from typing import Dict, List, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler

from utils import get_text, format_number, format_date
from decorators import require_admin
from api_client import (
    get_accounts,
    get_account,
    update_account,
    delete_account,
    reset_account_traffic,
    change_account_server,
    get_account_config,
    get_servers,
)
from .constants import SELECTING_ACCOUNT, ADMIN_MENU

# Define handlers list to be imported in __init__.py
handlers = []

@require_admin
async def account_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of VPN accounts."""
    query = update.callback_query
    await query.answer()
    
    # Get all accounts
    accounts = get_accounts()
    
    if not accounts:
        await query.edit_message_text(
            "🔑 اکانت‌های VPN\n\n"
            "هیچ اکانتی یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_menu")]
            ])
        )
    else:
        # Sort accounts by status and then by creation date
        accounts.sort(key=lambda x: (not x.get("is_active", True), x.get("created_at", "")), reverse=False)
        
        message = "🔑 اکانت‌های VPN\n\n"
        
        keyboard = []
        # Show only first 10 accounts to avoid message size limits
        for account in accounts[:10]:
            # Format account status
            status_emoji = "🟢" if account.get("is_active", True) else "🔴"
            email = account.get("email", "")
            server_name = account.get("server", {}).get("name", "")
            account_id = account.get("id", "")
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{status_emoji} {email} ({server_name})",
                    callback_data=f"account_details:{account_id}"
                )
            ])
        
        # Add pagination if there are more than 10 accounts
        if len(accounts) > 10:
            keyboard.append([
                InlineKeyboardButton("📄 بعدی", callback_data="account_list:2")
            ])
        
        keyboard.append([
            InlineKeyboardButton("➕ اکانت جدید", callback_data="account_create"),
            InlineKeyboardButton("🔄 به‌روزرسانی", callback_data="admin_accounts")
        ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_menu")
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_list_paginated(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show paginated list of VPN accounts."""
    query = update.callback_query
    await query.answer()
    
    # Get page number from callback data
    page = int(query.data.split(":")[1])
    
    # Get all accounts
    accounts = get_accounts()
    
    if not accounts:
        await query.edit_message_text(
            "🔑 اکانت‌های VPN\n\n"
            "هیچ اکانتی یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_menu")]
            ])
        )
        return SELECTING_ACCOUNT
    
    # Sort accounts by status and then by creation date
    accounts.sort(key=lambda x: (not x.get("is_active", True), x.get("created_at", "")), reverse=False)
    
    # Calculate pagination
    items_per_page = 10
    total_pages = (len(accounts) + items_per_page - 1) // items_per_page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(accounts))
    
    message = f"🔑 اکانت‌های VPN (صفحه {page}/{total_pages})\n\n"
    
    keyboard = []
    for account in accounts[start_idx:end_idx]:
        # Format account status
        status_emoji = "🟢" if account.get("is_active", True) else "🔴"
        email = account.get("email", "")
        server_name = account.get("server", {}).get("name", "")
        account_id = account.get("id", "")
        
        keyboard.append([
            InlineKeyboardButton(
                f"{status_emoji} {email} ({server_name})",
                callback_data=f"account_details:{account_id}"
            )
        ])
    
    # Add pagination buttons
    pagination = []
    if page > 1:
        pagination.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"account_list:{page-1}"))
    if page < total_pages:
        pagination.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"account_list:{page+1}"))
    if pagination:
        keyboard.append(pagination)
    
    keyboard.append([
        InlineKeyboardButton("➕ اکانت جدید", callback_data="account_create"),
        InlineKeyboardButton("🔄 به‌روزرسانی", callback_data="admin_accounts")
    ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_menu")
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show account details and management options."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID from callback data
    account_id = int(query.data.split(":")[1])
    
    # Store in context for later use
    context.user_data["current_account_id"] = account_id
    
    # Get account details
    account = get_account(account_id)
    
    if not account:
        await query.edit_message_text(
            "❌ خطا\n\n"
            "اکانت مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data="admin_accounts")]
            ])
        )
        return SELECTING_ACCOUNT
    
    # Format account information
    email = account.get("email", "")
    server_name = account.get("server", {}).get("name", "")
    protocol = account.get("protocol", "")
    
    # Traffic information
    upload_gb = account.get("upload", 0) / (1024 ** 3)
    download_gb = account.get("download", 0) / (1024 ** 3)
    total_gb = account.get("total_traffic", 0) / (1024 ** 3)
    
    # Traffic limit (if any)
    limit_gb = account.get("traffic_limit", 0) / (1024 ** 3) if account.get("traffic_limit", 0) > 0 else 0
    traffic_status = f"{total_gb:.2f} GB" if limit_gb == 0 else f"{total_gb:.2f} GB / {limit_gb:.2f} GB"
    
    # Expiry information
    expiry_date = account.get("expiry_date", None)
    if expiry_date:
        expiry_date_obj = datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
        expiry_str = expiry_date_obj.strftime("%Y-%m-%d %H:%M")
    else:
        expiry_str = "بدون محدودیت"
    
    # User information (if linked to a user)
    user_info = ""
    if account.get("user", None):
        user = account.get("user", {})
        username = user.get("username", "")
        user_id = user.get("id", "")
        user_info = f"👤 کاربر: {username} (ID: {user_id})\n"
    
    # Create message
    status_emoji = "🟢" if account.get("is_active", True) else "🔴"
    message = (
        f"🔑 جزئیات اکانت VPN\n\n"
        f"📧 ایمیل: {email}\n"
        f"🖥️ سرور: {server_name}\n"
        f"🔌 پروتکل: {protocol}\n"
        f"🚦 وضعیت: {status_emoji} {'فعال' if account.get('is_active', True) else 'غیرفعال'}\n"
        f"📊 ترافیک مصرفی: {traffic_status}\n"
        f"📤 آپلود: {upload_gb:.2f} GB\n"
        f"📥 دانلود: {download_gb:.2f} GB\n"
        f"⏱️ تاریخ انقضا: {expiry_str}\n"
        f"{user_info}\n"
        f"🕒 ایجاد شده در: {account.get('created_at', '')[:10]}"
    )
    
    # Create keyboard with management options
    is_active = account.get("is_active", True)
    keyboard = [
        [
            InlineKeyboardButton(
                "🔴 غیرفعال کردن" if is_active else "🟢 فعال کردن", 
                callback_data=f"account_toggle:{account_id}:{not is_active}"
            ),
            InlineKeyboardButton("🔄 ریست ترافیک", callback_data=f"account_reset_traffic:{account_id}")
        ],
        [
            InlineKeyboardButton("🔄 تغییر سرور", callback_data=f"account_change_server:{account_id}"),
            InlineKeyboardButton("📋 دریافت کانفیگ", callback_data=f"account_get_config:{account_id}")
        ],
        [
            InlineKeyboardButton("⏱️ تمدید", callback_data=f"account_extend:{account_id}"),
            InlineKeyboardButton("❌ حذف اکانت", callback_data=f"account_delete:{account_id}")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data="admin_accounts")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_toggle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle active status of a VPN account."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID and new status from callback data
    parts = query.data.split(":")
    account_id = int(parts[1])
    new_status = parts[2] == "True"
    
    # Update account status
    result = update_account(account_id, {"is_active": new_status})
    
    if result:
        status_text = "فعال" if new_status else "غیرفعال"
        await query.edit_message_text(
            f"✅ وضعیت اکانت با موفقیت به {status_text} تغییر یافت.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    else:
        await query.edit_message_text(
            "❌ خطا در تغییر وضعیت اکانت.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_reset_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Reset traffic counters for a VPN account."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID from callback data
    account_id = int(query.data.split(":")[1])
    
    # Reset traffic
    result = reset_account_traffic(account_id)
    
    if result:
        await query.edit_message_text(
            "✅ شمارنده‌های ترافیک با موفقیت ریست شدند.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    else:
        await query.edit_message_text(
            "❌ خطا در ریست کردن شمارنده‌های ترافیک.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm deletion of a VPN account."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID from callback data
    account_id = int(query.data.split(":")[1])
    
    # Get account details for confirmation
    account = get_account(account_id)
    
    if not account:
        await query.edit_message_text(
            "❌ خطا\n\n"
            "اکانت مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data="admin_accounts")]
            ])
        )
        return SELECTING_ACCOUNT
    
    email = account.get("email", "")
    server_name = account.get("server", {}).get("name", "")
    
    await query.edit_message_text(
        f"⚠️ آیا از حذف اکانت زیر اطمینان دارید؟\n\n"
        f"📧 ایمیل: {email}\n"
        f"🖥️ سرور: {server_name}\n\n"
        f"این عملیات غیرقابل بازگشت است!",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"account_delete_confirmed:{account_id}"),
                InlineKeyboardButton("❌ خیر، لغو", callback_data=f"account_details:{account_id}")
            ]
        ])
    )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_delete_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Delete a VPN account after confirmation."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID from callback data
    account_id = int(query.data.split(":")[1])
    
    # Delete account
    result = delete_account(account_id)
    
    if result:
        await query.edit_message_text(
            "✅ اکانت با موفقیت حذف شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data="admin_accounts")]
            ])
        )
    else:
        await query.edit_message_text(
            "❌ خطا در حذف اکانت.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_get_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get configuration for a VPN account."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID from callback data
    account_id = int(query.data.split(":")[1])
    
    # Get account config
    config = get_account_config(account_id)
    
    if config and not config.get("error", None):
        # Format the config based on available formats
        formats = []
        if "vmess" in config:
            formats.append(InlineKeyboardButton("VMess", callback_data=f"account_config:{account_id}:vmess"))
        if "vless" in config:
            formats.append(InlineKeyboardButton("VLess", callback_data=f"account_config:{account_id}:vless"))
        if "trojan" in config:
            formats.append(InlineKeyboardButton("Trojan", callback_data=f"account_config:{account_id}:trojan"))
        
        await query.edit_message_text(
            "📋 لطفاً فرمت کانفیگ مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                formats,
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    else:
        error = config.get("error", "خطای نامشخص")
        await query.edit_message_text(
            f"❌ خطا در دریافت کانفیگ:\n{error}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_show_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the selected config format."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID and format from callback data
    parts = query.data.split(":")
    account_id = int(parts[1])
    config_format = parts[2]
    
    # Get account config
    config = get_account_config(account_id)
    
    if config and not config.get("error", None):
        # Get the specific config format
        format_config = config.get(config_format, {})
        
        if format_config:
            # Handle different config formats
            if isinstance(format_config, str):
                # Direct string (possibly a URI)
                config_text = format_config
            elif isinstance(format_config, dict):
                # Dictionary format, pretty print as JSON
                config_text = json.dumps(format_config, indent=2, ensure_ascii=False)
            else:
                config_text = str(format_config)
            
            # Send config as a separate message to avoid tampering with navigation
            await query.message.reply_text(
                f"📋 {config_format.upper()} کانفیگ:\n\n"
                f"```\n{config_text}\n```",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Keep the current message unchanged
            return SELECTING_ACCOUNT
        else:
            await query.edit_message_text(
                f"❌ کانفیگ با فرمت {config_format} یافت نشد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
                ])
            )
    else:
        error = config.get("error", "خطای نامشخص")
        await query.edit_message_text(
            f"❌ خطا در دریافت کانفیگ:\n{error}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_change_server_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of servers to change to."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID from callback data
    account_id = int(query.data.split(":")[1])
    
    # Store for later use
    context.user_data["changing_server_for_account"] = account_id
    
    # Get all servers
    servers = get_servers()
    
    if not servers:
        await query.edit_message_text(
            "❌ هیچ سروری یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
        return SELECTING_ACCOUNT
    
    # Filter active servers only
    active_servers = [s for s in servers if s.get("is_active", False)]
    
    if not active_servers:
        await query.edit_message_text(
            "❌ هیچ سرور فعالی یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
        return SELECTING_ACCOUNT
    
    # Create message and keyboard
    message = "🖥️ سرور مورد نظر را انتخاب کنید:\n\n"
    
    keyboard = []
    for server in active_servers:
        server_id = server.get("id", "")
        server_name = server.get("name", "")
        server_location = server.get("location", "")
        keyboard.append([
            InlineKeyboardButton(
                f"{server_name} ({server_location})",
                callback_data=f"account_change_server_confirm:{account_id}:{server_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_change_server_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm server change for an account."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID and server ID from callback data
    parts = query.data.split(":")
    account_id = int(parts[1])
    server_id = int(parts[2])
    
    # Change server
    result = change_account_server(account_id, server_id)
    
    if result:
        await query.edit_message_text(
            "✅ سرور اکانت با موفقیت تغییر یافت.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    else:
        await query.edit_message_text(
            "❌ خطا در تغییر سرور اکانت.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_extend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Extend expiry date for a VPN account."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID from callback data
    account_id = int(query.data.split(":")[1])
    
    # Show options for extension
    await query.edit_message_text(
        "⏱️ مدت زمان تمدید را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("۱ ماه", callback_data=f"account_extend_confirm:{account_id}:30"),
                InlineKeyboardButton("۳ ماه", callback_data=f"account_extend_confirm:{account_id}:90")
            ],
            [
                InlineKeyboardButton("۶ ماه", callback_data=f"account_extend_confirm:{account_id}:180"),
                InlineKeyboardButton("۱ سال", callback_data=f"account_extend_confirm:{account_id}:365")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")
            ]
        ])
    )
    
    return SELECTING_ACCOUNT

@require_admin
async def account_extend_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm account extension."""
    query = update.callback_query
    await query.answer()
    
    # Get account ID and days from callback data
    parts = query.data.split(":")
    account_id = int(parts[1])
    days = int(parts[2])
    
    # Get account details
    account = get_account(account_id)
    
    if not account:
        await query.edit_message_text(
            "❌ خطا\n\n"
            "اکانت مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data="admin_accounts")]
            ])
        )
        return SELECTING_ACCOUNT
    
    # Calculate new expiry date
    current_expiry = account.get("expiry_date", None)
    
    if current_expiry:
        current_expiry_obj = datetime.fromisoformat(current_expiry.replace("Z", "+00:00"))
        new_expiry = current_expiry_obj + timedelta(days=days)
    else:
        # If no expiry date, use current time as base
        new_expiry = datetime.now(pytz.UTC) + timedelta(days=days)
    
    # Format the expiry date for the API
    new_expiry_str = new_expiry.isoformat()
    
    # Update account with new expiry date
    result = update_account(account_id, {"expiry_date": new_expiry_str})
    
    if result:
        # Format readable expiry date for message
        readable_expiry = new_expiry.strftime("%Y-%m-%d %H:%M")
        
        await query.edit_message_text(
            f"✅ تاریخ انقضای اکانت با موفقیت به {readable_expiry} تغییر یافت.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    else:
        await query.edit_message_text(
            "❌ خطا در تمدید اکانت.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"account_details:{account_id}")]
            ])
        )
    
    return SELECTING_ACCOUNT


# Add handlers to the handlers list
handlers = [
    CallbackQueryHandler(account_list, pattern="^admin_accounts$"),
    CallbackQueryHandler(account_list_paginated, pattern="^account_list:"),
    CallbackQueryHandler(account_details, pattern="^account_details:"),
    CallbackQueryHandler(account_toggle_status, pattern="^account_toggle:"),
    CallbackQueryHandler(account_reset_traffic, pattern="^account_reset_traffic:"),
    CallbackQueryHandler(account_delete_confirm, pattern="^account_delete:"),
    CallbackQueryHandler(account_delete_confirmed, pattern="^account_delete_confirmed:"),
    CallbackQueryHandler(account_get_config, pattern="^account_get_config:"),
    CallbackQueryHandler(account_show_config, pattern="^account_config:"),
    CallbackQueryHandler(account_change_server_list, pattern="^account_change_server:"),
    CallbackQueryHandler(account_change_server_confirm, pattern="^account_change_server_confirm:"),
    CallbackQueryHandler(account_extend, pattern="^account_extend:"),
    CallbackQueryHandler(account_extend_confirm, pattern="^account_extend_confirm:"),
]

# Create a class to hold the handlers for easier import
class account_handlers:
    handlers = handlers
    account_list = account_list 