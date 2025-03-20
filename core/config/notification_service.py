"""
Notification service for MoonVPN Telegram Bot.

This module provides services for sending notifications to admin groups.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from telegram import Bot
from telegram.constants import ParseMode

from app.core.database.models.admin import AdminGroup, AdminGroupType, NotificationLevel
from app.bot.services.admin_group_service import AdminGroupService

class NotificationService:
    """Service for sending notifications to admin groups."""
    
    def __init__(self, db: Session, bot: Bot):
        """Initialize the notification service.
        
        Args:
            db: Database session
            bot: Telegram bot instance
        """
        self.db = db
        self.bot = bot
        self.admin_service = AdminGroupService(db)
    
    async def send_notification(
        self,
        message: str,
        notification_type: str,
        level: NotificationLevel = NotificationLevel.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send a notification to relevant admin groups.
        
        Args:
            message: Notification message
            notification_type: Type of notification
            level: Importance level of the notification
            data: Additional data for the notification
            target_groups: Specific groups to notify (if None, notify all groups)
        """
        try:
            # Get all active admin groups
            groups = self.admin_service.db.query(AdminGroup).filter(
                AdminGroup.is_active == True
            ).all()
            
            # Filter groups by target groups if specified
            if target_groups:
                groups = [g for g in groups if g.type in target_groups]
            
            # Filter groups by notification level
            groups = [g for g in groups if g.notification_level.value >= level.value]
            
            # Filter groups by notification type
            groups = [g for g in groups if notification_type in g.notification_types]
            
            # Format the message
            formatted_message = self._format_notification(
                message=message,
                notification_type=notification_type,
                level=level,
                data=data
            )
            
            # Send to each group
            for group in groups:
                try:
                    await self.bot.send_message(
                        chat_id=group.chat_id,
                        text=formatted_message,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    # Log the error but continue with other groups
                    print(f"Failed to send notification to group {group.name}: {str(e)}")
                    
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
    
    def _format_notification(
        self,
        message: str,
        notification_type: str,
        level: NotificationLevel,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a notification message.
        
        Args:
            message: Notification message
            notification_type: Type of notification
            level: Importance level
            data: Additional data
            
        Returns:
            Formatted notification message
        """
        # Get level emoji
        level_emoji = {
            NotificationLevel.LOW: "📝",
            NotificationLevel.NORMAL: "📢",
            NotificationLevel.HIGH: "⚠️"
        }.get(level, "📢")
        
        # Format the message
        formatted = f"{level_emoji} <b>{notification_type.title()}</b>\n\n"
        formatted += f"{message}\n\n"
        
        # Add timestamp
        formatted += f"<i>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        # Add data if provided
        if data:
            formatted += "\n\n<b>Additional Data:</b>\n"
            for key, value in data.items():
                formatted += f"• {key}: {value}\n"
        
        return formatted
    
    async def send_system_status(
        self,
        status: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send system status notification.
        
        Args:
            status: System status data
            target_groups: Specific groups to notify
        """
        message = (
            "🖥️ <b>System Status Update</b>\n\n"
            f"CPU Usage: {status.get('cpu_usage', 'N/A')}%\n"
            f"Memory Usage: {status.get('memory_usage', 'N/A')}%\n"
            f"Disk Usage: {status.get('disk_usage', 'N/A')}%\n"
            f"Network Status: {status.get('network_status', 'N/A')}\n"
            f"Uptime: {status.get('uptime', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="system_status",
            level=NotificationLevel.NORMAL,
            target_groups=target_groups or [AdminGroupType.MANAGE, AdminGroupType.REPORTS]
        )
    
    async def send_error_notification(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send error notification.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
            target_groups: Specific groups to notify
        """
        message = (
            "❌ <b>Error Occurred</b>\n\n"
            f"Error Type: {type(error).__name__}\n"
            f"Message: {str(error)}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="error",
            level=NotificationLevel.HIGH,
            data=context,
            target_groups=target_groups or [AdminGroupType.MANAGE, AdminGroupType.LOGS]
        )
    
    async def send_user_activity(
        self,
        activity: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send user activity notification.
        
        Args:
            activity: User activity data
            target_groups: Specific groups to notify
        """
        message = (
            "👤 <b>User Activity</b>\n\n"
            f"User: {activity.get('username', 'N/A')}\n"
            f"Action: {activity.get('action', 'N/A')}\n"
            f"Details: {activity.get('details', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="user_activity",
            level=NotificationLevel.LOW,
            data=activity,
            target_groups=target_groups or [AdminGroupType.LOGS]
        )
    
    async def send_transaction_notification(
        self,
        transaction: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send transaction notification.
        
        Args:
            transaction: Transaction data
            target_groups: Specific groups to notify
        """
        message = (
            "💰 <b>New Transaction</b>\n\n"
            f"User: {transaction.get('username', 'N/A')}\n"
            f"Amount: {transaction.get('amount', 'N/A')}\n"
            f"Type: {transaction.get('type', 'N/A')}\n"
            f"Status: {transaction.get('status', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="transaction",
            level=NotificationLevel.NORMAL,
            data=transaction,
            target_groups=target_groups or [AdminGroupType.TRANSACTIONS]
        )
    
    async def send_service_outage(
        self,
        outage: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send service outage notification.
        
        Args:
            outage: Outage data
            target_groups: Specific groups to notify
        """
        message = (
            "🚫 <b>Service Outage</b>\n\n"
            f"Service: {outage.get('service', 'N/A')}\n"
            f"Status: {outage.get('status', 'N/A')}\n"
            f"Impact: {outage.get('impact', 'N/A')}\n"
            f"Details: {outage.get('details', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="outage",
            level=NotificationLevel.HIGH,
            data=outage,
            target_groups=target_groups or [AdminGroupType.OUTAGES, AdminGroupType.MANAGE]
        )
    
    async def send_backup_notification(
        self,
        backup: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send backup status notification.
        
        Args:
            backup: Backup data
            target_groups: Specific groups to notify
        """
        message = (
            "💾 <b>Backup Status</b>\n\n"
            f"Type: {backup.get('type', 'N/A')}\n"
            f"Status: {backup.get('status', 'N/A')}\n"
            f"Size: {backup.get('size', 'N/A')}\n"
            f"Duration: {backup.get('duration', 'N/A')}\n"
            f"Location: {backup.get('location', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="backup",
            level=NotificationLevel.NORMAL,
            data=backup,
            target_groups=target_groups or [AdminGroupType.BACKUPS]
        )
    
    async def send_security_alert(
        self,
        alert: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send security alert notification.
        
        Args:
            alert: Security alert data
            target_groups: Specific groups to notify
        """
        message = (
            "🚨 <b>Security Alert</b>\n\n"
            f"Type: {alert.get('type', 'N/A')}\n"
            f"Severity: {alert.get('severity', 'N/A')}\n"
            f"Source: {alert.get('source', 'N/A')}\n"
            f"Details: {alert.get('details', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="security",
            level=NotificationLevel.HIGH,
            data=alert,
            target_groups=target_groups or [AdminGroupType.MANAGE]
        )
    
    async def send_performance_alert(
        self,
        alert: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send performance alert notification.
        
        Args:
            alert: Performance alert data
            target_groups: Specific groups to notify
        """
        message = (
            "⚡ <b>Performance Alert</b>\n\n"
            f"Component: {alert.get('component', 'N/A')}\n"
            f"Metric: {alert.get('metric', 'N/A')}\n"
            f"Current Value: {alert.get('value', 'N/A')}\n"
            f"Threshold: {alert.get('threshold', 'N/A')}\n"
            f"Impact: {alert.get('impact', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="performance",
            level=NotificationLevel.HIGH,
            data=alert,
            target_groups=target_groups or [AdminGroupType.MANAGE, AdminGroupType.REPORTS]
        )
    
    async def send_reseller_notification(
        self,
        data: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send reseller-related notification.
        
        Args:
            data: Reseller notification data
            target_groups: Specific groups to notify
        """
        message = (
            "👥 <b>Reseller Update</b>\n\n"
            f"Reseller: {data.get('reseller', 'N/A')}\n"
            f"Action: {data.get('action', 'N/A')}\n"
            f"Details: {data.get('details', 'N/A')}\n"
            f"Status: {data.get('status', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="reseller",
            level=NotificationLevel.NORMAL,
            data=data,
            target_groups=target_groups or [AdminGroupType.SELLERS]
        )
    
    async def send_subscription_notification(
        self,
        data: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send subscription-related notification.
        
        Args:
            data: Subscription notification data
            target_groups: Specific groups to notify
        """
        message = (
            "📅 <b>Subscription Update</b>\n\n"
            f"User: {data.get('username', 'N/A')}\n"
            f"Plan: {data.get('plan', 'N/A')}\n"
            f"Action: {data.get('action', 'N/A')}\n"
            f"Status: {data.get('status', 'N/A')}\n"
            f"Next Billing: {data.get('next_billing', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="subscription",
            level=NotificationLevel.NORMAL,
            data=data,
            target_groups=target_groups or [AdminGroupType.TRANSACTIONS]
        )
    
    async def send_support_notification(
        self,
        data: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send support-related notification.
        
        Args:
            data: Support notification data
            target_groups: Specific groups to notify
        """
        message = (
            "🎯 <b>Support Request</b>\n\n"
            f"User: {data.get('username', 'N/A')}\n"
            f"Type: {data.get('type', 'N/A')}\n"
            f"Priority: {data.get('priority', 'N/A')}\n"
            f"Status: {data.get('status', 'N/A')}\n"
            f"Details: {data.get('details', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="support",
            level=NotificationLevel.NORMAL,
            data=data,
            target_groups=target_groups or [AdminGroupType.MANAGE]
        )
    
    async def send_maintenance_notification(
        self,
        data: Dict[str, Any],
        target_groups: Optional[List[AdminGroupType]] = None
    ) -> None:
        """Send maintenance-related notification.
        
        Args:
            data: Maintenance notification data
            target_groups: Specific groups to notify
        """
        message = (
            "🔧 <b>Maintenance Update</b>\n\n"
            f"Type: {data.get('type', 'N/A')}\n"
            f"Component: {data.get('component', 'N/A')}\n"
            f"Status: {data.get('status', 'N/A')}\n"
            f"Impact: {data.get('impact', 'N/A')}\n"
            f"Duration: {data.get('duration', 'N/A')}\n"
            f"Details: {data.get('details', 'N/A')}"
        )
        
        await self.send_notification(
            message=message,
            notification_type="maintenance",
            level=NotificationLevel.HIGH,
            data=data,
            target_groups=target_groups or [AdminGroupType.MANAGE, AdminGroupType.OUTAGES]
        ) 