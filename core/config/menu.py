"""
Admin menu handler.

This module contains the main admin menu handler.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from decorators import require_admin
from utils import get_text
from .constants import (
    ADMIN_MENU, 
    SERVER_MANAGEMENT, 
    USER_MANAGEMENT,
    ACCOUNT_MANAGEMENT,
    PAYMENT_MANAGEMENT,
    SERVICE_MANAGEMENT,
    SETTINGS_MANAGEMENT
)

from core.utils.helpers import management_group_access

@require_admin
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the admin menu."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Create message
    message = (
        f"🛡️ *پنل مدیریت*\n\n"
        f"به پنل مدیریت MoonVPN خوش آمدید.\n"
        f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # Create keyboard with admin options
    keyboard = [
        # First row - Main management options
        [
            InlineKeyboardButton(
                "📊 داشبورد", 
                callback_data="dashboard"
            ),
            InlineKeyboardButton(
                "👥 کاربران", 
                callback_data=USER_MANAGEMENT
            )
        ],
        # Second row - VPN management
        [
            InlineKeyboardButton(
                "🔑 اکانت‌ها", 
                callback_data=ACCOUNT_MANAGEMENT
            ),
            InlineKeyboardButton(
                "🖥️ سرورها", 
                callback_data=SERVER_MANAGEMENT
            )
        ],
        # Third row - Business management
        [
            InlineKeyboardButton(
                "💰 پرداخت‌ها", 
                callback_data=PAYMENT_MANAGEMENT
            ),
            InlineKeyboardButton(
                "🎯 پلن‌ها", 
                callback_data=SERVICE_MANAGEMENT
            )
        ],
        # Fourth row - Communication
        [
            InlineKeyboardButton(
                "📣 ارسال پیام گروهی", 
                callback_data="broadcast_menu"
            ),
            InlineKeyboardButton(
                "📝 گزارشات", 
                callback_data="reports_menu"
            )
        ],
        # Fifth row - Bot and system settings
        [
            InlineKeyboardButton(
                "⚙️ تنظیمات سیستم", 
                callback_data=SETTINGS_MANAGEMENT
            ),
            InlineKeyboardButton(
                "🛠️ تنظیمات مدیریتی", 
                callback_data="management_settings"
            )
        ],
        # Help row
        [
            InlineKeyboardButton(
                "👥 گروه‌های اطلاع‌رسانی", 
                callback_data="group_settings"
            ),
            InlineKeyboardButton(
                "❓ راهنما", 
                callback_data="admin_help"
            )
        ],
        # Back button
        [
            InlineKeyboardButton(
                "🔙 بازگشت به منوی اصلی", 
                callback_data="main_menu"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if message should be edited or sent new
    if update.callback_query:
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
    
    return ADMIN_MENU 

@management_group_access(["GENERAL_MANAGEMENT"])
async def handle_general_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle general management menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("📢 اعلان‌های عمومی", callback_data="admin_general_announcements"),
            InlineKeyboardButton("📊 داشبورد سیستم", callback_data="admin_general_dashboard")
        ],
        [
            InlineKeyboardButton("🚦 وضعیت سیستم", callback_data="admin_general_status"),
            InlineKeyboardButton("🔔 تنظیمات اعلان‌ها", callback_data="admin_general_notifications")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "👨‍💼 <b>مدیریت کلی</b>\n\n"
        "از طریق این بخش می‌توانید به مدیریت کلی سیستم بپردازید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["LOCATION_MANAGEMENT"])
async def handle_location_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle location management menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("➕ افزودن مکان جدید", callback_data="admin_location_add"),
            InlineKeyboardButton("📋 لیست مکان‌ها", callback_data="admin_location_list")
        ],
        [
            InlineKeyboardButton("🔄 به‌روزرسانی مکان‌ها", callback_data="admin_location_update"),
            InlineKeyboardButton("❌ حذف مکان", callback_data="admin_location_delete")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "🌎 <b>مدیریت مکان‌ها</b>\n\n"
        "از طریق این بخش می‌توانید مکان‌های جغرافیایی سرورها را مدیریت کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["SERVER_MANAGEMENT"])
async def handle_server_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle server management menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("➕ افزودن سرور جدید", callback_data="admin_server_add"),
            InlineKeyboardButton("📋 لیست سرورها", callback_data="admin_server_list")
        ],
        [
            InlineKeyboardButton("🧪 تست سرورها", callback_data="admin_server_test"),
            InlineKeyboardButton("🔄 به‌روزرسانی سرورها", callback_data="admin_server_update")
        ],
        [
            InlineKeyboardButton("❌ حذف سرور", callback_data="admin_server_delete"),
            InlineKeyboardButton("📊 آمار سرورها", callback_data="admin_server_stats")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "🖥️ <b>مدیریت سرورها</b>\n\n"
        "از طریق این بخش می‌توانید سرورهای VPN را مدیریت کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["SERVICE_MANAGEMENT"])
async def handle_service_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle service management menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("➕ افزودن خدمت جدید", callback_data="admin_service_add"),
            InlineKeyboardButton("📋 لیست خدمات", callback_data="admin_service_list")
        ],
        [
            InlineKeyboardButton("🔄 ویرایش خدمات", callback_data="admin_service_edit"),
            InlineKeyboardButton("❌ حذف خدمت", callback_data="admin_service_delete")
        ],
        [
            InlineKeyboardButton("📊 آمار فروش خدمات", callback_data="admin_service_stats"),
            InlineKeyboardButton("🏷️ تنظیم قیمت‌ها", callback_data="admin_service_pricing")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "🛒 <b>مدیریت خدمات</b>\n\n"
        "از طریق این بخش می‌توانید خدمات و سرویس‌های VPN را مدیریت کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["USER_MANAGEMENT"])
async def handle_user_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user management menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("📋 لیست کاربران", callback_data="admin_user_list"),
            InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_user_search")
        ],
        [
            InlineKeyboardButton("🚫 مسدود کردن کاربر", callback_data="admin_user_block"),
            InlineKeyboardButton("✅ فعال‌سازی کاربر", callback_data="admin_user_activate")
        ],
        [
            InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_user_stats"),
            InlineKeyboardButton("💰 شارژ کیف پول", callback_data="admin_user_wallet")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "👥 <b>مدیریت کاربران</b>\n\n"
        "از طریق این بخش می‌توانید کاربران را مدیریت کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["DISCOUNT_MARKETING"])
async def handle_discount_marketing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle discount and marketing menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("➕ افزودن کد تخفیف", callback_data="admin_discount_add"),
            InlineKeyboardButton("📋 لیست کدهای تخفیف", callback_data="admin_discount_list")
        ],
        [
            InlineKeyboardButton("🔄 ویرایش کد تخفیف", callback_data="admin_discount_edit"),
            InlineKeyboardButton("❌ حذف کد تخفیف", callback_data="admin_discount_delete")
        ],
        [
            InlineKeyboardButton("📊 آمار استفاده از تخفیف‌ها", callback_data="admin_discount_stats"),
            InlineKeyboardButton("📢 کمپین‌های بازاریابی", callback_data="admin_marketing_campaigns")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "🏷️ <b>تخفیف‌ها و بازاریابی</b>\n\n"
        "از طریق این بخش می‌توانید کدهای تخفیف و کمپین‌های بازاریابی را مدیریت کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["FINANCIAL_REPORTS"])
async def handle_financial_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle financial reports menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("📊 گزارش روزانه", callback_data="admin_financial_daily"),
            InlineKeyboardButton("📊 گزارش هفتگی", callback_data="admin_financial_weekly")
        ],
        [
            InlineKeyboardButton("📊 گزارش ماهانه", callback_data="admin_financial_monthly"),
            InlineKeyboardButton("📊 گزارش سالانه", callback_data="admin_financial_yearly")
        ],
        [
            InlineKeyboardButton("💰 گزارش تراکنش‌ها", callback_data="admin_financial_transactions"),
            InlineKeyboardButton("📈 نمودار فروش", callback_data="admin_financial_charts")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "📊 <b>گزارش‌های مالی</b>\n\n"
        "از طریق این بخش می‌توانید گزارش‌های مالی را مشاهده کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["BULK_MESSAGING"])
async def handle_bulk_messaging(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bulk messaging menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("📨 ارسال پیام به همه", callback_data="admin_message_all"),
            InlineKeyboardButton("📨 ارسال پیام به کاربران فعال", callback_data="admin_message_active")
        ],
        [
            InlineKeyboardButton("📨 ارسال پیام به کاربران خاص", callback_data="admin_message_specific"),
            InlineKeyboardButton("📝 ساخت پیام جدید", callback_data="admin_message_create")
        ],
        [
            InlineKeyboardButton("📋 قالب‌های پیش‌فرض", callback_data="admin_message_templates"),
            InlineKeyboardButton("📊 گزارش ارسال‌ها", callback_data="admin_message_reports")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "📨 <b>پیام‌رسانی انبوه</b>\n\n"
        "از طریق این بخش می‌توانید به گروه‌های مختلف کاربران پیام ارسال کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["SERVER_MONITORING"])
async def handle_server_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle server monitoring menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("📊 وضعیت سرورها", callback_data="admin_monitoring_status"),
            InlineKeyboardButton("📈 منابع سرورها", callback_data="admin_monitoring_resources")
        ],
        [
            InlineKeyboardButton("🔄 بررسی دسترسی‌پذیری", callback_data="admin_monitoring_availability"),
            InlineKeyboardButton("⚠️ هشدارها", callback_data="admin_monitoring_alerts")
        ],
        [
            InlineKeyboardButton("🧪 تست سرعت", callback_data="admin_monitoring_speed"),
            InlineKeyboardButton("📝 گزارش مشکلات", callback_data="admin_monitoring_issues")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "📡 <b>مانیتورینگ سرور</b>\n\n"
        "از طریق این بخش می‌توانید وضعیت سرورها را نظارت کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["ACCESS_MANAGEMENT"])
async def handle_access_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle access management menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("👥 مدیریت نقش‌ها", callback_data="admin_access_roles"),
            InlineKeyboardButton("🔐 سطوح دسترسی", callback_data="admin_access_levels")
        ],
        [
            InlineKeyboardButton("➕ افزودن مدیر", callback_data="admin_access_add_admin"),
            InlineKeyboardButton("❌ حذف مدیر", callback_data="admin_access_remove_admin")
        ],
        [
            InlineKeyboardButton("👨‍💼 مدیریت گروه‌ها", callback_data="management_groups"),
            InlineKeyboardButton("📋 لیست مدیران", callback_data="admin_access_admin_list")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "🔐 <b>مدیریت دسترسی</b>\n\n"
        "از طریق این بخش می‌توانید سطوح دسترسی و نقش‌های مختلف را مدیریت کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["SYSTEM_SETTINGS"])
async def handle_system_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle system settings menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("⚙️ تنظیمات عمومی", callback_data="admin_settings_general"),
            InlineKeyboardButton("💳 تنظیمات پرداخت", callback_data="admin_settings_payment")
        ],
        [
            InlineKeyboardButton("🤖 تنظیمات ربات", callback_data="admin_settings_bot"),
            InlineKeyboardButton("🌐 تنظیمات پنل", callback_data="admin_settings_panel")
        ],
        [
            InlineKeyboardButton("📱 تنظیمات اعلان‌ها", callback_data="admin_settings_notifications"),
            InlineKeyboardButton("💬 تنظیمات پشتیبانی", callback_data="admin_settings_support")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "⚙️ <b>تنظیمات سیستم</b>\n\n"
        "از طریق این بخش می‌توانید تنظیمات مختلف سیستم را مدیریت کنید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@management_group_access(["BACKUP_RESTORE"])
async def handle_backup_restore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle backup and restore menu."""
    # Create the keyboard
    buttons = [
        [
            InlineKeyboardButton("🔄 پشتیبان‌گیری جدید", callback_data="admin_backup_create"),
            InlineKeyboardButton("📋 لیست پشتیبان‌ها", callback_data="admin_backup_list")
        ],
        [
            InlineKeyboardButton("📤 دانلود پشتیبان", callback_data="admin_backup_download"),
            InlineKeyboardButton("📥 بازیابی پشتیبان", callback_data="admin_backup_restore")
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات پشتیبان‌گیری", callback_data="admin_backup_settings"),
            InlineKeyboardButton("❌ حذف پشتیبان", callback_data="admin_backup_delete")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی قبل", callback_data="admin_menu")
        ]
    ]

    message = (
        "🔄 <b>پشتیبان‌گیری و بازیابی</b>\n\n"
        "از طریق این بخش می‌توانید عملیات پشتیبان‌گیری و بازیابی را انجام دهید."
    )

    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    ) 