"""
MoonVPN FastAPI - Config Package

This package contains application configuration and settings.
"""

from .settings import Settings, get_settings
from .constants import (
    # API Constants
    API_VERSION,
    API_PREFIX,
    
    # Status Codes
    StatusCodes,
    
    # Messages
    Messages,
    
    # Error Codes
    ErrorCodes,
    
    # Rate Limits
    RateLimits,
    
    # Cache Keys
    CacheKeys,
    
    # Pagination
    Pagination,
    
    # Bot Commands
    Commands,
    
    # Callback Patterns
    CallbackPatterns,
    
    # States
    States,
    
    # Language
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    
    # Payment
    PAYMENT_METHODS,
    
    # Server
    SERVER_TYPES,
    
    # Account
    ACCOUNT_STATUS,
    
    # Ticket
    TICKET_STATUS,
    TICKET_PRIORITY,
    
    # Cache
    CACHE_TTL,
)

__all__ = [
    # Settings
    'Settings',
    'get_settings',
    
    # API Constants
    'API_VERSION',
    'API_PREFIX',
    
    # Status Codes
    'StatusCodes',
    
    # Messages
    'Messages',
    
    # Error Codes
    'ErrorCodes',
    
    # Rate Limits
    'RateLimits',
    
    # Cache Keys
    'CacheKeys',
    
    # Pagination
    'Pagination',
    
    # Bot Commands
    'Commands',
    
    # Callback Patterns
    'CallbackPatterns',
    
    # States
    'States',
    
    # Language
    'DEFAULT_LANGUAGE',
    'SUPPORTED_LANGUAGES',
    
    # Payment
    'PAYMENT_METHODS',
    
    # Server
    'SERVER_TYPES',
    
    # Account
    'ACCOUNT_STATUS',
    
    # Ticket
    'TICKET_STATUS',
    'TICKET_PRIORITY',
    
    # Cache
    'CACHE_TTL',
]
