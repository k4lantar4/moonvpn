"""
Core database models for MoonVPN.
This module contains all database models organized by domain.
"""

from .base import Base, BaseModel
from .user import User
from .vpn import VPNAccount, Server, Location, TrafficLog
from .payment import Payment, CardPayment, ZarinpalPayment
from .subscription import Plan, Subscription
from .points import PointsTransaction, PointsRedemptionRule, PointsRedemption
from .chat import LiveChatSession, LiveChatMessage, LiveChatOperator, LiveChatRating
from .api import APIKey, APIRequest, APIRateLimit, Webhook
from .role import Role, Permission

__all__ = [
    'Base',
    'BaseModel',
    'User',
    'VPNAccount',
    'Server',
    'Location',
    'TrafficLog',
    'Payment',
    'CardPayment',
    'ZarinpalPayment',
    'Plan',
    'Subscription',
    'PointsTransaction',
    'PointsRedemptionRule',
    'PointsRedemption',
    'LiveChatSession',
    'LiveChatMessage',
    'LiveChatOperator',
    'LiveChatRating',
    'APIKey',
    'APIRequest',
    'APIRateLimit',
    'Webhook',
    'Role',
    'Permission'
]

# Import all models for convenience
try:
    from core.database.models.chat import *
except ImportError:
    pass

try:
    from core.database.models.settings import *
except ImportError:
    pass

try:
    from core.database.models.src_main import *
except ImportError:
    pass

try:
    from core.database.models.referral import *
except ImportError:
    pass

try:
    from core.database.models.notification import *
except ImportError:
    pass

try:
    from core.database.models.chat_src import *
except ImportError:
    pass

try:
    from core.database.models.roles import *
except ImportError:
    pass

try:
    from core.database.models.backend_core import *
except ImportError:
    pass

try:
    from core.database.models.src_vpn import *
except ImportError:
    pass

try:
    from core.database.models.user_activity import *
except ImportError:
    pass

try:
    from core.database.models.accounts import *
except ImportError:
    pass

try:
    from core.database.models.moonvpn_users import *
except ImportError:
    pass

try:
    from core.database.models.traffic import *
except ImportError:
    pass

try:
    from core.database.models.src_v2ray import *
except ImportError:
    pass

try:
    from core.database.models.vpn_account import *
except ImportError:
    pass

try:
    from core.database.models.system_config import *
except ImportError:
    pass

try:
    from core.database.models.src_chat import *
except ImportError:
    pass

try:
    from core.database.models.discount import *
except ImportError:
    pass

try:
    from core.database.models.subscriptions import *
except ImportError:
    pass

try:
    from core.database.models.security import *
except ImportError:
    pass

try:
    from core.database.models.api import *
except ImportError:
    pass

try:
    from core.database.models.src_payments import *
except ImportError:
    pass

try:
    from core.database.models.payment import *
except ImportError:
    pass

try:
    from core.database.models.vpn import *
except ImportError:
    pass

try:
    from core.database.models.chat_backend import *
except ImportError:
    pass

try:
    from core.database.models.moonvpn_services import *
except ImportError:
    pass

try:
    from core.database.models.payments import *
except ImportError:
    pass

try:
    from core.database.models.src_api import *
except ImportError:
    pass

try:
    from core.database.models.database import *
except ImportError:
    pass

try:
    from core.database.models.transaction import *
except ImportError:
    pass

try:
    from core.database.models.subscription_plan import *
except ImportError:
    pass

try:
    from core.database.models.system_stats import *
except ImportError:
    pass

try:
    from core.database.models.src_points import *
except ImportError:
    pass

try:
    from core.database.models.feature_flag import *
except ImportError:
    pass

try:
    from core.database.models.bot_subscriptions import *
except ImportError:
    pass

try:
    from core.database.models.moonvpn import *
except ImportError:
    pass

try:
    from core.database.models.server import *
except ImportError:
    pass

try:
    from core.database.models.ticket import *
except ImportError:
    pass

try:
    from core.database.models.points import *
except ImportError:
    pass

try:
    from core.database.models.src_telegrambot import *
except ImportError:
    pass

try:
    from core.database.models.groups import *
except ImportError:
    pass

