"""
Monitoring handler for MoonVPN Telegram Bot.

This module handles commands for monitoring system status and health.
"""

from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from sqlalchemy.orm import Session

from app.bot.services.monitoring_service import MonitoringService
from app.bot.services.notification_service import NotificationService
from app.bot.utils.decorators import admin_required

class MonitoringHandler:
    """Handler for monitoring commands."""
    
    def __init__(self, db: Session, bot):
        """Initialize the monitoring handler.
        
        Args:
            db: Database session
            bot: Telegram bot instance
        """
        self.notification_service = NotificationService(db, bot)
        self.monitoring_service = MonitoringService(db, self.notification_service)
    
    async def handle_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /status command.
        
        Usage: /status
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            # Get system status
            status = self.monitoring_service._get_system_status()
            
            # Format the message
            message = (
                "🖥️ <b>System Status</b>\n\n"
                f"CPU Usage: {status['cpu_usage']}%\n"
                f"Memory Usage: {status['memory_usage']}%\n"
                f"Disk Usage: {status['disk_usage']}%\n"
                f"Uptime: {status['uptime']}\n\n"
                f"<b>Network Status:</b>\n"
                f"Bytes Sent: {status['network_status']['bytes_sent']:,}\n"
                f"Bytes Received: {status['network_status']['bytes_recv']:,}\n"
                f"Packets Sent: {status['network_status']['packets_sent']:,}\n"
                f"Packets Received: {status['network_status']['packets_recv']:,}\n\n"
                f"<b>System Information:</b>\n"
                f"OS: {status['system_info']['os']} {status['system_info']['os_release']}\n"
                f"Version: {status['system_info']['os_version']}\n"
                f"Architecture: {status['system_info']['architecture']}\n"
                f"Processor: {status['system_info']['processor']}"
            )
            
            await update.message.reply_text(
                text=message,
                parse_mode='HTML'
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Failed to get system status: {str(e)}"
            )
    
    async def handle_health(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /health command.
        
        Usage: /health
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            # Check service health
            health = await self.monitoring_service.check_service_health()
            
            # Format the message
            message = "🔍 <b>Service Health Check</b>\n\n"
            
            # Database status
            db_status = health['database']
            message += (
                f"<b>Database:</b> {db_status['status'].upper()}\n"
                f"{db_status['message']}\n\n"
            )
            
            # Network status
            network_status = health['network']
            message += (
                f"<b>Network:</b> {network_status['status'].upper()}\n"
                f"{network_status['message']}\n"
                if network_status.get('active_interfaces') else ""
                f"Active Interfaces: {', '.join(network_status['active_interfaces'])}\n\n"
            )
            
            # Disk status
            disk_status = health['disk']
            message += (
                f"<b>Disk:</b> {disk_status['status'].upper()}\n"
                f"{disk_status['message']}\n"
                f"Total: {disk_status['total']:,} bytes\n"
                f"Used: {disk_status['used']:,} bytes\n"
                f"Free: {disk_status['free']:,} bytes\n"
                f"Usage: {disk_status['percent']}%\n\n"
            )
            
            # Memory status
            memory_status = health['memory']
            message += (
                f"<b>Memory:</b> {memory_status['status'].upper()}\n"
                f"{memory_status['message']}\n"
                f"Total: {memory_status['total']:,} bytes\n"
                f"Available: {memory_status['available']:,} bytes\n"
                f"Used: {memory_status['used']:,} bytes\n"
                f"Usage: {memory_status['percent']}%\n\n"
            )
            
            # CPU status
            cpu_status = health['cpu']
            message += (
                f"<b>CPU:</b> {cpu_status['status'].upper()}\n"
                f"{cpu_status['message']}\n"
                f"Cores: {cpu_status['cores']}\n"
            )
            if cpu_status.get('frequency'):
                message += (
                    f"Current Frequency: {cpu_status['frequency']['current']:.1f} MHz\n"
                    f"Min Frequency: {cpu_status['frequency']['min']:.1f} MHz\n"
                    f"Max Frequency: {cpu_status['frequency']['max']:.1f} MHz\n"
                )
            
            await update.message.reply_text(
                text=message,
                parse_mode='HTML'
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Failed to check service health: {str(e)}"
            )
    
    async def handle_start_monitoring(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /start_monitoring command.
        
        Usage: /start_monitoring [interval]
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            # Get interval from args or use default
            interval = 300  # 5 minutes default
            if context.args:
                try:
                    interval = int(context.args[0])
                    if interval < 60:  # Minimum 1 minute
                        interval = 60
                    elif interval > 3600:  # Maximum 1 hour
                        interval = 3600
                except ValueError:
                    await update.message.reply_text(
                        "❌ Invalid interval. Please provide a number between 60 and 3600 seconds."
                    )
                    return
            
            # Start monitoring
            await self.monitoring_service.start_monitoring(interval)
            
            await update.message.reply_text(
                f"✅ Monitoring started with {interval} seconds interval!"
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Failed to start monitoring: {str(e)}"
            )
    
    async def handle_stop_monitoring(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /stop_monitoring command.
        
        Usage: /stop_monitoring
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            # Stop monitoring
            await self.monitoring_service.stop_monitoring()
            
            await update.message.reply_text("✅ Monitoring stopped!")
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Failed to stop monitoring: {str(e)}"
            )
    
    def get_handlers(self) -> list:
        """Get the command handlers for monitoring.
        
        Returns:
            List of command handlers
        """
        return [
            CommandHandler("status", self.handle_status),
            CommandHandler("health", self.handle_health),
            CommandHandler("start_monitoring", self.handle_start_monitoring),
            CommandHandler("stop_monitoring", self.handle_stop_monitoring)
        ] 