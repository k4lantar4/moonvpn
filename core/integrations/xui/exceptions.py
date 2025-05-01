"""
Custom exceptions for XUI integration.
"""

class XuiError(Exception):
    """Base exception for XUI integration errors."""
    pass

class XuiAuthenticationError(XuiError):
    """Raised for authentication failures (login, invalid token)."""
    pass

class XuiConnectionError(XuiError):
    """Raised for network connection issues with the XUI panel."""
    pass

class XuiValidationError(XuiError):
    """Raised for invalid input data provided to the API."""
    pass

class XuiOperationError(XuiError):
    """Raised for general errors during an XUI operation."""
    pass
    
class XuiNotFoundError(XuiError):
    """Raised when a requested resource (like an inbound) is not found."""
    pass 