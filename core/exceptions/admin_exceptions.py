"""
Admin-related exceptions for MoonVPN.

This module contains custom exceptions for admin-related errors.
"""

from typing import Optional
from app.core.exceptions.base import BaseError

class AdminError(BaseError):
    """Base exception for admin-related errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        """Initialize the exception."""
        super().__init__(message)
        self.status_code = status_code

class AdminConfigError(AdminError):
    """Raised when there is an error with admin configuration."""
    
    def __init__(self, message: str = "Admin configuration error"):
        """Initialize the exception."""
        super().__init__(message, status_code=500)

class AdminPermissionError(AdminError):
    """Raised when there is a permission error."""
    
    def __init__(self, message: str = "Insufficient admin permissions"):
        """Initialize the exception."""
        super().__init__(message, status_code=403)

class AdminGroupError(AdminError):
    """Raised when there is an error with admin groups."""
    
    def __init__(self, group_id: str, message: Optional[str] = None):
        """Initialize the exception."""
        msg = f"Error with admin group '{group_id}'"
        if message:
            msg += f": {message}"
        super().__init__(msg, status_code=500)

class AdminMonitoringError(AdminError):
    """Raised when there is an error with system monitoring."""
    
    def __init__(self, message: str = "System monitoring error"):
        """Initialize the exception."""
        super().__init__(message, status_code=500)

class AdminReportError(AdminError):
    """Raised when there is an error generating admin reports."""
    
    def __init__(self, report_type: str, message: Optional[str] = None):
        """Initialize the exception."""
        msg = f"Error generating {report_type} report"
        if message:
            msg += f": {message}"
        super().__init__(msg, status_code=500)

class AdminSettingError(AdminError):
    """Raised when there is an error with admin settings."""
    
    def __init__(self, setting_key: str, message: Optional[str] = None):
        """Initialize the exception."""
        msg = f"Error with admin setting '{setting_key}'"
        if message:
            msg += f": {message}"
        super().__init__(msg, status_code=500) 