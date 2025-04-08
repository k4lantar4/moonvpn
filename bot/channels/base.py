"""
Notification Channels Module

This module implements the channel-based notification system for the Telegram bot.
It provides different notification channels for various purposes (admin, payment, report, etc.)
and handles message formatting, delivery, and interactive buttons.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from telegram.error import TelegramError

from core.config import get_settings
from core.cache import get_cache
from core.i18n import get_translator

settings = get_settings()
logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Types of notification channels."""
    ADMIN = "admin"
    PAYMENT = "payment"
    REPORT = "report"
    LOG = "log"
    ALERT = "alert"
    BACKUP = "backup"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationManager:
    """
    Manager for handling notifications across different channels.
    
    This class:
    1. Manages different notification channels
    2. Handles message formatting
    3. Provides templates for various notification types
    4. Supports interactive buttons
    5. Handles delivery tracking and retries
    """
    
    def __init__(self, context: Optional[CallbackContext] = None):
        """
        Initialize notification manager.
        
        Args:
            context: Telegram context for sending messages
        """
        self.context = context
        self.channels: Dict[str, List[int]] = {
            ChannelType.ADMIN: self._parse_ids(settings.TELEGRAM_ADMIN_IDS),
            ChannelType.PAYMENT: self._parse_ids(settings.TELEGRAM_PAYMENT_CHANNEL),
            ChannelType.REPORT: self._parse_ids(settings.TELEGRAM_REPORT_CHANNEL),
            ChannelType.LOG: self._parse_ids(settings.TELEGRAM_LOG_CHANNEL),
            ChannelType.ALERT: self._parse_ids(settings.TELEGRAM_ALERT_CHANNEL),
            ChannelType.BACKUP: self._parse_ids(settings.TELEGRAM_BACKUP_CHANNEL),
        }
        self._translator = get_translator()
    
    @staticmethod
    def _parse_ids(ids_string: str) -> List[int]:
        """
        Parse comma-separated IDs into a list of integers.
        
        Args:
            ids_string: Comma-separated list of IDs
            
        Returns:
            List[int]: List of parsed IDs
        """
        if not ids_string:
            return []
        
        try:
            return [int(id_str.strip()) for id_str in ids_string.split(",") if id_str.strip()]
        except ValueError:
            logger.error(f"Invalid ID format in '{ids_string}'")
            return []
    
    async def send_notification(
        self,
        channel: Union[ChannelType, str],
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        buttons: Optional[List[Dict[str, str]]] = None,
        disable_notification: bool = False,
        parse_mode: str = "HTML",
        image_path: Optional[str] = None,
        document_path: Optional[str] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send notification to a channel.
        
        Args:
            channel: Channel type or custom channel name
            message: Message text (can include HTML formatting)
            priority: Message priority
            buttons: List of button configurations [{"text": "Button Text", "callback_data": "data"}]
            disable_notification: Whether to send silently
            parse_mode: Message parsing mode (HTML, Markdown)
            image_path: Path to image to send with message
            document_path: Path to document to send with message
            reply_to_message_id: Message ID to reply to
            
        Returns:
            List[Dict[str, Any]]: List of message send results
        """
        if not self.context:
            logger.error("Cannot send notification: No Telegram context provided")
            return [{"success": False, "error": "No Telegram context provided"}]
        
        # Get target chat IDs
        chat_ids = []
        if isinstance(channel, ChannelType) or channel in ChannelType.__members__:
            channel_type = channel if isinstance(channel, ChannelType) else ChannelType(channel)
            chat_ids = self.channels.get(channel_type, [])
        else:
            # Custom channel, try to parse as chat ID
            try:
                chat_id = int(channel)
                chat_ids = [chat_id]
            except ValueError:
                logger.error(f"Invalid channel: {channel}")
                return [{"success": False, "error": f"Invalid channel: {channel}"}]
        
        if not chat_ids:
            logger.warning(f"No recipients found for channel: {channel}")
            return [{"success": False, "error": f"No recipients for channel: {channel}"}]
        
        # Prepare keyboard if buttons provided
        reply_markup = None
        if buttons:
            keyboard = []
            row = []
            for button in buttons:
                row.append(InlineKeyboardButton(
                    text=button["text"], 
                    callback_data=button["callback_data"]
                ))
                # Add 2 buttons per row by default
                if len(row) >= 2:
                    keyboard.append(row)
                    row = []
            if row:  # Add remaining buttons
                keyboard.append(row)
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send messages
        results = []
        
        for chat_id in chat_ids:
            try:
                # Send image if provided
                if image_path:
                    msg = await self.context.bot.send_photo(
                        chat_id=chat_id,
                        photo=open(image_path, "rb"),
                        caption=message if len(message) <= 1024 else None,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                        disable_notification=disable_notification,
                        reply_to_message_id=reply_to_message_id,
                    )
                    
                    # Send message separately if caption was too long
                    if len(message) > 1024:
                        msg = await self.context.bot.send_message(
                            chat_id=chat_id,
                            text=message,
                            parse_mode=parse_mode,
                            reply_markup=reply_markup,
                            disable_notification=disable_notification,
                        )
                
                # Send document if provided
                elif document_path:
                    msg = await self.context.bot.send_document(
                        chat_id=chat_id,
                        document=open(document_path, "rb"),
                        caption=message if len(message) <= 1024 else None,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                        disable_notification=disable_notification,
                        reply_to_message_id=reply_to_message_id,
                    )
                    
                    # Send message separately if caption was too long
                    if len(message) > 1024:
                        msg = await self.context.bot.send_message(
                            chat_id=chat_id,
                            text=message,
                            parse_mode=parse_mode,
                            reply_markup=reply_markup,
                            disable_notification=disable_notification,
                        )
                
                # Send regular message
                else:
                    msg = await self.context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                        disable_notification=disable_notification,
                        reply_to_message_id=reply_to_message_id,
                    )
                
                results.append({
                    "success": True,
                    "chat_id": chat_id,
                    "message_id": msg.message_id
                })
                
            except Exception as e:
                logger.error(f"Error sending notification to {chat_id}: {str(e)}")
                results.append({
                    "success": False,
                    "chat_id": chat_id,
                    "error": str(e)
                })
        
        return results
    
    # --- Template methods for common notifications ---
    
    async def send_admin_notification(
        self, 
        message: str, 
        buttons: Optional[List[Dict[str, str]]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ) -> List[Dict[str, Any]]:
        """
        Send notification to admin channel.
        
        Args:
            message: Message text (can include HTML formatting)
            buttons: List of button configurations
            priority: Message priority
            
        Returns:
            List[Dict[str, Any]]: List of message send results
        """
        return await self.send_notification(
            channel=ChannelType.ADMIN,
            message=message,
            priority=priority,
            buttons=buttons,
            disable_notification=(priority == NotificationPriority.LOW)
        )
    
    async def send_panel_status_notification(
        self,
        panel_name: str,
        status: str,
        details: Dict[str, Any],
        buttons: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send panel status notification.
        
        Args:
            panel_name: Name of the panel
            status: Status (healthy, warning, error)
            details: Status details
            buttons: Optional buttons to include
            
        Returns:
            List[Dict[str, Any]]: List of message send results
        """
        priority = NotificationPriority.NORMAL
        if status == "error":
            priority = NotificationPriority.HIGH
        elif status == "warning":
            priority = NotificationPriority.NORMAL
        
        # Format message
        emoji = "✅" if status == "healthy" else "⚠️" if status == "warning" else "🚫"
        message = (
            f"{emoji} <b>پنل {panel_name}</b>\n\n"
            f"وضعیت: <b>{status}</b>\n"
        )
        
        if "version" in details:
            message += f"نسخه: {details['version']}\n"
        
        if "inbounds_count" in details:
            message += f"تعداد اینباندها: {details['inbounds_count']}\n"
        
        if "online_clients_count" in details:
            message += f"کاربران آنلاین: {details['online_clients_count']}\n"
        
        if "response_time_ms" in details:
            message += f"زمان پاسخ: {details['response_time_ms']:.1f} ms\n"
        
        # Add error details if present
        if "error" in details:
            message += f"\n<b>خطا:</b> {details['error']}\n"
        
        # Add timestamp
        message += f"\n<i>زمان بررسی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        return await self.send_admin_notification(
            message=message,
            buttons=buttons,
            priority=priority
        )
    
    async def send_client_added_notification(
        self,
        panel_name: str,
        inbound_id: int,
        client_email: str,
        protocol: str,
        expire_days: Optional[int] = None,
        traffic_limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send notification when a client is added.
        
        Args:
            panel_name: Name of the panel
            inbound_id: Inbound ID
            client_email: Client email
            protocol: Protocol (vmess, vless, trojan, shadowsocks)
            expire_days: Number of days until expiration
            traffic_limit: Traffic limit in GB
            
        Returns:
            List[Dict[str, Any]]: List of message send results
        """
        # Get protocol emoji
        protocol_emoji = {
            "vmess": "🔵",
            "vless": "🟣",
            "trojan": "🟢",
            "shadowsocks": "⚫",
            "wireguard": "🟡",
        }.get(protocol.lower(), "🔷")
        
        message = (
            f"🆕 <b>کاربر جدید اضافه شد</b>\n\n"
            f"پنل: <b>{panel_name}</b>\n"
            f"اینباند: <code>{inbound_id}</code>\n"
            f"پروتکل: {protocol_emoji} <code>{protocol}</code>\n"
            f"ایمیل: <code>{client_email}</code>\n"
        )
        
        if expire_days:
            message += f"انقضا: <b>{expire_days} روز</b>\n"
        
        if traffic_limit:
            message += f"حجم ترافیک: <b>{traffic_limit} GB</b>\n"
        
        # Add timestamp
        message += f"\n<i>زمان ایجاد: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        buttons = [
            {"text": "نمایش جزئیات", "callback_data": f"view_client:{client_email}"},
            {"text": "مشاهده ترافیک", "callback_data": f"view_traffic:{client_email}"}
        ]
        
        return await self.send_notification(
            channel=ChannelType.ADMIN,
            message=message,
            buttons=buttons
        )
    
    async def send_backup_notification(
        self,
        backup_path: str,
        backup_size: int,
        panels_count: int,
        clients_count: int,
    ) -> List[Dict[str, Any]]:
        """
        Send backup notification with the backup file.
        
        Args:
            backup_path: Path to backup file
            backup_size: Size of backup in bytes
            panels_count: Number of panels in backup
            clients_count: Number of clients in backup
            
        Returns:
            List[Dict[str, Any]]: List of message send results
        """
        size_mb = backup_size / (1024 * 1024)
        
        message = (
            f"💾 <b>پشتیبان گیری موفق</b>\n\n"
            f"اندازه فایل: <b>{size_mb:.2f} MB</b>\n"
            f"تعداد پنل‌ها: <b>{panels_count}</b>\n"
            f"تعداد کاربران: <b>{clients_count}</b>\n\n"
            f"<i>زمان پشتیبان گیری: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        )
        
        return await self.send_notification(
            channel=ChannelType.BACKUP,
            message=message,
            document_path=backup_path
        )


# Function to get NotificationManager as a dependency
async def get_notification_manager(context: Optional[CallbackContext] = None) -> NotificationManager:
    """
    Get a notification manager instance.
    
    Args:
        context: Telegram context for sending messages
        
    Returns:
        NotificationManager: Notification manager instance
    """
    return NotificationManager(context)
