"""
Utility functions for sending notifications.
"""
from typing import Optional
import aiohttp
from app.core.models.alert import Alert
from app.core.config import settings

async def send_alert_notification(alert: Alert) -> None:
    """Send alert notification through configured channels."""
    # Send to Telegram admin groups
    if settings.TELEGRAM_ADMIN_GROUPS:
        await send_telegram_alert(alert)

    # Send to email if configured
    if settings.ALERT_EMAIL_RECIPIENTS:
        await send_email_alert(alert)

    # Send to webhook if configured
    if settings.ALERT_WEBHOOK_URL:
        await send_webhook_alert(alert)

async def send_telegram_alert(alert: Alert) -> None:
    """Send alert to Telegram admin groups."""
    message = format_alert_message(alert)
    
    for group_id in settings.TELEGRAM_ADMIN_GROUPS:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                data = {
                    "chat_id": group_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        print(f"Failed to send Telegram alert: {await response.text()}")
        except Exception as e:
            print(f"Error sending Telegram alert: {str(e)}")

async def send_email_alert(alert: Alert) -> None:
    """Send alert via email."""
    # Implement email sending logic
    # This is a placeholder - implement actual email sending
    pass

async def send_webhook_alert(alert: Alert) -> None:
    """Send alert to configured webhook."""
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "id": alert.id,
                "component": alert.component,
                "severity": alert.severity,
                "status": alert.status,
                "title": alert.title,
                "message": alert.message,
                "metrics": alert.metrics,
                "created_at": alert.created_at.isoformat()
            }
            async with session.post(settings.ALERT_WEBHOOK_URL, json=data) as response:
                if response.status != 200:
                    print(f"Failed to send webhook alert: {await response.text()}")
    except Exception as e:
        print(f"Error sending webhook alert: {str(e)}")

def format_alert_message(alert: Alert) -> str:
    """Format alert message for Telegram."""
    severity_emoji = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "critical": "🚨"
    }
    
    status_emoji = {
        "active": "🔄",
        "acknowledged": "✅",
        "resolved": "✅",
        "ignored": "⏭️"
    }
    
    emoji = severity_emoji.get(alert.severity, "ℹ️")
    status = status_emoji.get(alert.status, "🔄")
    
    message = f"{emoji} <b>{alert.title}</b>\n\n"
    message += f"Component: {alert.component}\n"
    message += f"Severity: {alert.severity}\n"
    message += f"Status: {alert.status} {status}\n\n"
    message += f"{alert.message}\n\n"
    
    if alert.metrics:
        message += "<code>Metrics:</code>\n"
        for key, value in alert.metrics.items():
            message += f"{key}: {value}\n"
    
    return message 