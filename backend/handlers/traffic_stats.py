"""
MoonVPN Telegram Bot - Traffic Statistics Handler.

This module provides functionality to display traffic usage statistics and bandwidth information.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CallbackQueryHandler, 
    CommandHandler, 
    ConversationHandler
)

from core.database.models.user import User
from core.database.models.vpn_account import VPNAccount
from bot.constants import CallbackPatterns, States
from core.utils.formatting import format_size

logger = logging.getLogger(__name__)

# Traffic stats image URL
TRAFFIC_STATS_IMAGE = "https://example.com/path/to/traffic_stats.jpg"  # Replace with actual image URL or file_id

# States for the traffic conversation
(
    TRAFFIC_MAIN,
    TRAFFIC_DETAIL,
    TRAFFIC_HISTORY
) = range(3)

async def traffic_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show traffic statistics overview."""
    user = update.effective_user
    message = update.message or update.callback_query.message
    
    # Get user accounts from database
    # In real implementation, fetch from database
    accounts = get_user_accounts(user.id)
    
    if not accounts:
        # No accounts found
        stats_text = (
            "📊 <b>آمار مصرف ترافیک</b>\n\n"
            "شما هنوز هیچ اکانت فعالی ندارید. برای خرید اکانت، از منوی اصلی گزینه خرید را انتخاب کنید."
        )
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("🛒 خرید اکانت", callback_data=CallbackPatterns.BUY_ACCOUNT)],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send or edit message
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=stats_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await message.reply_text(
                text=stats_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        
        return ConversationHandler.END
    
    # Calculate total traffic stats
    total_stats = calculate_total_stats(accounts)
    
    # Create stats message
    stats_text = (
        f"📊 <b>آمار مصرف ترافیک</b>\n\n"
        f"<b>وضعیت کلی:</b>\n"
        f"• اکانت‌های فعال: {total_stats['active_accounts']}/{total_stats['total_accounts']}\n"
        f"• کل ترافیک: {total_stats['total_traffic']} GB\n"
        f"• ترافیک مصرفی: {total_stats['used_traffic']} GB ({total_stats['usage_percentage']}%)\n"
        f"• ترافیک باقی‌مانده: {total_stats['remaining_traffic']} GB\n\n"
    )
    
    # Create visual progress bar for total usage
    progress_bar = create_progress_bar(total_stats['usage_percentage'])
    stats_text += f"{progress_bar}\n\n"
    
    # Add list of accounts with brief stats
    stats_text += "<b>اکانت‌های شما:</b>\n\n"
    
    for i, account in enumerate(accounts, 1):
        status_emoji = "✅" if account['is_active'] else "❌"
        stats_text += (
            f"{i}. {status_emoji} <b>{account['name']}</b>\n"
            f"   • مصرف: {account['used_gb']}/{account['total_gb']} GB ({account['usage_percentage']}%)\n"
            f"   • انقضا: {account['days_left']} روز دیگر\n\n"
        )
    
    # Create keyboard
    keyboard = []
    
    # Add buttons for each account
    for i, account in enumerate(accounts, 1):
        keyboard.append([
            InlineKeyboardButton(f"📊 جزئیات اکانت {i}", callback_data=f"{CallbackPatterns.TRAFFIC_DETAIL}_{account['id']}")
        ])
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton("📈 نمودار مصرف", callback_data=f"{CallbackPatterns.TRAFFIC_GRAPH}"),
        InlineKeyboardButton("📜 تاریخچه مصرف", callback_data=f"{CallbackPatterns.TRAFFIC_HISTORY}")
    ])
    keyboard.append([
        InlineKeyboardButton("🔄 بروزرسانی آمار", callback_data=f"{CallbackPatterns.TRAFFIC_REFRESH}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.MAIN_MENU)
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    try:
        if update.callback_query:
            await update.callback_query.answer()
            
            if hasattr(update.callback_query.message, 'photo'):
                await update.callback_query.edit_message_caption(
                    caption=stats_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await update.callback_query.edit_message_text(
                    text=stats_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            try:
                await message.reply_photo(
                    photo=TRAFFIC_STATS_IMAGE,
                    caption=stats_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending traffic stats with image: {e}")
                await message.reply_text(
                    text=stats_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Error in traffic stats command: {e}")
    
    return TRAFFIC_MAIN

async def show_account_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show detailed traffic statistics for a specific account."""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    account_id = query.data.split("_")[1]
    user_id = update.effective_user.id
    
    # Get account details
    # In real implementation, fetch from database
    account = get_account_by_id(account_id, user_id)
    
    if not account:
        await query.edit_message_text(
            "❌ اکانت مورد نظر پیدا نشد یا متعلق به شما نیست.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.CHECK_TRAFFIC}")
            ]]),
            parse_mode="HTML"
        )
        return TRAFFIC_MAIN
    
    # Get detailed usage statistics
    # In real implementation, fetch from database or API
    usage_details = get_account_usage_details(account_id)
    
    # Create detail message
    detail_text = (
        f"📊 <b>جزئیات مصرف ترافیک</b>\n\n"
        f"<b>اکانت:</b> {account['name']}\n"
        f"<b>وضعیت:</b> {'فعال ✅' if account['is_active'] else 'غیرفعال ❌'}\n"
        f"<b>سرور:</b> {account['server']}\n"
        f"<b>آی‌پی:</b> {account['ip']}\n\n"
        
        f"<b>آمار ترافیک:</b>\n"
        f"• ترافیک کل: {account['total_gb']} GB\n"
        f"• ترافیک مصرفی: {account['used_gb']} GB ({account['usage_percentage']}%)\n"
        f"• ترافیک باقی‌مانده: {account['remaining_gb']} GB\n\n"
        
        f"<b>زمان انقضا:</b>\n"
        f"• تاریخ شروع: {account['start_date']}\n"
        f"• تاریخ انقضا: {account['expire_date']}\n"
        f"• زمان باقی‌مانده: {account['days_left']} روز\n\n"
    )
    
    # Create visual progress bar
    progress_bar = create_progress_bar(account['usage_percentage'])
    detail_text += f"{progress_bar}\n\n"
    
    # Add daily usage statistics
    detail_text += "<b>مصرف روزانه (۷ روز اخیر):</b>\n"
    
    for day_usage in usage_details['daily_usage']:
        detail_text += f"• {day_usage['date']}: {day_usage['usage']} GB\n"
    
    detail_text += "\n<b>مصرف بر اساس برنامه:</b>\n"
    
    for app_usage in usage_details['app_usage']:
        detail_text += f"• {app_usage['app_name']}: {app_usage['usage']} GB ({app_usage['percentage']}%)\n"
    
    # Create keyboard for navigation
    keyboard = [
        [
            InlineKeyboardButton("📈 نمودار مصرف", callback_data=f"{CallbackPatterns.TRAFFIC_GRAPH}_{account_id}"),
            InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"{CallbackPatterns.TRAFFIC_DETAIL}_{account_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت به لیست اکانت‌ها", callback_data=f"{CallbackPatterns.CHECK_TRAFFIC}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        await query.edit_message_text(
            text=detail_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing account detail: {e}")
    
    return TRAFFIC_DETAIL

async def show_traffic_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show traffic usage history."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    # Get traffic history
    # In real implementation, fetch from database
    history = get_traffic_history(user_id)
    
    # Create history message
    history_text = (
        "📜 <b>تاریخچه مصرف ترافیک</b>\n\n"
        "آمار مصرف ترافیک شما در ماه‌های اخیر:\n\n"
    )
    
    # Add monthly statistics
    for month in history['monthly_stats']:
        history_text += (
            f"<b>{month['month']}</b>\n"
            f"• مصرف کل: {month['total_usage']} GB\n"
            f"• میانگین روزانه: {month['daily_average']} GB\n"
            f"• بیشترین مصرف: {month['peak_day']} ({month['peak_usage']} GB)\n"
            f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        )
    
    # Create keyboard for filtering
    keyboard = [
        [
            InlineKeyboardButton("ماه جاری", callback_data=f"{CallbackPatterns.TRAFFIC_HISTORY}_current"),
            InlineKeyboardButton("۳ ماه اخیر", callback_data=f"{CallbackPatterns.TRAFFIC_HISTORY}_3months")
        ],
        [
            InlineKeyboardButton("۶ ماه اخیر", callback_data=f"{CallbackPatterns.TRAFFIC_HISTORY}_6months"),
            InlineKeyboardButton("یک سال اخیر", callback_data=f"{CallbackPatterns.TRAFFIC_HISTORY}_year")
        ],
        [InlineKeyboardButton("🔙 بازگشت به آمار ترافیک", callback_data=f"{CallbackPatterns.CHECK_TRAFFIC}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        await query.edit_message_text(
            text=history_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing traffic history: {e}")
    
    return TRAFFIC_HISTORY

async def show_traffic_graph(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show traffic usage graph."""
    query = update.callback_query
    await query.answer()
    
    # Check if account ID is provided for specific account graph
    parts = query.data.split("_")
    account_id = parts[1] if len(parts) > 1 else None
    
    # Message for graph
    graph_text = (
        "📈 <b>نمودار مصرف ترافیک</b>\n\n"
        "برای مشاهده نمودار، از وب‌پنل استفاده کنید. لینک مستقیم به نمودار مصرف شما:\n\n"
        "<a href='https://example.com/dashboard/traffic'>مشاهده نمودار در وب‌پنل</a>\n\n"
        "یا می‌توانید از مصرف روزانه خود در ۷ روز اخیر آگاه شوید:\n\n"
    )
    
    # Get daily usage data
    # In real implementation, fetch from database
    daily_usage = get_daily_usage(update.effective_user.id, account_id)
    
    # Add ASCII graph or representation
    for day in daily_usage:
        # Create a simple bar chart representation
        bar_length = int(day['usage_gb'] * 2)  # Scale for better visualization
        bar = "█" * bar_length
        graph_text += f"{day['date']}: {bar} {day['usage_gb']} GB\n"
    
    # Create keyboard for navigation
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.CHECK_TRAFFIC}")]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        await query.edit_message_text(
            text=graph_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing traffic graph: {e}")
    
    return TRAFFIC_MAIN

async def refresh_traffic_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Refresh traffic statistics."""
    query = update.callback_query
    await query.answer("در حال بروزرسانی آمار...")
    
    # Simulate a delay for data refreshing
    await asyncio.sleep(1)
    
    # Return to main traffic stats
    return await traffic_stats_command(update, context)

def get_user_accounts(user_id: int) -> List[Dict[str, Any]]:
    """Get all VPN accounts for a user.
    
    In a real implementation, this would fetch from the database.
    """
    # Mock data for demonstration
    return [
        {
            "id": "acc1",
            "name": "اکانت اصلی",
            "server": "هلند",
            "ip": "45.89.xx.xx",
            "is_active": True,
            "used_gb": 25.7,
            "total_gb": 100,
            "usage_percentage": 26,
            "remaining_gb": 74.3,
            "start_date": "2023-06-01",
            "expire_date": "2023-07-01",
            "days_left": 15
        },
        {
            "id": "acc2",
            "name": "اکانت مخصوص کار",
            "server": "آلمان",
            "ip": "138.201.xx.xx",
            "is_active": True,
            "used_gb": 42.3,
            "total_gb": 50,
            "usage_percentage": 85,
            "remaining_gb": 7.7,
            "start_date": "2023-05-15",
            "expire_date": "2023-06-15",
            "days_left": 5
        },
        {
            "id": "acc3",
            "name": "اکانت ذخیره",
            "server": "فرانسه",
            "ip": "51.158.xx.xx",
            "is_active": False,
            "used_gb": 0,
            "total_gb": 30,
            "usage_percentage": 0,
            "remaining_gb": 30,
            "start_date": "2023-04-01",
            "expire_date": "2023-05-01",
            "days_left": 0
        }
    ]

def get_account_by_id(account_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get account details by ID.
    
    In a real implementation, this would fetch from the database.
    """
    accounts = get_user_accounts(user_id)
    for account in accounts:
        if account['id'] == account_id:
            return account
    return None

def get_account_usage_details(account_id: str) -> Dict[str, Any]:
    """Get detailed usage statistics for an account.
    
    In a real implementation, this would fetch from the database or API.
    """
    # Mock data for demonstration
    return {
        "daily_usage": [
            {"date": "امروز", "usage": 1.2},
            {"date": "دیروز", "usage": 2.5},
            {"date": "2 روز قبل", "usage": 1.7},
            {"date": "3 روز قبل", "usage": 3.1},
            {"date": "4 روز قبل", "usage": 2.3},
            {"date": "5 روز قبل", "usage": 1.9},
            {"date": "6 روز قبل", "usage": 2.0}
        ],
        "app_usage": [
            {"app_name": "وب‌گردی", "usage": 12.5, "percentage": 48},
            {"app_name": "استریم ویدیو", "usage": 8.2, "percentage": 32},
            {"app_name": "دانلود", "usage": 3.7, "percentage": 14},
            {"app_name": "سایر", "usage": 1.3, "percentage": 6}
        ]
    }

def get_traffic_history(user_id: int) -> Dict[str, Any]:
    """Get traffic usage history.
    
    In a real implementation, this would fetch from the database.
    """
    # Mock data for demonstration
    return {
        "monthly_stats": [
            {
                "month": "خرداد ۱۴۰۲",
                "total_usage": 78.5,
                "daily_average": 2.6,
                "peak_day": "15 خرداد",
                "peak_usage": 5.2
            },
            {
                "month": "اردیبهشت ۱۴۰۲",
                "total_usage": 65.3,
                "daily_average": 2.1,
                "peak_day": "23 اردیبهشت",
                "peak_usage": 4.7
            },
            {
                "month": "فروردین ۱۴۰۲",
                "total_usage": 72.1,
                "daily_average": 2.3,
                "peak_day": "5 فروردین",
                "peak_usage": 6.8
            }
        ]
    }

def get_daily_usage(user_id: int, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get daily usage data for the last 7 days.
    
    In a real implementation, this would fetch from the database.
    """
    # Mock data for demonstration
    return [
        {"date": "امروز", "usage_gb": 1.8},
        {"date": "دیروز", "usage_gb": 2.5},
        {"date": "2 روز قبل", "usage_gb": 1.9},
        {"date": "3 روز قبل", "usage_gb": 3.2},
        {"date": "4 روز قبل", "usage_gb": 2.0},
        {"date": "5 روز قبل", "usage_gb": 1.5},
        {"date": "6 روز قبل", "usage_gb": 2.2}
    ]

def calculate_total_stats(accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate total traffic statistics from all accounts."""
    total_accounts = len(accounts)
    active_accounts = sum(1 for account in accounts if account['is_active'])
    
    total_traffic = sum(account['total_gb'] for account in accounts)
    used_traffic = sum(account['used_gb'] for account in accounts)
    remaining_traffic = total_traffic - used_traffic
    
    usage_percentage = int((used_traffic / total_traffic) * 100) if total_traffic > 0 else 0
    
    return {
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "total_traffic": total_traffic,
        "used_traffic": used_traffic,
        "remaining_traffic": remaining_traffic,
        "usage_percentage": usage_percentage
    }

def create_progress_bar(percentage: int, length: int = 10) -> str:
    """Create a visual progress bar based on percentage."""
    filled_length = int(length * percentage / 100)
    empty_length = length - filled_length
    
    # Create bar with different colors based on usage
    if percentage < 50:
        bar = "🟢" * filled_length + "⚪️" * empty_length
    elif percentage < 80:
        bar = "🟠" * filled_length + "⚪️" * empty_length
    else:
        bar = "🔴" * filled_length + "⚪️" * empty_length
    
    return f"{bar} {percentage}%"

def get_traffic_stats_handlers() -> List:
    """Return all handlers related to traffic statistics."""
    
    traffic_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("traffic", traffic_stats_command),
            CallbackQueryHandler(traffic_stats_command, pattern=f"^{CallbackPatterns.CHECK_TRAFFIC}$")
        ],
        states={
            TRAFFIC_MAIN: [
                CallbackQueryHandler(show_account_detail, pattern=f"^{CallbackPatterns.TRAFFIC_DETAIL}_"),
                CallbackQueryHandler(show_traffic_graph, pattern=f"^{CallbackPatterns.TRAFFIC_GRAPH}"),
                CallbackQueryHandler(show_traffic_history, pattern=f"^{CallbackPatterns.TRAFFIC_HISTORY}$"),
                CallbackQueryHandler(refresh_traffic_stats, pattern=f"^{CallbackPatterns.TRAFFIC_REFRESH}$"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$")
            ],
            TRAFFIC_DETAIL: [
                CallbackQueryHandler(show_traffic_graph, pattern=f"^{CallbackPatterns.TRAFFIC_GRAPH}_"),
                CallbackQueryHandler(show_account_detail, pattern=f"^{CallbackPatterns.TRAFFIC_DETAIL}_"),
                CallbackQueryHandler(traffic_stats_command, pattern=f"^{CallbackPatterns.CHECK_TRAFFIC}$")
            ],
            TRAFFIC_HISTORY: [
                CallbackQueryHandler(show_traffic_history, pattern=f"^{CallbackPatterns.TRAFFIC_HISTORY}_"),
                CallbackQueryHandler(traffic_stats_command, pattern=f"^{CallbackPatterns.CHECK_TRAFFIC}$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END)
        ],
        name="traffic_conversation",
        persistent=False
    )
    
    return [traffic_conversation] 