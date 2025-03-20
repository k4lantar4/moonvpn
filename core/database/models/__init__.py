"""
Database models package.
"""

from .base import Base, BaseModel

# Core models
from .core.user import User
from .core.group import Group

# VPN models
from .vpn.account import VPNAccount
from .vpn.server import Server

# Points models
from .points.points import UserPoints
from .points.transaction import PointsTransaction

# Chat models
from .chat.session import ChatSession
from .chat.message import ChatMessage

# Enhancement models
from .enhancements.health import SystemHealth
from .enhancements.backup import SystemBackup
from .enhancements.report import Report
from .enhancements.log import SystemLog
from .enhancements.metric import SystemMetric
from .enhancements.config import SystemConfig

__all__ = [
    # Base
    "Base",
    "BaseModel",
    
    # Core
    "User",
    "Group",
    
    # VPN
    "VPNAccount",
    "Server",
    
    # Points
    "UserPoints",
    "PointsTransaction",
    
    # Chat
    "ChatSession",
    "ChatMessage",
    
    # Enhancements
    "SystemHealth",
    "SystemBackup",
    "Report",
    "SystemLog",
    "SystemMetric",
    "SystemConfig",
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

