"""
Notification system for the V2Ray Telegram bot.

This module implements handlers for managing user notification preferences including:
- Account expiry notifications
- Traffic usage alerts
- Payment reminders
- System status updates

It also provides functions for sending notifications to users.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

from utils import (
    get_text,
    format_number,
    format_date,
)
from api_client import (
    get_user_profile,
    update_user_profile,
    get_all_users,
    get_admin_users,
    get_user_accounts,
    get_account,
    get_payment,
    get_server_stats,
)
from core.utils.helpers import require_auth
from bot.constants import (
    # Conversation states
    SELECTING_FEATURE,
    SELECTING_ACTION,
    END,
    
    # Callback data patterns
    NOTIFICATIONS_CB,
    TOGGLE_EXPIRY,
    TOGGLE_TRAFFIC,
    TOGGLE_PAYMENTS,
    TOGGLE_SYSTEM,
    PROFILE_CB,
    BACK_CB,
)
from .start import start, back_to_main

logger = logging.getLogger(__name__)

@require_auth
async def notifications_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show notification settings menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user notification settings
    user = get_user_profile(user_id)
    settings = user.get("notification_settings", {
        "expiry": True,
        "traffic": True,
        "payments": True,
        "system": True
    })
    
    message = get_text("notification_settings_info", language_code).format(
        expiry="✅" if settings.get("expiry", True) else "❌",
        traffic="✅" if settings.get("traffic", True) else "❌",
        payments="✅" if settings.get("payments", True) else "❌",
        system="✅" if settings.get("system", True) else "❌"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"{get_text('expiry_notifications', language_code)} {'✅' if settings.get('expiry', True) else '❌'}",
                callback_data=TOGGLE_EXPIRY
            )
        ],
        [
            InlineKeyboardButton(
                f"{get_text('traffic_notifications', language_code)} {'✅' if settings.get('traffic', True) else '❌'}",
                callback_data=TOGGLE_TRAFFIC
            )
        ],
        [
            InlineKeyboardButton(
                f"{get_text('payment_notifications', language_code)} {'✅' if settings.get('payments', True) else '❌'}",
                callback_data=TOGGLE_PAYMENTS
            )
        ],
        [
            InlineKeyboardButton(
                f"{get_text('system_notifications', language_code)} {'✅' if settings.get('system', True) else '❌'}",
                callback_data=TOGGLE_SYSTEM
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_profile", language_code),
                callback_data=PROFILE_CB
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_main", language_code),
                callback_data=BACK_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_ACTION

async def toggle_notification(update: Update, context: ContextTypes.DEFAULT_TYPE, setting_type: str) -> int:
    """Toggle a specific notification setting."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user profile
    user = get_user_profile(user_id)
    
    # Get current settings or set defaults
    settings = user.get("notification_settings", {
        "expiry": True,
        "traffic": True,
        "payments": True,
        "system": True
    })
    
    # Toggle the specified setting
    settings[setting_type] = not settings.get(setting_type, True)
    
    # Update user settings in database
    try:
        updated_user = update_user_profile(user_id, {"notification_settings": settings})
        
        if updated_user:
            # Success message
            await query.answer(
                get_text("notification_updated", language_code),
                show_alert=True
            )
        else:
            # Error message
            await query.answer(
                get_text("notification_update_failed", language_code),
                show_alert=True
            )
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        await query.answer(
            get_text("notification_update_error", language_code),
            show_alert=True
        )
    
    # Return to notifications menu
    return await notifications_menu(update, context)

@require_auth
async def toggle_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle expiry notifications."""
    return await toggle_notification(update, context, "expiry")

@require_auth
async def toggle_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle traffic notifications."""
    return await toggle_notification(update, context, "traffic")

@require_auth
async def toggle_payments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle payment notifications."""
    return await toggle_notification(update, context, "payments")

@require_auth
async def toggle_system(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle system notifications."""
    return await toggle_notification(update, context, "system")

# Notification sending functions

async def send_notification(
    bot: Bot,
    user_id: Union[str, int],
    message: str,
    keyboard: Optional[List[List[InlineKeyboardButton]]] = None,
    notification_type: str = "system"
) -> bool:
    """
    Send a notification to a user if they have the notification type enabled.
    
    Args:
        bot: The bot instance
        user_id: The user ID to send the notification to
        message: The message to send
        keyboard: Optional keyboard to attach to the message
        notification_type: The type of notification (expiry, traffic, payments, system)
        
    Returns:
        bool: True if the notification was sent, False otherwise
    """
    try:
        # Get user profile
        user = get_user_profile(user_id)
        
        if not user:
            logger.warning(f"User {user_id} not found for notification")
            return False
        
        # Check if user has this notification type enabled
        settings = user.get("notification_settings", {
            "expiry": True,
            "traffic": True,
            "payments": True,
            "system": True
        })
        
        if not settings.get(notification_type, True):
            logger.info(f"User {user_id} has {notification_type} notifications disabled")
            return False
        
        # Create reply markup if keyboard is provided
        reply_markup = None
        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the notification
        await bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return True
    except TelegramError as e:
        logger.error(f"Telegram error sending notification to {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending notification to {user_id}: {e}")
        return False

async def send_admin_notification(
    bot: Bot,
    message: str,
    keyboard: Optional[List[List[InlineKeyboardButton]]] = None
) -> int:
    """
    Send a notification to all admin users.
    
    Args:
        bot: The bot instance
        message: The message to send
        keyboard: Optional keyboard to attach to the message
        
    Returns:
        int: The number of admins the notification was sent to
    """
    # Get all admin users
    admins = get_admin_users()
    
    if not admins:
        logger.warning("No admin users found for notification")
        return 0
    
    sent_count = 0
    
    for admin in admins:
        admin_id = admin.get("id")
        
        if await send_notification(bot, admin_id, message, keyboard, "system"):
            sent_count += 1
    
    return sent_count

async def notify_account_expiry(bot: Bot) -> None:
    """
    Check for accounts expiring soon and send notifications to users.
    This should be run periodically (e.g., daily).
    """
    logger.info("Checking for accounts expiring soon...")
    
    # Get all users
    users = get_all_users()
    
    if not users:
        logger.info("No users found for expiry notifications")
        return
    
    # Check each user's accounts
    for user in users:
        user_id = user.get("id")
        language_code = user.get("language", "en")
        
        # Get user's accounts
        accounts = get_user_accounts(user_id)
        
        if not accounts:
            continue
        
        # Check each account for expiry
        for account in accounts:
            account_id = account.get("id")
            account_name = account.get("name", "Unknown")
            expiry_date = account.get("expiry_date", "")
            
            if not expiry_date:
                continue
            
            # Parse expiry date
            try:
                expiry_datetime = datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
                now = datetime.now().astimezone()
                
                # Calculate days until expiry
                days_until_expiry = (expiry_datetime - now).days
                
                # Notify if account expires in 3 days or less
                if 0 <= days_until_expiry <= 3:
                    # Create message
                    message = get_text("account_expiry_notification", language_code).format(
                        name=account_name,
                        days=days_until_expiry,
                        expiry_date=format_date(expiry_date, language_code)
                    )
                    
                    # Create keyboard
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                get_text("renew_account", language_code),
                                callback_data=f"renew_account:{account_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                get_text("view_accounts", language_code),
                                callback_data="accounts"
                            )
                        ]
                    ]
                    
                    # Send notification
                    await send_notification(bot, user_id, message, keyboard, "expiry")
            except Exception as e:
                logger.error(f"Error processing expiry date for account {account_id}: {e}")

async def notify_traffic_usage(bot: Bot) -> None:
    """
    Check for accounts with high traffic usage and send notifications to users.
    This should be run periodically (e.g., daily).
    """
    logger.info("Checking for accounts with high traffic usage...")
    
    # Get all users
    users = get_all_users()
    
    if not users:
        logger.info("No users found for traffic notifications")
        return
    
    # Check each user's accounts
    for user in users:
        user_id = user.get("id")
        language_code = user.get("language", "en")
        
        # Get user's accounts
        accounts = get_user_accounts(user_id)
        
        if not accounts:
            continue
        
        # Check each account for traffic usage
        for account in accounts:
            account_id = account.get("id")
            account_name = account.get("name", "Unknown")
            traffic_used = account.get("traffic_used", 0)
            traffic_limit = account.get("traffic_limit", 0)
            
            # Skip accounts with unlimited traffic
            if traffic_limit == 0:
                continue
            
            # Calculate usage percentage
            traffic_used_gb = traffic_used / 1024 / 1024 / 1024
            traffic_limit_gb = traffic_limit
            
            if traffic_limit_gb > 0:
                usage_percent = (traffic_used_gb / traffic_limit_gb) * 100
                
                # Notify if usage is over 80%
                if usage_percent >= 80:
                    # Create message
                    message = get_text("traffic_usage_notification", language_code).format(
                        name=account_name,
                        used=format_number(traffic_used_gb, language_code),
                        limit=format_number(traffic_limit_gb, language_code),
                        percent=int(usage_percent)
                    )
                    
                    # Create keyboard
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                get_text("view_account", language_code),
                                callback_data=f"view_account_details:{account_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                get_text("view_accounts", language_code),
                                callback_data="accounts"
                            )
                        ]
                    ]
                    
                    # Send notification
                    await send_notification(bot, user_id, message, keyboard, "traffic")

async def notify_payment_verification(bot: Bot, payment_id: str) -> None:
    """
    Notify a user that their payment has been verified.
    
    Args:
        bot: The bot instance
        payment_id: The ID of the verified payment
    """
    # Get payment details
    payment = get_payment(payment_id)
    
    if not payment:
        logger.warning(f"Payment {payment_id} not found for notification")
        return
    
    user_id = payment.get("user_id")
    language_code = get_user_profile(user_id).get("language", "en")
    amount = payment.get("amount", 0)
    payment_method = payment.get("payment_method", "")
    
    # Create message
    message = get_text("payment_verified_notification", language_code).format(
        amount=format_number(amount, language_code),
        method=get_text(f"payment_method_{payment_method}", language_code),
        id=payment_id
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("view_transactions", language_code),
                callback_data="transactions"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("create_account", language_code),
                callback_data="create_account"
            )
        ]
    ]
    
    # Send notification
    await send_notification(bot, user_id, message, keyboard, "payments")

async def notify_payment_rejected(bot: Bot, payment_id: str) -> None:
    """
    Notify a user that their payment has been rejected.
    
    Args:
        bot: The bot instance
        payment_id: The ID of the rejected payment
    """
    # Get payment details
    payment = get_payment(payment_id)
    
    if not payment:
        logger.warning(f"Payment {payment_id} not found for notification")
        return
    
    user_id = payment.get("user_id")
    language_code = get_user_profile(user_id).get("language", "en")
    amount = payment.get("amount", 0)
    payment_method = payment.get("payment_method", "")
    
    # Create message
    message = get_text("payment_rejected_notification", language_code).format(
        amount=format_number(amount, language_code),
        method=get_text(f"payment_method_{payment_method}", language_code),
        id=payment_id
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("add_funds", language_code),
                callback_data="payments"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("contact_support", language_code),
                callback_data="support"
            )
        ]
    ]
    
    # Send notification
    await send_notification(bot, user_id, message, keyboard, "payments")

async def notify_server_status(bot: Bot, server_id: str, status: str) -> None:
    """
    Notify admins about a server status change.
    
    Args:
        bot: The bot instance
        server_id: The ID of the server
        status: The new status of the server
    """
    # Get server details
    server = get_server_stats(server_id)
    
    if not server:
        logger.warning(f"Server {server_id} not found for notification")
        return
    
    server_name = server.get("name", "Unknown")
    
    # Create message
    message = f"🖥️ *Server Status Update*\n\n"
    message += f"Server: *{server_name}*\n"
    message += f"Status: *{status.upper()}*\n"
    message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "View Server Details",
                callback_data=f"admin_servers_details:{server_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "Server Management",
                callback_data="admin_servers"
            )
        ]
    ]
    
    # Send notification to admins
    await send_admin_notification(bot, message, keyboard)

def get_notifications_handlers() -> List[ConversationHandler]:
    """Return the handlers for notifications functionality."""
    # Notifications conversation handler
    notifications_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                notifications_menu, pattern=f"^{NOTIFICATIONS_CB}$"
            )
        ],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(toggle_expiry, pattern=f"^{TOGGLE_EXPIRY}$"),
                CallbackQueryHandler(toggle_traffic, pattern=f"^{TOGGLE_TRAFFIC}$"),
                CallbackQueryHandler(toggle_payments, pattern=f"^{TOGGLE_PAYMENTS}$"),
                CallbackQueryHandler(toggle_system, pattern=f"^{TOGGLE_SYSTEM}$"),
            ]
        },
        fallbacks=[
            CallbackQueryHandler(back_to_main, pattern=f"^{BACK_CB}$"),
            CallbackQueryHandler(notifications_menu, pattern=f"^{NOTIFICATIONS_CB}$"),
            CommandHandler("start", start)
        ],
        map_to_parent={
            END: SELECTING_FEATURE,
        },
        name="notifications_conversation",
        persistent=True
    )
    
    return [notifications_handler] 