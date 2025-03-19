"""
MoonVPN Telegram Bot - Admin Handler Implementation.

This module provides handlers for the admin feature.
"""

import logging
from typing import Dict, List, Optional, Union, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from models.user import User
from core.config import get_config_value
from core.utils.i18n import get_text
from core.utils.formatting import admin_filter

# States
ADMIN_MENU, ADMIN_USERS, ADMIN_SERVERS, ADMIN_PAYMENTS, ADMIN_SETTINGS, ADMIN_BROADCAST = range(6)

# Callback patterns
PATTERN_ADMIN = "admin"
PATTERN_ADMIN_USERS = "admin_users"
PATTERN_ADMIN_SERVERS = "admin_servers"
PATTERN_ADMIN_PAYMENTS = "admin_payments"
PATTERN_ADMIN_SETTINGS = "admin_settings"
PATTERN_ADMIN_BROADCAST = "admin_broadcast"
PATTERN_ADMIN_STATS = "admin_stats"

logger = logging.getLogger(__name__)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /admin command.
    
    This command displays the admin menu.
    """
    # Check if user is admin
    if not await admin_filter(update, context):
        await update.message.reply_text(
            "⛔️ شما دسترسی ادمین ندارید.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    return await admin_handler(update, context)

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the admin button callback.
    
    This function displays the admin menu.
    """
    # Check if user is admin
    if not await admin_filter(update, context):
        if update.callback_query:
            await update.callback_query.answer("⛔️ شما دسترسی ادمین ندارید.", show_alert=True)
        else:
            await update.message.reply_text(
                "⛔️ شما دسترسی ادمین ندارید.",
                parse_mode=ParseMode.HTML
            )
        return ConversationHandler.END
    
    user = update.effective_user
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    # Create a beautiful admin menu
    text = (
        "👨‍💼 <b>پنل مدیریت MoonVPN</b>\n\n"
        f"سلام {user.first_name}!\n"
        "به پنل مدیریت MoonVPN خوش آمدید.\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # Create keyboard with admin options
    keyboard = [
        [
            InlineKeyboardButton("👥 کاربران", callback_data=PATTERN_ADMIN_USERS),
            InlineKeyboardButton("🖥️ سرورها", callback_data=PATTERN_ADMIN_SERVERS)
        ],
        [
            InlineKeyboardButton("💰 پرداخت‌ها", callback_data=PATTERN_ADMIN_PAYMENTS),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data=PATTERN_ADMIN_SETTINGS)
        ],
        [
            InlineKeyboardButton("📢 ارسال پیام گروهی", callback_data=PATTERN_ADMIN_BROADCAST),
            InlineKeyboardButton("📊 آمار", callback_data=PATTERN_ADMIN_STATS)
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ADMIN_MENU

async def admin_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the admin users button callback.
    
    This function displays the user management menu.
    """
    query = update.callback_query
    await query.answer()
    
    # Get user count
    try:
        user_count = User.count()
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        user_count = 0
    
    # Create a beautiful user management menu
    text = (
        "👥 <b>مدیریت کاربران</b>\n\n"
        f"تعداد کل کاربران: {user_count}\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # Create keyboard with user management options
    keyboard = [
        [
            InlineKeyboardButton("👤 لیست کاربران", callback_data="admin_users_list"),
            InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_users_search")
        ],
        [
            InlineKeyboardButton("➕ افزودن کاربر", callback_data="admin_users_add"),
            InlineKeyboardButton("🚫 مسدود کردن کاربر", callback_data="admin_users_block")
        ],
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data=PATTERN_ADMIN)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ADMIN_USERS

async def admin_servers_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the admin servers button callback.
    
    This function displays the server management menu.
    """
    query = update.callback_query
    await query.answer()
    
    # Create a beautiful server management menu
    text = (
        "🖥️ <b>مدیریت سرورها</b>\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # Create keyboard with server management options
    keyboard = [
        [
            InlineKeyboardButton("📋 لیست سرورها", callback_data="admin_servers_list"),
            InlineKeyboardButton("➕ افزودن سرور", callback_data="admin_servers_add")
        ],
        [
            InlineKeyboardButton("🔄 بروزرسانی سرورها", callback_data="admin_servers_update"),
            InlineKeyboardButton("📊 وضعیت سرورها", callback_data="admin_servers_status")
        ],
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data=PATTERN_ADMIN)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ADMIN_SERVERS

async def admin_payments_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the admin payments button callback.
    
    This function displays the payment management menu.
    """
    query = update.callback_query
    await query.answer()
    
    # Create a beautiful payment management menu
    text = (
        "💰 <b>مدیریت پرداخت‌ها</b>\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # Create keyboard with payment management options
    keyboard = [
        [
            InlineKeyboardButton("📋 لیست پرداخت‌ها", callback_data="admin_payments_list"),
            InlineKeyboardButton("🔍 جستجوی پرداخت", callback_data="admin_payments_search")
        ],
        [
            InlineKeyboardButton("💳 تنظیمات پرداخت", callback_data="admin_payments_settings"),
            InlineKeyboardButton("📊 گزارش مالی", callback_data="admin_payments_report")
        ],
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data=PATTERN_ADMIN)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ADMIN_PAYMENTS

async def admin_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the admin settings button callback.
    
    This function displays the settings management menu.
    """
    query = update.callback_query
    await query.answer()
    
    # Get maintenance mode status
    maintenance_mode = get_config_value("maintenance_mode", False)
    maintenance_status = "🟢 فعال" if maintenance_mode else "🔴 غیرفعال"
    
    # Create a beautiful settings management menu
    text = (
        "⚙️ <b>تنظیمات</b>\n\n"
        f"حالت تعمیر و نگهداری: {maintenance_status}\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # Create keyboard with settings management options
    keyboard = [
        [
            InlineKeyboardButton("🛠️ حالت تعمیر و نگهداری", callback_data="admin_settings_maintenance"),
            InlineKeyboardButton("👥 مدیریت ادمین‌ها", callback_data="admin_settings_admins")
        ],
        [
            InlineKeyboardButton("🌐 تنظیمات ربات", callback_data="admin_settings_bot"),
            InlineKeyboardButton("💾 پشتیبان‌گیری", callback_data="admin_settings_backup")
        ],
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data=PATTERN_ADMIN)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ADMIN_SETTINGS

async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the admin broadcast button callback.
    
    This function displays the broadcast message menu.
    """
    query = update.callback_query
    await query.answer()
    
    # Create a beautiful broadcast message menu
    text = (
        "📢 <b>ارسال پیام گروهی</b>\n\n"
        "با استفاده از این بخش می‌توانید به تمام کاربران ربات پیام ارسال کنید.\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # Create keyboard with broadcast options
    keyboard = [
        [
            InlineKeyboardButton("📝 ارسال پیام متنی", callback_data="admin_broadcast_text"),
            InlineKeyboardButton("🖼️ ارسال پیام با تصویر", callback_data="admin_broadcast_photo")
        ],
        [
            InlineKeyboardButton("📊 گزارش ارسال‌ها", callback_data="admin_broadcast_report"),
            InlineKeyboardButton("⏱️ زمانبندی ارسال", callback_data="admin_broadcast_schedule")
        ],
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data=PATTERN_ADMIN)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ADMIN_BROADCAST

async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the admin stats button callback.
    
    This function displays the statistics menu.
    """
    query = update.callback_query
    await query.answer()
    
    # Get some basic stats
    try:
        user_count = User.count()
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        user_count = 0
    
    # Create a beautiful statistics menu
    text = (
        "📊 <b>آمار و گزارشات</b>\n\n"
        f"<b>تعداد کاربران:</b> {user_count}\n\n"
        "برای مشاهده آمار و گزارشات دقیق‌تر، یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # Create keyboard with statistics options
    keyboard = [
        [
            InlineKeyboardButton("👥 آمار کاربران", callback_data="admin_stats_users"),
            InlineKeyboardButton("💰 آمار مالی", callback_data="admin_stats_financial")
        ],
        [
            InlineKeyboardButton("🖥️ آمار سرورها", callback_data="admin_stats_servers"),
            InlineKeyboardButton("📈 نمودارها", callback_data="admin_stats_charts")
        ],
        [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data=PATTERN_ADMIN)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return ADMIN_MENU

def get_admin_handlers() -> List[Any]:
    """Return all handlers related to the admin feature."""
    
    # Create conversation handler for admin flow
    admin_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("admin", admin_command),
            CallbackQueryHandler(admin_handler, pattern=f"^{PATTERN_ADMIN}$")
        ],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(admin_users_handler, pattern=f"^{PATTERN_ADMIN_USERS}$"),
                CallbackQueryHandler(admin_servers_handler, pattern=f"^{PATTERN_ADMIN_SERVERS}$"),
                CallbackQueryHandler(admin_payments_handler, pattern=f"^{PATTERN_ADMIN_PAYMENTS}$"),
                CallbackQueryHandler(admin_settings_handler, pattern=f"^{PATTERN_ADMIN_SETTINGS}$"),
                CallbackQueryHandler(admin_broadcast_handler, pattern=f"^{PATTERN_ADMIN_BROADCAST}$"),
                CallbackQueryHandler(admin_stats_handler, pattern=f"^{PATTERN_ADMIN_STATS}$")
            ],
            ADMIN_USERS: [
                CallbackQueryHandler(admin_handler, pattern=f"^{PATTERN_ADMIN}$")
            ],
            ADMIN_SERVERS: [
                CallbackQueryHandler(admin_handler, pattern=f"^{PATTERN_ADMIN}$")
            ],
            ADMIN_PAYMENTS: [
                CallbackQueryHandler(admin_handler, pattern=f"^{PATTERN_ADMIN}$")
            ],
            ADMIN_SETTINGS: [
                CallbackQueryHandler(admin_handler, pattern=f"^{PATTERN_ADMIN}$")
            ],
            ADMIN_BROADCAST: [
                CallbackQueryHandler(admin_handler, pattern=f"^{PATTERN_ADMIN}$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(admin_handler, pattern=f"^{PATTERN_ADMIN}$"),
            CommandHandler("cancel", admin_handler)
        ],
        name="admin_conversation",
        persistent=False
    )
    
    return [admin_conv_handler] 