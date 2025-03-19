"""
Services package for MoonVPN Bot.

This package contains service modules that implement business logic.
"""

from .account_service import AccountService
from .payment_service import PaymentService
from .notification_service import notification_service
from .vpn_service import VPNService
from .user_service import UserService
from .broadcast_service import BroadcastService

__all__ = [
    'VPNService',
    'PaymentService',
    'UserService',
    'BroadcastService'
]

# Initialize service instances
vpn_service = VPNService()
payment_service = PaymentService()
user_service = UserService()
broadcast_service = BroadcastService() 