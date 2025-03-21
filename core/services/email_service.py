"""
Email Service for MoonVPN

This module handles all email-related functionality including sending verification emails,
notifications, and alerts.
"""

import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import json
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from app.core.config import settings
from app.core.models.user import User
from app.core.models.notification import Notification
from app.core.exceptions import EmailError

logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling all email operations."""
    
    def __init__(self):
        """Initialize the email service."""
        self.email_config = settings.EMAIL_CONFIG
        self.template_dir = Path(__file__).parent.parent.parent / "templates" / "email"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
    async def send_verification_email(self, user: User, token: str) -> None:
        """
        Send email verification link to user.
        
        Args:
            user: User object
            token: Verification token
        """
        try:
            template = self.jinja_env.get_template("verification.html")
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            
            html_content = template.render(
                username=user.username or user.email,
                verification_url=verification_url,
                expires_in="24 hours"
            )
            
            await self._send_email(
                to_email=user.email,
                subject="Verify Your MoonVPN Email",
                html_content=html_content
            )
            
            logger.info(f"Verification email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            raise EmailError(f"Failed to send verification email: {str(e)}")
    
    async def send_password_reset_email(self, user: User, token: str) -> None:
        """
        Send password reset link to user.
        
        Args:
            user: User object
            token: Reset token
        """
        try:
            template = self.jinja_env.get_template("password_reset.html")
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            html_content = template.render(
                username=user.username or user.email,
                reset_url=reset_url,
                expires_in="1 hour"
            )
            
            await self._send_email(
                to_email=user.email,
                subject="Reset Your MoonVPN Password",
                html_content=html_content
            )
            
            logger.info(f"Password reset email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            raise EmailError(f"Failed to send password reset email: {str(e)}")
    
    async def send_notification_email(self, notification: Notification) -> None:
        """
        Send notification email to user.
        
        Args:
            notification: Notification object
        """
        try:
            template = self.jinja_env.get_template("notification.html")
            
            html_content = template.render(
                title=notification.title,
                message=notification.message,
                timestamp=notification.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                notification_type=notification.type
            )
            
            await self._send_email(
                to_email=notification.user.email,
                subject=f"MoonVPN: {notification.title}",
                html_content=html_content
            )
            
            logger.info(f"Notification email sent to {notification.user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send notification email: {str(e)}")
            raise EmailError(f"Failed to send notification email: {str(e)}")
    
    async def send_alert_email(
        self,
        severity: str,
        message: str,
        details: Dict[str, Any],
        to_email: str
    ) -> None:
        """
        Send alert email.
        
        Args:
            severity: Alert severity level
            message: Alert message
            details: Additional alert details
            to_email: Recipient email address
        """
        try:
            template = self.jinja_env.get_template("alert.html")
            
            html_content = template.render(
                severity=severity.upper(),
                message=message,
                details=json.dumps(details, indent=2),
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            await self._send_email(
                to_email=to_email,
                subject=f"MoonVPN Alert [{severity.upper()}]: {message}",
                html_content=html_content
            )
            
            logger.info(f"Alert email sent to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            raise EmailError(f"Failed to send alert email: {str(e)}")
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> None:
        """
        Send email using configured SMTP server.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            from_email: Optional sender email address
        """
        try:
            if not self.email_config:
                raise EmailError("Email configuration not found")
            
            msg = MIMEMultipart()
            msg["From"] = from_email or self.email_config["from_email"]
            msg["To"] = to_email
            msg["Subject"] = subject
            
            msg.attach(MIMEText(html_content, "html"))
            
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
                
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise EmailError(f"Failed to send email: {str(e)}") 