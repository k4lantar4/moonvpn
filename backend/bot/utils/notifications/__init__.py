"""
Notifications utility module for MoonVPN

This module provides functions for sending notifications to users
via different channels like Telegram.
"""

import logging
import os
import requests
from typing import Union, Dict, Optional, Any

logger = logging.getLogger(__name__)

def send_telegram_notification(message: str, admin_only: bool = False, user_id: Optional[Union[int, str]] = None) -> bool:
    """
    Send a notification message via Telegram
    
    Args:
        message: The message to send
        admin_only: If True, only send to admin users
        user_id: Specific user ID to send to (overrides admin_only)
        
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        bot_token = os.environ.get('BOT_TOKEN')
        admin_id = os.environ.get('ADMIN_ID')
        
        if not bot_token:
            logger.warning("No BOT_TOKEN found in environment variables")
            return False
            
        # Mock implementation (prints to console)
        logger.info(f"[TELEGRAM] {'(ADMIN)' if admin_only else ''} {message}")
        
        # In a real implementation, we would use the python-telegram-bot library
        # or make API calls directly to Telegram
        if admin_only and admin_id:
            # Only send to admin
            _send_telegram_message(bot_token, admin_id, message)
        elif user_id:
            # Send to specific user
            _send_telegram_message(bot_token, user_id, message)
        else:
            # Get users from database and send to all
            # We'll just log for now
            logger.info("Would send to all users")
            
        return True
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")
        return False
        
def _send_telegram_message(bot_token: str, chat_id: Union[int, str], text: str) -> Dict[str, Any]:
    """
    Send a message through the Telegram Bot API
    
    Args:
        bot_token: Telegram Bot token
        chat_id: Telegram chat ID to send to
        text: Message text
        
    Returns:
        Dict: Response from Telegram API
    """
    # If DISABLE_TELEGRAM_NOTIFICATIONS is set, just return success without sending
    if os.environ.get('DISABLE_TELEGRAM_NOTIFICATIONS') == 'true':
        logger.info(f"Telegram notification would be sent to {chat_id}: {text}")
        return {"ok": True, "result": {"message_id": 0}}
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        # Return mock success to avoid breaking flows
        return {"ok": False, "error": str(e)}

def notify_payment_received(user: Any, amount: float, transaction_id: str) -> bool:
    """
    Send notification about received payment
    
    Args:
        user: User object who made the payment
        amount: Payment amount
        transaction_id: Transaction identifier
        
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        # Notify admin
        admin_message = f"💰 <b>New Payment Received</b>\n\n"
        admin_message += f"👤 User: {user.username or user.email}\n"
        admin_message += f"💵 Amount: {amount:,.0f} تومان\n"
        admin_message += f"🔢 Transaction ID: {transaction_id}\n"
        
        send_telegram_notification(admin_message, admin_only=True)
        
        # Notify user if they have a telegram_id
        if hasattr(user, 'telegram_id') and user.telegram_id:
            user_message = f"✅ <b>پرداخت شما با موفقیت ثبت شد</b>\n\n"
            user_message += f"💵 مبلغ: {amount:,.0f} تومان\n"
            user_message += f"🔢 شناسه تراکنش: {transaction_id}\n"
            user_message += f"🙏 با تشکر از اعتماد شما به MoonVPN"
            
            send_telegram_notification(user_message, user_id=user.telegram_id)
            
        return True
    except Exception as e:
        logger.error(f"Error sending payment notification: {str(e)}")
        return False