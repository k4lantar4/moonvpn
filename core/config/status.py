"""
Status command handler for MoonVPN Telegram Bot.

This module provides functionality to check the status of VPN accounts.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

from core.config import settings
from core.database import get_db
from core.models.user import User
from core.models.vpn_account import VPNAccount
from core.models.server import Server
from core.utils.i18n import _
from core.database import get_user_accounts
from core.utils.formatting import allowed_group_filter
from core.utils.helpers import require_feature

from core.utils.helpers import authenticated_user
from core.utils.helpers import get_user, human_readable_size
from backend.accounts.services import AccountService

logger = logging.getLogger(__name__)

# Define states
SHOWING_STATUS = 0
ACCOUNT_DETAILS = 1

@authenticated_user
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's VPN account status"""
    user = get_user(update.effective_user.id)
    
    try:
        # Get user's active account
        success, account_status, error = AccountService.get_account_status(user)
        
        if not success or error:
            await update.message.reply_text(
                f"⚠️ <b>خطا در دریافت وضعیت اکانت:</b>\n{error or 'خطای نامشخص'}\n\n"
                "اگر تازه اشتراک خریداری کرده‌اید، ممکن است هنوز فعال نشده باشد.\n"
                "برای خرید اشتراک از دستور /buy استفاده کنید.",
                parse_mode=ParseMode.HTML
            )
            return
        
        if not account_status:
            # User doesn't have an active account
            await update.message.reply_text(
                "⚠️ <b>شما هیچ اشتراک فعالی ندارید</b>\n\n"
                "برای خرید اشتراک از دستور /buy استفاده کنید.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Create account status message
        subscription_link = account_status.get('subscription_link', '')
        
        days_left = account_status.get('days_left', 0)
        if days_left <= 3:
            days_emoji = "🔴"
        elif days_left <= 7:
            days_emoji = "🟠"
        else:
            days_emoji = "🟢"
            
        traffic_used_bytes = account_status.get('used_traffic_bytes', 0)
        traffic_limit_bytes = account_status.get('traffic_limit_bytes', 0)
        traffic_percent = account_status.get('traffic_percent', 0)
        
        if traffic_percent >= 90:
            traffic_emoji = "🔴"
        elif traffic_percent >= 70:
            traffic_emoji = "🟠"
        else:
            traffic_emoji = "🟢"
        
        # Build status message
        status_message = (
            f"📊 <b>وضعیت اشتراک شما</b>\n\n"
            f"{days_emoji} <b>زمان باقیمانده:</b> {days_left} روز\n"
            f"{traffic_emoji} <b>حجم مصرف شده:</b> {human_readable_size(traffic_used_bytes)} از {human_readable_size(traffic_limit_bytes)} "
            f"({traffic_percent}%)\n\n"
        )
        
        # If account is almost expired, add renewal notice
        if days_left <= 3:
            status_message += "⚠️ <b>اشتراک شما به زودی منقضی می‌شود!</b>\n" \
                              "برای تمدید از دستور /buy استفاده کنید.\n\n"
        
        # If traffic is almost used up, add renewal notice
        if traffic_percent >= 90:
            status_message += "⚠️ <b>حجم اشتراک شما رو به اتمام است!</b>\n" \
                              "برای تمدید از دستور /buy استفاده کنید.\n\n"
        
        # Add server information if available
        if 'server_name' in account_status:
            status_message += f"🖥️ <b>سرور:</b> {account_status.get('server_name')}\n\n"
        
        # Add link information
        status_message += (
            f"🔗 <b>لینک اتصال شما:</b>\n"
            f"<code>{subscription_link}</code>\n\n"
        )
        
        # Create buttons for managing account
        buttons = [
            [InlineKeyboardButton("🔄 تمدید اشتراک", callback_data="buy")],
            [InlineKeyboardButton("📋 راهنمای اتصال", callback_data="connection_help")],
            [InlineKeyboardButton("🌐 تغییر سرور", callback_data="change_server")],
        ]
        
        # Add reset traffic button if available
        if account_status.get('can_reset_traffic', False):
            buttons.append([InlineKeyboardButton("🔁 ریست ترافیک", callback_data="reset_traffic")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await update.message.reply_text(
            status_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.exception(f"Error in status command: {str(e)}")
        await update.message.reply_text(
            "⚠️ خطایی در دریافت وضعیت اکانت رخ داد. لطفا بعدا مجددا تلاش کنید.",
            parse_mode=ParseMode.HTML
        )

async def reset_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset user's traffic"""
    query = update.callback_query
    await query.answer()
    
    user = get_user(query.from_user.id)
    
    try:
        # Check if user has permission to reset traffic
        success, account_status, error = AccountService.get_account_status(user)
        
        if not success or error or not account_status:
            await query.message.reply_text(
                "⚠️ خطا در بررسی وضعیت اکانت. لطفا بعدا مجددا تلاش کنید.",
                parse_mode=ParseMode.HTML
            )
            return
        
        if not account_status.get('can_reset_traffic', False):
            await query.message.reply_text(
                "⚠️ شما اجازه ریست ترافیک را ندارید.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Reset traffic
        success, new_status, error = AccountService.reset_account_traffic(user)
        
        if not success or error:
            await query.message.reply_text(
                f"⚠️ خطا در ریست ترافیک: {error or 'خطای نامشخص'}",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Success message
        await query.message.reply_text(
            "✅ <b>ترافیک اکانت شما با موفقیت ریست شد!</b>\n\n"
            "می‌توانید با دستور /status وضعیت جدید اکانت خود را مشاهده کنید.",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.exception(f"Error in reset_traffic: {str(e)}")
        await query.message.reply_text(
            "⚠️ خطایی در ریست ترافیک رخ داد. لطفا بعدا مجددا تلاش کنید.",
            parse_mode=ParseMode.HTML
        )

async def connection_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show connection help"""
    query = update.callback_query
    await query.answer()
    
    # Create help message with instructions for common platforms
    help_message = (
        "📖 <b>راهنمای اتصال</b>\n\n"
        "<b>📱 اندروید:</b>\n"
        "1. اپلیکیشن <b>V2rayNG</b> را از <a href='https://github.com/2dust/v2rayNG/releases'>اینجا</a> دانلود و نصب کنید.\n"
        "2. روی آیکون + کلیک کنید.\n"
        "3. گزینه Import config from clipboard را انتخاب کنید.\n"
        "4. لینک اشتراک خود را کپی و در برنامه وارد کنید.\n"
        "5. روی اتصال (V) کلیک کنید.\n\n"
        
        "<b>🍎 آیفون:</b>\n"
        "1. اپلیکیشن <b>Streisand</b> یا <b>Shadowrocket</b> را از اپ استور نصب کنید.\n"
        "2. لینک اشتراک خود را کپی کنید.\n"
        "3. اپلیکیشن به طور خودکار تنظیمات را وارد می‌کند.\n"
        "4. روی دکمه اتصال کلیک کنید.\n\n"
        
        "<b>💻 ویندوز:</b>\n"
        "1. نرم‌افزار <b>v2rayN</b> را از <a href='https://github.com/2dust/v2rayN/releases'>اینجا</a> دانلود و نصب کنید.\n"
        "2. روی Subscription کلیک کنید.\n"
        "3. لینک اشتراک خود را در قسمت URL وارد کنید.\n"
        "4. روی Update کلیک کنید.\n"
        "5. سرور مورد نظر را انتخاب و متصل شوید.\n\n"
        
        "<b>🍎 مک:</b>\n"
        "1. نرم‌افزار <b>V2rayU</b> یا <b>ClashX</b> را نصب کنید.\n"
        "2. لینک اشتراک خود را وارد کنید.\n"
        "3. روی Connect کلیک کنید.\n\n"
        
        "برای مشکلات و سوالات بیشتر با پشتیبانی تماس بگیرید."
    )
    
    # Create back button
    buttons = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_status")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.message.edit_text(
        help_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def status_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle status-related button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_status":
        # Go back to status view
        await status_command(update, context)
    elif query.data == "reset_traffic":
        await reset_traffic(update, context)
    elif query.data == "connection_help":
        await connection_help(update, context)
    elif query.data == "change_server":
        # Forward to change_server handler in a different module
        from core.handlers.bot.change_server import change_server_command
        await change_server_command(update, context)
    elif query.data == "buy":
        # Forward to buy handler in a different module
        from core.handlers.bot.buy import buy_command
        await buy_command(update, context)

# Handler for the /status command
status_handler = CommandHandler("status", status_command)
status_button_handler = CallbackQueryHandler(
    status_button_handler, 
    pattern=r"^back_to_status$|^reset_traffic$|^connection_help$|^change_server$|^buy$"
)

async def account_status_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show detailed status of a specific account."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    account_id = int(query.data.split("_")[-1])
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    
    if not account or account.user_id != user_id:
        # Invalid account or doesn't belong to this user
        await query.edit_message_text(
            _("❌ اکانت مورد نظر یافت نشد یا متعلق به شما نیست."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(_("🔙 بازگشت"), callback_data="account_status")]
            ])
        )
        return SHOWING_STATUS
    
    # Get server info
    server = account.get_server()
    server_name = server.name if server else _("نامشخص")
    server_location = server.location if server else _("نامشخص")
    
    # Calculate account metrics
    days_left = account.days_until_expiry()
    traffic_used_gb = round(account.used_traffic_gb, 2)
    traffic_total_gb = round(account.total_traffic_gb, 2)
    traffic_left_gb = round(max(0, account.total_traffic_gb - account.used_traffic_gb), 2)
    traffic_percent = account.traffic_used_percent()
    
    # Create traffic usage bar
    bar_length = 10
    filled_bars = int(traffic_percent / 100 * bar_length)
    traffic_bar = "▓" * filled_bars + "░" * (bar_length - filled_bars)
    
    # Determine status
    if account.is_active:
        if days_left <= 0:
            status = _("🔴 منقضی شده")
        elif traffic_percent >= 90:
            status = _("🟠 نزدیک به اتمام ترافیک")
        else:
            status = _("🟢 فعال")
    else:
        status = _("🔴 غیرفعال")
    
    # Create detailed status message
    message = _(
        f"📊 **جزئیات اکانت**\n\n"
        f"🔹 **نام**: {account.name}\n"
        f"🔹 **وضعیت**: {status}\n"
        f"🔹 **سرور**: {server_name} ({server_location})\n"
        f"🔹 **زمان باقیمانده**: {days_left} روز\n"
        f"🔹 **تاریخ انقضا**: {account.expiry_date.strftime('%Y-%m-%d')}\n\n"
        f"🔹 **ترافیک مصرف شده**: {traffic_used_gb} GB\n"
        f"🔹 **ترافیک کل**: {traffic_total_gb} GB\n"
        f"🔹 **ترافیک باقیمانده**: {traffic_left_gb} GB\n"
        f"🔹 **درصد مصرف**: {traffic_percent}%\n"
        f"🔹 {traffic_bar}"
    )
    
    # Create action buttons
    keyboard = [
        [
            InlineKeyboardButton(_("🔄 تمدید اکانت"), callback_data=f"renew_account_{account_id}"),
            InlineKeyboardButton(_("📲 دریافت کانفیگ"), callback_data=f"get_config_{account_id}")
        ],
        [
            InlineKeyboardButton(_("📱 تغییر لوکیشن"), callback_data=f"change_location_{account_id}"),
            InlineKeyboardButton(_("📊 آمار مصرف"), callback_data=f"traffic_usage_{account_id}")
        ],
        [InlineKeyboardButton(_("🔙 بازگشت به لیست اکانت‌ها"), callback_data="account_status")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message, 
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ACCOUNT_DETAILS

async def refresh_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Refresh the account status by fetching latest data."""
    query = update.callback_query
    await query.answer(_("در حال بروزرسانی وضعیت اکانت‌ها..."))
    
    # Simply call the status command again to refresh
    return await status_command(update, context)

@require_feature("account_status")
def get_status_handler():
    """Get the conversation handler for account status."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("status", status_command, filters=allowed_group_filter),
            CallbackQueryHandler(status_command, pattern=r"^account_status$")
        ],
        states={
            SHOWING_STATUS: [
                CallbackQueryHandler(account_status_details, pattern=r"^account_status_\d+$"),
                CallbackQueryHandler(refresh_status, pattern=r"^refresh_status$"),
                CallbackQueryHandler(status_command, pattern=r"^account_status$")
            ],
            ACCOUNT_DETAILS: [
                CallbackQueryHandler(status_command, pattern=r"^account_status$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", status_command),
            CallbackQueryHandler(status_command, pattern=r"^main_menu$")
        ],
        name="account_status",
        persistent=False
    ) 