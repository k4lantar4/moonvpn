"""
Notification Service for MoonVPN Telegram Bot

This module handles sending notifications to different management
groups based on notification types.
"""

import logging
from typing import Optional, Dict, Any, Union, List
from datetime import datetime
import json
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
import asyncio

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.constants import ParseMode

from core.database.models.groups import BotManagementGroup
from core.utils.helpers import get_formatted_datetime
from core.config import settings
from core.exceptions import SecurityError

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications to management groups."""
    
    def __init__(self):
        """Initialize the notification service."""
        self._bot: Optional[Bot] = None
        self.email_config = settings.EMAIL_CONFIG
        self.webhook_config = settings.WEBHOOK_CONFIG
        self.sms_config = settings.SMS_CONFIG
        self.telegram_config = settings.TELEGRAM_CONFIG
        
    async def set_bot(self, bot: Bot) -> None:
        """Set the bot instance for sending messages.
        
        Args:
            bot: The Telegram bot instance.
        """
        self._bot = bot
        
    async def send_notification(self, 
                               notification_type: str, 
                               message: str, 
                               reply_markup: Optional[InlineKeyboardMarkup] = None,
                               parse_mode: Optional[str] = ParseMode.HTML) -> Dict[int, bool]:
        """Send notification to all active management groups of the specified type.
        
        Args:
            notification_type: Type of notification (e.g., 'PAYMENT_NOTIFICATION', 'USER_MANAGEMENT').
            message: The message to send.
            reply_markup: Optional inline keyboard markup.
            parse_mode: Parse mode for the message.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        if not self._bot:
            logger.error("Bot not set in NotificationService")
            return {}
            
        # Get all active management groups that receive this notification type
        try:
            groups = await BotManagementGroup.filter(
                is_active=True,
                notification_types__contains=notification_type
            ).all()
            
            if not groups:
                logger.warning(f"No active management groups found for notification type: {notification_type}")
                return {}
                
            # Send message to each group
            results = {}
            for group in groups:
                success = await self._send_message_to_chat(
                    chat_id=group.chat_id,
                    message=f"{group.icon} {message}",
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                results[group.chat_id] = success
                
            return results
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {}
    
    async def send_payment_notification(self, 
                                       user_data: Dict[str, Any], 
                                       payment_data: Dict[str, Any],
                                       buttons: Optional[List[List[InlineKeyboardButton]]] = None) -> Dict[int, bool]:
        """Send payment notification to management groups.
        
        Args:
            user_data: User information.
            payment_data: Payment information.
            buttons: Optional buttons to add to the message.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            "<b>پرداخت جدید</b>\n\n"
            f"👤 کاربر: {user_data.get('full_name', 'نامشخص')} (@{user_data.get('username', 'بدون نام کاربری')})\n"
            f"🆔 شناسه کاربر: <code>{user_data.get('id', 'نامشخص')}</code>\n\n"
            f"💰 مبلغ: {payment_data.get('amount', 0):,} تومان\n"
            f"🧾 شماره پیگیری: <code>{payment_data.get('transaction_id', 'نامشخص')}</code>\n"
            f"💳 روش پرداخت: {payment_data.get('payment_method', 'نامشخص')}\n"
            f"⏱ زمان: {get_formatted_datetime(payment_data.get('created_at', datetime.now()))}\n"
            f"📝 توضیحات: {payment_data.get('description', '-')}"
        )
        
        # Create reply markup if buttons provided
        reply_markup = None
        if buttons:
            reply_markup = InlineKeyboardMarkup(buttons)
            
        # Send notification
        return await self.send_notification(
            notification_type="PAYMENT_NOTIFICATION",
            message=message,
            reply_markup=reply_markup
        )
    
    async def send_user_notification(self, 
                                    user_data: Dict[str, Any], 
                                    action: str,
                                    details: Optional[str] = None) -> Dict[int, bool]:
        """Send user-related notification to management groups.
        
        Args:
            user_data: User information.
            action: Action performed (e.g., 'registered', 'updated', 'deleted').
            details: Optional additional details.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            f"<b>کاربر {action}</b>\n\n"
            f"👤 نام: {user_data.get('full_name', 'نامشخص')}\n"
            f"🆔 شناسه: <code>{user_data.get('id', 'نامشخص')}</code>\n"
            f"@{user_data.get('username', 'بدون نام کاربری')}\n"
            f"📱 شماره تماس: {user_data.get('phone', 'نامشخص')}\n"
            f"⏱ زمان: {get_formatted_datetime(datetime.now())}"
        )
        
        if details:
            message += f"\n\n📝 جزئیات: {details}"
            
        # Send notification
        return await self.send_notification(
            notification_type="USER_MANAGEMENT",
            message=message
        )
    
    async def send_server_notification(self, 
                                      server_data: Dict[str, Any], 
                                      action: str,
                                      details: Optional[str] = None) -> Dict[int, bool]:
        """Send server-related notification to management groups.
        
        Args:
            server_data: Server information.
            action: Action performed (e.g., 'added', 'updated', 'deleted', 'down').
            details: Optional additional details.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            f"<b>سرور {action}</b>\n\n"
            f"🏷 نام: {server_data.get('name', 'نامشخص')}\n"
            f"🌐 آدرس: {server_data.get('address', 'نامشخص')}\n"
            f"🔢 پورت: {server_data.get('port', 'نامشخص')}\n"
            f"🌍 مکان: {server_data.get('location', 'نامشخص')}\n"
            f"⏱ زمان: {get_formatted_datetime(datetime.now())}"
        )
        
        if details:
            message += f"\n\n📝 جزئیات: {details}"
            
        # Send notification
        return await self.send_notification(
            notification_type="SERVER_MANAGEMENT",
            message=message
        )
    
    async def send_location_notification(self, 
                                        location_data: Dict[str, Any], 
                                        action: str,
                                        details: Optional[str] = None) -> Dict[int, bool]:
        """Send location-related notification to management groups.
        
        Args:
            location_data: Location information.
            action: Action performed (e.g., 'added', 'updated', 'deleted').
            details: Optional additional details.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            f"<b>مکان {action}</b>\n\n"
            f"🏷 نام: {location_data.get('name', 'نامشخص')}\n"
            f"🌍 کشور: {location_data.get('country', 'نامشخص')}\n"
            f"🚩 کد: {location_data.get('code', 'نامشخص')}\n"
            f"⏱ زمان: {get_formatted_datetime(datetime.now())}"
        )
        
        if details:
            message += f"\n\n📝 جزئیات: {details}"
            
        # Send notification
        return await self.send_notification(
            notification_type="LOCATION_MANAGEMENT",
            message=message
        )
    
    async def send_service_notification(self, 
                                       service_data: Dict[str, Any], 
                                       action: str,
                                       details: Optional[str] = None) -> Dict[int, bool]:
        """Send service-related notification to management groups.
        
        Args:
            service_data: Service information.
            action: Action performed (e.g., 'added', 'updated', 'deleted').
            details: Optional additional details.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            f"<b>خدمت {action}</b>\n\n"
            f"🏷 نام: {service_data.get('name', 'نامشخص')}\n"
            f"💰 قیمت: {service_data.get('price', 0):,} تومان\n"
            f"📊 ترافیک: {service_data.get('traffic', 0)} گیگابایت\n"
            f"⏳ مدت: {service_data.get('duration', 0)} روز\n"
            f"⏱ زمان: {get_formatted_datetime(datetime.now())}"
        )
        
        if details:
            message += f"\n\n📝 جزئیات: {details}"
            
        # Send notification
        return await self.send_notification(
            notification_type="SERVICE_MANAGEMENT",
            message=message
        )
    
    async def send_discount_notification(self, 
                                        discount_data: Dict[str, Any], 
                                        action: str,
                                        details: Optional[str] = None) -> Dict[int, bool]:
        """Send discount-related notification to management groups.
        
        Args:
            discount_data: Discount information.
            action: Action performed (e.g., 'added', 'updated', 'deleted', 'used').
            details: Optional additional details.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            f"<b>کد تخفیف {action}</b>\n\n"
            f"🏷 کد: <code>{discount_data.get('code', 'نامشخص')}</code>\n"
            f"💰 مقدار: {discount_data.get('amount', 0)}"
        )
        
        if 'percent' in discount_data and discount_data['percent']:
            message += f" درصد"
        else:
            message += f" تومان"
            
        message += f"\n⏱ زمان: {get_formatted_datetime(datetime.now())}"
        
        if details:
            message += f"\n\n📝 جزئیات: {details}"
            
        # Send notification
        return await self.send_notification(
            notification_type="DISCOUNT_MARKETING",
            message=message
        )
    
    async def send_financial_report(self, 
                                   report_data: Dict[str, Any],
                                   period: str,
                                   buttons: Optional[List[List[InlineKeyboardButton]]] = None) -> Dict[int, bool]:
        """Send financial report to management groups.
        
        Args:
            report_data: Report information.
            period: Report period (e.g., 'daily', 'weekly', 'monthly').
            buttons: Optional buttons to add to the message.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            f"<b>گزارش مالی {period}</b>\n\n"
            f"💰 درآمد کل: {report_data.get('total_income', 0):,} تومان\n"
            f"🧾 تعداد تراکنش‌ها: {report_data.get('transaction_count', 0)}\n"
            f"👤 تعداد کاربران: {report_data.get('user_count', 0)}\n"
            f"📊 میانگین خرید: {report_data.get('average_purchase', 0):,} تومان\n"
            f"⏱ زمان گزارش: {get_formatted_datetime(datetime.now())}"
        )
        
        # Create reply markup if buttons provided
        reply_markup = None
        if buttons:
            reply_markup = InlineKeyboardMarkup(buttons)
            
        # Send notification
        return await self.send_notification(
            notification_type="FINANCIAL_REPORTS",
            message=message,
            reply_markup=reply_markup
        )
    
    async def send_bulk_message_report(self, 
                                      message_data: Dict[str, Any]) -> Dict[int, bool]:
        """Send bulk messaging report to management groups.
        
        Args:
            message_data: Message information.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            "<b>گزارش پیام‌رسانی انبوه</b>\n\n"
            f"📨 پیام ارسال شده به {message_data.get('recipient_count', 0)} کاربر\n"
            f"✅ تحویل موفق: {message_data.get('success_count', 0)}\n"
            f"❌ تحویل ناموفق: {message_data.get('failure_count', 0)}\n"
            f"⏱ زمان ارسال: {get_formatted_datetime(message_data.get('sent_at', datetime.now()))}"
        )
        
        # Send notification
        return await self.send_notification(
            notification_type="BULK_MESSAGING",
            message=message
        )
    
    async def send_server_monitoring_alert(self, 
                                          server_data: Dict[str, Any],
                                          alert_type: str,
                                          details: str) -> Dict[int, bool]:
        """Send server monitoring alert to management groups.
        
        Args:
            server_data: Server information.
            alert_type: Type of alert (e.g., 'down', 'high_load', 'disk_space').
            details: Alert details.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            f"<b>⚠️ هشدار مانیتورینگ: {alert_type}</b>\n\n"
            f"🖥️ سرور: {server_data.get('name', 'نامشخص')}\n"
            f"🌐 آدرس: {server_data.get('address', 'نامشخص')}\n"
            f"⏱ زمان: {get_formatted_datetime(datetime.now())}\n\n"
            f"📝 جزئیات: {details}"
        )
        
        # Send notification
        return await self.send_notification(
            notification_type="SERVER_MONITORING",
            message=message
        )
    
    async def send_system_notification(self, 
                                     title: str,
                                     message: str,
                                     buttons: Optional[List[List[InlineKeyboardButton]]] = None) -> Dict[int, bool]:
        """Send system notification to management groups.
        
        Args:
            title: Notification title.
            message: Notification message.
            buttons: Optional buttons to add to the message.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        formatted_message = (
            f"<b>{title}</b>\n\n"
            f"{message}\n\n"
            f"⏱ زمان: {get_formatted_datetime(datetime.now())}"
        )
        
        # Create reply markup if buttons provided
        reply_markup = None
        if buttons:
            reply_markup = InlineKeyboardMarkup(buttons)
            
        # Send notification
        return await self.send_notification(
            notification_type="SYSTEM_SETTINGS",
            message=formatted_message,
            reply_markup=reply_markup
        )
    
    async def send_error_alert(self, 
                              error_message: str,
                              source: str,
                              stack_trace: Optional[str] = None) -> Dict[int, bool]:
        """Send error alert to management groups.
        
        Args:
            error_message: Error message.
            source: Source of the error.
            stack_trace: Optional stack trace.
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            "<b>⚠️ خطای سیستمی</b>\n\n"
            f"🔍 منبع: {source}\n"
            f"❌ خطا: {error_message}\n"
            f"⏱ زمان: {get_formatted_datetime(datetime.now())}"
        )
        
        if stack_trace:
            # Truncate stack trace if too long
            if len(stack_trace) > 500:
                stack_trace = stack_trace[:497] + "..."
                
            message += f"\n\n<pre>{stack_trace}</pre>"
            
        # Send notification
        return await self.send_notification(
            notification_type="ERROR_ALERTS",
            message=message
        )
    
    async def send_backup_notification(self, 
                                      backup_data: Dict[str, Any],
                                      action: str) -> Dict[int, bool]:
        """Send backup-related notification to management groups.
        
        Args:
            backup_data: Backup information.
            action: Action performed (e.g., 'created', 'restored', 'deleted').
            
        Returns:
            Dictionary of chat_id: success pairs.
        """
        # Format message
        message = (
            f"<b>پشتیبان‌گیری {action}</b>\n\n"
            f"📁 نام فایل: {backup_data.get('filename', 'نامشخص')}\n"
            f"📊 حجم: {backup_data.get('size', 'نامشخص')}\n"
            f"⏱ زمان: {get_formatted_datetime(datetime.now())}"
        )
        
        # Send notification
        return await self.send_notification(
            notification_type="BACKUP_RESTORE",
            message=message
        )
    
    async def _send_message_to_chat(self, 
                                   chat_id: Union[int, str], 
                                   message: str,
                                   reply_markup: Optional[InlineKeyboardMarkup] = None,
                                   parse_mode: Optional[str] = ParseMode.HTML) -> bool:
        """Send a message to a specific chat.
        
        Args:
            chat_id: The chat ID to send the message to.
            message: The message to send.
            reply_markup: Optional inline keyboard markup.
            parse_mode: Parse mode for the message.
            
        Returns:
            True if the message was sent successfully, False otherwise.
        """
        if not self._bot:
            logger.error("Bot not set in NotificationService")
            return False
            
        try:
            await self._bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            logger.error(f"Error sending message to chat {chat_id}: {e}")
            return False

    async def send_alert(
        self,
        severity: str,
        message: str,
        details: Dict[str, Any],
        channels: Optional[List[str]] = None
    ):
        """
        Send security alert through specified channels.
        
        Args:
            severity: Alert severity level
            message: Alert message
            details: Additional alert details
            channels: List of channels to send to (email, webhook, sms, telegram)
        """
        try:
            if not channels:
                channels = ["email", "webhook"]  # Default channels

            # Prepare notification data
            notification_data = {
                "severity": severity,
                "message": message,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Send through each channel
            tasks = []
            if "email" in channels:
                tasks.append(self._send_email(notification_data))
            if "webhook" in channels:
                tasks.append(self._send_webhook(notification_data))
            if "sms" in channels:
                tasks.append(self._send_sms(notification_data))
            if "telegram" in channels:
                tasks.append(self._send_telegram(notification_data))

            # Wait for all notifications to be sent
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            raise SecurityError(f"Failed to send alert notification: {str(e)}")

    async def _send_email(self, data: Dict[str, Any]):
        """Send alert via email."""
        try:
            if not self.email_config:
                logger.warning("Email configuration not found")
                return

            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.email_config["from_email"]
            msg["To"] = self.email_config["to_email"]
            msg["Subject"] = f"Security Alert [{data['severity'].upper()}]: {data['message']}"

            # Create email body
            body = f"""
            Security Alert Details:
            ----------------------
            Severity: {data['severity']}
            Message: {data['message']}
            Time: {data['timestamp']}
            
            Additional Details:
            -----------------
            {json.dumps(data['details'], indent=2)}
            """

            msg.attach(MIMEText(body, "plain"))

            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.email_config["smtp_host"],
                port=self.email_config["smtp_port"],
                use_tls=True
            ) as smtp:
                await smtp.login(
                    self.email_config["smtp_user"],
                    self.email_config["smtp_password"]
                )
                await smtp.send_message(msg)

            logger.info(f"Email alert sent to {self.email_config['to_email']}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            raise

    async def _send_webhook(self, data: Dict[str, Any]):
        """Send alert via webhook."""
        try:
            if not self.webhook_config:
                logger.warning("Webhook configuration not found")
                return

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_config["url"],
                    json=data,
                    headers=self.webhook_config.get("headers", {})
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Webhook request failed with status {response.status}")

            logger.info("Webhook alert sent successfully")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {str(e)}")
            raise

    async def _send_sms(self, data: Dict[str, Any]):
        """Send alert via SMS."""
        try:
            if not self.sms_config:
                logger.warning("SMS configuration not found")
                return

            # TODO: Implement SMS sending logic based on chosen provider
            # This is a placeholder for SMS implementation
            logger.info("SMS alert sending not implemented")

        except Exception as e:
            logger.error(f"Failed to send SMS alert: {str(e)}")
            raise

    async def _send_telegram(self, data: Dict[str, Any]):
        """Send alert via Telegram."""
        try:
            if not self.telegram_config:
                logger.warning("Telegram configuration not found")
                return

            # Format message for Telegram
            message = (
                f"🚨 Security Alert\n\n"
                f"Severity: {data['severity']}\n"
                f"Message: {data['message']}\n"
                f"Time: {data['timestamp']}\n\n"
                f"Details:\n{json.dumps(data['details'], indent=2)}"
            )

            # Send to Telegram
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            payload = {
                "chat_id": self.telegram_config["chat_id"],
                "text": message,
                "parse_mode": "HTML"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Telegram request failed with status {response.status}")

            logger.info("Telegram alert sent successfully")

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {str(e)}")
            raise

    async def send_to_admin_group(
        self,
        group_id: str,
        message: str,
        channels: Optional[List[str]] = None
    ):
        """
        Send message to admin group through specified channels.
        
        Args:
            group_id: Admin group ID
            message: Message to send
            channels: List of channels to send to
        """
        try:
            if not channels:
                channels = ["email", "webhook"]  # Default channels

            # Get admin group details from settings
            admin_group = settings.ADMIN_GROUPS.get(group_id)
            if not admin_group:
                raise SecurityError(f"Admin group {group_id} not found")

            # Prepare notification data
            notification_data = {
                "group_id": group_id,
                "group_name": admin_group["name"],
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Send through each channel
            tasks = []
            if "email" in channels:
                tasks.append(self._send_email(notification_data))
            if "webhook" in channels:
                tasks.append(self._send_webhook(notification_data))
            if "sms" in channels:
                tasks.append(self._send_sms(notification_data))
            if "telegram" in channels:
                tasks.append(self._send_telegram(notification_data))

            # Wait for all notifications to be sent
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            raise SecurityError(f"Failed to send admin group notification: {str(e)}")

# Create a singleton instance
notification_service = NotificationService() 