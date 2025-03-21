"""
Reports management handler for admin panel.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from bot.services import reports_service
from bot.utils import (
    build_navigation_keyboard,
    format_size,
    format_date,
    format_currency
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_REPORT_TYPE = 1
SELECTING_REPORT_PERIOD = 2
SELECTING_REPORT_FORMAT = 3
GENERATING_REPORT = 4

async def reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show reports management menu."""
    query = update.callback_query
    await query.answer()
    
    message = (
        "📊 <b>گزارش‌های مدیریتی</b>\n\n"
        "لطفاً نوع گزارش مورد نظر را انتخاب کنید:\n\n"
        "📈 <b>گزارش‌های مالی:</b>\n"
        "• درآمد و تراکنش‌ها\n"
        "• فروش پلن‌ها\n"
        "• تخفیف‌ها\n\n"
        "👥 <b>گزارش‌های کاربران:</b>\n"
        "• ثبت‌نام و فعالیت\n"
        "• مصرف ترافیک\n"
        "• تمدید اشتراک\n\n"
        "🌍 <b>گزارش‌های سرور:</b>\n"
        "• وضعیت و عملکرد\n"
        "• بار و ترافیک\n"
        "• خطاها و هشدارها"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="reports",
        buttons=[
            ("💰 مالی", "reports_financial"),
            ("👥 کاربران", "reports_users"),
            ("🌍 سرورها", "reports_servers"),
            ("📊 آمار کلی", "reports_overview"),
            ("🔙 بازگشت", "back_to_admin")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_REPORT_TYPE

async def show_financial_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show financial reports menu."""
    query = update.callback_query
    await query.answer()
    
    # Get quick stats
    stats = await reports_service.get_financial_stats()
    
    message = (
        "💰 <b>گزارش‌های مالی</b>\n\n"
        "📊 <b>خلاصه آمار:</b>\n"
        f"• درآمد امروز: {format_currency(stats['today_income'])}\n"
        f"• درآمد این ماه: {format_currency(stats['month_income'])}\n"
        f"• تراکنش‌های موفق: {stats['successful_transactions']}\n"
        f"• میانگین خرید: {format_currency(stats['average_purchase'])}\n\n"
        "📈 <b>نمودار درآمد:</b>\n"
        f"{stats['income_chart']}\n\n"
        "لطفاً نوع گزارش مورد نظر را انتخاب کنید:"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="reports",
        buttons=[
            ("📊 درآمد", "reports_income"),
            ("🛒 فروش", "reports_sales"),
            ("🏷 تخفیف‌ها", "reports_discounts"),
            ("🔙 بازگشت", "reports_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_REPORT_TYPE

async def show_user_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user reports menu."""
    query = update.callback_query
    await query.answer()
    
    # Get quick stats
    stats = await reports_service.get_user_stats()
    
    message = (
        "👥 <b>گزارش‌های کاربران</b>\n\n"
        "📊 <b>خلاصه آمار:</b>\n"
        f"• کل کاربران: {stats['total_users']}\n"
        f"• کاربران فعال: {stats['active_users']}\n"
        f"• ثبت‌نام امروز: {stats['today_registrations']}\n"
        f"• اشتراک منقضی: {stats['expired_subscriptions']}\n\n"
        "📈 <b>نمودار فعالیت:</b>\n"
        f"{stats['activity_chart']}\n\n"
        "لطفاً نوع گزارش مورد نظر را انتخاب کنید:"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="reports",
        buttons=[
            ("📊 فعالیت", "reports_activity"),
            ("📈 ترافیک", "reports_traffic"),
            ("🔄 تمدید", "reports_renewals"),
            ("🔙 بازگشت", "reports_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_REPORT_TYPE

async def show_server_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show server reports menu."""
    query = update.callback_query
    await query.answer()
    
    # Get quick stats
    stats = await reports_service.get_server_stats()
    
    message = (
        "🌍 <b>گزارش‌های سرور</b>\n\n"
        "📊 <b>خلاصه آمار:</b>\n"
        f"• سرورهای فعال: {stats['active_servers']}\n"
        f"• کل ترافیک: {format_size(stats['total_traffic'])}\n"
        f"• میانگین پینگ: {stats['average_ping']} ms\n"
        f"• خطاهای اخیر: {stats['recent_errors']}\n\n"
        "📈 <b>نمودار بار:</b>\n"
        f"{stats['load_chart']}\n\n"
        "لطفاً نوع گزارش مورد نظر را انتخاب کنید:"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="reports",
        buttons=[
            ("📊 وضعیت", "reports_status"),
            ("📈 ترافیک", "reports_server_traffic"),
            ("⚠️ خطاها", "reports_errors"),
            ("🔙 بازگشت", "reports_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_REPORT_TYPE

async def show_overview_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show overview report with key metrics."""
    query = update.callback_query
    await query.answer()
    
    # Get overview stats
    stats = await reports_service.get_overview_stats()
    
    message = (
        "📊 <b>گزارش کلی سیستم</b>\n\n"
        "💰 <b>وضعیت مالی:</b>\n"
        f"• درآمد کل: {format_currency(stats['total_income'])}\n"
        f"• درآمد ماه: {format_currency(stats['month_income'])}\n"
        f"• میانگین روزانه: {format_currency(stats['daily_average'])}\n\n"
        "👥 <b>وضعیت کاربران:</b>\n"
        f"• کل: {stats['total_users']}\n"
        f"• فعال: {stats['active_users']}\n"
        f"• جدید: {stats['new_users']}\n\n"
        "🌍 <b>وضعیت سرورها:</b>\n"
        f"• تعداد: {stats['total_servers']}\n"
        f"• ترافیک: {format_size(stats['total_traffic'])}\n"
        f"• بار: {stats['average_load']}%\n\n"
        "📈 <b>نمودار عملکرد:</b>\n"
        f"{stats['performance_chart']}"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="reports",
        buttons=[
            ("📥 دانلود PDF", "reports_download_pdf"),
            ("📊 نمودارها", "reports_charts"),
            ("🔄 بروزرسانی", "reports_refresh"),
            ("🔙 بازگشت", "reports_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_REPORT_TYPE

async def select_report_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select time period for report."""
    query = update.callback_query
    await query.answer()
    
    # Store report type in context
    context.user_data['report_type'] = query.data.split('_')[1]
    
    message = (
        "📅 <b>انتخاب بازه زمانی</b>\n\n"
        "لطفاً بازه زمانی مورد نظر برای گزارش را انتخاب کنید:"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="reports",
        buttons=[
            ("📅 امروز", "reports_period_today"),
            ("📅 هفته", "reports_period_week"),
            ("📅 ماه", "reports_period_month"),
            ("📅 سال", "reports_period_year"),
            ("🔙 بازگشت", "reports_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_REPORT_PERIOD

async def select_report_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select format for report."""
    query = update.callback_query
    await query.answer()
    
    # Store period in context
    context.user_data['report_period'] = query.data.split('_')[-1]
    
    message = (
        "📄 <b>انتخاب فرمت گزارش</b>\n\n"
        "لطفاً فرمت مورد نظر برای دریافت گزارش را انتخاب کنید:"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="reports",
        buttons=[
            ("📊 نمایش", "reports_format_view"),
            ("📥 PDF", "reports_format_pdf"),
            ("📊 Excel", "reports_format_excel"),
            ("🔙 بازگشت", "reports_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_REPORT_FORMAT

async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate and send the requested report."""
    query = update.callback_query
    await query.answer()
    
    # Get report parameters from context
    report_type = context.user_data.get('report_type')
    report_period = context.user_data.get('report_period')
    report_format = query.data.split('_')[-1]
    
    # Show progress message
    progress_message = await query.edit_message_text(
        "⏳ در حال تهیه گزارش...\n"
        "لطفاً صبر کنید...",
        parse_mode='HTML'
    )
    
    try:
        # Generate report
        result = await reports_service.generate_report(
            report_type=report_type,
            period=report_period,
            format=report_format
        )
        
        if report_format == 'view':
            # Show report in message
            message = (
                f"📊 <b>گزارش {result['title']}</b>\n\n"
                f"📅 بازه زمانی: {result['period']}\n"
                f"🕒 تاریخ تهیه: {format_date(datetime.now())}\n\n"
                f"{result['content']}"
            )
            
        else:
            # Send report file
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=result['file'],
                filename=result['filename'],
                caption=f"📊 گزارش {result['title']}\n"
                        f"📅 بازه زمانی: {result['period']}"
            )
            message = "✅ گزارش با موفقیت ارسال شد."
            
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        message = (
            "❌ <b>خطا در تهیه گزارش</b>\n\n"
            f"علت: {str(e)}"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="reports",
        buttons=[("🔙 بازگشت", "reports_menu")]
    )
    
    await progress_message.edit_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    # Clear report parameters from context
    context.user_data.pop('report_type', None)
    context.user_data.pop('report_period', None)
    
    return SELECTING_REPORT_TYPE

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

reports_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(reports_menu, pattern="^admin_reports$")
    ],
    states={
        SELECTING_REPORT_TYPE: [
            CallbackQueryHandler(show_financial_reports, pattern="^reports_financial$"),
            CallbackQueryHandler(show_user_reports, pattern="^reports_users$"),
            CallbackQueryHandler(show_server_reports, pattern="^reports_servers$"),
            CallbackQueryHandler(show_overview_report, pattern="^reports_overview$"),
            CallbackQueryHandler(select_report_period, pattern="^reports_(income|sales|discounts|activity|traffic|renewals|status|server_traffic|errors)$"),
            CallbackQueryHandler(reports_menu, pattern="^reports_menu$"),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
        ],
        SELECTING_REPORT_PERIOD: [
            CallbackQueryHandler(select_report_format, pattern="^reports_period_"),
            CallbackQueryHandler(reports_menu, pattern="^reports_menu$")
        ],
        SELECTING_REPORT_FORMAT: [
            CallbackQueryHandler(generate_report, pattern="^reports_format_"),
            CallbackQueryHandler(reports_menu, pattern="^reports_menu$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
    ],
    map_to_parent={
        ConversationHandler.END: 'SELECTING_ADMIN_ACTION'
    }
) 