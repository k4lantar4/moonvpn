"""
Initialization file for the XUI integration package.

Exports the main API wrapper classes for easy import.
"""

from .base import BaseApi
from .inbound_api import InboundApi
from .client_api import ClientApi
from .server_api import ServerApi
from .exceptions import (
    XuiError,
    XuiAuthenticationError,
    XuiConnectionError,
    XuiValidationError,
    XuiOperationError,
    XuiNotFoundError
)

__all__ = [
    "BaseApi",
    "InboundApi",
    "ClientApi",
    "ServerApi",
    "XuiError",
    "XuiAuthenticationError",
    "XuiConnectionError",
    "XuiValidationError",
    "XuiOperationError",
    "XuiNotFoundError",
] 