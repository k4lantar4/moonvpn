"""
Email-related exceptions for MoonVPN.

This module contains custom exceptions for email-related errors.
"""

from typing import Optional
from app.core.exceptions.base import BaseError

class EmailError(BaseError):
    """Base exception for email-related errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        """Initialize the exception."""
        super().__init__(message)
        self.status_code = status_code

class EmailConfigError(EmailError):
    """Raised when there is an error with email configuration."""
    
    def __init__(self, message: str = "Email configuration error"):
        """Initialize the exception."""
        super().__init__(message, status_code=500)

class EmailTemplateError(EmailError):
    """Raised when there is an error with email templates."""
    
    def __init__(self, template_name: str, message: Optional[str] = None):
        """Initialize the exception."""
        msg = f"Error with email template '{template_name}'"
        if message:
            msg += f": {message}"
        super().__init__(msg, status_code=500)

class EmailSendError(EmailError):
    """Raised when there is an error sending an email."""
    
    def __init__(self, to_email: str, message: Optional[str] = None):
        """Initialize the exception."""
        msg = f"Failed to send email to '{to_email}'"
        if message:
            msg += f": {message}"
        super().__init__(msg, status_code=500)

class EmailRateLimitError(EmailError):
    """Raised when email rate limit is exceeded."""
    
    def __init__(self, limit_type: str, limit: int):
        """Initialize the exception."""
        msg = f"Email rate limit exceeded: {limit} emails per {limit_type}"
        super().__init__(msg, status_code=429)

class EmailVerificationError(EmailError):
    """Raised when there is an error with email verification."""
    
    def __init__(self, message: str = "Email verification error"):
        """Initialize the exception."""
        super().__init__(message, status_code=400)

class EmailResetError(EmailError):
    """Raised when there is an error with password reset email."""
    
    def __init__(self, message: str = "Password reset email error"):
        """Initialize the exception."""
        super().__init__(message, status_code=400) 