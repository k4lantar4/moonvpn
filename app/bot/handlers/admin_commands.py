"""
Admin command handlers for MoonVPN Telegram Bot.

This module provides handlers for admin commands in different admin groups.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.bot.services.admin_service import AdminService
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin commands based on group type."""
    if not update.effective_chat or not update.effective_message:
        return
        
    chat_id = update.effective_chat.id
    admin_service = context.bot_data.get("admin_service")
    
    if not await admin_service.is_admin_group(chat_id):
        return
        
    group_type = await admin_service.get_group_type(chat_id)
    if not group_type:
        return
    
    command = update.effective_message.text.lower()
    
    try:
        if group_type == "manage":
            await handle_manage_commands(update, context, command)
        elif group_type == "reports":
            await handle_report_commands(update, context, command)
        elif group_type == "logs":
            await handle_log_commands(update, context, command)
        elif group_type == "transactions":
            await handle_transaction_commands(update, context, command)
        elif group_type == "outages":
            await handle_outage_commands(update, context, command)
        elif group_type == "sellers":
            await handle_seller_commands(update, context, command)
        elif group_type == "backups":
            await handle_backup_commands(update, context, command)
            
    except Exception as e:
        logger.error(f"Error handling admin command in group {group_type}: {str(e)}")
        await update.effective_message.reply_text(
            "❌ خطا در پردازش دستور. لطفاً دوباره تلاش کنید."
        )

async def handle_manage_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
    """Handle commands in the management group."""
    if command == "/status":
        # Get system status
        status = await context.bot_data["admin_service"].get_system_status(context.bot_data["db"])
        message = (
            f"📊 وضعیت سیستم:\n\n"
            f"🖥️ تعداد سرورها: {status['total_servers']}\n"
            f"✅ سرورهای آنلاین: {status['online_servers']}\n"
            f"👥 تعداد کاربران: {status['total_users']}\n"
            f"📡 ترافیک کل: {status['total_traffic'] / 1024 / 1024 / 1024:.2f} GB\n"
            f"🕒 آخرین بروزرسانی: {status['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await update.effective_message.reply_text(message)
        
    elif command == "/health":
        # Check server health
        servers = context.bot_data["db"].query(Server).filter(Server.is_active == True).all()
        for server in servers:
            health = await context.bot_data["admin_service"].check_server_health(server.id, context.bot_data["db"])
            if health["alerts"]:
                message = "⚠️ هشدارهای سلامت سرور:\n\n"
                for alert in health["alerts"]:
                    message += f"• {alert['message']}\n"
                await update.effective_message.reply_text(message)

async def handle_report_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
    """Handle commands in the reports group."""
    if command == "/stats":
        # Get group statistics
        stats = await context.bot_data["admin_service"].get_group_stats("reports", context.bot_data["db"])
        message = (
            f"📊 آمار سیستم:\n\n"
            f"🖥️ تعداد سرورها: {stats['total_servers']}\n"
            f"✅ سرورهای آنلاین: {stats['online_servers']}\n"
            f"👥 تعداد کاربران: {stats['total_users']}\n"
            f"📡 ترافیک کل: {stats['total_traffic'] / 1024 / 1024 / 1024:.2f} GB\n"
            f"🕒 زمان گزارش: {stats['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await update.effective_message.reply_text(message)

async def handle_log_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
    """Handle commands in the logs group."""
    if command == "/recent":
        # Get recent logs
        message = "📄 لاگ‌های اخیر سیستم:\n\n"
        # Implement log retrieval
        await update.effective_message.reply_text(message)

async def handle_transaction_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
    """Handle commands in the transactions group."""
    try:
        if command == "/transactions":
            # Get transaction statistics
            stats = await context.bot_data["transaction_service"].get_transaction_stats(context.bot_data["db"])
            message = (
                f"💰 آمار تراکنش‌ها (۳۰ روز اخیر):\n\n"
                f"📊 تعداد کل تراکنش‌ها: {stats['total_transactions']}\n"
                f"💵 مبلغ کل: {stats['total_amount']} تومان\n"
                f"✅ تراکنش‌های موفق: {stats['successful_transactions']}\n"
                f"💵 مبلغ موفق: {stats['successful_amount']} تومان\n"
                f"❌ تراکنش‌های ناموفق: {stats['failed_transactions']}\n"
                f"💵 مبلغ ناموفق: {stats['failed_amount']} تومان\n\n"
                f"📅 دوره: {stats['start_date'].strftime('%Y-%m-%d')} تا {stats['end_date'].strftime('%Y-%m-%d')}"
            )
            await update.effective_message.reply_text(message)
            
        elif command == "/transactions_recent":
            # Get recent transactions
            transactions = await context.bot_data["transaction_service"].get_recent_transactions(context.bot_data["db"])
            message = "📋 تراکنش‌های اخیر:\n\n"
            
            for t in transactions:
                status_emoji = "✅" if t["status"] == "success" else "❌"
                message += (
                    f"{status_emoji} {t['amount']} تومان\n"
                    f"👤 کاربر: {t['username'] or t['phone_number']}\n"
                    f"💳 روش پرداخت: {t['method']}\n"
                    f"🕒 تاریخ: {t['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
            
            await update.effective_message.reply_text(message)
            
        elif command == "/transactions_failed":
            # Get failed transactions
            transactions = await context.bot_data["transaction_service"].get_failed_transactions(context.bot_data["db"])
            message = "❌ تراکنش‌های ناموفق اخیر:\n\n"
            
            for t in transactions:
                message += (
                    f"💵 مبلغ: {t['amount']} تومان\n"
                    f"👤 کاربر: {t['username'] or t['phone_number']}\n"
                    f"💳 روش پرداخت: {t['method']}\n"
                    f"❌ خطا: {t['error']}\n"
                    f"🕒 تاریخ: {t['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
            
            await update.effective_message.reply_text(message)
            
        elif command == "/transactions_methods":
            # Get payment method statistics
            stats = await context.bot_data["transaction_service"].get_payment_method_stats(context.bot_data["db"])
            message = "💳 آمار روش‌های پرداخت:\n\n"
            
            for method in stats["methods"]:
                message += (
                    f"📊 {method['method']}:\n"
                    f"• تعداد کل: {method['total_count']}\n"
                    f"• مبلغ کل: {method['total_amount']} تومان\n"
                    f"• موفق: {method['success_count']} ({method['success_rate']:.1f}%)\n\n"
                )
            
            message += f"📅 دوره: {stats['start_date'].strftime('%Y-%m-%d')} تا {stats['end_date'].strftime('%Y-%m-%d')}"
            await update.effective_message.reply_text(message)
            
    except Exception as e:
        logger.error(f"Error handling transaction command: {str(e)}")
        await update.effective_message.reply_text(
            "❌ خطا در پردازش دستور تراکنش‌ها. لطفاً دوباره تلاش کنید."
        )

async def handle_outage_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
    """Handle commands in the outages group."""
    if command == "/outages":
        # Get current outages
        message = "⚠️ وضعیت مشکلات سیستم:\n\n"
        # Implement outage checking
        await update.effective_message.reply_text(message)

async def handle_seller_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
    """Handle commands in the sellers group."""
    if command == "/sellers":
        # Get seller statistics
        stats = await context.bot_data["admin_service"].get_group_stats("sellers", context.bot_data["db"])
        message = (
            f"👥 آمار فروشندگان:\n\n"
            f"📊 تعداد کل فروشندگان: {stats['total_sellers']}\n"
            f"✅ فروشندگان فعال: {stats['active_sellers']}\n"
            f"💰 مجموع کمیسیون: {stats['total_commission']} تومان"
        )
        await update.effective_message.reply_text(message)

async def handle_backup_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
    """Handle commands in the backups group."""
    try:
        if command == "/backup":
            # Get backup status for all servers
            servers = context.bot_data["db"].query(Server).filter(Server.is_active == True).all()
            message = "💾 وضعیت پشتیبان‌گیری:\n\n"
            
            for server in servers:
                status = await context.bot_data["backup_service"].get_backup_status(server.id, context.bot_data["db"])
                message += f"🖥️ سرور {server.name}:\n"
                message += f"📊 تعداد پشتیبان‌ها: {status['total_backups']}\n"
                if status['latest_backup']:
                    message += f"🕒 آخرین پشتیبان: {status['latest_backup']['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                message += "\n"
            
            await update.effective_message.reply_text(message)
            
        elif command == "/backup_create":
            # Create backup for all servers
            servers = context.bot_data["db"].query(Server).filter(Server.is_active == True).all()
            message = "🔄 در حال ایجاد پشتیبان...\n\n"
            
            for server in servers:
                try:
                    result = await context.bot_data["backup_service"].create_backup(server.id, context.bot_data["db"])
                    message += f"✅ پشتیبان سرور {server.name} با موفقیت ایجاد شد\n"
                except Exception as e:
                    message += f"❌ خطا در ایجاد پشتیبان سرور {server.name}: {str(e)}\n"
            
            await update.effective_message.reply_text(message)
            
        elif command == "/backup_cleanup":
            # Clean up old backups
            result = await context.bot_data["backup_service"].cleanup_old_backups()
            message = (
                f"🧹 پاکسازی پشتیبان‌های قدیمی:\n\n"
                f"📊 تعداد فایل‌های حذف شده: {result['removed_count']}\n"
                f"🕒 زمان اجرا: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await update.effective_message.reply_text(message)
            
        elif command == "/backup_stats":
            # Get backup statistics
            stats = await context.bot_data["backup_service"].get_backup_stats()
            message = (
                f"📊 آمار پشتیبان‌گیری:\n\n"
                f"📁 تعداد کل فایل‌ها: {stats['total_files']}\n"
                f"💾 حجم کل: {stats['total_size'] / 1024 / 1024:.2f} MB\n"
                f"🕒 قدیمی‌ترین پشتیبان: {stats['oldest_backup'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🕒 جدیدترین پشتیبان: {stats['newest_backup'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📅 دوره نگهداری: {stats['retention_days']} روز"
            )
            await update.effective_message.reply_text(message)
            
    except Exception as e:
        logger.error(f"Error handling backup command: {str(e)}")
        await update.effective_message.reply_text(
            "❌ خطا در پردازش دستور پشتیبان‌گیری. لطفاً دوباره تلاش کنید."
        ) 