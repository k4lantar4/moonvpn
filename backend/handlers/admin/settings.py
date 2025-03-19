"""
Settings management handler for admin panel.
"""

import logging
from typing import Dict, Any, List
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from core.config import settings
from bot.utils import build_navigation_keyboard

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_SETTINGS_ACTION = 1
EDITING_PLANS = 2
EDITING_SERVERS = 3
EDITING_PAYMENT = 4
EDITING_ACCESS = 5
EDITING_MESSAGES = 6
EDITING_GENERAL = 7
CONFIRMING_ACTION = 8

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show settings management menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="settings",
        buttons=[
            ("🏷 پلن‌ها", "settings_plans"),
            ("🌍 سرورها", "settings_servers"),
            ("💰 پرداخت", "settings_payment"),
            ("👥 دسترسی‌ها", "settings_access"),
            ("📨 پیام‌ها", "settings_messages"),
            ("⚙️ عمومی", "settings_general"),
            ("🔙 بازگشت", "back_to_admin")
        ]
    )
    
    message = (
        "⚙️ <b>تنظیمات ربات</b>\n\n"
        "از این بخش می‌توانید تنظیمات ربات را مدیریت کنید.\n"
        "لطفاً یکی از بخش‌های زیر را انتخاب کنید:"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_SETTINGS_ACTION

async def show_plans_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show subscription plans settings."""
    query = update.callback_query
    await query.answer()
    
    # Format current plans
    message = "🏷 <b>تنظیمات پلن‌ها</b>\n\n"
    
    for plan in settings.SUBSCRIPTION_PLANS:
        message += (
            f"📦 <b>{plan['name']}</b>\n"
            f"💰 قیمت: {plan['price']} تومان\n"
            f"⏱ مدت: {plan['duration']} روز\n"
            f"📊 حجم: {plan['traffic'] // (1024**3)} گیگابایت\n"
            f"📝 توضیحات: {plan['description']}\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="settings",
        buttons=[
            ("➕ پلن جدید", "settings_add_plan"),
            ("✏️ ویرایش پلن", "settings_edit_plan"),
            ("❌ حذف پلن", "settings_delete_plan"),
            ("🔙 بازگشت", "settings_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return EDITING_PLANS

async def show_servers_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show server settings."""
    query = update.callback_query
    await query.answer()
    
    # Format current server settings
    message = (
        "🌍 <b>تنظیمات سرورها</b>\n\n"
        "🔒 <b>امنیت:</b>\n"
        "• پروتکل: VLESS\n"
        "• رمزنگاری: AUTO\n"
        "• تأیید هویت: NONE\n\n"
        "⚡️ <b>عملکرد:</b>\n"
        "• حداکثر کاربر همزمان: 500\n"
        "• محدودیت پهنای باند: نامحدود\n"
        "• بافر TCP: 32 KB\n\n"
        "🔄 <b>بکاپ:</b>\n"
        "• وضعیت: فعال\n"
        "• زمان‌بندی: روزانه\n"
        "• نگهداری: 7 روز"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="settings",
        buttons=[
            ("🔒 امنیت", "settings_security"),
            ("⚡️ عملکرد", "settings_performance"),
            ("🔄 بکاپ", "settings_backup"),
            ("🔙 بازگشت", "settings_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return EDITING_SERVERS

async def show_payment_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show payment settings."""
    query = update.callback_query
    await query.answer()
    
    # Format current payment settings
    message = (
        "💰 <b>تنظیمات پرداخت</b>\n\n"
        "💳 <b>کارت به کارت:</b>\n"
        f"• شماره کارت: {settings.CARD_NUMBER}\n"
        f"• به نام: {settings.CARD_HOLDER}\n"
        f"• بانک: {settings.CARD_BANK}\n\n"
        "🔰 <b>زرین‌پال:</b>\n"
        "• وضعیت: غیرفعال\n"
        "• مرچنت: تنظیم نشده\n\n"
        "⚙️ <b>تنظیمات:</b>\n"
        "• تأیید خودکار: غیرفعال\n"
        "• حداقل مبلغ: 10,000 تومان\n"
        "• حداکثر مبلغ: نامحدود"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="settings",
        buttons=[
            ("💳 کارت بانکی", "settings_card"),
            ("🔰 درگاه آنلاین", "settings_gateway"),
            ("⚙️ تنظیمات", "settings_payment_config"),
            ("🔙 بازگشت", "settings_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return EDITING_PAYMENT

async def show_access_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show access control settings."""
    query = update.callback_query
    await query.answer()
    
    # Format current access settings
    message = (
        "👥 <b>تنظیمات دسترسی</b>\n\n"
        "👮‍♂️ <b>مدیران:</b>\n"
        "• تعداد: 2 نفر\n"
        "• دسترسی کامل به پنل مدیریت\n\n"
        "👨‍💼 <b>فروشندگان:</b>\n"
        "• تعداد: 5 نفر\n"
        "• دسترسی به پنل فروش\n"
        "• امکان ثبت سفارش\n"
        "• مشاهده گزارشات\n\n"
        "🛡 <b>محدودیت‌ها:</b>\n"
        "• حداکثر کاربر همزمان: 1000\n"
        "• محدودیت IP: غیرفعال\n"
        "• فیلتر کشور: غیرفعال"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="settings",
        buttons=[
            ("👮‍♂️ مدیران", "settings_admins"),
            ("👨‍💼 فروشندگان", "settings_sellers"),
            ("🛡 محدودیت‌ها", "settings_restrictions"),
            ("🔙 بازگشت", "settings_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return EDITING_ACCESS

async def show_messages_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show message templates settings."""
    query = update.callback_query
    await query.answer()
    
    # Format current message templates
    message = (
        "📨 <b>تنظیمات پیام‌ها</b>\n\n"
        "🤖 <b>پیام‌های سیستمی:</b>\n"
        "• خوش‌آمدگویی\n"
        "• راهنما\n"
        "• پشتیبانی\n"
        "• خطا\n\n"
        "💰 <b>پیام‌های مالی:</b>\n"
        "• تأیید پرداخت\n"
        "• رد پرداخت\n"
        "• فاکتور\n\n"
        "📦 <b>پیام‌های سرویس:</b>\n"
        "• اطلاعات اکانت\n"
        "• هشدار حجم\n"
        "• اتمام اشتراک"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="settings",
        buttons=[
            ("🤖 سیستمی", "settings_system_msgs"),
            ("💰 مالی", "settings_payment_msgs"),
            ("📦 سرویس", "settings_service_msgs"),
            ("🔙 بازگشت", "settings_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return EDITING_MESSAGES

async def show_general_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show general settings."""
    query = update.callback_query
    await query.answer()
    
    # Format current general settings
    message = (
        "⚙️ <b>تنظیمات عمومی</b>\n\n"
        "🤖 <b>ربات:</b>\n"
        "• نام: MoonVPN\n"
        "• توضیحات: فروش VPN\n"
        "• زبان پیش‌فرض: فارسی\n\n"
        "🔔 <b>اعلان‌ها:</b>\n"
        "• اعلان سفارش: فعال\n"
        "• اعلان پرداخت: فعال\n"
        "• اعلان پشتیبانی: فعال\n\n"
        "⏱ <b>زمان‌بندی:</b>\n"
        "• بررسی خودکار: هر 5 دقیقه\n"
        "• پاکسازی لاگ: هر هفته\n"
        "• بکاپ: روزانه"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="settings",
        buttons=[
            ("🤖 ربات", "settings_bot"),
            ("🔔 اعلان‌ها", "settings_notifications"),
            ("⏱ زمان‌بندی", "settings_scheduling"),
            ("🔙 بازگشت", "settings_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return EDITING_GENERAL

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

settings_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(settings_menu, pattern="^admin_settings$")
    ],
    states={
        SELECTING_SETTINGS_ACTION: [
            CallbackQueryHandler(show_plans_settings, pattern="^settings_plans$"),
            CallbackQueryHandler(show_servers_settings, pattern="^settings_servers$"),
            CallbackQueryHandler(show_payment_settings, pattern="^settings_payment$"),
            CallbackQueryHandler(show_access_settings, pattern="^settings_access$"),
            CallbackQueryHandler(show_messages_settings, pattern="^settings_messages$"),
            CallbackQueryHandler(show_general_settings, pattern="^settings_general$"),
            CallbackQueryHandler(settings_menu, pattern="^settings_menu$"),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
        ],
        EDITING_PLANS: [
            CallbackQueryHandler(settings_menu, pattern="^settings_menu$")
        ],
        EDITING_SERVERS: [
            CallbackQueryHandler(settings_menu, pattern="^settings_menu$")
        ],
        EDITING_PAYMENT: [
            CallbackQueryHandler(settings_menu, pattern="^settings_menu$")
        ],
        EDITING_ACCESS: [
            CallbackQueryHandler(settings_menu, pattern="^settings_menu$")
        ],
        EDITING_MESSAGES: [
            CallbackQueryHandler(settings_menu, pattern="^settings_menu$")
        ],
        EDITING_GENERAL: [
            CallbackQueryHandler(settings_menu, pattern="^settings_menu$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
    ],
    map_to_parent={
        ConversationHandler.END: 'SELECTING_ADMIN_ACTION'
    }
) 