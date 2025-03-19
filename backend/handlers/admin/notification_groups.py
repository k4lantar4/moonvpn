"""
Notification Groups.

This module contains functions for sending notifications to the configured groups.
"""

import logging
from typing import Dict, Any, Optional, List, Union

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

# Group types matching website specifications
GROUP_MANAGEMENT = "management"  # Main management group (MANAGE)
GROUP_REPORTS = "reports"  # System reports and statistics
GROUP_LOGS = "logs"  # User activity logs
GROUP_TRANSACTIONS = "transactions"  # Payment transactions
GROUP_OUTAGES = "outages"  # Server disruptions and outages
GROUP_SELLERS = "sellers"  # Resellers information
GROUP_BACKUPS = "backups"  # System backup notifications

# API client functions (replace with actual API calls)
async def get_group_chat_id(group_type: str) -> Optional[str]:
    """Get the chat ID for a specific notification group type."""
    # This should be replaced with an actual API call
    mock_groups = {
        GROUP_MANAGEMENT: "-100123456789",
        GROUP_REPORTS: "-100987654321",
        GROUP_LOGS: "-100123123123",
        GROUP_TRANSACTIONS: "-100456456456",
        GROUP_OUTAGES: "-100789789789",
        GROUP_SELLERS: "-100654654654",
        GROUP_BACKUPS: "-100321321321",
    }
    return mock_groups.get(group_type)

async def get_all_group_chat_ids() -> Dict[str, str]:
    """Get all configured notification group chat IDs."""
    # This should be replaced with an actual API call
    return {
        GROUP_MANAGEMENT: "-100123456789",
        GROUP_REPORTS: "-100987654321",
        GROUP_LOGS: "-100123123123",
        GROUP_TRANSACTIONS: "-100456456456",
        GROUP_OUTAGES: "-100789789789",
        GROUP_SELLERS: "-100654654654",
        GROUP_BACKUPS: "-100321321321",
    }

async def is_notification_enabled(group_type: str, notification_type: str) -> bool:
    """Check if a specific notification is enabled for a group."""
    # This should be replaced with an actual API call
    # For now, all notifications are enabled
    return True

# Notification functions
async def send_notification(
    bot: Bot, 
    group_type: str, 
    message: str, 
    notification_type: str = "general",
    keyboard: Any = None,
    silent: bool = False
) -> bool:
    """
    Send a notification to a specific group type.
    
    Args:
        bot: The bot instance
        group_type: The type of group to send to (e.g., "management", "transactions")
        message: The message text
        notification_type: The type of notification for filtering
        keyboard: Optional inline keyboard
        silent: Whether to disable notification sound
        
    Returns:
        bool: Whether the message was sent successfully
    """
    # Check if this notification is enabled
    is_enabled = await is_notification_enabled(group_type, notification_type)
    if not is_enabled:
        logger.info(f"Notification {notification_type} is disabled for group {group_type}")
        return False
    
    # Get chat ID for the group
    chat_id = await get_group_chat_id(group_type)
    if not chat_id:
        logger.warning(f"No chat ID configured for group type {group_type}")
        return False
    
    # Add group prefix based on type
    group_prefix = {
        GROUP_MANAGEMENT: "🛡️ *MANAGE*",
        GROUP_REPORTS: "📊 *REPORTS*",
        GROUP_LOGS: "📄 *LOGS*",
        GROUP_TRANSACTIONS: "💰 *TRANSACTIONS*", 
        GROUP_OUTAGES: "⚠️ *OUTAGES*",
        GROUP_SELLERS: "👥 *SELLERS*",
        GROUP_BACKUPS: "💾 *BACKUPS*",
    }.get(group_type, "")
    
    # Prepare the message with prefix
    full_message = f"{group_prefix}\n\n{message}" if group_prefix else message
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=full_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            disable_notification=silent
        )
        return True
    except TelegramError as e:
        logger.error(f"Failed to send notification to {group_type} group: {str(e)}")
        
        # Fall back to main group if this isn't the main group already
        if group_type != GROUP_MANAGEMENT:
            try:
                # Add prefix to indicate this was meant for another group
                fallback_message = f"⚠️ *Notification Fallback ({group_type})*\n\n{message}"
                main_chat_id = await get_group_chat_id(GROUP_MANAGEMENT)
                
                if main_chat_id:
                    await bot.send_message(
                        chat_id=main_chat_id,
                        text=fallback_message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard,
                        disable_notification=silent
                    )
                    logger.info(f"Notification sent to main group as fallback for {group_type}")
                    return True
            except TelegramError as e2:
                logger.error(f"Failed to send fallback notification to main group: {str(e2)}")
        
        return False

async def broadcast_notification(
    bot: Bot, 
    message: str, 
    group_types: List[str] = None,
    exclude_groups: List[str] = None,
    notification_type: str = "broadcast",
    keyboard: Any = None,
    silent: bool = False
) -> Dict[str, bool]:
    """
    Broadcast a notification to multiple groups.
    
    Args:
        bot: The bot instance
        message: The message text
        group_types: List of group types to send to, or None for all
        exclude_groups: List of group types to exclude
        notification_type: The type of notification for filtering
        keyboard: Optional inline keyboard
        silent: Whether to disable notification sound
        
    Returns:
        Dict[str, bool]: Results of sending to each group
    """
    exclude_groups = exclude_groups or []
    results = {}
    
    # Get all group IDs
    all_groups = await get_all_group_chat_ids()
    
    # Determine target groups
    target_groups = group_types if group_types else list(all_groups.keys())
    
    # Remove excluded groups
    target_groups = [g for g in target_groups if g not in exclude_groups]
    
    # Send to each group
    for group_type in target_groups:
        if group_type in all_groups:
            success = await send_notification(
                bot=bot,
                group_type=group_type,
                message=message,
                notification_type=notification_type,
                keyboard=keyboard,
                silent=silent
            )
            results[group_type] = success
    
    return results

# Specialized notification functions
async def notify_user_registration(
    bot: Bot, 
    user_data: Dict[str, Any]
) -> bool:
    """
    Send notification about a new user registration.
    
    Args:
        bot: The bot instance
        user_data: User data dictionary with details
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    user_id = user_data.get('id', 'unknown')
    username = user_data.get('username', 'ناشناس')
    full_name = user_data.get('name', 'بدون نام')
    
    message = (
        f"👤 *کاربر جدید ثبت‌نام کرد*\n\n"
        f"• شناسه: `{user_id}`\n"
        f"• نام کاربری: @{username}\n"
        f"• نام کامل: {full_name}\n"
        f"• زمان: {user_data.get('created_at', 'نامشخص')}"
    )
    
    # Send to both MANAGEMENT and LOGS groups per website specification
    return all(await broadcast_notification(
        bot=bot,
        message=message,
        group_types=[GROUP_MANAGEMENT, GROUP_LOGS],
        notification_type="user_registration"
    ).values())

async def notify_payment_new(
    bot: Bot, 
    payment_data: Dict[str, Any]
) -> bool:
    """
    Send notification about a new payment.
    
    Args:
        bot: The bot instance
        payment_data: Payment data dictionary
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    payment_id = payment_data.get('id', 'unknown')
    amount = payment_data.get('amount', 0)
    user_id = payment_data.get('user_id', 'unknown')
    username = payment_data.get('user_name', 'ناشناس')
    
    message = (
        f"💰 *پرداخت جدید دریافت شد*\n\n"
        f"• شناسه پرداخت: `{payment_id}`\n"
        f"• مبلغ: {amount:,} تومان\n"
        f"• کاربر: @{username} (`{user_id}`)\n"
        f"• زمان: {payment_data.get('created_at', 'نامشخص')}\n\n"
        f"این پرداخت در انتظار تایید است."
    )
    
    # Send to both MANAGEMENT and TRANSACTIONS groups
    return all(await broadcast_notification(
        bot=bot,
        message=message,
        group_types=[GROUP_MANAGEMENT, GROUP_TRANSACTIONS],
        notification_type="payment_new"
    ).values())

async def notify_payment_processed(
    bot: Bot, 
    payment_data: Dict[str, Any],
    approved: bool = False
) -> bool:
    """
    Send notification about a processed payment.
    
    Args:
        bot: The bot instance
        payment_data: Payment data dictionary
        approved: Whether the payment was approved or rejected
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    payment_id = payment_data.get('id', 'unknown')
    amount = payment_data.get('amount', 0)
    user_id = payment_data.get('user_id', 'unknown')
    username = payment_data.get('user_name', 'ناشناس')
    admin_username = payment_data.get('admin_username', 'ناشناس')
    
    if approved:
        status_emoji = "✅"
        status_text = "تایید شد"
    else:
        status_emoji = "❌"
        status_text = "رد شد"
        reason = payment_data.get('reason', 'دلیلی ذکر نشده')
    
    message = (
        f"{status_emoji} *پرداخت {status_text}*\n\n"
        f"• شناسه پرداخت: `{payment_id}`\n"
        f"• مبلغ: {amount:,} تومان\n"
        f"• کاربر: @{username} (`{user_id}`)\n"
    )
    
    if not approved:
        message += f"• دلیل رد: {reason}\n"
    
    message += f"• توسط: @{admin_username}\n"
    message += f"• زمان: {payment_data.get('updated_at', 'نامشخص')}"
    
    # Send to TRANSACTIONS group only
    return await send_notification(
        bot=bot,
        group_type=GROUP_TRANSACTIONS,
        message=message,
        notification_type="payment_processed"
    )

async def notify_server_status(
    bot: Bot, 
    server_data: Dict[str, Any],
    is_online: bool
) -> bool:
    """
    Send notification about server status change.
    
    Args:
        bot: The bot instance
        server_data: Server data dictionary
        is_online: Whether the server is coming online or going offline
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    server_id = server_data.get('id', 'unknown')
    name = server_data.get('name', 'نامشخص')
    location = server_data.get('location', 'نامشخص')
    
    if is_online:
        status_emoji = "🟢"
        status_text = "آنلاین شد"
    else:
        status_emoji = "🔴"
        status_text = "آفلاین شد"
    
    message = (
        f"{status_emoji} *سرور {status_text}*\n\n"
        f"• شناسه: `{server_id}`\n"
        f"• نام: {name}\n"
        f"• موقعیت: {location}\n"
        f"• IP: {server_data.get('ip', 'نامشخص')}\n"
        f"• زمان: {server_data.get('updated_at', 'نامشخص')}"
    )
    
    if not is_online:
        # For offline servers, notify both MANAGEMENT and OUTAGES groups
        return all(await broadcast_notification(
            bot=bot,
            message=message,
            group_types=[GROUP_MANAGEMENT, GROUP_OUTAGES],
            notification_type="server_status"
        ).values())
    else:
        # For online servers, notify only OUTAGES group
        return await send_notification(
            bot=bot,
            group_type=GROUP_OUTAGES,
            message=message,
            notification_type="server_status"
        )

async def notify_account_created(
    bot: Bot, 
    account_data: Dict[str, Any]
) -> bool:
    """
    Send notification about a new VPN account creation.
    
    Args:
        bot: The bot instance
        account_data: Account data dictionary
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    account_id = account_data.get('id', 'unknown')
    username = account_data.get('username', 'نامشخص')
    server_name = account_data.get('server_name', 'نامشخص')
    user_id = account_data.get('user_id', 'unknown')
    user_name = account_data.get('user_name', 'ناشناس')
    
    message = (
        f"🔑 *اکانت جدید ایجاد شد*\n\n"
        f"• شناسه: `{account_id}`\n"
        f"• نام کاربری: {username}\n"
        f"• سرور: {server_name}\n"
        f"• بسته: {account_data.get('package', 'نامشخص')}\n"
        f"• کاربر: @{user_name} (`{user_id}`)\n"
        f"• زمان ایجاد: {account_data.get('created_at', 'نامشخص')}\n"
        f"• تاریخ انقضا: {account_data.get('expire_date', 'نامشخص')}"
    )
    
    # Send to both MANAGEMENT and LOGS groups
    return all(await broadcast_notification(
        bot=bot,
        message=message,
        group_types=[GROUP_MANAGEMENT, GROUP_LOGS],
        notification_type="account_created"
    ).values())

async def notify_system_error(
    bot: Bot, 
    error_data: Dict[str, Any]
) -> bool:
    """
    Send notification about a system error.
    
    Args:
        bot: The bot instance
        error_data: Error data dictionary
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    error_type = error_data.get('type', 'نامشخص')
    error_msg = error_data.get('message', 'پیام خطا موجود نیست')
    component = error_data.get('component', 'نامشخص')
    
    message = (
        f"⚠️ *خطای سیستمی*\n\n"
        f"• بخش: {component}\n"
        f"• نوع خطا: {error_type}\n"
        f"• زمان: {error_data.get('timestamp', 'نامشخص')}\n\n"
        f"*پیام خطا:*\n```\n{error_msg}\n```"
    )
    
    # System errors go to MANAGEMENT group
    return await send_notification(
        bot=bot,
        group_type=GROUP_MANAGEMENT,
        message=message,
        notification_type="system_error"
    )

async def notify_backup_completed(
    bot: Bot, 
    backup_data: Dict[str, Any]
) -> bool:
    """
    Send notification about a completed backup.
    
    Args:
        bot: The bot instance
        backup_data: Backup data dictionary
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    backup_id = backup_data.get('id', 'unknown')
    size = backup_data.get('size', 'نامشخص')
    duration = backup_data.get('duration', 'نامشخص')
    status = backup_data.get('status', 'completed')
    
    success = status.lower() == 'completed'
    
    if success:
        status_emoji = "✅"
        status_text = "موفق"
    else:
        status_emoji = "❌"
        status_text = "ناموفق"
    
    message = (
        f"{status_emoji} *پشتیبان‌گیری {status_text}*\n\n"
        f"• شناسه: `{backup_id}`\n"
        f"• حجم: {size}\n"
        f"• مدت زمان: {duration}\n"
        f"• محل ذخیره: {backup_data.get('location', 'نامشخص')}\n"
        f"• زمان: {backup_data.get('timestamp', 'نامشخص')}"
    )
    
    if not success:
        error = backup_data.get('error', 'دلیل خطا ثبت نشده')
        message += f"\n\n*خطا:* {error}"
        
        # Failed backups go to both BACKUPS and MANAGEMENT
        return all(await broadcast_notification(
            bot=bot,
            message=message,
            group_types=[GROUP_BACKUPS, GROUP_MANAGEMENT],
            notification_type="backup_status"
        ).values())
    else:
        # Successful backups go only to BACKUPS
        return await send_notification(
            bot=bot,
            group_type=GROUP_BACKUPS,
            message=message,
            notification_type="backup_status"
        )

async def notify_high_system_load(
    bot: Bot, 
    system_data: Dict[str, Any]
) -> bool:
    """
    Send notification about high system load.
    
    Args:
        bot: The bot instance
        system_data: System data dictionary
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    load_avg = system_data.get('load_avg', ['N/A', 'N/A', 'N/A'])
    memory_used = system_data.get('memory_used', 'N/A')
    disk_used = system_data.get('disk_used', 'N/A')
    
    message = (
        f"🚨 *سیستم تحت فشار است*\n\n"
        f"• CPU Load: {load_avg[0]} (1m), {load_avg[1]} (5m), {load_avg[2]} (15m)\n"
        f"• مصرف رم: {memory_used}\n"
        f"• مصرف دیسک: {disk_used}\n"
        f"• تعداد کاربران آنلاین: {system_data.get('active_users', 'N/A')}\n"
        f"• زمان: {system_data.get('timestamp', 'نامشخص')}"
    )
    
    # High system load goes to both MANAGEMENT and OUTAGES groups
    return all(await broadcast_notification(
        bot=bot,
        message=message,
        group_types=[GROUP_MANAGEMENT, GROUP_OUTAGES],
        notification_type="system_load"
    ).values())

async def notify_seller_activity(
    bot: Bot, 
    seller_data: Dict[str, Any]
) -> bool:
    """
    Send notification about seller activities.
    
    Args:
        bot: The bot instance
        seller_data: Seller data dictionary
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    seller_id = seller_data.get('id', 'unknown')
    username = seller_data.get('username', 'ناشناس')
    action = seller_data.get('action', 'نامشخص')
    
    message = (
        f"👤 *فعالیت فروشنده*\n\n"
        f"• شناسه: `{seller_id}`\n"
        f"• نام کاربری: @{username}\n"
        f"• عملیات: {action}\n"
        f"• تعداد فروش: {seller_data.get('sales_count', 'N/A')}\n"
        f"• زمان: {seller_data.get('timestamp', 'نامشخص')}"
    )
    
    # Seller activities go to SELLERS group
    return await send_notification(
        bot=bot,
        group_type=GROUP_SELLERS,
        message=message,
        notification_type="seller_activity"
    ) 