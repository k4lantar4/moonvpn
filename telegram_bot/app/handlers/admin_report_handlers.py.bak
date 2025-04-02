import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
import io
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    filters
)

from app.api import api_client
from app.utils.logger import get_logger
from app.utils.permissions import is_admin, admin_only

# Set up logging
logger = get_logger(__name__)

# Define callback patterns
ADMIN_REPORT_PATTERN = r"^admin_report_(.+)$"
DATE_RANGE_PATTERN = r"^report_date_(.+)$"

# Compile patterns for faster matching
ADMIN_REPORT_REGEX = re.compile(ADMIN_REPORT_PATTERN)
DATE_RANGE_REGEX = re.compile(DATE_RANGE_PATTERN)

@admin_only
async def show_admin_reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the admin reports menu with different report options."""
    # Create keyboard with report options
    keyboard = [
        [InlineKeyboardButton("📊 گزارش عملکرد ادمین‌های پرداخت", callback_data="admin_report_payment")],
        [InlineKeyboardButton("🔍 جزئیات عملکرد من", callback_data="admin_report_my_performance")],
        [InlineKeyboardButton("📅 گزارش روزانه", callback_data="report_date_today")],
        [InlineKeyboardButton("📆 گزارش هفتگی", callback_data="report_date_week")],
        [InlineKeyboardButton("📅 گزارش ماهانه", callback_data="report_date_month")],
        [InlineKeyboardButton("🗓️ گزارش کامل", callback_data="report_date_all")],
    ]
    
    await update.effective_message.reply_text(
        "📊 *منوی گزارش‌های مدیریتی*\n\n"
        "لطفاً نوع گزارش موردنظر خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_admin_report_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin report selection."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Extract report type from callback data
    match = ADMIN_REPORT_REGEX.match(query.data)
    if not match:
        return
    
    report_type = match.group(1)
    
    # Handle different report types
    if report_type == "payment":
        # Show date range selection for payment admin report
        keyboard = [
            [InlineKeyboardButton("📅 امروز", callback_data="report_date_today")],
            [InlineKeyboardButton("📆 این هفته", callback_data="report_date_week")],
            [InlineKeyboardButton("🗓️ این ماه", callback_data="report_date_month")],
            [InlineKeyboardButton("📊 کل زمان", callback_data="report_date_all")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports_menu")]
        ]
        
        await query.edit_message_text(
            "📊 *گزارش عملکرد ادمین‌های پرداخت*\n\n"
            "لطفاً بازه زمانی موردنظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif report_type == "my_performance":
        # Show the current admin's performance
        await query.edit_message_text(
            "⏳ در حال دریافت گزارش عملکرد شما...",
            reply_markup=None
        )
        
        # Get reports for this admin only
        report_data = await api_client.get_payment_admin_reports(admin_id=user.id)
        
        if not report_data or not report_data.get("admins"):
            await query.edit_message_text(
                "❌ اطلاعاتی برای نمایش وجود ندارد یا خطایی رخ داده است.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports_menu")
                ]])
            )
            return
        
        # Get admin data (should only be one item since we filtered by admin_id)
        admin_data = report_data["admins"][0] if report_data["admins"] else None
        
        if not admin_data:
            await query.edit_message_text(
                "❌ اطلاعاتی برای نمایش وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports_menu")
                ]])
            )
            return
        
        # Format message with admin performance data
        admin_name = admin_data.get("admin_name", f"Admin #{admin_data['admin_id']}")
        approval_rate = admin_data.get("avg_approval_rate", 0) * 100
        avg_response_time = admin_data.get("avg_response_time_seconds", 0)
        
        if avg_response_time:
            # Format response time as minutes and seconds
            minutes = int(avg_response_time // 60)
            seconds = int(avg_response_time % 60)
            response_time_str = f"{minutes} دقیقه و {seconds} ثانیه"
        else:
            response_time_str = "اطلاعاتی موجود نیست"
        
        # Create detailed message
        message = (
            f"📊 *گزارش عملکرد {admin_name}*\n\n"
            f"📝 تعداد کل پرداخت‌های بررسی شده: {admin_data['total_processed']}\n"
            f"✅ تعداد تأییدشده‌ها: {admin_data['total_approved']}\n"
            f"❌ تعداد ردشده‌ها: {admin_data['total_rejected']}\n"
            f"📈 نرخ تأیید: {approval_rate:.1f}%\n"
            f"⏱️ میانگین زمان پاسخگویی: {response_time_str}\n\n"
            
            f"📅 *فعالیت اخیر:*\n"
            f"🔹 امروز: {admin_data['total_processed_today']} پرداخت\n"
            f"🔹 این هفته: {admin_data['total_processed_week']} پرداخت\n"
            f"🔹 این ماه: {admin_data['total_processed_month']} پرداخت\n\n"
        )
        
        # Add rejection reasons if available
        if admin_data.get("rejection_reasons"):
            message += f"❌ *دلایل رد پرداخت:*\n"
            for reason, count in sorted(admin_data["rejection_reasons"].items(), key=lambda x: x[1], reverse=True):
                message += f"🔹 {reason}: {count} مورد\n"
            message += "\n"
        
        # Add bank card distribution if available
        if admin_data.get("bank_card_distribution"):
            message += f"💳 *توزیع کارت‌های بانکی:*\n"
            for card, count in sorted(admin_data["bank_card_distribution"].items(), key=lambda x: x[1], reverse=True):
                message += f"🔹 {card}: {count} تراکنش\n"
        
        # Send message with back button
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports_menu")
            ]]),
            parse_mode="Markdown"
        )

async def handle_date_range_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle date range selection for reports."""
    query = update.callback_query
    await query.answer()
    
    # Handle special case for back button
    if query.data == "admin_reports_menu":
        return await show_admin_reports_menu(update, context)
    
    # Extract date range from callback data
    match = DATE_RANGE_REGEX.match(query.data)
    if not match:
        return
    
    date_range = match.group(1)
    
    # Calculate start and end dates based on selection
    end_date = datetime.now()
    start_date = None
    date_range_text = ""
    
    if date_range == "today":
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_range_text = "امروز"
    elif date_range == "week":
        # Start from beginning of the week (Saturday in Iranian calendar)
        days_since_saturday = (end_date.weekday() + 2) % 7  # Adjusting for Saturday as first day
        start_date = (end_date - timedelta(days=days_since_saturday)).replace(hour=0, minute=0, second=0, microsecond=0)
        date_range_text = "هفته جاری"
    elif date_range == "month":
        # Start from beginning of the month
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_range_text = "ماه جاری"
    elif date_range == "all":
        # No date filtering, use None for start_date
        date_range_text = "کل زمان"
    
    # Format dates for API request
    start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # Show loading message
    await query.edit_message_text(
        f"⏳ در حال دریافت گزارش {date_range_text}...",
        reply_markup=None
    )
    
    # Get report data from API
    report_data = await api_client.get_payment_admin_reports(
        start_date=start_date_str,
        end_date=end_date_str
    )
    
    if not report_data:
        await query.edit_message_text(
            "❌ اطلاعاتی برای نمایش وجود ندارد یا خطایی رخ داده است.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports_menu")
            ]])
        )
        return
    
    # Create text report
    report_message = await create_text_report(report_data, date_range_text)
    
    # Generate and send chart
    try:
        chart_image = await create_performance_chart(report_data)
        
        if chart_image:
            # Send chart image with caption
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=chart_image,
                caption=f"📊 نمودار عملکرد ادمین‌ها - {date_range_text}",
                reply_to_message_id=query.message.message_id
            )
    except Exception as e:
        logger.error(f"Error creating performance chart: {str(e)}")
    
    # Send text report with back button
    await query.edit_message_text(
        report_message,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت", callback_data="admin_reports_menu")
        ]]),
        parse_mode="Markdown"
    )

async def create_text_report(report_data: Dict, date_range_text: str) -> str:
    """Create a text report from the report data."""
    if not report_data or not report_data.get("admins"):
        return "❌ اطلاعاتی برای نمایش وجود ندارد."
    
    # Get overall statistics
    total_payments = report_data.get("total_payments", 0)
    total_approved = report_data.get("total_approved", 0)
    total_rejected = report_data.get("total_rejected", 0)
    overall_approval_rate = report_data.get("overall_approval_rate", 0) * 100
    avg_response_time = report_data.get("avg_response_time_seconds", 0)
    
    if avg_response_time:
        # Format response time as minutes and seconds
        minutes = int(avg_response_time // 60)
        seconds = int(avg_response_time % 60)
        response_time_str = f"{minutes} دقیقه و {seconds} ثانیه"
    else:
        response_time_str = "اطلاعاتی موجود نیست"
    
    # Create overall statistics message
    message = (
        f"📊 *گزارش عملکرد ادمین‌های پرداخت - {date_range_text}*\n\n"
        f"📝 تعداد کل پرداخت‌ها: {total_payments}\n"
        f"✅ تأییدشده: {total_approved} ({overall_approval_rate:.1f}%)\n"
        f"❌ ردشده: {total_rejected} ({100-overall_approval_rate:.1f}%)\n"
        f"⏱️ میانگین زمان پاسخگویی: {response_time_str}\n\n"
        f"👥 *عملکرد ادمین‌ها:*\n"
    )
    
    # Add individual admin statistics
    for i, admin in enumerate(report_data["admins"]):
        admin_name = admin.get("admin_name", f"Admin #{admin['admin_id']}")
        admin_approval_rate = admin.get("avg_approval_rate", 0) * 100
        admin_processed = admin.get("total_processed", 0)
        
        if i < 3:  # Show detailed stats for top 3 admins
            message += (
                f"\n🔸 *{admin_name}*\n"
                f"  • تعداد پرداخت‌ها: {admin_processed}\n"
                f"  • نرخ تأیید: {admin_approval_rate:.1f}%\n"
            )
            
            # Show response time if available
            admin_response_time = admin.get("avg_response_time_seconds")
            if admin_response_time:
                minutes = int(admin_response_time // 60)
                seconds = int(admin_response_time % 60)
                message += f"  • میانگین پاسخگویی: {minutes}:{seconds:02d}\n"
        else:
            # For remaining admins, just show basic stats on one line
            message += f"🔹 {admin_name}: {admin_processed} پرداخت ({admin_approval_rate:.1f}%)\n"
    
    return message

async def create_performance_chart(report_data: Dict) -> Optional[io.BytesIO]:
    """Create a performance chart from the report data."""
    if not report_data or not report_data.get("admins") or len(report_data["admins"]) == 0:
        return None
    
    try:
        # Create a new figure
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Get data for the chart
        admin_names = []
        approval_rates = []
        response_times = []
        transaction_counts = []
        
        # Limit to top 5 admins by transaction count
        top_admins = sorted(report_data["admins"], key=lambda x: x.get("total_processed", 0), reverse=True)[:5]
        
        for admin in top_admins:
            admin_name = admin.get("admin_name", f"Admin #{admin['admin_id']}")
            admin_names.append(admin_name)
            approval_rates.append(admin.get("avg_approval_rate", 0) * 100)
            
            # Convert response time to minutes for better visualization
            response_time = admin.get("avg_response_time_seconds", 0)
            response_time_min = response_time / 60 if response_time else 0
            response_times.append(response_time_min)
            
            transaction_counts.append(admin.get("total_processed", 0))
        
        # If no admins with data, return None
        if not admin_names:
            return None
        
        # Set up the bar chart
        x = np.arange(len(admin_names))
        width = 0.3
        
        # Plot bars
        bar1 = ax.bar(x - width, approval_rates, width, label='نرخ تأیید (%)', color='green', alpha=0.7)
        bar2 = ax.bar(x, transaction_counts, width, label='تعداد تراکنش', color='blue', alpha=0.7)
        bar3 = ax.bar(x + width, response_times, width, label='زمان پاسخگویی (دقیقه)', color='red', alpha=0.7)
        
        # Add labels and title
        ax.set_xlabel('ادمین‌ها')
        ax.set_title('مقایسه عملکرد ادمین‌های پرداخت')
        ax.set_xticks(x)
        ax.set_xticklabels(admin_names, rotation=45, ha='right')
        
        # Add legend
        ax.legend()
        
        # Add value labels on bars
        def add_labels(bars):
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
        
        add_labels(bar1)
        add_labels(bar2)
        add_labels(bar3)
        
        # Adjust layout
        fig.tight_layout()
        
        # Save figure to BytesIO object
        buf = io.BytesIO()
        canvas = FigureCanvas(fig)
        canvas.print_png(buf)
        buf.seek(0)
        
        return buf
    
    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        return None

def get_admin_report_handlers():
    """Return handlers for admin reports."""
    return [
        CommandHandler("reports", show_admin_reports_menu),
        CallbackQueryHandler(show_admin_reports_menu, pattern="^admin_reports_menu$"),
        CallbackQueryHandler(handle_admin_report_selection, pattern=ADMIN_REPORT_PATTERN),
        CallbackQueryHandler(handle_date_range_selection, pattern=DATE_RANGE_PATTERN)
    ]