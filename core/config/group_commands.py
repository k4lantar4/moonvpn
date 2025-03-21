"""
Group-specific command handlers for MoonVPN Telegram Bot.

This module implements command handlers specific to each admin group type,
providing specialized functionality for different administrative tasks.
"""

from typing import List, Dict, Any
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from app.core.database.models.admin import AdminGroupType
from app.bot.services.admin_service import AdminService
from app.bot.services.admin_analytics_service import AdminAnalyticsService
from app.bot.utils.decorators import admin_required, group_type_required
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class GroupCommandHandler:
    """Handler for group-specific admin commands."""
    
    def __init__(self, admin_service: AdminService, analytics_service: AdminAnalyticsService):
        """Initialize the group command handler.
        
        Args:
            admin_service: Admin service instance
            analytics_service: Analytics service instance
        """
        self.admin_service = admin_service
        self.analytics_service = analytics_service
    
    @admin_required
    @group_type_required(AdminGroupType.MANAGE)
    async def handle_manage_commands(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle commands for the management group.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not update.message or not update.message.text:
            return
            
        command = update.message.text.lower()
        
        if command == "/server_status":
            await self._handle_server_status(update, context)
        elif command == "/system_health":
            await self._handle_system_health(update, context)
        elif command == "/admin_stats":
            await self._handle_admin_stats(update, context)
        else:
            await update.message.reply_text(
                "❌ Unknown command. Available commands:\n"
                "/server_status - Check server status\n"
                "/system_health - Check system health\n"
                "/admin_stats - View admin statistics"
            )
    
    @admin_required
    @group_type_required(AdminGroupType.REPORTS)
    async def handle_report_commands(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle commands for the reports group.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not update.message or not update.message.text:
            return
            
        command = update.message.text.lower()
        
        if command == "/daily_report":
            await self._handle_daily_report(update, context)
        elif command == "/performance_report":
            await self._handle_performance_report(update, context)
        elif command == "/usage_report":
            await self._handle_usage_report(update, context)
        else:
            await update.message.reply_text(
                "❌ Unknown command. Available commands:\n"
                "/daily_report - Get daily system report\n"
                "/performance_report - Get performance metrics\n"
                "/usage_report - Get usage statistics"
            )
    
    @admin_required
    @group_type_required(AdminGroupType.LOGS)
    async def handle_log_commands(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle commands for the logs group.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not update.message or not update.message.text:
            return
            
        command = update.message.text.lower()
        
        if command == "/error_logs":
            await self._handle_error_logs(update, context)
        elif command == "/user_logs":
            await self._handle_user_logs(update, context)
        elif command == "/system_logs":
            await self._handle_system_logs(update, context)
        else:
            await update.message.reply_text(
                "❌ Unknown command. Available commands:\n"
                "/error_logs - View error logs\n"
                "/user_logs - View user activity logs\n"
                "/system_logs - View system event logs"
            )
    
    @admin_required
    @group_type_required(AdminGroupType.TRANSACTIONS)
    async def handle_transaction_commands(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle commands for the transactions group.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not update.message or not update.message.text:
            return
            
        command = update.message.text.lower()
        
        if command == "/transaction_stats":
            await self._handle_transaction_stats(update, context)
        elif command == "/payment_report":
            await self._handle_payment_report(update, context)
        elif command == "/refund_requests":
            await self._handle_refund_requests(update, context)
        else:
            await update.message.reply_text(
                "❌ Unknown command. Available commands:\n"
                "/transaction_stats - View transaction statistics\n"
                "/payment_report - Get payment processing report\n"
                "/refund_requests - View refund requests"
            )
    
    @admin_required
    @group_type_required(AdminGroupType.OUTAGES)
    async def handle_outage_commands(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle commands for the outages group.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not update.message or not update.message.text:
            return
            
        command = update.message.text.lower()
        
        if command == "/outage_status":
            await self._handle_outage_status(update, context)
        elif command == "/maintenance_schedule":
            await self._handle_maintenance_schedule(update, context)
        elif command == "/incident_report":
            await self._handle_incident_report(update, context)
        else:
            await update.message.reply_text(
                "❌ Unknown command. Available commands:\n"
                "/outage_status - Check current outage status\n"
                "/maintenance_schedule - View maintenance schedule\n"
                "/incident_report - Get incident report"
            )
    
    @admin_required
    @group_type_required(AdminGroupType.SELLERS)
    async def handle_seller_commands(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle commands for the sellers group.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not update.message or not update.message.text:
            return
            
        command = update.message.text.lower()
        
        if command == "/seller_stats":
            await self._handle_seller_stats(update, context)
        elif command == "/commission_report":
            await self._handle_commission_report(update, context)
        elif command == "/partner_status":
            await self._handle_partner_status(update, context)
        else:
            await update.message.reply_text(
                "❌ Unknown command. Available commands:\n"
                "/seller_stats - View seller statistics\n"
                "/commission_report - Get commission report\n"
                "/partner_status - Check partner status"
            )
    
    @admin_required
    @group_type_required(AdminGroupType.BACKUPS)
    async def handle_backup_commands(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle commands for the backups group.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not update.message or not update.message.text:
            return
            
        command = update.message.text.lower()
        
        if command == "/backup_status":
            await self._handle_backup_status(update, context)
        elif command == "/backup_schedule":
            await self._handle_backup_schedule(update, context)
        elif command == "/restore_points":
            await self._handle_restore_points(update, context)
        else:
            await update.message.reply_text(
                "❌ Unknown command. Available commands:\n"
                "/backup_status - Check backup status\n"
                "/backup_schedule - View backup schedule\n"
                "/restore_points - List restore points"
            )
    
    async def _handle_server_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle server status command."""
        try:
            status = await self.admin_service.get_current_server_status()
            message = (
                "🖥️ Server Status:\n\n"
                f"CPU Usage: {status['cpu_usage']}%\n"
                f"Memory Usage: {status['memory_usage']}%\n"
                f"Disk Usage: {status['disk_usage']}%\n"
                f"Network Status: {status['network_status']}\n"
                f"Uptime: {status['uptime']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling server status: {str(e)}")
            await update.message.reply_text("❌ Failed to get server status")
    
    async def _handle_system_health(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle system health command."""
        try:
            health = await self.admin_service.get_system_health()
            message = (
                "🏥 System Health:\n\n"
                f"Status: {health['status']}\n"
                f"Database: {health['database_status']}\n"
                f"API: {health['api_status']}\n"
                f"Bot: {health['bot_status']}\n"
                f"Last Check: {health['last_check']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling system health: {str(e)}")
            await update.message.reply_text("❌ Failed to get system health")
    
    async def _handle_admin_stats(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle admin statistics command."""
        try:
            stats = await self.admin_service.get_admin_statistics()
            message = (
                "👥 Admin Statistics:\n\n"
                f"Total Admins: {stats['total_admins']}\n"
                f"Active Admins: {stats['active_admins']}\n"
                f"Admin Actions: {stats['admin_actions']}\n"
                f"Last Update: {stats['last_update']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling admin stats: {str(e)}")
            await update.message.reply_text("❌ Failed to get admin statistics")
    
    async def _handle_daily_report(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle daily report command."""
        try:
            report = await self.admin_service.get_daily_report()
            message = (
                "📊 Daily Report:\n\n"
                f"Date: {report['date']}\n"
                f"New Users: {report['new_users']}\n"
                f"Active Users: {report['active_users']}\n"
                f"Total Revenue: ${report['total_revenue']}\n"
                f"System Uptime: {report['system_uptime']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling daily report: {str(e)}")
            await update.message.reply_text("❌ Failed to get daily report")
    
    async def _handle_performance_report(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle performance report command."""
        try:
            report = await self.admin_service.get_performance_report()
            message = (
                "⚡ Performance Report:\n\n"
                f"Response Time: {report['response_time']}ms\n"
                f"Error Rate: {report['error_rate']}%\n"
                f"CPU Usage: {report['cpu_usage']}%\n"
                f"Memory Usage: {report['memory_usage']}%\n"
                f"Network Load: {report['network_load']}%"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling performance report: {str(e)}")
            await update.message.reply_text("❌ Failed to get performance report")
    
    async def _handle_usage_report(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle usage report command."""
        try:
            report = await self.admin_service.get_usage_report()
            message = (
                "📈 Usage Report:\n\n"
                f"Total Users: {report['total_users']}\n"
                f"Active Sessions: {report['active_sessions']}\n"
                f"Bandwidth Usage: {report['bandwidth_usage']}\n"
                f"Peak Hours: {report['peak_hours']}\n"
                f"Avg Session: {report['avg_session']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling usage report: {str(e)}")
            await update.message.reply_text("❌ Failed to get usage report")
    
    async def _handle_error_logs(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle error logs command."""
        try:
            logs = await self.admin_service.get_error_logs()
            if not logs:
                await update.message.reply_text("✅ No error logs found")
                return
                
            message = "⚠️ Recent Error Logs:\n\n"
            for log in logs[:5]:  # Show last 5 errors
                message += f"• {log['timestamp']}: {log['message']}\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling error logs: {str(e)}")
            await update.message.reply_text("❌ Failed to get error logs")
    
    async def _handle_user_logs(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle user logs command."""
        try:
            logs = await self.admin_service.get_user_logs()
            if not logs:
                await update.message.reply_text("✅ No user logs found")
                return
                
            message = "👤 Recent User Activity:\n\n"
            for log in logs[:5]:  # Show last 5 activities
                message += f"• {log['timestamp']}: {log['user']} - {log['action']}\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling user logs: {str(e)}")
            await update.message.reply_text("❌ Failed to get user logs")
    
    async def _handle_system_logs(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle system logs command."""
        try:
            logs = await self.admin_service.get_system_logs()
            if not logs:
                await update.message.reply_text("✅ No system logs found")
                return
                
            message = "🔄 Recent System Events:\n\n"
            for log in logs[:5]:  # Show last 5 events
                message += f"• {log['timestamp']}: {log['event']}\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling system logs: {str(e)}")
            await update.message.reply_text("❌ Failed to get system logs")
    
    async def _handle_transaction_stats(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle transaction statistics command."""
        try:
            stats = await self.admin_service.get_transaction_statistics()
            message = (
                "💰 Transaction Statistics:\n\n"
                f"Total Transactions: {stats['total_transactions']}\n"
                f"Total Revenue: ${stats['total_revenue']}\n"
                f"Success Rate: {stats['success_rate']}%\n"
                f"Average Amount: ${stats['avg_amount']}\n"
                f"Last Update: {stats['last_update']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling transaction stats: {str(e)}")
            await update.message.reply_text("❌ Failed to get transaction statistics")
    
    async def _handle_payment_report(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle payment report command."""
        try:
            report = await self.admin_service.get_payment_report()
            message = (
                "💳 Payment Report:\n\n"
                f"Total Payments: {report['total_payments']}\n"
                f"Total Amount: ${report['total_amount']}\n"
                f"Success Rate: {report['success_rate']}%\n"
                f"Last Update: {report['last_update']}\n\n"
                "Payment Methods:\n"
            )
            
            for method in report['payment_methods']:
                message += f"• {method}\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling payment report: {str(e)}")
            await update.message.reply_text("❌ Failed to get payment report")
    
    async def _handle_refund_requests(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle refund requests command."""
        try:
            requests = await self.admin_service.get_refund_requests()
            if not requests:
                await update.message.reply_text("✅ No pending refund requests")
                return
                
            message = "🔄 Pending Refund Requests:\n\n"
            for req in requests[:5]:  # Show last 5 requests
                message += (
                    f"• ID: {req['id']}\n"
                    f"  User: {req['user']}\n"
                    f"  Amount: ${req['amount']}\n"
                    f"  Status: {req['status']}\n"
                    f"  Date: {req['date']}\n\n"
                )
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling refund requests: {str(e)}")
            await update.message.reply_text("❌ Failed to get refund requests")
    
    async def _handle_outage_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle outage status command."""
        try:
            status = await self.admin_service.get_outage_status()
            message = (
                "⚠️ Outage Status:\n\n"
                f"Current Status: {status['current_status']}\n"
                f"Impact Level: {status['impact_level']}\n"
                f"Start Time: {status['start_time'] or 'N/A'}\n"
                f"Estimated Resolution: {status['estimated_resolution'] or 'N/A'}\n\n"
                "Affected Services:\n"
            )
            
            if status['affected_services']:
                for service in status['affected_services']:
                    message += f"• {service}\n"
            else:
                message += "No services affected\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling outage status: {str(e)}")
            await update.message.reply_text("❌ Failed to get outage status")
    
    async def _handle_maintenance_schedule(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle maintenance schedule command."""
        try:
            schedule = await self.admin_service.get_maintenance_schedule()
            if not schedule:
                await update.message.reply_text("✅ No scheduled maintenance")
                return
                
            message = "🔧 Maintenance Schedule:\n\n"
            for window in schedule[:5]:  # Show next 5 windows
                message += (
                    f"• Start: {window['start_time']}\n"
                    f"  End: {window['end_time']}\n"
                    f"  Type: {window['type']}\n"
                    f"  Impact: {window['impact']}\n\n"
                )
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling maintenance schedule: {str(e)}")
            await update.message.reply_text("❌ Failed to get maintenance schedule")
    
    async def _handle_incident_report(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle incident report command."""
        try:
            report = await self.admin_service.get_incident_report()
            message = (
                "🚨 Incident Report:\n\n"
                f"Total Incidents: {report['total_incidents']}\n"
                f"Resolved: {report['resolved']}\n"
                f"Active: {report['active']}\n"
                f"Avg Resolution Time: {report['avg_resolution_time']}\n"
                f"Last Update: {report['last_update']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling incident report: {str(e)}")
            await update.message.reply_text("❌ Failed to get incident report")
    
    async def _handle_seller_stats(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle seller statistics command."""
        try:
            stats = await self.admin_service.get_seller_statistics()
            message = (
                "👥 Seller Statistics:\n\n"
                f"Total Sellers: {stats['total_sellers']}\n"
                f"Active Sellers: {stats['active_sellers']}\n"
                f"Total Sales: {stats['total_sales']}\n"
                f"Total Commission: ${stats['total_commission']}\n"
                f"Last Update: {stats['last_update']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling seller stats: {str(e)}")
            await update.message.reply_text("❌ Failed to get seller statistics")
    
    async def _handle_commission_report(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle commission report command."""
        try:
            report = await self.admin_service.get_commission_report()
            message = (
                "💰 Commission Report:\n\n"
                f"Total Commission: ${report['total_commission']}\n"
                f"Paid Commission: ${report['paid_commission']}\n"
                f"Pending Commission: ${report['pending_commission']}\n"
                f"Commission Rate: {report['commission_rate']}%\n"
                f"Last Update: {report['last_update']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling commission report: {str(e)}")
            await update.message.reply_text("❌ Failed to get commission report")
    
    async def _handle_partner_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle partner status command."""
        try:
            partners = await self.admin_service.get_partner_status()
            if not partners:
                await update.message.reply_text("✅ No active partners")
                return
                
            message = "🤝 Partner Status:\n\n"
            for partner in partners[:5]:  # Show last 5 partners
                message += (
                    f"• Name: {partner['name']}\n"
                    f"  Status: {partner['status']}\n"
                    f"  Sales: {partner['sales']}\n"
                    f"  Commission: ${partner['commission']}\n\n"
                )
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling partner status: {str(e)}")
            await update.message.reply_text("❌ Failed to get partner status")
    
    async def _handle_backup_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle backup status command."""
        try:
            status = await self.admin_service.get_backup_status()
            message = (
                "💾 Backup Status:\n\n"
                f"Last Backup: {status['last_backup'] or 'Never'}\n"
                f"Backup Size: {status['backup_size']}\n"
                f"Status: {status['status']}\n"
                f"Next Backup: {status['next_backup'] or 'Not scheduled'}\n"
                f"Storage Used: {status['storage_used']}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling backup status: {str(e)}")
            await update.message.reply_text("❌ Failed to get backup status")
    
    async def _handle_backup_schedule(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle backup schedule command."""
        try:
            schedule = await self.admin_service.get_backup_schedule()
            if not schedule:
                await update.message.reply_text("✅ No backup schedule configured")
                return
                
            message = "📅 Backup Schedule:\n\n"
            for backup in schedule[:5]:  # Show next 5 backups
                message += (
                    f"• Time: {backup['time']}\n"
                    f"  Type: {backup['type']}\n"
                    f"  Retention: {backup['retention']}\n"
                    f"  Status: {backup['status']}\n\n"
                )
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling backup schedule: {str(e)}")
            await update.message.reply_text("❌ Failed to get backup schedule")
    
    async def _handle_restore_points(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle restore points command."""
        try:
            points = await self.admin_service.get_restore_points()
            if not points:
                await update.message.reply_text("✅ No restore points available")
                return
                
            message = "🔄 Available Restore Points:\n\n"
            for point in points[:5]:  # Show last 5 points
                message += (
                    f"• Date: {point['date']}\n"
                    f"  Size: {point['size']}\n"
                    f"  Type: {point['type']}\n"
                    f"  Status: {point['status']}\n\n"
                )
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error handling restore points: {str(e)}")
            await update.message.reply_text("❌ Failed to get restore points")
    
    def get_handlers(self) -> List[Dict[str, Any]]:
        """Get command handlers for registration.
        
        Returns:
            List of command handlers
        """
        return [
            {
                "command": "server_status",
                "callback": self._handle_server_status,
                "group_type": AdminGroupType.MANAGE
            },
            {
                "command": "system_health",
                "callback": self._handle_system_health,
                "group_type": AdminGroupType.MANAGE
            },
            {
                "command": "admin_stats",
                "callback": self._handle_admin_stats,
                "group_type": AdminGroupType.MANAGE
            },
            {
                "command": "daily_report",
                "callback": self._handle_daily_report,
                "group_type": AdminGroupType.REPORTS
            },
            {
                "command": "performance_report",
                "callback": self._handle_performance_report,
                "group_type": AdminGroupType.REPORTS
            },
            {
                "command": "usage_report",
                "callback": self._handle_usage_report,
                "group_type": AdminGroupType.REPORTS
            },
            {
                "command": "error_logs",
                "callback": self._handle_error_logs,
                "group_type": AdminGroupType.LOGS
            },
            {
                "command": "user_logs",
                "callback": self._handle_user_logs,
                "group_type": AdminGroupType.LOGS
            },
            {
                "command": "system_logs",
                "callback": self._handle_system_logs,
                "group_type": AdminGroupType.LOGS
            },
            {
                "command": "transaction_stats",
                "callback": self._handle_transaction_stats,
                "group_type": AdminGroupType.TRANSACTIONS
            },
            {
                "command": "payment_report",
                "callback": self._handle_payment_report,
                "group_type": AdminGroupType.TRANSACTIONS
            },
            {
                "command": "refund_requests",
                "callback": self._handle_refund_requests,
                "group_type": AdminGroupType.TRANSACTIONS
            },
            {
                "command": "outage_status",
                "callback": self._handle_outage_status,
                "group_type": AdminGroupType.OUTAGES
            },
            {
                "command": "maintenance_schedule",
                "callback": self._handle_maintenance_schedule,
                "group_type": AdminGroupType.OUTAGES
            },
            {
                "command": "incident_report",
                "callback": self._handle_incident_report,
                "group_type": AdminGroupType.OUTAGES
            },
            {
                "command": "seller_stats",
                "callback": self._handle_seller_stats,
                "group_type": AdminGroupType.SELLERS
            },
            {
                "command": "commission_report",
                "callback": self._handle_commission_report,
                "group_type": AdminGroupType.SELLERS
            },
            {
                "command": "partner_status",
                "callback": self._handle_partner_status,
                "group_type": AdminGroupType.SELLERS
            },
            {
                "command": "backup_status",
                "callback": self._handle_backup_status,
                "group_type": AdminGroupType.BACKUPS
            },
            {
                "command": "backup_schedule",
                "callback": self._handle_backup_schedule,
                "group_type": AdminGroupType.BACKUPS
            },
            {
                "command": "restore_points",
                "callback": self._handle_restore_points,
                "group_type": AdminGroupType.BACKUPS
            }
        ] 