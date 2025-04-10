"""
Central import for all SQLAlchemy models.
Ensures all models are registered with the Base metadata before use.
"""

from core.database.session import Base # Import Base here once

# Import all model classes
from .user import User
from .role import Role, RoleName
from .location import Location
from .panel import Panel, PanelType
from .plan_category import PlanCategory # Added
from .plan import Plan # Added
from .panel_inbound import PanelInbound # Added
from .client_account import ClientAccount
from .order import Order
from .payment import Payment
from .transaction import Transaction
from .bank_card import BankCard
from .setting import Setting
from .notification_channel import NotificationChannel
from .panel_health_check import PanelHealthCheck # Added
from .client_migration import ClientMigration
from .client_id_sequence import ClientIdSequence
from .discount_code import DiscountCode # Added

# Define __all__ to control what 'from core.database.models import *' imports
__all__ = [
    "Base", # Export Base from here too
    "User",
    "Role",
    "RoleName",
    "Location",
    "Panel",
    "PanelType",
    "PlanCategory",
    "Plan",
    "PanelInbound",
    "ClientAccount",
    "Order",
    "Payment",
    "Transaction",
    "BankCard",
    "Setting",
    "NotificationChannel",
    "PanelHealthCheck",
    "ClientMigration",
    "ClientIdSequence",
    "DiscountCode",
]
