"""
Admin command handlers for MoonVPN Telegram Bot.

This module provides handlers for admin commands in various groups.
"""

from typing import Dict, Any
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.bot.services.admin_service import AdminService
from app.bot.services.backup_service import BackupService
from app.bot.services.transaction_service import TransactionService
from app.bot.services.seller_service import SellerService
from app.bot.services.alert_service import AlertService
from app.bot.services.log_service import LogService
from app.bot.utils.logger import setup_logger

# Initialize services
admin_service = AdminService()
backup_service = BackupService()
transaction_service = TransactionService()
seller_service = SellerService()
alert_service = AlertService()
log_service = LogService()

# Initialize logger
logger = setup_logger(__name__)

async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin commands based on the group type."""
    try:
        # Check if chat is an admin group
        if not admin_service.is_admin_group(update.effective_chat.id):
            return
        
        # Get group type
        group_type = admin_service.get_group_type(update.effective_chat.id)
        
        # Get command
        command = update.message.text.lower()
        
        # Handle commands based on group type
        if group_type == "MANAGE":
            await handle_manage_commands(update, context, command)
        elif group_type == "REPORTS":
            await handle_report_commands(update, context, command)
        elif group_type == "LOGS":
            await handle_log_commands(update, context, command)
        elif group_type == "TRANSACTIONS":
            await handle_transaction_commands(update, context, command)
        elif group_type == "OUTAGES":
            await handle_outage_commands(update, context, command)
        elif group_type == "SELLERS":
            await handle_seller_commands(update, context, command)
        elif group_type == "BACKUPS":
            await handle_backup_commands(update, context, command)
            
    except Exception as e:
        logger.error(f"Error handling admin command: {str(e)}")
        await update.message.reply_text("❌ خطا در پردازش دستور. لطفاً دوباره تلاش کنید.")

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
    """Handle log-related commands in the LOGS group."""
    try:
        if command == "/logs":
            # Get recent logs
            logs = await log_service.get_logs(context.bot_data["db"])
            
            if not logs:
                await update.message.reply_text("📊 هیچ لاگی یافت نشد.")
                return
            
            message = "📊 لاگ‌های اخیر:\n\n"
            
            for log in logs:
                emoji = log_service.log_levels.get(log["level"], "📝")
                message += (
                    f"{emoji} {log['message']}\n"
                    f"📅 {log['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                    f"🏷️ {log['category']}\n"
                    f"🆔 {log['id']}\n\n"
                )
            
            await update.message.reply_text(message)
            
        elif command == "/logs_stats":
            # Get log statistics
            stats = await log_service.get_log_stats(context.bot_data["db"])
            
            message = (
                f"📊 آمار لاگ‌ها (۷ روز اخیر)\n\n"
                f"📅 از: {stats['start_date'].strftime('%Y-%m-%d %H:%M')}\n"
                f"📅 تا: {stats['end_date'].strftime('%Y-%m-%d %H:%M')}\n\n"
                f"📈 تعداد کل لاگ‌ها: {stats['total_logs']}\n\n"
                f"📊 لاگ‌ها بر اساس سطح:\n"
            )
            
            for level, count in stats["logs_by_level"].items():
                emoji = log_service.log_levels.get(level, "📝")
                message += f"{emoji} {level}: {count}\n"
            
            message += "\n📊 لاگ‌ها بر اساس دسته‌بندی:\n"
            
            for category, count in stats["logs_by_category"].items():
                message += f"• {category}: {count}\n"
            
            message += "\n📊 لاگ‌ها بر اساس سرور:\n"
            
            for server_id, count in stats["logs_by_server"].items():
                message += f"• سرور {server_id}: {count}\n"
            
            await update.message.reply_text(message)
            
        elif command.startswith("/logs_user "):
            # Get user activity logs
            try:
                user_id = int(command.split()[1])
                activity = await log_service.get_user_activity_logs(context.bot_data["db"], user_id)
                
                message = (
                    f"👤 فعالیت کاربر\n\n"
                    f"🆔 شناسه: {activity['user']['id']}\n"
                    f"👤 نام کاربری: @{activity['user']['username']}\n"
                    f"📱 شماره تماس: {activity['user']['phone_number']}\n"
                    f"📅 تاریخ عضویت: {activity['user']['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"📊 لاگ‌های سیستم:\n"
                )
                
                for log in activity["system_logs"]:
                    emoji = log_service.log_levels.get(log["level"], "📝")
                    message += (
                        f"{emoji} {log['message']}\n"
                        f"📅 {log['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                        f"🏷️ {log['category']}\n\n"
                    )
                
                message += "\n🛍️ سفارش‌ها:\n"
                
                for order in activity["orders"]:
                    message += (
                        f"🆔 {order['id']}\n"
                        f"💰 {order['amount']:,} تومان\n"
                        f"✅ {order['status']}\n"
                        f"📅 {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
                    )
                
                message += "\n💳 تراکنش‌ها:\n"
                
                for transaction in activity["transactions"]:
                    message += (
                        f"🆔 {transaction['id']}\n"
                        f"💰 {transaction['amount']:,} تومان\n"
                        f"✅ {transaction['status']}\n"
                        f"📅 {transaction['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
                    )
                
                await update.message.reply_text(message)
                
            except (IndexError, ValueError):
                await update.message.reply_text("❌ لطفاً شناسه کاربر را به درستی وارد کنید.")
                
        elif command.startswith("/logs_server "):
            # Get server logs
            try:
                server_id = int(command.split()[1])
                logs = await log_service.get_server_logs(context.bot_data["db"], server_id)
                
                message = (
                    f"🖥️ لاگ‌های سرور\n\n"
                    f"🆔 شناسه: {logs['server']['id']}\n"
                    f"📝 نام: {logs['server']['name']}\n"
                    f"🌐 IP: {logs['server']['ip']}\n"
                    f"✅ وضعیت: {logs['server']['status']}\n\n"
                    f"📊 لاگ‌ها:\n"
                )
                
                for log in logs["logs"]:
                    emoji = log_service.log_levels.get(log["level"], "📝")
                    message += (
                        f"{emoji} {log['message']}\n"
                        f"📅 {log['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                        f"🏷️ {log['category']}\n\n"
                    )
                
                await update.message.reply_text(message)
                
            except (IndexError, ValueError):
                await update.message.reply_text("❌ لطفاً شناسه سرور را به درستی وارد کنید.")
                
    except Exception as e:
        logger.error(f"Error handling log commands: {str(e)}")
        await update.message.reply_text("❌ خطا در پردازش دستور. لطفاً دوباره تلاش کنید.")

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
        stats = await seller_service.get_seller_stats(context.bot_data["db"])
        
        message = (
            f"📊 آمار فروشندگان (۳۰ روز اخیر)\n\n"
            f"👥 تعداد کل فروشندگان: {stats['total_sellers']}\n"
            f"✅ فروشندگان فعال: {stats['active_sellers']}\n"
            f"💰 مجموع فروش: {stats['total_amount']:,} تومان\n"
            f"💵 مجموع کمیسیون: {stats['total_commission']:,} تومان\n\n"
            f"🏆 برترین فروشندگان:\n"
        )
        
        for i, seller in enumerate(stats["top_sellers"], 1):
            message += (
                f"{i}. @{seller['username']}\n"
                f"   📱 {seller['phone_number']}\n"
                f"   💰 {seller['total_amount']:,} تومان\n"
                f"   💵 {seller['total_commission']:,} تومان\n\n"
            )
        
        await update.effective_message.reply_text(message)
        
    elif command.startswith("/seller "):
        # Get seller details
        try:
            seller_id = int(command.split()[1])
            details = await seller_service.get_seller_details(seller_id, context.bot_data["db"])
            
            message = (
                f"👤 اطلاعات فروشنده\n\n"
                f"🆔 شناسه: {details['seller_id']}\n"
                f"👤 نام کاربری: @{details['username']}\n"
                f"📱 شماره تماس: {details['phone_number']}\n"
                f"📅 تاریخ عضویت: {details['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
                f"📊 آمار فروش (۳۰ روز اخیر):\n"
                f"💰 مجموع فروش: {details['total_amount']:,} تومان\n"
                f"💵 مجموع کمیسیون: {details['total_commission']:,} تومان\n\n"
                f"🔄 آخرین فروش‌ها:\n"
            )
            
            for sale in details["recent_sales"]:
                message += (
                    f"🆔 {sale['id']}\n"
                    f"💰 {sale['amount']:,} تومان\n"
                    f"💵 {sale['commission']:,} تومان\n"
                    f"📅 {sale['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                    f"✅ {sale['status']}\n\n"
                )
            
            await update.effective_message.reply_text(message)
            
        except (IndexError, ValueError):
            await update.effective_message.reply_text("❌ لطفاً شناسه فروشنده را به درستی وارد کنید.")
            
    elif command.startswith("/seller_balance "):
        # Get seller balance
        try:
            seller_id = int(command.split()[1])
            balance = await seller_service.get_seller_balance(seller_id, context.bot_data["db"])
            
            message = (
                f"💰 وضعیت حساب فروشنده\n\n"
                f"👤 نام کاربری: @{balance['username']}\n"
                f"📱 شماره تماس: {balance['phone_number']}\n\n"
                f"💵 کمیسیون در انتظار پرداخت: {balance['pending_commission']:,} تومان\n"
                f"✅ کمیسیون پرداخت شده: {balance['paid_commission']:,} تومان\n"
                f"💰 مجموع کمیسیون: {balance['total_commission']:,} تومان"
            )
            
            # Add payment button if there are pending commissions
            if balance["pending_commission"] > 0:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✅ ثبت پرداخت",
                            callback_data=f"pay_commission_{seller_id}"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.effective_message.reply_text(message, reply_markup=reply_markup)
            else:
                await update.effective_message.reply_text(message)
                
        except (IndexError, ValueError):
            await update.effective_message.reply_text("❌ لطفاً شناسه فروشنده را به درستی وارد کنید.")
            
    elif command.startswith("/pay_commission "):
        # Mark commission as paid
        try:
            seller_id = int(command.split()[1])
            result = await seller_service.mark_commission_paid(seller_id, context.bot_data["db"])
            
            message = (
                f"✅ ثبت پرداخت کمیسیون\n\n"
                f"👤 نام کاربری: @{result['username']}\n"
                f"📱 شماره تماس: {result['phone_number']}\n"
                f"💰 تعداد تراکنش‌های بروزرسانی شده: {result['updated_count']}\n"
                f"📅 تاریخ و ساعت: {result['timestamp'].strftime('%Y-%m-%d %H:%M')}"
            )
            
            await update.effective_message.reply_text(message)
            
        except (IndexError, ValueError):
            await update.effective_message.reply_text("❌ لطفاً شناسه فروشنده را به درستی وارد کنید.")

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